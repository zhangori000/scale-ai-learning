# Exercise: The Middleware Interceptor Pipeline (The "Chain" Pattern)

In `scale-agentex` (`src/api/authentication_middleware.py`), every request passes through several "Interceptors" before reaching the actual route.

1.  **LoggingInterceptor**: "I see a request from User 123."
2.  **AuthInterceptor**: "Is User 123 allowed to do this?"
3.  **Route**: "Process the task!"

## The Goal
Create a `MiddlewarePipeline` that executes a list of "Interceptors" in order. Each interceptor can "call the next one" or stop the request entirely.

## Requirements
1.  **Request Object:** A simple dictionary `{"user_id": str, "authorized": bool}`.
2.  **The Interceptor Interface:** A function `(request, next_call)`:
    *   It does some work.
    *   It then calls `next_call(request)`.
3.  **Interceptor A (Logging):** Simply prints "[LOG] Request from {user_id}".
4.  **Interceptor B (Auth):** 
    *   Checks if `request["authorized"]` is `True`.
    *   If yes, calls `next_call(request)`.
    *   If no, prints "[AUTH] DENIED!" and returns a 403 error string.
5.  **The Pipeline (YOUR JOB):** Implement `Pipeline.run(request, final_handler)` to recursively call each interceptor.

## Starter Code
```python
from typing import List, Callable, Dict, Any

# --- 1. The Interceptors (User Code) ---

def logging_interceptor(request: Dict, next_call: Callable) -> Any:
    print(f"  [LOG] Incoming request for user: {request['user_id']}")
    return next_call(request)

def auth_interceptor(request: Dict, next_call: Callable) -> Any:
    if not request.get("authorized", False):
        print("  [AUTH] Access Denied: User is not authorized.")
        return "HTTP 403 Forbidden"
    
    print("  [AUTH] Access Granted.")
    return next_call(request)

# --- 2. The Final Route Handler ---
def my_route_handler(request: Dict) -> Any:
    print("  [ROUTE] Executing business logic...")
    return f"Hello User {request['user_id']}! Here is your task data."

# --- 3. The Pipeline (YOUR JOB) ---
class MiddlewarePipeline:
    def __init__(self, interceptors: List[Callable]):
        self.interceptors = interceptors

    def run(self, request: Dict, final_handler: Callable) -> Any:
        """
        TODO: 
        1. Create a chain of calls.
        2. The last call should be the final_handler.
        3. Each interceptor should wrap the next call in the chain.
        """
        # Hint: You can use a recursive function or a loop to wrap the calls.
        pass

# --- 4. Execution ---
print("--- Scenario A: Authorized User ---")
req_a = {"user_id": "alice", "authorized": True}
pipeline = MiddlewarePipeline([logging_interceptor, auth_interceptor])
print(f"Final Result: {pipeline.run(req_a, my_route_handler)}")

print("
--- Scenario B: Unauthorized User ---")
req_b = {"user_id": "bob", "authorized": False}
print(f"Final Result: {pipeline.run(req_b, my_route_handler)}")
```
