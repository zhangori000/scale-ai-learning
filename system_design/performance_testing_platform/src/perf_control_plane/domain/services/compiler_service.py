from __future__ import annotations

from collections import Counter
from math import floor

from perf_control_plane.domain.entities.endpoints import EndpointEntity
from perf_control_plane.domain.entities.scenarios import ScenarioEntity
from perf_control_plane.domain.entities.test_plans import (
    CompiledLoadBandEntity,
    CompiledTestPlanBundleEntity,
    CompiledWorkloadBundleEntity,
    ScenarioWorkloadEntity,
    TestPlanEntity,
    WorkloadExecutionSettingsEntity,
    WorkloadRole,
)
from perf_control_plane.domain.exceptions import ValidationError


class CompilerService:
    def compile_test_plan(
        self,
        *,
        test_plan: TestPlanEntity,
        requested_by: str,
        scenarios: dict[str, ScenarioEntity],
        endpoints: dict[str, EndpointEntity],
    ) -> CompiledTestPlanBundleEntity:
        workloads = [
            self._compile_workload(
                workload=workload,
                scenario=scenarios[workload.scenario_id],
                endpoints=endpoints,
            )
            for workload in test_plan.workloads
        ]
        validation_notes = [
            note
            for item in workloads
            for note in item.validation_notes
        ]
        return CompiledTestPlanBundleEntity(
            plan_name=test_plan.name,
            requested_by=requested_by,
            environment=test_plan.environment,
            workloads=workloads,
            validation_notes=validation_notes,
        )

    def _compile_workload(
        self,
        *,
        workload: ScenarioWorkloadEntity,
        scenario: ScenarioEntity,
        endpoints: dict[str, EndpointEntity],
    ) -> CompiledWorkloadBundleEntity:
        measured_indexes = self._resolve_measured_indexes(workload=workload, scenario=scenario)

        resolved_steps = [
            self._resolve_step(
                step_index=index,
                step=scenario.steps[index],
                endpoint=endpoints[scenario.steps[index].endpoint_id],
            )
            for index in range(len(scenario.steps))
        ]
        measured_targets = [
            {
                "step_index": index,
                "request_name": f"step[{index}].{scenario.steps[index].name}",
                "endpoint_id": scenario.steps[index].endpoint_id,
                "path": endpoints[scenario.steps[index].endpoint_id].path,
            }
            for index in measured_indexes
        ]
        load_bands = self._compile_load_bands(workload.execution_settings)
        validation_notes = self._build_validation_notes(
            workload=workload,
            scenario=scenario,
            measured_indexes=measured_indexes,
        )
        return CompiledWorkloadBundleEntity(
            workload_name=workload.name,
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            role=workload.role,
            resolved_steps=resolved_steps,
            measured_targets=measured_targets,
            load_bands=load_bands,
            max_total_scenario_starts=workload.execution_settings.max_total_scenario_starts,
            stop_when_budget_exhausted=workload.execution_settings.stop_when_budget_exhausted,
            validation_notes=validation_notes,
        )

    def _resolve_measured_indexes(
        self,
        *,
        workload: ScenarioWorkloadEntity,
        scenario: ScenarioEntity,
    ) -> list[int]:
        if workload.role == WorkloadRole.SETUP:
            return []
        if workload.measured_step_indexes_override is not None:
            invalid_indexes = [
                index
                for index in workload.measured_step_indexes_override
                if index >= len(scenario.steps)
            ]
            if invalid_indexes:
                raise ValidationError(
                    f"measured_step_indexes_override references invalid step indexes: {invalid_indexes}"
                )
            return workload.measured_step_indexes_override
        return list(range(len(scenario.steps)))

    def _resolve_step(
        self,
        *,
        step_index: int,
        step,
        endpoint: EndpointEntity,
    ):
        return {
            "step_index": step_index,
            "name": step.name,
            "endpoint_id": step.endpoint_id,
            "service_name": endpoint.service_name,
            "method": endpoint.method.value,
            "path": endpoint.path,
            "base_url": endpoint.base_url,
            "owner_team": endpoint.owner_team,
        }

    def _compile_load_bands(
        self,
        execution_settings: WorkloadExecutionSettingsEntity,
    ) -> list[CompiledLoadBandEntity]:
        if execution_settings.uses_time_profile():
            return [
                CompiledLoadBandEntity(
                    sequence=index,
                    profile_family=execution_settings.load_profile_family(),
                    scenario_starts_per_second=segment.scenario_starts_per_second,
                    max_concurrency=segment.max_concurrency,
                    duration_seconds=segment.duration_seconds,
                )
                for index, segment in enumerate(execution_settings.effective_load_segments())
            ]

        total_budget = execution_settings.max_total_scenario_starts
        if total_budget is None:
            raise ValidationError("budget-based workloads require max_total_scenario_starts")
        bands = execution_settings.effective_budget_bands()
        allocated_counts: list[int] = []
        assigned = 0
        for index, band in enumerate(bands):
            if index == len(bands) - 1:
                scenario_count = total_budget - assigned
            else:
                scenario_count = floor(total_budget * band.share)
                assigned += scenario_count
            allocated_counts.append(scenario_count)

        return [
            CompiledLoadBandEntity(
                sequence=index,
                profile_family=execution_settings.load_profile_family(),
                scenario_starts_per_second=band.scenario_starts_per_second,
                max_concurrency=band.max_concurrency,
                scenario_count=allocated_counts[index],
                share=band.share,
            )
            for index, band in enumerate(bands)
        ]

    def _build_validation_notes(
        self,
        *,
        workload: ScenarioWorkloadEntity,
        scenario: ScenarioEntity,
        measured_indexes: list[int],
    ) -> list[str]:
        execution_settings = workload.execution_settings
        notes: list[str] = []

        if execution_settings.uses_time_profile():
            planned_scenario_starts = sum(
                segment.duration_seconds * segment.scenario_starts_per_second
                for segment in execution_settings.effective_load_segments()
            )
            if execution_settings.max_total_scenario_starts is not None:
                if planned_scenario_starts > execution_settings.max_total_scenario_starts:
                    notes.append(
                        f"workload '{workload.name}' planned time schedule exceeds max_total_scenario_starts; executor should stop early when the scenario budget is exhausted"
                    )
            else:
                notes.append(
                    f"workload '{workload.name}' has no max_total_scenario_starts; duration alone controls total scenario volume"
                )
        else:
            notes.append(
                f"workload '{workload.name}' uses budget-based load partitioning against the scenario budget"
            )

        if workload.role == WorkloadRole.SETUP:
            notes.append(
                f"workload '{workload.name}' is setup-only, so no scenario steps are measured"
            )
        elif workload.measured_step_indexes_override is None:
            notes.append(
                f"workload '{workload.name}' measures every step in the attached scenario"
            )
        elif measured_indexes:
            notes.append(
                f"workload '{workload.name}' measures only the explicitly selected scenario step indexes"
            )
        else:
            notes.append(
                f"workload '{workload.name}' has an explicit empty measurement override, so no scenario steps are measured"
            )

        measured_name_counts = Counter(scenario.steps[index].name for index in measured_indexes)
        for name, count in measured_name_counts.items():
            if count > 1:
                notes.append(
                    f"workload '{workload.name}' measures multiple occurrences of step name '{name}' by step index, not by name"
                )

        if execution_settings.stepped_load_profile is not None:
            total_duration = execution_settings.stepped_load_profile.total_duration_seconds()
            notes.append(
                f"workload '{workload.name}' load bands were derived from the stepped time profile abstraction"
            )
            if total_duration > 1800:
                notes.append(
                    f"workload '{workload.name}' runs longer than the default 30-minute recommendation"
                )
            if total_duration >= 3600:
                notes.append(
                    f"workload '{workload.name}' is one hour or longer; allow it, but treat it as an operator-reviewed run"
                )

        if execution_settings.budget_step_profile is not None:
            notes.append(
                f"workload '{workload.name}' budget bands were auto-generated from the budget step profile"
            )

        return notes
