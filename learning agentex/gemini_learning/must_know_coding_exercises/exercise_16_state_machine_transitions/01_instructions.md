# Exercise: The State Machine (Validating Transitions)

In `scale-agentex`, a Task follows a strict lifecycle. If a task is `COMPLETED`, it should stay `COMPLETED`. If a user (or a bug) tries to set a `COMPLETED` task back to `RUNNING`, the platform must **block** that action.

## The Goal
Create a `Task` class that only allows valid status updates based on a "State Transition Map."

## Requirements
1.  **Status Enum:** Create a `TaskStatus` enum with `PENDING`, `RUNNING`, `COMPLETED`, and `FAILED`.
2.  **Transition Map:** Create a dictionary `ALLOWED_TRANSITIONS` that defines which status can move to which:
    *   `PENDING` -> `RUNNING`, `FAILED`
    *   `RUNNING` -> `COMPLETED`, `FAILED`
    *   `COMPLETED` -> None (Terminal state)
    *   `FAILED` -> `PENDING` (Retry state)
3.  **The Method:** Create a `transition_to(new_status)` method that:
    *   Checks if the move from `current_status` to `new_status` is in the map.
    *   If yes, updates the status.
    *   If no, raises an `IllegalStateTransitionError`.

## Starter Code
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
    pass

# --- 3. The Task Class (YOUR JOB) ---
class Task:
    # TODO: Define ALLOWED_TRANSITIONS as a dictionary
    ALLOWED_TRANSITIONS = {
        # current_status: {set_of_allowed_new_statuses}
    }

    def __init__(self, name: str):
        self.name = name
        self.status = TaskStatus.PENDING

    def transition_to(self, new_status: TaskStatus):
        """
        TODO: 
        1. Check if the transition from self.status to new_status is allowed.
        2. If allowed, update self.status.
        3. If NOT allowed, raise IllegalStateTransitionError.
        """
        pass

# --- 4. Execution ---
t = Task("Audit Contract")

print(f"Initial Status: {t.status}")

# Test A: Valid move (PENDING -> RUNNING)
t.transition_to(TaskStatus.RUNNING)
print(f"Successfully moved to: {t.status}")

# Test B: Valid move (RUNNING -> COMPLETED)
t.transition_to(TaskStatus.COMPLETED)
print(f"Successfully moved to: {t.status}")

# Test C: INVALID move (COMPLETED -> RUNNING)
print("
--- Testing Invalid Transition ---")
try:
    t.transition_to(TaskStatus.RUNNING)
except IllegalStateTransitionError:
    print("  [SUCCESS] Blocked invalid transition: COMPLETED -> RUNNING")

# Test D: Retry logic (FAILED -> PENDING)
t.status = TaskStatus.FAILED # Manual override for test
t.transition_to(TaskStatus.PENDING)
print(f"Successfully moved FAILED back to: {t.status}")
```
