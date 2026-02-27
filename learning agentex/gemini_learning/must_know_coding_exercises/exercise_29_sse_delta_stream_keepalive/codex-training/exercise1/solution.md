# Codex Training - Exercise 1 Solution

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
        try:
            # First SSE chunk: connection established.
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"

            # Drain currently available messages from repo.
            async for message in self.repo.read_messages(last_id="$"):
                yield f"data: {json.dumps(message)}\n\n"
        finally:
            # Even in later versions with errors/cancel, cleanup must always run.
            await self.repo.cleanup_stream(topic)


async def demo():
    repo = MockStreamRepo()
    use_case = StreamsUseCase(repo)
    async for chunk in use_case.stream_task_events("task-1"):
        print(chunk.strip())


if __name__ == "__main__":
    asyncio.run(demo())
```

This step isolates the two most important fundamentals from the full Agentex pattern:
1. SSE framing (`data: ...\n\n`)
2. Cleanup guarantee (`finally`)

The next step can add the polling loop and keepalive pings.

