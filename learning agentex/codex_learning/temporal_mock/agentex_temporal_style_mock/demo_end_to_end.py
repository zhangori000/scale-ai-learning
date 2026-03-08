from __future__ import annotations

"""
End-to-end demo that uses the same split as docs:
- workflow.py (workflow definition)
- acp.py (protocol mapping to Temporal)
- run_worker.py (worker process)
"""

from acp import FastACP, TemporalACPConfig
from acp_types import Agent, CreateTaskParams, Event, SendEventParams, Task, TextContent
from activities import MESSAGE_STORE
from run_worker import build_worker
from temporal_runtime import MiniTemporalServer, TemporalClient
from workflow import MyAgentWorkflow, CoinbaseWorkflow, CoindeskWorkflow


def main() -> None:
    # "Temporal infrastructure" (teaching mock of server/client).
    server = MiniTemporalServer()
    temporal_client = TemporalClient(server=server)

    # "ACP server process" creates protocol mapping layers for multiple workflows.
    base_config = TemporalACPConfig(type="temporal", task_queue="agentex-temporal-task-queue")
    acp_general = FastACP.create(
        acp_type="async",
        config=base_config,
        temporal_client=temporal_client,
        workflow_cls=MyAgentWorkflow,
    )
    acp_coinbase = FastACP.create(
        acp_type="async",
        config=base_config,
        temporal_client=temporal_client,
        workflow_cls=CoinbaseWorkflow,
    )
    acp_coindesk = FastACP.create(
        acp_type="async",
        config=base_config,
        temporal_client=temporal_client,
        workflow_cls=CoindeskWorkflow,
    )

    # "Worker process" polls queue and executes workflow/activity code.
    worker = build_worker(server=server, task_queue="agentex-temporal-task-queue")

    agent = Agent(id="agent-123")
    task_general = Task(id="task-general-001", name="general-chat-task")
    task_coinbase = Task(id="task-coinbase-001", name="coinbase-briefing-task")
    task_coindesk = Task(id="task-coindesk-001", name="coindesk-briefing-task")

    # Start three workflow executions on the same task queue.
    workflow_general = acp_general.on_task_create(
        CreateTaskParams(agent=agent, task=task_general, params={"topic": "temporal-mapping"})
    )
    workflow_coinbase = acp_coinbase.on_task_create(
        CreateTaskParams(
            agent=agent,
            task=task_coinbase,
            params={"symbols": ["BTC", "ETH", "SOL"]},
        )
    )
    workflow_coindesk = acp_coindesk.on_task_create(
        CreateTaskParams(
            agent=agent,
            task=task_coindesk,
            params={"topics": ["ETF", "REGULATION"]},
        )
    )

    print("queue_size_after_starts:", server.queue_size("agentex-temporal-task-queue"))
    worker.run_until_idle()

    # Send events before running worker again to show shared queue interleaving.
    acp_general.on_task_event_send(
        SendEventParams(
            agent=agent,
            task=task_general,
            event=Event(content=TextContent(content="hello there")),
        )
    )
    acp_coinbase.on_task_event_send(
        SendEventParams(
            agent=agent,
            task=task_coinbase,
            event=Event(content=TextContent(content="scan")),
        )
    )
    acp_coindesk.on_task_event_send(
        SendEventParams(
            agent=agent,
            task=task_coindesk,
            event=Event(content=TextContent(content="scan")),
        )
    )
    print("queue_size_after_first_signal_batch:", server.queue_size("agentex-temporal-task-queue"))
    worker.run_until_idle()

    # Final signals to complete all three.
    acp_general.on_task_event_send(
        SendEventParams(
            agent=agent,
            task=task_general,
            event=Event(content=TextContent(content="done")),
        )
    )
    acp_coinbase.on_task_event_send(
        SendEventParams(
            agent=agent,
            task=task_coinbase,
            event=Event(content=TextContent(content="done")),
        )
    )
    acp_coindesk.on_task_event_send(
        SendEventParams(
            agent=agent,
            task=task_coindesk,
            event=Event(content=TextContent(content="done")),
        )
    )
    print("queue_size_after_completion_signal_batch:", server.queue_size("agentex-temporal-task-queue"))
    worker.run_until_idle()

    print("\n=== Execution Summary ===")
    for workflow_id in [workflow_general, workflow_coinbase, workflow_coindesk]:
        execution = server.executions[workflow_id]
        print(f"workflow_id={workflow_id} status={execution.status} result={execution.result}")

    print("\n=== Messages By Task ===")
    for task_id in [task_general.id, task_coinbase.id, task_coindesk.id]:
        print(f"\nTask {task_id}:")
        for idx, msg in enumerate(MESSAGE_STORE[task_id], 1):
            print(f"{idx:02d}. {msg}")

    print("\n=== Histories (trimmed to high-signal events) ===")
    interesting = {
        "WorkflowStarted",
        "SignalRequested",
        "SignalHandled",
        "WorkflowWaitingCondition",
        "WaitConditionSatisfied",
        "WorkflowCompleted",
    }
    for workflow_id in [workflow_general, workflow_coinbase, workflow_coindesk]:
        execution = server.executions[workflow_id]
        print(f"\nHistory for {workflow_id}:")
        idx = 0
        for event in execution.history:
            if event["event"] in interesting:
                idx += 1
                print(f"{idx:02d}. {event}")


if __name__ == "__main__":
    main()
