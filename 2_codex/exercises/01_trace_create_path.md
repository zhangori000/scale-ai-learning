# Exercise 1: Trace Task Creation Path

Goal: infer how a user task becomes a call to your workflow run method.

## Context files

- `scale-agentex/agentex/docs/docs/acp/agentic/temporal.md`
- `scale-agentex-python/src/agentex/lib/sdk/fastacp/impl/temporal_acp.py`
- `scale-agentex-python/src/agentex/lib/core/temporal/services/temporal_task_service.py`

## Steps

1. In `temporal.md`, find the claim:
- `@acp.on_task_create` forwards to `@workflow.run`.

2. In `temporal_acp.py`, find `_setup_handlers` and read `handle_task_create`.

3. In `temporal_task_service.py`, find `submit_task(...)` and read the `start_workflow(...)` call.

4. Identify the four values passed to Temporal start:
- `workflow`
- `arg`
- `id`
- `task_queue`

5. Explain in 3-5 lines:
- Why `WORKFLOW_NAME` must match `@workflow.defn(name=...)`.
- Why `task.id` is used as workflow `id`.

## Self-check

You are done when you can clearly say:

- "ACP does not run my business logic directly."
- "ACP starts a workflow by name, and Temporal dispatches to the `@workflow.run` method."
