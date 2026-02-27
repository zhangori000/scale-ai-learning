# Exercise 29: Production-Grade SSE Use Case (Level 3)

## Why this exercise exists
This is the final step before you can comfortably read and modify `scale-agentex/agentex/src/domain/use_cases/streams_use_case.py`. It incorporates:
1.  **Dependency Injection**: Using the `__init__` pattern seen in the real repo.
2.  **Entity Resolution**: Finding a `task_id` by its `task_name` if the ID isn't provided.
3.  **Class-Internal Method Delegation**: Moving the logic for reading and cleanup into the Use Case itself.
4.  **Annotated Types**: Mirroring the FastAPI dependency injection style.

## The Challenge

You must implement the `AdvancedStreamsUseCase` class with the exact signatures used in the production codebase.

### Requirements
1.  **Init with 3 Dependencies**: `stream_repository`, `task_service`, and `env_vars`.
2.  **Task Resolution**: In `stream_task_events`, if `task_id` is None but `task_name` is provided, call `self.task_service.get_task(name=task_name)` to get the ID.
3.  **Internal `read_messages`**: Implement a method that wraps the repository's generator and performs schema validation/conversion.
4.  **Internal `cleanup_stream`**: Implement a method that logs the cleanup and calls the repository.
5.  **Main Generator**: The `stream_task_events` method must orchestrate everything: resolution, initial event, the "Infinite Loop" with cursor tracking, and final cleanup.

## Starter Code

```python
import asyncio
import json
from typing import AsyncIterator, Optional, Annotated

# --- Mocking the Production Environment ---

class MockTask:
    def __init__(self, task_id, name):
        self.id = task_id
        self.name = name

class MockTaskService:
    async def get_task(self, name: str):
        print(f"[Service] Resolving task name: {name}")
        return MockTask("task-999", name)

class MockEnvVars:
    SSE_KEEPALIVE_PING_INTERVAL = 2.0

class MockRepo:
    async def read_messages(self, topic, last_id, timeout_ms, count):
        # Simulate Redis yielding (ID, Data)
        yield "msg-1", {"type": "update", "content": "Initializing..."}
        await asyncio.sleep(0.1)
        yield "msg-2", {"type": "update", "content": "Processing..."}

    async def cleanup_stream(self, topic):
        print(f"[Repo] Cleaned up: {topic}")

# --- Your Task: The Advanced Use Case ---

class AdvancedStreamsUseCase:
    def __init__(self, stream_repository: MockRepo, task_service: MockTaskService, env_vars: MockEnvVars):
        self.stream_repository = stream_repository
        self.task_service = task_service
        self.env_vars = env_vars

    async def read_messages(self, topic: str, last_id: str = "$") -> AsyncIterator[tuple[str, dict]]:
        """TODO: Wrap repo.read_messages and yield (id, data)"""
        pass

    async def cleanup_stream(self, topic: str):
        """TODO: Log and call repo.cleanup_stream"""
        pass

    async def stream_task_events(self, task_id: str = None, task_name: str = None) -> AsyncIterator[str]:
        """
        TODO: The Master Orchestrator
        1. Resolve task_id if needed.
        2. Yield 'connected' event.
        3. Start while True loop with last_id="$".
        4. Use self.read_messages(topic, last_id).
        5. Handle heartbeats, errors, and client disconnects.
        6. ALWAYS cleanup in finally.
        """
        pass

# --- Execution ---
async def simulate():
    use_case = AdvancedStreamsUseCase(MockRepo(), MockTaskService(), MockEnvVars())
    # Test resolution by name
    async for sse in use_case.stream_task_events(task_name="my-special-task"):
        print(f"OUT: {sse.strip()}")

if __name__ == "__main__":
    asyncio.run(simulate())
```
