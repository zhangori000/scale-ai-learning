# Exercise: Build a Durable Agent Reminder

We're going to build a Workflow that takes a "Reminder Message" and a "Delay (seconds)".

## The Goal
In a normal Python program, if you do `time.sleep(10)`, and the program crashes, your reminder is lost.

In this Temporal exercise, we'll build a workflow that uses `workflow.sleep()`. If the server crashes during that sleep, the Temporal Server will **resume** it exactly where it was when the server comes back online.

## Requirements
1.  **An Activity:** Create an activity `send_reminder_activity(message: str)` that simply prints the message to the console.
2.  **A Workflow:** Create a workflow `ReminderWorkflow` that:
    *   Takes a message and a delay (int).
    *   Waits for the delay using `await workflow.sleep(timedelta(seconds=delay))`.
    *   Calls the `send_reminder_activity`.
3.  **A Worker:** (Just write the code for it, no need to run yet).

## Starter Code
```python
from datetime import timedelta
from temporalio import activity, workflow

# 1. Your Activity here...

# 2. Your Workflow here...

# 3. Your Worker code here...
```

---
### When you are ready, check the solution file!
