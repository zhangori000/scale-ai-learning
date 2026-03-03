# Solution: Streaming Contract Fault Injection

## Layer-by-layer expected behavior

### Layer A: SDK ACP server (`BaseACPServer`)
- In `_handle_streaming_response(...)`, each emitted chunk is validated by:
  - `task_message_update_adapter.validate_python(chunk)`
- Non-conforming chunks should produce a JSON-RPC error stream record.

### Layer B: Backend ACP client (`AgentACPService`)
- `_call_jsonrpc_stream(...)` validates each NDJSON record as `JSONRPCResponse`.
- It enforces response id equality (`rpc_response.id == request_id`).
- `_parse_task_message_update(...)` rejects unknown update `type`.

### Layer C: Backend stream materialization (`AgentsACPUseCase`)
- `DeltaAccumulator.add_delta(...)` enforces same delta type per message index.
- Mismatch raises `ClientError` to prevent invalid message assembly.

## Test implementation sketch

## 1) Invalid stream chunk shape
Create a test ACP handler returning a bad chunk (e.g., plain string) and assert SDK returns stream error.

## 2) Mismatched response id
Mock `stream_call(...)` to emit chunk with a different `id`; assert `_call_jsonrpc_stream` raises `ValueError` with id mismatch.

## 3) Unknown update type
Call `_parse_task_message_update({"type": "nope"})` and assert `ValueError("Unknown update type")`.

## 4) Delta mismatch
Use `DeltaAccumulator` through `_handle_message_send_stream` path with:
- first delta type `text`
- second delta type `data`
Assert `ClientError("Delta type mismatch")`.

## Why this is protocol validation
These checks prevent a downstream agent from drifting away from ACP streaming contracts while still "looking alive" at HTTP level.  
They protect data integrity of persisted messages and replayable history.
