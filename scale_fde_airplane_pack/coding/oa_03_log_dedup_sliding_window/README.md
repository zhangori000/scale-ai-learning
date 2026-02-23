# OA-03: Log Deduplication in a Sliding Time Window (Essay Editorial)

This chapter walks through a deceptively simple operations-style coding question: suppress repeated logs within a configurable time window. The task looks easy until you account for unsorted input, stable ordering requirements, and edge cases around exact boundary timestamps.

Each log has:

`ts`. `service`. `fingerprint`.

A log should be emitted if the same `(service, fingerprint)` key has not been emitted within the last `window_sec` seconds.

The crucial phrase is "emitted," not "seen." If you track last-seen instead of last-emitted, you can accidentally suppress too much under unsorted input or dedupe churn.

The prompt also says input may be unsorted. That means processing order must be normalized first, otherwise dedupe decisions are non-deterministic.

A correct approach has three clear stages.

Stage one: stable sort input by `(ts, original_index)`.

Why include original index? To preserve deterministic ordering for logs with identical timestamp.

Stage two: maintain dictionary `last_emitted[(service, fingerprint)] = ts`.

Stage three: for each sorted row, emit if key is new or `ts - last_ts > window_sec`; when emitted, update last_emitted.

Reference implementation:

```python
from typing import List, Dict, Any, Tuple

def suppress_logs(logs: List[Dict[str, Any]], window_sec: int) -> List[Dict[str, Any]]:
    indexed: List[Tuple[int, Dict[str, Any]]] = list(enumerate(logs))
    indexed.sort(key=lambda x: (x[1]["ts"], x[0]))

    last_emitted: Dict[Tuple[str, str], int] = {}
    out: List[Dict[str, Any]] = []

    for _, row in indexed:
        key = (row["service"], row["fingerprint"])
        ts = row["ts"]

        if key not in last_emitted:
            out.append(row)
            last_emitted[key] = ts
            continue

        if ts - last_emitted[key] > window_sec:
            out.append(row)
            last_emitted[key] = ts

    return out
```

Boundary semantics deserve explicit statement. In this implementation, events at exactly `window_sec` distance are still suppressed because condition is `>` not `>=`. If interviewer wants inclusive boundary behavior, change condition accordingly and document it.

Complexity:

sorting dominates: `O(n log n)`. state map operations: `O(n)` average. memory: `O(k)` where `k` unique `(service,fingerprint)` keys.

Worked example:

Input logs (unsorted):

`(ts=12, service=a, fp=x)`. `(ts=10, service=a, fp=x)`. `(ts=15, service=a, fp=x)`.

Sorted becomes ts 10, 12, 15.

Emit ts 10.

At ts 12 with window 5: delta 2 -> suppress.

At ts 15: delta 5 -> still suppress under strict `>` rule.

If window is 4, ts 15 emits.

This explicit walkthrough helps avoid off-by-one mistakes.

Good test cases:

```python
def test_unsorted_input_stable_output():
    logs = [
        {"ts": 12, "service": "svc", "fingerprint": "a"},
        {"ts": 10, "service": "svc", "fingerprint": "a"},
    ]
    out = suppress_logs(logs, window_sec=5)
    assert out[0]["ts"] == 10

def test_exact_boundary_suppressed_in_strict_mode():
    logs = [
        {"ts": 10, "service": "svc", "fingerprint": "a"},
        {"ts": 15, "service": "svc", "fingerprint": "a"},
    ]
    out = suppress_logs(logs, window_sec=5)
    assert len(out) == 1

def test_different_keys_do_not_interfere():
    logs = [
        {"ts": 10, "service": "svc", "fingerprint": "a"},
        {"ts": 11, "service": "svc", "fingerprint": "b"},
    ]
    out = suppress_logs(logs, window_sec=100)
    assert len(out) == 2
```

Strong interview close:

"I normalize event order first with stable timestamp sorting, then dedupe against last emitted timestamp per key. That keeps behavior deterministic under unsorted inputs and makes window boundary policy explicit."

## Deep Dive Appendix

This section expands the sliding-window dedupe problem from a "quick hash map task" into a production-minded discussion.

### Problem Semantics Clarified

A log is emitted if and only if the same `(service,fingerprint)` has not been emitted in the previous `window_sec` interval.

This means the dedupe state must track last emitted timestamp, not last seen row blindly.

### Why Sorting Is Required

Input is unsorted. If you process unsorted rows as-is, dedupe decisions become order-dependent and non-deterministic.

Stable sort by `(ts, original_index)` gives deterministic temporal order and preserves original ordering among ties.

### Boundary Rule

The implementation uses `ts - last_ts > window_sec`.

This means exactly-equal-to-window events are still suppressed.

If interviewer expects inclusive boundary, switch to `>=`. The key is to state the chosen interpretation explicitly.

### Worked Example

Window = 5

Rows for same key:

ts=10 emit. ts=12 suppress (2 <= 5). ts=15 suppress (5 <= 5 under strict >). ts=16 emit (6 > 5).

This manual timeline is easy to communicate and demonstrates precision.

### Memory Growth Consideration

For very large key cardinality, `last_emitted` can grow indefinitely. In production you would add cleanup strategy:

periodic eviction of keys older than current_ts - window_sec. segmented maps by service. approximate dedupe (Bloom filters) where false positives are acceptable.

### Streaming Variant

If logs arrive in near-time order and you cannot sort globally, you need watermark-based ordering assumptions or bounded disorder buffering. Mentioning this shows you understand batch vs stream differences.

### Testing Notes

High-value tests:

unsorted input determinism. same-timestamp stable tie ordering. boundary behavior at exactly window_sec. different keys independent suppression.

### Learning summary

"I normalize event order with stable timestamp sorting, then suppress by last emitted timestamp per dedupe key. That keeps behavior deterministic on unsorted input and makes boundary semantics explicit."

## Algorithmic Foundations For This Problem

Restate input and output contract in deterministic terms. Define tie-breakers explicitly. Define malformed-input behavior explicitly.

Write invariants before coding. Invariants reduce logical bugs. Examples include deterministic ordering and no duplicate contribution.

Choose data structures based on semantics. Use map for dedupe and latest-by-key patterns. Use heap for progressive ordering extraction. Use stack for nested grammar. Use deque for sliding windows.

Separate transformation phase from aggregation phase when semantics differ. Dry-run tiny examples before implementation. Then scale to stress tests.

Complexity should be explained phase-by-phase. Prefer clarity first, then optimize if bottlenecks are measured.

