# Crash Course: Streaming Correctness for Senior Interviews

## The real challenge
Most candidates can parse stream events. Strong candidates can prove correctness when events are duplicated, delayed, reordered, and concurrent.

## Core model
Treat your projection as a reducer:
- `state_(n+1) = reduce(state_n, event_n)`

If this reducer is deterministic and idempotent, your system becomes debuggable and recoverable.

## Five interview-grade invariants
1. Idempotency by `event_id`.
2. Monotonic ordering by `seq`.
3. Explicit transition rules by current status.
4. Terminal-state protection.
5. Per-entity serialization under concurrency.

## Why this maps to Agentex
1. Agentex streams `start/delta/full/done` style updates for task messages.
2. SDK internals accumulate deltas and finalize to canonical message content.
3. Async flows and concurrent handlers exist in real code, so race safety is required.

## What interviewers look for
1. You define invariants before coding.
2. You enforce checks before mutation.
3. You isolate concurrency by entity key.
4. You produce traceable history for incident debugging.
