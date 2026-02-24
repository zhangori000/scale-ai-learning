# Exercise: The Adapter Pattern with Retries (Resilience)

In `scale-agentex` (`src/adapters/http/adapter_httpx.py`), the platform never calls `httpx` directly in its services. It uses an **Adapter** (a Gateway).

Why? Because the internet is **unreliable**. If an LLM call fails, we want to **retry** it automatically.

## The Goal
Create a `HTTPGateway` class that wraps a raw HTTP library and implements a "Retry" mechanism.

## Requirements
1.  **Gateway Interface:** Define a `Gateway` class with a `get(url: str)` method.
2.  **Mock Success/Failure:** Create a function `mock_httpx_call(url: str)` that:
    *   Fails 50% of the time (`random.random() < 0.5`).
    *   Succeeds the other 50%.
3.  **The Adapter (YOUR JOB):** Implement the `HTTPGateway.get()` method to:
    *   Try the call.
    *   If it fails, **retry** it up to 3 times.
    *   Sleep for 0.5s between retries.
    *   Only raise an error if ALL retries fail.

## Starter Code
```python
import random
import time
from typing import Any

# --- 1. The "Unreliable" External World ---
def mock_httpx_call(url: str):
    """Simulates a flaky network call"""
    if random.random() < 0.5:
        print(f"  [NETWORK] Error: Failed to connect to {url}")
        raise ConnectionError("Network timeout")
    print(f"  [NETWORK] Success: 200 OK from {url}")
    return {"status": "ok", "data": "Agent Intelligence"}

# --- 2. The Adapter (The Gateway) ---
class HTTPGateway:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def get(self, url: str) -> dict[str, Any]:
        """
        TODO: 
        1. Try to call mock_httpx_call(url).
        2. If it raises ConnectionError, increment retry counter.
        3. Sleep for 0.5s.
        4. Try again.
        5. If all 3 fail, raise the final error.
        """
        pass

# --- 3. The Execution ---
gateway = HTTPGateway(max_retries=3)

print("--- Calling unreliable AI Service ---")
try:
    result = gateway.get("http://api.agentex.ai/v1/analyze")
    print(f"
Final Result: {result}")
except ConnectionError:
    print("
Final Result: System Failure after all retries.")
```
