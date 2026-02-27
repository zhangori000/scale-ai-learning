# Documentation: Redis Stream Consumer & Pointer Management

In `scale-agentex`, the flow of events from an Agent to a User's browser relies on a robust consumption pattern. This document explains where the `StreamsUseCase` is used and how the "Pointer Management" (last_id) works in the real world.

## 1. Where is `StreamsUseCase` used?

The `StreamsUseCase` is the bridge between the **Redis Storage** and the **HTTP API**.

### API Routes
In `scale-agentex/agentex/src/api/routes/tasks.py`, the `StreamsUseCase` is injected into the streaming endpoints:

```python
@router.get("/{task_id}/stream")
async def stream_task_events(
    task_id: DAuthorizedId(...),
    stream_use_case: DStreamsUseCase, # <-- Injection
) -> StreamingResponse:
    return StreamingResponse(
        stream_use_case.stream_task_events(task_id=task_id),
        media_type="text/event-stream",
        # ... SSE Headers ...
    )
```

### Integration Tests
In `scale-agentex/agentex/tests/integration/test_task_stream.py`, the use case is heavily tested to ensure that:
1. It can resolve task names to IDs.
2. It correctly handles empty streams (yielding heartbeats).
3. It resumes from the correct `last_id` if a connection is dropped and re-established.

## 2. The Pointer Management Pattern

The core challenge of consuming a stream is **Resumability**. If a consumer crashes, it must know exactly where to start reading again.

### The `last_id` Workflow
1. **Initial State**: Usually `last_id = "$"`. This tells Redis: "I only want messages that arrive *from now on*."
2. **Reading**: The `RedisStreamRepository.read_messages` calls `xread(streams={topic: last_id}, count=10)`.
3. **Updating**: As messages are yielded by the repository, the `StreamsUseCase` updates its local `last_id` variable.
4. **Resumption**: If the `while True` loop in `StreamsUseCase` restarts (e.g., due to a transient Redis error), it uses the **latest** `last_id` it has seen, ensuring no messages are missed or duplicated.

## 3. The "Stuck Consumer" Problem
One common bug in stream consumers is getting "stuck" on a malformed message.
- If a message in the stream is corrupted (e.g., invalid JSON), and the consumer crashes before updating the pointer, it will restart and try to read that **same bad message** again.
- **The Solution**: In `StreamsUseCase.read_messages`, there is a `try/except` block *inside* the loop. If a message fails validation, it is logged and **skipped**, allowing the loop to move to the next message and update the pointer successfully.

## 4. Usage Example (The "Bonafide" Way)

If you were to use the `StreamsUseCase` manually (like in a CLI tool or a background worker), it would look like this:

```python
async def run_worker():
    # 1. Setup Dependencies
    repo = RedisStreamRepository(...)
    task_service = AgentTaskService(...)
    use_case = StreamsUseCase(repo, task_service, ...)

    # 2. Consume the stream
    async for sse_event in use_case.stream_task_events(task_id="task_123"):
        # The 'sse_event' is a string formatted as "data: {JSON}

"
        print(f"Received update: {sse_event}")
```
