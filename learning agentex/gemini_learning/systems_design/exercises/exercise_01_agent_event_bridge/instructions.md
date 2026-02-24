# Exercise: Design the "Event Forwarding" Component

In `scale-agentex`, sometimes the Agent needs to send an "Event" back to the platform (e.g., "I am 50% done" or "I need a human to help").

## The Goal
Design a simplified "Event Forwarding" system. This is a sub-component of the overall systems design.

## Requirements
1.  **Agent:** Needs to call a `send_event` endpoint on the Platform API.
2.  **Platform API (FastAPI):** Needs to receive the event, validate it, and then **push it to a message queue (Redis)** so the UI can see it immediately.
3.  **UI:** Needs to "subscribe" to that Redis queue for a specific task.

## The Task
Write a mock design in Python that implements:
1.  The `Agent` class that "emits" an event.
2.  The `PlatformAPI` class that "receives" and "dispatches" the event.
3.  The `RedisQueue` mock that stores and notifies.

## Starter Code
```python
class RedisQueue:
    def __init__(self):
        self.subscribers = {} # {task_id: [callback1, callback2]}

    def subscribe(self, task_id, callback):
        # TODO: Implement subscription logic
        pass

    def publish(self, task_id, event_data):
        # TODO: Implement notification logic
        pass

class PlatformAPI:
    def __init__(self, queue):
        self.queue = queue

    def receive_event_from_agent(self, task_id, event_data):
        # TODO: Receive and publish to queue
        pass

class Agent:
    def __init__(self, api, task_id):
        self.api = api
        self.task_id = task_id

    def perform_work_and_notify(self):
        # TODO: Simulate work and call api.receive_event_from_agent
        pass
```
