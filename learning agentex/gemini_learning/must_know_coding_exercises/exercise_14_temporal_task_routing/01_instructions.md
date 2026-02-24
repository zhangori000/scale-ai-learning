# Exercise: Task Queues & Routing (Scaling)

In `scale-agentex`, you might have 1,000 different agents. You don't want a "Customer Support" worker trying to run a "1,000-page Legal Analysis" task.

Temporal uses **Task Queues** to route the right work to the right worker.

## The Goal
Build a `TemporalRouter` that takes a task and "pushes" it to the correct queue. Then, create two specialized Workers that "poll" their specific queues.

## Requirements
1.  **The Server:** A class with a dictionary of lists: `self.queues = {"legal": [], "support": []}`.
2.  **The Router (YOUR JOB):** Implement `TemporalRouter.send_task(queue_name, task_data)` to:
    *   Append the task to the correct list.
3.  **The Worker (YOUR JOB):** Implement `Worker.poll_and_execute()` to:
    *   Look at its assigned queue.
    *   If a task exists, "Process" it (print its data).
    *   If no task exists, print "Waiting for work...".
4.  **The Execution:** Send 2 legal tasks and 2 support tasks. Start the workers and show that they only "see" their own work.

## Starter Code
```python
import time

# --- 1. The Server (The Brain/Router) ---
class MockTemporalServer:
    def __init__(self):
        # Different 'Task Queues' for different specialties
        self.queues = {
            "legal-queue": [],
            "support-queue": []
        }

    def send_task(self, queue_name: str, task_data: str):
        # TODO: Add the task_data to the correct queue list
        pass

# --- 2. The Worker (The Specialty Process) ---
class SpecialtyWorker:
    def __init__(self, server: MockTemporalServer, queue_name: str):
        self.server = server
        self.queue_name = queue_name # "legal-queue" or "support-queue"

    def poll_and_execute(self):
        """
        Simulates the worker asking the server for a specific type of work.
        """
        # TODO: 
        # 1. Check if server.queues[self.queue_name] has any items.
        # 2. If it does, 'pop(0)' the task and print "Worker on {queue} processing: {task}".
        # 3. If not, print "No work found for {queue}".
        pass

# --- 3. Execution ---
server = MockTemporalServer()

# 1. Dispatch 4 tasks
print("--- Dispatching 4 Tasks ---")
server.send_task("legal-queue", "Audit Contract 1")
server.send_task("legal-queue", "Audit Contract 2")
server.send_task("support-queue", "Reset Password")
server.send_task("support-queue", "Track Refund")

# 2. Start the Legal Worker (should ONLY see legal tasks)
print("
--- Legal Worker Polling ---")
legal_worker = SpecialtyWorker(server, "legal-queue")
legal_worker.poll_and_execute()
legal_worker.poll_and_execute()
legal_worker.poll_and_execute() # Should be empty now

# 3. Start the Support Worker (should ONLY see support tasks)
print("
--- Support Worker Polling ---")
support_worker = SpecialtyWorker(server, "support-queue")
support_worker.poll_and_execute()
support_worker.poll_and_execute()
```
