from __future__ import annotations

from datetime import datetime

from pydantic import Field, model_validator

from perf_control_plane.api.schemas.test_plans import TestPlanRequest
from perf_control_plane.domain.entities.base import BaseModel
from perf_control_plane.domain.entities.runs import (
    ExecutorSubmissionEntity,
    LatestMetricsEntity,
    RunStatus,
)
from perf_control_plane.domain.entities.test_plans import WorkloadRole


class RunCreateRequest(BaseModel):
    requested_by: str | None = None
    saved_config_id: str | None = None
    test_plan: TestPlanRequest | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> "RunCreateRequest":
        uses_saved_config = self.saved_config_id is not None
        uses_inline_plan = self.test_plan is not None

        if uses_saved_config == uses_inline_plan:
            raise ValueError(
                "provide exactly one of saved_config_id or test_plan"
            )
        if self.requested_by is None:
            raise ValueError("requested_by is required when submitting a run")
        return self


class WorkloadExecutionResultResponse(BaseModel):
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


class ExecutorUpdateRequest(BaseModel):
    status: RunStatus
    report_url: str | None = None
    status_url: str | None = None
    aggregate_metrics: LatestMetricsEntity | None = None
    workload_results: list[WorkloadExecutionResultResponse] = Field(default_factory=list)


class RunResponse(BaseModel):
    id: str
    test_plan_name: str
    saved_config_id: str | None = None
    environment: str
    requested_by: str
    status: RunStatus
    is_rerun: bool
    external_submission: ExecutorSubmissionEntity | None = None
    aggregate_metrics: LatestMetricsEntity | None = None
    workload_results: list[WorkloadExecutionResultResponse] = Field(default_factory=list)
    validation_notes: list[str]
    created_at: datetime
    updated_at: datetime
