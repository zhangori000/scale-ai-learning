# INF-01 Coding Round Editorial: Temporal vs Base Async Race Fix

This chapter is intentionally written as a long essay instead of a short checklist. The purpose is simple: if you are new to race conditions, you should be able to read this from top to bottom and feel like you finally understand not only what the bug is, but why it appears, why it is hard to detect, and why certain fixes work while others only look convincing.

Everything here is grounded in the `scale-agentex` race condition guide:

`scale-agentex/agentex/docs/docs/development_guides/race_conditions.md`.

## Abstract

A race condition is not "an exception under load." Most dangerous race conditions do not crash. They produce plausible but incorrect state. In asynchronous agent systems, this usually appears as lost updates, duplicated work, or inconsistent conversation state. The central technical question is this: when multiple events for the same logical entity (for example, one task) arrive close together, what mechanism guarantees that state transitions are applied in a consistent order exactly once in effect?

Temporal-based execution gives you one answer by design: serialized signal handling per workflow instance. Base async execution gives you flexibility but asks you to build that guarantee yourself. This chapter develops that difference from first principles, then constructs a robust Base async solution step by step.

## 1. The Problem Before Any Buzzwords

Imagine one agent task. Two user events arrive almost simultaneously.

Event A: "increment processing_count" Event B: "increment processing_count"

Suppose the current value is `0`.

If these events were handled one after another, final value would be `2`.

But in many async systems both handlers can run at the same time. Each handler reads `0`, each adds `1`, each writes `1`. Final value becomes `1`. One increment disappeared.

Nothing crashed. The database accepted both writes. Logs might show two successful requests. The system looks healthy while being wrong.

That is why this bug is hard.

## 2. A Concrete Broken Example

The race-condition guide in Agentex shows this pattern clearly. Below is the simplified shape:

```python
@acp.on_task_event_send
async def handle_event_send(params):
    state = await adk.state.get_by_task_and_agent(
        task_id=params.task.id,
        agent_id=params.agent.id,
    )

    processing_count = state.state.get("processing_count", 0)
    new_count = processing_count + 1

    state.state["processing_count"] = new_count
    await adk.state.update(state_id=state.id, state=state.state)
```

At first glance this looks reasonable. It reads state, computes next state, writes back. The bug is not in syntax. The bug is in schedule.

## 3. Why This Code Is Vulnerable

The vulnerable shape is called read-modify-write:

read current value. compute new value from current value. write computed value.

If two executions overlap, each may read the same old value. The second write overwrites the first. This is sometimes called a lost update anomaly.

Let us write the timeline:

T1 reads `count=0` T2 reads `count=0` T1 writes `count=1` T2 writes `count=1`

Both operations "succeeded." Final state is wrong.

## 4. Why You Usually Miss It In Early Development

In local testing:

events often arrive one at a time. CPU scheduling is stable. network latency is low.

Under production conditions:

multiple clients hit same task quickly. retries amplify concurrency. webhook bursts create concurrent handlers.

So the same code moves from "looks fine" to "silently corrupting state."

## 5. What Interviewers Are Actually Evaluating

When an interviewer gives this problem, they are usually not checking if you can say "use lock." They are checking whether you can do three things in sequence:

model the failure precisely. define the correctness invariant. choose a solution whose guarantees match that invariant.

If you jump directly to tool names without clear failure model, your answer sounds shallow.

## 6. Defining Correctness Invariant In Plain Language

For one task, events should affect state as if they were processed by a single logical writer in a deterministic order. If N unique events are accepted, state should reflect all N exactly once in effect.

The phrase "exactly once" here means exactly once effect on state, not exactly once network transport.

This distinction matters a lot.

## 7. Temporal Versus Base Async: The Core Distinction

Temporal workflow execution gives you a built-in serialization model for each workflow instance. Signals are queued and handled one by one in order. This greatly reduces in-workflow concurrent mutation races.

In the Agentex guide, Temporal workflow handlers are shown in this shape:

```python
@workflow.signal(name=SignalName.RECEIVE_EVENT)
async def on_task_event_send(self, params):
    self._state.turn_number += 1
    self._state.input_list.append(
        {"role": "user", "content": params.event.content.content}
    )
    result = await Runner.run(test_agent, self._state.input_list)
    self._state.input_list = result.final_output
```

