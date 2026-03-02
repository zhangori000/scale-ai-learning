# Solution: Task Queue to Worker Assignment

## Design rules

1. Queue binding is a contract: submit only to queues with active workers.
2. Assignment is exclusive: one task can have only one in-flight owner.
3. Completion decides lifecycle:
   - success -> `DONE`
   - retryable failure within budget -> `PENDING`
   - otherwise -> `DEAD_LETTER`
4. Capacity matters: workers cannot exceed `max_inflight`.

## Reference implementation

```python
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any, Literal


TaskStatus = Literal["PENDING", "INFLIGHT", "DONE", "DEAD_LETTER"]


@dataclass
class TaskRecord:
    task_id: str
    workflow_name: str
    queue_name: str
    payload: dict[str, Any]
    max_retries: int = 2
    attempts: int = 0
    status: TaskStatus = "PENDING"


@dataclass
class WorkerState:
    worker_id: str
    queue_name: str
    max_inflight: int = 1
    inflight: set[str] = field(default_factory=set)


@dataclass
class Assignment:
    worker_id: str
    task_id: str
    queue_name: str
    attempt: int


class TaskQueueRouter:
    def __init__(self):
        self.tasks: dict[str, TaskRecord] = {}
        self.workers: dict[str, WorkerState] = {}
        self.pending_by_queue: dict[str, deque[str]] = defaultdict(deque)
        self.worker_count_by_queue: dict[str, int] = defaultdict(int)
        self.inflight_owner: dict[str, str] = {}  # task_id -> worker_id
        self.dead_letter: list[str] = []

    def register_worker(self, worker_id: str, queue_name: str, max_inflight: int = 1) -> None:
        if worker_id in self.workers:
            prev = self.workers[worker_id]
            self.worker_count_by_queue[prev.queue_name] -= 1

        worker = WorkerState(
            worker_id=worker_id,
            queue_name=queue_name,
            max_inflight=max_inflight,
        )
        self.workers[worker_id] = worker
        self.worker_count_by_queue[queue_name] += 1

    def submit_task(
        self,
        task_id: str,
        workflow_name: str,
        queue_name: str,
        payload: dict[str, Any],
        max_retries: int = 2,
    ) -> None:
        if self.worker_count_by_queue[queue_name] <= 0:
            raise ValueError(f"No workers registered for queue '{queue_name}'")
        if task_id in self.tasks:
            raise ValueError(f"Task '{task_id}' already exists")

        record = TaskRecord(
            task_id=task_id,
            workflow_name=workflow_name,
            queue_name=queue_name,
            payload=payload,
            max_retries=max_retries,
            attempts=0,
            status="PENDING",
        )
        self.tasks[task_id] = record
        self.pending_by_queue[queue_name].append(task_id)

    def poll(self, worker_id: str) -> Assignment | None:
        if worker_id not in self.workers:
            raise ValueError(f"Unknown worker '{worker_id}'")

        worker = self.workers[worker_id]
        if len(worker.inflight) >= worker.max_inflight:
            return None

        queue = self.pending_by_queue[worker.queue_name]
        while queue:
            task_id = queue.popleft()
            task = self.tasks[task_id]

            if task.status != "PENDING":
                continue

            # Exclusive ownership invariant
            if task_id in self.inflight_owner:
                continue

            task.status = "INFLIGHT"
            self.inflight_owner[task_id] = worker_id
            worker.inflight.add(task_id)
            return Assignment(
                worker_id=worker_id,
                task_id=task_id,
                queue_name=worker.queue_name,
                attempt=task.attempts + 1,
            )

        return None

    def complete(
        self,
        worker_id: str,
        task_id: str,
        *,
        success: bool,
        retryable: bool = True,
    ) -> None:
        if worker_id not in self.workers:
            raise ValueError(f"Unknown worker '{worker_id}'")
        if task_id not in self.tasks:
            raise ValueError(f"Unknown task '{task_id}'")

        owner = self.inflight_owner.get(task_id)
        if owner != worker_id:
            raise ValueError(
                f"Worker '{worker_id}' cannot complete '{task_id}' owned by '{owner}'"
            )

        worker = self.workers[worker_id]
        task = self.tasks[task_id]

        # Release ownership first
        worker.inflight.discard(task_id)
        del self.inflight_owner[task_id]

        if success:
            task.status = "DONE"
            return

        task.attempts += 1
        can_retry = retryable and task.attempts <= task.max_retries
        if can_retry:
            task.status = "PENDING"
            self.pending_by_queue[task.queue_name].append(task_id)
        else:
            task.status = "DEAD_LETTER"
            self.dead_letter.append(task_id)


def run_checks() -> None:
    router = TaskQueueRouter()
    router.register_worker("w-a-1", "queue-a", max_inflight=1)
    router.register_worker("w-b-1", "queue-b", max_inflight=1)

    router.submit_task("task-1", "wf-a", "queue-a", {"v": 1}, max_retries=1)
    router.submit_task("task-2", "wf-b", "queue-b", {"v": 2}, max_retries=2)

    a1 = router.poll("w-a-1")
    b1 = router.poll("w-b-1")
    assert a1 and a1.task_id == "task-1"
    assert b1 and b1.task_id == "task-2"

    # Retry path
    router.complete("w-b-1", "task-2", success=False, retryable=True)
    b2 = router.poll("w-b-1")
    assert b2 and b2.task_id == "task-2"

    # Success completion
    router.complete("w-a-1", "task-1", success=True)
    assert router.tasks["task-1"].status == "DONE"

    # Non-retryable failure goes to dead-letter
    router.complete("w-b-1", "task-2", success=False, retryable=False)
    assert router.tasks["task-2"].status == "DEAD_LETTER"
    assert "task-2" in router.dead_letter

    # Reject submit to queue with no workers
    try:
        router.submit_task("task-3", "wf-c", "queue-c", {"v": 3})
        raise AssertionError("Expected ValueError for unbound queue")
    except ValueError:
        pass

    # Assignment exclusivity: no task can remain inflight after completion.
    assert "task-1" not in router.inflight_owner
    assert "task-2" not in router.inflight_owner

    print("All checks passed.")


if __name__ == "__main__":
    run_checks()
```

## Why this is foundational for Agentex

1. It mirrors `submit_task(... task_queue=...)` routing behavior in the SDK.
2. It mirrors worker queue binding (`Worker(task_queue=...)`) semantics.
3. It forces you to reason about assignment ownership and retry budget, which are the core failure semantics of real worker systems.
