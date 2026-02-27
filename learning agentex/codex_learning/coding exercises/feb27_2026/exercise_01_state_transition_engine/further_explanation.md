# Further Explanation: Why this maps to Agentex

## Direct references in your workspace
1. `scale-agentex/agentex/docs/docs/concepts/state.md`
   - Defines state isolation for each `(task_id, agent_id)` pair.
2. `scale-agentex-python/src/agentex/lib/sdk/state_machine/state_machine.py`
   - Shows explicit states, transitions, and step/run flow.
3. `scale-agentex-python/examples/tutorials/10_async/10_temporal/020_state_machine/project/workflow.py`
   - Shows real workflow signal handling + state transitions.
4. `scale-agentex-python/examples/tutorials/test_utils/async_utils.py`
   - Shows race-aware async patterns (`create_task` stream consumer before send).

## Definitive statements
1. Agentex already uses explicit state-machine structure; this is not optional theory.
2. The repo examples demonstrate asynchronous event flow where races are realistic, not hypothetical.
3. In production systems, transition correctness requires idempotency and ordering checks even if a basic state machine class does not enforce them yet.
4. `(task_id, agent_id)` scoping is a concurrency boundary; treat it as the unit of serialization.
5. If you cannot reason about per-key locking and replay-safe transitions, you will struggle with Temporal workflows and streaming internals.

## How this exercise adheres to repo patterns
1. Adheres strongly:
   - explicit states
   - explicit transitions
   - per task-agent isolation
   - async execution model
2. Intentional extension beyond baseline tutorial:
   - adds strict idempotency
   - adds sequence monotonicity
   - adds transition audit history
   - adds concurrent safety guarantees

## Why the extension matters
The tutorial state machine teaches structure. This exercise teaches structure plus reliability. At engineering scale, reliability is what prevents silent corruption when events retry, arrive late, or race.

## Interview-level takeaway
You should be able to state this from memory:

1. "My entity key is `(task_id, agent_id)`."
2. "I serialize transitions per key."
3. "I dedupe by event_id."
4. "I reject stale sequence numbers."
5. "I keep an append-only transition history."

That is the minimum bar for robust workflow state logic.
