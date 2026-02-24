# Exercise: Build a Mock Temporal Architecture

To truly understand Temporal, you need to see that it is just a **state-tracking system**. The "magic" isn't in the code; it's in the **database (Server)** that remembers what to do next.

## The Goal
Build a simplified Temporal engine in pure Python.

## The 4 Pieces You'll Implement (Mocks)
1.  **TemporalServer (The Brain):** A class with a `task_queue` (a list). It stores tasks and waits for Workers to "poll" (ask) for them.
2.  **Activity (The Doer):** A simple Python function that does some "unreliable" work (printing a string).
3.  **Workflow (The Logic):** A simple list or dictionary that defines which Activities should be run and in what order.
4.  **Worker (The Process):** A `while True` loop that asks the Server for a task, looks up the function, runs it, and tells the Server it's done.

## The Task
Complete the `TemporalServer.poll_task()` and `Worker.run()` methods in the starter code.

## Starter Code
```python
import time
import random

# --- 1. The Activities (User Code) ---
def activity_send_email(data):
    print(f"  [ACTIVITY] Sending email with: {data}")

def activity_charge_credit_card(data):
    print(f"  [ACTIVITY] Charging card: {data}")

# --- 2. The Server (The Brain/Database) ---
class MockTemporalServer:
    def __init__(self):
        self.task_queue = [] # Tasks waiting to be done
        self.history = []    # Completed tasks (persistence!)

    def add_workflow_to_queue(self, workflow_name, data):
        print(f"[SERVER] New Workflow Started: {workflow_name}")
        self.task_queue.append({"type": "WORKFLOW", "name": workflow_name, "data": data})

    def poll_task(self):
        """
        TODO: 
        1. If task_queue is not empty, pop the first task.
        2. Return it. Otherwise return None.
        """
        pass

# --- 3. The Worker (The Polling Process) ---
class MockWorker:
    def __init__(self, server, activity_map):
        self.server = server
        self.activity_map = activity_map # Maps names to functions

    def run(self):
        print("[WORKER] Started. Polling for tasks...")
        """
        TODO:
        1. Loop forever.
        2. Call server.poll_task().
        3. If there's a task, find the function in activity_map and run it.
        4. If no task, sleep for 1 second and try again.
        """
        pass

# --- 4. Execution ---
server = MockTemporalServer()
# Map activity names to the actual functions
activities = {
    "send_email": activity_send_email,
    "charge_card": activity_charge_credit_card
}

worker = MockWorker(server, activities)

# Add some work to the server
server.add_workflow_to_queue("Onboarding", "User-123")
server.add_workflow_to_queue("Payment", "Order-99")

# Start the worker (In real life, this is a separate process!)
# worker.run() 
```

---
### When you are ready, check the solution file!
