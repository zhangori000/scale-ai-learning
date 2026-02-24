# Solution: Standardized Error Mapping (The Domain-to-HTTP Bridge)

In `scale-agentex` (`src/api/app.py`), the platform uses `exception_handlers` to catch domain-specific errors like `ItemDoesNotExist` and map them to clean JSON responses for the user.

## The Implementation

```python
from typing import Dict, Any, Tuple

# --- 1. The Domain Layer (Pure Logic, No HTTP!) ---
# This layer doesn't know about 404s, 500s, or JSON. It only knows business errors.
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
    
    if len(agent_id) < 1:
        raise ValidationFailedError("Agent ID cannot be empty.")
        
    return {"id": agent_id, "name": "Active Agent"}

# --- 2. The API Layer (The Bridge) ---
# This layer bridges the "Brain" (Domain) to the "Web" (HTTP).

def map_domain_error_to_http(exc: DomainError) -> Tuple[int, Dict[str, Any]]:
    """
    Translates a Domain Exception into an HTTP Status Code and JSON Payload.
    """
    # 1. Map EntityNotFoundError to 404 Not Found
    if isinstance(exc, EntityNotFoundError):
        return 404, {
            "error": "Resource Not Found",
            "message": str(exc),
            "code": "NOT_FOUND"
        }
        
    # 2. Map ValidationFailedError to 400 Bad Request
    if isinstance(exc, ValidationFailedError):
        return 400, {
            "error": "Bad Request",
            "message": str(exc),
            "code": "INVALID_INPUT"
        }
        
    # 3. Default to 500 Internal Server Error (The "Ouch" case)
    return 500, {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred. Please contact support.",
        "code": "INTERNAL_ERROR"
    }

class MockFastAPI:
    def run_route(self, handler, *args, **kwargs):
        print(f"
--- Calling Route: {handler.__name__} ---")
        try:
            # 1. Execute the handler (This is where the 'magic' happens)
            result = handler(*args, **kwargs)
            print(f"SUCCESS (200 OK): {result}")
            
        except DomainError as e:
            # 2. Catch the domain error and map it to HTTP
            status_code, payload = map_domain_error_to_http(e)
            
            # 3. Final formatted output (like a real API response)
            print(f"FAILURE ({status_code} Error Response):")
            print(f"  {{ 'status': {status_code}, 'body': {payload} }}")

# --- 3. Execution ---
app = MockFastAPI()

# Test A: Success
app.run_route(mock_get_agent, agent_id="1")

# Test B: Failure (Not Found)
app.run_route(mock_get_agent, agent_id="999")

# Test C: Failure (Validation)
app.run_route(mock_get_agent, agent_id="")

# Test D: Unknown Domain Error
class UnknownError(DomainError): pass
app.run_route(lambda: exec('raise UnknownError("oops")'))
```

### Key Takeaways from the Solution

1.  **Decoupling:** Notice that the `mock_get_agent` function is **completely independent** of the web server. This makes it incredibly easy to **unit test** without starting a real server.
2.  **Centralization:** All error-mapping logic is in one place (`map_domain_error_to_http`). If you want to change your error format (e.g., add a "timestamp" to all errors), you only have to change it once!
3.  **Security:** By catching all `DomainError` types and providing a default `500` fallback, we ensure that we **never leak sensitive stack traces** or database errors directly to the user.
4.  **Why this matters for Scale-Agentex:** In a production-grade system, consistency is king. If every endpoint returns errors in a different format, the UI developers will go crazy. This mapping ensures that every error looks the same to the frontend.
