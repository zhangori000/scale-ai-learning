# Solution: Concurrent State Transition Engine

```python
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class WorkflowState(str, Enum):
    WAITING_FOR_USER_INPUT = "waiting_for_user_input"
    CLARIFYING_USER_QUERY = "clarifying_user_query"
    PERFORMING_DEEP_RESEARCH = "performing_deep_research"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(str, Enum):
    TASK_CREATED = "task_created"
    USER_MESSAGE_RECEIVED = "user_message_received"
    FOLLOW_UP_ASKED = "follow_up_asked"
    START_RESEARCH = "start_research"
    RESEARCH_COMPLETED = "research_completed"
    RESEARCH_FAILED = "research_failed"


class ApplyStatus(str, Enum):
    APPLIED = "applied"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Event:
    event_id: str
    task_id: str
    agent_id: str
    seq: int
    event_type: EventType


@dataclass(frozen=True)
class ApplyResult:
    status: ApplyStatus
    state: Optional[WorkflowState]
    reason: Optional[str] = None


@dataclass(frozen=True)
class TransitionRecord:
    event_id: str
    seq: int
    event_type: EventType
    from_state: Optional[WorkflowState]
    to_state: WorkflowState
    applied_at_ms: int


@dataclass(frozen=True)
class Key:
    task_id: str
    agent_id: str


class TaskAgentStateEngine:
    def __init__(self) -> None:
        self._state: dict[Key, WorkflowState] = {}
        self._last_seq: dict[Key, int] = {}
        self._applied_event_ids: dict[Key, set[str]] = defaultdict(set)
        self._history: dict[Key, list[TransitionRecord]] = defaultdict(list)
        self._locks: dict[Key, asyncio.Lock] = {}

    @staticmethod
    def _transition_target(
        event_type: EventType, current: Optional[WorkflowState]
    ) -> Optional[WorkflowState]:
        table: dict[EventType, tuple[set[Optional[WorkflowState]], WorkflowState]] = {
            EventType.TASK_CREATED: ({None}, WorkflowState.WAITING_FOR_USER_INPUT),
            EventType.USER_MESSAGE_RECEIVED: (
                {WorkflowState.WAITING_FOR_USER_INPUT},
                WorkflowState.CLARIFYING_USER_QUERY,
            ),
            EventType.FOLLOW_UP_ASKED: (
                {WorkflowState.CLARIFYING_USER_QUERY},
                WorkflowState.WAITING_FOR_USER_INPUT,
            ),
            EventType.START_RESEARCH: (
                {WorkflowState.CLARIFYING_USER_QUERY},
                WorkflowState.PERFORMING_DEEP_RESEARCH,
            ),
            EventType.RESEARCH_COMPLETED: (
                {WorkflowState.PERFORMING_DEEP_RESEARCH},
                WorkflowState.COMPLETED,
            ),
            EventType.RESEARCH_FAILED: (
                {WorkflowState.PERFORMING_DEEP_RESEARCH},
                WorkflowState.FAILED,
            ),
        }

        allowed_from, next_state = table[event_type]
        if current in allowed_from:
            return next_state
        return None

    def _lock_for(self, key: Key) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    async def apply(self, event: Event) -> ApplyResult:
        key = Key(task_id=event.task_id, agent_id=event.agent_id)

        async with self._lock_for(key):
            if event.event_id in self._applied_event_ids[key]:
                return ApplyResult(
                    status=ApplyStatus.DUPLICATE,
                    state=self._state.get(key),
                    reason="duplicate event_id",
                )

            last_seq = self._last_seq.get(key, -1)
            if event.seq < last_seq:
                return ApplyResult(
                    status=ApplyStatus.REJECTED,
                    state=self._state.get(key),
                    reason=f"out_of_order seq={event.seq} < last_seq={last_seq}",
                )

            current = self._state.get(key)
            target = self._transition_target(event.event_type, current)
            if target is None:
                return ApplyResult(
                    status=ApplyStatus.REJECTED,
                    state=current,
                    reason=f"invalid transition from {current} via {event.event_type.value}",
                )

            self._state[key] = target
            self._last_seq[key] = event.seq
            self._applied_event_ids[key].add(event.event_id)
            self._history[key].append(
                TransitionRecord(
                    event_id=event.event_id,
                    seq=event.seq,
                    event_type=event.event_type,
                    from_state=current,
                    to_state=target,
                    applied_at_ms=int(time.time() * 1000),
                )
            )
            return ApplyResult(status=ApplyStatus.APPLIED, state=target)

    def get_state(self, task_id: str, agent_id: str) -> Optional[WorkflowState]:
        return self._state.get(Key(task_id=task_id, agent_id=agent_id))

    def get_history(self, task_id: str, agent_id: str) -> list[TransitionRecord]:
        return list(self._history.get(Key(task_id=task_id, agent_id=agent_id), []))

    def dump_snapshot(self) -> dict[str, dict[str, object]]:
        out: dict[str, dict[str, object]] = {}
        for key, state in self._state.items():
            k = f"{key.task_id}:{key.agent_id}"
            out[k] = {
                "state": state.value,
                "last_seq": self._last_seq.get(key, -1),
                "history_len": len(self._history.get(key, [])),
            }
        return out


async def _self_test() -> None:
    engine = TaskAgentStateEngine()

    # 1. Happy path
    events = [
        Event("e1", "task-1", "agent-a", 1, EventType.TASK_CREATED),
        Event("e2", "task-1", "agent-a", 2, EventType.USER_MESSAGE_RECEIVED),
        Event("e3", "task-1", "agent-a", 3, EventType.START_RESEARCH),
        Event("e4", "task-1", "agent-a", 4, EventType.RESEARCH_COMPLETED),
    ]
    for ev in events:
        r = await engine.apply(ev)
        assert r.status == ApplyStatus.APPLIED
    assert engine.get_state("task-1", "agent-a") == WorkflowState.COMPLETED

    # 2. Duplicate event_id
    dup = Event("e5", "task-2", "agent-a", 1, EventType.TASK_CREATED)
    r1, r2 = await asyncio.gather(engine.apply(dup), engine.apply(dup))
    assert {r1.status, r2.status} == {ApplyStatus.APPLIED, ApplyStatus.DUPLICATE}

    # 3. Out-of-order sequence
    await engine.apply(Event("e6", "task-3", "agent-a", 3, EventType.TASK_CREATED))
    bad = await engine.apply(Event("e7", "task-3", "agent-a", 2, EventType.USER_MESSAGE_RECEIVED))
    assert bad.status == ApplyStatus.REJECTED

    # 4. Invalid transition
    await engine.apply(Event("e8", "task-4", "agent-a", 1, EventType.TASK_CREATED))
    invalid = await engine.apply(Event("e9", "task-4", "agent-a", 2, EventType.START_RESEARCH))
    assert invalid.status == ApplyStatus.REJECTED

    # 5. Isolation across agents on same task
    await engine.apply(Event("e10", "task-5", "agent-a", 1, EventType.TASK_CREATED))
    await engine.apply(Event("e11", "task-5", "agent-b", 1, EventType.TASK_CREATED))
    await engine.apply(Event("e12", "task-5", "agent-a", 2, EventType.USER_MESSAGE_RECEIVED))
    assert engine.get_state("task-5", "agent-a") == WorkflowState.CLARIFYING_USER_QUERY
    assert engine.get_state("task-5", "agent-b") == WorkflowState.WAITING_FOR_USER_INPUT


if __name__ == "__main__":
    asyncio.run(_self_test())
    print("All checks passed.")
```

## Definitive implementation notes
1. Per-key locking is mandatory. Without it, duplicate handling and ordering checks race.
2. Idempotency must be keyed by `event_id` per `(task_id, agent_id)`.
3. Transition table enforcement is the simplest way to keep behavior deterministic.
4. Audit history is not optional in distributed systems; it is your debugging truth source.
