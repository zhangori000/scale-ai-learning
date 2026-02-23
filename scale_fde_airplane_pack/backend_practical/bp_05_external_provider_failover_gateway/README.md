# BP-05: External Provider Failover Gateway (Backend Practical Essay)

This chapter covers a backend gateway pattern where your service depends on external providers and must remain useful under partial outages. The practical objective is graceful degradation, not theoretical perfect availability.

Requirement summary:

primary provider call first. fail over to secondary on retryable failures. enforce timeout budget. use circuit breaker for repeated failures. return response with `source_provider`.

The subtle design issue is time budget decomposition. If your full request budget is 1 second, you cannot let primary consume all 1 second and still meaningfully try secondary.

A practical split:

primary budget T1. retry/backoff within T1 cap. secondary budget T2. ensure `T1 + T2 <= total_budget`.

Retry policy should be selective.

Retryable: timeout, 5xx, and usually 429.

Non-retryable: most 4xx validation/auth errors.

Circuit breaker protects your system from repeatedly hammering a failing provider.

Typical state machine:

CLOSED: normal traffic. OPEN: short-circuit calls for cooldown period. HALF_OPEN: probe limited requests; close on success, reopen on failure.

Implementation sketch:

```python
async def enrich(query: str):
    if not breaker_primary.allow_request():
        data = await call_with_retry(secondary_client, query)
        return {"data": data, "source_provider": "secondary", "partial": False}

    try:
        data = await call_with_retry(primary_client, query)
        breaker_primary.record_success()
        return {"data": data, "source_provider": "primary", "partial": False}
    except RetryableError:
        breaker_primary.record_failure()
        data = await call_with_retry(secondary_client, query)
        return {"data": data, "source_provider": "secondary", "partial": False}
```

If both providers fail, return `502` with request ID for traceability.

Do not hide fallback behavior from clients. Including `source_provider` improves debugging and observability.

Metrics to instrument by provider:

p50/p95/p99 latency. timeout rate. 4xx and 5xx rate. failover ratio. circuit-open ratio.

These metrics help tune thresholds and budget splits.

Test strategy:

primary success path no fallback. primary timeout triggers secondary. breaker open skips primary immediately. both fail -> expected error contract. 4xx from primary does not retry/failover when policy says non-retryable.

Interview close:

"I implement failover as a budgeted control policy: bounded retries on retryable failures, circuit breaker to stop cascading harm, and deterministic secondary fallback with explicit source attribution in responses."

## Deep Dive Appendix

This addendum covers advanced failover routing concerns.

### Total Timeout Budgeting

Always partition timeout budget across primary, retries, and secondary. Otherwise failover becomes useless because no time remains for secondary call.

### Retry Storm Protection

When primary degrades, retries can multiply load. Controls:

bounded retries. jittered backoff. circuit breaker short-circuit. concurrency caps per provider.

### Response Semantics

Return `source_provider` to make fallback visible. Optionally return `degraded=true` when secondary is lower quality.

### Data Consistency Across Providers

Primary and secondary may return slightly different schemas/quality. Normalize output model in gateway to shield callers.

### Health-Aware Routing

Beyond binary failover, consider weighted routing by recent health metrics and cost.

### Metrics

failover ratio. breaker open time. timeout percentile per provider. provider error-class distribution.

### Learning summary

"Failover is a control policy problem: budget, retries, and breaker state must work together. I optimize for graceful degradation, not blind retries."

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

