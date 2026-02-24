# Exercise: Standardized Error Mapping (The Domain-to-HTTP Bridge)

In `scale-agentex`, we want to keep our business logic "Pure." This means our **Use Cases** and **Repositories** should NOT know about FastAPI or HTTP Status Codes.

Instead, they raise **Domain Exceptions** (e.g., `AgentNotReadyError`). The **API Layer** then catches these and converts them into a clean JSON response (e.g., `400 Bad Request`).

## The Goal
Create a "Global Exception Handler" that catches a custom `DomainError` and returns a formatted JSON dictionary.

## Requirements
1.  **Domain Errors:** Create a base `DomainError(Exception)` and two subclasses:
    *   `EntityNotFoundError` (e.g., "Agent 123 doesn't exist").
    *   `ValidationFailedError` (e.g., "Task name is too short").
2.  **The "API Bridge" (YOUR JOB):** Create a function `map_domain_error_to_http(error: DomainError)` that:
    *   Returns a tuple: `(status_code: int, payload: dict)`.
    *   If `EntityNotFoundError` -> `(404, {"error": "Not Found", "message": str(error)})`.
    *   If `ValidationFailedError` -> `(400, {"error": "Bad Request", "message": str(error)})`.
3.  **The "API App":** Create a class `MockFastAPI` that has a `run_route(handler)` method. This method should:
    *   `try` to run the handler.
    *   `except DomainError` and use your `map_domain_error_to_http` function to print the final JSON response.

## Starter Code
```python
from typing import Dict, Any, Tuple

# --- 1. The Domain Layer (Pure Logic, No HTTP!) ---
class DomainError(Exception):
    """Base class for all business logic errors"""
    pass

class EntityNotFoundError(DomainError):
    pass

class ValidationFailedError(DomainError):
    pass

def mock_get_agent(agent_id: str):
    # Simulate a business logic failure
    if agent_id == "999":
        raise EntityNotFoundError(f"Agent '{agent_id}' was not found in our database.")
    return {"id": agent_id, "name": "Active Agent"}

# --- 2. The API Layer (The Bridge) ---

def map_domain_error_to_http(exc: DomainError) -> Tuple[int, Dict[str, Any]]:
    """
    TODO: Implement the mapping logic here.
    """
    pass

class MockFastAPI:
    def run_route(self, handler, *args, **kwargs):
        print(f"--- Calling Route: {handler.__name__} ---")
        try:
            result = handler(*args, **kwargs)
            print(f"SUCCESS (200 OK): {result}")
        except DomainError as e:
            # TODO: 
            # 1. Use map_domain_error_to_http(e) to get code and payload.
            # 2. Print the final JSON-style response.
            pass

# --- 3. Execution ---
app = MockFastAPI()

# Test A: Success
app.run_route(mock_get_agent, agent_id="1")

# Test B: Failure (Not Found)
app.run_route(mock_get_agent, agent_id="999")
```
