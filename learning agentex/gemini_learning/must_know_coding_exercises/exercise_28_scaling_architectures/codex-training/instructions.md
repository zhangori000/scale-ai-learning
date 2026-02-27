# Codex Training: Agentex Scaling Deep Dive

## Goal
Build an interview-level understanding of what Agentex means by:

> "Scale up or down based on demand and usage patterns"

Your prompt called this file `agens.ms`; in the repo the real file is:
- `scale-agentex/agentex/docs/docs/concepts/agents.md`

## What To Read First
- `scale-agentex/agentex/docs/docs/concepts/agents.md` (focus on the "What Agentex Handles for You" section)
- `scale-agentex/agentex/docs/docs/getting_started/agentex_overview.md`
- `scale-agentex/agentex/docs/docs/configuration.md` (replicas and autoscaling fields)
- `scale-agentex-python/src/agentex/lib/cli/handlers/deploy_handlers.py` (generated Helm values and autoscaling defaults)
- `scale-agentex-python/src/agentex/lib/core/temporal/services/temporal_task_service.py` (task submission to Temporal queue)
- `scale-agentex-python/src/agentex/lib/core/temporal/workers/worker.py` (worker concurrency limits)
- `scale-agentex/agentex/src/temporal/run_worker.py` (server-side Temporal worker queue and concurrency settings)
- `scale-agentex/agentex/src/domain/services/agent_acp_service.py` (high-concurrency lock/pool warning)

## Tasks
1. Explain scaling in Agentex as a 4-layer model:
- deployment scaling
- queue-based execution scaling
- worker concurrency scaling
- data-plane bottleneck scaling
2. Create an evidence table with columns:
- claim
- proof file(s)
- why it matters in production
3. Answer this interview question:
- "How can Agentex scale a Temporal agent during demand spikes without changing business logic code?"
4. List 3 failure modes tied to scaling and give one mitigation each.
5. Complete `exercise1` in this folder.

## Deliverables
- A one-page written explanation.
- The evidence table.
- Completed `exercise1/instructions.md` tasks and your implementation.

## Scoring Rubric (Self Check)
- 0: vague async vs sync summary only.
- 1: mentions Temporal but no code references.
- 2: references code paths but misses deployment knobs.
- 3: connects docs claims to deployment + queue + worker concurrency.
- 4: includes failure modes, tradeoffs, and tuning strategy with concrete fields.
