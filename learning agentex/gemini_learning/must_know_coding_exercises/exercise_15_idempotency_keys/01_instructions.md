# Exercise: Idempotency Keys (The "Only Once" Rule)

In `scale-agentex`, creating a task is expensive (it starts a Temporal workflow). If a network blip happens and the UI sends the same `POST /tasks` twice, we **must not** start two separate workflows.

## The Problem
A user clicks "Analyze Contract." The server receives the request, starts the 5-minute analysis, but the user's internet drops before they see the "Success" message. The user clicks "Analyze Contract" again. 

Without an **Idempotency Key**, the server would start a *second* 5-minute analysis. **This wastes time and money.**

## The Goal
Build a `TaskService` that uses an `idempotency_key` to ensure a task is only created once.

## Requirements
1.  **Storage:** Use a dictionary `self.idempotency_store = {key: task_id}`.
2.  **Logic:** In `create_task(params, idempotency_key)`:
    *   Check if `idempotency_key` exists in the store.
    *   If it does, print "[IDEMPOTENCY] Found existing task! Returning {task_id}" and return that ID.
    *   If not, generate a new ID, print "[API] Creating NEW Task...", and store it.
3.  **The Test:** Call `create_task` with the same key three times. Only the first one should create a new task.

## Starter Code
```python
import uuid
from typing import Dict, Optional

class TaskService:
    def __init__(self):
        # Maps idempotency_key -> task_id
        self.idempotency_store: Dict[str, str] = {}
        # Simple task storage
        self.tasks: Dict[str, dict] = {}

    def create_task(self, params: dict, idempotency_key: str) -> str:
        """
        TODO: 
        1. Check if idempotency_key is in self.idempotency_store.
        2. If yes, return the stored task_id.
        3. If no, generate a new uuid.
        4. Print "Creating new task..."
        5. Store the new task_id in the idempotency_store.
        6. Return the new task_id.
        """
        pass

# --- 4. Execution ---
service = TaskService()
my_params = {"document": "contract.pdf"}
my_key = "unique-request-123"

print("--- Request 1 (The original) ---")
id1 = service.create_task(my_params, my_key)
print(f"Result ID: {id1}")

print("
--- Request 2 (The retry after a network blip) ---")
id2 = service.create_task(my_params, my_key)
print(f"Result ID: {id2}")

print("
--- Request 3 (Another retry) ---")
id3 = service.create_task(my_params, my_key)
print(f"Result ID: {id3}")

# Final Check: All IDs must be identical!
assert id1 == id2 == id3
```
