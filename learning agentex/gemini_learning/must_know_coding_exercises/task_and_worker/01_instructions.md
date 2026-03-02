# Exercise 31: The Task-Worker Lifecycle Pattern

In distributed systems like Agentex, the "Task-Worker" pattern is the engine of asynchronous execution. A **Worker** is a separate process that "polls" a **Task Queue** for work, executes it, and then reports the result back to the **State Store**.

This exercise simulates the core logic of a Temporal Worker or a custom background processor.

## The Challenge

You need to implement a `TaskWorker` that:
1.  **Polls** a queue for a batch of tasks.
2.  **Transition State**: Updates the task status to `RUNNING` before starting work.
3.  **Executes**: Simulates a long-running AI operation.
4.  **Completion/Failure**: Updates the status to `COMPLETED` or `FAILED` based on the outcome.
5.  **Concurrency**: Uses a `ThreadPoolExecutor` to handle multiple tasks in parallel (simulating the `max_workers` configuration in Agentex).

## Starter Code

```python
import asyncio
import uuid
import random
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
    """Simulates a central task queue (like Temporal or Redis)."""
    def __init__(self):
        self.queue = [
            Task(payload="Analyze sentiment: 'I love this!'"),
            Task(payload="Generate summary: 'Agentex is great'"),
            Task(payload="ERROR_TRIGGER"), # This one should fail
            Task(payload="Translate: 'Hello' to 'Spanish'"),
        ]

    async def poll_tasks(self, batch_size: int = 2) -> list[Task]:
        """Returns a batch of pending tasks."""
        pending = [t for t in self.queue if t.status == TaskStatus.PENDING]
        batch = pending[:batch_size]
        return batch

    async def update_status(self, task_id: str, status: TaskStatus, result: str = None, error: str = None):
        """Updates the persistent state of a task."""
        for t in self.queue:
            if t.id == task_id:
                t.status = status
                t.result = result
                t.error = error
                print(f"[Store] Task {task_id[:8]} updated to {status.value}")

# --- Your Task ---

class TaskWorker:
    def __init__(self, queue: MockTaskQueue, max_workers: int = 2):
        self.queue = queue
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def _sync_execute_ai_task(self, payload: str) -> str:
        """
        Simulates a CPU-bound or blocking AI operation.
        This runs inside the ThreadPool.
        """
        import time
        time.sleep(1) # Simulate delay
        if "ERROR" in payload:
            raise ValueError("AI Engine Crash!")
        return f"Processed: {payload}"

    async def process_task(self, task: Task):
        """
        TODO: Implement the task lifecycle logic.
        1. Update status to RUNNING.
        2. Run self._sync_execute_ai_task in the executor using asyncio.to_thread 
           (or run_in_executor).
        3. If success: Update status to COMPLETED with result.
        4. If failure: Update status to FAILED with error message.
        """
        pass

    async def run(self):
        """
        TODO: Implement the polling loop.
        1. Infinite loop (while True).
        2. Poll for a batch of tasks.
        3. If no tasks, break (for simulation) or sleep.
        4. Run process_task for each task in the batch CONCURRENTLY (gather).
        """
        pass

async def main():
    mq = MockTaskQueue()
    worker = TaskWorker(mq)
    print("--- Starting Task Worker ---")
    await worker.run()
    print("--- All Tasks Processed ---")

if __name__ == "__main__":
    asyncio.run(main())
```
