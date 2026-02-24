# Solution: The Repository Pattern (Database Abstraction)

In `scale-agentex`, you will find repositories in `src/domain/repositories/`. This is why we can mock databases in unit tests!

```python
import uuid
from typing import Protocol, Dict, Optional, runtime_checkable

# --- 1. The Interface (Contract) ---
@runtime_checkable
class TaskRepository(Protocol):
    def save(self, task: Dict) -> None:
        ...
    
    def get(self, task_id: str) -> Optional[Dict]:
        ...

# --- 2. The Implementations ---
class InMemoryTaskRepository:
    def __init__(self):
        self.storage = {}

    def save(self, task: Dict) -> None:
        self.storage[task["id"]] = task
        print(f"  [MEMORY] Saved task: {task['id']}")

    def get(self, task_id: str) -> Optional[Dict]:
        print(f"  [MEMORY] Fetching task: {task_id}")
        return self.storage.get(task_id)

class MockPostgresTaskRepository:
    def __init__(self):
        self.db = {} # Simulate DB table

    def save(self, task: Dict) -> None:
        self.db[task["id"]] = task
        print(f"  [SQL] INSERT INTO tasks (id, name, status) VALUES ('{task['id']}', '{task['name']}', '{task['status']}')")

    def get(self, task_id: str) -> Optional[Dict]:
        print(f"  [SQL] SELECT * FROM tasks WHERE id = '{task_id}'")
        return self.db.get(task_id)

# --- 3. The Service (Business Logic) ---
class TaskService:
    # Dependency Injection: We rely on the abstraction, not the detail.
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def create_task(self, name: str) -> Dict:
        task_id = str(uuid.uuid4())[:8]
        task = {"id": task_id, "name": name, "status": "PENDING"}
        self.repository.save(task)
        print(f"[SERVICE] Task '{name}' created with ID: {task_id}")
        return task

# --- 4. Execution ---
print("--- Using IN-MEMORY Repository (Testing) ---")
repo_mem = InMemoryTaskRepository()
service_test = TaskService(repo_mem)

t1 = service_test.create_task("Test Task A")
# Output:
#   [MEMORY] Saved task: ...
# [SERVICE] Task 'Test Task A' created...

print("
--- Using POSTGRES Repository (Production) ---")
repo_pg = MockPostgresTaskRepository()
service_prod = TaskService(repo_pg)

t2 = service_prod.create_task("Production Task B")
# Output:
#   [SQL] INSERT INTO tasks ...
# [SERVICE] Task 'Production Task B' created...
```

### Why this matters for Scale-Agentex?
In the codebase, you will see `DTaskRepository` injected into services. This means we can swap out the database entirely (e.g., replace Postgres with Mongo) just by changing the implementation class, without rewriting a single line of business logic in the `TaskService`.
