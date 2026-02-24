# Exercise: Child Workflows (The "Sub-Agent" Coordinator)

In `scale-agentex`, a "Task" might need help from many different specialized agents. To do this efficiently, we don't want to run them one by one. We want to **Fan-out** (run them all at once) and then **Fan-in** (combine the results).

## The Goal
Create a `ParentWorkflow` that spawns 3 `ChildWorkflows` (Sub-Agents), waits for all of them to finish, and combines their findings.

## Requirements
1.  **The Child Workflow:** Create a function `child_workflow(agent_type: str, data: str)`:
    *   Sleeps for a random duration (1-3 seconds).
    *   Returns a specialized string like `[Agent {agent_type}] says: {data}`.
2.  **The Manager:** Create a `WorkflowManager` that:
    *   Can `execute_child_workflow(coro)`: This should start a child task and return the `asyncio.Task` object immediately.
    *   Can `gather_results(tasks: list)`: This should wait for all tasks in the list to finish and return their results.
3.  **The Parent Workflow:** Create a `ParentWorkflow` that:
    *   "Spawns" three children: `researcher`, `coder`, and `writer`.
    *   Wait for all three.
    *   Joins the results with a newline.

## Starter Code
```python
import asyncio
import random
from typing import List

# --- 1. The Child Workflow (The Sub-Agent) ---
async def child_workflow(agent_type: str, prompt: str) -> str:
    # TODO:
    # 1. Print "[CHILD] Agent {type} starting analysis on '{prompt}'..."
    # 2. sleep for random.randint(1, 3) seconds.
    # 3. Return the result string.
    pass

# --- 2. The Parent Workflow (The Coordinator) ---
class ParentWorkflow:
    def __init__(self):
        self.child_tasks = []

    async def run(self, prompt: str):
        print(f"[PARENT] Received complex prompt: '{prompt}'")
        print("[PARENT] Spawning 3 specialized sub-agents in parallel...")

        # TODO: 
        # 1. Start 3 child_workflow tasks using asyncio.create_task().
        # 2. Store them in self.child_tasks.
        # 3. Wait for all 3 to finish using asyncio.gather().
        # 4. Print and return the combined result.
        pass

# --- 3. Execution (The Simulation) ---
async def main():
    start_time = asyncio.get_event_loop().time()
    
    parent = ParentWorkflow()
    result = await parent.run("Write a new AI app")
    
    end_time = asyncio.get_event_loop().time()
    
    print("
--- Final Consolidated Report ---")
    print(result)
    print(f"
Total Execution Time: {end_time - start_time:.2f}s")
    # Hint: Since they run in parallel, the total time should be 
    # the time of the SLOWEST child, not the SUM of all children.

if __name__ == "__main__":
    asyncio.run(main())
```
