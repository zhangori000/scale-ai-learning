# Exercise: The RBAC Permission System (The Authorization Guard)

In `scale-agentex`, almost every API call is guarded. We don't just check if you are "logged in." We check: 
**"Can this Principal (User/Agent) perform this Operation (Read/Update/Execute) on this Resource (Task_123)?"**

This is called **Fine-Grained Access Control**.

## The Goal
Create an `AuthorizationService` that can store "Grants" (Permissions) and check them at runtime.

## Requirements
1.  **Enums:** Create an `Operation` enum (READ, UPDATE, DELETE) and a `ResourceType` enum (TASK, AGENT).
2.  **The Service:** Create an `AuthorizationService` with a `self.grants` dictionary (`{principal_id: set((resource_id, operation))}`).
3.  **Grant Method:** `grant(principal_id: str, resource_id: str, operation: Operation)`:
    *   Adds the permission to the principal's set.
4.  **Check Method:** `check_permission(principal_id: str, resource_id: str, operation: Operation)`:
    *   Checks if the principal has the exact permission.
    *   **Advanced:** If the principal has a "Wildcard" grant (e.g., `resource_id="*"`), it should allow any resource ID for that operation.
5.  **Exception:** If the check fails, raise a custom `AccessDeniedError`.

## Starter Code
```python
from enum import Enum
from typing import Set, Tuple, Dict, Any

# --- 1. Define the Types (Enums) ---
class Operation(str, Enum):
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

class ResourceType(str, Enum):
    TASK = "task"
    AGENT = "agent"

# --- 2. The Custom Exception ---
class AccessDeniedError(Exception):
    pass

# --- 3. The Authorization Service (YOUR JOB) ---
class AuthorizationService:
    def __init__(self):
        # Stores permissions: { principal_id: set((resource_id, operation)) }
        self.grants: Dict[str, Set[Tuple[str, Operation]]] = {}

    def grant(self, principal_id: str, resource_id: str, operation: Operation):
        # TODO: Add the permission to the principal's set
        pass

    def check_permission(self, principal_id: str, resource_id: str, operation: Operation):
        """
        TODO: 
        1. Find the permissions for the principal_id.
        2. Check if (resource_id, operation) is in the set.
        3. Check if ('*', operation) is in the set (The Wildcard!).
        4. If not found, raise AccessDeniedError.
        """
        pass

# --- 4. Execution ---
auth = AuthorizationService()

# 1. Setup Permissions
auth.grant("agent-007", "task-1", Operation.READ)
auth.grant("admin-bob", "*", Operation.DELETE) # Admin can delete ANYTHING

# 2. Test Success Cases
print("--- Success Tests ---")
auth.check_permission("agent-007", "task-1", Operation.READ)
print("  [AUTH] Agent-007 can read Task-1")

auth.check_permission("admin-bob", "task-999", Operation.DELETE)
print("  [AUTH] Admin-Bob can delete Task-999 (Wildcard)")

# 3. Test Failure Cases
print("
--- Failure Tests ---")
try:
    auth.check_permission("agent-007", "task-1", Operation.DELETE)
except AccessDeniedError:
    print("  [AUTH] DENIED: Agent-007 cannot delete Task-1")
```
