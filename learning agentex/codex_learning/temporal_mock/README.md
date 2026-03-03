# Mini Temporal (Mock) for Learning

This folder contains a tiny, runnable mock of Temporal to explain core concepts:

- `workflow`: orchestration logic (decision making)
- `activity`: side-effect logic (external/API/DB work)
- `task queue`: where workflow/activity tasks are scheduled
- `worker`: process that polls tasks and executes them
- `event history`: append-only log of what happened

## Key definitions

### Side effect
A side effect is anything that changes the outside world or depends on it:
- charging a credit card
- writing to a database
- sending email
- calling an external API

In Temporal, side effects belong in **activities**, not workflow logic.

### Workflow
A workflow is durable orchestration logic:
- it decides *what should happen next*
- it calls activities
- it tracks state/progress
- it should be deterministic (same history => same decisions)

### Activity
An activity is the worker-executed side-effect function:
- can fail/retry
- can be long-running
- can touch external systems

### Worker + task queue
Workers poll the queue and run:
- workflow tasks (advance orchestration)
- activity tasks (perform side effects)

## Run the demo

```powershell
python "learning agentex\codex_learning\temporal_mock\mini_temporal.py"
```

## What to observe

1. `charge_card` fails on first attempt, then succeeds on retry.
2. Workflow does not directly write DB/send email; activities do.
3. Event history clearly shows:
   - workflow start
   - activity scheduled/completed/failed/retried
   - workflow completion

## Important limitation

This is an in-memory teaching mock, not real durability.
Real Temporal persists workflow history in Temporal Server and can recover across process crashes.
