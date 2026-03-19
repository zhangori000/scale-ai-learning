from __future__ import annotations

from datetime import datetime

from perf_control_plane.api.schemas.runs import RunResponse
from perf_control_plane.api.schemas.test_plans import TestPlanRequest
from perf_control_plane.domain.entities.base import BaseModel


class FolderCreateRequest(BaseModel):
    name: str
    owner_eid: str
    owner_name: str
    description: str | None = None


class FolderResponse(BaseModel):
    id: str
    name: str
    owner_eid: str
    owner_name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class SavedTestConfigCreateRequest(BaseModel):
    folder_id: str
    owner_eid: str
    owner_name: str
    name: str
    description: str | None = None
    plan_template: TestPlanRequest


class SavedTestConfigResponse(BaseModel):
    id: str
    folder_id: str
    owner_eid: str
    owner_name: str
    name: str
    description: str | None = None
    plan_template: TestPlanRequest
    created_at: datetime
    updated_at: datetime


class FolderDetailsResponse(BaseModel):
    folder: FolderResponse
    configs: list[SavedTestConfigResponse]


class SavedTestConfigDetailsResponse(BaseModel):
    config: SavedTestConfigResponse
    recent_runs: list[RunResponse]


class RunFromSavedConfigRequest(BaseModel):
    requested_by: str
    test_plan_override: TestPlanRequest | None = None
