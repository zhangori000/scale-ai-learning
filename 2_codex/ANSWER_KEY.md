# Answer Key (Use After Attempting)

## Exercise 1 expected conclusions

1. `TemporalACP._setup_handlers` installs ACP handlers.
2. On task create, handler calls `TemporalTaskService.submit_task(...)`.
3. `submit_task(...)` calls `TemporalClient.start_workflow(...)`.
4. Workflow is started by string name (`WORKFLOW_NAME`), with:
- `arg=CreateTaskParams(...)`
- `id=task.id`
- `task_queue=WORKFLOW_TASK_QUEUE`
5. `WORKFLOW_NAME` must match `@workflow.defn(name=...)` so worker registration and start request refer to the same workflow type.

## Exercise 2 expected conclusions

1. Event send path is ACP handler -> `TemporalTaskService.send_event(...)` -> `TemporalClient.send_signal(...)`.
2. Signal routing is name-based using `SignalName.RECEIVE_EVENT.value`.
3. Payload is serialized (`model_dump`) before transmission.
4. If signal names differ between sender and `@workflow.signal(name=...)`, the workflow handler will not be matched.

## Exercise 3 expected conclusions

1. Decorators annotate classes/functions with metadata.
2. Runtime (worker/client) uses that metadata to route start/signal/query calls.
3. Decorators alone do not execute workflows; they define registration/dispatch metadata.
