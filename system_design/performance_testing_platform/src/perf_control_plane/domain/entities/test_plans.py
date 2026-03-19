from __future__ import annotations

from enum import Enum

from pydantic import Field, model_validator

from perf_control_plane.domain.entities.base import BaseModel
from perf_control_plane.domain.entities.scenarios import (
    LoadSegmentEntity,
    MeasuredTargetEntity,
    ResolvedScenarioStepEntity,
    SteppedLoadProfileEntity,
)


class WorkloadRole(str, Enum):
    SETUP = "setup"
    MEASURED = "measured"
    TEARDOWN = "teardown"


class BudgetLoadBandEntity(BaseModel):
    share: float
    scenario_starts_per_second: int
    max_concurrency: int | None = None

    @model_validator(mode="after")
    def validate_band(self) -> "BudgetLoadBandEntity":
        if self.share <= 0 or self.share > 1:
            raise ValueError("budget band share must be in the range (0, 1]")
        if self.scenario_starts_per_second <= 0:
            raise ValueError("scenario_starts_per_second must be positive")
        return self


class BudgetStepLoadProfileEntity(BaseModel):
    part_count: int = 3
    initial_scenario_starts_per_second: int = 1000
    step_size: int = 250
    max_concurrency: int | None = None

    @model_validator(mode="after")
    def validate_profile(self) -> "BudgetStepLoadProfileEntity":
        if self.part_count <= 0:
            raise ValueError("part_count must be positive")
        if self.initial_scenario_starts_per_second <= 0:
            raise ValueError("initial_scenario_starts_per_second must be positive")
        if self.step_size < 0:
            raise ValueError("step_size must be zero or positive")
        return self

    def to_budget_bands(self) -> list[BudgetLoadBandEntity]:
        equal_share = 1.0 / self.part_count
        return [
            BudgetLoadBandEntity(
                share=equal_share,
                scenario_starts_per_second=(
                    self.initial_scenario_starts_per_second + (index * self.step_size)
                ),
                max_concurrency=self.max_concurrency,
            )
            for index in range(self.part_count)
        ]


class WorkloadExecutionSettingsEntity(BaseModel):
    load_segments: list[LoadSegmentEntity] = Field(default_factory=list)
    stepped_load_profile: SteppedLoadProfileEntity | None = None
    budget_bands: list[BudgetLoadBandEntity] = Field(default_factory=list)
    budget_step_profile: BudgetStepLoadProfileEntity | None = None
    max_total_scenario_starts: int | None = None
    stop_when_budget_exhausted: bool = True

    @model_validator(mode="after")
    def validate_load_shape(self) -> "WorkloadExecutionSettingsEntity":
        configured_profiles = [
            bool(self.load_segments),
            self.stepped_load_profile is not None,
            bool(self.budget_bands),
            self.budget_step_profile is not None,
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
        if self.budget_bands:
            total_share = sum(item.share for item in self.budget_bands)
            if abs(total_share - 1.0) > 1e-6:
                raise ValueError("budget band shares must sum to 1.0")
        return self

    def uses_time_profile(self) -> bool:
        return bool(self.load_segments) or self.stepped_load_profile is not None

    def uses_budget_profile(self) -> bool:
        return bool(self.budget_bands) or self.budget_step_profile is not None

    def effective_load_segments(self) -> list[LoadSegmentEntity]:
        if self.load_segments:
            return self.load_segments
        if self.stepped_load_profile is None:
            return []
        return self.stepped_load_profile.to_load_segments()

    def effective_budget_bands(self) -> list[BudgetLoadBandEntity]:
        if self.budget_bands:
            return self.budget_bands
        if self.budget_step_profile is None:
            return []
        return self.budget_step_profile.to_budget_bands()

    def load_profile_family(self) -> str:
        if self.load_segments:
            return "time_segments"
        if self.stepped_load_profile is not None:
            return "time_step"
        if self.budget_bands:
            return "budget_bands"
        if self.budget_step_profile is not None:
            return "budget_step"
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


class CompiledLoadBandEntity(BaseModel):
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
    load_bands: list[CompiledLoadBandEntity]
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
