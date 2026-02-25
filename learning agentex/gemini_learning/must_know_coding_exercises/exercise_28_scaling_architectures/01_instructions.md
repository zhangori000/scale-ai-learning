# Exercise 28: Scaling Architectures (Sync vs. Async vs. Temporal)

In `scale-agentex`, "scaling" isn't just about adding more RAM. It's about how the code handles **thousands of events** at once without dropping any.

## The Goal
Imagine a "Transcription Task" (e.g., transcribing a 1-hour audio file).
We need to process **1,000 tasks** at the same time.

## 3 Different "Scaling" Strategies

### 1. The "Old Way" (Sync / Threads)
- **Mechanism**: Each task gets a dedicated "thread."
- **Problem**: 1,000 threads = 1,000 separate "workers" in the OS. This eats all your RAM and crashes the server.
- **Result**: Slow and expensive.

### 2. The "Base Way" (Asyncio / Event Loop)
- **Mechanism**: One single "thread" (The Event Loop) manages all 1,000 tasks.
- **Benefit**: Super fast! While one task is waiting for a database, the Event Loop starts the next one.
- **Problem**: If the server crashes, all 1,000 tasks are LOST forever. No "Infrastructure" to remember them.

### 3. The "Agentex Way" (Temporal / Durable Execution)
- **Mechanism**: Code runs on "Workers." The "Infrastructure" (Temporal) manages a **Persistent Queue**.
- **Benefit**:
    - **Scaling**: If you need to handle 10,000 more tasks, you just start more "Workers" on any server in the world.
    - **Reliability**: If a Worker crashes mid-transcription, Temporal **REPLAYS** the code on a new worker from the exact point it stopped.
    - **Abstracted Infra**: You write code like it's local, but Temporal scales it like a massive distributed system.

## Your Task: "The Orchestrator"
Build a simulation that shows these 3 patterns.

### Requirements
1.  **Sync Processor**: Processes tasks one by one (Simulate `time.sleep`).
2.  **Async Processor**: Processes tasks concurrently (Simulate `asyncio.gather`).
3.  **Durable Processor**: Simulates a "Temporal" worker that can "recover" if it crashes.

## Starter Code
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
        # Blocks the entire program
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
    # Runs all of them 'at once'
    results = await asyncio.gather(*[transcribe_chunk_async(c) for c in chunks])
    print(f"DONE (Async). Took {time.time() - start:.2f}s")

# --- 3. DURABLE (The 'Agentex' Way) ---
# Your Job: Simulate a "Temporal Worker" that:
# 1. Pulls tasks from a "Persistent Queue"
# 2. Tracks its own "Progress" (State)
# 3. Can resume from a crash

class TemporalSimulation:
    def __init__(self):
        self.queue = list(range(10)) # 10 chunks to transcribe
        self.processed = [] # This is the "State" Temporal stores for us

    def worker_run(self, fail_at=5):
        """TODO: Simulate a worker that processes until it 'fails'"""
        pass

    def resume_worker(self):
        """TODO: Resume from where 'processed' left off"""
        pass

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
    # TODO: Execute your Temporal Simulation here
```
