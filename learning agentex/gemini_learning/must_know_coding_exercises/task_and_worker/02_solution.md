# Solution: The Task-Worker Lifecycle Pattern

This solution demonstrates the core "Lifecycle" logic of a Worker in AgentEx. In a real-world scenario, this logic is often provided by **Temporal**, but understanding the "Handshake" between a Task Queue and a Worker is essential for any Backend Engineer.

## The Solution Code

```python
import asyncio
import uuid
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    payload: str = ""
    result: str = None
    error: str = None

class MockTaskQueue:
    def __init__(self):
        self.queue = [
            Task(payload="Analyze sentiment: 'I love this!'"),
            Task(payload="Generate summary: 'Agentex is great'"),
            Task(payload="ERROR_TRIGGER"), 
            Task(payload="Translate: 'Hello' to 'Spanish'"),
        ]

    async def poll_tasks(self, batch_size: int = 2) -> list[Task]:
        pending = [t for t in self.queue if t.status == TaskStatus.PENDING]
        return pending[:batch_size]

    async def update_status(self, task_id: str, status: TaskStatus, result: str = None, error: str = None):
        for t in self.queue:
            if t.id == task_id:
                t.status = status
                t.result = result
                t.error = error
                print(f"[Store] Task {task_id[:8]} updated to {status.value}")

class TaskWorker:
    def __init__(self, queue: MockTaskQueue, max_workers: int = 2):
        self.queue = queue
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def _sync_execute_ai_task(self, payload: str) -> str:
        """Simulates CPU-bound or blocking AI operation (Synchronous)."""
        import time
        time.sleep(1) # Simulate delay
        if "ERROR" in payload:
            raise ValueError("AI Engine Crash!")
        return f"Processed: {payload}"

    async def process_task(self, task: Task):
        """
        The Lifecycle of a single task.
        """
        print(f"[Worker] Starting task {task.id[:8]}...")
        
        # 1. State Transition: Move to RUNNING
        await self.queue.update_status(task.id, TaskStatus.RUNNING)

        try:
            # 2. Execution: Run the synchronous code in a thread pool
            # Use asyncio.to_thread (standard in Python 3.9+)
            result = await asyncio.to_thread(self._sync_execute_ai_task, task.payload)
            
            # 3. Success: Move to COMPLETED
            await self.queue.update_status(task.id, TaskStatus.COMPLETED, result=result)
            print(f"[Worker] Task {task.id[:8]} finished: {result}")
            
        except Exception as e:
            # 4. Failure: Move to FAILED
            print(f"[Worker] Task {task.id[:8]} FAILED: {str(e)}")
            await self.queue.update_status(task.id, TaskStatus.FAILED, error=str(e))

    async def run(self):
        """
        The Polling Loop.
        """
        while True:
            # 1. Poll for a batch
            batch = await self.queue.poll_tasks(batch_size=2)
            
            if not batch:
                print("[Worker] No more tasks. Shutting down.")
                break

            # 2. Process the batch in PARALLEL
            # This is critical for scaling workers.
            print(f"
[Worker] Polled batch of {len(batch)} tasks...")
            
            # Use gather to run all tasks in this batch concurrently
            await asyncio.gather(*(self.process_task(task) for task in batch))
            
            # 3. Small pause to prevent tight polling loops
            await asyncio.sleep(0.1)

async def main():
    mq = MockTaskQueue()
    worker = TaskWorker(mq)
    print("--- Starting Task Worker ---")
    await worker.run()
    print("--- All Tasks Processed ---")

if __name__ == "__main__":
    asyncio.run(main())
```

## Output Analysis
When you run this code, you will see the worker picking up tasks in pairs (batch size of 2). Because of `asyncio.gather` and `asyncio.to_thread`, both tasks in a batch will start almost simultaneously, even though they each "sleep" for 1 second. 

This simulates how Agentex workers can scale horizontally by increasing the `max_workers` and `max_concurrent_activities` configuration.
