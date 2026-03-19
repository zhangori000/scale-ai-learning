from __future__ import annotations

from pydantic import Field

from perf_control_plane.domain.entities.base import BaseModel
from perf_control_plane.domain.entities.test_plans import WorkloadRole


class LoadSegmentRequest(BaseModel):
    duration_seconds: int
    scenario_starts_per_second: int
    max_concurrency: int | None = None


class SteppedTimeLoadProfileRequest(BaseModel):
    initial_scenario_starts_per_second: int = 1000
    step_size: int = 250
    step_count: int = 3
    step_duration_seconds: int = 600
    max_concurrency: int | None = None


class BudgetLoadBandRequest(BaseModel):
    share: float
    scenario_starts_per_second: int
    max_concurrency: int | None = None


class BudgetStepLoadProfileRequest(BaseModel):
    part_count: int = 3
    initial_scenario_starts_per_second: int = 1000
    step_size: int = 250
    max_concurrency: int | None = None


class WorkloadExecutionSettingsRequest(BaseModel):
    load_segments: list[LoadSegmentRequest] = Field(default_factory=list)
    stepped_load_profile: SteppedTimeLoadProfileRequest | None = None
    budget_bands: list[BudgetLoadBandRequest] = Field(default_factory=list)
    budget_step_profile: BudgetStepLoadProfileRequest | None = None
    max_total_scenario_starts: int | None = None
    stop_when_budget_exhausted: bool = True


class ScenarioWorkloadRequest(BaseModel):
    name: str
    scenario_id: str
    scenario_name: str | None = None
    role: WorkloadRole
    measured_step_indexes_override: list[int] | None = None
    execution_settings: WorkloadExecutionSettingsRequest


class TestPlanRequest(BaseModel):
    name: str
    environment: str
    notes: str | None = None
    workloads: list[ScenarioWorkloadRequest]
