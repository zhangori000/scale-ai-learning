# Exercise: The Task Concurrency Lock (Preventing Lost Updates)

In `scale-agentex`, a task can receive many streaming "deltas" (chunks of text) very quickly. If two chunks (e.g., "Hello" and "World") arrive at the same millisecond, and both try to "append" to the database, a **Race Condition** happens.

## The Problem (The "Lost Update")
1.  **Process A** reads the text: `"He"`
2.  **Process B** reads the text: `"He"`
3.  **Process A** appends `"llo"` and saves: `"Hello"`
4.  **Process B** appends `"llo"` and saves: `"Hello"`
5.  **OH NO!** We lost one of the "llo" chunks because Process B overwrote Process A.

## The Goal
Build a `TaskStore` that uses an `asyncio.Lock` to ensure that every update to a message happens one at a time.

## Requirements
1.  **The Store:** Create a `TaskStore` with `self.message_text = ""` and `self.lock = asyncio.Lock()`.
2.  **The Flaky Update:** Create a method `update_message(chunk: str)` that:
    *   Reads the current text.
    *   Simulates a tiny delay (`await asyncio.sleep(0.01)`).
    *   Appends the new chunk and saves it.
3.  **The Fix (YOUR JOB):** Implement the same logic but wrap it in `async with self.lock:`.
4.  **The Test:** Run 10 updates in parallel (using `asyncio.gather`) and show that without the lock, you lose data, but with the lock, the final text is perfect.

## Starter Code
```python
import asyncio
import time

class TaskStore:
    def __init__(self):
        self.message_text = ""
        self.lock = asyncio.Lock()

    async def update_WITHOUT_lock(self, chunk: str):
        """
        This method will FAIL the test because it doesn't protect the 'Read-Modify-Write' cycle.
        """
        # 1. READ
        current = self.message_text
        # 2. WAIT (Simulate database latency)
        await asyncio.sleep(0.01)
        # 3. WRITE
        self.message_text = current + chunk

    async def update_WITH_lock(self, chunk: str):
        """
        TODO: 
        1. Use 'async with self.lock:' to wrap the logic.
        2. Perform the same Read-Modify-Write cycle.
        """
        pass

# --- 4. Execution (The Simulation) ---
async def main():
    # --- TEST 1: WITHOUT LOCK ---
    store_bad = TaskStore()
    print("--- Test 1: Running 10 updates WITHOUT lock ---")
    # We send 'X' 10 times. Expected length: 10
    tasks = [store_bad.update_WITHOUT_lock("X") for _ in range(10)]
    await asyncio.gather(*tasks)
    print(f"  Final Text: {store_bad.message_text} (Length: {len(store_bad.message_text)})")

    # --- TEST 2: WITH LOCK ---
    store_good = TaskStore()
    print("
--- Test 2: Running 10 updates WITH lock ---")
    tasks = [store_good.update_WITH_lock("X") for _ in range(10)]
    await asyncio.gather(*tasks)
    print(f"  Final Text: {store_good.message_text} (Length: {len(store_good.message_text)})")

if __name__ == "__main__":
    asyncio.run(main())
```
