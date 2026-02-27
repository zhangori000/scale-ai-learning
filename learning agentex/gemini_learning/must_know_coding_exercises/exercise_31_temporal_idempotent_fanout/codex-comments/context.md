# Codex Context: Exercise 31 (Temporal Idempotent Fanout)

This exercise is motivated by several real patterns across `agentex` + `agentex-python`:

1. Temporal idempotency guidance:
   - `scale-agentex/agentex/docs/docs/temporal_development/tool_patterns.md`
   - `scale-agentex/agentex/docs/docs/temporal_development/troubleshooting.md`
   - Both explicitly require idempotent activity behavior because retries are normal.
2. Temporal duplicate workflow control:
   - `scale-agentex-python/src/agentex/lib/core/clients/temporal/types.py`
   - `scale-agentex-python/src/agentex/lib/core/clients/temporal/temporal_client.py`
   - Exposes `DuplicateWorkflowPolicy` mapped to Temporal `WorkflowIDReusePolicy`.
3. Retry-safe idempotency key behavior in SDK transport:
   - `scale-agentex-python/src/agentex/_base_client.py`
   - Reuses an idempotency key across retries for non-GET requests.
4. Forward-only event processing progress:
   - `scale-agentex/agentex/src/domain/repositories/agent_task_tracker_repository.py`
   - Enforces "cursor cannot move backwards" for last processed event.

Why this pattern exists:

1. External events and network retries are at-least-once, not exactly-once.
2. Fanout expands one input event into multiple side-effecting workflows.
3. Without deterministic keys + duplicate-safe start semantics, retries create duplicate workflows.

