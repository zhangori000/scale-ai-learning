# Exercise 5: The Distributed Orchestrator (Workers, Tasks, and Retries)

## Goal
In this exercise, you will move beyond a single-process "Replay Engine" and build a **Distributed Task Orchestrator**. This simulates how Temporal actually manages work across multiple machines.

In `agentex`, workflows aren't just functions that run; they are orchestrated processes that:
1.  **Queue Tasks**: Workflows push activity requests into a task queue.
2.  **Workers Poll**: Independent worker processes pull tasks from the queue and execute them.
3.  **Automatic Retries**: If a worker fails, the orchestrator detects the timeout and re-queues the task for another worker.

## The Problem
If an activity involves an external API (like OpenAI in `agentex-python`), it will fail occasionally. You need a system that:
-   Decouples the **Request** from the **Execution**.
-   Handles **Retry Policies** (exponential backoff).
-   Supports **Heartbeating** (letting the orchestrator know the task is still alive).

## Your Tasks

Implement the following in `solution.py`:

1.  **`TaskQueue`**: A thread-safe (or simulated) queue where activities wait to be picked up.
2.  **`Worker`**:
    *   Polls the `TaskQueue`.
    *   Executes the activity.
    *   Can "fail" randomly (to test your retry logic).
3.  **`Orchestrator`**:
    *   Accepts activity requests.
    *   Manages a **Retry Policy** (max_attempts, backoff).
    *   Tracks task state (Pending, Running, Completed, Failed).
4.  **`Workflow`**:
    *   A high-level function that submits multiple activities and waits for results (synchronously or with a simple callback).

## Requirements
*   **Retry Simulation**: If an activity fails, the Orchestrator should re-schedule it until `max_attempts` is reached.
*   **Backoff Logic**: Wait longer between each retry (e.g., 1s, 2s, 4s).
*   **Concurrency**: Use Python's `threading` or `asyncio` to run multiple Workers simultaneously.

## Example Usage
```python
# Retry 3 times with exponential backoff
policy = RetryPolicy(max_attempts=3, initial_interval=1)

@activity(retry_policy=policy)
def unreliable_llm_call(prompt):
    if random.random() < 0.7: # 70% failure rate
        raise Exception("API Timeout")
    return f"Response to {prompt}"

orchestrator = Orchestrator()
worker1 = Worker(orchestrator, name="Worker-A")
worker2 = Worker(orchestrator, name="Worker-B")

# Start workers in the background
worker1.start()
worker2.start()

# Submit workflow
result = orchestrator.execute_workflow(my_workflow, "Analyze this text")
```

## Why this matters for `agentex`?
`agentex` workers are separate processes. When a `TemporalTaskService` sends an event, it's hitting the Temporal Server (the orchestrator). The actual work happens on a Worker. If your worker process crashes during a heavy LLM task, Temporal's retry policy and task queue ensure that another worker picks up the job without losing data.
