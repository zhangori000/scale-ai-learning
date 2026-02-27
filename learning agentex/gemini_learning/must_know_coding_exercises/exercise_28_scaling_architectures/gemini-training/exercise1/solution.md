# Exercise 1: Reference Solution

```python
import time
import random
from collections import deque

class TemporalServer:
    def __init__(self):
        self.queue = deque()
        self.history = {} # taskId -> result

    def submit_task(self, task_id, data):
        # API Level Idempotency
        if task_id in self.history:
            return "ALREADY_DONE"
        self.queue.append((task_id, data))
        return "SUBMITTED"

    def poll_task(self):
        if not self.queue:
            return None
        return self.queue.popleft()

    def record_success(self, task_id, result):
        self.history[task_id] = result

class Worker:
    def __init__(self, worker_id, server):
        self.worker_id = worker_id
        self.server = server
        self.active = True

    def poll_and_process(self):
        if not self.active:
            return False
        
        task = self.server.poll_task()
        if not task:
            return False
        
        task_id, data = task
        
        # 1. Check if already done (Idempotency)
        if task_id in self.server.history:
            print(f"  [Worker {self.worker_id}] Task {task_id} already in history. Skipping.")
            return True
        
        # 2. Simulate heavy work
        print(f"  [Worker {self.worker_id}] Processing {task_id}: {data}...")
        time.sleep(0.05)
        
        # 3. Random Failure mid-processing (Scaling crash)
        if random.random() < 0.1: # 10% chance to crash
            print(f"  [Worker {self.worker_id}] !!! CRASHED !!! during task {task_id}")
            # Task is LOST from the queue but NOT in history.
            # In real Temporal, the timeout would trigger a re-enqueue.
            # Here, we re-enqueue manually to simulate Temporal's "Retry" behavior.
            self.server.submit_task(task_id, data)
            self.active = False # Worker dies
            return False

        # 4. Success: Record to Server (Persistent Layer)
        result = f"DONE_{data}"
        self.server.record_success(task_id, result)
        print(f"  [Worker {self.worker_id}] Finished {task_id}")
        return True

def run_scaling_simulation():
    server = TemporalServer()
    
    # 1. Load initial tasks
    print("--- Submitting Tasks ---")
    for i in range(15):
        server.submit_task(f"T{i}", f"Data_{i}")
    
    # 2. Start with 2 Workers
    workers = [Worker(1, server), Worker(2, server)]
    
    print("
--- Processing with 2 Workers ---")
    step = 0
    while server.queue or any(w.active for w in workers):
        step += 1
        
        # Scaling Event: Scale Up at step 5
        if step == 5:
            print("
[Scaling UP] Adding Worker 3 and 4...")
            workers.append(Worker(3, server))
            workers.append(Worker(4, server))
        
        # All active workers process one task
        active_workers = [w for w in workers if w.active]
        if not active_workers and server.queue:
            print("
[System Alert] No active workers! Spawning recovery worker...")
            workers.append(Worker(step + 10, server))
            continue
            
        if not server.queue:
            break
            
        for w in active_workers:
            w.poll_and_process()

    print(f"
--- Simulation Complete ---")
    print(f"Tasks in history: {len(server.history)} / 15")
    print(f"Total Workers Spawned: {len(workers)}")

if __name__ == "__main__":
    run_scaling_simulation()
```

## Why this matches Agentex behavior
- **Independent worker scaling**: Workers can be added or removed mid-process without losing data because the queue and history are in the "Server" (Temporal).
- **Idempotency**: The `if task_id in self.server.history` check ensures that even if a worker crashes after finishing but before committing, the next worker handles it correctly.
- **Durable execution**: The system is resilient to individual node failures.

## Key Takeaway for Agentex Developers
When you use `await workflow.execute_activity(...)`, you are delegating the responsibility for "scaling" and "retrying" to the Temporal infrastructure. Your code remains clean and focused on business logic.
