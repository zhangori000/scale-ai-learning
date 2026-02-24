# Solution: The Deterministic Replay (Workflow Internals)

In `scale-agentex`, Temporal workflows use this exact pattern. If the server crashes, it "re-runs" the entire Python function from the beginning, but it "replaces" all the actual API calls with the results it already has in its database (Postgres).

## The Implementation

```python
import time

# --- 1. The Real Work (Simulation) ---
def real_api_call(value: int):
    print(f"  [NETWORK] Actually calling API for value: {value}...")
    # This represents a slow network call to an AI Agent or OpenAI
    time.sleep(1)
    return value * 2

# --- 2. The Replay Engine ---
class ReplayEngine:
    def __init__(self, history=None):
        self.history = history or [] # This is 'Event History' in Temporal
        self.current_step = 0        # A counter of where we are in replay

    def execute_activity(self, activity_id: str, func, *args):
        """
        The magic logic: If we have history for this step, 
        WE DON'T CALL THE FUNCTION. We just return the past result.
        """
        if self.current_step < len(self.history):
            # 1. We have history! This is a "Replay"
            result = self.history[self.current_step]
            print(f"  [REPLAY] Activity '{activity_id}' - Using history: {result}")
            self.current_step += 1
            return result
        else:
            # 2. No history for this step. This is a "Live" call
            result = func(*args)
            print(f"  [LIVE] Activity '{activity_id}' - Executed: {result}")
            self.history.append(result)
            self.current_step += 1
            return result

# --- 3. The "Workflow" (Business Logic) ---
def my_workflow(engine: ReplayEngine):
    # This code is run by Temporal every time the workflow starts or resumes.
    # It must be 'Deterministic' - always produce the same order of calls.
    
    # Step 1: Call API with 5
    res1 = engine.execute_activity("step-1", real_api_call, 5)
    
    # Step 2: Call API with 10
    res2 = engine.execute_activity("step-2", real_api_call, 10)
    
    print(f"
Final Workflow Sum: {res1 + res2}")

# --- 4. Execution (The Simulation) ---

# Scenario: The server CRASHED after step 1 was finished.
# The 'Temporal Server' (Postgres) remembers that step 1 resulted in '10'.
mock_history = [10]

print("--- Resuming Workflow from Crash ---")
print(f"Initial History: {mock_history}")

engine = ReplayEngine(history=mock_history)
my_workflow(engine)

# Final History should contain both steps now
print(f"
Updated Event History: {engine.history}")

# Observe:
# 1. 'step-1' did NOT print "[NETWORK] Actually calling API" because it was replayed.
# 2. 'step-2' DID print "[NETWORK] Actually calling API" because it was a new live call.
```

### Key Takeaways

1.  **Immortality:** By replaying history, a workflow can "live" forever across multiple server restarts.
2.  **Determinism Rule:** Never use `random.random()` or `datetime.now()` inside a Workflow! Why? Because during "Replay," those values would change, and the history wouldn't match the new code path.
3.  **Why we use it for Agents:** If an Agent task takes 10 minutes (analyzing a legal contract), and the platform crashes at minute 9, Temporal "replays" the history up to minute 9 and then picks up right where it left off!
