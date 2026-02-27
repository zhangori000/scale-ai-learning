# Codex Comments Solution 30: Crash-Safe Redis Stream Pointer

```python
import asyncio
from typing import AsyncIterator

from pydantic import BaseModel, ValidationError


class TaskEvent(BaseModel):
    task_id: str
    status: str


class MockRedis:
    def __init__(self):
        self.stream = [
            ("1000-0", {"task_id": "A1", "status": "running"}),
            ("1001-0", {"task_id": "A2", "status": "completed"}),
            ("1002-0", {"BAD_DATA": "missing_fields"}),  # poison pill
            ("1003-0", {"task_id": "A3", "status": "failed"}),
        ]

    async def read_batch(self, last_id: str, count: int = 2) -> list[tuple[str, dict]]:
        result: list[tuple[str, dict]] = []
        for msg_id, data in self.stream:
            if last_id == "0" or msg_id > last_id:
                result.append((msg_id, data))
                if len(result) == count:
                    break
        return result


class CheckpointStore:
    def __init__(self):
        self.value: str = "0"

    async def load(self) -> str:
        return self.value

    async def save(self, message_id: str):
        self.value = message_id


class StreamConsumer:
    def __init__(self, redis: MockRedis, checkpoints: CheckpointStore):
        self.redis = redis
        self.checkpoints = checkpoints

    async def consume_stream(self, batch_size: int = 2) -> AsyncIterator[tuple[str, TaskEvent]]:
        current_id = await self.checkpoints.load()

        while True:
            batch = await self.redis.read_batch(last_id=current_id, count=batch_size)
            if not batch:
                break

            for msg_id, data in batch:
                try:
                    event = TaskEvent.model_validate(data)
                    yield (msg_id, event)
                except ValidationError as exc:
                    print(f"[warning] invalid payload at {msg_id}: {exc.errors()[0]['msg']}")
                finally:
                    # This is the critical guarantee: always advance pointer.
                    current_id = msg_id
                    await self.checkpoints.save(current_id)


async def phase_with_crash():
    redis = MockRedis()
    checkpoints = CheckpointStore()
    consumer = StreamConsumer(redis, checkpoints)

    print("Phase 1 (crash after A2)")
    async for msg_id, event in consumer.consume_stream():
        print(f"  processed: {msg_id} -> {event.task_id}/{event.status}")
        if event.task_id == "A2":
            print("  [simulated crash]")
            break

    print(f"Checkpoint after crash: {await checkpoints.load()}")

    print("Phase 2 (reboot and continue)")
    consumer2 = StreamConsumer(redis, checkpoints)
    async for msg_id, event in consumer2.consume_stream():
        print(f"  processed: {msg_id} -> {event.task_id}/{event.status}")

    print(f"Final checkpoint: {await checkpoints.load()}")


if __name__ == "__main__":
    asyncio.run(phase_with_crash())
```

## Why this matches real Agentex patterns

1. Per-message schema validation with local handling mirrors `streams_use_case.read_messages(...)`.
2. Cursor progression after each message mirrors `stream_task_events(...)` `last_id` update flow.
3. Poison-pill skip with pointer advance prevents infinite re-read loops.

