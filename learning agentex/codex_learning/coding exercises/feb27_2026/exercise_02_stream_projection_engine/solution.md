# Solution: Stream Projection Engine

```python
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


EventType = Literal["start", "delta", "full", "done"]
StatusType = Literal["NOT_STARTED", "IN_PROGRESS", "DONE"]


class ApplyStatus(str, Enum):
    APPLIED = "applied"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


@dataclass(frozen=True)
class StreamEvent:
    event_id: str
    task_id: str
    message_id: str
    seq: int
    type: EventType
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ApplyResult:
    status: ApplyStatus
    reason: str | None


@dataclass(frozen=True)
class HistoryRecord:
    event_id: str
    seq: int
    type: EventType
    before_status: StatusType
    after_status: StatusType
    before_content: str
    after_content: str
    applied_at_ms: int


@dataclass
class MessageProjection:
    status: StatusType = "NOT_STARTED"
    content: str = ""
    last_seq: int = -1
    applied_event_ids: set[str] = field(default_factory=set)
    history: list[HistoryRecord] = field(default_factory=list)


@dataclass(frozen=True)
class MessageKey:
    task_id: str
    message_id: str


class ProjectionEngine:
    def __init__(self) -> None:
        self._messages: dict[MessageKey, MessageProjection] = {}
        self._locks: dict[MessageKey, asyncio.Lock] = {}

    def _get_projection(self, key: MessageKey) -> MessageProjection:
        if key not in self._messages:
            self._messages[key] = MessageProjection()
        return self._messages[key]

    def _get_lock(self, key: MessageKey) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def apply(self, event: StreamEvent) -> ApplyResult:
        key = MessageKey(task_id=event.task_id, message_id=event.message_id)

        async with self._get_lock(key):
            projection = self._get_projection(key)

            if event.event_id in projection.applied_event_ids:
                return ApplyResult(ApplyStatus.DUPLICATE, "duplicate event_id")

            if event.seq < projection.last_seq:
                return ApplyResult(
                    ApplyStatus.REJECTED,
                    f"out_of_order seq={event.seq} < last_seq={projection.last_seq}",
                )

            before_status = projection.status
            before_content = projection.content
            ok, reason = self._apply_transition(projection, event)
            if not ok:
                return ApplyResult(ApplyStatus.REJECTED, reason)

            projection.last_seq = event.seq
            projection.applied_event_ids.add(event.event_id)
            projection.history.append(
                HistoryRecord(
                    event_id=event.event_id,
                    seq=event.seq,
                    type=event.type,
                    before_status=before_status,
                    after_status=projection.status,
                    before_content=before_content,
                    after_content=projection.content,
                    applied_at_ms=int(time.time() * 1000),
                )
            )
            return ApplyResult(ApplyStatus.APPLIED, None)

    @staticmethod
    def _apply_transition(projection: MessageProjection, event: StreamEvent) -> tuple[bool, str | None]:
        if projection.status == "DONE":
            return False, "terminal state"

        if event.type == "start":
            if projection.status != "NOT_STARTED":
                return False, f"start invalid from {projection.status}"
            projection.status = "IN_PROGRESS"
            return True, None

        if event.type == "delta":
            if projection.status != "IN_PROGRESS":
                return False, f"delta invalid from {projection.status}"
            text = str(event.payload.get("text", ""))
            projection.content += text
            return True, None

        if event.type == "full":
            if projection.status != "IN_PROGRESS":
                return False, f"full invalid from {projection.status}"
            projection.content = str(event.payload.get("text", ""))
            return True, None

        if event.type == "done":
            if projection.status != "IN_PROGRESS":
                return False, f"done invalid from {projection.status}"
            projection.status = "DONE"
            return True, None

        return False, f"unknown event type: {event.type}"

    def get_message(self, task_id: str, message_id: str) -> MessageProjection:
        return self._get_projection(MessageKey(task_id=task_id, message_id=message_id))

    def get_history(self, task_id: str, message_id: str) -> list[HistoryRecord]:
        return list(self.get_message(task_id, message_id).history)

    def get_task_messages(self, task_id: str) -> dict[str, MessageProjection]:
        out: dict[str, MessageProjection] = {}
        for key, projection in self._messages.items():
            if key.task_id == task_id:
                out[key.message_id] = projection
        return out


async def _self_test() -> None:
    engine = ProjectionEngine()

    # 1) Happy path
    events = [
        StreamEvent("e1", "t1", "m1", 1, "start"),
        StreamEvent("e2", "t1", "m1", 2, "delta", {"text": "Hel"}),
        StreamEvent("e3", "t1", "m1", 3, "delta", {"text": "lo"}),
        StreamEvent("e4", "t1", "m1", 4, "done"),
    ]
    for ev in events:
        r = await engine.apply(ev)
        assert r.status == ApplyStatus.APPLIED
    m = engine.get_message("t1", "m1")
    assert m.content == "Hello" and m.status == "DONE"

    # 2) Full replacement
    await engine.apply(StreamEvent("e5", "t1", "m2", 1, "start"))
    await engine.apply(StreamEvent("e6", "t1", "m2", 2, "delta", {"text": "wrong"}))
    await engine.apply(StreamEvent("e7", "t1", "m2", 3, "full", {"text": "correct"}))
    await engine.apply(StreamEvent("e8", "t1", "m2", 4, "done"))
    assert engine.get_message("t1", "m2").content == "correct"

    # 3) Duplicate
    dup = StreamEvent("e9", "t2", "m1", 1, "start")
    r1, r2 = await asyncio.gather(engine.apply(dup), engine.apply(dup))
    assert {r1.status, r2.status} == {ApplyStatus.APPLIED, ApplyStatus.DUPLICATE}

    # 4) Out-of-order
    await engine.apply(StreamEvent("e10", "t3", "m1", 5, "start"))
    bad = await engine.apply(StreamEvent("e11", "t3", "m1", 4, "delta", {"text": "x"}))
    assert bad.status == ApplyStatus.REJECTED

    # 5) Post-terminal reject
    await engine.apply(StreamEvent("e12", "t4", "m1", 1, "start"))
    await engine.apply(StreamEvent("e13", "t4", "m1", 2, "done"))
    bad2 = await engine.apply(StreamEvent("e14", "t4", "m1", 3, "delta", {"text": "late"}))
    assert bad2.status == ApplyStatus.REJECTED

    # 6) Isolation
    await engine.apply(StreamEvent("e15", "t5", "m1", 1, "start"))
    await engine.apply(StreamEvent("e16", "t5", "m2", 1, "start"))
    await engine.apply(StreamEvent("e17", "t5", "m1", 2, "delta", {"text": "A"}))
    await engine.apply(StreamEvent("e18", "t5", "m2", 2, "delta", {"text": "B"}))
    assert engine.get_message("t5", "m1").content == "A"
    assert engine.get_message("t5", "m2").content == "B"


if __name__ == "__main__":
    asyncio.run(_self_test())
    print("All checks passed.")
```

## Senior-level takeaways
1. Reducer-style state updates make streaming behavior testable and deterministic.
2. Per-entity lock is the minimum concurrency primitive for correctness.
3. Idempotency and ordering checks must run before mutation.
