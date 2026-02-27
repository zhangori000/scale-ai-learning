# Exercise 2: Durable Streaming State Machine

This exercise is inspired by:
1. `scale-agentex/agentex/docs/docs/concepts/streaming.md`
2. `scale-agentex/agentex/src/domain/use_cases/agents_acp_use_case.py` (`_handle_message_send_stream`)
3. `scale-agentex-python/src/agentex/resources/messages/messages.py` (`with_streaming_response`)

## What you must learn

A senior engineer must understand this non-negotiable rule:
1. Streaming to clients is real-time and lossy.
2. Durable message history is replayable and authoritative.
3. Your orchestrator must keep both views consistent.

## System design deliverables (required before coding)

1. Functional requirements:
   - handle `START`, `DELTA`, `DONE`, `FULL`.
   - support multiple concurrent message indexes.
2. Non-functional requirements:
   - low-latency stream forwarding.
   - crash-safe persistence semantics.
3. Failure strategy:
   - duplicate chunks
   - `DELTA` arriving before `START`
   - stream abort before `DONE`
4. Invariants:
   - exactly one durable parent message per `(task_id, index)`
   - `DONE` means final persisted content exists

## Coding challenge

Implement `StreamingOrchestrator.stream_and_persist`.

### Required behavior

1. On first update for an index, create parent message once.
2. If first update is `DELTA`, synthesize `START` semantics internally.
3. Accumulate deltas per index.
4. On `DONE`, flush final accumulated content and mark status `"DONE"`.
5. On `FULL`, write final content immediately and mark index complete.
6. Ignore further updates for completed indexes.
7. When source ends, flush any non-completed indexes.
8. If `fail_on_chunk_n` triggers, mark task failed and raise.

## Starter code

```python
import asyncio
from dataclasses import dataclass
from typing import AsyncIterator, Literal


Status = Literal["IN_PROGRESS", "DONE"]


@dataclass
class Start:
    index: int
    content: str


@dataclass
class Delta:
    index: int
    text_delta: str


@dataclass
class Done:
    index: int


@dataclass
class Full:
    index: int
    content: str


StreamUpdate = Start | Delta | Done | Full


@dataclass
class MessageRecord:
    id: str
    task_id: str
    index: int
    content: str
    status: Status


class InMemoryMessageRepo:
    def __init__(self):
        self.messages: dict[str, MessageRecord] = {}
        self.by_task: dict[str, list[str]] = {}
        self._seq = 0

    def _next_id(self) -> str:
        self._seq += 1
        return f"msg-{self._seq:06d}"

    async def create(self, task_id: str, index: int, content: str, status: Status) -> MessageRecord:
        mid = self._next_id()
        record = MessageRecord(id=mid, task_id=task_id, index=index, content=content, status=status)
        self.messages[mid] = record
        self.by_task.setdefault(task_id, []).append(mid)
        return record

    async def update(self, message_id: str, content: str, status: Status | None = None) -> MessageRecord:
        record = self.messages[message_id]
        record.content = content
        if status is not None:
            record.status = status
        return record

    async def list_by_task(self, task_id: str) -> list[MessageRecord]:
        return [self.messages[mid] for mid in self.by_task.get(task_id, [])]


class StreamingOrchestrator:
    def __init__(self, repo: InMemoryMessageRepo):
        self.repo = repo
        self.failed_tasks: set[str] = set()

    async def stream_and_persist(
        self,
        task_id: str,
        updates: AsyncIterator[StreamUpdate],
        fail_on_chunk_n: int | None = None,
    ) -> AsyncIterator[str]:
        """
        TODO:
        - Maintain:
          - parent_message_by_index
          - accumulator_by_index
          - completed_indexes
        - Yield client-visible events as strings:
          - START index=<i> message_id=<id>
          - DELTA index=<i> text=<delta>
          - DONE index=<i> message_id=<id>
          - FULL index=<i> message_id=<id>
        - Enforce required behavior list above.
        """
        pass


async def source_updates() -> AsyncIterator[StreamUpdate]:
    # Intentional DELTA before START for index 1
    yield Delta(index=1, text_delta="Hel")
    yield Delta(index=1, text_delta="lo")
    yield Done(index=1)
    yield Full(index=2, content="Single shot message")


async def demo():
    repo = InMemoryMessageRepo()
    orchestrator = StreamingOrchestrator(repo)

    async for event in orchestrator.stream_and_persist("task-200", source_updates()):
        print(event)

    stored = await repo.list_by_task("task-200")
    for m in stored:
        print(m)


if __name__ == "__main__":
    asyncio.run(demo())
```

## Success criteria

1. Exactly one durable parent record per index.
2. `index=1` final persisted content equals `"Hello"` and status is `"DONE"`.
3. `index=2` persisted from `FULL` with status `"DONE"`.
4. Duplicate or late updates after completion are ignored.

