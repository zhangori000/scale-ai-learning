# Exercise 30: Advanced Redis Stream Consumer (Level 2)

## Why this exercise exists
This exercise moves beyond simple batch reading and focuses on **Resilience** and **Recovery** in a streaming system. In the real `scale-agentex` codebase, the `StreamsUseCase` doesn't just read messages; it must handle:
1.  **Cursor Tracking (`last_id`)**: Ensuring the pointer is always updated, even when individual messages fail validation.
2.  **Transient Error Recovery**: If the `read_batch` itself fails (e.g., a Redis blip), the consumer must wait and retry from the **exact same `last_id`**.
3.  **Batch Yielding**: Correctly yielding each message in a batch while maintaining the "Pointer Integrity" for the next batch.

## The Challenge

You will implement the `AdvancedStreamConsumer` class to mimic the "Inner Processing Loop" of `StreamsUseCase`.

### Requirements
1.  **The Pointer**: Maintain `current_id`. Initialize it to `starting_id`.
2.  **The Infinite Loop**: Use `while True` to consume messages.
3.  **The Batch Processor**:
    - Call `self.redis.read_batch(current_id)`.
    - If successful, loop over each `(msg_id, raw_data)` in the batch.
    - **Crucial**: Use a `try/except ValidationError` inside the batch loop to skip bad messages but **still update `current_id`**.
4.  **Error Backoff**: If the entire `read_batch` call fails (simulated by a `RuntimeError`), catch it, wait 1 second, and **stay in the loop** to retry with the same `current_id`.
5.  **Logging**: Print a warning for malformed messages and an error for batch failures.

## Starter Code

```python
import asyncio
import json
from typing import AsyncIterator, Optional
from pydantic import BaseModel, ValidationError

# --- Domain Model ---
class TaskEvent(BaseModel):
    task_id: str
    status: str

# --- Simulated Infrastructure ---
class MockRedis:
    def __init__(self):
        self.stream = [
            ("1000-0", {"task_id": "A1", "status": "running"}),
            ("1001-0", {"BAD_DATA": "missing_fields"}), # Malformed!
            ("1002-0", {"task_id": "A2", "status": "completed"}),
            ("1003-0", {"task_id": "A3", "status": "failed"}),
        ]
        self.fail_next_batch = False # For simulating Redis blips

    async def read_batch(self, last_id: str, count: int = 2) -> list[tuple[str, dict]]:
        """Simulates XREAD from Redis."""
        if self.fail_next_batch:
            self.fail_next_batch = False
            raise RuntimeError("Redis connection blip!")
            
        results = []
        for msg_id, data in self.stream:
            if last_id == "0" or msg_id > last_id:
                results.append((msg_id, data))
                if len(results) == count:
                    break
        return results

# --- Your Task: Advanced Consumer ---

class AdvancedStreamConsumer:
    def __init__(self, redis: MockRedis):
        self.redis = redis

    async def consume(self, starting_id: str = "0") -> AsyncIterator[tuple[str, TaskEvent]]:
        """
        TODO: Implement the Advanced Consumer.
        
        Logic:
        1. Initialize current_id = starting_id.
        2. outer while True:
           3. inner try...except RuntimeError (The 'Blip' catch):
              - batch = await self.redis.read_batch(current_id)
              - if not batch: break loop (for simulation only)
              - for msg_id, raw_data in batch:
                - inner-inner try...except ValidationError (The 'Bad Message' catch):
                  - event = TaskEvent.model_validate(raw_data)
                  - yield (msg_id, event)
                - always: update current_id = msg_id
           4. except RuntimeError:
              - print error, await asyncio.sleep(1), and continue.
        """
        pass

# --- Execution ---
async def main():
    redis = MockRedis()
    consumer = AdvancedStreamConsumer(redis)
    
    # 1. First 2 messages (one is bad)
    print("--- Batch 1 (A1 and Malformed) ---")
    async for msg_id, event in consumer.consume(starting_id="0"):
        print(f"Consumed: {msg_id} -> {event}")
        if msg_id == "1001-0": break # Stop for simulation

    # 2. Simulate a Redis blip before next batch
    print("
--- Simulating Redis Blip ---")
    redis.fail_next_batch = True
    
    # 3. Resume from where we left off (1001-0)
    print("
--- Batch 2 (A2 and A3 after recovery) ---")
    async for msg_id, event in consumer.consume(starting_id="1001-0"):
         print(f"Consumed: {msg_id} -> {event}")

if __name__ == "__main__":
    asyncio.run(main())
```
