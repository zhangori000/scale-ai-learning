# Solution: Build a Real-time Event Bridge

This solution demonstrates the "Reactive" part of `scale-agentex`. It uses a **Pub/Sub (Publish-Subscribe)** pattern to ensure that when an Agent emits an event, the UI (or any other subscriber) sees it immediately.

## The Implementation

```python
import time
import uuid

# --- 1. The Real-time Message Bus (Redis Mock) ---
class RedisPubSub:
    """
    Simulates Redis's ability to 'broadcast' messages to multiple 
    listeners without storing them forever.
    """
    def __init__(self):
        # Dictionary of lists: {task_id: [callback_function_1, callback_function_2]}
        self.subscribers = {}

    def subscribe(self, task_id, callback):
        if task_id not in self.subscribers:
            self.subscribers[task_id] = []
        self.subscribers[task_id].append(callback)
        print(f"  [REDIS] New subscriber added for Task: {task_id}")

    def publish(self, task_id, event_data):
        """
        When a message comes in, push it to every listener for that task.
        """
        if task_id in self.subscribers:
            print(f"  [REDIS] Broadcasting event to {len(self.subscribers[task_id])} listener(s)...")
            for callback in self.subscribers[task_id]:
                callback(event_data)
        else:
            print(f"  [REDIS] No one listening for Task: {task_id}. Event dropped.")

# --- 2. The Platform API (FastAPI Mock) ---
class PlatformAPI:
    """
    The 'Ingestion Point' for events coming from agents.
    In scale-agentex, this is handled by routes like '/tasks/{task_id}/events'.
    """
    def __init__(self, pubsub):
        self.pubsub = pubsub

    def receive_event_from_agent(self, task_id, event_type, content):
        print(f"[API] Received '{event_type}' event from Agent for Task: {task_id}")
        
        # 1. We could save this to MongoDB for history here...
        # 2. But the most important part is to notify the UI via Pub/Sub
        event_payload = {
            "id": str(uuid.uuid4())[:8],
            "type": event_type,
            "content": content,
            "timestamp": time.time()
        }
        self.pubsub.publish(task_id, event_payload)

# --- 3. The Agent (The Logic) ---
class Agent:
    def __init__(self, api, task_id):
        self.api = api
        self.task_id = task_id

    def do_intelligent_work(self):
        print(f"[AGENT] Starting work on Task: {self.task_id}...")
        
        # Step 1: Notify that we've started
        self.api.receive_event_from_agent(self.task_id, "STATUS_UPDATE", "I am now analyzing your request.")
        time.sleep(1)
        
        # Step 2: Notify about an intermediate thought
        self.api.receive_event_from_agent(self.task_id, "THOUGHT", "I think I should search for the weather first.")
        time.sleep(1)
        
        # Step 3: Final Response
        self.api.receive_event_from_agent(self.task_id, "DONE", "The weather in San Francisco is 65°F and sunny.")

# --- 4. Execution (The Simulation) ---

# 1. Setup the infrastructure
redis = RedisPubSub()
api = PlatformAPI(redis)

# 2. Mock a UI "Subscribing" to a task
def ui_listener(event):
    print(f"  >>> [UI NOTIFICATION] Received: {event['type']} - {event['content']}")

task_id = "TASK_ABC_123"
redis.subscribe(task_id, ui_listener)

# 3. Start the agent (which will push events to the API)
my_agent = Agent(api, task_id)
my_agent.do_intelligent_work()
```

### Key Takeaways from the Systems Design

1.  **Loose Coupling:** The Agent doesn't know who is listening to its events. It just calls the API. This makes the system very flexible.
2.  **Responsiveness:** By using a Pub/Sub system (like Redis), the UI can update the moment the Agent has a "thought." This creates the "Agent is alive" feeling.
3.  **Scale:** In a real production environment, you might have 1,000 Agents sending events at the same time. The Redis Pub/Sub architecture is designed to handle this high-frequency, "fire-and-forget" traffic.
