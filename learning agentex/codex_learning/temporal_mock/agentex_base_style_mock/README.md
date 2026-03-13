# Agentex Base Async ACP Style Mock

This folder mirrors the real docs page:

- `docs/docs/acp/agentic/base.md`

Goal: show Base Async ACP without Temporal runtime concepts.

## What is modeled

- `acp.py`:
  - creates `acp = FastACP.create(acp_type="async", config=AsyncACPConfig(type="base"))`
- `handlers.py`:
  - manual handler implementation with:
    - `@acp.on_task_create`
    - `@acp.on_task_event_send`
    - `@acp.on_task_cancel`
- `mock_adk.py`:
  - tiny in-memory stand-in for:
    - `adk.state.create/get/update/delete`
    - `adk.messages.create`
- `demo_end_to_end.py`:
  - simulates incoming ACP routes:
    - `task/create`
    - `event/send`
    - `task/cancel`

## Why this differs from Temporal mock

- Base Async ACP:
  - you write ACP handlers directly
  - state transitions are explicit in handler code
  - no workflow class, no signals, no worker task queue
- Temporal Async ACP:
  - ACP routes are forwarded to workflow run/signal methods
  - Temporal runtime handles orchestration/task scheduling

## Run

```powershell
python "learning agentex\codex_learning\temporal_mock\agentex_base_style_mock\demo_end_to_end.py"
```

## Suggested reading order

1. `mock_fastacp.py` (route -> handler dispatch)
2. `acp.py` (ACP object construction)
3. `mock_adk.py` (state/messages APIs)
4. `handlers.py` (manual lifecycle logic)
5. `demo_end_to_end.py` (full flow)
