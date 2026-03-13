from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from itertools import count
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

NO_TASK_TO_RETURN = "NO_TASK_TO_RETURN"

RawTask = Dict[str, Any]
RawSubtask = Union[str, RawTask]


class TaskServicePart1:
    """
    Part 1:
    - AddTasks(tasks)
    - ConsumeTask()
    """

    def __init__(self) -> None:
        self._heap: List[Tuple[int, int, str]] = []
        self._pending_ids: Set[str] = set()
        self._sequence = count()

    def AddTasks(self, tasks: Sequence[RawTask]) -> None:
        for task in tasks:
            task_id = _read_task_id(task)
            deadline = _read_deadline(task)
            if task_id in self._pending_ids:
                raise ValueError(f"Duplicate active task id: {task_id}")

            self._pending_ids.add(task_id)
            heapq.heappush(self._heap, (deadline, next(self._sequence), task_id))

    def ConsumeTask(self) -> str:
        if not self._heap:
            return NO_TASK_TO_RETURN

        _, _, task_id = heapq.heappop(self._heap)
        self._pending_ids.remove(task_id)
        return task_id


@dataclass
class _TaskNode:
    id: str
    deadline: Optional[int] = None
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    consumed: bool = False
    queued: bool = False


class TaskServicePart2:
    """
    Part 2:
    - Supports nested subtasks.
    - Supports subtask entries that are only IDs.
    - A task can be consumed only after all subtasks are consumed.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, _TaskNode] = {}
        self._ready_heap: List[Tuple[int, int, str]] = []
        self._sequence = count()

    def AddTasks(self, tasks: Sequence[RawTask]) -> None:
        for raw_task in tasks:
            self._ingest_task(raw_task=raw_task, parent_id=None, ancestors=set())

    def ConsumeTask(self) -> str:
        while self._ready_heap:
            _, _, task_id = heapq.heappop(self._ready_heap)
            node = self._tasks[task_id]

            # Stale entry due to dependency/definition updates.
            if not node.queued:
                continue

            node.queued = False
            if not self._is_ready(node):
                continue

            node.consumed = True
            for dependent_id in sorted(node.dependents):
                self._enqueue_if_ready(dependent_id)

            return task_id

        return NO_TASK_TO_RETURN

    def _ingest_task(self, raw_task: RawSubtask, parent_id: Optional[str], ancestors: Set[str]) -> str:
        if isinstance(raw_task, str):
            task_id = raw_task.strip()
            if not task_id:
                raise ValueError("Task IDs must be non-empty strings.")

            self._ensure_task(task_id)
            if parent_id is not None:
                self._link_dependency(parent_id=parent_id, dependency_id=task_id)
            self._enqueue_if_ready(task_id)
            return task_id

        if not isinstance(raw_task, dict):
            raise ValueError("Each task must be a dict or string subtask ID.")

        task_id = _read_task_id(raw_task)
        if task_id in ancestors:
            raise ValueError(f"Cycle detected while ingesting nested tasks at id: {task_id}")

        node = self._ensure_task(task_id)
        if parent_id is not None:
            self._link_dependency(parent_id=parent_id, dependency_id=task_id)

        if "deadline" in raw_task and raw_task["deadline"] is not None:
            deadline = _coerce_deadline(raw_task["deadline"])
            if node.deadline is not None and node.deadline != deadline:
                raise ValueError(
                    f"Conflicting deadlines for task '{task_id}': {node.deadline} vs {deadline}"
                )
            node.deadline = deadline
        elif parent_id is None and node.deadline is None:
            raise ValueError(f"Top-level task '{task_id}' is missing required deadline.")

        subtasks_value = raw_task.get("subtasks", [])
        if subtasks_value is None:
            subtasks: List[RawSubtask] = []
        elif isinstance(subtasks_value, list):
            subtasks = subtasks_value
        else:
            raise ValueError(f"Task '{task_id}' has non-list subtasks.")

        next_ancestors = set(ancestors)
        next_ancestors.add(task_id)
        for subtask in subtasks:
            self._ingest_task(raw_task=subtask, parent_id=task_id, ancestors=next_ancestors)

        self._enqueue_if_ready(task_id)
        return task_id

    def _ensure_task(self, task_id: str) -> _TaskNode:
        if task_id not in self._tasks:
            self._tasks[task_id] = _TaskNode(id=task_id)
        return self._tasks[task_id]

    def _link_dependency(self, parent_id: str, dependency_id: str) -> None:
        if parent_id == dependency_id:
            raise ValueError(f"Task '{parent_id}' cannot depend on itself.")

        parent = self._ensure_task(parent_id)
        dependency = self._ensure_task(dependency_id)
        if dependency_id in parent.dependencies:
            return

        parent.dependencies.add(dependency_id)
        dependency.dependents.add(parent_id)

        # If parent was enqueued earlier, this new dependency may make that entry stale.
        parent.queued = False

    def _enqueue_if_ready(self, task_id: str) -> None:
        node = self._tasks[task_id]
        if node.queued or node.consumed or not self._is_ready(node):
            return

        node.queued = True
        heapq.heappush(self._ready_heap, (node.deadline, next(self._sequence), task_id))

    def _is_ready(self, node: _TaskNode) -> bool:
        if node.deadline is None or node.consumed:
            return False
        return all(self._tasks[dep_id].consumed for dep_id in node.dependencies)


def _read_task_id(task: RawTask) -> str:
    if "id" not in task:
        raise ValueError("Task is missing required field 'id'.")

    raw_id = task["id"]
    if not isinstance(raw_id, str):
        raise ValueError("Task id must be a string.")

    task_id = raw_id.strip()
    if not task_id:
        raise ValueError("Task id must be a non-empty string.")

    return task_id


def _read_deadline(task: RawTask) -> int:
    if "deadline" not in task:
        raise ValueError("Task is missing required field 'deadline'.")
    return _coerce_deadline(task["deadline"])


def _coerce_deadline(raw_deadline: Any) -> int:
    if not isinstance(raw_deadline, int):
        raise ValueError("Task deadline must be an integer.")
    return raw_deadline
