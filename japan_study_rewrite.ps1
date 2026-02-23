$ErrorActionPreference='Stop'

$root = 'japan study plan'
$days = Get-ChildItem -Path $root -Directory | Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}$' } | Sort-Object Name

# remove junk files per day
foreach($d in $days){
  foreach($name in @('01_focus.md','02_mock.md','00_reading_index.md')){
    $p = Join-Path $d.FullName $name
    if(Test-Path $p){ Remove-Item -Path $p -Force }
  }
}

$dailyVariants = @(
  'Baseline mode: prioritize a correct and readable MVP in under 30 minutes.',
  'Add malformed input handling: reject bad records with explicit reason codes.',
  'Add streaming mode: process updates incrementally without full recompute.',
  'Add memory cap: avoid storing unnecessary intermediate structures.',
  'Add timezone diversity: inputs mix Z timestamps and offset timestamps.',
  'Add partial failures: one shard can fail; output should still be deterministic for healthy shards.',
  'Add strict tie policy: document and enforce all tie-break rules.',
  'Add bug injection: interviewer introduces one failing test at minute 30; patch fast.',
  'Add persistence layer: explain what table/index changes you would make.',
  'Add scale target: assume 1e6 records and discuss bottlenecks.',
  'Add requirement pivot mid-way: new field must be supported without rewrite.',
  'Add observability: include metrics/logging signals you would emit.',
  'Final rehearsal mode: solve and explain as if this is the real phone screen.'
)

function Build-DocsForProblem {
  param(
    [string]$title,
    [string]$prompt,
    [string]$example,
    [string]$constraints,
    [string]$editorial,
    [string]$lang,
    [string]$code
  )
  return [pscustomobject]@{
    Title=$title; Prompt=$prompt; Example=$example; Constraints=$constraints; Editorial=$editorial; Lang=$lang; Code=$code
  }
}

