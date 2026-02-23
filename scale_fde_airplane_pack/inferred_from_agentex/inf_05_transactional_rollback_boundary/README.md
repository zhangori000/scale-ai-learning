# INF-05 Coding Round Editorial: Transactional Rollback Boundary

This chapter is a deep guide for a practical backend interview problem: SQL rollback works, but your workflow also talks to external systems.

Grounded source files:

`scale-agentex/agentex/tests/unit/infrastructure/test_transactional_proof.py`. `scale-agentex/agentex/src/domain/services/task_service.py`. `scale-agentex/agentex/src/domain/use_cases/tasks_use_case.py`.

## The Real Problem

You can make DB writes atomic, but you cannot include external API calls, Redis publishes, or webhook sends in the same database transaction.

So the real question is:

"How do I preserve correctness across this boundary?"

## Mental Model

Split the workflow into two guarantees:

Atomic state change in DB. Reliable eventual side effect outside DB.

If you try to do both inline in one function call, partial failures will create inconsistency.

## Why Interviewers Ask This

They want to distinguish candidates who know transaction syntax from candidates who design failure-safe workflows.

## Step 0: Mark Boundary Explicitly

Write this sentence in your own words:

"SQL transactions guarantee atomicity only for operations inside that database boundary."

Everything else follows from that.

## Step 1: Identify Unsafe Inline Pattern

Unsafe shape:

```python
await db_write(...)
await external_send(...)
```

Failure between these lines means DB committed but external side effect missing.

## Step 2: Introduce Transactional Outbox

Inside one DB transaction, write:

business row(s). outbox row describing intended external action.

Then commit once.

This guarantees side-effect intent is never lost.

## Step 3: Outbox Schema Basics

Minimum fields:

`id`. `event_type`. `payload`. `status` (`PENDING`, `DELIVERED`, `DEAD_LETTER`). `attempts`. `next_attempt_at`. timestamps.

## Step 4: Producer Transaction

```python
async with db.transaction():
    event = await event_repo.create(...)
    await outbox_repo.insert(
        id=uuid4(),
        event_type="task_event_created",
        payload=event.model_dump(mode="json"),
        status="PENDING",
        attempts=0,
    )
```

No network calls inside this transaction.

## Step 5: Delivery Worker

```python
rows = await outbox_repo.fetch_due(limit=100)
for row in rows:
    try:
        await downstream.send(row.payload, idempotency_key=row.id)
        await outbox_repo.mark_delivered(row.id)
    except Exception:
        await outbox_repo.reschedule(row.id, attempts=row.attempts + 1)
```

Now delivery is retriable and observable.

## Step 6: Idempotency Is Mandatory

Retries can resend same event. That is expected.

Receiver must dedupe by idempotency key (often outbox `id`).

Without this, retry logic creates duplicates.

## Step 7: Dead-Letter Policy

After max attempts:

mark row `DEAD_LETTER`. alert operators. provide replay tooling.

Do not silently drop permanently failing rows.

## Step 8: Worked Failure Timeline

Scenario:

request creates event row. process crashes before external send.

With outbox:

outbox row still `PENDING`. worker later sends successfully.

Without outbox:

downstream never sees event. intent lost.

This is the decisive difference.

## Step 9: Implementation Order

add outbox model/repository. write producer transaction path. implement worker fetch/send/mark loop. add retry and dead-letter logic. add metrics and tests.

## Step 10: Tests You Need

Test 1: rollback removes both business and outbox writes.

Test 2: send failure keeps row pending with incremented attempts.

Test 3: successful resend marks delivered.

Test 4: duplicate send does not duplicate downstream effect.

Test 5: max retries routes to dead-letter.

## Common Mistakes

writing outbox row after commit. sending externally inside transaction. no idempotency key. no dead-letter handling.

## Interview Wrap-Up Script

"I treat the DB boundary explicitly. I make business state and delivery intent atomic using a transactional outbox, then deliver outbox entries asynchronously with retries and idempotency keys. This removes partial-failure data loss without pretending to do distributed transactions."
