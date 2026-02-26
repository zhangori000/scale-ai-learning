# Exercise 44: The Resource Hierarchy (Lazy Loading)

In `scale-agentex-python/src/agentex/_client.py`, you'll see many resources like `spans`, `tasks`, and `agents`. If the SDK initialized every resource class immediately, it would be slow and waste memory.

Instead, it uses the **Lazy Loading** pattern with `cached_property`.

## The Challenge
Implement a `MiniSDK` that:
1. Has two resources: `Tasks` and `Agents`.
2. These resources are **not** created when `MiniSDK` starts.
3. They are created only the **first time** you access them.
4. Subsequent accesses return the **same** instance (Singleton per Client).

## Starter Code
```python
import functools

class Tasks:
    def __init__(self, client):
        print("  [Init] Tasks Resource Created!")
        self.client = client

class Agents:
    def __init__(self, client):
        print("  [Init] Agents Resource Created!")
        self.client = client

class MiniSDK:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # TODO: Initialize resources lazily

    @property
    @functools.lru_cache() # Or implement your own caching logic
    def tasks(self):
        # TODO: Return a Tasks instance
        pass

    @property
    @functools.lru_cache()
    def agents(self):
        # TODO: Return an Agents instance
        pass

# --- Simulation ---
print("1. Creating Client...")
client = MiniSDK("secret-key")

print("
2. Accessing client.tasks for the first time...")
t1 = client.tasks

print("
3. Accessing client.tasks for the second time...")
t2 = client.tasks

# Check if it's the same instance (Lazy Singleton)
assert t1 is t2
print("
Validation Successful: Resource is cached!")
```
