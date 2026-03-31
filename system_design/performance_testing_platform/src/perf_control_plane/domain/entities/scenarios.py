from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field, model_validator

from perf_control_plane.domain.entities.base import BaseModel


class ScenarioStepEntity(BaseModel):
    name: str
    endpoint_id: str
    description: str | None = None


class ScenarioEntity(BaseModel):
    id: str
    name: str
    owner_eid: str
    owner_name: str
    description: str | None = None
    is_starred: bool = False
    steps: list[ScenarioStepEntity]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_steps(self) -> "ScenarioEntity":
        if not self.steps:
            raise ValueError("scenarios require at least one step")
        return self


class ResolvedScenarioStepEntity(BaseModel):
    step_index: int
    name: str
    endpoint_id: str
    service_name: str
    method: str
    path: str
    base_url: str | None = None
    owner_team: str


class MeasuredTargetEntity(BaseModel):
    step_index: int
    request_name: str
    endpoint_id: str
    path: str
