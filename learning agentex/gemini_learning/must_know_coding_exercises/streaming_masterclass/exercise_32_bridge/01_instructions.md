# Exercise 32: The Producer-Consumer Bridge

In Agentex, the "Agent" and the "API" are often two different processes. 
1. The **Agent** is running a long AI task (Temporal Worker).
2. The **API** is waiting to send data to the user's browser (FastAPI).

They communicate via **Redis Streams**. This exercise simulates that bridge using `asyncio.Queue`.

## The Challenge
You must implement a `StreamBridge`. It has two roles:
1. `produce(chunk_id)`: Simulates the Agent writing a small piece of text to the stream.
2. `consume()`: An async generator that the API uses to yield data to the SSE stream.

**The catch**: The API must stay alive and wait for new data even if the Agent is currently "thinking" and not sending anything.

## Starter Code
```python
import asyncio
import random

class StreamBridge:
    def __init__(self):
        # In real Agentex, this is a Redis Topic
        self.queue = asyncio.Queue()
        self.is_finished = False

    async def produce(self, content: str):
        """Simulates the Agent writing to the stream"""
        print(f"  [Agent] Producing: {content}")
        await self.queue.put(content)

    async def finish(self):
        """Signals the stream is done"""
        self.is_finished = True
        await self.queue.put(None) # Sentinel value to stop the consumer

    async def consume(self):
        """
        TODO: Implement the API Consumer.
        
        Requirements:
        1. Loop infinitely while `not self.is_finished` or queue is not empty.
        2. Get items from `self.queue`.
        3. If item is `None`, break.
        4. Yield the content.
        """
        pass

async def agent_task(bridge: StreamBridge):
    """Simulates an Agent thinking and streaming"""
    chunks = ["Hello", "how", "can", "I", "help", "today?"]
    for chunk in chunks:
        await asyncio.sleep(random.uniform(0.1, 0.5)) # Thinking...
        await bridge.produce(chunk)
    await bridge.finish()

async def api_endpoint(bridge: StreamBridge):
    """Simulates the FastAPI SSE endpoint"""
    print("--- [API] SSE Connection Opened ---")
    async for data in bridge.consume():
        print(f"--- [API] Yielding to Browser: {data}")
    print("--- [API] SSE Connection Closed ---")

async def main():
    bridge = StreamBridge()
    # Run both concurrently
    await asyncio.gather(agent_task(bridge), api_endpoint(bridge))

if __name__ == "__main__":
    asyncio.run(main())
```
