# Exercise 35: The Backpressure Problem (Batching)

LLMs like GPT-4 can sometimes generate 50+ tokens per second. If the Agentex API tries to send 50 separate SSE messages every second, the browser's main thread will lock up (UI lag).

To solve this, Agentex uses **Adaptive Batching**. 

## The Challenge
Implement a `BatchingStreamer`.
- It receives individual "Tokens" (strings).
- Instead of yielding them immediately, it waits until either:
    1. It has collected **10 tokens**.
    2. **0.2 seconds** have passed since the last token arrived.
- Then it yields the combined string.

## Starter Code
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
        """
        TODO: Implement the batching logic.
        
        Requirements:
        1. Loop over 'token_iterator'.
        2. Append token to 'self.buffer'.
        3. If len(buffer) >= batch_size OR (now - last_yield > max_wait):
            - Join buffer into a string.
            - Yield it.
            - Clear buffer.
            - Update last_yield_time.
        4. After the loop, yield any remaining tokens in the buffer.
        """
        pass

# --- Simulation ---
async def mock_tokens():
    """Simulates a fast LLM"""
    for i in range(25):
        yield f"t{i} "
        await asyncio.sleep(0.05) # 20 tokens per second

async def main():
    streamer = BatchingStreamer(batch_size=8, max_wait=0.3)
    print("--- Starting Batched Stream ---")
    async for chunk in streamer.stream(mock_tokens()):
        print(f"UI Received Chunk: '{chunk}'")

if __name__ == "__main__":
    asyncio.run(main())
```
