# Solution: The Streaming Delta Accumulator (LeetCode OOD)

This solution demonstrates how `scale-agentex` handles the "messiness" of streaming AI. In a real-world scenario, an LLM might send 100 small JSON fragments per second. The platform must be able to "Reconstruct" these fragments perfectly without losing a single character.

## The Implementation

```python
from typing import List, Dict, Any

class DeltaAccumulator:
    """
    A stateful accumulator that reconstructs messages from a stream of fragments.
    """
    def __init__(self):
        # Maps index (int) -> state dictionary
        self.registry: Dict[int, Dict[str, Any]] = {}

    def _ensure_index(self, index: int):
        """Initializes a new entry if it's the first time we see this index."""
        if index not in self.registry:
            self.registry[index] = {
                "index": index,
                "text": "",
                "tool_args": "",
                "status": "PENDING"
            }

    def process_update(self, update: Dict[str, Any]):
        """
        Main logic for merging deltas into the state.
        """
        idx = update.get("index")
        type_ = update.get("type")
        content = update.get("content", "")

        # 1. Setup the bucket for this index
        self._ensure_index(idx)
        bucket = self.registry[idx]

        # 2. Update logic based on type
        if type_ == "TEXT_DELTA":
            bucket["text"] += content
            
        elif type_ == "TOOL_DELTA":
            bucket["tool_args"] += content
            
        elif type_ == "DONE":
            bucket["status"] = "FINISHED"
            
        # START doesn't do much in this simple version, 
        # but in real Agentex it might set metadata.

    def get_final_messages(self) -> List[Dict[str, Any]]:
        """
        Filters out pending messages and returns the finished ones, 
        sorted correctly by their index.
        """
        # 1. Collect only those that are 'FINISHED'
        finished = [
            # Clean up the output by removing the 'status' internal field
            {k: v for k, v in item.items() if k != "status"}
            for item in self.registry.values()
            if item["status"] == "FINISHED"
        ]

        # 2. Sort by index (In streaming, things can arrive out of order!)
        finished.sort(key=lambda x: x["index"])
        
        return finished

# --- 3. The "LeetCode" Test Case ---
updates = [
    {"index": 0, "type": "START"},
    {"index": 1, "type": "START"},
    {"index": 0, "type": "TEXT_DELTA", "content": "The weather "},
    {"index": 1, "type": "TOOL_DELTA", "content": '{"loc": "SF"}'},
    {"index": 0, "type": "TEXT_DELTA", "content": "is sunny."},
    {"index": 0, "type": "DONE"},
    {"index": 1, "type": "DONE"},
]

accumulator = DeltaAccumulator()
for u in updates:
    accumulator.process_update(u)

final_results = accumulator.get_final_messages()

print("--- RECONSTRUCTED MESSAGES ---")
for msg in final_results:
    print(f"Index {msg['index']}:")
    if msg['text']: print(f"  Text: '{msg['text']}'")
    if msg['tool_args']: print(f"  Tool Args: '{msg['tool_args']}'")

# VERIFICATION:
assert final_results[0]["text"] == "The weather is sunny."
assert final_results[1]["tool_args"] == '{"loc": "SF"}'
print("
[SUCCESS] All deltas correctly accumulated and ordered.")
```

### Key Takeaways from the Solution

1.  **State Management:** This is the core of OOD. Instead of just "processing" a request, you are maintaining a "Registry" of what has happened in the past.
2.  **Order Consistency:** In complex network architectures, messages might arrive at the server out of order (e.g., Index 1 arrives before Index 0). By sorting in `get_final_messages`, we ensure the UI always sees the correct sequence.
3.  **Encapsulation:** The `_ensure_index` private method hides the boring initialization logic, keeping the `process_update` method focused on the business rules.
4.  **Why this matters for Scale-Agentex:** Agents are high-concurrency systems. An agent might be streaming "Thinking..." text while *simultaneously* generating a tool call for a database search. This "Delta Accumulator" pattern is the only way to merge these separate streams of data into a single, valid JSON message that the platform can save.
