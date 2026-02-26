# Exercise 33: Delta Accumulation Logic

In `scale-agentex`, streaming isn't just about text. It's about **States**.
Imagine the Agent is filling out a form:
1. `{"status": "thinking"}`
2. `{"progress": 20}`
3. `{"progress": 50, "status": "searching"}`

Instead of sending the *entire* state every time (which is slow), Agentex sends **Deltas** (only what changed).

## The Challenge
Implement a `DeltaManager`. 
- It receives a stream of partial dictionaries.
- It maintains a `full_state` object.
- Every time a delta arrives, it updates the `full_state`.
- It yields a "Response Package" containing both the delta and the current full state.

## Starter Code
```python
from typing import Dict, Any, Iterator

class DeltaManager:
    def __init__(self):
        self.full_state: Dict[str, Any] = {}

    def apply_delta(self, delta: Dict[str, Any]) -> Dict[str, Any]:
        """
        TODO: 
        1. Merge 'delta' into 'self.full_state'.
        2. If a key in delta is a dictionary, merge it recursively (Optional challenge).
        3. Return the updated full_state.
        """
        pass

# --- Simulation ---
deltas = [
    {"status": "initializing", "user": "admin"},
    {"status": "processing", "progress": 10},
    {"progress": 25},
    {"metadata": {"model": "gpt-4"}}, # Nested update
    {"status": "complete", "progress": 100}
]

manager = DeltaManager()
print("--- Starting Delta Stream ---")
for d in deltas:
    updated = manager.apply_delta(d)
    print(f"Delta: {d} 
  => Full State: {updated}
")
```
