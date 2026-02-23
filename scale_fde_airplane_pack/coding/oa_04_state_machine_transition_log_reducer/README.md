# OA-04: State Machine Transition Log Reducer

This coding problem is inferred from: scale-agentex/agentex/docs/docs/development_guides/state_machines.md.

You are given transition logs from many workflow runs. Each row has: run_id. from_state. to_state. ts. workflow_name.

Implement a reducer that validates transitions and returns: final state per run. invalid transition list with reasons. time spent in each state per run.

Assume out-of-order arrival and duplicate rows. Use deterministic ordering by (run_id, ts, original_index) after dedupe.

## Algorithmic Foundations For This Problem

Restate input and output contract in deterministic terms. Define tie-breakers explicitly. Define malformed-input behavior explicitly.

Write invariants before coding. Invariants reduce logical bugs. Examples include deterministic ordering and no duplicate contribution.

Choose data structures based on semantics. Use map for dedupe and latest-by-key patterns. Use heap for progressive ordering extraction. Use stack for nested grammar. Use deque for sliding windows.

Separate transformation phase from aggregation phase when semantics differ. Dry-run tiny examples before implementation. Then scale to stress tests.

Complexity should be explained phase-by-phase. Prefer clarity first, then optimize if bottlenecks are measured.

