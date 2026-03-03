# Solution: Discriminated Unions and Streaming Shapes

## Reference script sketch

```python
from pydantic import TypeAdapter

from agentex.types.task_message_content import TaskMessageContent
from agentex.types.task_message_delta import TaskMessageDelta
from agentex.types.task_message_update import TaskMessageUpdate

content_adapter = TypeAdapter(TaskMessageContent)
delta_adapter = TypeAdapter(TaskMessageDelta)
update_adapter = TypeAdapter(TaskMessageUpdate)

valid_content = [
    {"type": "text", "author": "agent", "content": "hello"},
    {"type": "reasoning", "author": "agent", "summary": ["step 1"]},
    {"type": "data", "author": "agent", "data": {"ok": True}},
    {"type": "tool_request", "author": "agent", "name": "search", "tool_call_id": "1", "arguments": {"q": "hi"}},
    {"type": "tool_response", "author": "agent", "name": "search", "tool_call_id": "1", "content": {"hits": 3}},
]

valid_delta = [
    {"type": "text", "text_delta": "h"},
    {"type": "data", "data_delta": "{\"partial\": true}"},
    {"type": "tool_request", "name": "search", "tool_call_id": "1", "arguments_delta": "{\"q\":\"h\"}"},
    {"type": "tool_response", "name": "search", "tool_call_id": "1", "content_delta": "{\"hits\":1}"},
    {"type": "reasoning_summary", "summary_index": 0, "summary_delta": "thinking"},
    {"type": "reasoning_content", "content_index": 0, "content_delta": "more thinking"},
]

valid_updates = [
    {"type": "start", "content": valid_content[0], "index": 0},
    {"type": "delta", "delta": valid_delta[0], "index": 0},
    {"type": "full", "content": valid_content[2], "index": 0},
    {"type": "done", "index": 0},
]

invalid_cases = [
    ("content missing author", content_adapter, {"type": "text", "content": "oops"}),
    ("unknown delta type", delta_adapter, {"type": "unknown", "x": 1}),
    ("update delta with wrong shape", update_adapter, {"type": "delta", "delta": {"type": "tool_request"}}),
]

for payload in valid_content:
    print("content ok:", type(content_adapter.validate_python(payload)).__name__)

for payload in valid_delta:
    print("delta ok:", type(delta_adapter.validate_python(payload)).__name__)

for payload in valid_updates:
    print("update ok:", type(update_adapter.validate_python(payload)).__name__)

for label, adapter, payload in invalid_cases:
    try:
        adapter.validate_python(payload)
        print("UNEXPECTED PASS:", label)
    except Exception as e:
        print("expected failure:", label, type(e).__name__)
```

## What good output looks like

- 5 successful `TaskMessageContent` parses.
- 6 successful `TaskMessageDelta` parses.
- 4 successful `TaskMessageUpdate` parses.
- 3 expected failures with validation errors.

## Why this matters

You validate the three main polymorphic contracts in the SDK:
- user-visible message content
- incremental message deltas
- streaming event envelopes

If these parse correctly, higher-level ADK/ACP logic has a stable shape to operate on.
