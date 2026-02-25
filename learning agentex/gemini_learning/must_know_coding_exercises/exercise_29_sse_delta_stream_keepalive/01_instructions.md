# Exercise 29: Server-Sent Events (SSE) Delta Streamer

In `scale-agentex`, when an Agent is processing a long task, the UI doesn't want to wait 5 minutes for a single response. Instead, Agentex streams "deltas" (partial updates) using Server-Sent Events (SSE).

If you look at `agentex/src/domain/use_cases/streams_use_case.py`, you'll see a complex `async def stream_task_events()` generator.

## The Challenge

SSE connections are fragile. If no data is sent for a while, load balancers might drop the connection. Furthermore, clients can disconnect at any time, and the server must clean up resources.

You need to build a robust `stream_task_events` generator that:
1.  Yields an initial `"connected"` event.
2.  Continuously polls a simulated `read_messages` generator.
3.  If a message is found, yield it formatted as `data: {"some": "json"}

`.
4.  **Keepalive**: If no messages are found for `ping_interval` seconds, yield a `:ping

` string to keep the connection alive.
5.  **Graceful Disconnect**: If the client disconnects (simulated by `asyncio.CancelledError`), catch it, log it, and ensure `cleanup_stream` is called in a `finally` block.

## Starter Code

```python
import asyncio
import json
from typing import AsyncIterator

# --- Simulated Infrastructure ---

class MockStreamRepo:
    def __init__(self):
        self.messages = [
            (0.5, {"type": "update", "content": "Thinking..."}),
            (1.0, {"type": "update", "content": "Searching DB..."}),
            # Huge gap here to force a keepalive ping!
            (4.0, {"type": "complete", "content": "Done!"})
        ]
        self.start_time = None

    async def read_messages(self, last_id: str) -> AsyncIterator[dict]:
        """Simulates reading from Redis. Yields one message if available, or nothing."""
        if self.start_time is None:
            self.start_time = asyncio.get_event_loop().time()
            
        current_time = asyncio.get_event_loop().time() - self.start_time
        
        # Find messages that should have arrived by now
        available = [m for m in self.messages if m[0] <= current_time]
        for m in available:
            self.messages.remove(m) # Remove from queue
            yield m[1]

    async def cleanup_stream(self, topic: str):
        print(f"[Repo] Cleaned up stream: {topic}")

# --- Your Task ---

class StreamsUseCase:
    def __init__(self, repo: MockStreamRepo, ping_interval: float = 2.0):
        self.repo = repo
        self.ping_interval = ping_interval

    async def stream_task_events(self, topic: str) -> AsyncIterator[str]:
        """
        TODO: Implement the SSE Streamer!
        
        Requirements:
        1. Yield `data: {"type": "connected"}

` immediately.
        2. Enter a loop:
           - Try to read messages from `self.repo.read_messages("$")`
           - If you get a message, yield `data: <json>

` and reset the ping timer.
           - If no message, and `ping_interval` has passed since last yield, yield `:ping

`.
           - sleep(0.1) to prevent CPU hogging.
        3. Handle `asyncio.CancelledError` gracefully.
        4. ALWAYS call `self.repo.cleanup_stream(topic)` when exiting.
        """
        pass

# --- Execution Simulation ---
async def simulate_client():
    repo = MockStreamRepo()
    use_case = StreamsUseCase(repo, ping_interval=1.5)
    
    print("--- Client Connecting ---")
    try:
        # Simulate a client consuming the stream for 5 seconds
        async with asyncio.timeout(5.0):
            async for sse_string in use_case.stream_task_events("task-123"):
                print(f"Client received: {sse_string.strip()}")
    except TimeoutError:
        print("--- Client Disconnected (Timeout) ---")

if __name__ == "__main__":
    asyncio.run(simulate_client())
```