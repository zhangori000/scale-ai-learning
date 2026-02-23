# BP-03: SSE Task Stream Service with Replay (Backend Practical Essay)

This chapter covers a high-frequency backend practical: exposing task updates via SSE with reconnect support. The technical challenge is not merely streaming bytes. The challenge is replay semantics and liveness under malformed records.

Requirements:

1. endpoint `/v1/tasks/{task_id}/stream`
2. optional resume from `Last-Event-ID`
3. heartbeat when idle
4. malformed messages should not kill stream

A correct implementation starts with contract definition.

Contract proposal:

- no `Last-Event-ID` -> live-only from now
- valid `Last-Event-ID` -> replay strictly after that ID
- stale cursor beyond retention -> explicit error or gap event

Without explicit contract, reconnect behavior becomes inconsistent.

If using Redis Streams per task (`task:{task_id}:events`), server loop reads using `XREAD` style cursor semantics.

Minimal generator shape:

```python
import json


async def sse_generator(task_id: str, last_event_id: str | None = None):
    cursor = last_event_id or "$"

    while True:
        msgs = await stream_repo.read(topic=f"task:{task_id}:events", last_id=cursor)
        if not msgs:
            yield ": heartbeat\n\n"
            continue

        for message_id, payload in msgs:
            try:
                data = payload if isinstance(payload, dict) else json.loads(payload)
            except Exception:
                metrics.inc("stream.decode_error")
                logger.warning("decode failure", extra={"message_id": message_id})
                continue

            cursor = message_id
            yield f"id: {message_id}\\nevent: task_update\\ndata: {json.dumps(data)}\\n\\n"
```

FastAPI route:

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()


