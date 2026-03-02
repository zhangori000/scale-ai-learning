# Exercise 01: Task Queue to Worker Assignment

This exercise is inspired by:
1. `scale-agentex/agentex/src/temporal/run_worker.py`
2. `scale-agentex/agentex/src/temporal/run_healthcheck_workflow.py`
3. `scale-agentex-python/src/agentex/lib/core/temporal/services/temporal_task_service.py`
4. `scale-agentex-python/src/agentex/lib/core/temporal/workers/worker.py`
5. `scale-agentex-python/src/agentex/lib/cli/templates/temporal/manifest.yaml.j2`

## What you must learn

1. Tasks are not assigned to workers directly; they are routed through a queue contract.
2. Worker assignment must prevent duplicate in-flight ownership of the same task.
3. Failure handling needs clear retry and dead-letter semantics.
4. Routing and assignment bugs are architecture bugs, not just implementation bugs.

## Problem statement

Build a minimal in-memory router that simulates how queue-based worker assignment works:

1. Producers submit tasks to a named queue.
2. Workers register themselves as polling a specific queue.
3. A poll operation assigns one pending task to a worker if capacity allows.
4. Completion can succeed, retry, or dead-letter.

## Required behavior

1. Reject task submission when no workers are bound to that queue.
2. `poll(worker_id)` must only assign tasks from the worker's queue.
3. Never assign one task to two workers at the same time.
4. On failure:
   - if retryable and attempts <= `max_retries`, re-queue task.
   - otherwise mark as `DEAD_LETTER`.
5. Maintain statuses: `PENDING`, `INFLIGHT`, `DONE`, `DEAD_LETTER`.
6. Enforce worker capacity (`max_inflight`).

## Starter code

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
        # TODO
        pass

    def submit_task(
        self,
        task_id: str,
        workflow_name: str,
        queue_name: str,
        payload: dict[str, Any],
        max_retries: int = 2,
    ) -> None:
        # TODO
        pass

    def poll(self, worker_id: str) -> Assignment | None:
        # TODO
        pass

    def complete(
        self,
        worker_id: str,
        task_id: str,
        *,
        success: bool,
        retryable: bool = True,
    ) -> None:
        # TODO
        pass


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

    print("All checks passed.")


if __name__ == "__main__":
    run_checks()
```

## Success criteria

1. `run_checks()` prints `All checks passed.`
2. No task is simultaneously owned by two workers.
3. Retry path increments attempts and returns task to `PENDING`.
4. Dead-letter tasks are terminal and tracked in `dead_letter`.
