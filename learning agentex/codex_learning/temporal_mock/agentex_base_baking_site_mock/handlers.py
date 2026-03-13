from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from acp import acp
from acp_types import CancelTaskParams, CreateTaskParams, SendEventParams
from baking_services import (
    build_timeline,
    check_missing_ingredients,
    search_recipes,
    submit_ingredient_order,
)
from mock_adk import adk


# Archive store to show cleanup behavior in @acp.on_task_cancel.
ARCHIVE_STORE: dict[str, dict[str, Any]] = {}
STEPS: list[str] = [
    "welcome",
    "collect_profile",
    "choose_recipe",
    "verify_plan",
    "checkout",
    "complete",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _profile_prompt() -> str:
    return (
        "collect_profile: send profile as "
        "'goal=<target>;skill=<beginner|intermediate|advanced>;"
        "diet=<any|vegan>;servings=<int>;pantry=<item1,item2,...>'."
    )


def _choose_recipe_prompt() -> str:
    return "choose_recipe: reply with recipe number (for example: 1)."


def _verify_prompt() -> str:
    return "verify_plan: reply 'yes' to continue, or 'no' to pick another recipe."


def _checkout_prompt() -> str:
    return "checkout: reply 'buy' to order missing ingredients or 'skip' to finish without ordering."


def _record_transition(state: dict[str, Any], from_stage: str, to_stage: str, reason: str) -> None:
    state["audit_log"].append(
        {
            "from": from_stage,
            "to": to_stage,
            "reason": reason,
            "at": _utc_now_iso(),
        }
    )


def _set_stage(state: dict[str, Any], next_stage: str, reason: str) -> None:
    current_stage = str(state["workflow_stage"])
    state["workflow_stage"] = next_stage
    state["current_step_index"] = STEPS.index(next_stage)
    _record_transition(state, current_stage, next_stage, reason)


def _append_conversation(state: dict[str, Any], role: str, content: str) -> None:
    state["conversation_history"].append(
        {
            "role": role,
            "content": content,
            "at": _utc_now_iso(),
            "stage": state["workflow_stage"],
        }
    )


def _safe_int(value: str, fallback: int) -> int:
    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return fallback


def _parse_profile(text: str) -> tuple[dict[str, Any], list[str]]:
    parsed: dict[str, str] = {}
    errors: list[str] = []
    for segment in [chunk.strip() for chunk in text.split(";") if chunk.strip()]:
        if "=" not in segment:
            errors.append(f"Missing '=' in '{segment}'.")
            continue
        key, raw_value = segment.split("=", 1)
        parsed[key.strip().lower()] = raw_value.strip()

    profile = {
        "goal": parsed.get("goal", ""),
        "skill": parsed.get("skill", "beginner").lower(),
        "diet": parsed.get("diet", "any").lower(),
        "servings": _safe_int(parsed.get("servings", "8"), 8),
        "pantry": [item.strip().lower() for item in parsed.get("pantry", "").split(",") if item.strip()],
    }

    if profile["skill"] not in {"beginner", "intermediate", "advanced"}:
        errors.append("skill must be beginner, intermediate, or advanced.")
    if profile["diet"] not in {"any", "vegan"}:
        errors.append("diet must be any or vegan.")
    if profile["servings"] < 1:
        errors.append("servings must be at least 1.")
    return profile, errors


def _parse_recipe_choice(text: str, candidate_count: int) -> int | None:
    normalized = text.strip().lower().replace("recipe", "").strip()
    if normalized.isdigit():
        choice = int(normalized)
        if 1 <= choice <= candidate_count:
            return choice - 1
    return None


def _format_candidates(candidates: list[dict[str, Any]]) -> str:
    lines = []
    for index, item in enumerate(candidates, 1):
        lines.append(
            f"{index}) {item['name']} | difficulty={item['difficulty']} "
            f"| serves={item['serves']} | missing={len(item['missing_ingredients'])}"
        )
    return "\n".join(lines)


def _build_initial_state(params: CreateTaskParams) -> dict[str, Any]:
    site_mode = "recipe_planner"
    if params.params and isinstance(params.params.get("mode"), str):
        site_mode = params.params["mode"].strip().lower()

    return {
        "site_mode": site_mode,
        "workflow_stage": "welcome",
        "steps": list(STEPS),
        "current_step_index": 0,
        "profile": {},
        "candidate_recipes": [],
        "selected_recipe": {},
        "plan": {},
        "checkout": {
            "needed_ingredients": [],
            "order": None,
        },
        "conversation_history": [],
        "audit_log": [],
        "complete": False,
        "metadata": {
            "created_at": _utc_now_iso(),
            "version": "1.0",
        },
        "last_updated": _utc_now_iso(),
    }


async def _send_agent_message(task_id: str, agent_id: str, state: dict[str, Any], content: str) -> None:
    _append_conversation(state, "agent", content)
    await adk.messages.create(
        task_id=task_id,
        agent_id=agent_id,
        content=content,
    )


@acp.on_task_create
async def on_task_create(params: CreateTaskParams) -> None:
    initial_state = _build_initial_state(params)
    state_record = await adk.state.create(
        task_id=params.task.id,
        agent_id=params.agent.id,
        state=initial_state,
    )

    site_mode = state_record.state["site_mode"]
    steps = state_record.state["steps"]
    welcome = (
        f"Task created for baking site mode={site_mode}. "
        f"Step 1/{len(steps)}: welcome. "
        f"Send any message to continue to profile collection. "
        f"You can send 'done' anytime to force completion."
    )
    await _send_agent_message(
        task_id=params.task.id,
        agent_id=params.agent.id,
        state=state_record.state,
        content=welcome,
    )
    await adk.state.update(state_id=state_record.id, state=state_record.state)


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
    _append_conversation(state, "user", text)

    if lowered in {"done", "complete", "stop"}:
        _set_stage(state, "complete", "forced_from_user")
        state["complete"] = True
        state["last_updated"] = _utc_now_iso()
        await adk.state.update(state_id=state_record.id, state=state)
        await _send_agent_message(
            task_id=params.task.id,
            agent_id=params.agent.id,
            state=state,
            content="Marked complete from event input. Send task/cancel to cleanup state.",
        )
        return

    current_stage = str(state["workflow_stage"])
    response: str

    if current_stage == "welcome":
        _set_stage(state, "collect_profile", "welcome_acknowledged")
        response = f"Step 2/{len(STEPS)}. {_profile_prompt()}"

    elif current_stage == "collect_profile":
        profile, errors = _parse_profile(text)
        if errors:
            response = "Profile format issues: " + " ".join(errors) + " " + _profile_prompt()
        else:
            state["profile"] = profile
            recipes = await search_recipes(profile)
            pantry = set(profile["pantry"])

            async def enrich_recipe(recipe: Any) -> dict[str, Any]:
                missing = await check_missing_ingredients(recipe, pantry)
                return {
                    "name": recipe.name,
                    "difficulty": recipe.difficulty,
                    "dietary": recipe.dietary,
                    "serves": recipe.serves,
                    "bake_minutes": recipe.bake_minutes,
                    "ingredients": list(recipe.ingredients),
                    "missing_ingredients": missing,
                }

            enriched_candidates = await asyncio.gather(
                *(enrich_recipe(recipe) for recipe in recipes[:4])
            )
            enriched_candidates.sort(
                key=lambda item: (len(item["missing_ingredients"]), item["bake_minutes"])
            )
            state["candidate_recipes"] = enriched_candidates[:3]

            _set_stage(state, "choose_recipe", "profile_collected")
            response = (
                f"Step 3/{len(STEPS)} candidates:\n"
                f"{_format_candidates(state['candidate_recipes'])}\n"
                f"{_choose_recipe_prompt()}"
            )

    elif current_stage == "choose_recipe":
        candidates = state["candidate_recipes"]
        if not candidates:
            _set_stage(state, "collect_profile", "no_candidates")
            response = "No candidates available. " + _profile_prompt()
        else:
            choice_index = _parse_recipe_choice(text, len(candidates))
            if choice_index is None:
                response = "Could not parse choice. " + _choose_recipe_prompt()
            else:
                selected_recipe = dict(candidates[choice_index])
                timeline = await build_timeline(
                    selected_recipe,
                    state["profile"].get("skill", "beginner"),
                )
                state["selected_recipe"] = selected_recipe
                state["plan"] = {
                    "timeline": timeline,
                    "servings": state["profile"].get("servings", selected_recipe["serves"]),
                }
                _set_stage(state, "verify_plan", "recipe_selected")
                response = (
                    f"Step 4/{len(STEPS)} selected '{selected_recipe['name']}'. "
                    f"Timeline={timeline['total_minutes']} min. "
                    f"Missing ingredients={selected_recipe['missing_ingredients']}. "
                    f"{_verify_prompt()}"
                )

    elif current_stage == "verify_plan":
        if lowered in {"yes", "y", "confirm"}:
            missing = list(state.get("selected_recipe", {}).get("missing_ingredients", []))
            if missing:
                state["checkout"]["needed_ingredients"] = missing
                _set_stage(state, "checkout", "plan_verified_missing_items")
                response = (
                    f"Step 5/{len(STEPS)} missing ingredients: {missing}. "
                    f"{_checkout_prompt()}"
                )
            else:
                _set_stage(state, "complete", "plan_verified_no_missing_items")
                state["complete"] = True
                response = (
                    f"Step 6/{len(STEPS)} complete. You already have all ingredients. "
                    "Send task/cancel to cleanup state."
                )
        elif lowered in {"no", "n", "change"}:
            _set_stage(state, "choose_recipe", "plan_rejected")
            response = (
                f"Returning to Step 3/{len(STEPS)}.\n"
                f"{_format_candidates(state['candidate_recipes'])}\n"
                f"{_choose_recipe_prompt()}"
            )
        else:
            response = _verify_prompt()

    elif current_stage == "checkout":
        if lowered in {"buy", "order", "yes"}:
            missing_items = list(state["checkout"]["needed_ingredients"])
            order = await submit_ingredient_order(params.task.id, missing_items)
            state["checkout"]["order"] = order
            _set_stage(state, "complete", "order_placed")
            state["complete"] = True
            response = (
                f"Step 6/{len(STEPS)} complete. Order placed: {order['order_id']} "
                f"for items={order['items']}."
            )
        elif lowered in {"skip", "no"}:
            _set_stage(state, "complete", "order_skipped")
            state["complete"] = True
            response = f"Step 6/{len(STEPS)} complete without placing an ingredient order."
        else:
            response = _checkout_prompt()

    else:
        response = "Workflow already complete. Send task/cancel to cleanup state."

    state["last_updated"] = _utc_now_iso()
    await adk.state.update(state_id=state_record.id, state=state)
    await _send_agent_message(
        task_id=params.task.id,
        agent_id=params.agent.id,
        state=state,
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
