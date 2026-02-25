# Solution: Scaling Architectures (Sync vs. Async vs. Temporal)

In this solution, you will see how `scale-agentex` "scales" by decoupling **execution** (the Worker) from **orchestration** (the Temporal Server).

## The Key Insight
- **Sync**: Scales by adding **Threads**. (Expensive, memory heavy).
- **Async**: Scales by adding **Event Loops**. (Cheap, but fragile. If the process dies, all tasks in memory DIE).
- **Temporal (Agentex)**: Scales by adding **Workers**. (Cheap, Reliable, and Stateless).

---

## The Solution Code

```python
import time
import asyncio
import random

# --- The Task ---
def transcribe_chunk(chunk_id):
    """Simulates a heavy AI task"""
    # Simulate work
    return f"Result for chunk {chunk_id}"

# --- 1. SYNC (The 'Slow' Way) ---
def process_sync(chunks):
    print("--- Starting SYNC Scaling ---")
    start = time.time()
    results = []
    for c in chunks:
        # Blocks the entire program. 10 * 0.1 = 1s
        time.sleep(0.1) 
        results.append(transcribe_chunk(c))
    print(f"DONE (Sync). Took {time.time() - start:.2f}s")

# --- 2. ASYNC (The 'Fast but Fragile' Way) ---
async def transcribe_chunk_async(chunk_id):
    await asyncio.sleep(0.1) # DOES NOT block others
    return transcribe_chunk(chunk_id)

async def process_async(chunks):
    print("
--- Starting ASYNC Scaling ---")
    start = time.time()
    # Runs all of them 'at once'. Total time = 0.1s
    results = await asyncio.gather(*[transcribe_chunk_async(c) for c in chunks])
    print(f"DONE (Async). Took {time.time() - start:.2f}s")

# --- 3. DURABLE (The 'Agentex' Way) ---
# How Agentex scales complex workflows.

class TemporalSimulation:
    def __init__(self, tasks):
        self.queue = tasks # This represents the "Temporal Server" task list
        self.processed_ids = [] # This is the "State" stored in the DB (History)

    def worker_run(self, fail_at=5):
        """Simulate a worker that processes until it 'fails'"""
        print(f"  [Worker 1] Starting tasks...")
        
        # Pull from the queue (The Server gives us tasks)
        for i, task_id in enumerate(list(self.queue)):
            if i >= fail_at:
                print(f"  [Worker 1] !!! CRASH !!! Process died.")
                break # Simulate a crash
            
            # Simulate work
            time.sleep(0.1)
            self.processed_ids.append(task_id) # STORE state in "history"
            print(f"  [Worker 1] Finished chunk {task_id}")

    def resume_worker(self):
        """Resume from where 'processed' left off"""
        # Temporal "Replays" the code. It sees we already did task 0-4.
        # It only asks the worker to do task 5-9.
        remaining_tasks = [t for t in self.queue if t not in self.processed_ids]
        
        print(f"
  [Worker 2] Resuming work. I see {len(remaining_tasks)} tasks remaining.")
        
        for task_id in remaining_tasks:
            time.sleep(0.1)
            self.processed_ids.append(task_id)
            print(f"  [Worker 2] Finished chunk {task_id}")
            
        print("  [Worker 2] All tasks complete!")

# --- 4. Execution ---
if __name__ == "__main__":
    tasks = list(range(10))
    
    # 1. Sync
    process_sync(tasks)
    
    # 2. Async
    asyncio.run(process_async(tasks))
    
    # 3. Durable (Temporal)
    print("
--- Starting DURABLE (Agentex) Scaling ---")
    
    # Initialize the "System"
    system = TemporalSimulation(tasks)
    
    # Worker 1 starts, but crashes after 5 tasks
    system.worker_run(fail_at=5)
    
    # Worker 2 starts up, sees the "State" in the database, and resumes!
    system.resume_worker()
```

---

## Why this matters for Agentex?

### 1. "Infrastructure is Abstracted"
In `scale-agentex`, a developer writes:
```python
await workflow.execute_activity(transcribe_chunk, args=[chunk_id])
```
The developer **does not** care if there is 1 worker or 10,000 workers. They don't care about memory or "threads." They just write the logic. The "Infrastructure" (Temporal) manages the queueing and distribution.

### 2. "Scaling" = More Workers
If the `transcribe_chunk` task is slow, you don't rewrite your code. You just start **10 more Docker containers** running the same worker code. They will all connect to the same Temporal server and pull tasks from the queue.

### 3. "Idempotency" is the Key
Notice in the `Durable` simulation: `Worker 2` checked `processed_ids` before starting. In Agentex, all workers must be **idempotent** (doing the same thing twice shouldn't break the system). This is how they handle scaling and retries safely.