Because one workflow instance processes one signal at a time, you do not get arbitrary concurrent writes to `self._state`.

Base async, by contrast, can run multiple handlers at once for the same task unless you design coordination explicitly.

Temporal is not magic. It gives a stronger default execution model for this class of problem.

## 8. Why "Just Use Temporal" Is Not A Complete Interview Answer

You may not always control platform choice. You might be debugging an existing Base async service, or a customer deployment where Temporal is not in place yet.

So you still need to answer:

"How do I guarantee correctness in Base async?"

This chapter now builds that answer from scratch.

## 9. A Taxonomy Of Fixes

Different fixes solve different subsets of the problem.

### 9.1 In-process lock

You can put a mutex around handler logic. This helps only inside one process. If multiple worker processes or pods handle the same task, lock scope is insufficient.

### 9.2 Atomic database update

If state transition is simple (for example increment counter), a database atomic update can solve lost update for that field. But complex transitions spanning multiple records/events need more structure.

### 9.3 Optimistic locking

Use version numbers. Update succeeds only if version matches what you read. On mismatch, retry. This is good, but you still need replay/idempotency strategy for event-driven systems.

### 9.4 Cursor-based sequential event application

Track progress by durable cursor (`last_processed_event_id`), read forward, apply atomically, advance cursor only after success. Add idempotency so retries do not duplicate effect.

This is the most general pattern for event-style Base async processing, and it matches the direction in Agentex docs.

## 10. The Idea Of A Durable Cursor (Introduced Slowly)

Do not think "cursor means pagination." Here cursor means durable progress marker for processing pipeline.

For each task, store:

`last_processed_event_id`

Interpretation:

"All events with ID less than or equal to this marker have already been applied."

Processing loop always asks for events strictly greater than this marker.

This gives you resumability after crash and a stable source of truth for progress.

## 11. Why Cursor Must Advance Only After Successful State Commit

Consider wrong order:

advance cursor to E100. then write state for E100. write fails.

Now cursor says E100 is done, but state is not. On restart, E100 is skipped. Data loss.

Correct order:

apply state changes for batch. commit. include cursor movement in same transaction.

If transaction fails, neither state nor cursor moves.

This is the heart of correctness.

## 12. Why Idempotency Is Still Required

Even with correct cursor order, crashes can happen after commit but before downstream acknowledgement path, causing replay attempts. Network retries can duplicate requests. Worker restarts can re-read boundary events depending on implementation.

Idempotency guard means:

"Applying the same logical event twice does not change final state beyond first application."

Common method: dedupe table keyed by `(task_id, event_id)` with unique constraint.

## 13. Building The Solution Step By Step

Now we move from concept to code.

### 13.1 Data model primitives

You need three storage concepts:

Event log table/stream with monotonic event IDs. Task state table/document. Tracker row with `last_processed_event_id`.

Optional but recommended:

Dedupe table for applied event IDs.

### 13.2 Repository interfaces

```python
class EventRepo:
    async def list_after(self, task_id: str, event_id: str, limit: int) -> list[Event]:
        ...

class TrackerRepo:
    async def get_cursor(self, task_id: str) -> str:
        ...
    async def set_cursor(self, task_id: str, event_id: str) -> None:
        ...

class DedupeRepo:
    async def insert_if_absent(self, task_id: str, event_id: str) -> bool:
        ...
```

### 13.3 Event application function

```python
async def apply_event_once(task_id: str, event: Event) -> None:
    inserted = await dedupe_repo.insert_if_absent(task_id, event.id)
    if not inserted:
        return  # already applied

    state = await state_repo.get(task_id)
    new_state = evolve_state(state, event)  # deterministic pure logic if possible
    await state_repo.update(task_id, new_state)
```

### 13.4 Batch processing loop with atomic boundary

```python
async def process_task_events(task_id: str, batch_size: int = 50) -> None:
    cursor = await tracker_repo.get_cursor(task_id)

    while True:
        events = await event_repo.list_after(task_id=task_id, event_id=cursor, limit=batch_size)
        if not events:
            await asyncio.sleep(0.1)
            continue

        async with db.transaction():
            for event in events:
                await apply_event_once(task_id, event)
            cursor = events[-1].id
            await tracker_repo.set_cursor(task_id, cursor)
```

