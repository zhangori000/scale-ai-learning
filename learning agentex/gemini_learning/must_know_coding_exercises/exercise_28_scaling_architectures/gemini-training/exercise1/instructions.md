# Exercise 1: Building a Scaling-Aware Temporal Simulator

## Why this exercise exists
This exercise moves beyond simple sync vs async and asks you to model the **Worker Lifecycle** in a scaling Agentex environment. You will simulate how multiple workers share a task queue and how "Durable Execution" handles scaling-induced restarts.

## Problem
In `scaling_aware_temporal.py`, implement a simulator that can handle:
- **Variable Worker Replicas**: Multiple workers polling from the same queue.
- **Worker Crash/Scaling Events**: Workers can be added or removed mid-execution.
- **History-Based Replay**: Workers check a "Persistence Layer" to see if a task was already finished.
- **Idempotency Check**: Deduplicating duplicate task submissions from the API.

## Requirements
1. **The Server (Persistent Queue & History)**:
    - Maintain a `task_queue` of pending tasks.
    - Maintain a `task_history` of completed tasks.
2. **The Worker**:
    - Poll the server for a task.
    - Before processing, check the `task_history` (simulate idempotency).
    - If successful, record the result in `task_history`.
3. **The Simulator**:
    - Allow adding/removing workers while tasks are in the queue.
    - Log which worker processed which task.
    - Ensure no task is processed twice (idempotency).

## Starter Code
```python
import time
import random
from collections import deque

class TemporalServer:
    def __init__(self):
        self.queue = deque()
        self.history = {} # taskId -> result

    def submit_task(self, task_id, data):
        if task_id in self.history:
            return "ALREADY_DONE"
        self.queue.append((task_id, data))
        return "SUBMITTED"

class Worker:
    def __init__(self, worker_id, server):
        self.worker_id = worker_id
        self.server = server

    def poll_and_process(self):
        """Implement the poll and process logic with idempotency check"""
        pass

def run_scaling_simulation():
    server = TemporalServer()
    # 1. Submit 20 tasks
    # 2. Start 2 workers
    # 3. Mid-way, add 2 more workers (Scale Up)
    # 4. Mid-way, crash one worker (Scale Down/Failure)
    # 5. Verify all tasks completed exactly once.
    pass
```

## Interview Prompts
1. How does decoupling the "History" (Server) from the "Execution" (Worker) enable infinite horizontal scaling?
2. What happens to a task if a worker crashes *after* finishing the work but *before* updating the history? How does Agentex/Temporal handle this (Idempotency)?
