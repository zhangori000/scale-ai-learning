from __future__ import annotations

"""
Temporal-style mock demo where Task and Agent objects are created by a service layer.

This emulates real Agentex flow more closely:
Client -> Agentex Service API -> TemporalACP -> Temporal runtime/worker
"""

from agentex_service import AgentexClientMock, AgentexServiceMock
from run_worker import build_worker
from temporal_runtime import MiniTemporalServer, TemporalClient
from workflow import CoinbaseWorkflow, CoindeskWorkflow, MyAgentWorkflow


def _print_messages(service: AgentexServiceMock, task_id: str) -> None:
    print(f"\nMessages for {task_id}:")
    for idx, message in enumerate(service.get_task_messages(task_id), 1):
        print(f"{idx:02d}. {message}")


def main() -> None:
    task_queue = "agentex-temporal-task-queue"

    # Layer 1: Temporal runtime infra (server/client/worker).
    # In production these are often separate processes/services.
    server = MiniTemporalServer()
    temporal_client = TemporalClient(server=server)
    worker = build_worker(server=server, task_queue=task_queue)

    # Layer 2: Agentex API boundary and client SDK.
    # This is where we emulate "Client -> Agentex Server" rather than
    # manually building ACP parameter objects in caller code.
    service = AgentexServiceMock(
        server=server,
        temporal_client=temporal_client,
        worker=worker,
        default_task_queue=task_queue,
    )
    client = AgentexClientMock(service=service)

    # Startup registration:
    # - agent name -> workflow class
    # - agent name -> ACP adapter
    # - agent name -> task queue
    service.register_temporal_agent(
        agent_name="general-assistant",
        workflow_cls=MyAgentWorkflow,
        agent_id="agent-general-001",
    )
    service.register_temporal_agent(
        agent_name="coinbase-assistant",
        workflow_cls=CoinbaseWorkflow,
        agent_id="agent-coinbase-001",
    )
    service.register_temporal_agent(
        agent_name="coindesk-assistant",
        workflow_cls=CoindeskWorkflow,
        agent_id="agent-coindesk-001",
    )

    # Phase A: client creates tasks with simple API-style calls.
    # Internally the service constructs Agent/Task/CreateTaskParams and calls ACP.
    general_task = client.create_task(
        agent_name="general-assistant",
        task_name="general-chat",
        params={"topic": "temporal-acp-mapping"},
    )
    coinbase_task = client.create_task(
        agent_name="coinbase-assistant",
        task_name="coinbase-market-watch",
        params={"symbols": ["BTC", "ETH", "SOL"]},
    )
    coindesk_task = client.create_task(
        agent_name="coindesk-assistant",
        task_name="coindesk-news-watch",
        params={"topics": ["ETF", "REGULATION"]},
    )

    print("Created tasks:")
    print(general_task)
    print(coinbase_task)
    print(coindesk_task)
    print("\nqueue_size_after_create:", service.queue_size())

    # Pump worker loop so newly started workflows can execute initial steps.
    service.run_until_idle()

    # Phase B: client sends events by task_id.
    # Internally this becomes SendEventParams and then a workflow signal.
    client.send_event(general_task["task_id"], "hello from client ui")
    client.send_event(coinbase_task["task_id"], "scan")
    client.send_event(coindesk_task["task_id"], "scan")
    print("queue_size_after_event_batch_1:", service.queue_size())

    # Pump again so workflows handle first event batch.
    service.run_until_idle()

    # Phase C: completion events.
    client.send_event(general_task["task_id"], "done")
    client.send_event(coinbase_task["task_id"], "done")
    client.send_event(coindesk_task["task_id"], "done")
    print("queue_size_after_event_batch_2:", service.queue_size())

    # Final pump to completion.
    service.run_until_idle()

    print("\nTask snapshots:")
    # get_task() reads from service records, which are synced from workflow status.
    print(client.get_task(general_task["task_id"]))
    print(client.get_task(coinbase_task["task_id"]))
    print(client.get_task(coindesk_task["task_id"]))

    # User-visible messages by task.
    _print_messages(service, general_task["task_id"])
    _print_messages(service, coinbase_task["task_id"])
    _print_messages(service, coindesk_task["task_id"])


if __name__ == "__main__":
    main()
