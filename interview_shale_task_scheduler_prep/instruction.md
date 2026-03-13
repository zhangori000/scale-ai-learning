# Shale Task Scheduler Interview Prep (Part 1 + Part 2)

This folder is a focused prep package for the Shale/BigBrain task scheduling question.

## Why this implementation can earn a strong signal

It is designed to show interviewers that you:
- Read constraints carefully.
- Prioritize correctness over premature optimization.
- Handle edge cases explicitly (empty queue, blocked parents, missing dependencies, cycles).
- Write clean tests that prove behavior.

## Problem summary

Part 1:
- `AddTasks(tasks)` receives tasks with `id` and `deadline`.
- `ConsumeTask()` returns and removes the task with smallest deadline.
- If no tasks exist, return `"NO_TASK_TO_RETURN"`.

Part 2:
- Tasks now include `subtasks`.
- A task is eligible only when all subtasks are already consumed.
- `ConsumeTask()` returns the earliest deadline among eligible tasks.
- If no eligible task exists, return `"NO_TASK_TO_RETURN"`.
- This prep supports both:
  - nested subtask objects
  - subtasks provided as only IDs (common interview variant)

## Files

- `task_scheduler.py`
  - `TaskServicePart1` for Part 1
  - `TaskServicePart2` for Part 2
  - shared constant: `NO_TASK_TO_RETURN`

- `test_task_scheduler.py`
  - Unit tests for both parts and key edge cases.

- `demo.py`
  - Simple runnable walkthrough.

## Interview assumptions (state these out loud)

- Tie-break on equal deadlines is insertion order.
- IDs are expected to be unique for active tasks.
- If a task depends on an undefined ID, it remains blocked until that ID is later added with a deadline.
- Cycles have no eligible task; therefore `ConsumeTask()` returns `"NO_TASK_TO_RETURN"`.

## How Part 2 works

- Keep all tasks in a graph:
  - each node tracks dependencies (subtasks) and dependents (parents).
- Maintain a min-heap of currently eligible tasks by deadline.
- On `ConsumeTask()`:
  - pop the earliest eligible task
  - mark it consumed
  - re-check and enqueue its dependents if they become unblocked

This is correctness-first and easy to reason about.

## What to say in the interview

Use this short script:
1. "I model this as dependency-aware scheduling."
2. "I keep a min-heap for the earliest-deadline candidate and a graph for subtask dependencies."
3. "A task is consumable iff all its dependencies are already consumed."
4. "When I consume a task, I only need to revisit its parents."
5. "I wrote tests for nested subtasks, ID-only subtasks, missing dependencies, and cycles."

## Quick run

From this folder:

```bash
python demo.py
python -m unittest test_task_scheduler.py -v
```
