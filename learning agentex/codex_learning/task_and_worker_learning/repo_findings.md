# Task and Worker Repo Findings

This note captures references from both repos related to tasks, workers, assignment, and routing.

## Server-side (`scale-agentex`)

1. `scale-agentex/agentex/src/temporal/run_worker.py`
   - Worker starts on exactly one `task_queue` and executes registered workflows/activities.
   - Key idea: queue binding is explicit and operationally critical.

2. `scale-agentex/agentex/src/temporal/run_healthcheck_workflow.py`
   - Health-check workflows are started with `task_queue=environment_variables.AGENTEX_SERVER_TASK_QUEUE`.
   - Key idea: workflow execution is routed by queue name.

3. `scale-agentex/agentex/src/config/environment_variables.py`
   - `AGENTEX_SERVER_TASK_QUEUE` is configurable from env.
   - Key idea: misconfiguration can route tasks to queues with no workers.

4. `scale-agentex/agentex/src/api/schemas/schedules.py`
   - Schedule request includes `task_queue` ("where the agent's worker is listening").
   - Key idea: producers must target a queue that consumers actually poll.

5. `scale-agentex/agentex/src/domain/repositories/task_repository.py`
   - Task creation also creates an `AgentTaskTracker` row (`last_processed_event_id=None`).
   - Key idea: task lifecycle and processing cursor are coupled at creation time.

6. `scale-agentex/agentex/src/domain/repositories/agent_task_tracker_repository.py`
   - Cursor commits use `SELECT ... FOR UPDATE` and forbid moving backward by sequence.
   - Key idea: assignment/processing state must be monotonic to stay replay-safe.

## SDK-side (`scale-agentex-python`)

1. `scale-agentex-python/src/agentex/lib/core/temporal/services/temporal_task_service.py`
   - `submit_task` starts workflow with `task_queue=self._env_vars.WORKFLOW_TASK_QUEUE`.
   - Key idea: task routing to workers is queue-driven at submit time.

2. `scale-agentex-python/src/agentex/lib/core/temporal/workers/worker.py`
   - `AgentexWorker` is created with a single `task_queue`; Temporal worker polls that queue.
   - Key idea: worker identity and capability are represented by queue membership.

3. `scale-agentex-python/src/agentex/lib/environment_variables.py`
   - `WORKFLOW_TASK_QUEUE`/`WORKFLOW_NAME` are first-class env vars.
   - Key idea: runtime configuration controls routing contract.

4. `scale-agentex-python/src/agentex/lib/cli/templates/temporal/manifest.yaml.j2`
   - Agent manifest defines `temporal.workflows[].queue_name`.
   - Key idea: deployment config declares assignment topology (which tasks go where).

## Selected foundational topic

**Task queue to worker assignment integrity**:
How tasks are routed by queue name, how workers claim tasks, and how retries/dead-lettering preserve correctness when execution fails.
