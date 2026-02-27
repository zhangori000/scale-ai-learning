# Solution: Protocol Kernel + Adapter Boundary

```python
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class UpdateType(str, Enum):
    START = "start"
    DELTA = "delta"
    FULL = "full"
    DONE = "done"


class DeltaKind(str, Enum):
    TEXT = "text"
    DATA = "data"
    TOOL_REQUEST = "tool_request"
    TOOL_RESPONSE = "tool_response"
    REASONING_SUMMARY = "reasoning_summary"
    REASONING_CONTENT = "reasoning_content"


class ApplyStatus(str, Enum):
    APPLIED = "applied"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


@dataclass(frozen=True)
class StreamUpdate:
    update_id: str
    seq: int
    index: int
    type: UpdateType
    delta_kind: DeltaKind | None = None
    content: str | None = None


@dataclass(frozen=True)
class KernelAction:
    name: str
    index: int
    content: str | None = None
    delta_kind: DeltaKind | None = None


@dataclass(frozen=True)
class KernelResult:
    status: ApplyStatus
    actions: list[KernelAction] = field(default_factory=list)
    reason: str | None = None


@dataclass
class IndexState:
    started: bool = False
    terminal: bool = False
    start_content: str = ""
    delta_kind: DeltaKind | None = None
    delta_parts: list[str] = field(default_factory=list)
    final_content: str = ""


class ProtocolKernel:
    def __init__(self) -> None:
        self._seen_update_ids: set[str] = set()
        self._last_seq: int = -1
        self._indices: dict[int, IndexState] = {}

    @staticmethod
    def _delta_kind_compatible(existing: DeltaKind, incoming: DeltaKind) -> bool:
        if existing == incoming:
            return True
        reasoning_kinds = {DeltaKind.REASONING_SUMMARY, DeltaKind.REASONING_CONTENT}
        return existing in reasoning_kinds and incoming in reasoning_kinds

    @staticmethod
    def _flush_deltas(state: IndexState) -> str:
        return "".join(state.delta_parts)

    def apply(self, update: StreamUpdate) -> KernelResult:
        if update.update_id in self._seen_update_ids:
            return KernelResult(status=ApplyStatus.DUPLICATE, reason="duplicate update_id")

        if update.seq < self._last_seq:
            return KernelResult(
                status=ApplyStatus.REJECTED,
                reason=f"out_of_order seq={update.seq} < last_seq={self._last_seq}",
            )

        state = self._indices.setdefault(update.index, IndexState())
        if state.terminal:
            return KernelResult(status=ApplyStatus.REJECTED, reason="index already terminal")

        actions: list[KernelAction] = []

        if update.type == UpdateType.START:
            if state.started:
                return KernelResult(status=ApplyStatus.REJECTED, reason="duplicate start")
            state.started = True
            state.start_content = update.content or ""
            actions.append(
                KernelAction(name="create_parent", index=update.index, content=state.start_content)
            )
            actions.append(
                KernelAction(name="emit_start", index=update.index, content=state.start_content)
            )

        elif update.type == UpdateType.DELTA:
            if update.delta_kind is None:
                return KernelResult(status=ApplyStatus.REJECTED, reason="delta_kind required for delta")

            if not state.started:
                state.started = True
                state.start_content = ""
                actions.append(KernelAction(name="create_parent", index=update.index, content=""))
                actions.append(KernelAction(name="emit_start", index=update.index, content=""))

            if state.delta_kind is None:
                state.delta_kind = update.delta_kind
            elif not self._delta_kind_compatible(state.delta_kind, update.delta_kind):
                return KernelResult(
                    status=ApplyStatus.REJECTED,
                    reason=f"delta_type_mismatch {state.delta_kind.value} vs {update.delta_kind.value}",
                )

            piece = update.content or ""
            state.delta_parts.append(piece)
            actions.append(
                KernelAction(
                    name="emit_delta",
                    index=update.index,
                    content=piece,
                    delta_kind=update.delta_kind,
                )
            )

        elif update.type == UpdateType.FULL:
            full_content = update.content or ""
            if not state.started:
                state.started = True
                actions.append(KernelAction(name="create_parent", index=update.index, content=""))

            state.final_content = full_content
            state.terminal = True
            actions.append(KernelAction(name="emit_full", index=update.index, content=full_content))
            actions.append(KernelAction(name="persist_done", index=update.index, content=full_content))

        elif update.type == UpdateType.DONE:
            if not state.started:
                return KernelResult(status=ApplyStatus.REJECTED, reason="done before start")

            final_content = state.final_content
            if not final_content:
                final_content = self._flush_deltas(state)
                state.final_content = final_content

            state.terminal = True
            actions.append(KernelAction(name="emit_done", index=update.index, content=final_content))
            actions.append(KernelAction(name="persist_done", index=update.index, content=final_content))

        else:
            return KernelResult(status=ApplyStatus.REJECTED, reason=f"unknown update type {update.type}")

        self._seen_update_ids.add(update.update_id)
        self._last_seq = update.seq
        return KernelResult(status=ApplyStatus.APPLIED, actions=actions)


class MessageStorePort(Protocol):
    async def create_in_progress(self, task_id: str, index: int, content: str) -> str:
        ...

    async def mark_done(self, task_id: str, message_id: str, content: str) -> None:
        ...


class StreamOutPort(Protocol):
    async def publish(self, task_id: str, payload: dict) -> None:
        ...


@dataclass
class Session:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    kernel: ProtocolKernel = field(default_factory=ProtocolKernel)
    index_to_message_id: dict[int, str] = field(default_factory=dict)


class ProtocolProjectionService:
    def __init__(self, message_store: MessageStorePort, stream_out: StreamOutPort) -> None:
        self._message_store = message_store
        self._stream_out = stream_out
        self._sessions: dict[tuple[str, str], Session] = {}

    def _session_for(self, task_id: str, request_id: str) -> Session:
        key = (task_id, request_id)
        if key not in self._sessions:
            self._sessions[key] = Session()
        return self._sessions[key]

    async def apply(self, task_id: str, request_id: str, update: StreamUpdate) -> KernelResult:
        session = self._session_for(task_id, request_id)
        async with session.lock:
            result = session.kernel.apply(update)
            if result.status != ApplyStatus.APPLIED:
                return result

            for action in result.actions:
                await self._execute_action(task_id, session, action)
            return result

    async def _ensure_message(self, task_id: str, session: Session, index: int, content: str = "") -> str:
        message_id = session.index_to_message_id.get(index)
        if message_id is None:
            message_id = await self._message_store.create_in_progress(task_id=task_id, index=index, content=content)
            session.index_to_message_id[index] = message_id
        return message_id

    async def _execute_action(self, task_id: str, session: Session, action: KernelAction) -> None:
        if action.name == "create_parent":
            await self._ensure_message(task_id, session, action.index, action.content or "")
            return

        if action.name in {"emit_start", "emit_delta", "emit_full", "emit_done"}:
            message_id = await self._ensure_message(task_id, session, action.index)
            payload = {
                "type": action.name.removeprefix("emit_"),
                "index": action.index,
                "message_id": message_id,
                "content": action.content,
                "delta_kind": action.delta_kind.value if action.delta_kind else None,
            }
            await self._stream_out.publish(task_id=task_id, payload=payload)
            return

        if action.name == "persist_done":
            message_id = await self._ensure_message(task_id, session, action.index)
            await self._message_store.mark_done(
                task_id=task_id,
                message_id=message_id,
                content=action.content or "",
            )
            return

        raise ValueError(f"Unknown action {action.name}")


class InMemoryMessageStore(MessageStorePort):
    def __init__(self) -> None:
        self._counter = 0
        self.messages: dict[str, dict] = {}

    async def create_in_progress(self, task_id: str, index: int, content: str) -> str:
        self._counter += 1
        message_id = f"m-{self._counter}"
        self.messages[message_id] = {
            "task_id": task_id,
            "index": index,
            "content": content,
            "status": "IN_PROGRESS",
        }
        return message_id

    async def mark_done(self, task_id: str, message_id: str, content: str) -> None:
        msg = self.messages[message_id]
        if msg["task_id"] != task_id:
            raise ValueError("task_id mismatch")
        msg["content"] = content
        msg["status"] = "DONE"


class InMemoryStreamOut(StreamOutPort):
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def publish(self, task_id: str, payload: dict) -> None:
        self.events.append({"task_id": task_id, **payload})


async def _self_test() -> None:
    store = InMemoryMessageStore()
    out = InMemoryStreamOut()
    svc = ProtocolProjectionService(store, out)

    # 1) Delta-only path
    assert (await svc.apply("t1", "r1", StreamUpdate("u1", 1, 0, UpdateType.DELTA, DeltaKind.TEXT, "Hel"))).status == ApplyStatus.APPLIED
    assert (await svc.apply("t1", "r1", StreamUpdate("u2", 2, 0, UpdateType.DELTA, DeltaKind.TEXT, "lo"))).status == ApplyStatus.APPLIED
    assert (await svc.apply("t1", "r1", StreamUpdate("u3", 3, 0, UpdateType.DONE))).status == ApplyStatus.APPLIED
    m0 = next(v for v in store.messages.values() if v["task_id"] == "t1" and v["index"] == 0)
    assert m0["status"] == "DONE" and m0["content"] == "Hello"

    # 2) Full overrides
    await svc.apply("t2", "r2", StreamUpdate("u4", 1, 0, UpdateType.START, content="x"))
    await svc.apply("t2", "r2", StreamUpdate("u5", 2, 0, UpdateType.DELTA, DeltaKind.TEXT, "wrong"))
    await svc.apply("t2", "r2", StreamUpdate("u6", 3, 0, UpdateType.FULL, content="correct"))
    m1 = next(v for v in store.messages.values() if v["task_id"] == "t2" and v["index"] == 0)
    assert m1["content"] == "correct" and m1["status"] == "DONE"

    # 3) Duplicate handling
    first = await svc.apply("t3", "r3", StreamUpdate("dup", 1, 0, UpdateType.START))
    second = await svc.apply("t3", "r3", StreamUpdate("dup", 2, 0, UpdateType.DELTA, DeltaKind.TEXT, "x"))
    assert first.status == ApplyStatus.APPLIED
    assert second.status == ApplyStatus.DUPLICATE

    # 4) Out-of-order
    await svc.apply("t4", "r4", StreamUpdate("u7", 5, 0, UpdateType.START))
    bad_order = await svc.apply("t4", "r4", StreamUpdate("u8", 4, 0, UpdateType.DELTA, DeltaKind.TEXT, "x"))
    assert bad_order.status == ApplyStatus.REJECTED

    # 5) Illegal delta mix
    await svc.apply("t5", "r5", StreamUpdate("u9", 1, 0, UpdateType.START))
    await svc.apply("t5", "r5", StreamUpdate("u10", 2, 0, UpdateType.DELTA, DeltaKind.TEXT, "x"))
    mixed = await svc.apply("t5", "r5", StreamUpdate("u11", 3, 0, UpdateType.DELTA, DeltaKind.TOOL_RESPONSE, "y"))
    assert mixed.status == ApplyStatus.REJECTED

    # 6) Terminal reject
    await svc.apply("t6", "r6", StreamUpdate("u12", 1, 0, UpdateType.START))
    await svc.apply("t6", "r6", StreamUpdate("u13", 2, 0, UpdateType.FULL, content="done-now"))
    terminal = await svc.apply("t6", "r6", StreamUpdate("u14", 3, 0, UpdateType.DELTA, DeltaKind.TEXT, "late"))
    assert terminal.status == ApplyStatus.REJECTED


if __name__ == "__main__":
    asyncio.run(_self_test())
    print("All checks passed.")
```

## Why this is senior-level
1. The kernel is pure and deterministic.
2. The adapter service is concurrency-safe and side-effect-only through ports.
3. The design separates protocol correctness from infrastructure behavior.
