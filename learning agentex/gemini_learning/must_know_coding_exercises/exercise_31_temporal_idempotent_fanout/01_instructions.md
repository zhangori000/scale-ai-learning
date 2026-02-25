# Exercise 31: Idempotent Event-to-Task Fanout

In `scale-agentex`, an external system (like a webhook from a customer) sends an **Event**. The Agentex `EventsUseCase` is responsible for taking that single event and fanning it out into one or more **Tasks** (1:M Mapping).

However, external systems (like Stripe or GitHub webhooks) guarantee *At-Least-Once* delivery. This means if Agentex is slow to respond with a `200 OK`, the external system will send the **exact same webhook again 5 seconds later**.

## The Challenge

If Agentex processes the same webhook twice, it might spawn duplicate Temporal Workflows, double-charging a customer or doing the same AI generation twice.

You must build an `Idempotent` fanout system. If an Event asks to create 3 tasks, you must generate a deterministic `idempotency_key` for each task based on the Event ID. Before creating a task, you must check the database to see if a task with that key already exists.

## Starter Code

```python
import uuid

# --- Domain Models ---
class Event:
    def __init__(self, event_id: str, data: dict):
        self.id = event_id
        self.data = data

class Task:
    def __init__(self, name: str, idempotency_key: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.idempotency_key = idempotency_key

# --- Simulated Infrastructure ---
class MockDB:
    def __init__(self):
        self.tasks = {} # Key: task.id, Value: Task
        # Secondary Index to simulate UNIQUE CONSTRAINT on idempotency_key
        self.idemp_index = {} 

    def get_task_by_idempotency_key(self, key: str) -> Task | None:
        return self.idemp_index.get(key)

    def save_task(self, task: Task):
        if task.idempotency_key in self.idemp_index:
            raise ValueError(f"Integrity Error: Duplicate idempotency_key '{task.idempotency_key}'")
        self.tasks[task.id] = task
        self.idemp_index[task.idempotency_key] = task
        print(f"  [DB] Saved task: {task.name} with key: {task.idempotency_key}")

class MockTemporal:
    def start_workflow(self, task: Task):
        print(f"  [Temporal] Started workflow for Task ID: {task.id}")

# --- Your Task ---

class EventsUseCase:
    def __init__(self, db: MockDB, temporal: MockTemporal):
        self.db = db
        self.temporal = temporal

    def process_event(self, event: Event):
        """
        TODO: Implement Idempotent Fanout.
        
        Requirements:
        1. Read the list of target task names from `event.data["create_tasks"]`.
        2. For each task name, generate a UNIQUE but DETERMINISTIC idempotency key.
           (Hint: Combine event.id and the task name or index).
        3. Check the DB. If a task with that key exists, SKIP IT (already processed).
        4. If it doesn't exist, create a new `Task`, save it to the DB, and start the Temporal workflow.
        """
        pass

# --- Execution Simulation ---
def simulate_webhook_retry():
    db = MockDB()
    temporal = MockTemporal()
    use_case = EventsUseCase(db, temporal)
    
    event_payload = Event(
        event_id="evt_999", 
        data={"create_tasks": ["transcribe_audio", "generate_summary"]}
    )
    
    print("--- Attempt 1: Initial Webhook Receipt ---")
    use_case.process_event(event_payload)
    
    print("
--- Attempt 2: Webhook Retried (Due to network timeout) ---")
    # This should NOT crash, and should NOT create duplicate tasks!
    use_case.process_event(event_payload)

if __name__ == "__main__":
    simulate_webhook_retry()
```