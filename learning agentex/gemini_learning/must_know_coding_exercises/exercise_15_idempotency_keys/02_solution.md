# Solution: Idempotency Keys (The "Only Once" Rule)

This solution demonstrates the "Durable Control" pattern in `scale-agentex`. It's how the platform ensures that even if the internet is flaky, the AI only runs exactly once.

## The Implementation

```python
import uuid
from typing import Dict, Optional

class TaskService:
    def __init__(self):
        # A dictionary mapping a 'Unique Request Key' to a 'Task ID'.
        # In scale-agentex, this is usually stored in PostgreSQL with a 
        # 'UNIQUE' constraint on the idempotency_key column.
        self.idempotency_store: Dict[str, str] = {}
        
        # A simple dictionary to store the actual tasks
        self.tasks: Dict[str, dict] = {}

    def create_task(self, params: dict, idempotency_key: str) -> str:
        """
        The key logic for 'Idempotent' task creation.
        It ensures that if the same request comes in twice, 
        we only do the expensive work once.
        """
        # 1. Check if we've seen this idempotency_key before
        if idempotency_key in self.idempotency_store:
            # Found it! This is a duplicate request.
            task_id = self.idempotency_store[idempotency_key]
            print(f"  [IDEMPOTENCY] Found existing task! Returning Task ID: {task_id}")
            return task_id

        # 2. Not found! This is the FIRST time we're seeing this request.
        # This is where the expensive work starts...
        task_id = str(uuid.uuid4())[:8]
        print(f"  [API] Creating NEW Task: '{task_id}' for request '{idempotency_key}'...")
        
        # 3. Simulate expensive setup (e.g. creating the Temporal workflow)
        new_task = {
            "id": task_id,
            "params": params,
            "status": "RUNNING",
            "idempotency_key": idempotency_key
        }
        self.tasks[task_id] = new_task
        
        # 4. CRITICAL: Store the mapping so we can find it later
        self.idempotency_store[idempotency_key] = task_id
        
        return task_id

# --- 4. Execution (The Simulation) ---
service = TaskService()
my_params = {"document": "legal_contract.pdf"}
my_key = "request-uuid-abc-123"

print("--- Request 1 (The original) ---")
# The user clicks "Send" for the first time.
id1 = service.create_task(my_params, my_key)
print(f"Final Result ID: {id1}")

print("
--- Request 2 (The retry after a network blip) ---")
# The user's internet dropped, so their browser retried the request.
# But it sent the same 'my_key', so we know it's a retry!
id2 = service.create_task(my_params, my_key)
print(f"Final Result ID: {id2}")

print("
--- Request 3 (Another retry) ---")
id3 = service.create_task(my_params, my_key)
print(f"Final Result ID: {id3}")

# Final Check: All IDs must be identical!
# We didn't start 3 tasks. We started ONE task and returned the ID 3 times.
assert id1 == id2 == id3
print("
[SUCCESS] Idempotency logic correctly prevented duplicate tasks.")
```

### Key Takeaways from the Solution:

1.  **Atomicity:** In a real production system (like Scale-Agentex), you would use a single database transaction to check the key and insert the task at the same time. This prevents a "race condition" where two workers both try to create the task simultaneously.
2.  **Request IDs:** Clients (like the `agentex-ui`) should always generate a unique `idempotency_key` for every new action they perform.
3.  **No Cost:** Retrying an idempotent request is almost "free." It's just a quick database lookup instead of a slow, expensive AI analysis.
4.  **Why we use it for Agents:** Agents are the most expensive things we build. If an agent task costs $10.00 to run (due to complex token usage), failing to implement idempotency is a very expensive mistake!
