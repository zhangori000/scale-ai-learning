# Solution: Build a Mock Temporal Architecture

This solution shows that Temporal isn't magic. It's just a **client-server application** where the "Worker" does the work and the "Server" keeps the "To-Do" list.

## The Implementation

```python
import time
import random

# --- 1. The Activities (User Code) ---
def activity_send_email(data):
    print(f"  [ACTIVITY] Executed: Sending email with: {data}")

def activity_charge_credit_card(data):
    # Simulate a "Flaky" activity that might fail (Temporal would retry this!)
    if random.random() < 0.2:
        print(f"  [ACTIVITY] CHARGE FAILED for: {data}")
        return
    print(f"  [ACTIVITY] Executed: Charged card: {data}")

# --- 2. The Server (The Brain/Database) ---
class MockTemporalServer:
    def __init__(self):
        # In a real Temporal Server (like in scale-agentex), this is in PostgreSQL/Cassandra
        self.task_queue = [] 
        self.history = []    # Completed tasks (persistence!)

    def add_workflow_to_queue(self, workflow_name, data):
        print(f"
[SERVER] New Workflow Started: {workflow_name}")
        self.task_queue.append({"type": "WORKFLOW", "name": workflow_name, "data": data})

    def poll_task(self):
        """
        The key piece: This is how the server 'hands off' work to a Worker.
        """
        if self.task_queue:
            task = self.task_queue.pop(0)
            print(f"[SERVER] Handing off task '{task['name']}' to a Worker...")
            return task
        return None

# --- 3. The Worker (The Polling Process) ---
class MockWorker:
    def __init__(self, server, activity_map):
        self.server = server
        self.activity_map = activity_map # Maps names to functions

    def run(self):
        """
        The Worker is just a loop that continuously asks the Server for work.
        """
        print("[WORKER] Started. Polling for tasks...")
        
        while True:
            # 1. Ask the server for a task (Poll)
            task = self.server.poll_task()
            
            if task:
                # 2. Extract info
                func_name = task.get("name")
                data = task.get("data")
                
                # 3. Lookup the actual code and RUN it
                if func_name in self.activity_map:
                    func = self.activity_map[func_name]
                    func(data)
                else:
                    print(f"  [WORKER] ERROR: No function found for '{func_name}'")
            else:
                # 4. If no work, back off (don't spam the server)
                print("[WORKER] No tasks found. Sleeping for 2s...")
                time.sleep(2)

# --- 4. Execution ---
server = MockTemporalServer()
# Map activity names to the actual functions
activities = {
    "send_email": activity_send_email,
    "charge_card": activity_charge_credit_card
}

# Create the worker
worker = MockWorker(server, activities)

# Add some work to the server (imagine these are coming from an API call)
server.add_workflow_to_queue("send_email", "User-123@example.com")
server.add_workflow_to_queue("charge_card", "Order-99")

# Start the worker
# In a real Temporal setup, you would have 10 workers running on 10 different servers!
try:
    worker.run()
except KeyboardInterrupt:
    print("
[WORKER] Stopped.")
```

### Key Takeaways from the Internal View

1.  **Decoupling:** The "Server" and the "Worker" can be on completely different sides of the planet. As long as they can talk over HTTP/gRPC, the work gets done.
2.  **Polling:** Notice how the `Worker` is the one asking the `Server` for work. This is safer than the server "pushing" work, because the Worker only asks when it's ready.
3.  **Persistence:** In a real server, if the `Worker` crashed after popping the task but before finishing, the `Server` would wait for a "timeout" and then **put the task back in the queue** for another worker. That's how Temporal guarantees the work is never lost!
