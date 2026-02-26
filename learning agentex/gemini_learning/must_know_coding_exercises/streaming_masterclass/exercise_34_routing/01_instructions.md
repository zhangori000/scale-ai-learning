# Exercise 34: Multi-Tenant Stream Routing

In a real platform like Scale AI, you don't have just one stream. You have **thousands** of users running agents simultaneously. 

Each Agent (Worker) needs to know *exactly* which "Topic" to write to, and the API needs to know *exactly* which "Topic" to listen to for a specific `task_id`.

## The Challenge
Implement a `StreamRouter`. 
1. It must generate a unique topic string for a given `task_id`.
2. It must track "Active Listeners". If 3 browser tabs are open for the same `task_id`, they should all receive the same data.
3. **The Garbage Collector**: If all listeners for a topic disconnect, the router must clean up the topic from memory to prevent a leak.

## Starter Code
```python
import asyncio

class StreamRouter:
    def __init__(self):
        # Maps task_id -> list of asyncio.Queues (one per listener)
        self.topics: dict[str, list[asyncio.Queue]] = {}

    def get_topic_name(self, task_id: str) -> str:
        return f"stream:task:{task_id}"

    async def subscribe(self, task_id: str):
        """
        TODO:
        1. Create a new asyncio.Queue for this specific listener.
        2. Add it to the list of listeners for this task_id.
        3. Yield data from the queue.
        4. CRITICAL: Use a 'finally' block to remove the queue from the list 
           when the listener disconnects.
        """
        pass

    async def publish(self, task_id: str, data: str):
        """
        TODO:
        1. Find all queues listening to this task_id.
        2. Put the data into every queue.
        """
        pass

# --- Simulation ---
async def client_listener(router: StreamRouter, name: str, task_id: str):
    print(f"  [Client {name}] Subscribing to {task_id}")
    count = 0
    async for msg in router.subscribe(task_id):
        print(f"  [Client {name}] Received: {msg}")
        count += 1
        if count >= 2: break # Simulate client closing after 2 messages

async def main():
    router = StreamRouter()
    
    # 1. Start two clients for the same task
    l1 = asyncio.create_task(client_listener(router, "A", "task-1"))
    l2 = asyncio.create_task(client_listener(router, "B", "task-1"))
    await asyncio.sleep(0.1)

    # 2. Publish data once
    print("[Server] Publishing update for task-1")
    await router.publish("task-1", "Update #1")
    await router.publish("task-1", "Update #2")
    
    await asyncio.gather(l1, l2)
    print(f"[Server] Active topics: {list(router.topics.keys())}")
    # Requirement: If both A and B finished, 'task-1' should be gone from router.topics!

if __name__ == "__main__":
    asyncio.run(main())
```
