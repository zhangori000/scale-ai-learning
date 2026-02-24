# Exercise: The Deterministic Replay (How Workflows "Resume")

This is the "Magic" of Temporal. If your server crashes mid-workflow, Temporal starts a new server, looks at the **Event History**, and "Replays" the code.

## The Problem
A Workflow is a function. If it crashes at line 10, how does the new server "Skip" to line 10 without re-running the activities it already did? 

**Answer:** It uses a `History` log. Every time it calls an activity, it records the result. During "Replay," it just looks up the result instead of calling the activity again.

## The Goal
Build a `ReplayEngine` that executes a "summing" function by reading a list of past events.

## Requirements
1.  **The History:** A list of events like `[{"type": "ACTIVITY_DONE", "result": 5}, {"type": "ACTIVITY_DONE", "result": 10}]`.
2.  **The Proxy:** Create a `workflow_execute_activity(id, func)` function that:
    *   Checks the `History` for an event with that `id`.
    *   If it exists, **immediately returns the result** from the history (No re-calculation!).
    *   If it doesn't exist, **calls the actual function** and adds a new event to history.
3.  **The Task:** Write a "Workflow" that calls `workflow_execute_activity` twice and sums the results.

## Starter Code
```python
import time

# --- 1. The Real Work (Simulation) ---
def real_api_call(value: int):
    print(f"  [NETWORK] Actually calling API for value: {value}...")
    time.sleep(1)
    return value * 2

# --- 2. The Replay Engine ---
class ReplayEngine:
    def __init__(self, history=None):
        self.history = history or [] # List of past event results
        self.current_step = 0        # Where are we in the history?

    def execute_activity(self, activity_id: str, func, *args):
        # TODO: 
        # 1. Check if self.current_step < len(self.history).
        # 2. If it is, get the result from history and increment step.
        # 3. Print "[REPLAY] Using history for step X: {result}"
        # 4. If not, call func(*args) and append to history.
        # 5. Print "[LIVE] Executing step X: {result}"
        pass

# --- 3. The "Workflow" (Business Logic) ---
def my_workflow(engine: ReplayEngine):
    # Step 1: Call API with 5
    res1 = engine.execute_activity("step-1", real_api_call, 5)
    
    # Step 2: Call API with 10
    res2 = engine.execute_activity("step-2", real_api_call, 10)
    
    print(f"Workflow Sum Result: {res1 + res2}")

# --- 4. Execution (The Simulation) ---

# Scenario: The server CRASHED after step 1.
# We have history for step 1, but NOT step 2.
mock_history = [10] # result of real_api_call(5)

print("--- Resuming Workflow from Crash ---")
engine = ReplayEngine(history=mock_history)
my_workflow(engine)

# Final History should contain both steps
print(f"
Final Event History: {engine.history}")
```
