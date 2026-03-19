from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import Field

from perf_control_plane.domain.entities.base import BaseModel
from perf_control_plane.domain.entities.test_plans import (
    CompiledTestPlanBundleEntity,
    TestPlanEntity,
    WorkloadExecutionResultEntity,
)


class RunStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ExecutorSubmissionEntity(BaseModel):
    external_run_id: str
    accepted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status_url: str | None = None
    report_url: str | None = None
    raw_response: dict[str, Any] | None = None
    aggregate_metrics: "LatestMetricsEntity | None" = None
    workload_results: list[WorkloadExecutionResultEntity] = Field(default_factory=list)


class LatestMetricsEntity(BaseModel):
    actual_scenario_starts_per_second: float | None = None
    actual_requests_per_second: float | None = None
    error_rate: float | None = None
    p95_ms: float | None = None
    p99_ms: float | None = None


class PerfTestRunEntity(BaseModel):
    id: str
    test_plan_name: str
    saved_config_id: str | None = None
    environment: str
    requested_by: str
    status: RunStatus
    is_rerun: bool = False
    plan_snapshot: TestPlanEntity
    compiled_plan: CompiledTestPlanBundleEntity
    validation_notes: list[str] = Field(default_factory=list)
    external_submission: ExecutorSubmissionEntity | None = None
    aggregate_metrics: LatestMetricsEntity | None = None
    workload_results: list[WorkloadExecutionResultEntity] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
