# Solution: Durable Streaming State Machine

## Part 0: Definitive design rules

1. You MUST create a durable parent message exactly once per `(task_id, index)`.
2. You MUST treat `DELTA` as incremental updates to one accumulator per index.
3. You MUST mark persisted status `"DONE"` only when segment completion is certain (`DONE` or `FULL`).
4. You MUST ignore updates after an index is completed.
5. You MUST fail the task on orchestration error and stop processing.

## Part 1: Reference implementation

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
        parent_by_index: dict[int, MessageRecord] = {}
        accumulator_by_index: dict[int, str] = {}
        completed_indexes: set[int] = set()
        chunk_count = 0

        async def ensure_parent(index: int, initial_content: str) -> MessageRecord:
            if index in parent_by_index:
                return parent_by_index[index]
            parent = await self.repo.create(
                task_id=task_id,
                index=index,
                content=initial_content,
                status="IN_PROGRESS",
            )
            parent_by_index[index] = parent
            accumulator_by_index.setdefault(index, initial_content)
            return parent

        async def flush_index(index: int) -> MessageRecord | None:
            if index in completed_indexes:
                return parent_by_index.get(index)
            parent = parent_by_index.get(index)
            if not parent:
                return None

            final_content = accumulator_by_index.get(index, parent.content)
            parent = await self.repo.update(parent.id, final_content, status="DONE")
            parent_by_index[index] = parent
            completed_indexes.add(index)
            return parent

        try:
            async for update in updates:
                chunk_count += 1
                if fail_on_chunk_n is not None and chunk_count == fail_on_chunk_n:
                    raise RuntimeError(f"simulated streaming failure at chunk {chunk_count}")

                index = update.index
                if index in completed_indexes:
                    continue

                if isinstance(update, Full):
                    parent = await ensure_parent(index=index, initial_content=update.content)
                    accumulator_by_index[index] = update.content
                    parent = await self.repo.update(parent.id, update.content, status="DONE")
                    parent_by_index[index] = parent
                    completed_indexes.add(index)
                    yield f"FULL index={index} message_id={parent.id}"
                    continue

                if isinstance(update, Start):
                    parent = await ensure_parent(index=index, initial_content=update.content)
                    if index not in accumulator_by_index or accumulator_by_index[index] == "":
                        accumulator_by_index[index] = update.content
                        await self.repo.update(parent.id, accumulator_by_index[index], status="IN_PROGRESS")
                    yield f"START index={index} message_id={parent.id}"
                    continue

                if isinstance(update, Delta):
                    if index not in parent_by_index:
                        # Agentex-style behavior: delta can trigger synthetic start setup.
                        parent = await ensure_parent(index=index, initial_content="")
                        accumulator_by_index[index] = ""
                        yield f"START index={index} message_id={parent.id}"

                    parent = parent_by_index[index]
                    accumulator_by_index[index] = accumulator_by_index.get(index, "") + update.text_delta
                    await self.repo.update(parent.id, accumulator_by_index[index], status="IN_PROGRESS")
                    yield f"DELTA index={index} text={update.text_delta}"
                    continue

                if isinstance(update, Done):
                    parent = await flush_index(index)
                    if parent is not None:
                        yield f"DONE index={index} message_id={parent.id}"
                    continue

        except Exception:
            self.failed_tasks.add(task_id)
            raise

        # Stream ended normally: flush any unfinished indexes.
        unfinished = sorted(set(parent_by_index.keys()) - completed_indexes)
        for index in unfinished:
            parent = await flush_index(index)
            if parent is not None:
                yield f"DONE index={index} message_id={parent.id}"


async def source_updates() -> AsyncIterator[StreamUpdate]:
    # Intentional DELTA before START for index 1.
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

## Part 2: Code guide for confusing parts

1. `ensure_parent`:
   - Why: prevents duplicate durable rows for same index.
   - Rule: parent identity is owned by index.
2. `accumulator_by_index`:
   - Why: isolates partial text assembly per index.
   - Rule: never mix chunks between indexes.
3. synthetic `START` in `DELTA` branch:
   - Why: stream producers can emit delta-first updates.
   - Rule: normalize protocol edge cases at orchestrator boundary.
4. `flush_index`:
   - Why: creates one completion path for `DONE` and end-of-stream cleanup.
   - Rule: centralize completion logic to avoid status divergence.
5. `completed_indexes` guard:
   - Why: prevents duplicate writes after completion.
   - Rule: completion is terminal.
6. failure path:
   - Why: task-level failure marker is required for ops visibility.
   - Rule: fail fast, then rely on retry workflow.

## Part 3: Why this matches Agentex/SDK design

1. Agentex streaming lifecycle (`START/DELTA/DONE/FULL`) maps to this orchestrator state machine.
2. Agentex backend accumulates deltas and flushes durable content at completion.
3. SDK streaming wrappers expose streaming transport ergonomics; backend still owns durable correctness.

## Part 4: Definitive production upgrades

1. Persist accumulator checkpoints for long streams.
2. Add per-index idempotency tokens to ignore duplicate chunks deterministically.
3. Add timeout sweeper for stale `"IN_PROGRESS"` messages.
4. Add structured metrics for chunk latency and flush latency.

