from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserRecord:
    user_id: str
    name: str
    email: str


@dataclass
class TaskRecord:
    task_id: str
    user_id: str
    description: str
    category: str | None = None
    classification_error: bool = False


@dataclass
class IngestResult:
    status: str
    job_id: str
    users_count: int
    tasks_count: int
    classified_tasks_count: int
    errors: list[str] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)
    tasks: list[dict[str, Any]] | None = None
