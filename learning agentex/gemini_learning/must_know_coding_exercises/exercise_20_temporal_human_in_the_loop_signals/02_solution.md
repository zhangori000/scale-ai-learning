# Solution: Human-in-the-Loop (Durable Signals)

In `scale-agentex`, a "Task" follows a strict lifecycle. When an AI needs human input, it emits an event, and the platform "Pauses" the Temporal Workflow until a human clicks a button in the UI.

## The Implementation

```python
import asyncio
from enum import Enum

# --- 1. Define the Decisions ---
class Decision(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

# --- 2. The Durable Workflow ---
class ReviewWorkflow:
    def __init__(self):
        # Starts as pending
        self.decision = Decision.PENDING
        # This is our 'Pause' button. 
        # In real Temporal, this is 'workflow.wait_condition'.
        self.approval_event = asyncio.Event()

    def receive_signal(self, decision: Decision):
        """
        An external call from the UI/API that 'wakes up' the workflow.
        """
        print(f"  [SIGNAL] Signal received: {decision.upper()}!")
        self.decision = decision
        
        # This 'Sets' the event, allowing anything awaiting it to continue.
        self.approval_event.set()

    async def run(self):
        """
        The main business logic. It can run, pause, and resume.
        """
        print("[WORKFLOW] Doing initial AI analysis on the document...")
        # Simulate some fast AI work
        await asyncio.sleep(1)
        
        print("[WORKFLOW] PAUSED: Awaiting human approval via signal...")
        
        # 1. The 'Immortal Wait'
        # This is where Temporal would save the state to Postgres and stop 
        # the CPU process entirely until the signal arrives.
        await self.approval_event.wait()
        
        # 2. Resuming!
        print("[WORKFLOW] RESUMING: Processing decision...")
        
        if self.decision == Decision.APPROVED:
            print("  [SUCCESS] Human Approved. Filing the legal document!")
        elif self.decision == Decision.REJECTED:
            print("  [ACTION] Human Rejected. Notifying the Agent to rewrite.")
        
        print("[WORKFLOW] Final state: COMPLETED")

# --- 3. Execution (The Simulation) ---
async def main():
    # Instantiate our 'Durable' workflow
    workflow = ReviewWorkflow()
    
    # 1. Start the workflow in the background (Imagine it's running on a Temporal Worker)
    # We don't 'await' it yet, because it's going to pause!
    workflow_task = asyncio.create_task(workflow.run())
    
    # 2. Wait for a few seconds (Simulates the human partner taking their time)
    print("
[SYSTEM] Waiting for human review (simulating 3 seconds)...")
    await asyncio.sleep(3)
    
    # 3. A human partner logs into the Agentex UI and clicks "APPROVE"
    print("
[UI] Human Partner clicks 'APPROVE' on Task ID: 123")
    workflow.receive_signal(Decision.APPROVED)
    
    # 4. Now we wait for the workflow to finish its final steps
    await workflow_task

if __name__ == "__main__":
    asyncio.run(main())
```

### Key Takeaways from the Solution:

1.  **Non-Blocking Wait:** The `await self.approval_event.wait()` is the most important part. It tells the Python event loop: "I'm not doing anything right now, feel free to process other requests while I wait for this flag."
2.  **External Trigger:** The `receive_signal` method is called from the **Outside**. In `scale-agentex`, this would be an API endpoint like `POST /tasks/{id}/approve`.
3.  **Durable State:** Notice that `self.decision` is stored on the object. In real Temporal, this object is **Serialized** (converted to JSON) and saved in a database, so if the server crashes while waiting, the decision is never lost.
4.  **Why we use it for Agents:** In "Level 5" autonomous systems, the agent acts as a **Copilot**. It does 90% of the work and then waits for the human to do the final 10%. This pattern is how we build safe AI that keeps a "Human in the Loop" for critical decisions.
