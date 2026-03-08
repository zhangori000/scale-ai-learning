from __future__ import annotations

"""
Mini Temporal with signals (teaching version).

This extends the original mock to show how external events (signals) interact
with workflow orchestration.

Concepts modeled:
- workflow tasks: advance orchestration logic
- activity tasks: execute side effects
- signals: external events delivered to a running workflow
- signal buffering: signals can arrive before workflow starts waiting for them
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, DefaultDict, Generator, Optional
import uuid


@dataclass
class ActivityCall:
    """Workflow command: run an activity."""

    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    max_attempts: int = 3


def call_activity(name: str, *args: Any, max_attempts: int = 3, **kwargs: Any) -> ActivityCall:
    return ActivityCall(name=name, args=args, kwargs=kwargs, max_attempts=max_attempts)


@dataclass
class WaitSignal:
    """
    Workflow command: pause until signal `name` arrives.

    Workflow resumes with the signal payload as the yielded expression value.
    """

    name: str


def wait_for_signal(name: str) -> WaitSignal:
    return WaitSignal(name=name)


@dataclass
class WorkflowTask:
    workflow_id: str


@dataclass
class ActivityTask:
    workflow_id: str
    activity_id: str
    call: ActivityCall
    attempt: int


@dataclass
class WorkflowExecution:
    workflow_name: str
    workflow_input: Any
    generator: Generator[Any, Any, Any]
    status: str = "RUNNING"
    result: Any = None
    error: Optional[str] = None
    started: bool = False
    next_value: Any = None
    next_error: Optional[Exception] = None
    waiting_activity_id: Optional[str] = None
    waiting_signal_name: Optional[str] = None
    signal_buffer: DefaultDict[str, Deque[Any]] = field(default_factory=lambda: defaultdict(deque))
    history: list[dict[str, Any]] = field(default_factory=list)


class MiniTemporalWithSignals:
    """
    Single-process teaching engine with activity + signal support.
    """

    def __init__(self) -> None:
        self.workflows: dict[str, Callable[[Any], Generator[Any, Any, Any]]] = {}
        self.activities: dict[str, Callable[..., Any]] = {}
        self.executions: dict[str, WorkflowExecution] = {}
        self.task_queue: Deque[WorkflowTask | ActivityTask] = deque()

    def register_workflow(self, name: str, fn: Callable[[Any], Generator[Any, Any, Any]]) -> None:
        self.workflows[name] = fn

    def register_activity(self, name: str, fn: Callable[..., Any]) -> None:
        self.activities[name] = fn

    def start_workflow(self, workflow_name: str, workflow_input: Any) -> str:
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        workflow_id = str(uuid.uuid4())
        gen = self.workflows[workflow_name](workflow_input)
        execution = WorkflowExecution(
            workflow_name=workflow_name,
            workflow_input=workflow_input,
            generator=gen,
        )
        execution.history.append(
            {"event": "WorkflowStarted", "workflow_name": workflow_name, "input": workflow_input}
        )
        self.executions[workflow_id] = execution
        self.task_queue.append(WorkflowTask(workflow_id=workflow_id))
        return workflow_id

    def signal_workflow(self, workflow_id: str, signal_name: str, payload: Any) -> None:
        """
        External caller API: deliver signal payload to a workflow.

        Delivery behavior:
        - If workflow is currently waiting for this signal, deliver immediately.
        - Otherwise, buffer it for later consumption.
        """

        execution = self.executions[workflow_id]
        execution.history.append(
            {"event": "SignalReceived", "signal_name": signal_name, "payload": payload}
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

        if execution.waiting_signal_name == signal_name:
            execution.waiting_signal_name = None
            execution.next_value = payload
            execution.history.append(
                {"event": "SignalDeliveredToWaitingWorkflow", "signal_name": signal_name}
            )
            self.task_queue.append(WorkflowTask(workflow_id=workflow_id))
        else:
            execution.signal_buffer[signal_name].append(payload)
            execution.history.append({"event": "SignalBuffered", "signal_name": signal_name})

    def run_until_idle(self, max_steps: int = 10_000) -> None:
        steps = 0
        while self.task_queue and steps < max_steps:
            steps += 1
            task = self.task_queue.popleft()
            if isinstance(task, WorkflowTask):
                self._run_workflow_task(task)
            else:
                self._run_activity_task(task)

        if steps >= max_steps:
            raise RuntimeError("Max steps reached; possible infinite loop.")

    def _run_workflow_task(self, task: WorkflowTask) -> None:
        execution = self.executions[task.workflow_id]
        if execution.status != "RUNNING":
            return

        try:
            if execution.next_error is not None:
                err = execution.next_error
                execution.next_error = None
                yielded = execution.generator.throw(err)
                execution.started = True
            elif not execution.started:
                yielded = next(execution.generator)
                execution.started = True
            else:
                value = execution.next_value
                execution.next_value = None
                yielded = execution.generator.send(value)

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
                self.task_queue.append(
                    ActivityTask(
                        workflow_id=task.workflow_id,
                        activity_id=activity_id,
                        call=yielded,
                        attempt=1,
                    )
                )
                return

            if isinstance(yielded, WaitSignal):
                signal_name = yielded.name
                buffered = self._pop_buffered_signal(execution, signal_name)

                if buffered is None:
                    execution.waiting_signal_name = signal_name
                    execution.history.append(
                        {"event": "WorkflowWaitingForSignal", "signal_name": signal_name}
                    )
                else:
                    execution.history.append(
                        {
                            "event": "SignalConsumedFromBuffer",
                            "signal_name": signal_name,
                            "payload": buffered,
                        }
                    )
                    execution.next_value = buffered
                    self.task_queue.append(WorkflowTask(workflow_id=task.workflow_id))
                return

            raise TypeError(
                f"Workflow must yield ActivityCall or WaitSignal, got {type(yielded).__name__}"
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
        execution = self.executions[task.workflow_id]
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
            self.task_queue.append(WorkflowTask(workflow_id=task.workflow_id))
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
                self.task_queue.append(
                    ActivityTask(
                        workflow_id=task.workflow_id,
                        activity_id=task.activity_id,
                        call=task.call,
                        attempt=next_attempt,
                    )
                )
            else:
                execution.next_error = RuntimeError(
                    f"Activity {task.call.name} failed after {task.attempt} attempts: {exc}"
                )
                self.task_queue.append(WorkflowTask(workflow_id=task.workflow_id))

    @staticmethod
    def _pop_buffered_signal(execution: WorkflowExecution, signal_name: str) -> Any | None:
        buf = execution.signal_buffer.get(signal_name)
        if not buf:
            return None
        return buf.popleft()


# ------------------ Demo domain ------------------

FAKE_DB: list[dict[str, Any]] = []
FAKE_OUTBOX: list[dict[str, Any]] = []


def write_order_created(order_id: str) -> None:
    FAKE_DB.append({"order_id": order_id, "status": "PENDING_APPROVAL"})


def charge_card(order_id: str, amount: float) -> str:
    return f"payment_{order_id}_{amount:.2f}"


def send_email(email: str, subject: str) -> None:
    FAKE_OUTBOX.append({"to": email, "subject": subject})


def mark_order_canceled(order_id: str) -> None:
    FAKE_DB.append({"order_id": order_id, "status": "CANCELED"})


def approval_workflow(order: dict[str, Any]) -> Generator[Any, Any, dict[str, Any]]:
    """
    Orchestration:
    1) record pending order
    2) wait for external decision signal
    3) branch into approve or cancel path
    """

    yield call_activity("write_order_created", order["order_id"])
    decision = yield wait_for_signal("customer_decision")

    if decision.get("approved"):
        payment_id = yield call_activity("charge_card", order["order_id"], order["amount"])
        yield call_activity(
            "send_email",
            order["email"],
            f"Order {order['order_id']} confirmed ({payment_id})",
        )
        return {"status": "CONFIRMED", "order_id": order["order_id"], "payment_id": payment_id}

    yield call_activity("mark_order_canceled", order["order_id"])
    yield call_activity("send_email", order["email"], f"Order {order['order_id']} canceled")
    return {"status": "CANCELED", "order_id": order["order_id"]}


def print_execution(engine: MiniTemporalWithSignals, workflow_id: str, title: str) -> None:
    e = engine.executions[workflow_id]
    print(f"\n=== {title} ===")
    print(f"workflow_id={workflow_id}")
    print(f"status={e.status}")
    print(f"waiting_signal={e.waiting_signal_name}")
    print(f"result={e.result}")
    print("history:")
    for i, event in enumerate(e.history, 1):
        print(f"{i:02d}. {event}")


def main() -> None:
    engine = MiniTemporalWithSignals()
    engine.register_workflow("approval_workflow", approval_workflow)

    engine.register_activity("write_order_created", write_order_created)
    engine.register_activity("charge_card", charge_card)
    engine.register_activity("send_email", send_email)
    engine.register_activity("mark_order_canceled", mark_order_canceled)

    # Case 1: signal arrives early and is buffered.
    early_id = engine.start_workflow(
        "approval_workflow",
        {"order_id": "ord_early", "amount": 25.0, "email": "early@example.com"},
    )
    engine.signal_workflow(early_id, "customer_decision", {"approved": True})
    engine.run_until_idle()
    print_execution(engine, early_id, "CASE 1 - EARLY SIGNAL (BUFFERED)")

    # Case 2: workflow waits first, then signal arrives later.
    late_id = engine.start_workflow(
        "approval_workflow",
        {"order_id": "ord_late", "amount": 40.0, "email": "late@example.com"},
    )
    engine.run_until_idle()  # reaches waiting-for-signal state
    print_execution(engine, late_id, "CASE 2 - BEFORE LATE SIGNAL")
    engine.signal_workflow(late_id, "customer_decision", {"approved": False})
    engine.run_until_idle()
    print_execution(engine, late_id, "CASE 2 - AFTER LATE SIGNAL")

    print("\nFAKE_DB:", FAKE_DB)
    print("FAKE_OUTBOX:", FAKE_OUTBOX)


if __name__ == "__main__":
    main()
