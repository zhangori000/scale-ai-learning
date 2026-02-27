# Exercise 29: Advanced SSE Streamer Solution (Level 3)

This implementation is a one-to-one architectural match for `scale-agentex/agentex/src/domain/use_cases/streams_use_case.py`.

```python
import asyncio
import json
from typing import AsyncIterator, Optional, Annotated

# --- Entity Transformation simulation ---

def convert_to_entity(data: dict):
    # This simulates the TaskStreamEvent model_validate pattern
    if "type" not in data or "content" not in data:
        raise ValueError("Invalid Event Schema")
    return {"type": data["type"], "content": data["content"]}

# --- Use Case Implementation ---

class AdvancedStreamsUseCase:
    def __init__(self, stream_repository, task_service, env_vars):
        """
        The Dependency Injection pattern used in FastAPI and Agentex.
        """
        self.stream_repository = stream_repository
        self.task_service = task_service
        self.env_vars = env_vars

    async def read_messages(self, topic: str, last_id: str = "$", timeout_ms: int = 2000, count: int = 10) -> AsyncIterator[tuple[str, dict]]:
        """
        An internal method that wraps the Repository's generator.
        This layer is where 'Entity Transformation' and 'Pydantic Validation' usually happen.
        """
        # Pass through from the repository
        async for message_id, raw_data in self.stream_repository.read_messages(
            topic=topic, last_id=last_id, timeout_ms=timeout_ms, count=count
        ):
            try:
                # 1. Entity Conversion (Pydantic simulation)
                entity = convert_to_entity(raw_data)
                yield (message_id, entity)
            except ValueError as e:
                print(f"[UseCase] Skipping bad message {message_id}: {e}")

    async def cleanup_stream(self, topic: str):
        """
        Internal cleanup that can trigger logging, metrics, or side-effects.
        """
        print(f"[UseCase] Starting cleanup for topic {topic}")
        try:
            await self.stream_repository.cleanup_stream(topic)
        except Exception as e:
            print(f"[UseCase] Critical Error during cleanup: {e}")

    async def stream_task_events(self, task_id: str | None = None, task_name: str | None = None) -> AsyncIterator[str]:
        # 2. Resolve task_id if needed (Entity Resolution Pattern)
        if not task_id:
            if not task_name:
                raise ValueError("Must provide task_id or task_name")
            task = await self.task_service.get_task(name=task_name)
            task_id = task.id

        stream_topic = f"task:{task_id}:events"
        last_id = "$"
        last_message_time = asyncio.get_running_loop().time()
        ping_interval = float(self.env_vars.SSE_KEEPALIVE_PING_INTERVAL)

        # 3. Protocol Framing: Initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'taskId': task_id})}\n\n"

        try:
            while True:
                try:
                    # 4. Pull from the internal read_messages generator
                    message_gen = self.read_messages(topic=stream_topic, last_id=last_id)
                    message_count = 0

                    async for msg_id, data in message_gen:
                        # 5. Update Cursor and State
                        last_id = msg_id
                        message_count += 1
                        
                        # 6. Format as SSE data string
                        yield f"data: {json.dumps(data)}\n\n"
                        last_message_time = asyncio.get_running_loop().time()
                        
                        # Batch throttle
                        await asyncio.sleep(0.02)

                    # 7. Heartbeat/Keepalive logic
                    if message_count == 0:
                        current_time = asyncio.get_running_loop().time()
                        if current_time - last_message_time >= ping_interval:
                            yield ":ping\n\n"
                            last_message_time = current_time
                        
                        # Idle throttle (prevent tight loop)
                        await asyncio.sleep(0.1)
                    else:
                        # Small pause between batches
                        await asyncio.sleep(0.02)

                except asyncio.CancelledError:
                    # 8. User disconnected while waiting (Inner loop catch)
                    print(f"[UseCase] Client disconnected from {task_id}")
                    raise # Propagate to outer try
                except Exception as e:
                    # 9. Transient Error Handling: Yield error JSON, then retry
                    print(f"[UseCase] Transient error: {e}")
                    error_json = json.dumps({"type": "error", "message": str(e)})
                    yield f"data: {error_json}\n\n"
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            # 10. Outer loop shutdown
            pass
        finally:
            # 11. Final Cleanup Pattern
            await self.cleanup_stream(stream_topic)
            print(f"[UseCase] SSE stream for {task_id} has ended")

# --- Concept Summary ---

"""
Why this matches production:
1.  __init__: Uses Dependency Injection for Repositories and Services.
2.  Resolution: The logic for task_id/task_name mapping matches the real Use Case.
3.  Nested Generators: read_messages() delegates to the repo and transforms data.
4.  Cursor State: last_id = "$" ensures we only get new messages after a reconnect.
5.  Double Exception Handling: Captures both transient loop errors and fatal cancellations.
"""
```
