# Solution: Backend ACP-Type Method Gating

## Core enforcement points
- Matrix definition: `ACP_TYPE_TO_ALLOWED_RPC_METHODS` in `entities/agents_rpc.py`
- Gate logic: `_validate_rpc_method_for_acp_type(...)` in `agents_acp_use_case.py`
- Gate call site: `handle_rpc_request(...)` before method dispatch

## Recommended test structure
Use parameterized tests in `test_agents_acp_use_case.py`.

### 1) Allowed matrix test
Verify no exception for:
- `(SYNC, TASK_CREATE)`
- `(SYNC, MESSAGE_SEND)`
- `(ASYNC, TASK_CREATE | TASK_CANCEL | EVENT_SEND)`
- `(AGENTIC, TASK_CREATE | TASK_CANCEL | EVENT_SEND)`

### 2) Disallowed matrix test
Verify `ClientError` for:
- `(SYNC, EVENT_SEND)`
- `(SYNC, TASK_CANCEL)`
- `(ASYNC, MESSAGE_SEND)` from direct agent-rpc route semantics
- `(AGENTIC, MESSAGE_SEND)` from direct agent-rpc route semantics

### 3) Dispatch short-circuit test
Patch a handler method (`_handle_event_send` for sync agent) and assert it is not called when gating fails.

## Example assertion pattern

```python
with pytest.raises(ClientError, match="Unsupported method"):
    use_case._validate_rpc_method_for_acp_type(acp_type, method)
```

And for short-circuit:

```python
use_case._handle_event_send = AsyncMock()
with pytest.raises(ClientError):
    await use_case.handle_rpc_request(...)
use_case._handle_event_send.assert_not_called()
```

## Why this is protocol validation
This layer validates semantic compatibility between agent capability (`acp_type`) and requested RPC method, preventing illegal protocol operations even when payload schemas are valid.
