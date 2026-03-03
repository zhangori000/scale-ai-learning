# Exercise 4: Implementing a Deterministic Replay Engine (Temporal Deep Dive)

## Goal
In `agentex`, Temporal is used to ensure that long-running agent tasks are durable. If a worker crashes mid-task, Temporal can "replay" the workflow from its event history to restore its state exactly where it left off. 

Your goal is to implement a **Mini Workflow Engine** that supports **Deterministic Replay** and **Activity Execution**.

## The Problem
Standard Python functions are not "durable." If a function is running and the process dies, all local state is lost. To fix this, Temporal uses **Event Sourcing**:
1. Every time a "side effect" (like an API call) happens, it is recorded in a **History**.
2. To "resume," the engine starts the function from the beginning.
3. When the function reaches a point where it previously recorded a result, the engine **intercepts** the call and returns the recorded result instead of re-executing it.

## Your Tasks

Implement the following components in `solution.py`:

1.  **`Activity` Decorator**: Marks a function as an activity that should be recorded in history.
2.  **`WorkflowContext`**:
    *   `execute_activity(activity_fn, *args)`: Checks if this activity (with these args) has already been executed in the current `history`.
    *   If yes: returns the stored result.
    *   If no: executes the activity, records the result in history, and returns it.
3.  **`WorkflowEngine`**:
    *   `run(workflow_fn, *args)`: Executes the workflow and returns the final result and the generated history.
    *   `replay(workflow_fn, history, *args)`: Executes the workflow again, but uses the provided history to "skip" activity executions.

## Requirements
*   **Determinism Check**: If the workflow tries to execute an activity that doesn't match the history during a replay, it should raise a `NonDeterministicError`.
*   **History Structure**: A simple list of dictionaries like `{"type": "activity", "name": "...", "args": [...], "result": ...}`.
*   **Concurrency**: For this exercise, assume synchronous execution (no `async/await` needed, though you can use it if you prefer).

## Example Usage
```python
@activity
def get_user_email(user_id):
    print(f"--- Fetching email for {user_id} ---")
    return f"{user_id}@example.com"

def my_workflow(ctx, user_id):
    email = ctx.execute_activity(get_user_email, user_id)
    return f"Sent email to {email}"

engine = WorkflowEngine()
# First Run
result, history = engine.run(my_workflow, "user_123")
# Output: --- Fetching email for user_123 ---

# Replay
# Should NOT print "Fetching email..." again!
replay_result = engine.replay(my_workflow, history, "user_123")
assert result == replay_result
```

## Why this matters for `agentex`?
`agentex` relies on `TemporalTaskService` to send events and manage agent state. Understanding how the history allows for "time travel" and "recovery" is key to debugging stuck workflows or non-deterministic errors in the production codebase.
