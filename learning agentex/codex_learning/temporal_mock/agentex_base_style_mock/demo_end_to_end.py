from __future__ import annotations

"""
End-to-end Base Async ACP demo.

Focus:
- ACP routes (`task/create`, `event/send`, `task/cancel`)
- Manual handler registration via decorators
- Explicit adk.state and adk.messages usage
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
from handlers import ARCHIVE_STORE  # noqa: F401 - ensures handlers module is imported/registered
from mock_adk import adk


def _print_messages(task_id: str) -> None:
    print(f"\nMessages for {task_id}:")
    for idx, message in enumerate(adk.messages.by_task.get(task_id, []), 1):
        print(f"{idx:02d}. {message.content}")


async def main() -> None:
    adk.reset()
    ARCHIVE_STORE.clear()

    agent = Agent(id="agent-123")
    task_general = Task(id="task-general-001", name="general-base-task")
    task_coinbase = Task(id="task-coinbase-001", name="coinbase-base-task")
    task_coindesk = Task(id="task-coindesk-001", name="coindesk-base-task")

    # 1) task/create route for three tasks
    await acp.dispatch(
        "task/create",
        CreateTaskParams(agent=agent, task=task_general, params={"mode": "general"}),
    )
    await acp.dispatch(
        "task/create",
        CreateTaskParams(agent=agent, task=task_coinbase, params={"mode": "coinbase"}),
    )
    await acp.dispatch(
        "task/create",
        CreateTaskParams(agent=agent, task=task_coindesk, params={"mode": "coindesk"}),
    )

    # 2) event/send route drives the workflow state machine forward
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_general,
            event=Event(content=TextContent(content="hello")),
        ),
    )
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_general,
            event=Event(content=TextContent(content="build me a checklist app")),
        ),
    )
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_general,
            event=Event(content=TextContent(content="yes")),
        ),
    )

    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_coinbase,
            event=Event(content=TextContent(content="hello")),
        ),
    )
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_coinbase,
            event=Event(content=TextContent(content="BTC ETH SOL")),
        ),
    )
    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_coinbase,
            event=Event(content=TextContent(content="yes")),
        ),
    )

    await acp.dispatch(
        "event/send",
        SendEventParams(
            agent=agent,
            task=task_coindesk,
            event=Event(content=TextContent(content="done")),
        ),
    )

    # 3) task/cancel route for cleanup demonstration
    await acp.dispatch(
        "task/cancel",
        CancelTaskParams(agent=agent, task=task_coinbase, reason="user closed page"),
    )

    print("=== Remaining State Records ===")
    for record_id, record in adk.state.records_by_id.items():
        print(
            f"- state_id={record_id} task={record.task_id} "
            f"stage={record.state.get('workflow_stage')} complete={record.state.get('complete')}"
        )

    print("\n=== Archived On Cancel ===")
    for task_id, archived_state in ARCHIVE_STORE.items():
        print(
            f"- task={task_id} archived_stage={archived_state.get('workflow_stage')} "
            f"keys={sorted(list(archived_state.keys()))}"
        )

    _print_messages(task_general.id)
    _print_messages(task_coinbase.id)
    _print_messages(task_coindesk.id)


if __name__ == "__main__":
    asyncio.run(main())
