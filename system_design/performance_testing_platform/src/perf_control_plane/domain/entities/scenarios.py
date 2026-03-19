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

class LoadSegmentEntity(BaseModel):
    duration_seconds: int
    scenario_starts_per_second: int
    max_concurrency: int | None = None


class SteppedLoadProfileEntity(BaseModel):
    initial_scenario_starts_per_second: int = 1000
    step_size: int = 250
    step_count: int = 3
    step_duration_seconds: int = 600
    max_concurrency: int | None = None

    @model_validator(mode="after")
    def validate_profile(self) -> "SteppedLoadProfileEntity":
        if self.initial_scenario_starts_per_second <= 0:
            raise ValueError("initial_scenario_starts_per_second must be positive")
        if self.step_size < 0:
            raise ValueError("step_size must be zero or positive")
        if self.step_count <= 0:
            raise ValueError("step_count must be positive")
        if self.step_duration_seconds <= 0:
            raise ValueError("step_duration_seconds must be positive")
        return self

    def to_load_segments(self) -> list[LoadSegmentEntity]:
        return [
            LoadSegmentEntity(
                duration_seconds=self.step_duration_seconds,
                scenario_starts_per_second=(
                    self.initial_scenario_starts_per_second + (index * self.step_size)
                ),
                max_concurrency=self.max_concurrency,
            )
            for index in range(self.step_count)
        ]

    def total_duration_seconds(self) -> int:
        return self.step_count * self.step_duration_seconds


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
