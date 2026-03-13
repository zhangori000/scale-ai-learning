from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class StateRecord:
    id: str
    task_id: str
    agent_id: str
    state: dict[str, Any]


@dataclass
class MessageRecord:
    id: str
    task_id: str
    agent_id: str
    content: str
    created_at: str


class MockStateAPI:
    """
    Minimal in-memory stand-in for adk.state.

    Real Agentex stores state in persistent infra.
    This learning mock keeps the same shape but stores data in dicts.
    """

    def __init__(self) -> None:
        self.records_by_id: dict[str, StateRecord] = {}
        self.index_by_task_agent: dict[tuple[str, str], str] = {}

    async def create(self, task_id: str, agent_id: str, state: dict[str, Any]) -> StateRecord:
        state_id = str(uuid.uuid4())
        record = StateRecord(
            id=state_id,
            task_id=task_id,
            agent_id=agent_id,
            state=dict(state),
        )
        self.records_by_id[state_id] = record
        self.index_by_task_agent[(task_id, agent_id)] = state_id
        return record

    async def get_by_task_and_agent(self, task_id: str, agent_id: str) -> StateRecord | None:
        state_id = self.index_by_task_agent.get((task_id, agent_id))
        if state_id is None:
            return None
        return self.records_by_id.get(state_id)

    async def update(self, state_id: str, state: dict[str, Any]) -> StateRecord:
        record = self.records_by_id.get(state_id)
        if record is None:
            raise KeyError(f"State not found: {state_id}")
        record.state = dict(state)
        return record

    async def delete(self, state_id: str) -> None:
        record = self.records_by_id.pop(state_id, None)
        if record is None:
            return
        key = (record.task_id, record.agent_id)
        if self.index_by_task_agent.get(key) == state_id:
            del self.index_by_task_agent[key]


class MockMessagesAPI:
    """Minimal in-memory stand-in for adk.messages."""

    def __init__(self) -> None:
        self.by_task: dict[str, list[MessageRecord]] = defaultdict(list)

    async def create(self, task_id: str, agent_id: str, content: str) -> MessageRecord:
        record = MessageRecord(
            id=str(uuid.uuid4()),
            task_id=task_id,
            agent_id=agent_id,
            content=content,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.by_task[task_id].append(record)
        return record


class MockADK:
    def __init__(self) -> None:
        self.state = MockStateAPI()
        self.messages = MockMessagesAPI()

    def reset(self) -> None:
        self.state = MockStateAPI()
        self.messages = MockMessagesAPI()


adk = MockADK()
