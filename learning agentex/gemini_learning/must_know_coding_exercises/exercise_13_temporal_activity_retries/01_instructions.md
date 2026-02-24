# Exercise: Activity Retries (Exponential Backoff)

In `scale-agentex`, the actual AI code is an **Activity**. Activities are "Mortal" because they talk to the outside world (like OpenAI). If OpenAI is down, the Activity fails.

Temporal solves this by **Retrying** the activity with **Exponential Backoff**.

## The Goal
Build an `ActivityWorker` that retries a failing function with an increasing delay (e.g., 1s, 2s, 4s).

## Requirements
1.  **Flaky Activity:** Create a function `unreliable_api()` that fails the first 2 times and succeeds the 3rd time.
2.  **The Retry Logic (YOUR JOB):** Implement `ActivityWorker.execute_with_retry()` to:
    *   Try the function.
    *   If it fails, print "Attempt X failed. Waiting Y seconds..."
    *   Wait for `base_delay * (2 ** attempts)` seconds (Exponential Backoff).
    *   Try again until success or `max_retries`.
3.  **The Result:** Print the total time it took to succeed.

## Starter Code
```python
import time
import random

# --- 1. The "Flaky" External Service ---
class UnreliableAgent:
    def __init__(self):
        self.fail_count = 0

    def call_ai(self, prompt: str):
        self.fail_count += 1
        if self.fail_count < 3:
            print(f"  [AGENT] Internal Server Error (Fail #{self.fail_count})")
            raise ConnectionError("Service Unavailable")
        
        print(f"  [AGENT] Success! Response for: '{prompt}'")
        return "AI Answer"

# --- 2. The Activity Worker (YOUR JOB) ---
class ActivityWorker:
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute_with_retry(self, func, *args):
        # TODO: 
        # 1. Loop while attempts < max_retries.
        # 2. Try to run func(*args).
        # 3. If it fails with ConnectionError, calculate delay: 2^attempts.
        # 4. time.sleep(delay).
        # 5. If successful, return the result.
        pass

# --- 3. Execution ---
agent = UnreliableAgent()
worker = ActivityWorker(max_retries=5, base_delay=1.0)

print("--- Starting Activity: Call Agent ---")
start_time = time.time()

try:
    result = worker.execute_with_retry(agent.call_ai, "What is Agentex?")
    end_time = time.time()
    print(f"
Final Result: {result}")
    print(f"Total time elapsed: {end_time - start_time:.2f}s")
except ConnectionError:
    print("
Final Result: Task Failed permanently after 5 retries.")
```
