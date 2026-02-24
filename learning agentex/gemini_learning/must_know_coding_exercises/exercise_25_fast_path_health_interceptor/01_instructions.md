# Exercise: The Fast-Path Health Interceptor (Systems Optimization)

In `scale-agentex` (`src/api/health_interceptor.py`), the platform handles health checks (e.g., `/health`) differently than normal requests.

If the platform is under heavy load (e.g., waiting for 1,000 LLM calls), the "standard" middleware stack might be too slow. A health check needs to respond **immediately**, bypassing things like authentication or database connection checks.

## The Goal
Create an `ASGI Middleware` (a wrapper) that "peeks" at the URL path and short-circuits the request if it's a health check.

## Requirements
1.  **The App:** A function `standard_app(request)` that takes 2 seconds to run (simulating a heavy AI load).
2.  **The Interceptor (YOUR JOB):** Implement `HealthInterceptor.run(request)`:
    *   If the path is `/health`, immediately return `{"status": "ok"}` (Fast Path).
    *   If the path is anything else, call `standard_app(request)` (Standard Path).
3.  **The Test:** Show that a call to `/health` is fast, while a call to `/tasks` is slow.

## Starter Code
```python
import time
import asyncio

# --- 1. The Heavy Application (The standard path) ---
async def standard_app(request: dict):
    """Simulates a heavy AI processing task"""
    print(f"  [APP] Starting heavy processing for {request['path']}...")
    await asyncio.sleep(2.0) # Simulating DB and LLM delays
    return {"result": "Task completed!"}

# --- 2. The Interceptor (YOUR JOB) ---
class HealthInterceptor:
    def __init__(self, app_to_wrap):
        self.app = app_to_wrap

    async def run(self, request: dict):
        """
        TODO: 
        1. Check if request['path'] == "/health".
        2. If YES, return {"status": "ok"} immediately.
        3. If NO, return await self.app(request).
        """
        pass

# --- 3. Execution (The Simulation) ---
async def main():
    # Wrap our heavy app with the fast-path interceptor
    fast_app = HealthInterceptor(standard_app)

    print("--- Request 1: Checking Health (Should be INSTANT) ---")
    t1 = time.time()
    res1 = await fast_app.run({"path": "/health"})
    print(f"  Response: {res1}")
    print(f"  Time taken: {time.time() - t1:.4f}s")

    print("
--- Request 2: Running Task (Should be SLOW) ---")
    t2 = time.time()
    res2 = await fast_app.run({"path": "/tasks"})
    print(f"  Response: {res2}")
    print(f"  Time taken: {time.time() - t2:.4f}s")

if __name__ == "__main__":
    asyncio.run(main())
```
