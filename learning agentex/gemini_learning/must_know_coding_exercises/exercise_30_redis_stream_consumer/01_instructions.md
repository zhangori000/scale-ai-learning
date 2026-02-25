# Exercise 30: Redis Stream Consumer Pointer Management

In distributed systems, reading from a queue isn't enough. You have to ensure that if your service crashes **while** processing a message, that message isn't lost forever.

In Agentex, the `StreamsUseCase` reads from Redis Streams using a `last_id` pointer. 

## The Challenge

You need to write a consumer loop that reads from a stream in batches. 
The critical rule is: **Only update `last_id` AFTER the message has been successfully processed/yielded.** If you update the pointer *before* processing, and a crash occurs, that message is skipped on the next reboot.

Furthermore, Agentex uses `Pydantic` to validate incoming data. Sometimes, bad data gets into the stream. Your consumer must catch `ValidationError`, skip the bad message, but **still update the pointer**, otherwise the consumer will get stuck infinitely trying to read the bad message.

## Starter Code

```python
import asyncio
from typing import AsyncIterator
from pydantic import BaseModel, ValidationError

# --- Domain Model ---
class TaskEvent(BaseModel):
    task_id: str
    status: str

# --- Simulated Infrastructure ---
class MockRedis:
    def __init__(self):
        # Format: (message_id, data_dict)
        self.stream = [
            ("1000-0", {"task_id": "A1", "status": "running"}),
            ("1001-0", {"task_id": "A2", "status": "completed"}),
            ("1002-0", {"BAD_DATA": "missing_fields"}), # This will fail validation!
            ("1003-0", {"task_id": "A3", "status": "failed"}),
        ]

    async def read_batch(self, last_id: str, count: int = 2) -> list[tuple[str, dict]]:
        """Simulates XREAD from Redis."""
        results = []
        for msg_id, data in self.stream:
            if last_id == "0" or msg_id > last_id:
                results.append((msg_id, data))
                if len(results) == count:
                    break
        return results

# --- Your Task ---

class StreamConsumer:
    def __init__(self, redis: MockRedis):
        self.redis = redis

    async def consume_stream(self, starting_id: str = "0") -> AsyncIterator[tuple[str, TaskEvent]]:
        """
        TODO: Implement the robust consumer loop.
        
        Requirements:
        1. Maintain a `current_id` pointer (starts at `starting_id`).
        2. Loop infinitely (or until stream is empty for this simulation).
        3. Read a batch of messages using `self.redis.read_batch(current_id)`.
        4. For each message:
            a. Try to validate it into a `TaskEvent` using `TaskEvent.model_validate(data)`.
            b. If it fails, log a warning, BUT STILL UPDATE `current_id` so we don't get stuck.
            c. If successful, yield `(msg_id, TaskEvent)`.
            d. ONLY update `current_id` AFTER yielding or skipping.
        5. If `read_batch` returns empty, break the loop (for this simulation).
        """
        pass

# --- Execution Simulation ---
async def main():
    redis = MockRedis()
    consumer = StreamConsumer(redis)
    
    print("--- Starting Consumer ---")
    
    # Simulate a consumer crashing after processing 'A2', and restarting from '1001-0'
    print("Phase 1: Reading from start...")
    async for msg_id, event in consumer.consume_stream(starting_id="0"):
        print(f"Processed: {msg_id} -> {event.task_id} ({event.status})")
        # In reality, this is where we yield to the UI or trigger a Workflow.
        
        # We will stop the simulation early to show why updating the pointer matters.

if __name__ == "__main__":
    asyncio.run(main())
```