$defs = @(
  (Build-DocsForProblem `
    'Session Pass Ranking (Latest-State Aggregation)' `
    'You receive score events with fields: session_id, user_id, score, timestamp. For each (session_id, user_id), only the latest timestamp counts. Return one row per session with pass_count (score >= pass_score), avg_pass_score over passing users only, and top_user (highest passing score, lexical tie-break). Include sessions with zero passers. Sort by pass_count desc, avg_pass_score desc, session_id asc.' `
    'Input events: [(s1,u1,65,1),(s1,u1,80,2),(s1,u2,90,3),(s2,u3,75,1),(s2,u3,60,2)], pass_score=70. Output: s1 -> pass_count=2, avg=85.0, top_user=u2; s2 -> pass_count=0, avg=0.0, top_user=None.' `
    'n up to 2e5 events. O(n + m log m) target where m is session count.' `
    'Phase 1 reconstructs latest state per (session,user) key using timestamp comparison. Phase 2 aggregates per session only over latest states. Phase 3 applies deterministic sorting. Most bugs come from aggregating before dedupe.' `
    'python' `
@'
from collections import defaultdict

def session_pass_ranking(events, pass_score):
    latest = {}
    for s, u, score, ts in events:
        key = (s, u)
        if key not in latest or ts > latest[key][1]:
            latest[key] = (score, ts)

    acc = defaultdict(lambda: {"pass_count": 0, "pass_sum": 0.0, "top_user": None, "top_score": None})

    for (s, u), (score, _) in latest.items():
        row = acc[s]
        if score >= pass_score:
            row["pass_count"] += 1
            row["pass_sum"] += score
            if row["top_score"] is None or score > row["top_score"]:
                row["top_score"] = score
                row["top_user"] = u
            elif score == row["top_score"] and u < row["top_user"]:
                row["top_user"] = u

    out = []
    for s, row in acc.items():
        pc = row["pass_count"]
        avg = row["pass_sum"] / pc if pc else 0.0
        out.append({"session_id": s, "pass_count": pc, "avg_pass_score": avg, "top_user": row["top_user"]})

    out.sort(key=lambda r: (-r["pass_count"], -r["avg_pass_score"], r["session_id"]))
    return out
'@),
  (Build-DocsForProblem `
    'Poker Hand Evaluator (5 Cards, No Jokers)' `
    'Given 5 cards like "AH", "TD", "7S", evaluate the hand category and tie-break key. Categories (high to low): straight flush, four-kind, full house, flush, straight, three-kind, two pair, one pair, high card.' `
    'Input: ["AH","KH","QH","JH","TH"] => straight flush. Input: ["9C","9D","9H","9S","2D"] => four-kind.' `
    'Exactly 5 valid cards, no duplicates.' `
    'Map ranks to counts and suits to counts. Detect flush (all suits same) and straight (consecutive ranks, including wheel A-2-3-4-5). Build category rank and tie vector for deterministic comparison.' `
    'python' `
@'
from collections import Counter

RANKS = {r:i for i,r in enumerate("23456789TJQKA", start=2)}

def eval_hand(cards):
    vals = sorted([RANKS[c[0]] for c in cards], reverse=True)
    suits = [c[1] for c in cards]
    cnt = Counter(vals)
    groups = sorted(((v,k) for k,v in cnt.items()), reverse=True)

    is_flush = len(set(suits)) == 1
    uniq = sorted(set(vals))
    is_wheel = uniq == [2,3,4,5,14]
    is_straight = (len(uniq)==5 and uniq[-1]-uniq[0]==4) or is_wheel
    high_straight = 5 if is_wheel else max(vals)

    if is_straight and is_flush:
        return (8, [high_straight])
    if groups[0][0] == 4:
        four = groups[0][1]
        kicker = [x for x in vals if x != four][0]
        return (7, [four, kicker])
    if groups[0][0] == 3 and groups[1][0] == 2:
        return (6, [groups[0][1], groups[1][1]])
    if is_flush:
        return (5, sorted(vals, reverse=True))
    if is_straight:
        return (4, [high_straight])
    if groups[0][0] == 3:
        three = groups[0][1]
        kickers = sorted([x for x in vals if x != three], reverse=True)
        return (3, [three] + kickers)
    if groups[0][0] == 2 and groups[1][0] == 2:
        p1, p2 = sorted([groups[0][1], groups[1][1]], reverse=True)
        kicker = [x for x in vals if x != p1 and x != p2][0]
        return (2, [p1, p2, kicker])
    if groups[0][0] == 2:
        pair = groups[0][1]
        kickers = sorted([x for x in vals if x != pair], reverse=True)
        return (1, [pair] + kickers)
    return (0, sorted(vals, reverse=True))
'@),
  (Build-DocsForProblem `
    'Poker With Jokers (Wildcard Maximization)' `
    'Given a 5-card hand that may contain up to 2 jokers represented as "X", compute the best possible hand rank by replacing jokers with any missing card values/suits.' `
    'Input: ["X","X","AH","KH","QH"] => best is royal straight flush by replacing X with JH and TH.' `
    'At most 2 jokers; avoid duplicate concrete cards after replacement.' `
    'Enumerate replacement candidates for jokers from full deck minus existing cards, evaluate each concrete hand with the base evaluator, and keep max lexicographic score.' `
    'python' `
@'
import itertools

DECK = [r+s for r in "23456789TJQKA" for s in "CDHS"]

def best_with_jokers(cards, eval_hand):
    jokers = [i for i,c in enumerate(cards) if c == "X"]
    fixed = [c for c in cards if c != "X"]
    used = set(fixed)
    pool = [c for c in DECK if c not in used]

    if not jokers:
        return eval_hand(cards)

    best = None
    for repl in itertools.permutations(pool, len(jokers)):
        arr = cards[:]
        for idx, card in zip(jokers, repl):
            arr[idx] = card
        score = eval_hand(arr)
        if best is None or score > best:
            best = score
    return best
'@),
  (Build-DocsForProblem `
    'Party Times: Merge Windows and Compute Dead Zone' `
    'Input is a list of party attendance windows: (town, neighborhood, start, end). For each neighborhood, merge overlapping windows. For each town, compute dead-zone time inside [town_min_start, town_max_end] where no neighborhood has activity.' `
    'If two neighborhoods in same town cover [10,12] and [13,15], dead-zone is 1 hour between 12 and 13.' `
    'Up to 1e5 windows total.' `
    'Normalize windows, group by neighborhood, merge intervals. Then union all merged neighborhood intervals per town and subtract union coverage from global span.' `
    'python' `
@'
from collections import defaultdict

def merge(intervals):
    intervals.sort()
    out = []
    for s,e in intervals:
        if not out or s > out[-1][1]:
            out.append([s,e])
        else:
            out[-1][1] = max(out[-1][1], e)
    return out

def party_dead_zone(records):
    by_n = defaultdict(list)
    for town, neigh, s, e in records:
        by_n[(town, neigh)].append((s,e))

    merged_n = {k: merge(v) for k,v in by_n.items()}
    by_t = defaultdict(list)
    for (town,_), ints in merged_n.items():
        by_t[town].extend(ints)

    dead = {}
    for town, ints in by_t.items():
        u = merge(ints)
        lo = min(s for s,_ in u)
        hi = max(e for _,e in u)
        covered = sum(e-s for s,e in u)
        dead[town] = (hi-lo) - covered
    return merged_n, dead
'@),
  (Build-DocsForProblem `
    'Timezone-Safe Window Normalizer' `
    'Given ISO-8601 timestamp windows possibly in different offsets, normalize all to UTC epoch seconds and merge by key. Return merged UTC windows.' `
    '"2026-03-01T10:00:00+02:00" equals "2026-03-01T08:00:00Z".' `
    'Assume valid ISO strings; keys can repeat heavily.' `
    'Never compare raw timestamp strings across offsets. Parse into timezone-aware datetime, convert to UTC instant, then merge intervals.' `
    'python' `
@'
from datetime import datetime, timezone
from collections import defaultdict

def to_epoch(ts):
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return int(dt.astimezone(timezone.utc).timestamp())

def normalize_merge(rows):
    by_key = defaultdict(list)
    for key, start_ts, end_ts in rows:
        s = to_epoch(start_ts)
        e = to_epoch(end_ts)
        if e < s:
            s, e = e, s
        by_key[key].append((s,e))

    out = {}
    for k, arr in by_key.items():
        arr.sort()
        merged = []
        for s,e in arr:
            if not merged or s > merged[-1][1]:
                merged.append([s,e])
            else:
                merged[-1][1] = max(merged[-1][1], e)
        out[k] = merged
    return out
'@),
  (Build-DocsForProblem `
    'Deterministic Leaderboard with Latest Updates' `
    'Each update is (user_id, score, ts). Keep latest score per user. Return top K users sorted by score desc, then user_id asc.' `
    'Updates: (u1,50,1),(u1,70,2),(u2,70,1), K=2 => [u1,u2] by lexical tie-break.' `
    'n up to 3e5.' `
    'First dedupe to latest by user, then sort unique users by deterministic key. Hidden tests often fail when tie-breakers are omitted.' `
    'python' `
@'
def top_k_latest(updates, k):
    latest = {}
    for u, score, ts in updates:
        if u not in latest or ts > latest[u][1]:
            latest[u] = (score, ts)
    arr = [(u, s) for u, (s, _) in latest.items()]
    arr.sort(key=lambda x: (-x[1], x[0]))
    return arr[:k]
'@),
  (Build-DocsForProblem `
    'Fix Lost Update in Async Counter Store' `
    'Implement keyed async counter increments so concurrent increments on same key cannot lose updates.' `
    'If 100 concurrent increments on key A start from 0, final value must be 100.' `
    'Use asyncio; multiple keys should still progress concurrently.' `
    'Use one lock per key instead of one global lock. This prevents races while preserving parallelism across different keys.' `
    'python' `
@'
import asyncio
from collections import defaultdict

class KeyedCounter:
    def __init__(self):
        self.values = defaultdict(int)
        self.locks = defaultdict(asyncio.Lock)

    async def increment(self, key, delta=1):
        async with self.locks[key]:
            self.values[key] += delta
            return self.values[key]

    async def get(self, key):
        return self.values[key]
'@),
  (Build-DocsForProblem `
    'State Transition Log Reducer' `
    'Given transitions (entity, from_state, to_state, ts), keep latest valid state per entity using allowed transition graph. Invalid transitions are ignored.' `
    'Allowed: NEW->RUNNING->DONE. Log containing RUNNING->NEW is ignored.' `
    'n up to 2e5 logs.' `
    'Sort by timestamp, track current state per entity, and accept only transitions that match current state and allowed edges.' `
    'python' `
@'
def reduce_transitions(logs, allowed):
    logs = sorted(logs, key=lambda x: x[3])
    cur = {}
    for entity, frm, to, ts in logs:
        if entity not in cur:
            if frm is None and to in allowed.get(None, set()):
                cur[entity] = to
            elif frm in allowed and to in allowed[frm]:
                cur[entity] = to
            continue
        if cur[entity] == frm and to in allowed.get(frm, set()):
            cur[entity] = to
    return cur
'@),
  (Build-DocsForProblem `
    'Idempotent Request Processor' `
    'Requests have (idempotency_key, payload_hash). First occurrence is ACCEPTED. Same key with same hash is DUPLICATE. Same key with different hash is CONFLICT.' `
    'k1:h1 => ACCEPTED, k1:h1 => DUPLICATE, k1:h2 => CONFLICT.' `
    'O(1) expected per request.' `
    'Store key->hash map. Compare incoming hash to stored hash. This is the core pattern behind webhook and payment idempotency.' `
    'python' `
@'
def process_idempotent(reqs):
    seen = {}
    out = []
    for key, h in reqs:
        if key not in seen:
            seen[key] = h
            out.append((key, "ACCEPTED"))
        elif seen[key] == h:
            out.append((key, "DUPLICATE"))
        else:
            out.append((key, "CONFLICT"))
    return out
'@),
  (Build-DocsForProblem `
    'SQL Design Challenge: Webhook Ingestion Schema' `
    'Design SQL tables for webhook ingestion with idempotency, processing status, and replay-safe audit trail.' `
    'You must support duplicate deliveries, signature validation status, and asynchronous processing.' `
    'PostgreSQL preferred; explicit primary/unique keys required.' `
    'Separate receipt table (immutable raw data) from processing table (mutable lifecycle). Enforce idempotency with unique(source, provider_event_id).' `
    'sql' `
@'
CREATE TABLE webhook_receipts (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  provider_event_id TEXT NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  signature_valid BOOLEAN NOT NULL,
  raw_body JSONB NOT NULL,
  UNIQUE (source, provider_event_id)
);

CREATE TABLE webhook_processing (
  receipt_id BIGINT PRIMARY KEY REFERENCES webhook_receipts(id),
  status TEXT NOT NULL,
  attempt_count INT NOT NULL DEFAULT 0,
  last_error TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_webhook_processing_status ON webhook_processing(status);
'@),
  (Build-DocsForProblem `
    'SQL Query + Index Challenge: Latest Order Assignment' `
    'Given order_events(order_id, station_id, status, ts), return latest status per order and count active orders per station where latest status IN (QUEUED,RUNNING).' `
    'If order 42 moved QUEUED->RUNNING->DONE, it should not count as active.' `
    'Large table; query should avoid full table scans when possible.' `
    'Use ROW_NUMBER partitioned by order_id ordered by ts desc. Filter rn=1 then aggregate by station_id. Add index on (order_id, ts desc).' `
    'sql' `
@'
WITH latest AS (
  SELECT
    order_id,
    station_id,
    status,
    ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY ts DESC) AS rn
  FROM order_events
)
SELECT station_id, COUNT(*) AS active_orders
FROM latest
WHERE rn = 1
  AND status IN ('QUEUED', 'RUNNING')
GROUP BY station_id
ORDER BY active_orders DESC, station_id ASC;

-- CREATE INDEX idx_order_events_order_ts ON order_events(order_id, ts DESC);
'@),
  (Build-DocsForProblem `
    'Webhook Signature Window + Dedupe' `
    'Each webhook has (provider_event_id, signed_ts, received_ts, signature_ok). Accept only if signature_ok and |received_ts-signed_ts| <= 300 seconds. Dedupe by provider_event_id (first accepted wins).' `
    'Two valid duplicates for same id => only first accepted, second marked DUPLICATE.' `
    'n up to 1e5.' `
    'Validate freshness and signature first, then idempotency check. Keep explicit rejection reasons for observability and debugging.' `
    'python' `
@'
def process_webhooks(rows, max_skew=300):
    accepted = set()
    out = []
    for eid, signed_ts, recv_ts, sig_ok in rows:
        if not sig_ok:
            out.append((eid, "REJECT_BAD_SIGNATURE"))
            continue
        if abs(recv_ts - signed_ts) > max_skew:
            out.append((eid, "REJECT_OUTSIDE_WINDOW"))
            continue
        if eid in accepted:
            out.append((eid, "DUPLICATE"))
            continue
        accepted.add(eid)
        out.append((eid, "ACCEPTED"))
    return out
'@),
  (Build-DocsForProblem `
    'Async Job Commands Reducer' `
    'Commands: CREATE, START, PROGRESS(x), CANCEL, COMPLETE, FAIL. Reduce command stream to final job state while enforcing legal transitions and monotonic progress.' `
    'CREATE->START->PROGRESS(20)->CANCEL->COMPLETE should end CANCELED; COMPLETE after CANCEL is invalid.' `
    'Input may contain retries and out-of-order noise.' `
    'Model as explicit state machine. Ignore illegal commands and keep audit reasons if desired.' `
    'python' `
@'
def reduce_job(commands):
    state = None
    progress = 0
    for cmd in commands:
        name = cmd[0]
        arg = cmd[1] if len(cmd) > 1 else None

        if state is None and name == "CREATE":
            state = "QUEUED"
        elif state == "QUEUED" and name == "START":
            state = "RUNNING"
        elif state == "RUNNING" and name == "PROGRESS":
            progress = max(progress, int(arg))
        elif state == "RUNNING" and name == "CANCEL":
            state = "CANCELED"
        elif state == "RUNNING" and name == "COMPLETE":
            state = "SUCCEEDED"
        elif state == "RUNNING" and name == "FAIL":
            state = "FAILED"
    return {"state": state, "progress": progress}
'@),
  (Build-DocsForProblem `
    'Negative Cache Policy Simulator' `
    'Simulate auth cache with positive TTL and negative TTL. Requests are (ts, user_id, upstream_result). Cache hit should bypass upstream until TTL expiry. Negative entries must expire quickly.' `
    'A temporary 404 should not lock user out forever; negative TTL controls this.' `
    'Events sorted by ts.' `
    'Store cache[user] = (value, expire_ts, is_negative). On each request, expire if ts >= expire_ts.' `
    'python' `
@'
def simulate_auth_cache(events, pos_ttl=300, neg_ttl=30):
    cache = {}
    out = []
    for ts, user, upstream in events:
        if user in cache and ts >= cache[user][1]:
            del cache[user]

        if user in cache:
            val, exp, neg = cache[user]
            out.append((user, "CACHE_HIT", val))
            continue

        val = upstream
        if val == "ALLOW":
            cache[user] = (val, ts + pos_ttl, False)
        else:
            cache[user] = (val, ts + neg_ttl, True)
        out.append((user, "UPSTREAM", val))
    return out
'@),
  (Build-DocsForProblem `
    'Circuit Breaker State Machine' `
    'Implement circuit breaker over call outcomes (SUCCESS/FAIL). States: CLOSED, OPEN, HALF_OPEN. After fail_threshold consecutive failures in CLOSED, move to OPEN. After cooldown ticks, move to HALF_OPEN. In HALF_OPEN, one success closes; one fail reopens.' `
    'Threshold=3, cooldown=2: FAIL,FAIL,FAIL => OPEN; after 2 ticks => HALF_OPEN.' `
    'Input stream includes CALL outcome events and TICK events.' `
    'Track state, failure streak, and open-until tick. This is a compact practical exercise in guarded transitions.' `
    'python' `
@'
def run_breaker(events, fail_threshold=3, cooldown=2):
    state = "CLOSED"
    fail_streak = 0
    t = 0
    open_until = -1
    trace = []

    for e in events:
        if e == "TICK":
            t += 1
            if state == "OPEN" and t >= open_until:
                state = "HALF_OPEN"
            trace.append(state)
            continue

        if state == "OPEN":
            trace.append("OPEN_BLOCK")
            continue

        if state == "CLOSED":
            if e == "SUCCESS":
                fail_streak = 0
            else:
                fail_streak += 1
                if fail_streak >= fail_threshold:
                    state = "OPEN"
                    open_until = t + cooldown
            trace.append(state)
        else:
            if e == "SUCCESS":
                state = "CLOSED"
                fail_streak = 0
            else:
                state = "OPEN"
                open_until = t + cooldown
            trace.append(state)
    return trace
'@),
  (Build-DocsForProblem `
    'System Design Prompt: Event Ingestion for External Producers' `
    'Design a high-throughput ingestion system for external webhook producers with retries, duplicates, out-of-order arrival, and occasional malformed payloads.' `
    'Need to ingest 50k events/sec peak, maintain exactly-once effect per provider_event_id, and support replay of failed events.' `
    'Must support tenant isolation and operational observability.' `
    'Reference solution: edge API validates auth and schema, writes immutable raw log, queues IDs, async workers apply idempotent effects, DLQ for poison events, replay tooling, full metrics.' `
    'text' `
@'
Component layout:
1) API Gateway + Auth
2) Ingestion Service -> Raw Event Store (immutable)
3) Queue (partition by tenant/source)
4) Idempotent Consumer Workers
5) Effect Store with unique(idempotency_key)
6) Dead Letter Queue + Replay Service
7) Metrics/Tracing/Alerting
'@),
  (Build-DocsForProblem `
    'Cursor Pagination with Stable Ordering' `
    'Given items sorted by (created_at desc, id asc), implement cursor pagination. Cursor should encode last seen (created_at, id). Return next page and next cursor.' `
    'If multiple rows share same timestamp, id tie-break prevents duplicates/skips.' `
    'Must be stable under concurrent inserts newer than current page.' `
    'Use keyset pagination, not OFFSET. Decode cursor into boundary and filter by tuple comparison consistent with sort order.' `
    'python' `
@'
import base64

def enc(ts, i):
    return base64.urlsafe_b64encode(f"{ts}|{i}".encode()).decode()

def dec(cur):
    ts, i = base64.urlsafe_b64decode(cur.encode()).decode().split("|")
    return int(ts), i

def page(items, limit, cursor=None):
    if cursor:
        bts, bid = dec(cursor)
        filtered = [x for x in items if (x[0] < bts) or (x[0] == bts and x[1] > bid)]
    else:
        filtered = items
    chunk = filtered[:limit]
    next_cursor = enc(chunk[-1][0], chunk[-1][1]) if len(chunk) == limit else None
    return chunk, next_cursor
'@),
  (Build-DocsForProblem `
    'Multi-Tenant RBAC Permission Check' `
    'Given role inheritance, role-permission assignments, and user-role assignments per tenant, implement has_permission(tenant,user,perm).' `
    'Role editor inherits viewer. User with editor should have all viewer permissions in same tenant only.' `
    'Up to 1e4 roles, DAG inheritance.' `
    'Precompute effective permissions per role via memoized DFS. Always include tenant in lookup key.' `
    'python' `
@'
from functools import lru_cache

def build_checker(role_parents, role_perms, user_roles):
    @lru_cache(None)
    def eff(role):
        perms = set(role_perms.get(role, set()))
        for p in role_parents.get(role, []):
            perms |= eff(p)
        return perms

    def has_permission(tenant, user, perm):
        for role in user_roles.get((tenant, user), []):
            if perm in eff(role):
                return True
        return False
    return has_permission
'@),
  (Build-DocsForProblem `
    'System Design Prompt: Tenant-Safe Analytics API' `
    'Design an API for per-tenant analytics dashboards with near-real-time updates, strict tenant isolation, and RBAC.' `
    'Customers want hourly aggregates, drill-down by project, and export endpoints.' `
    'P95 query latency under 400ms, eventual consistency acceptable within 2 minutes.' `
    'Reference solution: stream ingestion to aggregate store, tenant-leading keys, RBAC enforced at gateway and query layer, async exports, audit logs, and freshness metrics.' `
    'text' `
@'
Interview answer skeleton:
- Requirements: QPS, latency, freshness, consistency
- Data model: tenant_id first in partition and indexes
- Serving path: pre-aggregations + cache
- Security: RBAC + tenant filter everywhere
- Reliability: retries, DLQ, backfill jobs
- Observability: lag, freshness, deny-rate, export success
'@),
  (Build-DocsForProblem `
    'Composite Practical Challenge (Phone + Backend + Design)' `
    'Build a processor for events (tenant_id, event_id, timestamp, value). Requirements: idempotent by (tenant_id,event_id), normalize timestamps, aggregate per-tenant daily sum, expose top K tenants by sum with deterministic ties.' `
    'Duplicate event_id for same tenant should not change totals. Same sum ties resolve by tenant_id asc.' `
    'n up to 5e5 events; memory-conscious approach preferred.' `
    'Use dedupe key set, day-bucket normalization, hashmap aggregation, then deterministic sort for top K.' `
    'python' `
@'
from datetime import datetime, timezone
from collections import defaultdict

def day_bucket(ts):
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")

def process(events, k):
    seen = set()
    sums = defaultdict(float)

    for tenant, event_id, ts, value in events:
        key = (tenant, event_id)
        if key in seen:
            continue
        seen.add(key)
        sums[(tenant, day_bucket(ts))] += value

    tenant_sum = defaultdict(float)
    for (tenant, _day), v in sums.items():
        tenant_sum[tenant] += v

    top = sorted(tenant_sum.items(), key=lambda x: (-x[1], x[0]))[:k]
    return top, sums
'@)
)

$filenames = @(
  '01_phone_screen_contract_first.md',
  '02_card_game_object_modeling.md',
  '03_card_game_variant_extension.md',
  '04_party_times_interval_merging.md',
  '05_datetime_timezone_safety.md',
  '06_deterministic_output_contracts.md',
  '07_debugging_rhythm_45_minutes.md',
  '08_test_design_for_practical_rounds.md',
  '09_fastapi_request_lifecycle.md',
  '10_sql_schema_primer_for_interviews.md',
  '11_sql_query_patterns_and_indexes.md',
  '12_webhook_idempotency_and_retries.md',
  '13_async_jobs_and_state_transitions.md',
  '14_cache_negative_entry_policy.md',
  '15_reliability_timeouts_retries_circuit_breakers.md',
  '16_system_design_event_ingestion.md',
  '17_system_design_pagination_and_consistency.md',
  '18_system_design_multitenancy_and_rbac.md',
  '19_interview_communication_for_fde.md',
  '20_final_rehearsal_playbook.md'
)

$total = 0
for($i=0; $i -lt $days.Count; $i++){
  $day = $days[$i]
  $variant = $dailyVariants[$i]
  $readingDir = Join-Path $day.FullName 'readings'
  if(-not (Test-Path $readingDir)){ New-Item -ItemType Directory -Path $readingDir -Force | Out-Null }

  for($j=0; $j -lt $filenames.Count; $j++){
    $def = $defs[$j]
    $body = @"
# $($def.Title)

## Prompt
$($def.Prompt)

## Example
$($def.Example)

## Constraints
$($def.Constraints)

## Editorial Solution
$($def.Editorial)

## Reference Implementation
~~~$($def.Lang)
$($def.Code)
~~~

## Complexity
Discuss expected time/space tradeoffs and confirm deterministic behavior under ties and malformed input.

## Day Variant ($($day.Name))
$variant
"@
    Set-Content -Path (Join-Path $readingDir $filenames[$j]) -Value $body -Encoding UTF8
    $total++
  }
}

Write-Output "rewritten_readings=$total"
Write-Output "days=$($days.Count)"
