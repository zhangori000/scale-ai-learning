# Solution: State Isolation and the Compound Key

In Agentex, the database (MongoDB) enforces this isolation via a **Compound Index**. 
In our Python simulation, we recreate this with a tuple-based key `(task_id, agent_id)`.

## The Solution

```python
class StateStore:
    def __init__(self):
        # A dictionary where the keys are tuples (task_id, agent_id)
        self._storage = {}

    def _get_key(self, task_id: str, agent_id: str) -> tuple[str, str]:
        # Using a tuple as a key in Python is extremely efficient 
        # because tuples are hashable.
        return (task_id, agent_id)

    def save_state(self, task_id: str, agent_id: str, data: dict):
        key = self._get_key(task_id, agent_id)
        self._storage[key] = data

    def get_state(self, task_id: str, agent_id: str) -> dict:
        key = self._get_key(task_id, agent_id)
        return self._storage.get(key, {})
```

## Why this is Agentex-style:
1. **Agent Independence**: Agentex allows multiple agents to work on a single task (e.g., one agent to brainstorm, one to fact-check). Without this compound key, they would overwrite each other's memory.
2. **Global Uniqueness**: In `src/domain/entities/states.py`, it explicitly states: *"The combination of task_id and agent_id is globally unique."*
3. **Database Performance**: By indexing on both fields, the database can find a 1KB state in a 10TB table in milliseconds.
