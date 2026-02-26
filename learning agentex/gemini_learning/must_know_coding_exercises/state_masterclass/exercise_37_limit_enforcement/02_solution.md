# Solution: Limit Enforcement and Serialization Cost

Calculating size using `json.dumps()` is the most accurate way to mirror the database's perspective.

## The Solution

```python
import json

class ValidatedStateStore:
    def __init__(self, max_bytes: int = 1024):
        self.max_bytes = max_bytes
        self.storage = {}

    def save(self, key: str, data: dict):
        # Serialize to string once
        serialized_data = json.dumps(data)
        
        # Calculate size in bytes (UTF-8)
        byte_size = len(serialized_data.encode('utf-8'))
        
        if byte_size > self.max_bytes:
            raise ValueError(f"State too large: {byte_size} bytes (Max: {self.max_bytes})")
            
        # Store the serialized version (simulating a DB write)
        self.storage[key] = serialized_data
        print(f"  [Store] Saved {key} ({byte_size} bytes)")
```

## Why this is Agentex-style:
1. **The 16MB Wall**: MongoDB's BSON document limit is 16MB. If Agentex didn't enforce this at the application layer, the database would throw a fatal error mid-request, potentially causing data corruption or lost progress.
2. **UTF-8 Awareness**: In modern Python, `len("😀")` is 1, but its byte size in UTF-8 is 4. Agentex must track the **byte size** because that's what fills up disk space.
3. **Early Failure**: By checking the size *before* sending the data to the DB, Agentex can return a clean `400 Bad Request` to the Agent instead of a `500 Internal Server Error`.
