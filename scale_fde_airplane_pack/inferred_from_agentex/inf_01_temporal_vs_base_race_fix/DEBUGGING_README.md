# INF-01 Debugging Editorial: Temporal vs Base Async Race Fix

This is the long-form debugging chapter for race-condition incidents in asynchronous task processing systems. The goal is not only to show the fix, but to teach a reproducible forensic method you can use in an interview or a real outage.

## 1. Incident Framing

A user-visible symptom appears: task counters are occasionally too low, or conversation state appears to "forget" one of multiple rapid events. No exception is thrown. Service latency looks normal. Error dashboards are quiet.

This symptom profile strongly suggests silent write-order corruption, not request failure.

## 2. Why This Bug Is Hard

Race conditions in async systems often pass functional tests because those tests are mostly sequential. The bug requires specific overlap timing between two handlers that mutate the same logical state.

If those handlers run in close temporal proximity, the system can lose updates with no crash.

## 3. Minimal Reproduction Strategy

A strong debugger creates a deterministic stress harness.

```python
await asyncio.gather(*[
    handler(task_id="t1", event_id=str(i))
    for i in range(1000)
])
state = await repo.get_state("t1")
assert state["processed"] == 1000
```

If assertion fails intermittently, keep this harness. It becomes your regression test after the fix.

## 4. Interleaving Evidence Collection

Add temporary instrumentation at read and write boundaries:

- task_id
- event_id
- value_before_read
- value_before_write
- value_after_write
- timestamp and worker id

You are looking for this pattern:

1. handler A reads X
2. handler B reads X
3. handler A writes X+1
4. handler B writes X+1

That sequence proves lost update.

## 5. Race Amplification Technique

If overlap is rare, intentionally widen critical window:

```python
val = await repo.read(task_id)
await asyncio.sleep(0.01)
await repo.write(task_id, val + 1)
```

This is for diagnosis only. Do not ship with this.

## 6. Root Cause Model

The broken pattern is read-modify-write without isolation guarantee for same entity.

In Base async execution models, multiple handlers for same task can run concurrently unless explicit coordination exists.

Temporal workflows differ because signal handling is serialized per workflow instance. That platform property reduces this class of race by default.

## 7. Fix Architecture (Base Async)

Robust solution has three coordinated controls:

1. durable per-task progress cursor (`last_processed_event_id`)
2. atomic batch apply plus cursor advance in same transaction
3. idempotent event application

Why all three:

- cursor alone does not prevent duplicate effect on replay
- idempotency alone does not prevent missing events if cursor jumps early
- atomicity alone does not provide resumable ordering semantics

## 8. Failure-Window Validation

Test two crash windows explicitly:

Window A: crash before commit

- expected: no cursor movement, no durable state movement

Window B: crash after commit but before ack/report

- expected: replay may occur, idempotency prevents duplicate effect

If either fails, patch is incomplete.

## 9. Regression Suite You Should Keep

1. high-concurrency same-task burst test
2. crash-before-cursor-advance test
3. duplicate event replay test
4. multi-task parallelism isolation test

These tests should become permanent because race regressions are easy to reintroduce.

## 10. Operational Signals Post-Fix

Add metrics:

- processed_events_total
- deduped_events_total
- cursor_lag
- failed_batch_commits

A rising dedupe rate might indicate upstream retry storm; rising cursor lag indicates underprovisioning or lock contention.

## 11. Interview Delivery Paragraph

"I approached this as silent state corruption. I reproduced with controlled concurrent handlers, captured overlapping read-modify-write interleavings, and confirmed lost updates. The durable fix was a cursor-driven single-writer effect: atomic state+cursor commit and idempotent apply for replay safety. I verified both burst correctness and crash-restart correctness with regression tests."

## 12. Closing Thought

The practical lesson is that race debugging is a discipline: reproduce, capture interleaving evidence, model the invariant, then validate crash windows. Without crash-window validation, many "fixes" are only timing patches.
