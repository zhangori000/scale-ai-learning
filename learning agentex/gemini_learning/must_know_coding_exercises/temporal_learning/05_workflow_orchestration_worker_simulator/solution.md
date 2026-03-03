# Solution: Distributed Orchestrator (Workers, Tasks, and Retries)

This implementation uses `asyncio` to simulate a distributed system where an **Orchestrator** manages a **Task Queue**, and multiple **Workers** execute tasks with **Automatic Retries**.

```python
import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum, auto

# --- Core Types ---

class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()

@dataclass
class RetryPolicy:
    max_attempts: int = 3
    initial_interval: float = 1.0  # seconds
    backoff_coefficient: float = 2.0

@dataclass
class ActivityTask:
    id: str
    name: str
    func: Callable
    args: tuple
    retry_policy: RetryPolicy
    attempt: int = 1
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None

# --- Orchestrator ---

class Orchestrator:
    def __init__(self):
        # A queue of Task IDs that are ready for pickup
        self.task_queue: asyncio.Queue[str] = asyncio.Queue()
        # Storage for all tasks (indexed by ID)
        self.tasks: Dict[str, ActivityTask] = {}
        # Event to notify when a specific task is finished
        self.task_completion_events: Dict[str, asyncio.Event] = {}

    async def schedule_activity(self, func: Callable, args: tuple, retry_policy: RetryPolicy) -> Any:
        """Schedules an activity and waits for its completion."""
        task_id = f"task-{random.getrandbits(32):x}"
        task = ActivityTask(
            id=task_id, 
            name=func.__name__, 
            func=func, 
            args=args, 
            retry_policy=retry_policy
        )
        
        self.tasks[task_id] = task
        self.task_completion_events[task_id] = asyncio.Event()
        
        # Put the task ID on the queue for workers to poll
        print(f"[ORCHESTRATOR] Scheduled: {task.name} (ID: {task_id})")
        await self.task_queue.put(task_id)

        # Wait until a worker completes or fails the task
        await self.task_completion_events[task_id].wait()

        final_task = self.tasks[task_id]
        if final_task.status == TaskStatus.FAILED:
            raise Exception(f"Task {final_task.name} failed after {final_task.attempt} attempts: {final_task.error}")
        
        return final_task.result

    async def report_result(self, task_id: str, result: Any = None, error: Exception = None):
        """Called by Workers to report completion or failure."""
        task = self.tasks[task_id]

        if error:
            print(f"[ORCHESTRATOR] Task {task_id} failed attempt {task.attempt}: {error}")
            
            # CHECK RETRY POLICY
            if task.attempt < task.retry_policy.max_attempts:
                # Calculate exponential backoff
                wait_time = task.retry_policy.initial_interval * (task.retry_policy.backoff_coefficient ** (task.attempt - 1))
                task.attempt += 1
                task.status = TaskStatus.PENDING
                
                # Reschedule after backoff
                asyncio.create_task(self._delayed_reschedule(task_id, wait_time))
            else:
                task.status = TaskStatus.FAILED
                task.error = str(error)
                self.task_completion_events[task_id].set()
        else:
            print(f"[ORCHESTRATOR] Task {task_id} COMPLETED successfully.")
            task.status = TaskStatus.COMPLETED
            task.result = result
            self.task_completion_events[task_id].set()

    async def _delayed_reschedule(self, task_id: str, delay: float):
        """Handles the backoff wait before re-queuing."""
        await asyncio.sleep(delay)
        print(f"[ORCHESTRATOR] Rescheduling {task_id} after {delay}s backoff...")
        await self.task_queue.put(task_id)

# --- Worker ---

class Worker:
    def __init__(self, orchestrator: Orchestrator, name: str):
        self.orchestrator = orchestrator
        self.name = name

    async def start(self):
        """Polls the orchestrator for tasks indefinitely."""
        print(f"[{self.name}] Worker started and polling...")
        while True:
            # POLL: Fetch a task ID from the orchestrator's queue
            task_id = await self.orchestrator.task_queue.get()
            task = self.orchestrator.tasks[task_id]
            task.status = TaskStatus.RUNNING
            
            print(f"[{self.name}] Executing {task.name} (Attempt {task.attempt})...")
            
            try:
                # SIMULATE NETWORK DELAY
                await asyncio.sleep(0.5)
                
                # EXECUTE ACTIVITY
                result = await task.func(*task.args)
                await self.orchestrator.report_result(task_id, result=result)
            except Exception as e:
                await self.orchestrator.report_result(task_id, error=e)
            finally:
                self.orchestrator.task_queue.task_done()

# --- Example Activities ---

async def unreliable_api_call(prompt: str):
    """Simulates an flaky API call."""
    if random.random() < 0.7:  # 70% failure rate
        raise Exception("Connection Timeout")
    return f"Model response for: {prompt}"

async def database_save(data: str):
    """Simulates a stable DB write."""
    return f"Saved: {data}"

# --- The Workflow ---

async def main_workflow(orchestrator: Orchestrator):
    policy = RetryPolicy(max_attempts=5, initial_interval=1.0)
    
    print("
--- Starting Main Workflow ---")
    try:
        # Step 1: Flaky API Call (Requires Retries)
        llm_response = await orchestrator.schedule_activity(unreliable_api_call, ("Tell me a joke",), policy)
        print(f"WORKFLOW PROGRESS: Received LLM output: {llm_response}")

        # Step 2: Stable DB Save
        db_result = await orchestrator.schedule_activity(database_save, (llm_response,), policy)
        print(f"WORKFLOW COMPLETE: {db_result}")
    except Exception as e:
        print(f"WORKFLOW FAILED: {e}")

# --- Runner ---

async def run_simulation():
    orchestrator = Orchestrator()
    
    # Start two independent workers
    worker_a = Worker(orchestrator, "Worker-A")
    worker_b = Worker(orchestrator, "Worker-B")
    
    # Run workers in background
    asyncio.create_task(worker_a.start())
    asyncio.create_task(worker_b.start())

    # Run the workflow
    await main_workflow(orchestrator)

if __name__ == "__main__":
    asyncio.run(run_simulation())
```

## Deep Dive Explanation

### 1. Decoupling Request from Execution
In standard Python, `await func()` runs the function on the local event loop. In this orchestrator (and in Temporal), `schedule_activity` does **NOT** run the function. It creates a **Task Record** and puts it in a **Queue**. Any worker in the fleet can pick it up. This is the foundation of **Scalability**.

### 2. The Orchestrator as a "Source of Truth"
The Orchestrator doesn't know *who* is running the task, only that it is currently `RUNNING`. If the worker reports an error, the Orchestrator applies the `RetryPolicy`. The workflow itself is suspended (via `asyncio.Event().wait()`) while this happens, making the retry logic transparent to the workflow author.

### 3. Exponential Backoff
The formula `initial_interval * (backoff_coefficient ** (attempt - 1))` is the standard way to handle retries. 
- Attempt 1: 1s wait
- Attempt 2: 2s wait
- Attempt 3: 4s wait
- Attempt 4: 8s wait
This prevents "Thundering Herd" problems where failed clients DOS a service by retrying too fast.

### 4. Connection to `agentex`
In `agentex`, your workers are configured with a `task_queue` name. When you start a worker, it connects to Temporal and says "I am ready for tasks from queue 'X'". 
The `agentex-python` SDK handles the background polling and result reporting automatically, but under the hood, it's doing exactly what this `Worker` class does: 
1. Fetch Task -> 2. Run Activity -> 3. Report Success/Failure.
