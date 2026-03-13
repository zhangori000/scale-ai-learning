from __future__ import annotations

"""
End-to-end Base Async ACP demo for a baking website workflow.

Focus:
- ACP routes (`task/create`, `event/send`, `task/cancel`)
- Manual handler registration via decorators
- Explicit adk.state and adk.messages usage
- Async side effects for recipe search / inventory / order placement
"""

import asyncio

from acp import acp
from acp_types import (
    Agent,
    CancelTaskParams,
    CreateTaskParams,
    Event,
    SendEventParams,
    Task,
    TextContent,
)
from baking_services import ORDER_STORE, reset_order_store
from handlers import ARCHIVE_STORE  # noqa: F401 - import registers handlers
from mock_adk import adk


def _print_messages(task_id: str) -> None:
    print(f"\nMessages for {task_id}:")
    for idx, message in enumerate(adk.messages.by_task.get(task_id, []), 1):
        print(f"{idx:02d}. {message.content}")


async def main() -> None:
    adk.reset()
    ARCHIVE_STORE.clear()
    reset_order_store()

    agent = Agent(id="agent-baking-001")
    task_cake = Task(id="task-cake-001", name="birthday-cake-planning")
    task_vegan = Task(id="task-vegan-001", name="vegan-muffin-planning")
    task_cancelled = Task(id="task-cancel-001", name="cancelled-flow")

    # 1) task/create for three website sessions
    await acp.dispatch(
        "task/create",
        CreateTaskParams(agent=agent, task=task_cake, params={"mode": "recipe_planner"}),
    )
    await acp.dispatch(
        "task/create",
        CreateTaskParams(agent=agent, task=task_vegan, params={"mode": "recipe_planner"}),
    )
    await acp.dispatch(
        "task/create",
        CreateTaskParams(agent=agent, task=task_cancelled, params={"mode": "recipe_planner"}),
    )

    # 2) event/send drives each task's state machine independently
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_cake,
            event=Event(content=TextContent(content="hi baker")),
        ),
    )
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_cake,
            event=Event(
                content=TextContent(
                    content=(
                        "goal=birthday cake;skill=beginner;diet=any;servings=10;"
                        "pantry=flour,sugar,eggs,milk"
                    )
                )
            ),
        ),
    )
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_cake,
            event=Event(content=TextContent(content="1")),
        ),
    )
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_cake,
            event=Event(content=TextContent(content="yes")),
        ),
    )
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_cake,
            event=Event(content=TextContent(content="buy")),
        ),
    )

    # Vegan flow with no ordering
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_vegan,
            event=Event(content=TextContent(content="hello")),
        ),
    )
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_vegan,
            event=Event(
                content=TextContent(
                    content=(
                        "goal=vegan muffins;skill=beginner;diet=vegan;servings=12;"
                        "pantry=flour,sugar,berries,almond milk,vegetable oil,baking powder"
                    )
                )
            ),
        ),
    )
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_vegan,
            event=Event(content=TextContent(content="1")),
        ),
    )
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_vegan,
            event=Event(content=TextContent(content="yes")),
        ),
    )

    # 3) task/cancel for explicit cleanup behavior
    await acp.dispatch(
        "task/cancel",
        CancelTaskParams(agent=agent, task=task_cancelled, reason="user navigated away"),
    )
    await acp.dispatch(
        "task/cancel",
        CancelTaskParams(agent=agent, task=task_cake, reason="session closed after purchase"),
    )

    print("=== Remaining State Records ===")
    for record_id, record in adk.state.records_by_id.items():
        print(
            f"- state_id={record_id} task={record.task_id} "
            f"stage={record.state.get('workflow_stage')} complete={record.state.get('complete')} "
            f"mode={record.state.get('site_mode')}"
        )

    print("\n=== Archived On Cancel ===")
    for task_id, archived_state in ARCHIVE_STORE.items():
        print(
            f"- task={task_id} archived_stage={archived_state.get('workflow_stage')} "
            f"audit_entries={len(archived_state.get('audit_log', []))}"
        )

    print("\n=== Ingredient Orders ===")
    for order_id, order in ORDER_STORE.items():
        print(f"- {order_id}: items={order['items']} status={order['status']}")

    _print_messages(task_cake.id)
    _print_messages(task_vegan.id)
    _print_messages(task_cancelled.id)


if __name__ == "__main__":
    asyncio.run(main())
