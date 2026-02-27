# Codex Comments Exercise 30: Crash-Safe Redis Stream Pointer

This is a stricter version of Exercise 30 with explicit restart behavior.

## Goal

Implement a stream consumer that:

1. validates each payload with Pydantic,
2. yields only valid events,
3. advances checkpoint for both valid and invalid messages,
4. resumes correctly after a simulated crash.

## Starter Code

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
        """
        TODO:
        1. Start from checkpoint store.
        2. Read batches until empty.
        3. For each message:
           - Try TaskEvent.model_validate(data).
           - If valid: yield (msg_id, event).
           - If invalid: log warning and skip yield.
           - In BOTH cases, always update checkpoint to msg_id.
        4. Ensure pointer advancement is in finally-equivalent logic.
        """
        pass


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

## Expected Behavior

1. Phase 1 processes A1 and A2, then "crashes".
2. Phase 2 resumes from `1001-0`, encounters poison message `1002-0`, logs warning, advances pointer.
3. Phase 2 still processes A3.
4. Final checkpoint is `1003-0`.

