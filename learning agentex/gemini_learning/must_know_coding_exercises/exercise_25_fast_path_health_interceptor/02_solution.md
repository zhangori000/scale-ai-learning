# Solution: The Fast-Path Health Interceptor (Systems Optimization)

This pattern is a production "Best Practice" for high-availability systems. It's implemented in `scale-agentex` using the `HealthCheckInterceptor` class.

## The Implementation

```python
import time
import asyncio

# --- 1. The Heavy Application (The standard path) ---
async def standard_app(request: dict):
    """
    Represents the full application stack, including Auth, 
    Database connections, and Agent business logic.
    """
    print(f"  [APP] Starting heavy processing for {request['path']}...")
    # This delay would cause a health-check timeout in production!
    await asyncio.sleep(2.0) 
    return {"result": "Task completed successfully"}

# --- 2. The Interceptor (The Fast Path) ---
class HealthInterceptor:
    """
    An ASGI-style middleware that intercepts specific paths 
    before they reach the main application logic.
    """
    def __init__(self, app_to_wrap):
        self.app = app_to_wrap

    async def run(self, request: dict):
        """
        The key logic for 'Short-Circuiting' specific requests.
        """
        # 1. Identify the 'Health Check' path
        # In real systems, we might also check for /ready or /metrics
        if request.get("path") == "/health":
            # 2. BYPASS: Return a response immediately!
            # We don't call self.app(request), so we skip the 2-second sleep.
            print("  [INTERCEPTOR] Health check detected. Bypassing heavy app stack.")
            return {"status": "ok", "message": "System is alive"}

        # 3. STANDARD PATH: Pass the request to the real app
        return await self.app(request)

# --- 3. Execution (The Simulation) ---
async def main():
    # We wrap our 'Heavy' app with the 'Fast' interceptor
    # This is known as 'Middleware Decoration'
    app_stack = HealthInterceptor(standard_app)

    print("--- Scenario A: Load Balancer checks /health ---")
    start_a = time.time()
    # The Load Balancer expects a response in < 50ms
    res_a = await app_stack.run({"path": "/health"})
    print(f"  Response: {res_a}")
    print(f"  Total Time: {time.time() - start_a:.4f}s (INSTANT)")

    print("
--- Scenario B: User requests /tasks/create ---")
    start_b = time.time()
    # This is a normal request that needs the full power of the app
    res_b = await app_stack.run({"path": "/tasks/create"})
    print(f"  Response: {res_b}")
    print(f"  Total Time: {time.time() - start_b:.4f}s (SLOW)")

if __name__ == "__main__":
    asyncio.run(main())
```

### Key Takeaways from the Solution:

1.  **Short-Circuiting:** This is the act of returning a result early without running the rest of the code. It is the most powerful tool for performance optimization.
2.  **Resource Bypass:** In `scale-agentex`, the `HealthCheckInterceptor` bypasses the **Authentication Middleware**. Why? Because a health check from a Load Balancer (like AWS ALBs) often doesn't have an API Key. If we didn't bypass it, the health check would fail with a `401 Unauthorized` even if the system was healthy!
3.  **Independence:** Notice that the interceptor doesn't need to know *how* the `standard_app` works. It only needs to know the URL path. This makes it highly reusable.
4.  **Why this matters for Scale-Agentex:** When you are running 50 Docker containers of the Agentex Backend, the Load Balancer needs to know which ones are alive. If a container is "busy" with an LLM call and takes 30 seconds to respond to a health check, the Load Balancer will think it's dead and kill it. This interceptor prevents that "False Death" scenario by ensuring health checks are always fast.
