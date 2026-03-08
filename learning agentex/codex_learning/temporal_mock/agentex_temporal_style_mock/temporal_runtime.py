from __future__ import annotations

"""
Mini runtime that models the pieces hidden behind Temporal docs:

- Temporal Server: stores execution state/history and task queues
- Temporal Client: start workflow + send signal APIs
- Worker: polls queue, runs workflow and activities
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Generator, Optional
import uuid

from mock_temporalio import WaitCondition


@dataclass
class ActivityCall:
    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    max_attempts: int = 3


def call_activity(name: str, *args: Any, max_attempts: int = 3, **kwargs: Any) -> ActivityCall:
    return ActivityCall(name=name, args=args, kwargs=kwargs, max_attempts=max_attempts)


@dataclass
class WorkflowTask:
    task_queue: str
    workflow_id: str


@dataclass
class ActivityTask:
    task_queue: str
    workflow_id: str
    activity_id: str
    call: ActivityCall
    attempt: int


@dataclass
class SignalEnvelope:
    name: str
    payload: Any


@dataclass
class WorkflowExecution:
    workflow_id: str
    workflow_name: str
    workflow_cls: type[Any]
    run_params: Any
    task_queue: str
    status: str = "RUNNING"
    result: Any = None
    error: Optional[str] = None

    instance: Any = None
    run_generator: Optional[Generator[Any, Any, Any]] = None
    run_method_name: str = ""
    signal_handlers: dict[str, str] = field(default_factory=dict)
    started: bool = False

    next_value: Any = None
    next_error: Optional[Exception] = None
    waiting_condition: Optional[WaitCondition] = None
    waiting_activity_id: Optional[str] = None
    pending_signals: Deque[SignalEnvelope] = field(default_factory=deque)
    history: list[dict[str, Any]] = field(default_factory=list)


class MiniTemporalServer:
    """Stores workflow state and queues (in-memory teaching version)."""

    def __init__(self) -> None:
        self.executions: dict[str, WorkflowExecution] = {}
        self.task_queues: dict[str, Deque[WorkflowTask | ActivityTask]] = {}

    def start_workflow(
        self,
        workflow_cls: type[Any],
        run_params: Any,
        task_queue: str,
        workflow_id: str | None = None,
    ) -> str:
        workflow_name = getattr(workflow_cls, "__workflow_name__", workflow_cls.__name__)
        wf_id = workflow_id or str(uuid.uuid4())
        if wf_id in self.executions:
            raise ValueError(f"Workflow ID already exists: {wf_id}")

        run_method_name, signal_handlers = _extract_workflow_metadata(workflow_cls)
        execution = WorkflowExecution(
            workflow_id=wf_id,
            workflow_name=workflow_name,
            workflow_cls=workflow_cls,
            run_params=run_params,
            task_queue=task_queue,
            run_method_name=run_method_name,
            signal_handlers=signal_handlers,
        )
        execution.history.append(
            {
                "event": "WorkflowStarted",
                "workflow_name": workflow_name,
                "workflow_id": wf_id,
                "task_queue": task_queue,
            }
        )
        self.executions[wf_id] = execution
        self.enqueue_task(WorkflowTask(task_queue=task_queue, workflow_id=wf_id))
        return wf_id

    def signal_workflow(self, workflow_id: str, signal_name: str, payload: Any) -> None:
        execution = self.executions[workflow_id]
        execution.history.append(
            {"event": "SignalRequested", "signal_name": signal_name, "payload": payload}
        )

        if execution.status != "RUNNING":
            execution.history.append(
                {
                    "event": "SignalIgnored",
                    "signal_name": signal_name,
                    "reason": f"workflow status={execution.status}",
                }
            )
            return

        execution.pending_signals.append(SignalEnvelope(name=signal_name, payload=payload))
        self.enqueue_task(WorkflowTask(task_queue=execution.task_queue, workflow_id=workflow_id))

    def enqueue_task(self, task: WorkflowTask | ActivityTask) -> None:
        queue = self.task_queues.setdefault(task.task_queue, deque())
        queue.append(task)

    def poll_task(self, task_queue: str) -> WorkflowTask | ActivityTask | None:
        queue = self.task_queues.setdefault(task_queue, deque())
        if not queue:
            return None
        return queue.popleft()

    def queue_size(self, task_queue: str) -> int:
        return len(self.task_queues.setdefault(task_queue, deque()))


class TemporalClient:
    """The API surface ACP uses to talk to Temporal Server."""

    def __init__(self, server: MiniTemporalServer) -> None:
        self.server = server

    def start_workflow(
        self,
        workflow_cls: type[Any],
        run_params: Any,
        task_queue: str,
        workflow_id: str | None = None,
    ) -> str:
        return self.server.start_workflow(
            workflow_cls=workflow_cls,
            run_params=run_params,
            task_queue=task_queue,
            workflow_id=workflow_id,
        )

    def signal_workflow(self, workflow_id: str, signal_name: str, payload: Any) -> None:
        self.server.signal_workflow(workflow_id=workflow_id, signal_name=signal_name, payload=payload)


class AgentexWorker:
    """
    Worker process model.

    In production, this is often a separate long-running process/pod polling one
    task queue continuously.
    """

    def __init__(self, server: MiniTemporalServer, task_queue: str) -> None:
        self.server = server
        self.task_queue = task_queue
        self.activities: dict[str, Callable[..., Any]] = {}
        self.workflow_names: set[str] = set()

    def register_workflow(self, workflow_cls: type[Any]) -> None:
        workflow_name = getattr(workflow_cls, "__workflow_name__", workflow_cls.__name__)
        self.workflow_names.add(workflow_name)

    def register_activities(self, activities: dict[str, Callable[..., Any]]) -> None:
        self.activities.update(activities)

    def run_until_idle(self, max_steps: int = 10_000) -> None:
        steps = 0
        while steps < max_steps:
            task = self.server.poll_task(self.task_queue)
            if task is None:
                return
            steps += 1
            if isinstance(task, WorkflowTask):
                self._run_workflow_task(task)
            else:
                self._run_activity_task(task)
        raise RuntimeError("Max steps reached; possible infinite loop.")

    def _run_workflow_task(self, task: WorkflowTask) -> None:
        execution = self.server.executions[task.workflow_id]
        if execution.status != "RUNNING":
            return

        if execution.workflow_name not in self.workflow_names:
            execution.status = "FAILED"
            execution.error = f"Workflow {execution.workflow_name} not registered on this worker"
            execution.history.append({"event": "WorkflowFailed", "error": execution.error})
            return

        if execution.instance is None:
            execution.instance = execution.workflow_cls()
            run_method = getattr(execution.instance, execution.run_method_name)
            execution.run_generator = run_method(execution.run_params)

        self._deliver_pending_signals(execution)

        if execution.waiting_condition is not None:
            if execution.waiting_condition.predicate():
                execution.history.append(
                    {
                        "event": "WaitConditionSatisfied",
                        "description": execution.waiting_condition.description,
                    }
                )
                execution.waiting_condition = None
                execution.next_value = None
            else:
                # Still waiting: do not advance the run method.
                return

        try:
            yielded: Any
            if execution.next_error is not None:
                err = execution.next_error
                execution.next_error = None
                yielded = execution.run_generator.throw(err)
                execution.started = True
            elif not execution.started:
                yielded = next(execution.run_generator)
                execution.started = True
            else:
                value = execution.next_value
                execution.next_value = None
                yielded = execution.run_generator.send(value)

            if isinstance(yielded, ActivityCall):
                activity_id = str(uuid.uuid4())
                execution.waiting_activity_id = activity_id
                execution.history.append(
                    {
                        "event": "ActivityScheduled",
                        "activity_id": activity_id,
                        "name": yielded.name,
                        "args": yielded.args,
                        "kwargs": yielded.kwargs,
                        "max_attempts": yielded.max_attempts,
                    }
                )
                self.server.enqueue_task(
                    ActivityTask(
                        task_queue=execution.task_queue,
                        workflow_id=execution.workflow_id,
                        activity_id=activity_id,
                        call=yielded,
                        attempt=1,
                    )
                )
                return

            if isinstance(yielded, WaitCondition):
                if yielded.predicate():
                    # Condition is already true; continue soon.
                    execution.history.append(
                        {
                            "event": "WaitConditionAlreadyTrue",
                            "description": yielded.description,
                        }
                    )
                    self.server.enqueue_task(
                        WorkflowTask(task_queue=execution.task_queue, workflow_id=execution.workflow_id)
                    )
                else:
                    execution.waiting_condition = yielded
                    execution.history.append(
                        {
                            "event": "WorkflowWaitingCondition",
                            "description": yielded.description,
                        }
                    )
                return

            raise TypeError(
                f"Workflow must yield ActivityCall or WaitCondition, got {type(yielded).__name__}"
            )

        except StopIteration as done:
            execution.status = "COMPLETED"
            execution.result = done.value
            execution.history.append({"event": "WorkflowCompleted", "result": done.value})
        except Exception as exc:
            execution.status = "FAILED"
            execution.error = str(exc)
            execution.history.append({"event": "WorkflowFailed", "error": str(exc)})

    def _run_activity_task(self, task: ActivityTask) -> None:
        execution = self.server.executions[task.workflow_id]
        if execution.status != "RUNNING":
            return

        fn = self.activities.get(task.call.name)
        if fn is None:
            execution.status = "FAILED"
            execution.error = f"Unknown activity: {task.call.name}"
            execution.history.append(
                {
                    "event": "ActivityFailed",
                    "activity_id": task.activity_id,
                    "name": task.call.name,
                    "attempt": task.attempt,
                    "error": execution.error,
                }
            )
            return

        try:
            result = fn(*task.call.args, **task.call.kwargs)
            execution.history.append(
                {
                    "event": "ActivityCompleted",
                    "activity_id": task.activity_id,
                    "name": task.call.name,
                    "attempt": task.attempt,
                    "result": result,
                }
            )
            execution.waiting_activity_id = None
            execution.next_value = result
            self.server.enqueue_task(
                WorkflowTask(task_queue=execution.task_queue, workflow_id=execution.workflow_id)
            )
        except Exception as exc:
            execution.history.append(
                {
                    "event": "ActivityFailed",
                    "activity_id": task.activity_id,
                    "name": task.call.name,
                    "attempt": task.attempt,
                    "error": str(exc),
                }
            )
            if task.attempt < task.call.max_attempts:
                next_attempt = task.attempt + 1
                execution.history.append(
                    {
                        "event": "ActivityRetryScheduled",
                        "activity_id": task.activity_id,
                        "name": task.call.name,
                        "next_attempt": next_attempt,
                    }
                )
                self.server.enqueue_task(
                    ActivityTask(
                        task_queue=execution.task_queue,
                        workflow_id=execution.workflow_id,
                        activity_id=task.activity_id,
                        call=task.call,
                        attempt=next_attempt,
                    )
                )
            else:
                execution.next_error = RuntimeError(
                    f"Activity {task.call.name} failed after {task.attempt} attempts: {exc}"
                )
                self.server.enqueue_task(
                    WorkflowTask(task_queue=execution.task_queue, workflow_id=execution.workflow_id)
                )

    def _deliver_pending_signals(self, execution: WorkflowExecution) -> None:
        while execution.pending_signals:
            signal = execution.pending_signals.popleft()
            method_name = execution.signal_handlers.get(signal.name)
            if method_name is None:
                execution.history.append(
                    {
                        "event": "SignalDropped",
                        "signal_name": signal.name,
                        "reason": "no handler registered",
                    }
                )
                continue
            handler = getattr(execution.instance, method_name)
            handler(signal.payload)
            execution.history.append(
                {
                    "event": "SignalHandled",
                    "signal_name": signal.name,
                    "handler": method_name,
                }
            )


def _extract_workflow_metadata(workflow_cls: type[Any]) -> tuple[str, dict[str, str]]:
    run_method_name = ""
    signal_handlers: dict[str, str] = {}

    for attr_name in dir(workflow_cls):
        attr = getattr(workflow_cls, attr_name)
        if getattr(attr, "__is_workflow_run__", False):
            run_method_name = attr_name
        signal_name = getattr(attr, "__workflow_signal_name__", None)
        if signal_name is not None:
            signal_handlers[signal_name] = attr_name

    if not run_method_name:
        raise ValueError(
            f"Workflow class {workflow_cls.__name__} is missing a @workflow.run method"
        )

    return run_method_name, signal_handlers
