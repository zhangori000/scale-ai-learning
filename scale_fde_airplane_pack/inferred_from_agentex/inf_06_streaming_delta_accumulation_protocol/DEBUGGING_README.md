# INF-06 Debugging Editorial: Streaming Delta Accumulation Protocol

This chapter explains how to debug state-machine failures in streaming delta protocols, where live token output and persisted final messages diverge.

## 1. Symptom Profile

You may observe:

- missing tail content in final saved message
- invalid JSON for data/tool payloads
- FULL override ignored
- duplicate completion behavior

These symptoms usually come from invalid event ordering or weak completion guards.

## 2. First Debugging Principle

Debug per message index, not per stream globally.

Each index is its own protocol state machine. Mixing logs from all indexes obscures root cause.

## 3. Timeline Reconstruction

For each index, reconstruct ordered sequence of:

- START
- DELTA (possibly many)
- FULL (optional)
- DONE (optional)

Then mark state transitions (`OPEN` -> `COMPLETED`).

## 4. Common Violation Patterns

1. delta after completion
2. mixed delta types in one index
3. done before any accumulator exists
4. competing finalization writes (`FULL` and `DONE` both writing)

Any of these can corrupt final persisted content.

## 5. JSON Assembly Failure Analysis

For data/tool-request streams, parse failure often means chunk sequence is invalid, not parser bug.

Capture and log exact concatenated payload string before parse at completion boundary.

## 6. Persistence Race Check

Verify write order:

1. parent message created
2. updates attached to correct parent
3. exactly one final content write per index

If multiple final writes happen, results depend on race order.

## 7. Patch Strategy

- strict per-index state table
- reject mixed delta types
- idempotent completion guard
- ignore or flag late events after completion
- single authoritative finalization path

## 8. Regression Matrix

1. multi-index interleaving
2. full override after deltas
3. duplicate done event
4. malformed JSON fragment sequence
5. stream termination without done

All should behave deterministically.

## 9. Observability

Metrics:

- completion_by_path_total (FULL vs DONE vs stream_end)
- late_event_after_complete_total
- mixed_delta_type_error_total
- json_flush_error_total

These counters make protocol-health visible.

## 10. Interview Delivery Paragraph

"I debugged this by reconstructing per-index event timelines and identifying illegal state transitions. The fix was a strict per-index state machine with idempotent completion and type-safe accumulation, then regression tests across interleaving and override paths."

## 11. Closing Thought

Streaming bugs become tractable when treated as protocol-state errors rather than generic asynchronous noise.
