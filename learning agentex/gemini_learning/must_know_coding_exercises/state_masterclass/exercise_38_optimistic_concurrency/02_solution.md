# Solution: Optimistic Concurrency (State Versions)

This is the standard way to handle "Shared State" in distributed systems without using slow, expensive "Locks".

## The Solution

```python
class ConcurrencyError(Exception): pass

class ConcurrentStateStore:
    def __init__(self):
        self.storage = {}

    def get(self, key: str):
        return self.storage.get(key, {"data": {}, "version": 0})

    def save(self, key: str, data: dict, expected_version: int):
        current_record = self.get(key)
        current_version = current_record["version"]
        
        # 1. Check for collision
        if current_version != expected_version:
            raise ConcurrencyError(
                f"Version mismatch! Expected {expected_version}, but DB has {current_version}."
            )
        
        # 2. Atomic Update (Increment version)
        new_version = current_version + 1
        self.storage[key] = {"data": data, "version": new_version}
        print(f"  [DB] Updated {key} to version {new_version}")
```

## Why this is Agentex-style:
1. **The "Compare-and-Swap" Pattern**: Even if Agentex uses MongoDB's atomic operators (like `$set` with a query filter), the logic is the same: *"Only update if the current state is exactly what I think it is."*
2. **Reliability**: If an Agent crashes and retries, it might try to resend an old state update. This version check ensures the "Late Arriving" update doesn't corrupt the fresh data written by the retry.
3. **Decoupled Workers**: Multiple Temporal Workers can attempt to update the same task state; versioning ensures they coordinate safely.
