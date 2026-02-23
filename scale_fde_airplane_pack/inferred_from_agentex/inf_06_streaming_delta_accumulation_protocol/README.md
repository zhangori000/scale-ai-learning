# INF-06 Coding Round Editorial: Streaming Delta Accumulation Protocol

This chapter is a full walkthrough for designing a streaming update protocol where partial deltas become one deterministic final message.

Grounded source files:

`scale-agentex/agentex/src/domain/use_cases/agents_acp_use_case.py`. `scale-agentex/agentex/docs/docs/development_guides/streaming_patterns.md`.

## The Real Problem

Token streaming has two outputs:

realtime updates to client. stable final persisted message.

If protocol rules are loose, these two diverge.

You can end up with:

UI showing text that DB never saved. malformed JSON from mixed delta types. duplicate finalization events.

## Mental Model

Each message index is its own mini state machine.

Do not treat stream as a single append-only string globally.

## Why Interviewers Ask This

They are checking protocol design maturity:

explicit event semantics. deterministic finalization rules. robust behavior under retries and out-of-order arrivals.

## Event Types

Common update events:

`START(index, initial_content?)`. `DELTA(index, chunk)`. `FULL(index, final_content)`. `DONE(index)`.

All correctness depends on how these transition state.

## Step 0: Define State Machine

Per `index`, state is either:

`OPEN`. `COMPLETED`.

Transition rules:

`DELTA` allowed only in `OPEN`. `FULL` sets final content and moves to `COMPLETED`. `DONE` flushes accumulator and moves to `COMPLETED`. late events for `COMPLETED` are ignored/logged.

## Step 1: Enforce Delta Type Consistency

As in Agentex `DeltaAccumulator`, once first delta type appears for an index, all later deltas for that index must match.

Why:

text concatenation rules differ from data/tool JSON assembly. mixing types silently corrupts output.

## Step 2: Type-Specific Accumulation

Text: concatenate strings. Data/tool request: concatenate fragments then parse JSON once at finalization. Tool response/reasoning: type-specific reconstruction.

Never parse JSON on each tiny chunk unless protocol guarantees chunk validity at each step.

## Step 3: Parent Message Lifecycle

Persistence pattern:

create parent message placeholder on first event for index. keep accumulating deltas in memory. write final content when `FULL` or `DONE` arrives.

This matches the structure in `agents_acp_use_case.py`.

## Step 4: FULL Override Semantics

If `FULL` arrives after deltas:

replace delta-derived interpretation. mark index completed. ignore later deltas.

This gives deterministic override behavior.

## Step 5: End-Of-Stream Sweep

If stream ends without explicit `DONE`, choose a policy.

Practical policy used in many systems:

flush any non-empty accumulators at stream end.

This prevents stranded partial results.

## Step 6: Reference Implementation Shape

```python
on_delta(i, d):
    if completed[i]:
        return
    accum[i].add(d)

on_full(i, content):
    persist_final(i, content)
    completed[i] = True

on_done(i):
    if completed[i]:
        return
    persist_final(i, accum[i].to_content())
    completed[i] = True

on_stream_end():
    for i in seen_indexes:
        if not completed[i] and accum[i].has_data():
            persist_final(i, accum[i].to_content())
```

## Step 7: Error Contract

Define behavior for:

mixed delta type -> protocol error. malformed JSON on flush -> fail message/task with structured error. done-without-delta -> no-op or empty content by policy. duplicate done -> idempotent no-op.

Document this clearly.

## Step 8: Worked Timeline

Index 0 receives:

`DELTA("Hel")`. `DELTA("lo")`. `DONE`.

Final persisted content is `Hello`.

If later `FULL("Hello world")` arrives after completion, it should be ignored unless protocol explicitly allows reopen, which is uncommon.

## Step 9: Implementation Order

implement state table per index. implement typed accumulator. wire event handlers (`START`, `DELTA`, `FULL`, `DONE`). add persistence hooks. add stream-end sweep. add tests.

## Step 10: Tests You Need

Test 1: text accumulation + done finalization.

Test 2: full override wins over previous deltas.

Test 3: mixed delta type rejected.

Test 4: malformed JSON fails predictably.

Test 5: stream-end sweep flushes unfinished indexes.

Test 6: multiple indexes interleaving stay isolated.

## Common Mistakes

one global accumulator for all indexes. no completed-index guard. no type consistency check. forgetting stream-end flush policy.

## Interview Wrap-Up Script

"I design streaming updates as a per-index state machine. Deltas are type-safe and accumulated deterministically, FULL and DONE are explicit finalization transitions, and completed indexes reject late updates. That keeps real-time UX and persisted state consistent under retries and partial failures."
