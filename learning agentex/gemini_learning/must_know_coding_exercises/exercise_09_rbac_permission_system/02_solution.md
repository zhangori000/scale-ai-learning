# Solution: The RBAC Permission System (Authorization Guard)

In `scale-agentex`, this logic is the "last line of defense." It's implemented in `src/domain/services/authorization_service.py` and is called by every route to ensure the security of the platform.

## The Implementation

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
    def __init__(self, principal_id: str, resource_id: str, operation: Operation):
        super().__init__(
            f"Access Denied: Principal '{principal_id}' does not have '{operation}' permission for Resource '{resource_id}'."
        )

# --- 3. The Authorization Service ---
class AuthorizationService:
    def __init__(self):
        # A dictionary mapping a Principal (User/Agent) to a SET of permissions.
        # Format: { principal_id: set((resource_id, operation)) }
        self.grants: Dict[str, Set[Tuple[str, Operation]]] = {}

    def grant(self, principal_id: str, resource_id: str, operation: Operation):
        """
        Gives a principal a specific permission on a specific resource.
        """
        if principal_id not in self.grants:
            self.grants[principal_id] = set()
        
        # Add the (Resource, Operation) pair to the set
        self.grants[principal_id].add((resource_id, operation))
        print(f"[AUTH] Granted: {principal_id} -> {operation.upper()} on {resource_id}")

    def check_permission(self, principal_id: str, resource_id: str, operation: Operation):
        """
        The key logic for checking if an action is allowed.
        """
        # 1. Get the set of grants for this principal
        user_grants = self.grants.get(principal_id, set())
        
        # 2. Check for an EXACT MATCH (e.g., ("task-1", READ))
        if (resource_id, operation) in user_grants:
            return True
            
        # 3. Check for a WILDCARD MATCH (e.g., ("*", DELETE))
        # This is how 'Admins' or 'Owners' are often handled!
        if ("*", operation) in user_grants:
            return True
            
        # 4. If neither matches, throw the Access Denied error
        raise AccessDeniedError(principal_id, resource_id, operation)

# --- 4. Execution ---
auth = AuthorizationService()

# Setup Permissions
auth.grant("agent-007", "task-1", Operation.READ)
auth.grant("admin-bob", "*", Operation.DELETE) # Admin can delete ANYTHING

print("
--- Testing Success ---")
try:
    auth.check_permission("agent-007", "task-1", Operation.READ)
    print("  [SUCCESS] Agent-007 read Task-1")
    
    auth.check_permission("admin-bob", "any-random-task", Operation.DELETE)
    print("  [SUCCESS] Admin-Bob deleted Task-X (Wildcard)")
except AccessDeniedError as e:
    print(f"  [ERROR] {e}")

print("
--- Testing Failure ---")
try:
    # 007 has READ, but not DELETE
    auth.check_permission("agent-007", "task-1", Operation.DELETE)
except AccessDeniedError as e:
    print(f"  [DENIED] {e}")

try:
    # A user with NO permissions at all
    auth.check_permission("hacker-hannah", "task-1", Operation.READ)
except AccessDeniedError as e:
    print(f"  [DENIED] {e}")
```

### Key Takeaways

1.  **Set Over List:** Notice we use a `set()` for permissions. This makes checking very fast (`O(1)` time complexity) even if a principal has 10,000 permissions.
2.  **Explicit Grants:** By default, everything is denied. You must explicitly "Grant" a permission for it to work. This is the **Principle of Least Privilege**.
3.  **Wildcards:** The `"*"` wildcard is a powerful tool used in `scale-agentex` to allow administrative tasks or to give an owner access to "all" tasks.
4.  **Why this matters for Agents:** In a multi-tenant system (where many companies use the same platform), you MUST ensure that Company A's agent cannot read Company B's tasks. This RBAC system is the wall that keeps them separated.
