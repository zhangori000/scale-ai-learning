from __future__ import annotations

import heapq
import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from time import monotonic
from typing import Any, Callable


class WorkerStatus(str, Enum):
    ACTIVE = "active"
    OVERLOADED = "overloaded"
    LOST = "lost"


class TaskPriority(IntEnum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class Worker:
    worker_id: str
    capacity: int = 1
    in_flight: int = 0
    last_heartbeat: float = 0.0
    status: WorkerStatus = WorkerStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)

    def available_slots(self) -> int:
        return max(0, self.capacity - self.in_flight)


@dataclass
class Task:
    task_id: str
    payload: Any
    priority: TaskPriority = TaskPriority.MEDIUM
    max_retries: int = 2
    lease_timeout_s: float = 10.0
    attempt: int = 0
    created_at: float = 0.0
    last_error: str | None = None

    @property
    def max_attempts(self) -> int:
        # Example: max_retries=2 means 1 initial attempt + 2 retries = 3 attempts total.
        return 1 + max(0, self.max_retries)


@dataclass
class Lease:
    task_id: str
    worker_id: str
    assigned_at: float
    expires_at: float


@dataclass
class Assignment:
    task_id: str
    worker_id: str
    payload: Any
    priority: TaskPriority
    attempt: int
    lease_expires_at: float


