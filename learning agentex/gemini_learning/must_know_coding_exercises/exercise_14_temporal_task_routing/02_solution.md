# Solution: Task Queues & Routing (Scaling)

In `scale-agentex`, this pattern is essential for **Isolation**. If the Legal Agent's worker crashes, the Support Agent's worker is completely unaffected because they are listening to different Task Queues on the Temporal Server.

## The Implementation

```python
import time

# --- 1. The Server (The Brain/Router) ---
class MockTemporalServer:
    def __init__(self):
        # Different 'Task Queues' for different specialties
        # In real Temporal, these are implemented in a high-performance DB like Postgres.
        self.queues = {
            "legal-queue": [],
            "support-queue": []
        }

    def send_task(self, queue_name: str, task_data: str):
        """
        The key logic for 'routing' work to the correct specialty.
        """
        if queue_name in self.queues:
            print(f"  [SERVER] Task '{task_data}' added to: {queue_name}")
            self.queues[queue_name].append(task_data)
        else:
            print(f"  [SERVER] Error: Queue '{queue_name}' does not exist.")

# --- 2. The Worker (The Specialty Process) ---
class SpecialtyWorker:
    def __init__(self, server: MockTemporalServer, queue_name: str):
        self.server = server
        self.queue_name = queue_name # "legal-queue" or "support-queue"

    def poll_and_execute(self):
        """
        The key logic for a 'Worker' asking for a specific type of work.
        """
        # 1. Look at its assigned queue
        queue = self.server.queues.get(self.queue_name, [])
        
        # 2. If a task exists, 'pop' it from the list
        if queue:
            task = queue.pop(0)
            print(f"  [WORKER] SUCCESS: {self.queue_name.upper()} worker is now processing: '{task}'")
        else:
            # 3. If no task, wait for next poll
            print(f"  [WORKER] IDLE: No work found for '{self.queue_name}'. Waiting...")

# --- 3. Execution ---
server = MockTemporalServer()

# 1. Dispatch 4 tasks (simulated from a user clicking 'Send' in the UI)
print("--- Dispatching 4 Tasks ---")
server.send_task("legal-queue", "Audit Contract 1")
server.send_task("legal-queue", "Audit Contract 2")
server.send_task("support-queue", "Reset Password")
server.send_task("support-queue", "Track Refund")

# 2. Start the Legal Worker (should ONLY see legal tasks)
print("
--- Legal Worker Polling (Specialist) ---")
legal_worker = SpecialtyWorker(server, "legal-queue")

# The worker polls 3 times
legal_worker.poll_and_execute() # Processes Audit 1
legal_worker.poll_and_execute() # Processes Audit 2
legal_worker.poll_and_execute() # No more work

# 3. Start the Support Worker (should ONLY see support tasks)
print("
--- Support Worker Polling (Specialist) ---")
support_worker = SpecialtyWorker(server, "support-queue")

# The worker polls 2 times
support_worker.poll_and_execute() # Processes Reset Password
support_worker.poll_and_execute() # Processes Track Refund
```

### Key Takeaways from the Solution

1.  **Isolation:** The "Legal" worker never sees "Support" tasks. This means even if the Legal Agent is extremely slow, it won't "clog up" the queue for the fast Support Agent.
2.  **Scaling:** You can start **100 Legal Workers** if the firm is busy. They will all listen to the same `legal-queue` and automatically "share" the load without any extra code!
3.  **Why we use it for Agents:** In `scale-agentex`, every Agent you build can have its own Task Queue. This is the **most powerful scaling feature** of the platform—it allows you to scale from 1 agent to 1,000 agents without any centralized "bottleneck" in the worker logic.
