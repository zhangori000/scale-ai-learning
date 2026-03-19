from __future__ import annotations

from datetime import datetime

from perf_control_plane.domain.entities.base import BaseModel


class ScenarioStepRequest(BaseModel):
    name: str
    endpoint_id: str
    description: str | None = None


class ScenarioCreateRequest(BaseModel):
    name: str
    owner_eid: str
    owner_name: str
    description: str | None = None
    is_starred: bool = False
    steps: list[ScenarioStepRequest]


class ScenarioStepResponse(BaseModel):
    name: str
    endpoint_id: str
    description: str | None = None


class ScenarioResponse(BaseModel):
    id: str
    name: str
    owner_eid: str
    owner_name: str
    description: str | None = None
    is_starred: bool
    steps: list[ScenarioStepResponse]
    created_at: datetime
    updated_at: datetime


class ScenarioStarResponse(BaseModel):
    id: str
    is_starred: bool
