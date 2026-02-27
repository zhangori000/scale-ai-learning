# Crash Course (Read in 10-15 minutes)

## Core terms
1. `State machine`: a finite set of states plus explicit transition rules.
2. `Deterministic`: same input + same current state = same next state, always.
3. `Idempotent event handling`: replaying the same event does not change outcome.
4. `Per-entity serialization`: process updates one-at-a-time per entity key.
5. `Audit log`: append-only transition history for debugging and replay analysis.

## What Scale-level systems require
1. You must assume retries happen.
2. You must assume out-of-order delivery happens.
3. You must assume concurrent handlers hit the same entity.
4. You must design so all three cases are safe by default.

## Mental model for this exercise
Use key = `(task_id, agent_id)`.

Why:
1. Agentex state is isolated per task-agent pair.
2. Same task with two agents is parallel by design.
3. Isolation avoids cross-agent corruption.

## Five invariants you should memorize
1. Only valid transitions are allowed.
2. Duplicate `event_id` is a no-op.
3. `seq` cannot go backward.
4. Same key is serialized with one lock.
5. Applied transitions are always logged.

## Fast implementation plan
1. Define enums and dataclasses.
2. Build transition table.
3. Build in-memory stores (`state`, `last_seq`, `applied_ids`, `history`, `locks`).
4. Implement `apply()` with this strict order:
   - lock
   - dedupe check
   - sequence check
   - transition validation
   - commit + audit append
5. Write assertions for happy path and four failure/edge cases.

## Common failure modes
1. Global lock instead of per-key lock (kills throughput).
2. Deduping after state mutation (too late).
3. Accepting out-of-order events silently.
4. Not logging rejected reasons (hard to debug).
