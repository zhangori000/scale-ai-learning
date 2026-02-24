# Solution: Child Workflows (The "Sub-Agent" Coordinator)

This solution demonstrates the "Fan-out/Fan-in" pattern. In `scale-agentex`, this is used to coordinate complex, multi-agent behaviors. Instead of a single "Mono-Agent" trying to do everything, we use a Parent Workflow to orchestrate many specialized Child Workflows.

## The Implementation

```python
import asyncio
import random
from typing import List

# --- 1. The Child Workflow (The Sub-Agent) ---
async def child_workflow(agent_type: str, prompt: str) -> str:
    """
    Simulates a specialized agent (e.g. Researcher, Coder, Writer).
    In real Temporal, this would be its own independent Workflow with its own ID.
    """
    print(f"  [CHILD] Agent '{agent_type}' starting analysis on '{prompt}'...")
    
    # 1. Simulate varying work times (1 to 3 seconds)
    # Since they run in parallel, the total time will be the MAX of these!
    work_time = random.uniform(1.0, 3.0)
    await asyncio.sleep(work_time)
    
    # 2. Return a formatted result
    result = f"[{agent_type.upper()}] says: For the prompt '{prompt}', my specialized finding is COMPLETE. (Took {work_time:.2f}s)"
    
    print(f"  [CHILD] Agent '{agent_type}' FINISHED.")
    return result

# --- 2. The Parent Workflow (The Coordinator) ---
class ParentWorkflow:
    def __init__(self):
        # In real Temporal, we'd have a list of ChildWorkflowHandles
        self.child_tasks: List[asyncio.Task] = []

    async def run(self, prompt: str):
        print(f"[PARENT] Received complex prompt: '{prompt}'")
        print("[PARENT] Spawning 3 specialized sub-agents in parallel...")

        # 1. FAN-OUT: Start multiple child tasks at the same time
        # We use asyncio.create_task() so they start running IMMEDIATELY 
        # without blocking each other.
        task_research = asyncio.create_task(child_workflow("researcher", prompt))
        task_coder = asyncio.create_task(child_workflow("coder", prompt))
        task_writer = asyncio.create_task(child_workflow("writer", prompt))

        # 2. FAN-IN: Wait for all of them to finish
        # asyncio.gather() blocks until all tasks in the list are complete.
        # It returns a list of all their results in order.
        print("[PARENT] All sub-agents are working. Waiting for results...")
        
        results = await asyncio.gather(
            task_research, 
            task_coder, 
            task_writer
        )

        # 3. CONSOLIDATE: Combine all the sub-agent findings into one final answer
        print("[PARENT] All results gathered. Consolidating final report...")
        final_report = "
---
".join(results)
        
        return f"FINAL ARCHITECTURAL REPORT FOR: '{prompt}'

{final_report}"

# --- 3. Execution (The Simulation) ---
async def main():
    start_time = asyncio.get_event_loop().time()
    
    # Create the parent orchestrator
    parent = ParentWorkflow()
    
    # Run the complex task
    # Observe: Even though 3 sub-agents work for ~2s each, 
    # the total time should ONLY be around 2-3s (not 6s).
    result = await parent.run("Build a new AI-powered Legal App")
    
    end_time = asyncio.get_event_loop().time()
    
    print("
" + "="*40)
    print("      CONSOLIDATED AGENT OUTPUT")
    print("="*40)
    print(result)
    print("="*40)
    print(f"
Total Execution Time: {end_time - start_time:.2f}s")
    # SUCCESS: You've implemented parallel coordination!

if __name__ == "__main__":
    asyncio.run(main())
```

### Key Takeaways from the Solution:

1.  **Concurrency vs. Parallelism:** By using `asyncio.create_task()`, we allow the sub-agents to work concurrently. This is the **most powerful performance boost** for agents that talk to multiple APIs or LLMs.
2.  **Isolation:** If the "Researcher" agent fails, the "Coder" and "Writer" can still finish their work. The Parent Workflow can then decide: "I'll try the researcher again," or "I'll proceed with just the coder and writer."
3.  **Durable Coordination:** In a real `scale-agentex` environment, if the server restarts while 3 child workflows are running, Temporal **remembers all of them**. When it reboots, it "re-joins" the parent to the children and continues exactly where it left off.
4.  **Why we use it for Agents:** Real-world agentic work is never a straight line. It's a complex "Tree" of sub-tasks. Child Workflows are the only way to manage this "Tree" at scale without losing control.
