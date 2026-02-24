# Lesson 01: What is Temporal? (Durable Execution)

### The Problem: "The World is Unreliable"
Imagine you are building an AI agent that:
1.  Takes a user's request.
2.  Calls an LLM (takes 30 seconds).
3.  Calls a payment API (takes 5 seconds).
4.  Sends an email confirmation.

**What happens if your server crashes at step 3?** 
In a normal app, that request is **lost**. The user was charged, but never got the email. You'd have to write complex logic to "resume" or "retry" every single step.

### The Solution: Temporal
Temporal provides **Durable Execution**. It means your code is "fault-tolerant." If your server dies, Temporal "remembers" exactly where it was and **restarts the code on a different server** from the last successful step.

### How it Works (The 4 Main Pieces)

1.  **Temporal Server:** The "Brain." It keeps track of the state of every running workflow. (In `scale-agentex`, this is running in Docker).
2.  **Workflow:** The "Orchestrator." It's a function that defines the high-level steps (the "what"). It MUST be deterministic (no random numbers, no direct API calls).
3.  **Activity:** The "Worker." This is where the actual work happens (API calls, DB writes, LLM calls). Activities can fail and be retried automatically.
4.  **Worker:** The "Process." A long-running program on your server that listens to the Temporal Server and actually executes the Workflows and Activities.

---

# Lesson 02: Workflows vs. Activities

In `scale-agentex`, Temporal is used to manage complex agent tasks. Here is the mental model:

### 1. The Activity (The "Doing")
Activities are for "unreliable" things like network calls. Temporal will automatically retry them if they fail.

```python
from temporalio import activity

@activity.define
async def call_openai(prompt: str) -> str:
    # This is where the actual network call happens
    # If this fails, Temporal retries it 3 times (by default)
    return f"AI Response to: {prompt}"
```

### 2. The Workflow (The "Ordering")
Workflows coordinate activities. They are like a script.

```python
from datetime import timedelta
from temporalio import workflow

# Import our activity
with workflow.unsafe.imports_passed_through():
    from activities import call_openai

@workflow.define
class MyAgentWorkflow:
    @workflow.run
    async def run(self, prompt: str) -> str:
        # We 'execute' the activity through the workflow context
        result = await workflow.execute_activity(
            call_openai, 
            prompt, 
            start_to_close_timeout=timedelta(seconds=60)
        )
        return result
```

### 3. Why the split?
*   **Workflows** are "immortal." They can sleep for 10 years and resume.
*   **Activities** are "mortal." They do the dangerous, messy work of talking to the outside world.