class LightweightLoadBalancer:
    """
    In-memory lightweight load balancer with:
    - worker liveness and overload states
    - priority queue scheduling
    - dynamic worker joins
    - lease-based failover and retry handling
    """

    def __init__(
        self,
        heartbeat_timeout_s: float = 15.0,
        default_lease_timeout_s: float = 10.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.heartbeat_timeout_s = heartbeat_timeout_s
        self.default_lease_timeout_s = default_lease_timeout_s
        self._clock = clock or monotonic
        self._lock = threading.RLock()

        self._workers: dict[str, Worker] = {}
        self._tasks: dict[str, Task] = {}
        self._pending_heap: list[tuple[int, int, str]] = []
        self._leases: dict[str, Lease] = {}
        self._dead_letter: list[Task] = []
        self._seq = 0

    def _now(self) -> float:
        return self._clock()

    # ---------------------------------------------------------------------
    # Worker management
    # ---------------------------------------------------------------------
    def register_worker(
        self,
        worker_id: str,
        capacity: int = 1,
        metadata: dict[str, Any] | None = None,
    ) -> Worker:
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        with self._lock:
            now = self._now()
            worker = self._workers.get(worker_id)
            if worker is None:
                worker = Worker(
                    worker_id=worker_id,
                    capacity=capacity,
                    in_flight=0,
                    last_heartbeat=now,
                    status=WorkerStatus.ACTIVE,
                    metadata=metadata or {},
                )
                self._workers[worker_id] = worker
            else:
                worker.capacity = capacity
                worker.last_heartbeat = now
                worker.status = WorkerStatus.ACTIVE
                if metadata:
                    worker.metadata.update(metadata)
            self._refresh_worker_states_locked(now)
            return worker

    def heartbeat(
        self,
        worker_id: str,
        in_flight: int | None = None,
        capacity: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Worker:
        with self._lock:
            now = self._now()
            worker = self._workers.get(worker_id)
            if worker is None:
                worker = self.register_worker(
                    worker_id=worker_id,
                    capacity=capacity or 1,
                    metadata=metadata,
                )
            worker.last_heartbeat = now
            if in_flight is not None:
                worker.in_flight = max(0, in_flight)
            if capacity is not None:
                if capacity <= 0:
                    raise ValueError("capacity must be > 0")
                worker.capacity = capacity
            if metadata:
                worker.metadata.update(metadata)
            self._refresh_worker_states_locked(now)
            return worker

    def mark_worker_lost(self, worker_id: str) -> None:
        with self._lock:
            worker = self._workers.get(worker_id)
            if not worker:
                return
            worker.status = WorkerStatus.LOST
            self._tick_locked()

    # ---------------------------------------------------------------------
    # Task lifecycle
    # ---------------------------------------------------------------------
    def enqueue_task(
        self,
        payload: Any,
        priority: TaskPriority = TaskPriority.MEDIUM,
        task_id: str | None = None,
        max_retries: int = 2,
        lease_timeout_s: float | None = None,
    ) -> str:
        with self._lock:
            now = self._now()
            task_id = task_id or str(uuid.uuid4())
            if task_id in self._tasks:
                raise ValueError(f"task_id already exists: {task_id}")
            task = Task(
                task_id=task_id,
                payload=payload,
                priority=priority,
                max_retries=max_retries,
                lease_timeout_s=lease_timeout_s or self.default_lease_timeout_s,
                created_at=now,
            )
            self._tasks[task_id] = task
            self._push_pending_locked(task_id, task.priority)
            return task_id

    def dispatch(self, max_assignments: int | None = None) -> list[Assignment]:
        with self._lock:
            self._tick_locked()
            now = self._now()
            target = max_assignments if max_assignments is not None else 10**9
            assignments: list[Assignment] = []

            while len(assignments) < target:
                task_id = self._pop_next_pending_task_id_locked()
                if task_id is None:
                    break

                worker = self._select_best_worker_locked()
                if worker is None:
                    task = self._tasks.get(task_id)
                    if task:
                        self._push_pending_locked(task_id, task.priority)
                    break

                task = self._tasks.get(task_id)
                if task is None:
                    continue

                task.attempt += 1
                if task.attempt > task.max_attempts:
                    self._dead_letter_task_locked(task, "max attempts exceeded before assign")
                    continue

                lease_ttl = task.lease_timeout_s or self.default_lease_timeout_s
                lease = Lease(
                    task_id=task.task_id,
                    worker_id=worker.worker_id,
                    assigned_at=now,
                    expires_at=now + lease_ttl,
                )
                self._leases[task.task_id] = lease
                worker.in_flight += 1

                self._refresh_worker_states_locked(now)
                assignments.append(
                    Assignment(
                        task_id=task.task_id,
                        worker_id=worker.worker_id,
                        payload=task.payload,
                        priority=task.priority,
                        attempt=task.attempt,
                        lease_expires_at=lease.expires_at,
                    )
                )
            return assignments

    def ack(
        self,
        worker_id: str,
        task_id: str,
        success: bool,
        retryable: bool = True,
        error: str | None = None,
    ) -> bool:
        with self._lock:
            lease = self._leases.get(task_id)
            task = self._tasks.get(task_id)
            if task is None:
                return False

            if lease is not None:
                if lease.worker_id != worker_id:
                    # Stale ack from non-owner worker.
                    return False
                self._leases.pop(task_id, None)
                lease_worker = self._workers.get(lease.worker_id)
                if lease_worker:
                    lease_worker.in_flight = max(0, lease_worker.in_flight - 1)

            if success:
                self._tasks.pop(task_id, None)
                self._refresh_worker_states_locked(self._now())
                return True

            task.last_error = error
            if retryable and task.attempt < task.max_attempts:
                self._push_pending_locked(task.task_id, task.priority)
            else:
                self._dead_letter_task_locked(task, error or "non-retryable failure")

            self._refresh_worker_states_locked(self._now())
            return True

    # ---------------------------------------------------------------------
    # Housekeeping / failover
    # ---------------------------------------------------------------------
    def tick(self) -> None:
        with self._lock:
            self._tick_locked()

    def _tick_locked(self) -> None:
        now = self._now()
        self._refresh_worker_states_locked(now)

        # Reclaim tasks from lost workers or expired leases.
        for lease in list(self._leases.values()):
            worker = self._workers.get(lease.worker_id)
            worker_lost = worker is None or worker.status == WorkerStatus.LOST
            lease_expired = now >= lease.expires_at
            if not worker_lost and not lease_expired:
                continue

            self._leases.pop(lease.task_id, None)
            if worker is not None:
                worker.in_flight = max(0, worker.in_flight - 1)

            task = self._tasks.get(lease.task_id)
            if task is None:
                continue

            if task.attempt < task.max_attempts:
                self._push_pending_locked(task.task_id, task.priority)
            else:
                reason = "lease expired and retry budget exhausted"
                if worker_lost:
                    reason = "worker lost and retry budget exhausted"
                self._dead_letter_task_locked(task, reason)

        self._refresh_worker_states_locked(now)

    # ---------------------------------------------------------------------
    # Debug / observability helpers
    # ---------------------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            self._tick_locked()
            workers = {
                worker_id: {
                    "status": worker.status.value,
                    "capacity": worker.capacity,
                    "in_flight": worker.in_flight,
                    "last_heartbeat": worker.last_heartbeat,
                    "metadata": dict(worker.metadata),
                }
                for worker_id, worker in self._workers.items()
            }
            pending = [item[2] for item in sorted(self._pending_heap)]
            leases = {
                task_id: {
                    "worker_id": lease.worker_id,
                    "assigned_at": lease.assigned_at,
                    "expires_at": lease.expires_at,
                }
                for task_id, lease in self._leases.items()
            }
            dead_letter = [task.task_id for task in self._dead_letter]
            return {
                "workers": workers,
                "pending_count": len([t for t in pending if t in self._tasks and t not in self._leases]),
                "leases_count": len(self._leases),
                "dead_letter_count": len(dead_letter),
                "pending_task_ids": pending,
                "leased_task_ids": list(self._leases.keys()),
                "dead_letter_task_ids": dead_letter,
            }

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _refresh_worker_states_locked(self, now: float) -> None:
        for worker in self._workers.values():
            if now - worker.last_heartbeat > self.heartbeat_timeout_s:
                worker.status = WorkerStatus.LOST
                continue
            if worker.in_flight >= worker.capacity:
                worker.status = WorkerStatus.OVERLOADED
            else:
                worker.status = WorkerStatus.ACTIVE

    def _select_best_worker_locked(self) -> Worker | None:
        candidates = [
            worker
            for worker in self._workers.values()
            if worker.status != WorkerStatus.LOST and worker.available_slots() > 0
        ]
        if not candidates:
            return None
        candidates.sort(
            key=lambda w: (
                w.in_flight / max(1, w.capacity),
                w.in_flight,
                -w.last_heartbeat,
            )
        )
        return candidates[0]

    def _push_pending_locked(self, task_id: str, priority: TaskPriority) -> None:
        self._seq += 1
        heapq.heappush(self._pending_heap, (int(priority), self._seq, task_id))

    def _pop_next_pending_task_id_locked(self) -> str | None:
        while self._pending_heap:
            _, _, task_id = heapq.heappop(self._pending_heap)
            if task_id not in self._tasks:
                continue
            if task_id in self._leases:
                continue
            return task_id
        return None

    def _dead_letter_task_locked(self, task: Task, reason: str) -> None:
        task.last_error = reason
        self._dead_letter.append(task)
        self._tasks.pop(task.task_id, None)
        self._leases.pop(task.task_id, None)


__all__ = [
    "Assignment",
    "LightweightLoadBalancer",
    "TaskPriority",
    "WorkerStatus",
]
