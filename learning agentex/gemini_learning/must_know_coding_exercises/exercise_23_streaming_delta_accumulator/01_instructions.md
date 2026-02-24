# Exercise: The Streaming Delta Accumulator (LeetCode OOD)

In `scale-agentex` (`src/domain/use_cases/agents_acp_use_case.py`), the platform receives a stream of "Deltas" from the agent. An agent might be doing two things at once (e.g., typing a message while preparing a tool call). 

The platform must **accumulate** these fragments into a final, valid state for each message index.

## The Problem
You receive a list of "Update" objects. Each update has:
1.  `index`: Which message it belongs to (0, 1, 2...).
2.  `type`: The kind of update (`START`, `TEXT_DELTA`, `TOOL_DELTA`, `DONE`).
3.  `content`: The partial string fragment.

## The Goal
Build a `DeltaAccumulator` class that processes these updates and returns a list of "Final Messages" in the correct order.

## Requirements
1.  **State Tracking:** Keep track of multiple message indexes simultaneously.
2.  **Merging:** 
    *   `TEXT_DELTA` should append to the message's `text`.
    *   `TOOL_DELTA` should append to the message's `tool_args`.
3.  **Completion:** A message is only "Finished" when you receive a `DONE` update for that index.
4.  **The Output:** `get_final_messages()` should return a list of dictionaries, one for each index that has finished.

## Starter Code
```python
from typing import List, Dict, Any

class DeltaAccumulator:
    def __init__(self):
        # TODO: Store state for each index
        # index -> {"text": "", "tool_args": "", "status": "PENDING"}
        self.registry = {}

    def process_update(self, update: Dict[str, Any]):
        """
        Example Update: {"index": 0, "type": "TEXT_DELTA", "content": "Hello"}
        """
        # TODO: 
        # 1. If index not in registry, initialize it.
        # 2. If TEXT_DELTA, append to 'text'.
        # 3. If TOOL_DELTA, append to 'tool_args'.
        # 4. If DONE, mark as 'FINISHED'.
        pass

    def get_final_messages(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all FINISHED messages, ordered by index.
        """
        # TODO: Implement
        pass

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

# Expected Output:
# [
#   {"index": 0, "text": "The weather is sunny.", "tool_args": ""},
#   {"index": 1, "text": "", "tool_args": '{"loc": "SF"}'}
# ]
print(accumulator.get_final_messages())
```
