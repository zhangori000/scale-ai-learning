# Solution: Activity Retries (Exponential Backoff)

This pattern is a key feature of Temporal, implemented in `scale-agentex` to ensure that flaky Agent calls don't crash the entire platform.

## The Implementation

```python
import time
import random

# --- 1. The "Flaky" External Service ---
class UnreliableAgent:
    def __init__(self):
        # This simulates an agent that is 'busy' at first but eventually recovers
        self.attempts_to_fail = 2
        self.current_attempt = 0

    def call_ai(self, prompt: str):
        self.current_attempt += 1
        if self.current_attempt <= self.attempts_to_fail:
            # Simulate a real 503 error from an LLM API
            print(f"  [AGENT] HTTP 503 Service Unavailable (Attempt #{self.current_attempt})")
            raise ConnectionError("LLM API overloaded")
        
        # After 2 failures, it succeeds!
        print(f"  [AGENT] HTTP 200 OK! Response for: '{prompt}'")
        return "The weather is 72°F and sunny."

# --- 2. The Activity Worker (The Implementation) ---
class ActivityWorker:
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def execute_with_retry(self, func, *args):
        """
        The key logic for 'durable' execution:
        If at first you don't succeed, wait longer and longer and try again.
        """
        attempts = 0
        
        while attempts < self.max_retries:
            try:
                # 1. Try to run the function
                return func(*args)
                
            except ConnectionError as e:
                # 2. Increment attempt counter
                attempts += 1
                
                # 3. Handle exhaustion of retries
                if attempts >= self.max_retries:
                    print(f"  [WORKER] Fatal: Maximum retries ({self.max_retries}) reached.")
                    raise e
                
                # 4. Calculate Exponential Backoff Delay
                # Delay = base_delay * (2 ^ attempts)
                # This makes the server wait: 1s, 2s, 4s, 8s, 16s...
                delay = self.base_delay * (2 ** (attempts - 1))
                
                print(f"  [WORKER] Warning: Attempt {attempts} failed. Waiting {delay}s before retry...")
                time.sleep(delay)
                
        # This part should never be reached
        raise ConnectionError("Unknown Error in ActivityWorker")

# --- 3. Execution ---
agent = UnreliableAgent()
worker = ActivityWorker(max_retries=5, base_delay=1.0)

print("--- Starting Activity: Call Agent ---")
start_time = time.time()

try:
    # Our service code just calls this and knows it's resilient
    result = worker.execute_with_retry(agent.call_ai, "What is the weather?")
    end_time = time.time()
    print(f"
Final Result: {result}")
    print(f"Total time elapsed: {end_time - start_time:.2f}s")
    # Observe: It should take around 3s total (1s + 2s sleep)
except ConnectionError:
    print("
Final Result: Task Failed permanently after 5 retries.")
```

### Key Takeaways from the Solution:

1.  **Fault Tolerance:** The `ActivityWorker` ensures that temporary network glitches or LLM rate limits don't stop the overall task.
2.  **Wait and See:** Exponential backoff is the industry standard for retrying APIs. It prevents "DDOS-ing" a service that is already struggling.
3.  **The Temporal Magic:** In a real `scale-agentex` setup, Temporal handles this **across multiple servers**. If Worker A dies during the sleep, Worker B will pick up the task and retry it after the delay.
4.  **Why we use it for Agents:** Agents often call 5 different APIs (OpenAI, Google Search, Postgres). If any of them are slow or flaky, the Platform must handle the retries automatically without losing the user's task.
