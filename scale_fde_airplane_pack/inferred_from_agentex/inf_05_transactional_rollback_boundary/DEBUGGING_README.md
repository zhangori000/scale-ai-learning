# INF-05 Debugging Editorial: Transactional Rollback Boundary

This chapter details how to debug and fix incidents where database state commits but external side effects are missing, delayed, or duplicated.

## 1. Incident Signature

Common report:

- business row exists in DB
- downstream action did not happen
- no request-level exception visible to user

This pattern indicates a transaction boundary mismatch.

## 2. Triage Questions

Ask in order:

1. did DB transaction commit?
2. was side-effect intent durably recorded?
3. was external publish/send attempted?
4. was send ack persisted?

These questions isolate where reliability guarantee broke.

## 3. Typical Broken Pattern

```python
await db_write(...)
await external_send(...)
```

If failure occurs between these calls, data and side effects diverge.

## 4. Reproduction Method

Inject failure right after DB commit and before external completion.

Expected in broken design:

- DB row present
- no downstream event

This turns conceptual bug into measurable failure.

## 5. Corrective Architecture

Use transactional outbox:

1. write business data + outbox record in same transaction
2. commit
3. worker sends outbox records with retry
4. mark delivered on success

This preserves delivery intent even when external system fails.

## 6. Debugging Existing Outbox Systems

If outbox already exists, inspect:

- backlog age
- retry attempts
- dead-letter growth
- worker heartbeat

Many incidents are operational (stuck workers, bad retry policy), not design-level.

## 7. Duplicate Safety Check

Retries imply possible duplicate sends. Verify receiver idempotency by stable key (often outbox id).

Without idempotency, fixing missing side effects can create duplicate side effects.

## 8. Validation Matrix

1. external transient failure -> pending then delivered
2. external permanent failure -> dead-letter and alert
3. crash after send before mark-delivered -> safe duplicate replay
4. rollback before commit -> no outbox row and no business row

## 9. Metrics

Track:

- outbox_pending_count
- outbox_oldest_age
- outbox_retry_total
- outbox_dead_letter_total

These metrics make reliability visible.

## 10. Interview Delivery Paragraph

"I diagnosed the issue as boundary inconsistency between atomic DB writes and non-atomic external side effects. I fixed it by moving side-effect intent into a transactional outbox, then validated retry, duplicate safety, and dead-letter handling."

## 11. Closing Thought

Many reliability incidents are boundary definition failures. Once boundaries are explicit and observable, fixes become systematic rather than ad hoc.
