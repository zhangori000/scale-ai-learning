# Exercise: Human-in-the-Loop (Durable Signals)

In `scale-agentex`, a "Task" might need human approval before it can finish. We don't want a Python loop to run for 3 days waiting; we want a **Workflow** that "Pauses" and waits for an external **Signal**.

## The Goal
Create a `DurableWorkflow` that starts some work, then "Pauses" until a human sends a "Signal" (either `APPROVE` or `REJECT`).

## Requirements
1.  **Status Enum:** Create a `Decision` enum with `PENDING`, `APPROVED`, and `REJECTED`.
2.  **The Workflow:** Create a `ReviewWorkflow` class with:
    *   `self.approval_event`: Use an `asyncio.Event` to simulate the "Pause."
    *   `self.decision`: Initially `Decision.PENDING`.
3.  **The Signal Handler:** Create a method `receive_signal(decision: Decision)`:
    *   Updates `self.decision`.
    *   Calls `self.approval_event.set()` to "wake up" the workflow.
4.  **The Run Method:** `async def run()`:
    *   Print "Starting work... waiting for human review."
    *   Wait for the event: `await self.approval_event.wait()`.
    *   Print the result based on the decision.

## Starter Code
```python
import asyncio
from enum import Enum

# --- 1. Define the Decisions ---
class Decision(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

# --- 2. The Durable Workflow (YOUR JOB) ---
class ReviewWorkflow:
    def __init__(self):
        # TODO: Initialize decision and asyncio.Event
        pass

    def receive_signal(self, decision: Decision):
        """
        TODO: 
        1. Set the internal decision.
        2. 'Wake up' the workflow by setting the event.
        """
        pass

    async def run(self):
        print("[WORKFLOW] Doing initial analysis...")
        await asyncio.sleep(1)
        
        print("[WORKFLOW] PAUSED: Awaiting human approval via signal...")
        
        # TODO: 
        # 1. Wait for the 'approval_event' to be set.
        # 2. Print the outcome based on self.decision.
        pass

# --- 3. Execution (The Simulation) ---
async def main():
    workflow = ReviewWorkflow()
    
    # 1. Start the workflow in the background (The Agent is working!)
    task = asyncio.create_task(workflow.run())
    
    # 2. Wait for a few seconds (Simulates the human being busy)
    await asyncio.sleep(3)
    
    # 3. A human partner clicks "APPROVE" in the UI
    print("
[UI] Human Partner clicks 'APPROVE'!")
    workflow.receive_signal(Decision.APPROVED)
    
    # 4. Wait for the workflow to finish
    await task

if __name__ == "__main__":
    asyncio.run(main())
```
