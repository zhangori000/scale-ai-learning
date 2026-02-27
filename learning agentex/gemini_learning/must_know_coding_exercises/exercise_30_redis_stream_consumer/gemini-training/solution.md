# Exercise 30: Advanced Redis Stream Consumer Solution

This solution mirrors the architecture of `scale-agentex/agentex/src/domain/use_cases/streams_use_case.py`.

## Key Architectural Decisions
- **Nested `try...except`**: Separates **Fatal Errors** (User closed tab) from **Transient Errors** (Redis blip) and **Data Errors** (Pydantic validation).
- **Pointer Integrity**: `current_id` is updated **after each message**, even if it fails validation, to ensure the consumer never gets stuck.
- **Backoff Recovery**: If a batch read fails, the consumer waits 1 second and retries with the **exact same `current_id`**.

```python
import asyncio
import json
from typing import AsyncIterator, Optional, Dict, Any
from pydantic import BaseModel, ValidationError

# --- Models ---

class TaskEvent(BaseModel):
    task_id: str
    status: str

# --- Advanced Consumer Implementation ---

class AdvancedStreamConsumer:
    def __init__(self, redis):
        self.redis = redis

    async def consume(self, starting_id: str = "0") -> AsyncIterator[tuple[str, TaskEvent]]:
        # 1. Initialize the pointer (the "Cursor")
        current_id = starting_id
        
        # 2. Outer loop: The "Life of the Connection"
        while True:
            try:
                # 3. Inner loop catch for batch processing errors (Transient Errors)
                batch = await self.redis.read_batch(current_id)
                
                # Simulation exit: In reality, we would wait/heartbeat
                if not batch:
                    break

                for msg_id, raw_data in batch:
                    try:
                        # 4. Pydantic Validation Pattern
                        # This happens inside the loop to avoid "killing the batch" on one bad message.
                        event = TaskEvent.model_validate(raw_data)
                        
                        # 5. Yield to the Caller (e.g., the Web Server)
                        yield (msg_id, event)
                        
                    except ValidationError as ve:
                        # 6. Skip Bad Data: Still log it, but move to the next ID
                        print(f"[Consumer] Warning: Skipping malformed message {msg_id}: {ve}")
                    
                    finally:
                        # 7. Pointer Update (Crucial)
                        # We MUST update current_id even if validation failed!
                        # This ensures the next batch read() starts after this message.
                        current_id = msg_id
                        
                # Batch throttle (optional, but good practice)
                await asyncio.sleep(0.02)

            except RuntimeError as re:
                # 8. Transient Error: Redis blip
                # We catch the error, wait 1 second, and STAY in the while True loop.
                # The next call to read_batch() will use the same 'current_id'.
                print(f"[Consumer] Error: Transient failure: {re}. Retrying in 1s...")
                await asyncio.sleep(1)
                continue
            
            except asyncio.CancelledError:
                # 9. Lifecycle Event: User closed the connection
                # We stop the while True loop and trigger cleanup.
                print(f"[Consumer] Client disconnected. Shutting down...")
                raise # Re-raise to trigger outer cleanup if needed

# --- Summary of Concepts ---

"""
Why this matches production:
1.  try...finally around current_id: Ensures the pointer is ALWAYS updated after a message is seen.
2.  Inner/Outer Try Split: Distinguishes between "Bad Data" (skip) and "Bad Network" (retry).
3.  Resumability: Because current_id is updated per-message, a crash between messages 
    in a batch only repeats the processing for the LAST message (at most).
"""
```
