# Exercise 37: Limit Enforcement and Serialization Cost

Agentex has a strict **16MB limit** per state object. But here's the catch: the limit applies to the **JSON-serialized string**, not the Python dictionary in memory.

## The Challenge
Implement a `ValidatedStateStore` that:
1. Calculates the size of the state as if it were stored as JSON.
2. Rejects any state that exceeds a given limit (we'll use 1KB for this test).
3. **The Efficiency Goal**: Don't serialize the JSON twice (once for size check and once for saving).

## Starter Code
```python
import json

class ValidatedStateStore:
    def __init__(self, max_bytes: int = 1024):
        self.max_bytes = max_bytes
        self.storage = {}

    def save(self, key: str, data: dict):
        """
        TODO: 
        1. Convert 'data' to a JSON string.
        2. Check the byte-size of that string.
        3. If > self.max_bytes, raise ValueError.
        4. Otherwise, save the string to self.storage.
        """
        pass

# --- Simulation ---
store = ValidatedStateStore(max_bytes=100) # 100 byte limit

# OK
store.save("small", {"count": 1})

# TOO BIG
try:
    large_data = {"text": "A" * 200} # 200 chars > 100 bytes
    store.save("large", large_data)
except ValueError as e:
    print(f"Caught expected error: {e}")
```
