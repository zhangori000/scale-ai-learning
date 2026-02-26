# Exercise 40: State Pruning Logic (Memory Management)

Because of the 16MB limit, an Agent that talks for hours will eventually crash. To prevent this, developers must implement **Pruning Logic** (e.g., "Forget everything but the last 10 messages").

## The Challenge
Implement a `PruningManager`.
1. It takes a state object and a `max_history` limit.
2. If `len(state["history"]) > max_history`, it removes the oldest entries.
3. **Advanced**: It should summarize the deleted entries into a `summary` field so the context isn't completely lost.

## Starter Code
```python
class PruningManager:
    def prune(self, state: dict, max_history: int = 5) -> dict:
        """
        TODO: 
        1. If 'history' count exceeds max_history:
           - Calculate how many to remove.
           - Prepend a note to 'summary' about what was removed.
           - Slice the 'history' list.
        """
        pass

# --- Simulation ---
pm = PruningManager()
state = {
    "summary": "Conversation started.",
    "history": [f"Message {i}" for i in range(10)] # 10 messages
}

pruned = pm.prune(state, max_history=3)

print(f"Summary: {pruned['summary']}")
print(f"History Remaining: {len(pruned['history'])}")
print(f"Messages: {pruned['history']}")

assert len(pruned['history']) == 3
```
