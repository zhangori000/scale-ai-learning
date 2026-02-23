# DBG-02: Async Lost Update Race (Debugging Essay)

This chapter is about the most dangerous category of concurrency bug: the system stays up, logs look normal, and state drifts wrong. The observed symptom is undercounting on a field that should increment exactly once per event.

Broken handler pattern:

```python
async def on_event(task_id, repo):
    state = await repo.get_state(task_id)
    count = state.get("processed", 0)
    await asyncio.sleep(0)
    state["processed"] = count + 1
    await repo.save_state(task_id, state)
```

The sleep line is only there to magnify the race. The race exists even without explicit sleep.

Root cause is read-modify-write under concurrency.

Two concurrent executions can do:

read same old value. compute same incremented value. write same result.

One increment is lost.

Debugging methodology:

reproduce with high concurrency using `asyncio.gather`. log before-read and after-write values. verify final count < expected count.

Repro test:

```python
import asyncio

async def test_lost_updates(repo):
    task_id = "t1"
    await repo.set_state(task_id, {"processed": 0})
    await asyncio.gather(*[on_event(task_id, repo) for _ in range(500)])
    state = await repo.get_state(task_id)
    assert state["processed"] == 500
```

This test should fail on broken code and pass after fix.

Fix strategy depends on mutation type. For pure counter increments, storage-level atomic update is strongest and simplest.

```python
async def on_event(task_id, repo):
    await repo.increment_counter_atomic(task_id, "processed", 1)
```

SQL shape:

```sql
UPDATE task_state
SET processed = processed + 1
WHERE task_id = :task_id;
```

Why atomic update works:

no stale read in application layer. increment happens inside single storage operation. concurrent increments compose correctly.

If mutation is more complex than numeric increments, alternatives are optimistic locking or per-entity serialized processing. But for this specific bug class, atomic increment is ideal.

Post-fix verification:

rerun concurrency test at larger scale. run with multiple worker processes if relevant. check production metric "events processed vs expected".

Important anti-pattern: adding in-process lock without understanding deployment topology. If you run multiple pods, local lock only serializes per process, not globally.

A practical interview close:

"I reproduced undercount with concurrent invocations and identified non-atomic read-modify-write. I moved increment into atomic storage operation, then validated with high-concurrency regression tests so each event contributes exactly one increment."
