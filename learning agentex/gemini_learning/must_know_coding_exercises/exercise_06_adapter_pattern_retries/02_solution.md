# Solution: The Adapter Pattern with Retries (Resilience)

This pattern is why `scale-agentex` can handle thousands of LLM calls without crashing. It expects failure and builds **resiliency** into the foundational layers of the system.

## The Implementation

```python
import random
import time
from typing import Any

# --- 1. The "Unreliable" External World ---
# In a real app, this is 'httpx.get' or 'requests.get'.
def mock_httpx_call(url: str):
    """Simulates a flaky network call"""
    if random.random() < 0.5:
        print(f"  [NETWORK] Error: Failed to connect to {url}")
        raise ConnectionError("Network timeout")
    print(f"  [NETWORK] Success: 200 OK from {url}")
    return {"status": "ok", "data": "Agent Intelligence"}

# --- 2. The Adapter (The Gateway) ---
class HTTPGateway:
    def __init__(self, max_retries: int = 3, retry_delay: float = 0.5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def get(self, url: str) -> dict[str, Any]:
        """
        The key logic for 'resilient' API calls.
        """
        # We start with attempt 1
        attempts = 0
        
        while attempts < self.max_retries:
            try:
                # 1. Try the call
                return mock_httpx_call(url)
                
            except ConnectionError as e:
                # 2. Increment attempt counter
                attempts += 1
                
                # 3. Handle exhaustion of retries
                if attempts >= self.max_retries:
                    print(f"  [GATEWAY] Fatal: Maximum retries ({self.max_retries}) reached.")
                    raise e
                
                # 4. Wait before next attempt (Exponential backoff is even better!)
                print(f"  [GATEWAY] Warning: Attempt {attempts} failed. Retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)
                
        # This part should never be reached
        raise ConnectionError("Unknown Error in Gateway")

# --- 3. The Execution ---
# We configure our gateway once
gateway = HTTPGateway(max_retries=5, retry_delay=1.0)

print("--- Calling unreliable AI Service ---")
try:
    # Our service logic doesn't care about retries.
    # It just asks the gateway for the data.
    result = gateway.get("http://api.agentex.ai/v1/analyze")
    print(f"
Final Result: {result}")
except ConnectionError:
    print("
Final Result: System Failure after all retries.")
```

### Key Takeaways from the Solution:

1.  **Encapsulation:** The "Retry Logic" is hidden inside the `HTTPGateway`. Your "Service" code is now much cleaner because it doesn't have `try-except-retry` loops everywhere.
2.  **Backoff:** By sleeping between retries, we are being "polite" to the network. In real production apps (like Scale-Agentex), we often use "Exponential Backoff" (e.g., wait 1s, then 2s, then 4s).
3.  **Resilience:** This pattern is a fundamental requirement for **Level 5 Agents**. If the AI is autonomous, it must be able to heal itself from minor network glitches without human intervention.
