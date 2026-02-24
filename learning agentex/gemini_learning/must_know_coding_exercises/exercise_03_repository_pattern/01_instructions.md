# Exercise: The Repository Pattern (Database Abstraction)

In `scale-agentex`, you will never see raw SQL queries in the API routes.
Instead, you see calls like `await task_repository.get_task(id=...)`.

This is called the **Repository Pattern**. It allows us to swap the database (e.g., from Postgres to a simple dictionary for testing) without changing the business logic.

## The Goal
Create a `TaskRepository` interface and two implementations: one using a dictionary (Memory) and one simulating a database (Postgres). Then, write a service that uses the interface.

## Requirements
1.  **Protocol (Interface):** Define a `TaskRepository` protocol with methods:
    *   `save(task: dict)` -> None
    *   `get(id: str)` -> dict or None
2.  **Implementations:**
    *   `InMemoryTaskRepository`: Stores tasks in a simple `self.storage = {}`.
    *   `MockPostgresTaskRepository`: Prints "Executing SQL: INSERT..." and "Executing SQL: SELECT..." but uses a dictionary internally.
3.  **Service:** Create a `TaskService` class that takes a `TaskRepository` in its `__init__`.
    *   `create_task(name: str)` -> generates an ID, saves it, and returns the task.
    *   `get_task(id: str)` -> returns the task.
4.  **Execution:** Instantiate the service with the Memory repo and test it. Then instantiate with the Postgres repo and test it.

## Starter Code
```python
import uuid
from typing import Protocol, Dict, Optional

# --- 1. The Interface (Contract) ---
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
        # TODO: Implement
        pass

    def get(self, task_id: str) -> Optional[Dict]:
        # TODO: Implement
        pass

class MockPostgresTaskRepository:
    def __init__(self):
        self.db = {} # Simulate DB table

    def save(self, task: Dict) -> None:
        print(f"  [SQL] INSERT INTO tasks VALUES ({task})")
        # TODO: Implement logic
        pass

    def get(self, task_id: str) -> Optional[Dict]:
        print(f"  [SQL] SELECT * FROM tasks WHERE id = {task_id}")
        # TODO: Implement logic
        pass

# --- 3. The Service (Business Logic) ---
class TaskService:
    # Dependency Injection: We ask for the Interface, not a specific class!
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def create_task(self, name: str) -> Dict:
        task_id = str(uuid.uuid4())[:8]
        task = {"id": task_id, "name": name, "status": "PENDING"}
        self.repository.save(task)
        print(f"[SERVICE] Task '{name}' created with ID: {task_id}")
        return task

# --- 4. Execution ---
# TODO: Test with both repositories!
```
