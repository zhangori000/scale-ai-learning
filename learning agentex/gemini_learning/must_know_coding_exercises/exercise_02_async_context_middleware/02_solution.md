# Solution: Async Context Middleware

In `scale-agentex`, this pattern is used for logging (`src/utils/logging.py`) and authentication (`src/api/authentication_middleware.py`).

```python
import contextvars
import uuid
from typing import Callable, Any

# --- 1. Define the Global Context Variable ---
# This variable acts like a "thread-local" but for async tasks.
# Each request gets its own separate value, even if they run concurrently!
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="unknown")

# --- 2. The Service Function (Deep inside the app) ---
def process_data():
    # We can retrieve the value WITHOUT passing it as an argument!
    current_id = request_id_ctx.get()
    print(f"  [SERVICE] Processing data for Request ID: {current_id}")

# --- 3. The Middleware (The Entry Point) ---
def middleware(handler: Callable):
    # 1. Generate a unique ID for this request
    req_id = str(uuid.uuid4())[:8]
    print(f"[MIDDLEWARE] Incoming Request -> ID: {req_id}")
    
    # 2. Set the context variable
    # This returns a 'Token' which we can use to reset it later
    token = request_id_ctx.set(req_id)
    
    try:
        # 3. Call the handler
        # Inside this call, request_id_ctx.get() will return our new ID
        handler()
    finally:
        # 4. Clean up! (Reset to previous value)
        # This is important in some async frameworks to prevent leaking context
        print("[MIDDLEWARE] Request Finished -> Cleaning up context")
        request_id_ctx.reset(token)

# --- 4. Execution ---
print("--- Request 1 ---")
middleware(process_data)
# Expected: 
# [MIDDLEWARE] Incoming Request -> ID: a1b2c3d4
#   [SERVICE] Processing data for Request ID: a1b2c3d4
# [MIDDLEWARE] Request Finished -> Cleaning up context

print("
--- Request 2 ---")
middleware(process_data)
# Expected:
# [MIDDLEWARE] Incoming Request -> ID: e5f6g7h8
#   [SERVICE] Processing data for Request ID: e5f6g7h8
# [MIDDLEWARE] Request Finished -> Cleaning up context
```

### Why this matters for Scale-Agentex?
Imagine you have a bug where an Agent creates a Task, which sends a Message, which triggers an Event. That's 4 layers deep. By using `ContextVar`, the initial "Trace ID" from the very first request is automatically available in the deepest log message, allowing you to trace the entire chain of events perfectly.
