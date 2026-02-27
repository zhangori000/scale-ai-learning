# Documentation: Decoding the Agentex Streaming Pattern

This document breaks down the specific patterns used in `exercise_29` and `scale-agentex/agentex/src/domain/use_cases/streams_use_case.py`.

## 1. Dependency Injection (`__init__`)
In `scale-agentex`, we follow the **Repository/Service Pattern**. 
- **The Use Case** (`StreamsUseCase`) does not talk to Redis or the Database directly.
- **The Repository** (`DRedisStreamRepository`) handles the "Plumbing" (Redis commands).
- **The Task Service** (`DAgentTaskService`) handles high-level "Task" operations (like finding an ID by name).

**Why?** This makes the code **testable**. We can swap out the "Real" Redis Repository for a "Mock" Repository during unit tests without changing the Use Case logic.

## 2. Entity Resolution Pattern
In the `stream_task_events` method:
```python
if not task_id:
    task = await self.task_service.get_task(name=task_name)
    task_id = task.id
```
This is common in AI systems where a user might know the "Human-readable Name" of an agent but not its "Internal UUID." The Use Case is responsible for resolving these "Entities" before starting the stream.

## 3. Nested Generators (`read_messages`)
You'll notice `read_messages` is a method that calls *another* generator in the repository. This is where **Validation** lives:
- **Repository**: Returns raw dictionaries from Redis.
- **Use Case**: Uses Pydantic to ensure the dictionary is valid. If it's not, the Use Case catches the `ValidationError`, logs it, and continues to the next message. 
- **The Golden Rule**: One bad message in the database should NEVER kill the user's entire stream.

## 4. Cursor Management (`last_id`)
When the server reads from a Redis Stream, it needs a **Cursor** to know where it left off.
- `last_id = "$"`: Means "only give me messages that arrive *after* this exact moment."
- `last_id = "0"`: Means "give me everything from the beginning of time."
- `last_id = new_id`: Every time we successfully yield a message, we update the cursor. If the inner loop crashes and restarts, we resume exactly where we left off.

## 5. Double Exception Handling
You'll see a `try` block inside the `while True` loop, and another `try` block wrapping the *entire* method.
- **Inner Try**: Handles "Transient Errors" (e.g., a brief network blip to Redis). We log it, yield an error event to the user, and **stay in the loop** to try again.
- **Outer Try**: Handles "Fatal Events" (e.g., the user closes the tab). This raises a `CancelledError`, which breaks the `while True` loop and triggers the `finally` block.

## 6. Heartbeat Tuning
Load balancers (like AWS or Nginx) are "impatient." If they don't see any data for a set time (the "Idle Timeout"), they close the connection. 
- **The Ping**: Yielding `:ping

` sends valid SSE bytes that the browser ignores but the load balancer sees as "activity," keeping the line open.
- **Tuning**: In `scale-agentex`, this interval is configurable via `env_vars.SSE_KEEPALIVE_PING_INTERVAL`.

## 7. Performance: The "Throttle"
- **`await asyncio.sleep(0.02)`**: Used after a successful message batch to let the event loop process other users.
- **`await asyncio.sleep(0.1)`**: Used when the stream is empty to prevent a "Tight Loop" that would peg the CPU at 100%.
- **`await asyncio.sleep(1)`**: Used after an error to prevent "Spamming" the logs or the user with constant retry attempts.
