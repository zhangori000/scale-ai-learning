# Codex Training - Exercise 1: SSE Envelope Basics

This is the first small step toward understanding the `stream_task_events` pattern used in `streams_use_case.py`.

For this exercise, ignore keepalive pings and disconnect handling. We only want the core SSE shape.

## Goal

Implement `stream_task_events` so it:
1. Yields a `connected` event first.
2. Reads all available messages from `repo.read_messages("$")`.
3. Yields each message in SSE format: `data: <json>\n\n`.
4. Always calls `repo.cleanup_stream(topic)` before returning.

## Starter Code

```python
import asyncio
import json
from typing import AsyncIterator


class MockStreamRepo:
    def __init__(self):
        self.messages = [
            {"type": "update", "content": "Thinking..."},
            {"type": "update", "content": "Searching..."},
            {"type": "complete", "content": "Done!"},
        ]

    async def read_messages(self, last_id: str) -> AsyncIterator[dict]:
        while self.messages:
            yield self.messages.pop(0)

    async def cleanup_stream(self, topic: str):
        print(f"[Repo] cleanup called for: {topic}")


class StreamsUseCase:
    def __init__(self, repo: MockStreamRepo):
        self.repo = repo

    async def stream_task_events(self, topic: str) -> AsyncIterator[str]:
        """
        TODO:
        - Yield connected event first.
        - Drain repo messages and yield each as SSE data.
        - Ensure cleanup_stream(topic) is always called.
        """
        pass


async def demo():
    repo = MockStreamRepo()
    use_case = StreamsUseCase(repo)
    async for chunk in use_case.stream_task_events("task-1"):
        print(chunk.strip())


if __name__ == "__main__":
    asyncio.run(demo())
```

## Expected Output Shape

Order matters:
1. `data: {"type": "connected"}`
2. `data: {"type": "update", "content": "Thinking..."}`
3. `data: {"type": "update", "content": "Searching..."}`
4. `data: {"type": "complete", "content": "Done!"}`
5. Cleanup log from repo

