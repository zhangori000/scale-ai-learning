# Solution: Multi-Tenant Stream Routing

This exercise demonstrates the **Fan-out Pattern**. In Agentex, a single worker might generate an event, but multiple users (or multiple browser tabs) might be watching that task.

## The Solution

```python
import asyncio

class StreamRouter:
    def __init__(self):
        self.topics: dict[str, list[asyncio.Queue]] = {}

    async def subscribe(self, task_id: str):
        # 1. Register the new listener
        q = asyncio.Queue()
        if task_id not in self.topics:
            self.topics[task_id] = []
        self.topics[task_id].append(q)
        
        try:
            # 2. Yield messages until disconnected
            while True:
                msg = await q.get()
                yield msg
        finally:
            # 3. CLEANUP (The most important part!)
            print(f"  [Router] Cleaning up listener for {task_id}")
            self.topics[task_id].remove(q)
            
            # 4. If no more listeners, delete the topic to save RAM
            if not self.topics[task_id]:
                del self.topics[task_id]

    async def publish(self, task_id: str, data: str):
        if task_id in self.topics:
            # Broadcast to all active subscribers
            for q in self.topics[task_id]:
                await q.put(data)
```

## Why this is Agentex-style:
1. **The `finally` block**: In high-scale systems, memory leaks from forgotten connections are the #1 cause of crashes. Agentex uses this pattern (and Redis expiration) to ensure old streams don't hang around forever.
2. **Broadcasting**: In `src/utils/stream_topics.py`, you'll see how Agentex standardizes these topic names (`stream:task:{id}`) so different services can find each other.
3. **Isolation**: Because each `task_id` is a separate key in the `topics` dict, User A's data never leaks to User B.
