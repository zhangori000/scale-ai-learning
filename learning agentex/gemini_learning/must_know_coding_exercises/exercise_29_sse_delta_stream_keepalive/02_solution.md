# Solution: Server-Sent Events (SSE) Delta Streamer

This pattern is ripped straight from `agentex/src/domain/use_cases/streams_use_case.py`. 

It demonstrates how Agentex balances providing real-time UI updates while managing the harsh realities of network programming (dropped connections, silent timeouts).

## The Solution Code

```python
import asyncio
import json
from typing import AsyncIterator

# ... (MockStreamRepo omitted for brevity) ...

class StreamsUseCase:
    def __init__(self, repo: MockStreamRepo, ping_interval: float = 2.0):
        self.repo = repo
        self.ping_interval = ping_interval

    async def stream_task_events(self, topic: str) -> AsyncIterator[str]:
        # 1. Initial Connection Data
        yield f"data: {json.dumps({'type': 'connected'})}

"
        
        last_message_time = asyncio.get_event_loop().time()
        
        try:
            # 2. The Infinite Control Loop
            while True:
                try:
                    message_count = 0
                    
                    # 3. Drain the queue (Simulating Redis read)
                    async for data in self.repo.read_messages(last_id="$"):
                        message_count += 1
                        
                        # Format as SSE Data
                        yield f"data: {json.dumps(data)}

"
                        
                        # Reset the keepalive timer!
                        last_message_time = asyncio.get_event_loop().time()
                        
                        # Yield to the event loop between messages
                        await asyncio.sleep(0.01) 

                    # 4. Keepalive Logic
                    if message_count == 0:
                        current_time = asyncio.get_event_loop().time()
                        
                        # Has it been too long since we sent bytes to the client?
                        if current_time - last_message_time >= self.ping_interval:
                            yield ":ping

"
                            last_message_time = current_time
                        
                        # Prevent the while loop from pegging the CPU at 100%
                        await asyncio.sleep(0.1)

                except asyncio.CancelledError:
                    # 5. Client Disconnected!
                    print(f"[Server] Client disconnected from SSE stream: {topic}")
                    raise # Re-raise to break the generator
                    
                except Exception as e:
                    # Catching random Redis/Network errors and telling the UI
                    print(f"[Server] Internal Error: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}

"
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass # Expected disconnect
        finally:
            # 6. The Cleanup Guarantee
            print(f"[Server] Stream generator ending. Firing cleanup.")
            await self.repo.cleanup_stream(topic)
```

## Why this is difficult (and important)

1. **The Double `CancelledError` Catch**: When a FastAPI client disconnects mid-stream, Python throws an `asyncio.CancelledError` *inside* the generator. If you don't catch it and handle it gracefully, your server logs will be full of terrifying stack traces, and worse, you might leak database connections.
2. **The `finally` block**: In Agentex, multiple workers might be pushing to a Redis stream. If the UI disconnects, Agentex *must* tell Redis to stop tracking that consumer group. The `finally` block guarantees this happens, even if the server crashes.
3. **The SSE Format**: Standard JSON isn't enough for streaming. SSE requires specific prefixes (`data: `) and double-newlines (`

`) so the browser knows when a "chunk" is complete.
4. **The Ping**: `":ping

"` is an SSE comment. The browser's `EventSource` ignores it completely, but the physical TCP router between the server and the client sees traffic, so it keeps the connection open.