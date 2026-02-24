# Solution: The Task Concurrency Lock (Preventing Lost Updates)

In `scale-agentex`, this is known as an **Advisory Lock**. When multiple workers are streaming tokens for the same task, we use database-level locking (like `SELECT ... FOR UPDATE` in Postgres) to ensure that the message text doesn't become garbled or missing words.

## The Implementation

```python
import asyncio
import time

class TaskStore:
    def __init__(self):
        # The 'Resource' we are trying to protect
        self.message_text = ""
        # The 'Guard' that controls access to the resource
        self.lock = asyncio.Lock()

    async def update_WITHOUT_lock(self, chunk: str):
        """
        This method fails because multiple async tasks 'Read' the same empty string 
        before anyone has a chance to 'Write' their update.
        """
        current = self.message_text
        await asyncio.sleep(0.01) # Simulates DB delay
        self.message_text = current + chunk

    async def update_WITH_lock(self, chunk: str):
        """
        The key logic for 'Atomic' updates.
        The lock ensures that only ONE async task is inside this block at a time.
        """
        # 1. Ask for permission to enter the room
        # If someone else is in there, we wait (suspend) here.
        async with self.lock:
            # 2. We are now the ONLY task running this specific logic
            # READ
            current = self.message_text
            
            # WAIT
            await asyncio.sleep(0.01)
            
            # WRITE
            self.message_text = current + chunk
            
        # 3. Exit the room automatically (lock is released)

# --- 4. Execution (The Simulation) ---
async def main():
    # --- TEST 1: WITHOUT LOCK ---
    store_bad = TaskStore()
    print("--- Test 1: Running 10 parallel updates WITHOUT lock ---")
    
    # We fire off 10 requests at the EXACT same time
    tasks = [store_bad.update_WITHOUT_lock("X") for _ in range(10)]
    await asyncio.gather(*tasks)
    
    # Observe: Since all 10 read "" at the same time, they all wrote "X"
    # Result will likely be just "X" (Length 1) instead of "XXXXXXXXXX"
    print(f"  Final Text: {store_bad.message_text}")
    print(f"  Length: {len(store_bad.message_text)} / 10 (FAIL)")

    # --- TEST 2: WITH LOCK ---
    store_good = TaskStore()
    print("
--- Test 2: Running 10 parallel updates WITH lock ---")
    
    tasks = [store_good.update_WITH_lock("X") for _ in range(10)]
    await asyncio.gather(*tasks)
    
    # Observe: Even though we fired them in parallel, the Lock forced them 
    # to queue up and wait for their turn.
    print(f"  Final Text: {store_good.message_text}")
    print(f"  Length: {len(store_good.message_text)} / 10 (SUCCESS)")

if __name__ == "__main__":
    asyncio.run(main())
```

### Key Takeaways from the Solution:

1.  **Critical Section:** The code between `async with self.lock:` and the end of the block is the "Critical Section." You should keep this as short as possible to maintain high performance.
2.  **Sequential Execution:** While `asyncio` is great for concurrency, sometimes you *must* be sequential. The lock provides a "Serialized" gateway for parallel tasks.
3.  **Database Level:** In `scale-agentex`, because we have multiple backend servers, a simple `asyncio.Lock` (which only works on one server) isn't enough. We use **Postgres Advisory Locks** or `SELECT FOR UPDATE` to lock the row in the database so that Server A and Server B don't overwrite each other.
4.  **Why we use it for Agents:** Agents stream hundreds of small "deltas" per second. If two deltas for the same sentence arrive simultaneously, the sentence would be missing words without this locking mechanism. This ensures that the user always sees a perfect, complete transcript.
