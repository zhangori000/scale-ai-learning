# Solution: The Middleware Interceptor Pipeline (The "Chain" Pattern)

In `scale-agentex` (`src/api/authentication_middleware.py`), this pattern is used to authorize every request before it hits the platform. It's a "Chain of Responsibility" that ensures safety and consistency across the entire API.

## The Implementation

```python
from typing import List, Callable, Dict, Any

# --- 1. The Interceptors (The Middlemen) ---

def logging_interceptor(request: Dict, next_call: Callable) -> Any:
    """A simple 'Log' interceptor."""
    print(f"  [LOG] Incoming request for user: {request.get('user_id', 'Unknown')}")
    # Always call the next piece of code in the chain
    return next_call(request)

def auth_interceptor(request: Dict, next_call: Callable) -> Any:
    """A 'Security' interceptor that can 'short-circuit' the request."""
    if not request.get("authorized", False):
        print("  [AUTH] Access Denied: User is not authorized.")
        # STOP HERE! We return an error and DO NOT call next_call()
        return "HTTP 403 Forbidden"
    
    print("  [AUTH] Access Granted.")
    # Proceed to the next step
    return next_call(request)

# --- 2. The Final Route Handler (The Target) ---
def my_route_handler(request: Dict) -> Any:
    """The actual business logic of the route."""
    print("  [ROUTE] Executing business logic...")
    return f"Hello User {request['user_id']}! Here is your task data."

# --- 3. The Pipeline (The Orchestrator) ---
class MiddlewarePipeline:
    def __init__(self, interceptors: List[Callable]):
        self.interceptors = interceptors

    def run(self, request: Dict, final_handler: Callable) -> Any:
        """
        Building a recursive chain of functions.
        Think of it as nesting: 
        LogInterceptor(AuthInterceptor(RouteHandler()))
        """
        # We start with the final handler at the end of the chain
        current_call = final_handler

        # We reverse the list and wrap each interceptor around the current call
        # Reverse because we want the first interceptor to be the 'outermost' wrapper.
        for interceptor in reversed(self.interceptors):
            # Capture the current state of 'current_call' in a closure
            def make_next_call(prev_call):
                return lambda req: interceptor(req, prev_call)
            
            current_call = make_next_call(current_call)

        # Now, current_call is a single function that runs the whole pipeline!
        return current_call(request)

# --- 4. Execution ---
print("--- Scenario A: Authorized User ---")
req_a = {"user_id": "alice", "authorized": True}
pipeline = MiddlewarePipeline([logging_interceptor, auth_interceptor])

# Alice's request will go through Log -> Auth -> Route
result_a = pipeline.run(req_a, my_route_handler)
print(f"Final Result: {result_a}")

print("
--- Scenario B: Unauthorized User ---")
req_b = {"user_id": "bob", "authorized": False}

# Bob's request will go through Log -> Auth -> (STOPPED!)
result_b = pipeline.run(req_b, my_route_handler)
print(f"Final Result: {result_b}")
```

### Key Takeaways from the Solution:

1.  **Chain of Responsibility:** This pattern is powerful because it allows you to add features (like "Rate Limiting," "Tracing," or "Caching") just by adding a new interceptor to the list. You don't have to change any of the existing code.
2.  **Short-Circuiting:** The `auth_interceptor` is a "Security Guard." It has the power to stop the request and return an error before it ever reaches the expensive business logic of the `route_handler`.
3.  **Recursive Wrapping:** By wrapping the functions in a loop, we create a single "Call Chain." This is exactly how the `FastAPI` and `Starlette` middleware stacks are built under the hood.
4.  **Why we use it for Agents:** In `scale-agentex`, we need to ensure that every task is authorized. By using a middleware pipeline, we can guarantee that no request ever reaches an agent unless it has been properly authenticated and logged first.
