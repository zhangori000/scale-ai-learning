# Solution: The Background Job Tracker (Task Registry)

This solution demonstrates the "Durable Control" pattern in `scale-agentex`. It ensures that every background job is tracked and can be safely terminated without leaking resources.

## The Implementation

```python
import asyncio
import uuid
from typing import Dict, Coroutine, Callable

# --- 1. The Job (Simulates an Agent's Thought Process) ---
async def agent_thinking(task_id: str):
    try:
        print(f"  [AGENT {task_id}] Starting deep thought...")
        for i in range(10):
            await asyncio.sleep(1) # Simulating work
            print(f"  [AGENT {task_id}] Step {i+1}/10 complete...")
        print(f"  [AGENT {task_id}] Success: Thought finished!")
    except asyncio.CancelledError:
        # Handling the "Stop" signal
        print(f"  [AGENT {task_id}] CRITICAL: Received Cancel Signal! Cleaning up...")
        # CRITICAL: Always re-raise CancelledError to ensure the task finishes
        raise

# --- 2. The Tracker (The Platform's Registry) ---
class TaskTracker:
    def __init__(self):
        # Maps task_id to the actual running asyncio.Task
        self.active_tasks: Dict[str, asyncio.Task] = {}

    def start_job(self, task_id: str, coro: Coroutine):
        """
        Starts a coroutine in the background and tracks it.
        """
        # 1. Create the task using asyncio.create_task
        task = asyncio.create_task(coro)
        
        # 2. Store it in our registry
        self.active_tasks[task_id] = task
        print(f"[TRACKER] Registered task: {task_id}")

        # 3. Add a callback to remove the task from the registry once it finishes
        # This prevents memory leaks!
        def remove_from_registry(finished_task):
            print(f"[TRACKER] Task {task_id} finished/cancelled. Removing from registry...")
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

        task.add_done_callback(remove_from_registry)

    def cancel_job(self, task_id: str):
        """
        Finds a running task and stops it immediately.
        """
        if task_id in self.active_tasks:
            print(f"[TRACKER] Cancelling task: {task_id}")
            task = self.active_tasks[task_id]
            
            # This throws a 'CancelledError' inside the running task!
            task.cancel()
        else:
            print(f"[TRACKER] Warning: No task found with ID: {task_id}")

# --- 3. The Execution ---
async def main():
    tracker = TaskTracker()
    t_id = "TASK-123"

    # 1. Start a long-running job in the background
    # Note: We don't 'await' start_job, it runs in the background.
    tracker.start_job(t_id, agent_thinking(t_id))
    
    # 2. Let it run for 3 seconds
    await asyncio.sleep(3)
    
    # 3. Simulate the user clicking "CANCEL" in the UI
    print("
[USER] Clicks 'Cancel' in UI...")
    tracker.cancel_job(t_id)
    
    # 4. Wait for the cleanup to finish
    # We must yield control to the event loop so the task can catch the CancelledError.
    await asyncio.sleep(0.5)
    print(f"
Active tasks remaining: {len(tracker.active_tasks)}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Key Takeaways from the Solution

1.  **Callbacks:** The `add_done_callback` is crucial for production systems. Without it, your `active_tasks` dictionary would grow forever, eventually crashing your server with a memory leak.
2.  **CancelledError:** You MUST catch this if your task is doing something important (like holding a database lock or writing to a file) to ensure it cleans up before dying.
3.  **The Event Loop:** `task.cancel()` doesn't kill the code immediately like a hammer. It "requests" the task to stop at the next `await` point. This is much safer than traditional threading!
4.  **Why we use it for Agents:** If an LLM starts "looping" or talking too long, the user needs to be able to stop it to save tokens and time. This pattern is how `scale-agentex` implements the "Stop" button.
