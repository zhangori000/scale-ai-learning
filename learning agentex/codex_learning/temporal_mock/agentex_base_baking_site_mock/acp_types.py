from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Agent:
    id: str


@dataclass
class Task:
    id: str
    name: str | None = None
    params: dict[str, Any] | None = None


@dataclass
class TextContent:
    content: str


@dataclass
class Event:
    content: TextContent
    metadata: dict[str, Any] | None = None


@dataclass
class CreateTaskParams:
    agent: Agent
    task: Task
    params: dict[str, Any] | None = None


@dataclass
class SendEventParams:
    agent: Agent
    task: Task
    event: Event


@dataclass
class CancelTaskParams:
    agent: Agent
    task: Task
    reason: str | None = None
