from __future__ import annotations

"""
Mini Temporal teaching engine.

This file intentionally models Temporal at a conceptual level:
1) A workflow is orchestration logic that yields "do this activity next".
2) Activities are side-effect functions (DB/API/email/etc).
3) Workers poll a task queue and execute workflow/activity tasks.
4) History is append-only so you can inspect exactly what happened.

What this mock intentionally does NOT provide:
- true durability across process restarts
- distributed workers
- timers/signals/queries/versioning
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, Generator, Optional
import uuid


@dataclass
class ActivityCall:
    """
    Represents a workflow command: "please run activity X with these args".

    In real Temporal, workflow code does not call side-effect code directly.
    Instead it schedules an activity command that a worker executes separately.
    """

    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    max_attempts: int = 3


def call_activity(name: str, *args: Any, max_attempts: int = 3, **kwargs: Any) -> ActivityCall:
    """
    Helper used inside workflow code.

    This makes workflow code read like:
        result = yield call_activity("charge_card", ...)

    `yield` is important in this mock: it pauses the workflow and asks the engine
    to schedule the activity task.
    """

    return ActivityCall(name=name, args=args, kwargs=kwargs, max_attempts=max_attempts)


@dataclass
class WorkflowTask:
    """
    Unit of work that advances workflow orchestration state by one step.
    """

    workflow_id: str


@dataclass
class ActivityTask:
    """
    Unit of work that executes one side-effecting activity attempt.
    """

    workflow_id: str
    activity_id: str
    call: ActivityCall
    attempt: int


@dataclass
class WorkflowExecution:
    """
    In-memory execution state for one workflow instance.

    `next_value`/`next_error` model how activity outcomes are fed back into
    workflow code:
    - success -> send(value)
    - failure after retries -> throw(error)
    """

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
    history: list[dict[str, Any]] = field(default_factory=list)


class MiniTemporal:
    """
    Tiny single-process scheduler + worker loop.

    Conceptual mapping to real Temporal:
    - `workflows`/`activities`: registered definitions
    - `task_queue`: server-side queue (in Temporal, persisted)
    - `run_until_idle`: workers polling and executing tasks
    - `history`: event history for observability/debugging
    """

    def __init__(self) -> None:
        self.workflows: dict[str, Callable[[Any], Generator[Any, Any, Any]]] = {}
        self.activities: dict[str, Callable[..., Any]] = {}
        self.executions: dict[str, WorkflowExecution] = {}
        self.task_queue: Deque[WorkflowTask | ActivityTask] = deque()

    def register_workflow(self, name: str, fn: Callable[[Any], Generator[Any, Any, Any]]) -> None:
        """Register orchestration logic."""
        self.workflows[name] = fn

    def register_activity(self, name: str, fn: Callable[..., Any]) -> None:
        """Register side-effect implementation."""
        self.activities[name] = fn

    def start_workflow(self, workflow_name: str, workflow_input: Any) -> str:
        """
        Create a workflow execution and enqueue its first workflow task.

        A "workflow task" means: "advance orchestration until next command
        (or completion/failure)".
        """

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

    def run_until_idle(self, max_steps: int = 10_000) -> None:
        """
        Worker loop: keep polling tasks until queue is empty.

        Real Temporal has many workers, often across machines. This mock uses
        one in-process loop to keep the mechanics visible.
        """

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
        """
        Execute one orchestration step.

        Workflow step outcomes:
        - yields ActivityCall -> schedule activity task
        - returns value -> workflow completed
        - raises -> workflow failed
        """

        execution = self.executions[task.workflow_id]
        if execution.status != "RUNNING":
            return

        try:
            if execution.next_error is not None:
                # Resume workflow with a thrown error from failed activity chain.
                err = execution.next_error
                execution.next_error = None
                yielded = execution.generator.throw(err)
                execution.started = True
            elif not execution.started:
                # First activation of workflow code.
                yielded = next(execution.generator)
                execution.started = True
            else:
                # Resume workflow with last successful activity result.
                value = execution.next_value
                execution.next_value = None
                yielded = execution.generator.send(value)

            if not isinstance(yielded, ActivityCall):
                raise TypeError(
                    f"Workflow must yield ActivityCall, got {type(yielded).__name__}"
                )

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

        except StopIteration as done:
            # Generator return value means workflow completion.
            execution.status = "COMPLETED"
            execution.result = done.value
            execution.history.append({"event": "WorkflowCompleted", "result": done.value})
        except Exception as exc:
            # Any uncaught workflow exception marks execution as failed.
            execution.status = "FAILED"
            execution.error = str(exc)
            execution.history.append({"event": "WorkflowFailed", "error": str(exc)})

    def _run_activity_task(self, task: ActivityTask) -> None:
        """
        Execute one activity attempt.

        Activity outcomes:
        - success -> record completion, wake workflow with result
        - failure + attempts left -> enqueue retry
        - failure + no attempts left -> wake workflow with exception
        """

        execution = self.executions[task.workflow_id]
        if execution.status != "RUNNING":
            return

        fn = self.activities.get(task.call.name)
        if fn is None:
            # Unknown activity is a non-retryable engine/config issue here.
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
            # Re-enqueue workflow task so orchestration can continue.
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
                # Retry policy: immediate retry in this mock.
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
                # Retries exhausted: surface failure to workflow logic.
                execution.next_error = RuntimeError(
                    f"Activity {task.call.name} failed after {task.attempt} attempts: {exc}"
                )
                self.task_queue.append(WorkflowTask(workflow_id=task.workflow_id))


# ------------------ Demo domain (side-effect activities) ------------------

FAKE_DB: list[dict[str, Any]] = []
FAKE_OUTBOX: list[dict[str, Any]] = []
CHARGE_ATTEMPTS: dict[str, int] = {}


def get_shipping_quote(zip_code: str) -> dict[str, Any]:
    # Pure computation / external query simulation.
    return {"carrier": "mock-express", "cost": 8.5, "zip_code": zip_code}


def charge_card(order_id: str, amount: float) -> str:
    attempts = CHARGE_ATTEMPTS.get(order_id, 0) + 1
    CHARGE_ATTEMPTS[order_id] = attempts

    # Intentional transient failure on first attempt to demonstrate retries.
    if attempts == 1:
        raise RuntimeError("payment gateway timeout")

    return f"payment_{order_id}_{amount:.2f}"


def write_order_to_db(order_id: str, payment_id: str, quote: dict[str, Any]) -> None:
    # Side effect: mutates external state (database).
    FAKE_DB.append({"order_id": order_id, "payment_id": payment_id, "shipping_quote": quote})


def send_confirmation_email(email: str, order_id: str) -> None:
    # Side effect: emits outbound communication.
    FAKE_OUTBOX.append({"to": email, "subject": f"Order {order_id} confirmed"})


def order_workflow(order: dict[str, Any]) -> Generator[Any, Any, dict[str, Any]]:
    """
    Workflow = orchestration only.

    Notice the workflow does not directly mutate DB/send email/charge card.
    It only schedules activities and stitches results into a business outcome.
    """

    if order["amount"] <= 0:
        return {"status": "REJECTED", "reason": "amount must be positive"}

    # Step 1: get quote.
    quote = yield call_activity("get_shipping_quote", order["zip_code"], max_attempts=2)
    # Step 2: charge payment (demonstrates transient failure + retry).
    payment_id = yield call_activity(
        "charge_card",
        order["order_id"],
        order["amount"] + quote["cost"],
        max_attempts=3,
    )
    # Step 3: persist order.
    yield call_activity("write_order_to_db", order["order_id"], payment_id, quote, max_attempts=1)
    # Step 4: notify customer.
    yield call_activity(
        "send_confirmation_email",
        order["email"],
        order["order_id"],
        max_attempts=2,
    )

    return {
        "status": "CONFIRMED",
        "order_id": order["order_id"],
        "payment_id": payment_id,
        "shipping_quote": quote,
    }


def main() -> None:
    # Engine setup: register workflow definitions and activity implementations.
    engine = MiniTemporal()
    engine.register_workflow("order_workflow", order_workflow)

    engine.register_activity("get_shipping_quote", get_shipping_quote)
    engine.register_activity("charge_card", charge_card)
    engine.register_activity("write_order_to_db", write_order_to_db)
    engine.register_activity("send_confirmation_email", send_confirmation_email)

    workflow_id = engine.start_workflow(
        "order_workflow",
        {
            "order_id": "ord_123",
            "amount": 99.0,
            "zip_code": "94107",
            "email": "alice@example.com",
        },
    )
    # Run worker loop until no more tasks are queued.
    engine.run_until_idle()

    execution = engine.executions[workflow_id]
    print(f"workflow_id={workflow_id}")
    print(f"status={execution.status}")
    print(f"result={execution.result}")
    print(f"db_rows={FAKE_DB}")
    print(f"outbox={FAKE_OUTBOX}")
    print("\nEvent history:")
    for i, event in enumerate(execution.history, 1):
        print(f"{i:02d}. {event}")


if __name__ == "__main__":
    main()
