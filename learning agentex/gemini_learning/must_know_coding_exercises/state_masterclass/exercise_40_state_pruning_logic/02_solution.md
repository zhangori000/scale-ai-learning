# Solution: State Pruning Logic (Memory Management)

Pruning is the most common way Agentex developers stay under the 16MB limit for long-running agents.

## The Solution

```python
class PruningManager:
    def prune(self, state: dict, max_history: int = 5) -> dict:
        history = state.get("history", [])
        
        if len(history) > max_history:
            num_to_remove = len(history) - max_history
            
            # 1. Update the Summary (Context preservation)
            removed_content = ", ".join(history[:num_to_remove])
            state["summary"] += f" [Archived: {removed_content}]"
            
            # 2. Slice the History (The actual pruning)
            # Keeping only the most recent 'max_history' items
            state["history"] = history[-max_history:]
            
            print(f"  [Pruner] Removed {num_to_remove} old messages.")
            
        return state
```

## Why this is Agentex-style:
1. **Durable Memory**: Unlike a simple ChatGPT session, Agentex state is persistent. If you don't prune, it grows forever.
2. **Infinite Conversations**: By combining pruning with a "Summary" field, you create a "Rolling Window" of memory. The agent remembers the *essence* of the past (via the summary) but keeps the *details* of the present (via the history).
3. **Safety**: Pruning is usually done in the `@acp.on_message_send` hook, ensuring the state stays healthy before it's saved to the database.
