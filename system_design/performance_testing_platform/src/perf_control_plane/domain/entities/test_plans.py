from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from perf_control_plane.domain.entities.base import BaseModel
from perf_control_plane.domain.entities.load_profiles import (
    BudgetSegmentEntity,
    BudgetRampProfileEntity,
    TimeRampProfileEntity,
    TimeSegmentEntity,
)
from perf_control_plane.domain.entities.scenarios import (
    MeasuredTargetEntity,
    ResolvedScenarioStepEntity,
)


class WorkloadRole(str, Enum):
    SETUP = "setup"
    MEASURED = "measured"
    TEARDOWN = "teardown"


class WorkloadExecutionSettingsEntity(BaseModel):
    time_segments: list[TimeSegmentEntity] = Field(default_factory=list)
    time_ramp_profile: TimeRampProfileEntity | None = None
    budget_segments: list[BudgetSegmentEntity] = Field(default_factory=list)
    budget_ramp_profile: BudgetRampProfileEntity | None = None
    max_total_scenario_starts: int | None = None
    stop_when_budget_exhausted: bool = True

    @model_validator(mode="after")
    def validate_load_shape(self) -> "WorkloadExecutionSettingsEntity":
        configured_profiles = [
            bool(self.time_segments),
            self.time_ramp_profile is not None,
            bool(self.budget_segments),
            self.budget_ramp_profile is not None,
        ]
        if sum(configured_profiles) != 1:
            raise ValueError(
                "exactly one load profile family must be configured per workload"
            )
        if self.max_total_scenario_starts is not None and self.max_total_scenario_starts <= 0:
            raise ValueError("max_total_scenario_starts must be positive when provided")
        if self.uses_budget_profile() and self.max_total_scenario_starts is None:
            raise ValueError(
                "budget-based workload profiles require max_total_scenario_starts"
            )
        if self.budget_segments:
            total_share = sum(item.share for item in self.budget_segments)
            if abs(total_share - 1.0) > 1e-6:
                raise ValueError("budget segment shares must sum to 1.0")
        return self

    def uses_time_profile(self) -> bool:
        return bool(self.time_segments) or self.time_ramp_profile is not None

    def uses_budget_profile(self) -> bool:
        return bool(self.budget_segments) or self.budget_ramp_profile is not None

    def effective_time_segments(self) -> list[TimeSegmentEntity]:
        if self.time_segments:
            return self.time_segments
        if self.time_ramp_profile is None:
            return []
        return self.time_ramp_profile.to_time_segments()

    def effective_budget_segments(self) -> list[BudgetSegmentEntity]:
        if self.budget_segments:
            return self.budget_segments
        if self.budget_ramp_profile is None:
            return []
        return self.budget_ramp_profile.to_budget_segments()

    def load_profile_family(self) -> str:
        if self.time_segments:
            return "time_segments"
        if self.time_ramp_profile is not None:
            return "time_ramp"
        if self.budget_segments:
            return "budget_segments"
        if self.budget_ramp_profile is not None:
            return "budget_ramp"
        return "unknown"


class ScenarioWorkloadEntity(BaseModel):
    name: str
    scenario_id: str
    scenario_name: str | None = None
    role: WorkloadRole
    measured_step_indexes_override: list[int] | None = None
    execution_settings: WorkloadExecutionSettingsEntity

    @model_validator(mode="after")
    def validate_measurement_override(self) -> "ScenarioWorkloadEntity":
        if self.measured_step_indexes_override is None:
            return self
        if any(index < 0 for index in self.measured_step_indexes_override):
            raise ValueError("measured_step_indexes_override cannot contain negative indexes")
        if len(set(self.measured_step_indexes_override)) != len(
            self.measured_step_indexes_override
        ):
            raise ValueError("measured_step_indexes_override cannot contain duplicates")
        if self.role == WorkloadRole.SETUP and self.measured_step_indexes_override:
            raise ValueError("setup workloads cannot define measured_step_indexes_override")
        return self


class TestPlanEntity(BaseModel):
    name: str
    environment: str
    notes: str | None = None
    workloads: list[ScenarioWorkloadEntity]

    @model_validator(mode="after")
    def validate_plan(self) -> "TestPlanEntity":
        if not self.workloads:
            raise ValueError("test plans require at least one workload")
        return self


class CompiledLoadSegmentEntity(BaseModel):
    sequence: int
    profile_family: str
    scenario_starts_per_second: int
    max_concurrency: int | None = None
    duration_seconds: int | None = None
    scenario_count: int | None = None
    share: float | None = None


class CompiledWorkloadBundleEntity(BaseModel):
    workload_name: str
    scenario_id: str
    scenario_name: str
    role: WorkloadRole
    resolved_steps: list[ResolvedScenarioStepEntity]
    measured_targets: list[MeasuredTargetEntity]
    load_segments: list[CompiledLoadSegmentEntity]
    max_total_scenario_starts: int | None = None
    stop_when_budget_exhausted: bool = True
    validation_notes: list[str] = Field(default_factory=list)


class CompiledTestPlanBundleEntity(BaseModel):
    plan_name: str
    requested_by: str
    environment: str
    workloads: list[CompiledWorkloadBundleEntity]
    validation_notes: list[str] = Field(default_factory=list)


class WorkloadExecutionResultEntity(BaseModel):
    workload_name: str
    scenario_id: str
    scenario_name: str
    role: WorkloadRole
    status: str
    actual_scenario_starts_per_second: float | None = None
    actual_requests_per_second: float | None = None
    error_rate: float | None = None
    p95_ms: float | None = None
    p99_ms: float | None = None
    status_url: str | None = None
    report_url: str | None = None
