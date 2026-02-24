# Exercise: The Background Job Tracker (Task Registry)

In `scale-agentex`, when an agent is "Thinking," it's running as an asynchronous task in the background. The platform needs a way to "Find" that specific task if the user clicks **Cancel**.

## The Goal
Create a `TaskTracker` class that can start, track, and stop background async jobs by a unique ID.

## Requirements
1.  **Tracker Class:** Create a `TaskTracker` with a `self.active_tasks` dictionary (`{task_id: asyncio.Task}`).
2.  **Start Method:** `start_job(task_id: str, coro: Coroutine)`:
    *   Wraps the coroutine in `asyncio.create_task()`.
    *   Stores it in the dictionary.
    *   Adds a "callback" so that when the task finishes, it removes itself from the dictionary.
3.  **Cancel Method:** `cancel_job(task_id: str)`:
    *   Finds the task in the dictionary.
    *   Calls `.cancel()`.
4.  **The Job:** Create a simple `async def long_thinking_process()` that:
    *   Sleeps for 10 seconds.
    *   Prints "Thinking complete!"
    *   **Crucial:** Catches `asyncio.CancelledError` and prints "Cleaning up resources...".

## Starter Code
```python
import asyncio
import uuid
from typing import Dict, Coroutine

# --- 1. The Job (Simulates an Agent's Thought Process) ---
async def agent_thinking(task_id: str):
    try:
        print(f"  [AGENT {task_id}] Starting deep thought...")
        for i in range(10):
            await asyncio.sleep(1) # Simulating work
            print(f"  [AGENT {task_id}] Step {i+1}/10 complete...")
        print(f"  [AGENT {task_id}] Success: Thought finished!")
    except asyncio.CancelledError:
        # TODO: Handle the "Stop" signal
        print(f"  [AGENT {task_id}] CRITICAL: Received Cancel Signal! Cleaning up...")
        raise # Always re-raise CancelledError!

# --- 2. The Tracker (The Platform's Registry) ---
class TaskTracker:
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}

    def start_job(self, task_id: str, coro: Coroutine):
        # TODO: 
        # 1. Create the task using asyncio.create_task(coro)
        # 2. Store it in self.active_tasks
        # 3. (Advanced) Add a 'done_callback' to remove it when finished
        pass

    def cancel_job(self, task_id: str):
        # TODO: Find and cancel the task
        pass

# --- 3. The Execution ---
async def main():
    tracker = TaskTracker()
    t_id = "TASK-123"

    # 1. Start a 10-second job
    tracker.start_job(t_id, agent_thinking(t_id))
    
    # 2. Let it run for 3 seconds
    await asyncio.sleep(3)
    
    # 3. Simulate User clicking "CANCEL"
    print("
[USER] Clicks 'Cancel' in UI...")
    tracker.cancel_job(t_id)
    
    # 4. Wait a bit to see the cleanup
    await asyncio.sleep(1)
    print(f"Active tasks remaining: {len(tracker.active_tasks)}")

if __name__ == "__main__":
    asyncio.run(main())
```
