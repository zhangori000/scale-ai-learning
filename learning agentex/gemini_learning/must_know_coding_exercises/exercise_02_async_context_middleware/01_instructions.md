# Exercise: Async Context Middleware (The Invisible Data)

In `scale-agentex`, every log line has a `request_id` attached to it. Yet, if you look at the function signatures in `src/domain/services`, they don't take `request_id` as an argument.

How does the logger know the ID?
Answer: **ContextVars**.

## The Goal
Create a system where a "Request ID" is generated in middleware and accessed deep in a service function **without passing it as an argument**.

## Requirements
1.  **ContextVar:** Define a global `ContextVar` called `request_id_ctx`.
2.  **Middleware:** Create a function `middleware(func)` that:
    *   Generates a random ID.
    *   Sets the `request_id_ctx`.
    *   Calls `func`.
    *   **Crucial:** Resets the token after the call (cleanup).
3.  **Service:** Create a function `process_data()` that:
    *   Does NOT take any arguments.
    *   Prints "Processing data for Request ID: {id}" by reading the ContextVar.
4.  **Execution:** Call `middleware(process_data)` twice to show different IDs.

## Starter Code
```python
import contextvars
import uuid
from typing import Callable

# --- 1. Define the Global Context Variable ---
# This is thread-safe and async-safe!
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="unknown")

# --- 2. The Service Function (Deep inside the app) ---
def process_data():
    # TODO: Get the current request ID from the context variable
    current_id = "???" 
    print(f"  [SERVICE] Processing data for Request ID: {current_id}")

# --- 3. The Middleware (The Entry Point) ---
def middleware(handler: Callable):
    # TODO: 
    # 1. Generate a UUID.
    # 2. Set the ContextVar.
    # 3. Call the handler().
    # 4. (Optional but good practice) Reset the ContextVar.
    pass

# --- 4. Execution ---
print("--- Request 1 ---")
middleware(process_data)

print("
--- Request 2 ---")
middleware(process_data)
```
