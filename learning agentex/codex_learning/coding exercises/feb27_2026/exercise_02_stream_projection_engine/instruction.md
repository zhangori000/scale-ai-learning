# Exercise 02: Stream Projection Engine (Senior Interview Level)

## Why this exercise
Senior engineers in Agentex-like systems must design deterministic projection logic for streamed updates. The hard part is not parsing events. The hard part is correctness under retries, out-of-order delivery, and concurrency.

## Timebox
- 75 minutes
- 15 min: requirements + invariants
- 45 min: implementation
- 15 min: validation scenarios

## Problem statement
Implement `stream_projection.py` that consumes message stream events and builds the canonical task message projection.

You must support these event types:
- `start`
- `delta`
- `full`
- `done`

Use event fields:
- `event_id: str`
- `task_id: str`
- `message_id: str`
- `seq: int`
- `type: Literal["start","delta","full","done"]`
- `payload: dict[str, object]`

## Projection model
Per `(task_id, message_id)` keep:
- `status: Literal["NOT_STARTED","IN_PROGRESS","DONE"]`
- `content: str`
- `last_seq: int`
- `applied_event_ids: set[str]`
- `history: list[...]`

## Required semantics
1. `start`
   - Valid only when status is `NOT_STARTED`
   - Moves status to `IN_PROGRESS`
2. `delta`
   - Valid only in `IN_PROGRESS`
   - Appends `payload["text"]` to content
3. `full`
   - Valid in `IN_PROGRESS`
   - Replaces content with `payload["text"]`
4. `done`
   - Valid in `IN_PROGRESS`
   - Moves status to `DONE`
5. Terminal behavior
   - Once `DONE`, any non-duplicate future event is rejected.

## Non-negotiable invariants
1. Idempotency:
   - duplicate `event_id` for same `(task_id, message_id)` returns `DUPLICATE` and does not mutate.
2. Ordering:
   - if `seq < last_seq`, return `REJECTED` (`out_of_order`).
3. Concurrency:
   - per-message lock with `asyncio.Lock`.
   - same message must serialize; different messages can proceed concurrently.
4. Auditability:
   - every applied event must append a history record.

## Required API
```python
class ProjectionEngine:
    async def apply(self, event: StreamEvent) -> ApplyResult: ...
    def get_message(self, task_id: str, message_id: str) -> MessageProjection: ...
    def get_history(self, task_id: str, message_id: str) -> list[HistoryRecord]: ...
    def get_task_messages(self, task_id: str) -> dict[str, MessageProjection]: ...
```

## Validation scenarios (must pass)
1. Happy path:
   - `start -> delta("Hel") -> delta("lo") -> done`
   - final content is `"Hello"`, status `DONE`.
2. Full replacement:
   - `start -> delta("wrong") -> full("correct") -> done`
   - final content is `"correct"`.
3. Duplicate handling:
   - same `event_id` applied twice
   - first `APPLIED`, second `DUPLICATE`.
4. Out-of-order:
   - apply `seq=5` then `seq=4`
   - second rejected.
5. Post-terminal reject:
   - after `done`, apply `delta`
   - rejected.
6. Isolation:
   - same task, two message IDs
   - state and history independent.

## Definition of done
All six scenarios pass with assertions in one runnable async test harness.
