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

extract `tenant_id` and `principal_id` from auth context. build permission tuple key. check short-lived cache. on cache miss, check DB. allow only if explicit match.

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

allows quick hot-path permissions. reduces risk of negative-cache lockout after permission grants. keeps revocation lag bounded by short TTL.

If you cache DENY as well, TTL and invalidation design become more sensitive.

Security hardening checklist:

enforce tenant scoping in all data queries, not just authorization middleware. avoid wildcard permissions unless explicitly modeled and audited. write audit logs for denied write actions. include authorization reason codes for incident debugging.

Test plan:

valid tenant+permission -> allowed. cross-tenant access attempt -> denied. missing permission -> denied. cache hit on repeated allow check. permission revocation reflected after TTL or invalidation.

Useful extension topics for interviewer follow-up:

group/role expansion. hierarchical resource inheritance. policy engines (OPA, Cedar). batched authorization checks for list endpoints.

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

role/group grants expanded at request time or materialized cache. wildcard scopes for controlled resource sets. policy decision point service with local cache.

### Auditability

Denied writes should be audit logged with:

principal. tenant. resource. action. reason code.

This is invaluable for security incident response.

### Testing Beyond Happy Path

cross-tenant spoof attempts. stale cache after revoke. partial auth context (missing tenant claim). wildcard permission edge behavior.

### Learning summary

"RBAC correctness is not only allow/deny logic. It is tenant isolation at every data boundary, deterministic policy evaluation, and auditable denial behavior with controlled cache staleness."

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

