from __future__ import annotations

"""
Mock of the "Client -> Agentex Server -> ACP" layer.

Purpose:
- Client code should not manually build Agent/Task dataclasses.
- Agentex server layer should create Task context, map to ACP handlers,
  and call into Temporal-backed ACP.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import uuid

from acp import FastACP, TemporalACP, TemporalACPConfig
from acp_types import Agent, CreateTaskParams, Event, SendEventParams, Task, TextContent
from activities import MESSAGE_STORE
from temporal_runtime import AgentexWorker, MiniTemporalServer, TemporalClient


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentRegistration:
    """
    One registered agent in the service layer.

    Key point: each registered agent owns one TemporalACP adapter instance.
    That adapter knows which workflow class to start for this agent.
    """

    id: str
    name: str
    workflow_cls: type[Any]
    task_queue: str
    acp: TemporalACP


@dataclass
class TaskRecord:
    """
    Service-side task metadata, similar to what a real API would expose.

    We keep both `task_id` and `workflow_id` here to make the mapping explicit.
    In this mock they are usually the same string, but conceptually they are
    different identifiers.
    """

    id: str
    name: str
    agent_id: str
    agent_name: str
    workflow_id: str
    task_queue: str
    status: str
    created_at: str
    params: dict[str, Any] | None


class AgentexServiceMock:
    """
    Teaching version of the Agentex service boundary.

    Responsibilities:
    - hold agent registry (name -> ACP adapter)
    - create task records and build CreateTaskParams internally
    - send events by task_id and build SendEventParams internally
    - expose task status/messages to client callers
    """

    def __init__(
        self,
        server: MiniTemporalServer,
        temporal_client: TemporalClient,
        worker: AgentexWorker,
        default_task_queue: str,
    ) -> None:
        self.server = server
        self.temporal_client = temporal_client
        self.worker = worker
        self.default_task_queue = default_task_queue

        self.agents_by_name: dict[str, AgentRegistration] = {}
        self.tasks_by_id: dict[str, TaskRecord] = {}

    def register_temporal_agent(
        self,
        agent_name: str,
        workflow_cls: type[Any],
        task_queue: str | None = None,
        agent_id: str | None = None,
    ) -> AgentRegistration:
        """
        Startup-time registration.

        Real systems do similar wiring at process boot:
        - select workflow class
        - choose task queue
        - build the ACP adapter that translates ACP routes into Temporal calls
        """

        if agent_name in self.agents_by_name:
            raise ValueError(f"Agent already registered: {agent_name}")

        chosen_queue = task_queue or self.default_task_queue
        registration = AgentRegistration(
            id=agent_id or f"agent-{uuid.uuid4().hex[:8]}",
            name=agent_name,
            workflow_cls=workflow_cls,
            task_queue=chosen_queue,
            acp=FastACP.create(
                # FastACP picks/builds the concrete ACP adapter implementation.
                acp_type="async",
                config=TemporalACPConfig(type="temporal", task_queue=chosen_queue),
                temporal_client=self.temporal_client,
                workflow_cls=workflow_cls,
            ),
        )
        self.agents_by_name[agent_name] = registration
        return registration

    def create_task(
        self,
        agent_name: str,
        task_name: str,
        params: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> TaskRecord:
        """
        Emulates client calling Agentex "task/create".

        Notice what the client does NOT provide directly:
        - CreateTaskParams object
        - Agent dataclass
        - Task dataclass

        The service builds these internal protocol objects before calling ACP.
        """

        registration = self.agents_by_name.get(agent_name)
        if registration is None:
            raise KeyError(f"Unknown agent: {agent_name}")

        created_task_id = task_id or f"task-{uuid.uuid4().hex[:10]}"
        # Convert external API-ish inputs into ACP-typed parameters.
        agent = Agent(id=registration.id)
        task = Task(id=created_task_id, name=task_name, params=params)
        create_params = CreateTaskParams(agent=agent, task=task, params=params)

        # This is the ACP bridge point:
        # task/create -> TemporalACP.on_task_create -> TemporalClient.start_workflow.
        workflow_id = registration.acp.on_task_create(create_params)
        record = TaskRecord(
            id=created_task_id,
            name=task_name,
            agent_id=registration.id,
            agent_name=registration.name,
            workflow_id=workflow_id,
            task_queue=registration.task_queue,
            status="RUNNING",
            created_at=_utc_now_iso(),
            params=params,
        )
        self.tasks_by_id[created_task_id] = record
        return record

    def send_event(self, task_id: str, content: str) -> None:
        """
        Emulates client calling Agentex "event/send".

        Client sends only task_id + content.
        Service resolves the owning agent and builds SendEventParams internally.
        """

        record = self.tasks_by_id.get(task_id)
        if record is None:
            raise KeyError(f"Unknown task: {task_id}")

        registration = self.agents_by_name[record.agent_name]
        send_params = SendEventParams(
            agent=Agent(id=record.agent_id),
            task=Task(id=record.id, name=record.name, params=record.params),
            event=Event(content=TextContent(content=content)),
        )
        # ACP bridge point:
        # event/send -> TemporalACP.on_task_event_send -> TemporalClient.signal_workflow.
        registration.acp.on_task_event_send(send_params)

    def run_until_idle(self) -> None:
        # In real deployment worker polling is continuous.
        # Here we call it manually to keep the loop visible while learning.
        self.worker.run_until_idle()
        self._sync_task_statuses()

    def queue_size(self, task_queue: str | None = None) -> int:
        return self.server.queue_size(task_queue or self.default_task_queue)

    def get_task_record(self, task_id: str) -> TaskRecord:
        record = self.tasks_by_id.get(task_id)
        if record is None:
            raise KeyError(f"Unknown task: {task_id}")
        self._sync_one_task(record)
        return record

    def get_task_messages(self, task_id: str) -> list[str]:
        return list(MESSAGE_STORE.get(task_id, []))

    def _sync_task_statuses(self) -> None:
        for record in self.tasks_by_id.values():
            self._sync_one_task(record)

    def _sync_one_task(self, record: TaskRecord) -> None:
        # Service "task status" is derived from workflow execution status.
        execution = self.server.executions.get(record.workflow_id)
        if execution is None:
            return
        record.status = execution.status


class AgentexClientMock:
    """
    Teaching version of a client SDK calling Agentex Server APIs.

    It deliberately hides ACP/Temporal internals from caller code:
    caller uses high-level methods like create_task/send_event/get_task.
    """

    def __init__(self, service: AgentexServiceMock) -> None:
        self.service = service

    def create_task(
        self,
        agent_name: str,
        task_name: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = self.service.create_task(agent_name=agent_name, task_name=task_name, params=params)
        return {
            "task_id": record.id,
            "task_name": record.name,
            "agent_name": record.agent_name,
            "status": record.status,
            "created_at": record.created_at,
        }

    def send_event(self, task_id: str, content: str) -> None:
        self.service.send_event(task_id=task_id, content=content)

    def get_task(self, task_id: str) -> dict[str, Any]:
        record = self.service.get_task_record(task_id)
        return {
            "task_id": record.id,
            "task_name": record.name,
            "agent_name": record.agent_name,
            "status": record.status,
            "workflow_id": record.workflow_id,
        }
