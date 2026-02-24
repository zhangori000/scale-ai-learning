# Solution: The State Machine (Validating Transitions)

In `scale-agentex`, this logic is often enforced in the **Use Case** or **Service** layer before updating the **PostgreSQL** database. It ensures that the lifecycle of every task is consistent and predictable.

## The Implementation

```python
from enum import Enum
from typing import Dict, Set

# --- 1. Define the Statuses ---
class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

# --- 2. The Custom Exception ---
class IllegalStateTransitionError(Exception):
    def __init__(self, from_status, to_status):
        super().__init__(
            f"Illegal State Transition: A task in '{from_status}' state cannot move to '{to_status}'."
        )

# --- 3. The Task Class ---
class Task:
    # A dictionary where:
    # Key = Current Status
    # Value = A Set of Statuses that we ARE allowed to move into.
    ALLOWED_TRANSITIONS: Dict[TaskStatus, Set[TaskStatus]] = {
        # 1. PENDING: Can start working or fail immediately
        TaskStatus.PENDING: {TaskStatus.RUNNING, TaskStatus.FAILED},
        
        # 2. RUNNING: Can finish successfully or encounter an error
        TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED},
        
        # 3. FAILED: Can be retried (PENDING) or deleted (Terminal)
        TaskStatus.FAILED: {TaskStatus.PENDING},
        
        # 4. COMPLETED: Terminal state. No more moves allowed.
        TaskStatus.COMPLETED: set() 
    }

    def __init__(self, name: str):
        self.name = name
        self.status = TaskStatus.PENDING

    def transition_to(self, new_status: TaskStatus):
        """
        Validates the move before updating the internal status.
        """
        # 1. Look up what is allowed from our current status
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, set())
        
        # 2. Check if the new status is in that set
        if new_status not in allowed:
            # 3. If NOT allowed, raise our custom error
            raise IllegalStateTransitionError(self.status, new_status)
            
        # 4. If YES, update the status
        print(f"  [STATE] Moving from {self.status} to {new_status}")
        self.status = new_status

# --- 4. Execution ---
t = Task("Audit Contract")

print(f"Initial Status: {t.status}")

# Test A: Valid move (PENDING -> RUNNING)
t.transition_to(TaskStatus.RUNNING)

# Test B: Valid move (RUNNING -> COMPLETED)
t.transition_to(TaskStatus.COMPLETED)

# Test C: INVALID move (COMPLETED -> RUNNING)
print("
--- Testing Invalid Transition ---")
try:
    # This should be BLOCKED because 'COMPLETED' is a terminal state.
    t.transition_to(TaskStatus.RUNNING)
except IllegalStateTransitionError as e:
    print(f"  [SUCCESS] Exception Caught: {e}")

# Test D: Retry logic (FAILED -> PENDING)
# Imagine the task failed during analysis...
t.status = TaskStatus.FAILED 
print(f"
Task failed. Status: {t.status}")

# We can move from FAILED back to PENDING to retry it.
t.transition_to(TaskStatus.PENDING)
print(f"Status after retry signal: {t.status}")
```

### Key Takeaways from the Solution

1.  **Immutability of Finished Work:** Terminal states like `COMPLETED` are powerful. They protect your historical data from accidental "Zombification."
2.  **Explicit over Implicit:** You don't have to guess what's allowed; it's all defined in one simple dictionary (`ALLOWED_TRANSITIONS`).
3.  **Traceability:** By using a `transition_to` method instead of directly setting `t.status = "..."`, you can easily add **logging** or **metrics** (e.g., "This task took 5 minutes to move from PENDING to COMPLETED").
4.  **Why we use it for Agents:** Agents are complex. They can fail 10 times and retry. They can be cancelled. They can be completed. Without a State Machine, it's impossible to track the "Ground Truth" of where an agent task actually stands in its lifecycle.
