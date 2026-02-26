# Exercise 36: State Isolation and the Compound Key

In Agentex, state is not just "global". It is scoped to a specific **Task** and a specific **Agent**. 
Looking at `src/domain/repositories/task_state_repository.py`, we see a compound index on `("task_id", "agent_id")`.

## The Challenge
Implement a `StateStore` that ensures strict isolation.
1. `save_state(task_id, agent_id, data)`: Stores the data.
2. `get_state(task_id, agent_id)`: Retrieves data ONLY if both IDs match.
3. **The Trap**: Ensure that Agent A working on Task 1 cannot see Agent A's state on Task 2.

## Starter Code
```python
class StateStore:
    def __init__(self):
        # TODO: What is the best data structure for a compound key?
        self._storage = {}

    def _get_key(self, task_id: str, agent_id: str) -> str:
        # TODO: Implement a unique string key
        pass

    def save_state(self, task_id: str, agent_id: str, data: dict):
        key = self._get_key(task_id, agent_id)
        self._storage[key] = data

    def get_state(self, task_id: str, agent_id: str) -> dict:
        key = self._get_key(task_id, agent_id)
        return self._storage.get(key, {})

# --- Simulation ---
store = StateStore()

# Agent 'Alpha' works on two tasks
store.save_state("task_1", "alpha", {"step": 1})
store.save_state("task_2", "alpha", {"step": 99})

# Agent 'Beta' works on Task 1
store.save_state("task_1", "beta", {"role": "reviewer"})

print(f"Alpha on Task 1: {store.get_state('task_1', 'alpha')}")
print(f"Alpha on Task 2: {store.get_state('task_2', 'alpha')}")
print(f"Beta on Task 1: {store.get_state('task_1', 'beta')}")

# Validation: Are they isolated?
assert store.get_state('task_1', 'alpha') != store.get_state('task_2', 'alpha')
```
