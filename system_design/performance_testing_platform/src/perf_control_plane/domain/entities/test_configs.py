from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field

from perf_control_plane.domain.entities.base import BaseModel
from perf_control_plane.domain.entities.runs import PerfTestRunEntity
from perf_control_plane.domain.entities.test_plans import TestPlanEntity


class TestConfigFolderEntity(BaseModel):
    id: str
    name: str
    owner_eid: str
    owner_name: str
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FolderDetailsEntity(BaseModel):
    folder: TestConfigFolderEntity
    configs: list["SavedTestConfigEntity"] = Field(default_factory=list)


class SavedTestConfigEntity(BaseModel):
    id: str
    folder_id: str
    owner_eid: str
    owner_name: str
    name: str
    description: str | None = None
    plan_template: TestPlanEntity
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SavedTestConfigDetailsEntity(BaseModel):
    config: SavedTestConfigEntity
    recent_runs: list[PerfTestRunEntity] = Field(default_factory=list)
