# Agentex Base Async ACP Baking Site Mock

This folder is a from-scratch learning implementation of Base Async ACP for a baking website assistant.

It mirrors the ideas from:
- `scale-agentex/agentex/docs/docs/acp/agentic/base.md`

No real Agentex SDK code is used here; everything is implemented locally so the control flow is visible.

## What this teaches

- Manual ACP lifecycle handling:
  - `@acp.on_task_create`
  - `@acp.on_task_event_send`
  - `@acp.on_task_cancel`
- Explicit state CRUD:
  - `adk.state.create/get_by_task_and_agent/update/delete`
- Explicit messaging:
  - `adk.messages.create`
- Multi-step workflow state machine:
  - `welcome -> collect_profile -> choose_recipe -> verify_plan -> checkout -> complete`
- Async side effects from handlers:
  - recipe lookup
  - pantry gap detection
  - timeline estimation
  - ingredient order placement

## Files

- `mock_fastacp.py`: tiny route dispatcher + handler decorators
- `acp.py`: creates the `acp` object using `type="base"`
- `acp_types.py`: small parameter models for create/send/cancel routes
- `mock_adk.py`: in-memory state/message APIs
- `baking_services.py`: async side-effect functions and static recipe catalog
- `handlers.py`: full workflow logic and state transitions
- `demo_end_to_end.py`: runs multiple tasks through the workflow

## Run

```powershell
python "learning agentex\codex_learning\temporal_mock\agentex_base_baking_site_mock\demo_end_to_end.py"
```

## Reading order

1. `mock_fastacp.py`
2. `mock_adk.py`
3. `baking_services.py`
4. `handlers.py`
5. `demo_end_to_end.py`

## Extension ideas

- Add a `decorate` step for frosting/theme planning.
- Track partial form updates with `event.metadata` and merge in handler code.
- Add retry wrappers in `baking_services.py` to model flaky API calls.
