# BP-06: Batch Job Orchestrator API (Backend Practical Essay)

This chapter is a practical guide for implementing asynchronous job orchestration APIs. The pattern is common in internal tools and enterprise systems where long-running operations must be started quickly, monitored reliably, and canceled safely.

Core endpoints:

`POST /v1/jobs` to create job and return immediately. `GET /v1/jobs/{job_id}` to poll state. `POST /v1/jobs/{job_id}/cancel` to request cancellation.

Status model:

`QUEUED`. `RUNNING`. `SUCCEEDED`. `FAILED`. `CANCEL_REQUESTED`. `CANCELED`.

The primary challenge is state transition correctness under concurrent workers and cancellation races.

Baseline schema:

```sql
CREATE TABLE jobs (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  payload JSONB NOT NULL,
  status TEXT NOT NULL,
  progress INT NOT NULL DEFAULT 0,
  result JSONB NULL,
  error TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Create endpoint should do minimal synchronous work:

validate request. insert `QUEUED` row. enqueue job id. return job_id and queued status.

Worker correctness hinges on compare-and-swap transition from `QUEUED` to `RUNNING`.

```sql
UPDATE jobs
SET status='RUNNING'
WHERE id=:job_id AND status='QUEUED';
```

Only one worker should win this transition. Others should skip.

During execution, worker should periodically:

update progress. check whether status became `CANCEL_REQUESTED`. stop gracefully and transition to `CANCELED` if requested.

Terminal transition rules:

only one terminal status write allowed. terminal jobs should reject further cancel attempts.

Pseudo worker:

```python
async def run_job(job_id: str):
    won = await repo.try_mark_running(job_id)
    if not won:
        return

    try:
        for step in steps:
            if await repo.is_cancel_requested(job_id):
                await repo.mark_canceled(job_id)
                return
            await execute_step(step)
            await repo.update_progress(job_id, step.progress)

        await repo.mark_succeeded(job_id, result={"ok": True})
    except Exception as exc:
        await repo.mark_failed(job_id, error=str(exc))
```

Cancellation endpoint semantics:

if job in `QUEUED` or `RUNNING`, set `CANCEL_REQUESTED`. if terminal, return conflict or no-op according to API contract.

Test plan:

create returns quickly and job appears queued. worker moves job through valid lifecycle. double worker pickup prevented by CAS transition. cancel request during run leads to canceled terminal state. terminal job cannot be canceled again.

Operational metrics:

queue depth. pickup latency. run duration by job type. success/failure/cancel rates.

Interview close:

"I treat job orchestration as a state machine with guarded transitions. API paths are lightweight, workers own execution, and compare-and-swap status updates prevent duplicate execution under concurrency. Cancellation is cooperative and observable through explicit intermediate state."

## Deep Dive Appendix

This addendum expands job orchestration into a state-machine and operations topic.

### State Machine Discipline

Define legal transitions explicitly, for example:

QUEUED -> RUNNING. RUNNING -> SUCCEEDED | FAILED | CANCELED. RUNNING/QUEUED -> CANCEL_REQUESTED. CANCEL_REQUESTED -> CANCELED.

Reject invalid transitions at repository layer.

### Idempotent Worker Start

Workers may receive duplicate queue deliveries. CAS transition on status ensures only one worker executes.

### Progress Semantics

Progress should be monotonic and bounded [0,100]. For multi-stage jobs, represent progress as weighted stage completion.

### Cancellation Semantics

Cancellation is cooperative in most systems. Worker should check cancel flag between units of work and stop gracefully.

### Retry Policy for Failed Jobs

If retries are required, include attempt count and backoff schedule fields. Avoid infinite retry loops without dead-letter terminal state.

### Observability

queue wait time. run duration by job type. failure reason taxonomy. cancellation latency.

### Learning summary

"I model jobs as a strict state machine with CAS-guarded pickup, cooperative cancellation, and observable lifecycle metrics so control-plane APIs remain reliable under concurrency."

## FastAPI Foundations For Beginners

FastAPI is a Python web framework for HTTP APIs. A route decorator connects HTTP path and method to a Python function. Use async functions for IO-heavy operations.

A GET endpoint returns data. A POST endpoint usually accepts body data and creates or triggers work.

Path parameter example uses a value inside URL path. Query parameter example uses values after question mark. Header extraction uses Header dependency.

HTTPException is used for explicit error responses. Pydantic models validate input payloads with type hints. Dependency injection allows sharing DB sessions and auth context.

A production route should be thin. Keep business logic in a service layer. Keep SQL details in repository layer. This separation simplifies testing and debugging.

Use 202 Accepted when request is accepted for asynchronous processing. Use 409 Conflict for duplicate or state conflict conditions. Use 401 for authentication failures. Use 403 for authorization failures. Use 503 when dependency outage blocks request fulfillment.

Add structured logs with request_id and key resource ids. Add baseline metrics for latency, error rates, and throughput.

## SQL Foundations For Beginners

A SQL table has rows and columns. Each column has a type.

TEXT means variable-length string. INT means integer. BOOLEAN means true or false. TIMESTAMPTZ means timestamp with timezone. JSONB means JSON stored efficiently in PostgreSQL.

PRIMARY KEY uniquely identifies each row. NOT NULL means value cannot be missing. UNIQUE prevents duplicate values. DEFAULT provides fallback value. CHECK enforces predicate constraints.

CREATE TABLE defines schema. INSERT adds rows. SELECT reads rows. UPDATE modifies rows. DELETE removes rows.

JOIN combines rows from related tables. INNER JOIN keeps matching rows. LEFT JOIN keeps all left rows and optional right matches.

Index speeds read paths. B-tree index is default. Composite index uses multiple columns and order matters.

Use transaction when multiple writes must succeed together. Transaction gives atomicity.

Idempotent insert can use ON CONFLICT DO NOTHING. Conditional update can enforce concurrency safety. If affected row count is zero, race was lost or precondition failed.

Use EXPLAIN to inspect query plans. Tune indexes based on real query patterns.

