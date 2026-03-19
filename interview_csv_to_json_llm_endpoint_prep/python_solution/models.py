from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UserRecord:
    row_index: int
    id: str
    name: str


@dataclass(frozen=True)
class TaskRecord:
    row_index: int
    id: str
    task: str


@dataclass(frozen=True)
class IngestManifest:
    job_id: str
    users_json_path: str
    tasks_json_path: str
    manifest_json_path: str
    users_count: int
    tasks_count: int


@dataclass(frozen=True)
class ClassificationResult:
    job_id: str
    dataset: str
    row_index: int
    label: str
    label_options: list[str]
    record: dict[str, str | int]
    classification_json_path: str
    prompt: str


@dataclass(frozen=True)
class IngestResponse:
    status: str
    manifest: IngestManifest
    errors: list[str] = field(default_factory=list)
