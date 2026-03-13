from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from acp import acp
from acp_types import CancelTaskParams, CreateTaskParams, SendEventParams
from mock_adk import adk


# Archive store to show cleanup behavior in @acp.on_task_cancel.
ARCHIVE_STORE: dict[str, dict[str, Any]] = {}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_initial_state(params: CreateTaskParams) -> dict[str, Any]:
    mode = "general"
    if params.params and isinstance(params.params.get("mode"), str):
        mode = params.params["mode"].strip().lower()

    # Base async pattern: state is explicit and user-defined.
    return {
        "mode": mode,
        "workflow_stage": "welcome",
        "steps": ["welcome", "collect_info", "verify", "complete"],
        "current_step_index": 0,
        "step_data": {},
        "conversation_history": [],
        "complete": False,
        "metadata": {
            "created_at": _utc_now_iso(),
            "version": "1.0",
        },
        "last_updated": _utc_now_iso(),
    }


def _step_prompt(mode: str, step_name: str) -> str:
    if step_name == "collect_info":
        if mode == "coinbase":
            return "collect_info: send symbols to track (example: BTC ETH SOL)."
        if mode == "coindesk":
            return "collect_info: send topics to track (example: ETF REGULATION)."
        return "collect_info: tell me what you want to work on."
    if step_name == "verify":
        return "verify: reply 'yes' to confirm, or send corrections."
    if step_name == "complete":
        return "complete: workflow finished. Send task/cancel to cleanup state."
    return "welcome: send any message to continue."


@acp.on_task_create
async def on_task_create(params: CreateTaskParams) -> None:
    initial_state = _build_initial_state(params)
    state_record = await adk.state.create(
        task_id=params.task.id,
        agent_id=params.agent.id,
        state=initial_state,
    )

    mode = state_record.state["mode"]
    steps = state_record.state["steps"]
    await adk.messages.create(
        task_id=params.task.id,
        agent_id=params.agent.id,
        content=(
            f"Task created (mode={mode}). "
            f"Step 1/{len(steps)}: welcome. "
            "Send any message to move forward, or 'done' to finish."
        ),
    )


@acp.on_task_event_send
async def on_task_event_send(params: SendEventParams) -> None:
    state_record = await adk.state.get_by_task_and_agent(
        task_id=params.task.id,
        agent_id=params.agent.id,
    )
    if state_record is None:
        await adk.messages.create(
            task_id=params.task.id,
            agent_id=params.agent.id,
            content="No state found for task. Send task/create first.",
        )
        return

    state = state_record.state
    text = params.event.content.content.strip()
    lowered = text.lower()
    state["conversation_history"].append({"role": "user", "content": text, "at": _utc_now_iso()})

    if lowered in {"done", "complete", "stop"}:
        state["current_step_index"] = len(state["steps"]) - 1
        state["workflow_stage"] = "complete"
        state["complete"] = True
        state["last_updated"] = _utc_now_iso()
        await adk.state.update(state_id=state_record.id, state=state)
        await adk.messages.create(
            task_id=params.task.id,
            agent_id=params.agent.id,
            content="Marked complete from event input.",
        )
        return

    steps: list[str] = state["steps"]
    current_index: int = int(state["current_step_index"])
    current_step = steps[current_index]
    mode: str = state["mode"]

    if current_step == "welcome":
        state["step_data"]["welcome"] = {"first_input": text}
        state["current_step_index"] = 1
        state["workflow_stage"] = "collect_info"
        response = f"Moved to Step 2/{len(steps)}. {_step_prompt(mode, 'collect_info')}"
    elif current_step == "collect_info":
        state["step_data"]["collect_info"] = {"input": text}
        state["current_step_index"] = 2
        state["workflow_stage"] = "verify"
        response = f"Info saved ({mode}). Moved to Step 3/{len(steps)}. {_step_prompt(mode, 'verify')}"
    elif current_step == "verify":
        if lowered in {"yes", "y", "confirm"}:
            state["step_data"]["verify"] = {"approved": True, "input": text}
            state["current_step_index"] = 3
            state["workflow_stage"] = "complete"
            state["complete"] = True
            response = f"Verified. Step 4/{len(steps)} complete."
        else:
            state["step_data"]["verify"] = {"approved": False, "input": text}
            state["current_step_index"] = 1
            state["workflow_stage"] = "collect_info"
            response = (
                "Not verified. Returning to collect_info. "
                f"{_step_prompt(mode, 'collect_info')}"
            )
    else:
        response = _step_prompt(mode, "complete")

    state["last_updated"] = _utc_now_iso()
    await adk.state.update(state_id=state_record.id, state=state)
    await adk.messages.create(
        task_id=params.task.id,
        agent_id=params.agent.id,
        content=response,
    )


@acp.on_task_cancel
async def on_task_cancel(params: CancelTaskParams) -> None:
    state_record = await adk.state.get_by_task_and_agent(
        task_id=params.task.id,
        agent_id=params.agent.id,
    )
    if state_record is None:
        await adk.messages.create(
            task_id=params.task.id,
            agent_id=params.agent.id,
            content="Cancel received, but no state record exists.",
        )
        return

    # This mirrors docs guidance: optionally archive before cleanup.
    ARCHIVE_STORE[params.task.id] = dict(state_record.state)
    await adk.state.delete(state_id=state_record.id)
    await adk.messages.create(
        task_id=params.task.id,
        agent_id=params.agent.id,
        content=f"Task cancelled (reason={params.reason or 'unspecified'}). State deleted.",
    )
