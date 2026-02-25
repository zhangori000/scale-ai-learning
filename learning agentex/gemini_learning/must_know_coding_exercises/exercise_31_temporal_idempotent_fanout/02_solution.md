# Solution: Idempotent Event-to-Task Fanout

This exercise highlights a core concept in the `scale-agentex` architecture. 

When you decouple an API (FastAPI) from its execution engine (Temporal Worker), you **must** use idempotency keys. Without them, network retries lead to duplicated asynchronous work, which is incredibly difficult to untangle later.

## The Solution Code

```python
import uuid

# ... (Domain Models and Infrastructure omitted for brevity) ...

class EventsUseCase:
    def __init__(self, db: MockDB, temporal: MockTemporal):
        self.db = db
        self.temporal = temporal

    def process_event(self, event: Event):
        task_names = event.data.get("create_tasks", [])
        
        for task_name in task_names:
            # 1. Generate Deterministic Key
            # We combine the Event ID with the Task Name. 
            # If this exact webhook is retried, it will generate the EXACT SAME KEY.
            idemp_key = f"{event.id}::{task_name}"
            
            # 2. Check Database (The Source of Truth)
            existing_task = self.db.get_task_by_idempotency_key(idemp_key)
            
            if existing_task:
                # 3. Handle Idempotent Hit
                print(f"  [EventsUseCase] Idempotency Hit! Task '{task_name}' already spawned from Event '{event.id}'. Skipping.")
                continue # Move to the next task in the fanout
                
            # 4. Handle Cache Miss (First time seeing this task)
            new_task = Task(name=task_name, idempotency_key=idemp_key)
            
            # 5. Save State *Before* starting the async work
            # This ensures if we crash right after saving, the next retry will hit the DB and stop.
            self.db.save_task(new_task)
            
            # 6. Spawn the worker
            self.temporal.start_workflow(new_task)

# --- Output Analysis ---
# --- Attempt 1: Initial Webhook Receipt ---
#   [DB] Saved task: transcribe_audio with key: evt_999::transcribe_audio
#   [Temporal] Started workflow for Task ID: <uuid-1>
#   [DB] Saved task: generate_summary with key: evt_999::generate_summary
#   [Temporal] Started workflow for Task ID: <uuid-2>
#
# --- Attempt 2: Webhook Retried (Due to network timeout) ---
#   [EventsUseCase] Idempotency Hit! Task 'transcribe_audio' already spawned... Skipping.
#   [EventsUseCase] Idempotency Hit! Task 'generate_summary' already spawned... Skipping.
```

## Why this is difficult (and important)

1. **The DB Constraint:** In Agentex, the `tasks` table in PostgreSQL has a `UNIQUE` constraint on the `idempotency_key` column. Even if two webhooks hit two different servers at the *exact same microsecond*, the database will throw an `IntegrityError` on the second one, preventing a race condition.
2. **Order of Operations:** Notice that `self.db.save_task()` happens **before** `self.temporal.start_workflow()`. 
    * If Temporal started first and the DB save failed, you would have a "Ghost Workflow" running without any record of it in the Agentex API.
    * By saving to the DB first, if Temporal fails to start, the webhook will retry, hit the DB, see the task exists, but (in a real system) realize Temporal hasn't started yet and retry the start command.
3. **Fanning Out Safely:** If a webhook requires creating 10 tasks, and the server crashes after creating task 5... the webhook will retry. The first 5 tasks will be skipped (Idempotent Hits), and tasks 6-10 will be created perfectly. 