The code above captures the key invariants:

forward-only read. idempotent apply. cursor advancement in same commit boundary.

## 14. A Worked Timeline Through Failure

Suppose cursor is E10 and events E11, E12, E13 are pending.

Worker reads E11-E13.

It applies E11, E12, E13.

Right before commit, process crashes.

After restart:

Cursor is still E10 because commit never happened.

Worker reads E11-E13 again.

Dedupe table rejects already-inserted event markers if partial effects had committed, or all apply if nothing committed.

Either way final state converges correctly.

That is the practical power of combining transaction boundary and idempotency.

## 15. Why This Is Better Than A Global Lock

Global lock serializes everything and destroys throughput for unrelated tasks.

Cursor sequencing can be per task. That means task A and task B can process in parallel, while each task remains internally consistent.

So you get correctness and scalable concurrency.

## 16. How To Explain Temporal Comparison In One Clean Paragraph

Temporal reduces this class of race by enforcing serialized signal handling per workflow instance and persisting workflow history. Base async does not give that guarantee by default. Therefore in Base async we emulate the same logical guarantee at application level using forward-only durable cursors, atomic state-plus-cursor commits, and idempotent event application.

If you can say that clearly, you will sound precise.

## 17. A Minimal Reproduction Harness You Can Actually Run

Broken implementation:

```python
async def broken_increment(task_id: str):
    s = await state_repo.get(task_id)
    c = s["count"]
    await asyncio.sleep(0.005)  # widen race window
    s["count"] = c + 1
    await state_repo.update(task_id, s)
```

Repro test:

```python
async def test_lost_update():
    await state_repo.update("t1", {"count": 0})
    await asyncio.gather(*[broken_increment("t1") for _ in range(200)])
    result = await state_repo.get("t1")
    assert result["count"] == 200  # typically fails
```

Now compare with cursor+idempotent pipeline test where assertion should hold.

## 18. Observability: How To Know Fix Is Working In Production

Instrumentation should include:

`events_fetched_total`. `events_applied_total`. `events_deduped_total`. `cursor_lag` (latest_event_id minus cursor). `batch_commit_latency_ms`.

If dedupe spikes abnormally, you may have retry storm. If cursor lag grows, you may be underprovisioned or blocked.

A strong interview answer mentions at least one correctness metric and one lag metric.

## 19. Formal Proof Sketch Without Heavy Math

Assume:

event IDs are totally ordered per task. `list_after(cursor)` returns only IDs greater than cursor. cursor updates and state updates are in one atomic transaction. apply operation is idempotent per event ID.

Then:

cursor never goes backward. no committed event effect is permanently skipped. repeated processing of same event does not create repeated effect.

Therefore final state equals deterministic fold of unique processed events in order, even across crashes and retries.

That is the practical correctness statement interviewers want.

## 20. Connecting Back To The Agentex Race Guide

The Agentex guide teaches two key ideas:

Temporal processes events sequentially in workflow context, which naturally avoids many concurrent state races. Base async can be made safe with tracker-cursor based coordinated processing and careful update ordering.

This chapter took those ideas and expanded them into an implementation editorial with concrete code and reasoning.

## 21. How To Speak This Out Loud In Interview

If you get this question live, a strong flow is:

First, describe the race with a concrete interleaving timeline.

Second, define invariant: one logical ordered effect per event.

Third, propose architecture: durable cursor + atomic state/cursor commit + idempotent apply.

Fourth, explain crash scenario and why it still converges.

Fifth, mention tests and metrics you would add.

You do not need to sound dramatic. You need to sound exact.

## 22. Closing

The biggest shift in thinking is this: race conditions are not solved by one keyword. They are solved by designing state progression semantics that remain true under concurrency, retries, and crashes. Temporal gives you stronger default semantics inside workflow boundaries. Base async asks you to build them explicitly. Cursor-driven coordination plus idempotent event application is one of the most reliable ways to do that in real systems, and it is exactly the kind of engineering judgment this interview topic is trying to surface.
