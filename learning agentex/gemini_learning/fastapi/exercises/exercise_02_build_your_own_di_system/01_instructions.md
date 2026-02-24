# Exercise: Build Your Own Dependency Injector

This is an **advanced** Python exercise. We are going to rebuild the "magic" part of FastAPI: the Dependency Injection system.

## The Goal
In FastAPI, you write `def my_route(user_agent: Annotated[str, Header()])`.
You never call `my_route("Mozilla/5.0")` manually. **FastAPI calls it for you.**

Your job is to write that caller function.

## What you need to learn
1.  **`typing.Annotated`**: It's just a container. `Annotated[int, "metadata"]` is treated as `int` by type checkers, but at runtime, you can access `"metadata"`.
2.  **`inspect.signature`**: This Python module lets you look at a function and see its arguments and their type hints.

## The Task
Write a function `resolve_and_call(func, request)` that:
1.  Looks at the arguments of `func`.
2.  Checks if an argument has an `Annotated` type hint.
3.  If the annotation is `Header()`, it looks up that header in the `request` dictionary.
4.  If the annotation is `Depends(dependency_func)`, it calls `dependency_func` first, then passes the result.
5.  Finally, it calls `func` with all the correct arguments.

## Starter Code

```python
import inspect
from typing import Annotated, Any, Callable

# --- 1. The "Framework" Primitives ---
class Header:
    """Marker class to tell our framework to look in headers"""
    def __init__(self, alias: str | None = None):
        self.alias = alias

class Depends:
    """Marker class to tell our framework to run another function first"""
    def __init__(self, dependency: Callable):
        self.dependency = dependency

# --- 2. The "Framework" Engine (YOUR JOB) ---
def resolve_and_call(func: Callable, request: dict) -> Any:
    """
    Inspects 'func', finds arguments with Annotated[T, Header()] or Annotated[T, Depends()],
    resolves them using 'request', and calls 'func'.
    """
    # TODO: Implement this!
    # Hint: use inspect.signature(func).parameters
    pass

# --- 3. The "User Code" (Test Case) ---

# A simple dependency
def get_database():
    return {"db_connection": "connected"}

# The route handler
def my_controller(
    user_agent: Annotated[str, Header(alias="User-Agent")], 
    db: Annotated[dict, Depends(get_database)]
):
    return f"User-Agent: {user_agent}, DB: {db['db_connection']}"

# --- 4. The Execution ---
mock_request = {
    "headers": {"User-Agent": "FastAPI-Student/1.0"}
}

# This should print: "User-Agent: FastAPI-Student/1.0, DB: connected"
print(resolve_and_call(my_controller, mock_request))
```
