from __future__ import annotations

from perf_control_plane.api.schemas.test_plans import TestPlanRequest, WorkloadExecutionSettingsRequest
from perf_control_plane.domain.entities.scenarios import (
    LoadSegmentEntity,
    SteppedLoadProfileEntity,
)
from perf_control_plane.domain.entities.test_plans import (
    BudgetLoadBandEntity,
    BudgetStepLoadProfileEntity,
    ScenarioWorkloadEntity,
    TestPlanEntity,
    WorkloadExecutionSettingsEntity,
)


def to_execution_settings(
    request: WorkloadExecutionSettingsRequest,
) -> WorkloadExecutionSettingsEntity:
    return WorkloadExecutionSettingsEntity(
        load_segments=[
            LoadSegmentEntity(
                duration_seconds=item.duration_seconds,
                scenario_starts_per_second=item.scenario_starts_per_second,
                max_concurrency=item.max_concurrency,
            )
            for item in request.load_segments
        ],
        stepped_load_profile=(
            SteppedLoadProfileEntity(
                initial_scenario_starts_per_second=request.stepped_load_profile.initial_scenario_starts_per_second,
                step_size=request.stepped_load_profile.step_size,
                step_count=request.stepped_load_profile.step_count,
                step_duration_seconds=request.stepped_load_profile.step_duration_seconds,
                max_concurrency=request.stepped_load_profile.max_concurrency,
            )
            if request.stepped_load_profile is not None
            else None
        ),
        budget_bands=[
            BudgetLoadBandEntity(
                share=item.share,
                scenario_starts_per_second=item.scenario_starts_per_second,
                max_concurrency=item.max_concurrency,
            )
            for item in request.budget_bands
        ],
        budget_step_profile=(
            BudgetStepLoadProfileEntity(
                part_count=request.budget_step_profile.part_count,
                initial_scenario_starts_per_second=request.budget_step_profile.initial_scenario_starts_per_second,
                step_size=request.budget_step_profile.step_size,
                max_concurrency=request.budget_step_profile.max_concurrency,
            )
            if request.budget_step_profile is not None
            else None
        ),
        max_total_scenario_starts=request.max_total_scenario_starts,
        stop_when_budget_exhausted=request.stop_when_budget_exhausted,
    )


def to_test_plan(request: TestPlanRequest) -> TestPlanEntity:
    return TestPlanEntity(
        name=request.name,
        environment=request.environment,
        notes=request.notes,
        workloads=[
            ScenarioWorkloadEntity(
                name=item.name,
                scenario_id=item.scenario_id,
                scenario_name=item.scenario_name,
                role=item.role,
                measured_step_indexes_override=item.measured_step_indexes_override,
                execution_settings=to_execution_settings(item.execution_settings),
            )
            for item in request.workloads
        ],
    )
