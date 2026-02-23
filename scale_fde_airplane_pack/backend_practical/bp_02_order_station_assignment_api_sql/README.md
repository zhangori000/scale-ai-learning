# BP-02: Order-to-Station Assignment API (Backend Practical Essay)

This chapter covers a backend practical that combines SQL reasoning, transactional correctness, and concurrency control. The service must assign pending orders to stations under region and capacity constraints.

Rules recap:

station must be active. station region must match user region. station must have remaining capacity. choose station with highest available capacity. tie-break by smallest station_id.

The hidden challenge is concurrency. If multiple workers assign simultaneously, naive reads can over-assign capacity unless updates are guarded atomically.

A clean design splits assignment into two layers:

candidate selection query. guarded transactional updates.

Schema baseline:

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  region TEXT NOT NULL
);

CREATE TABLE stations (
  id TEXT PRIMARY KEY,
  region TEXT NOT NULL,
  active BOOLEAN NOT NULL,
  capacity INT NOT NULL,
  used INT NOT NULL DEFAULT 0
);

CREATE TABLE orders (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  status TEXT NOT NULL,
  station_id TEXT NULL REFERENCES stations(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Candidate query should generate best station per pending order using deterministic ranking.

```sql
WITH pending AS (
  SELECT o.id AS order_id, o.user_id
  FROM orders o
  WHERE o.status = 'PENDING'
  ORDER BY o.created_at ASC
  LIMIT :limit
),
choices AS (
  SELECT
    p.order_id,
    s.id AS station_id,
    (s.capacity - s.used) AS avail,
    ROW_NUMBER() OVER (
      PARTITION BY p.order_id
      ORDER BY (s.capacity - s.used) DESC, s.id ASC
    ) AS rn
  FROM pending p
  JOIN users u ON u.id = p.user_id
  JOIN stations s ON s.region = u.region
  WHERE s.active = TRUE
    AND s.used < s.capacity
)
SELECT order_id, station_id
FROM choices
WHERE rn = 1;
```

This query gives candidate intent, not final truth. Under concurrency, a candidate may become invalid before write.

Therefore writes must be guarded.

Transactional assignment sequence:

begin transaction. fetch candidates. for each candidate pair:. increment station usage with guard `used < capacity`. only if station update succeeds, assign order with guard `status='PENDING'`. commit.

The two guards are critical:

station guard prevents over-capacity. order status guard prevents double-assignment.

Pseudo implementation:

```python
async def assign_pending_orders(limit: int):
    assigned = []
    async with db.transaction():
        pairs = await repo.fetch_candidates(limit)

        for pair in pairs:
            sid = pair["station_id"]
            oid = pair["order_id"]

            station_ok = await repo.try_consume_capacity(sid)
            if not station_ok:
                continue

            order_ok = await repo.try_assign_order(oid, sid)
            if not order_ok:
                # optional compensation: release capacity if assignment lost race
                await repo.release_capacity(sid)
                continue

            assigned.append({"order_id": oid, "station_id": sid})

    return assigned
```

This compensation step is important when station update succeeds but order update loses race.

Indexes needed for performance:

```sql
CREATE INDEX idx_orders_status_created ON orders(status, created_at);
CREATE INDEX idx_stations_region_active ON stations(region, active);
CREATE INDEX idx_users_region ON users(region);
```

Test strategy:

happy path deterministic assignment. tie-break by station_id. capacity exhaustion handling. concurrent workers do not exceed capacity. repeated assignment call does not reassign already assigned orders.

Interview close:

"I use SQL to compute best candidates, but enforce correctness at write time with guarded updates inside a transaction. Candidate ranking decides preference, while conditional updates enforce capacity and single-assignment under concurrency."

## Deep Dive Appendix

This addendum goes deeper on assignment correctness under concurrent workers.

### Concurrency Hazard

Two workers can pick the same candidate order and station simultaneously. If updates are not guarded, both may increment `used` and both may assign same order.

Guarded conditional updates are therefore mandatory, not optional.

### Capacity and Assignment Consistency

A subtle failure window exists if station capacity is consumed but order assignment fails due race. To avoid leaking capacity, apply compensation by decrementing `used` when order update fails.

Alternative is using stronger row locking strategy (`SELECT ... FOR UPDATE SKIP LOCKED`) to reduce compensation frequency.

### SQL Locking Strategy Discussion

You can mention two approaches:

optimistic conditional updates (simple, scalable). pessimistic row locking (strong control, potential contention).

In interviews, choosing optimistic with compensation is usually a good pragmatic answer.

### Fairness Consideration

Highest available capacity can starve smaller stations. If fairness matters, consider weighted round-robin or least-recently-assigned tie-breaking.

### Idempotency for Repeated API Calls

Repeated assignment endpoint calls should be safe. Orders already assigned remain excluded by `status='PENDING'` guard.

### Observability

Useful metrics:

assigned orders per run. race-lost capacity updates. compensation count. pending queue age.

### Learning summary

"Candidate ranking is advisory; correctness is enforced at write time with conditional updates inside a transaction. This gives safe behavior under concurrent workers without over-assignment."

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

