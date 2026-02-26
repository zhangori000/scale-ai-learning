# Exercise 38: Optimistic Concurrency (State Versions)

In a distributed system, two processes might try to update the same State at the same time:
1. **Process A** reads State (v1).
2. **Process B** reads State (v1).
3. **Process A** saves updated State (v2).
4. **Process B** saves updated State (v2), **overwriting** Process A's changes! 

This is called the **"Lost Update"** problem. Agentex prevents this using state versions.

## The Challenge
Implement a `ConcurrentStateStore`.
1. Every state object must have a `version` number.
2. `save(key, data, expected_version)`:
   - If the current version in the store matches `expected_version`, increment the version and save.
   - If the version has already changed, raise a `ConcurrencyError`.

## Starter Code
```python
class ConcurrencyError(Exception): pass

class ConcurrentStateStore:
    def __init__(self):
        # Maps key -> {"data": dict, "version": int}
        self.storage = {}

    def get(self, key: str):
        return self.storage.get(key, {"data": {}, "version": 0})

    def save(self, key: str, data: dict, expected_version: int):
        """
        TODO: 
        1. Look up existing record.
        2. If current version != expected_version, raise ConcurrencyError.
        3. Save new data and increment version.
        """
        pass

# --- Simulation ---
store = ConcurrentStateStore()

# Both processes read the state at the same time
state_a = store.get("task_1") # version: 0
state_b = store.get("task_1") # version: 0

# Process A finishes first and saves
store.save("task_1", {"msg": "A won"}, expected_version=0)
print("Process A saved successfully.")

# Process B tries to save using the OLD version
try:
    store.save("task_1", {"msg": "B won"}, expected_version=0)
except ConcurrencyError:
    print("Caught Process B's Concurrency Error! (State was modified by A)")
```
