from __future__ import annotations

from perf_control_plane.api.schemas.test_plans import TestPlanRequest, WorkloadExecutionSettingsRequest
from perf_control_plane.domain.entities.load_profiles import (
    BudgetSegmentEntity,
    BudgetRampProfileEntity,
    TimeRampProfileEntity,
    TimeSegmentEntity,
)
from perf_control_plane.domain.entities.test_plans import (
    ScenarioWorkloadEntity,
    TestPlanEntity,
    WorkloadExecutionSettingsEntity,
)


def to_execution_settings(
    request: WorkloadExecutionSettingsRequest,
) -> WorkloadExecutionSettingsEntity:
    return WorkloadExecutionSettingsEntity(
        time_segments=[
            TimeSegmentEntity(
                duration_seconds=item.duration_seconds,
                scenario_starts_per_second=item.scenario_starts_per_second,
                max_concurrency=item.max_concurrency,
            )
            for item in request.time_segments
        ],
        time_ramp_profile=(
            TimeRampProfileEntity(
                initial_scenario_starts_per_second=request.time_ramp_profile.initial_scenario_starts_per_second,
                step_size=request.time_ramp_profile.step_size,
                step_count=request.time_ramp_profile.step_count,
                step_duration_seconds=request.time_ramp_profile.step_duration_seconds,
                max_concurrency=request.time_ramp_profile.max_concurrency,
            )
            if request.time_ramp_profile is not None
            else None
        ),
        budget_segments=[
            BudgetSegmentEntity(
                share=item.share,
                scenario_starts_per_second=item.scenario_starts_per_second,
                max_concurrency=item.max_concurrency,
            )
            for item in request.budget_segments
        ],
        budget_ramp_profile=(
            BudgetRampProfileEntity(
                part_count=request.budget_ramp_profile.part_count,
                initial_scenario_starts_per_second=request.budget_ramp_profile.initial_scenario_starts_per_second,
                step_size=request.budget_ramp_profile.step_size,
                max_concurrency=request.budget_ramp_profile.max_concurrency,
            )
            if request.budget_ramp_profile is not None
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
