# Solution: The Backpressure Problem (Batching)

This exercise solves the "Thundering Herd" problem where too many small messages overwhelm the system.

## The Solution

```python
import asyncio
import time

class BatchingStreamer:
    def __init__(self, batch_size: int = 10, max_wait: float = 0.2):
        self.batch_size = batch_size
        self.max_wait = max_wait
        self.buffer = []
        self.last_yield_time = time.time()

    async def stream(self, token_iterator):
        async for token in token_iterator:
            self.buffer.append(token)
            
            now = time.time()
            time_since_last = now - self.last_yield_time
            
            # Check if we should flush the buffer
            if len(self.buffer) >= self.batch_size or time_since_last >= self.max_wait:
                yield "".join(self.buffer)
                self.buffer = []
                self.last_yield_time = now
        
        # Flush the final remainder
        if self.buffer:
            yield "".join(self.buffer)
```

## Why this is Agentex-style:
1. **Performance**: Sending 1 packet of 500 bytes is much more efficient than sending 50 packets of 10 bytes over TCP.
2. **Smoothness**: By batching, the UI only has to re-render 5 times per second instead of 50, which keeps the "scrolling" feeling smooth for the user.
3. **Infrastructure Cost**: Fewer SSE writes means lower CPU usage on the API gateway and fewer Redis `XADD` operations.
