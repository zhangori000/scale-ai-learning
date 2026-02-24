# Solution: The Resilient Auth Cache (Negative Caching)

In `scale-agentex` (`src/api/authentication_cache.py`), this pattern is used to protect the database from being overwhelmed by authentication requests. It combines **Time-to-Live (TTL)** for freshness and **Least-Recently-Used (LRU)** for memory management.

## The Implementation

```python
import asyncio
import time
from collections import OrderedDict
from typing import Any, Optional

class ResilientCache:
    """
    An async-safe cache that supports time-based expiration 
    and size-based eviction (LRU).
    """
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        # OrderedDict maintains the order of insertion.
        # We use this to track which items were used 'Least Recently'.
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        # Ensure only one async task modifies the cache at a time.
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieves a value and refreshes its 'Recent' status.
        """
        async with self.lock:
            if key not in self.cache:
                return None

            value, expiry_time = self.cache[key]

            # 1. Check for Expiration
            if time.time() > expiry_time:
                print(f"  [CACHE] Key '{key}' expired. Evicting.")
                del self.cache[key]
                return None

            # 2. LRU Logic: Move the key to the 'End' (Most Recently Used)
            self.cache.move_to_end(key)
            return value

    async def set(self, key: str, value: Any, ttl: int = 300):
        """
        Stores a value with a specific Time-To-Live.
        """
        async with self.lock:
            # 1. LRU Eviction: If full and new key, remove the oldest (the first item)
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key, _ = self.cache.popitem(last=False)
                print(f"  [CACHE] Capacity reached. Evicting oldest key: '{oldest_key}'")

            # 2. Store the new value
            expiry_time = time.time() + ttl
            self.cache[key] = (value, expiry_time)
            
            # Ensure it's marked as the 'Most Recent'
            self.cache.move_to_end(key)
            print(f"  [CACHE] Saved '{key}' (Value: {value}, TTL: {ttl}s)")

# --- 3. Execution (The Simulation) ---
async def main():
    # Setup a cache that only holds 2 items
    cache = ResilientCache(max_size=2)

    print("--- Scenario 1: Negative Caching (Failure) ---")
    # We cache that 'key_bad' is INVALID (False) for 2 seconds.
    # This prevents us from checking the DB again for this hacker.
    await cache.set("key_bad", False, ttl=2)
    
    val = await cache.get("key_bad")
    print(f"  Is key valid? {val}") # Output: False

    print("
--- Scenario 2: Expiry ---")
    await asyncio.sleep(2.1)
    val_expired = await cache.get("key_bad")
    print(f"  Result after expiry: {val_expired}") # Output: None

    print("
--- Scenario 3: LRU Eviction ---")
    await cache.set("User_A", "Session_A", ttl=60)
    await cache.set("User_B", "Session_B", ttl=60)
    # Cache is now full: [User_A, User_B]
    
    print("  Adding User_C (should evict User_A)...")
    await cache.set("User_C", "Session_C", ttl=60)
    
    # User_A was the oldest, so it's gone.
    print(f"  User_A in cache? {await cache.get('User_A')}") # Output: None
    print(f"  User_B in cache? {await cache.get('User_B')}") # Output: Session_B

if __name__ == "__main__":
    asyncio.run(main())
```

### Key Takeaways from the Solution

1.  **OrderedDict Power:** `OrderedDict.move_to_end()` and `popitem(last=False)` are the perfect tools for building an LRU cache in Python.
2.  **Negative Caching:** By storing `False` as a value, you differentiate between "I don't know this key" (None) and "I KNOW this key is bad" (False). This is a vital security distinction.
3.  **Concurrency Safety:** In `scale-agentex`, multiple API requests might hit the cache at the same time. The `asyncio.Lock` ensures that the internal state of the dictionary never becomes corrupted.
4.  **Why this matters for Scale-Agentex:** Auth checks are the "Front Door." If the front door is slow because it checks the database every time, the whole house is slow. This cache makes the front door open instantly for valid users and slam shut instantly for known hackers.
