# Exercise 2: Trace Event Signal Path

Goal: infer how an incoming event ends up in your `@workflow.signal` handler.

## Context files

- `scale-agentex-python/src/agentex/lib/sdk/fastacp/impl/temporal_acp.py`
- `scale-agentex-python/src/agentex/lib/core/temporal/services/temporal_task_service.py`
- `scale-agentex-python/examples/tutorials/10_async/10_temporal/000_hello_acp/project/workflow.py`

## Steps

1. In `temporal_acp.py`, find `handle_event_send`.
2. Follow call to `TemporalTaskService.send_event(...)`.
3. In `send_event(...)`, find the `send_signal(...)` call and note:
- `workflow_id=task.id`
- `signal=SignalName.RECEIVE_EVENT.value`
- `payload=SendEventParams(...).model_dump()`
4. In tutorial `workflow.py`, find:
- `@workflow.signal(name=SignalName.RECEIVE_EVENT)`
- `async def on_task_event_send(...)`

5. Write a short answer:
- Why does `signal` use a string name?
- What could break if the signal name in workflow decorator and sender differ?

## Self-check

You are done when you can explain:

- Signal routing is name-based.
- The payload is serialized before crossing process boundaries.
