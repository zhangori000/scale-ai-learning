# Agentex-Style Temporal Mock

This mock is intentionally shaped like docs examples:

- `workflow.py`
- `acp.py`
- `run_worker.py`

It answers:
1. What do `@workflow.defn` and `@workflow.run` do?
2. Why are `workflow.py` and `acp.py` separate files?
3. What runs where (ACP server vs worker vs Temporal service)?

## File mapping to docs

### `workflow.py`
Contains workflow class and decorators:
- `@workflow.defn(name="...")`: workflow type registration metadata
- `@workflow.run`: entrypoint method metadata
- `@workflow.signal(name=...)`: signal handler metadata

### `acp.py`
Contains protocol bridge:
- `on_task_create` maps to `TemporalClient.start_workflow(...)`
- `on_task_event_send` maps to `TemporalClient.signal_workflow(...)`

This is the "under-the-hood" piece not shown in most high-level docs.

### `run_worker.py`
Contains worker setup:
- register workflow class
- register activities
- poll a task queue and execute tasks

## What runs where

In real deployments these are often separate processes/pods:

1. ACP process (`acp.py`)
- receives Agentex ACP traffic (`task/create`, `event/send`)
- calls Temporal client APIs

2. Worker process (`run_worker.py`)
- polls Temporal task queue
- executes workflow code + activity code

3. Temporal service (server)
- stores workflow state/history
- routes tasks/signals to queues

In this teaching mock they run in one Python process, but with separated classes.

## Decorator confusion clarified

- `@workflow.defn` and `@workflow.run` are markers (metadata), not the run loop.
- The run loop analog is `worker.run_until_idle(...)` in this mock (in real SDK it's worker polling APIs).

## Run the demo

```powershell
python "learning agentex\codex_learning\temporal_mock\agentex_temporal_style_mock\demo_end_to_end.py"
```

Current demo starts three workflows on the same queue:
- `MyAgentWorkflow`
- `CoinbaseWorkflow`
- `CoindeskWorkflow`

## End-to-end connection map

1. `demo_end_to_end.py`
- Builds `MiniTemporalServer`, `TemporalClient`, `ACP`, and worker.

2. `acp.py`
- `on_task_create` calls `TemporalClient.start_workflow(...)`
- `on_task_event_send` calls `TemporalClient.signal_workflow(...)`

3. `temporal_runtime.py`
- Server stores `WorkflowExecution` and enqueues queue tasks.
- Worker polls tasks, runs workflow methods, runs activities, records history.

4. `workflow.py`
- Defines workflow run loops and signal handlers.

5. `activities.py`
- Implements side-effect functions used by workflow (`create_message`, `fetch_briefing`, `analyze_sentiment`).
