# Solution: Build Your Own Dependency Injector

This solution demonstrates the "magic" behind FastAPI's dependency injection system. It uses Python's `inspect` module and `typing.get_type_hints` to introspect function signatures and resolve dependencies at runtime.

## The Implementation

```python
import inspect
from typing import Annotated, Any, Callable, get_args, get_origin

# --- 1. The "Framework" Primitives ---
class Header:
    """Marker class to tell our framework to look in headers"""
    def __init__(self, alias: str | None = None):
        self.alias = alias

class Depends:
    """Marker class to tell our framework to run another function first"""
    def __init__(self, dependency: Callable):
        self.dependency = dependency

# --- 2. The "Framework" Engine ---
def resolve_dependency(param_name: str, annotation: Any, request: dict) -> Any:
    """
    Resolves a single dependency based on its annotation.
    """
    # Check if the annotation is actually an Annotated type
    if get_origin(annotation) is Annotated:
        # Annotated[T, meta1, meta2...] -> get_args returns (T, meta1, meta2...)
        base_type, *metadata = get_args(annotation)
        
        # We only care about the first metadata item for this simple framework
        marker = metadata[0]
        
        if isinstance(marker, Header):
            # Resolve from headers
            header_name = marker.alias or param_name
            # In real frameworks, headers are case-insensitive
            # Here we just do a direct lookup
            return request.get("headers", {}).get(header_name)
            
        elif isinstance(marker, Depends):
            # Resolve recursively!
            # The dependency function itself might have dependencies
            return resolve_and_call(marker.dependency, request)
            
    # If not Annotated or no matching marker, just return None (or handle default)
    return None

def resolve_and_call(func: Callable, request: dict) -> Any:
    """
    Inspects 'func', finds arguments with Annotated[T, Header()] or Annotated[T, Depends()],
    resolves them using 'request', and calls 'func'.
    """
    # 1. Inspect the function signature to find parameter names and annotations
    sig = inspect.signature(func)
    # type_hints handles forward references and string types better than sig.parameters alone
    type_hints = {
        name: param.annotation 
        for name, param in sig.parameters.items() 
        if param.annotation != inspect.Parameter.empty
    }
    
    resolved_args = {}
    
    for param_name, annotation in type_hints.items():
        # resolve the value for this parameter
        value = resolve_dependency(param_name, annotation, request)
        resolved_args[param_name] = value
        
    # 2. Call the function with the resolved arguments
    return func(**resolved_args)

# --- 3. The "User Code" (Test Case) ---

# A simple dependency
def get_database():
    print("  -> (Dependency) Connecting to DB...")
    return {"db_connection": "connected"}

# Another dependency that depends on the first one!
def get_user_dao(db: Annotated[dict, Depends(get_database)]):
    print("  -> (Dependency) Creating User DAO...")
    return {"dao_type": "postgres", "connection": db}

# The route handler
def my_controller(
    user_agent: Annotated[str, Header(alias="User-Agent")], 
    dao: Annotated[dict, Depends(get_user_dao)]
):
    print("-> (Controller) Handling Request")
    return f"User-Agent: {user_agent}, DAO: {dao['dao_type']}"

# --- 4. The Execution ---
mock_request = {
    "headers": {"User-Agent": "FastAPI-Student/1.0"}
}

print("Starting Framework Execution...")
result = resolve_and_call(my_controller, mock_request)
print(f"
Result: {result}")
```

### Key Takeaways

1.  **Reflection:** Frameworks like FastAPI use `inspect` heavily. They don't magically know what arguments you want; they *read* your function definition at runtime.
2.  **Metadata:** `Annotated` is powerful because it lets you attach arbitrary objects (like our `Header` and `Depends` classes) to types. The framework reads these objects to decide what to do.
3.  **Recursion:** Notice how `resolve_dependency` calls `resolve_and_call` when it encounters a `Depends`. This allows for complex dependency graphs (A depends on B, B depends on C...).
