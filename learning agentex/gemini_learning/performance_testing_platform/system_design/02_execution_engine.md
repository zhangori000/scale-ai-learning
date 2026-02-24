# Chapter 2: The Execution Engine (The "Gatling" Core)

To build a load generator, you must master the **Event Loop** and **Concurrency Models**.

## 1. Threading vs. AsyncIO
*   **Threading (Java/Gatling):** Uses OS threads. Good for CPU-bound tasks, but expensive (memory overhead per thread). Hard to scale to 10k concurrent users on one box.
*   **AsyncIO (Python/Go/Locust):** Uses a single thread with an Event Loop. Extremely lightweight. You can have 100k "virtual users" waiting for a response on a single core. **We will use this approach.**

## 2. The "Tick" Loop (Rate Limiting)
How do you send *exactly* 100 requests per second?
*   **Naive Approach:** `sleep(1/100)`. **Fail.** `sleep` is not precise. It drifts.
*   **Token Bucket Algorithm:**
    *   Fill a bucket with 100 tokens every second.
    *   Workers grab a token. If bucket empty, they wait.
*   **Scheduled Ticks:**
    *   Calculate the exact start time for every request: `t0, t0 + 10ms, t0 + 20ms...`
    *   Spin up a "pacer" task that wakes up workers at those exact times.

## 3. Concurrency Pools & Memory Management
If your target server slows down, your "virtual users" will pile up.
*   **The Danger Zone:** If you spawn a new coroutine for every request without limit, and the server hangs, you will create 1M coroutines and **Crash (OOM)**.
*   **The Semaphore Pattern:** Use `asyncio.Semaphore(max_concurrency)`.
    *   If `max_concurrency=1000` and 1000 requests are pending, the 1001st request **waits** (Backpressure).
    *   This protects *your* generator from crashing, even if the target is dead.

## 4. The Multi-Step Workflow
Handling "Provisioning" vs. "Testing":
1.  **Phase 1: Setup (Blocking):** Run `create_user()`. Wait for 200 OK.
    *   *Do NOT record metrics.* This is noise.
2.  **Phase 2: The Test (Non-Blocking):** Run `get_dashboard()`.
    *   *Record Latency.*
3.  **Phase 3: Teardown:** Run `delete_user()`.

We need a **Scenario Runner** class that executes these steps in order for each "Virtual User."
