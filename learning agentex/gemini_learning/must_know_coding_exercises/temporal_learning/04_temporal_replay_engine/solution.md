# Solution: Mini Temporal Replay Engine

This implementation focuses on how Temporal achieves **durable execution** through **event sourcing** and **deterministic replay**.

```python
import functools
from typing import Any, Callable, Dict, List, Optional, Tuple

class NonDeterministicError(Exception):
    """Raised when the workflow execution deviates from history during replay."""
    pass

def activity(func: Callable) -> Callable:
    """Decorator to mark a function as a Temporal Activity."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.__is_activity__ = True
    return wrapper

class WorkflowContext:
    def __init__(self, history: Optional[List[Dict[str, Any]]] = None):
        # The history of events recorded so far.
        self.history: List[Dict[str, Any]] = history or []
        # A pointer to the current position in history (used during replay).
        self._history_pointer: int = 0
        # Tracks if we are currently in 'replay' mode.
        self._is_replaying: bool = history is not None

    def execute_activity(self, activity_fn: Callable, *args) -> Any:
        """
        Executes an activity or returns a recorded result from history.
        This is the core 'interceptor' that enables Temporal's durability.
        """
        activity_name = activity_fn.__name__

        # REPLAY LOGIC: Check if this step was already recorded
        if self._is_replaying and self._history_pointer < len(self.history):
            event = self.history[self._history_pointer]
            
            # DETERMINISM CHECK: 
            # If the activity name or arguments don't match, we have a problem.
            # In real Temporal, this is why you shouldn't use random() or time.now() 
            # inside a workflow directly!
            if event["type"] != "activity" or event["name"] != activity_name or event["args"] != list(args):
                msg = f"Non-deterministic deviation at step {self._history_pointer}: " 
                      f"Expected {event['name']}({event['args']}), but workflow called {activity_name}({args})"
                raise NonDeterministicError(msg)
            
            # Increment pointer and return the STALED result
            self._history_pointer += 1
            print(f"[REPLAY] Using cached result for {activity_name}: {event['result']}")
            return event["result"]

        # LIVE EXECUTION LOGIC: Record a new event
        if not getattr(activity_fn, "__is_activity__", False):
            raise ValueError(f"Function {activity_name} must be decorated with @activity")

        # Execute the actual side-effect
        result = activity_fn(*args)

        # Append to history for future replays
        self.history.append({
            "type": "activity",
            "name": activity_name,
            "args": list(args),
            "result": result
        })
        self._history_pointer += 1
        return result

class WorkflowEngine:
    def run(self, workflow_fn: Callable, *args) -> Tuple[Any, List[Dict[str, Any]]]:
        """Runs a workflow for the first time and records history."""
        print(f"\n--- Starting Workflow: {workflow_fn.__name__} ---")
        ctx = WorkflowContext()
        result = workflow_fn(ctx, *args)
        return result, ctx.history

    def replay(self, workflow_fn: Callable, history: List[Dict[str, Any]], *args) -> Any:
        """Replays a workflow using an existing history."""
        print(f"\n--- Replaying Workflow: {workflow_fn.__name__} ---")
        ctx = WorkflowContext(history=history)
        return workflow_fn(ctx, *args)

# --- Example Usage ---

@activity
def get_user_id(username: str) -> int:
    print(f"SIDE EFFECT: Querying DB for {username}...")
    return 101

@activity
def send_welcome_email(user_id: int, email: str) -> bool:
    print(f"SIDE EFFECT: Sending email to {email} (ID: {user_id})...")
    return True

def signup_workflow(ctx: WorkflowContext, username: str, email: str):
    # Step 1: Get ID
    user_id = ctx.execute_activity(get_user_id, username)
    
    # Step 2: Complex logic that doesn't need to be an activity (deterministic)
    greeting = f"Welcome, {username}!"
    print(f"LOGIC: Prepared greeting: {greeting}")
    
    # Step 3: Send email
    success = ctx.execute_activity(send_welcome_email, user_id, email)
    
    return f"Workflow complete. Email status: {success}"

if __name__ == "__main__":
    engine = WorkflowEngine()
    
    # 1. Initial execution
    result, history = engine.run(signup_workflow, "jdoe", "jdoe@example.com")
    print(f"RESULT: {result}")
    
    # 2. Replay (Simulation of a worker crash and recovery)
    # Notice how the "SIDE EFFECT" print statements DO NOT run during replay.
    replay_result = engine.replay(signup_workflow, history, "jdoe", "jdoe@example.com")
    print(f"REPLAY RESULT: {replay_result}")
    
    # 3. Non-deterministic Error Simulation
    # If we change the arguments during replay, it should fail.
    try:
        engine.replay(signup_workflow, history, "different_user", "jdoe@example.com")
    except NonDeterministicError as e:
        print(f"CAUGHT ERROR: {e}")
```

## Deep Dive Explanation

### 1. The Interception Pattern
The `WorkflowContext.execute_activity` method is the most important part. It sits between the workflow code and the actual execution of side effects. This is exactly how `temporalio` works. Instead of calling a function directly, you call `workflow.execute_activity()`.

### 2. Determinism
Notice that in `signup_workflow`, the `greeting` variable is just a standard Python string. This is fine because it's **deterministic**—given the same inputs (`username`), it will always produce the same string. However, if you put `datetime.now()` there, the string might change during replay, leading to potential bugs if that string was later used in an activity argument.

### 3. Replay Pointer
The `_history_pointer` ensures that we process events in the exact order they were recorded. If the workflow tries to call Activity B before Activity A during replay, the engine detects the mismatch and throws a `NonDeterministicError`.

### 4. Connection to `agentex`
In `agentex`, when you see `TemporalTaskService.send_event`, it's essentially sending a signal to a running workflow. Signals are recorded in the history just like activities. When a workflow is "re-hydrated" (replayed), it checks the history to see which signals have already been processed, ensuring that even if the worker crashed while processing a signal, it won't be lost or double-processed.
