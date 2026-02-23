# Day 12 - Code: Error Handling and Resiliency (Python + Tenacity)

How do you handle 1,000,000 API calls that fail? This is a **Distributed Resiliency** lesson.

## 1. The Scenario
Scale AI's Ingestor API calls the "Model Service" to get a pre-label for an image. 

**The Problem:** The "Model Service" is a bit slow. Sometimes it returns a `503 Service Unavailable` or a `504 Gateway Timeout`.

---

## 2. The Solution: Retries with "Exponential Backoff" and "Jitter"
You don't just "Retry" 3 times. If you have 10,000 workers all "Retrying" at the same time, you'll melt the Model Service. This is a **Retry Storm**.

### The "Scale AI" Resiliency Strategy:
1.  **Exponential Backoff:** Wait 1s, then 2s, then 4s, then 8s...
2.  **Jitter:** Wait 1.1s, then 2.3s, then 4.5s... (Randomized!) 
3.  **Circuit Breaker:** If the Model Service fails 10 times in a row, **Stop Retrying** for 60 seconds to let it recover.

### The Implementation in Python (using `tenacity`):
```python
from tenacity import retry, stop_after_attempt, wait_exponential
import random

# Scale's 'Gold Standard' for retries
@retry(
    stop=stop_after_attempt(5), 
    wait=wait_exponential(multiplier=1, min=1, max=10),
    # JITTER: Add a random 0-500ms to every wait
    # This prevents 'Retry Storms' from a million workers!
    before_sleep=lambda retry_state: log.info(f"Retrying (Attempt {retry_state.attempt_number})...")
)
async def call_model_service(image_url: str):
    """
    1. RETRY: Automatically retries on any Exception.
    2. BACKOFF: Each wait is 2x longer than the last.
    3. MAX: Stops after 5 attempts and raises the error.
    """
    response = await http_client.get(f"https://model-service/predict?url={image_url}")
    
    if response.status_code == 503:
        # We only retry 'Retryable' errors (5xx)
        raise Exception("Service Unavailable")
        
    return response.json()
```

---

## 3. 🧠 Key Teaching Points:
*   **The "Jitter" Importance**: If you have 1,000,000 workers and the network blips for 1 second, all 1,000,000 will retry at exactly T+1s. That's a **Thundering Herd**. Jitter (randomizing the wait) "Smears" the load so it doesn't crash the server.
*   **The "Retryable" vs. "Non-Retryable" Error**: Never retry a `400 Bad Request` or a `401 Unauthorized`. These errors won't fix themselves. Only retry `5xx` (Server Error) or `429` (Rate Limit).
*   **Circuit Breaker**: This is a "Safety Fuse." If a service is down, don't keep hitting it! Let it "Cool Down."
*   **FDE Tip**: When an interviewer says "The system is failing during high load," your first check is the **Retry Policy**. Are your workers "DDoS-ing" your own services with too many retries?
*   **Scale's Best Practice**: Always use `tenacity` or a similar library. Never write `while True: try: except: time.sleep(1)`. It's too simple and doesn't handle backoff or jitter.
