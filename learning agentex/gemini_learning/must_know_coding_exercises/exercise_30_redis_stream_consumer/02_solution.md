# Solution: Redis Stream Consumer Pointer Management

This exercise shows why the `StreamsUseCase` in Agentex separates reading from yielding, and why `try/except ValidationError` is placed *inside* the processing loop, not outside.

If a `ValidationError` crashes the whole generator, you never update the `last_id` pointer. When the consumer reboots, it reads the *exact same bad message* and crashes again. This is called a "Poison Pill" message.

## The Solution Code

```python
import asyncio
from typing import AsyncIterator
from pydantic import BaseModel, ValidationError

# ... (Domain Model and MockRedis omitted) ...

class StreamConsumer:
    def __init__(self, redis: MockRedis):
        self.redis = redis

    async def consume_stream(self, starting_id: str = "0") -> AsyncIterator[tuple[str, TaskEvent]]:
        current_id = starting_id
        
        while True:
            # 1. Read a batch. (In Redis, XREAD block=timeout)
            batch = await self.redis.read_batch(current_id, count=2)
            
            # 2. Break if stream is empty (for this mock simulation)
            if not batch:
                break
                
            for msg_id, data in batch:
                try:
                    # 3. Attempt Validation (Pydantic magic)
                    event = TaskEvent.model_validate(data)
                    
                    # 4. Success! Yield the data.
                    # The caller (like the SSE streamer) might take time processing this.
                    yield (msg_id, event)
                    
                except ValidationError as e:
                    # 5. POISON PILL CAUGHT!
                    # A bad message (like missing task_id) was found in Redis.
                    print(f"[Warning] Failed to validate stream event {msg_id}: {e}")
                    # We DO NOT raise the error. We just skip yielding it.
                    
                finally:
                    # 6. CRITICAL: The Pointer Update.
                    # Whether the message was valid or poison, we MUST move the pointer forward.
                    # If we crash on the *next* message, we don't want to re-read this one.
                    current_id = msg_id

# --- Execution Simulation ---
async def main():
    redis = MockRedis()
    consumer = StreamConsumer(redis)
    
    print("--- Phase 1: Reading from start ---")
    # Simulate a crash after 2 messages
    async for msg_id, event in consumer.consume_stream(starting_id="0"):
        print(f"Processed: {msg_id} -> {event.task_id} ({event.status})")
        if event.task_id == "A2":
            print("[Simulated Server Crash!]")
            break
            
    print("
--- Phase 2: Rebooting and Resuming ---")
    # In reality, '1001-0' would be read from a database or Redis Hash
    async for msg_id, event in consumer.consume_stream(starting_id="1001-0"):
        print(f"Processed: {msg_id} -> {event.task_id} ({event.status})")

if __name__ == "__main__":
    asyncio.run(main())
```

## Output Analysis
When you run this code, `A1` and `A2` process. The server "crashes".
On reboot, it resumes from `1001-0`. The next message in the queue is the **Poison Pill** (`1002-0`).
Because of the `try/except` inside the loop, it prints a warning, updates the pointer, and successfully moves on to process `A3`. 

If the `try/except` was missing, Phase 2 would crash immediately, and `A3` would never be processed.