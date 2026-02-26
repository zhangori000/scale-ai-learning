# Solution: The Producer-Consumer Bridge

The key to this exercise is understanding that the `consume` generator "hangs" on `await self.queue.get()` until data is available. This is exactly how the `StreamsUseCase` in Agentex waits for Redis data without blocking the whole server.

## The Solution

```python
import asyncio
import random

class StreamBridge:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.is_finished = False

    async def produce(self, content: str):
        await self.queue.put(content)

    async def finish(self):
        self.is_finished = True
        await self.queue.put(None) 

    async def consume(self):
        while True:
            # This line is the 'Heartbeat' of streaming. 
            # It pauses this specific coroutine until the Agent puts something in the queue.
            item = await self.queue.get()
            
            if item is None:
                break
                
            yield item
            
            # Mark the task as done in the queue (internal cleanup)
            self.queue.task_done()
```

## Why this is Agentex-style:
1. **Decoupling**: The `agent_task` doesn't know *who* is consuming the data. It just pushes to the "Topic".
2. **Non-blocking**: While `await self.queue.get()` is waiting, the Python Event Loop can handle thousands of other user requests.
3. **Sentinel Pattern**: Using `None` to signal the end of a stream is a standard way to close an SSE connection cleanly.
