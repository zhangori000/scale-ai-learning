# Exercise 03: Protocol Kernel + Adapter Boundary

## Why this is the right layer
After a ground-up read of both repos, the two deepest layers are:

1. **Most fundamental layer**: protocol contracts and invariants  
   - ACP methods and payload contracts (`task/create`, `event/send`, `message/send`, `task/cancel`)
   - streaming update semantics (`start`, `delta`, `full`, `done`)
   - identity/scoping invariants (`task_id`, `agent_id`, message index)
2. **Second most fundamental layer**: transport/storage adapter boundaries  
   - ports/interfaces for streams, persistence, and orchestration
   - adapters for Redis/HTTP/Temporal/postgres/mongo around those ports

This exercise forces you to build these two layers directly.

## Timebox
- 90 minutes

## Implement
Create `protocol_kernel.py` with:

1. A **pure protocol kernel** (no I/O):
   - accepts stream updates
   - validates idempotency + ordering + transition rules
   - emits deterministic actions
2. An **adapter-boundary service**:
   - executes kernel actions through ports
   - uses per-stream lock for concurrency safety

## Required models
- `UpdateType`: `start`, `delta`, `full`, `done`
- `DeltaKind`: `text`, `data`, `tool_request`, `tool_response`, `reasoning_summary`, `reasoning_content`
- `StreamUpdate`: `{update_id, seq, index, type, delta_kind?, content?}`
- `ApplyStatus`: `applied`, `duplicate`, `rejected`
- `KernelAction`: at minimum support:
  - `create_parent`
  - `emit_start`
  - `emit_delta`
  - `emit_full`
  - `emit_done`
  - `persist_done`

## Kernel rules (strict)
1. `update_id` duplicate -> `duplicate` (no mutation).
2. `seq < last_seq` -> `rejected`.
3. Once an index is terminal (`done`), any non-duplicate update on that index is rejected.
4. `delta` before `start` must auto-create parent and emit synthetic `start`.
5. Delta type rules:
   - same delta type can continue
   - `reasoning_summary` and `reasoning_content` may mix
   - any other cross-type mix is rejected
6. `full` is terminal for that index and must produce `persist_done`.
7. `done` flushes accumulated deltas into final content and must produce `persist_done`.

## Adapter boundary rules
Define ports:

```python
class MessageStorePort(Protocol):
    async def create_in_progress(self, task_id: str, index: int, content: str) -> str: ...
    async def mark_done(self, task_id: str, message_id: str, content: str) -> None: ...

class StreamOutPort(Protocol):
    async def publish(self, task_id: str, payload: dict) -> None: ...
```

Service behavior:
1. Per `(task_id, request_id)` lock.
2. Index -> message_id mapping.
3. Executes kernel actions in order.
4. Never bypasses ports.

## Validation scenarios
1. Delta-only path:
   - `delta("Hel")`, `delta("lo")`, `done`
   - must auto-start and persist `"Hello"`.
2. Full overrides:
   - `start("x")`, `delta("wrong")`, `full("correct")`
   - final content `"correct"`.
3. Duplicate:
   - same `update_id` twice
   - first `applied`, second `duplicate`.
4. Out-of-order:
   - seq 5 then seq 4
   - second rejected.
5. Illegal delta mix:
   - `text` then `tool_response`
   - rejected.
6. Terminal reject:
   - after terminal, any new non-duplicate update rejected.

## Definition of done
All six scenarios pass in one async self-test.
