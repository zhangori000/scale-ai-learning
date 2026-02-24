# Solution: Build a Durable Agent Reminder

This solution demonstrates the "magic" of Temporal's `workflow.sleep`. Unlike `time.sleep`, it tells the Temporal Server: "I'm going to sleep now. You can stop my process and resume it later."

## The Implementation

```python
import asyncio
from datetime import timedelta
from temporalio import activity, workflow, client, worker

# 1. The Activity (The "Doing")
# In real life, this might send an email or a Slack message.
@activity.define
async def send_reminder_activity(message: str) -> None:
    print(f"--- [ACTIVITY] Reminding you: {message} ---")

# 2. The Workflow (The "Ordering")
@workflow.define
class ReminderWorkflow:
    @workflow.run
    async def run(self, message: str, delay_seconds: int) -> str:
        print(f"-> [WORKFLOW] Starting reminder for '{message}' in {delay_seconds}s")
        
        # This is the "Immortal Sleep"
        # If your server crashes here, Temporal resumes right after this sleep!
        await workflow.sleep(timedelta(seconds=delay_seconds))
        
        # We execute the activity through the workflow context
        await workflow.execute_activity(
            send_reminder_activity,
            message,
            start_to_close_timeout=timedelta(seconds=5)
        )
        
        return f"Reminder '{message}' sent successfully!"

# 3. The Worker (The "Process")
# This program listens for tasks from the Temporal Server.
async def main():
    # Connect to the Temporal Server (running in Docker)
    c = await client.Client.connect("localhost:7233")
    
    # Create the Worker
    w = worker.Worker(
        c,
        task_queue="reminder-task-queue",
        workflows=[ReminderWorkflow],
        activities=[send_reminder_activity],
    )
    
    print("Worker started. Listening for tasks...")
    await w.run()

if __name__ == "__main__":
    asyncio.run(main())

# To Test:
# In one terminal, run 'python main.py' to start the Worker.
# In another terminal, run a separate script to start the workflow:
# client.execute_workflow(ReminderWorkflow.run, "Take a break!", 10, id="reminder-1", task_queue="reminder-task-queue")
```

### Key Takeaways

1.  **Fault Tolerance:** If you stop your `main.py` while it's sleeping, then start it again 10 seconds later, the reminder will fire **immediately** because the "time passed" was tracked on the server, not in your code's memory.
2.  **`workflow.sleep` vs `asyncio.sleep`**: ALWAYS use `workflow.sleep` inside a workflow. If you use `asyncio.sleep`, Temporal cannot track the state, and your workflow will fail.
3.  **Determinism:** Workflows must be deterministic. Never do `print(time.time())` or `random.random()` inside a workflow function. Use `workflow.now()` and `workflow.random()` instead!
