# BP-04: Multi-Tenant RBAC Service (Backend Practical Essay)

This chapter is a practical authorization design walkthrough for multi-tenant APIs. The key challenge is preventing cross-tenant leakage while keeping authorization checks efficient enough for hot endpoints.

Core requirement:

Every authorization decision is keyed by `(tenant_id, principal_id, resource_type, resource_id, action)`.

Deny by default.

This is the right default in security-sensitive systems.

A common anti-pattern is trusting `tenant_id` from request body or query parameters. In strong systems, tenant identity comes from authenticated principal context (token claims, session context), not user-provided payload.

Permission schema:

```sql
CREATE TABLE permissions (
  tenant_id TEXT,
  principal_id TEXT,
  resource_type TEXT,
  resource_id TEXT,
  action TEXT,
  PRIMARY KEY (tenant_id, principal_id, resource_type, resource_id, action)
);
```

Authorization middleware/dependency flow:

1. extract `tenant_id` and `principal_id` from auth context
2. build permission tuple key
3. check short-lived cache
4. on cache miss, check DB
5. allow only if explicit match

Reference function:

```python
async def authorize(principal_id, tenant_id, resource_type, resource_id, action):
    key = f"{tenant_id}:{principal_id}:{resource_type}:{resource_id}:{action}"

    cached = await cache.get(key)
    if cached == "ALLOW":
        return True

    allowed = await repo.has_permission(
        tenant_id=tenant_id,
        principal_id=principal_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
    )

    if allowed:
        await cache.set(key, "ALLOW", ttl=60)
        return True

    return False
```

Why only cache ALLOW in this baseline?

- allows quick hot-path permissions
- reduces risk of negative-cache lockout after permission grants
- keeps revocation lag bounded by short TTL

If you cache DENY as well, TTL and invalidation design become more sensitive.

Security hardening checklist:

1. enforce tenant scoping in all data queries, not just authorization middleware
2. avoid wildcard permissions unless explicitly modeled and audited
3. write audit logs for denied write actions
4. include authorization reason codes for incident debugging

Test plan:

1. valid tenant+permission -> allowed
2. cross-tenant access attempt -> denied
3. missing permission -> denied
4. cache hit on repeated allow check
5. permission revocation reflected after TTL or invalidation

Useful extension topics for interviewer follow-up:

- group/role expansion
- hierarchical resource inheritance
- policy engines (OPA, Cedar)
- batched authorization checks for list endpoints

Interview close:

"I model authorization as explicit tenant-scoped tuple checks with deny-by-default semantics. Tenant identity comes from auth context, not user input. I use short-lived positive cache for performance and preserve strict tenant filters at query level to prevent cross-tenant leakage."

## Deep Dive Appendix

This addendum expands RBAC design toward enterprise realism.

### Tenant Isolation Principle

Authorization checks and data queries must both enforce tenant boundary. If only middleware checks tenant but query layer forgets tenant filter, cross-tenant leakage can still occur.

### Policy Caching Tradeoff

Short positive-cache TTL improves latency. But revocation takes effect only after TTL unless invalidation is wired. Mention this explicitly.

### Permission Cardinality

At scale, per-resource permissions can grow quickly. Common optimizations:

1. role/group grants expanded at request time or materialized cache
2. wildcard scopes for controlled resource sets
3. policy decision point service with local cache

### Auditability

Denied writes should be audit logged with:

- principal
- tenant
- resource
- action
- reason code

This is invaluable for security incident response.

### Testing Beyond Happy Path

1. cross-tenant spoof attempts
2. stale cache after revoke
3. partial auth context (missing tenant claim)
4. wildcard permission edge behavior

### Learning summary

"RBAC correctness is not only allow/deny logic. It is tenant isolation at every data boundary, deterministic policy evaluation, and auditable denial behavior with controlled cache staleness."

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

### Extended Teaching Block 44
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