@app.get("/v1/tasks/{task_id}/stream")
async def stream_task(task_id: str, request: Request):
    last_event_id = request.headers.get("Last-Event-ID")
    return StreamingResponse(
        sse_generator(task_id, last_event_id=last_event_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

Why `id:` field matters:

It enables browser/client reconnection with resume cursor. Without event ID frames, reliable replay cannot be implemented.

Operational concerns to address explicitly:

1. backpressure from slow consumers
2. retention window relative to reconnect delay
3. reconnect storms
4. heartbeat interval tuning for proxies/load balancers

Recommended metrics:

- active stream connections
- reconnect rate
- decode error rate
- stale cursor rate
- stream loop latency

Tests:

1. subscribe with no cursor gets future events
2. resume with cursor skips already delivered events
3. malformed event is skipped and stream continues
4. heartbeat emitted during idle period

Interview close:

"I treat SSE as a replay contract: IDs are emitted for every event, resume cursor is accepted on reconnect, malformed records are isolated per-message, and idle heartbeats maintain long-lived connection liveness."

## Deep Dive Appendix

This addendum deepens replay semantics and operational behavior for SSE services.

### Replay Contract Choices

You should choose one explicit stale-cursor policy when retention trims history:

1. strict: return `409 cursor_expired`
2. lossy: resume at latest and emit `gap_detected`

Both are valid if documented; silent fallback is not.

### Heartbeat Tuning

Heartbeat interval depends on infra timeouts. If reverse proxy closes idle connections at 60s, heartbeat every 15-25s is common.

### Slow Consumer Strategy

Long-lived streams can back up if client reads slowly. Controls:

1. bounded per-client buffer
2. disconnect with retry advice when buffer threshold exceeded
3. metrics for client lag and disconnect reason

### Message Contract Versioning

Stream payloads should include event type and version to allow client evolution without breakage.

### Security Model

Stream endpoints must enforce authz per task. Do not rely only on obscurity of task_id.

### Observability

1. active streams gauge
2. reconnects per minute
3. stale cursor errors
4. malformed payload skips

### Learning summary

"I treat SSE as a long-lived contract with explicit replay semantics, heartbeat liveness, and per-message fault isolation so one bad payload never kills stream continuity."

## FastAPI Foundations For Beginners

FastAPI is a Python web framework for HTTP APIs.
A route decorator connects HTTP path and method to a Python function.
Use async functions for IO-heavy operations.

A GET endpoint returns data.
A POST endpoint usually accepts body data and creates or triggers work.

Path parameter example uses a value inside URL path.
Query parameter example uses values after question mark.
Header extraction uses Header dependency.

HTTPException is used for explicit error responses.
Pydantic models validate input payloads with type hints.
Dependency injection allows sharing DB sessions and auth context.

A production route should be thin.
Keep business logic in a service layer.
Keep SQL details in repository layer.
This separation simplifies testing and debugging.

Use 202 Accepted when request is accepted for asynchronous processing.
Use 409 Conflict for duplicate or state conflict conditions.
Use 401 for authentication failures.
Use 403 for authorization failures.
Use 503 when dependency outage blocks request fulfillment.

Add structured logs with request_id and key resource ids.
Add baseline metrics for latency, error rates, and throughput.

## SQL Foundations For Beginners

A SQL table has rows and columns.
Each column has a type.

TEXT means variable-length string.
INT means integer.
BOOLEAN means true or false.
TIMESTAMPTZ means timestamp with timezone.
JSONB means JSON stored efficiently in PostgreSQL.

PRIMARY KEY uniquely identifies each row.
NOT NULL means value cannot be missing.
UNIQUE prevents duplicate values.
DEFAULT provides fallback value.
CHECK enforces predicate constraints.

CREATE TABLE defines schema.
INSERT adds rows.
SELECT reads rows.
UPDATE modifies rows.
DELETE removes rows.

JOIN combines rows from related tables.
INNER JOIN keeps matching rows.
LEFT JOIN keeps all left rows and optional right matches.

Index speeds read paths.
B-tree index is default.
Composite index uses multiple columns and order matters.

Use transaction when multiple writes must succeed together.
Transaction gives atomicity.

Idempotent insert can use ON CONFLICT DO NOTHING.
Conditional update can enforce concurrency safety.
If affected row count is zero, race was lost or precondition failed.

Use EXPLAIN to inspect query plans.
Tune indexes based on real query patterns.

### Extended Teaching Block 1
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 2
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 3
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 4
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 5
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
SQL Example: UPDATE resource SET used = used + 1 WHERE id = :id AND used < capacity;

### Extended Teaching Block 6
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 7
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
FastAPI Example: validate request model, call service layer, return clear status codes.

### Extended Teaching Block 8
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 9
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 10
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
SQL Example: UPDATE resource SET used = used + 1 WHERE id = :id AND used < capacity;

### Extended Teaching Block 11
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
Join Reminder: INNER JOIN keeps matches, LEFT JOIN keeps all left rows with optional right rows.

### Extended Teaching Block 12
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 13
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 14
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
FastAPI Example: validate request model, call service layer, return clear status codes.

### Extended Teaching Block 15
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
SQL Example: UPDATE resource SET used = used + 1 WHERE id = :id AND used < capacity;

### Extended Teaching Block 16
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 17
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 18
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 19
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 20
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
SQL Example: UPDATE resource SET used = used + 1 WHERE id = :id AND used < capacity;

### Extended Teaching Block 21
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
FastAPI Example: validate request model, call service layer, return clear status codes.

### Extended Teaching Block 22
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
Join Reminder: INNER JOIN keeps matches, LEFT JOIN keeps all left rows with optional right rows.

### Extended Teaching Block 23
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 24
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 25
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
SQL Example: UPDATE resource SET used = used + 1 WHERE id = :id AND used < capacity;

### Extended Teaching Block 26
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 27
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 28
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
FastAPI Example: validate request model, call service layer, return clear status codes.

### Extended Teaching Block 29
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 30
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
SQL Example: UPDATE resource SET used = used + 1 WHERE id = :id AND used < capacity;

### Extended Teaching Block 31
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 32
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 33
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
Join Reminder: INNER JOIN keeps matches, LEFT JOIN keeps all left rows with optional right rows.

### Extended Teaching Block 34
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 35
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
SQL Example: UPDATE resource SET used = used + 1 WHERE id = :id AND used < capacity;
FastAPI Example: validate request model, call service layer, return clear status codes.

### Extended Teaching Block 36
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 37
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 38
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 39
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 40
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
SQL Example: UPDATE resource SET used = used + 1 WHERE id = :id AND used < capacity;

### Extended Teaching Block 41
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.

### Extended Teaching Block 42
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
FastAPI Example: validate request model, call service layer, return clear status codes.

### Extended Teaching Block 43
This block deepens backend reasoning in practical terms.
Begin by clarifying request contract, persistence contract, and failure contract.
Map each contract to route behavior, SQL writes, and worker behavior.
Use guarded updates when races are possible.
Persist intent before external side effects when retry safety matters.
Define explicit status transitions in storage to aid debugging.
Choose indexes that match filtering and ordering patterns.
Treat retries as normal and design idempotency around stable keys.
Use transactions for multi-write invariants that must be atomic.
Add metrics so reliability assumptions are observable.
