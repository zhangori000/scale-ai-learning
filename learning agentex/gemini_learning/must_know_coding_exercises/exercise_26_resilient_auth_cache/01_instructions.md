# Exercise: The Resilient Auth Cache (Negative Caching)

In `scale-agentex` (`src/api/authentication_cache.py`), the platform uses a specialized cache to store authentication results. 

One of the most difficult problems in security is **Negative Caching**. If a hacker tries a million invalid API keys, you don't want to check your database a million times. You want to "Cache the Failure" so you can reject them instantly for the next 5 minutes.

## The Goal
Build an `AsyncTTLCache` that supports **LRU Eviction** (Least Recently Used) and **Time-Based Expiration**.

## Requirements
1.  **Storage:** Use an `OrderedDict` to track the order of items (for LRU).
2.  **The Entry:** Store values as a tuple: `(value, expiry_time)`.
3.  **Get Method:** `async def get(key)`:
    *   If key is missing, return `None`.
    *   If key exists but is expired, delete it and return `None`.
    *   If key exists and is valid, **move it to the end** (making it the Most Recently Used) and return value.
4.  **Set Method:** `async def set(key, value, ttl)`:
    *   If the cache is full (e.g., > 3 items), delete the **first** item (the Least Recently Used).
    *   Store the new value with `time.time() + ttl`.
5.  **Thread Safety:** Wrap all logic in `async with self.lock:`.

## Starter Code
```python
import asyncio
import time
from collections import OrderedDict
from typing import Any, Optional

class ResilientCache:
    def __init__(self, max_size: int = 3):
        self.max_size = max_size
        self.cache = OrderedDict() # key -> (value, expiry)
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        # TODO: 
        # 1. Use lock.
        # 2. Check existence and expiry.
        # 3. If valid, move to end (MRU).
        pass

    async def set(self, key: str, value: Any, ttl: int = 5):
        # TODO:
        # 1. Use lock.
        # 2. If full and key is new, pop oldest (index 0).
        # 3. Store with expiry.
        pass

# --- 3. Execution (The Simulation) ---
async def main():
    cache = ResilientCache(max_size=2) # Small size to test LRU

    print("--- Step 1: Negative Caching (Caching a Failure) ---")
    # We cache that 'key_123' is INVALID (False) for 2 seconds
    await cache.set("key_123", False, ttl=2)
    
    val = await cache.get("key_123")
    print(f"  Result for key_123 (immediately): {val}") # Expected: False

    print("
--- Step 2: Testing Expiry ---")
    await asyncio.sleep(2.1)
    val_expired = await cache.get("key_123")
    print(f"  Result for key_123 (after 2s): {val_expired}") # Expected: None

    print("
--- Step 3: Testing LRU Eviction ---")
    await cache.set("A", "Apple", ttl=10)
    await cache.set("B", "Banana", ttl=10)
    # Cache is now full [A, B]
    
    await cache.set("C", "Cherry", ttl=10)
    # Cache was full, 'A' should be evicted! [B, C]
    
    print(f"  Is 'A' still in cache? {await cache.get('A')}") # Expected: None
    print(f"  Is 'B' still in cache? {await cache.get('B')}") # Expected: Banana

if __name__ == "__main__":
    asyncio.run(main())
```
