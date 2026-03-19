from __future__ import annotations

from datetime import UTC, datetime

from perf_control_plane.domain.entities.endpoints import EndpointEntity
from perf_control_plane.domain.entities.runs import (
    LatestMetricsEntity,
    PerfTestRunEntity,
    RunStatus,
)
from perf_control_plane.domain.entities.scenarios import ScenarioEntity
from perf_control_plane.domain.entities.test_plans import TestPlanEntity
from perf_control_plane.domain.exceptions import ValidationError
from perf_control_plane.domain.ports.execution_gateway import ExecutionGateway
from perf_control_plane.domain.ports.repositories import (
    EndpointRepository,
    RunRepository,
    ScenarioRepository,
)
from perf_control_plane.domain.services.compiler_service import CompilerService
from perf_control_plane.utils.ids import new_id


class RunService:
    def __init__(
        self,
        run_repository: RunRepository,
        scenario_repository: ScenarioRepository,
        endpoint_repository: EndpointRepository,
        compiler_service: CompilerService,
        execution_gateway: ExecutionGateway,
    ) -> None:
        self._run_repository = run_repository
        self._scenario_repository = scenario_repository
        self._endpoint_repository = endpoint_repository
        self._compiler_service = compiler_service
        self._execution_gateway = execution_gateway

    async def submit_test_plan(
        self,
        *,
        test_plan: TestPlanEntity,
        requested_by: str,
        is_rerun: bool = False,
        saved_config_id: str | None = None,
    ) -> PerfTestRunEntity:
        scenarios = await self._load_scenarios_for_plan(test_plan)
        endpoints = await self._load_endpoints_for_scenarios(scenarios)
        compiled_plan = self._compiler_service.compile_test_plan(
            test_plan=test_plan,
            requested_by=requested_by,
            scenarios=scenarios,
            endpoints=endpoints,
        )
        run = PerfTestRunEntity(
            id=new_id("run"),
            test_plan_name=test_plan.name,
            saved_config_id=saved_config_id,
            environment=test_plan.environment,
            requested_by=requested_by,
            status=RunStatus.DRAFT,
            is_rerun=is_rerun,
            plan_snapshot=test_plan,
            compiled_plan=compiled_plan,
            validation_notes=compiled_plan.validation_notes,
        )
        run = await self._run_repository.create(run)
        submission = await self._execution_gateway.submit_run(compiled_plan)
        has_stub_results = bool(submission.workload_results) or submission.aggregate_metrics is not None
        run = run.model_copy(
            update={
                "status": RunStatus.COMPLETED if has_stub_results else RunStatus.SUBMITTED,
                "external_submission": submission,
                "aggregate_metrics": submission.aggregate_metrics,
                "workload_results": submission.workload_results,
                "updated_at": datetime.now(UTC),
            }
        )
        return await self._run_repository.update(run)

    async def list_runs(self) -> list[PerfTestRunEntity]:
        return await self._run_repository.list()

    async def list_recent_runs(self, limit: int) -> list[PerfTestRunEntity]:
        return await self._run_repository.list_recent(limit)

    async def get_run(self, run_id: str) -> PerfTestRunEntity:
        return await self._run_repository.get(run_id)

    async def rerun(self, run_id: str) -> PerfTestRunEntity:
        original = await self._run_repository.get(run_id)
        return await self.submit_test_plan(
            test_plan=original.plan_snapshot,
            requested_by=original.requested_by,
            is_rerun=True,
            saved_config_id=original.saved_config_id,
        )

    async def record_executor_update(
        self,
        *,
        run_id: str,
        status: RunStatus,
        report_url: str | None,
        status_url: str | None,
        aggregate_metrics: LatestMetricsEntity | None,
        workload_results,
    ) -> PerfTestRunEntity:
        run = await self._run_repository.get(run_id)
        external_submission = run.external_submission
        if external_submission is not None:
            external_submission = external_submission.model_copy(
                update={
                    "report_url": report_url or external_submission.report_url,
                    "status_url": status_url or external_submission.status_url,
                }
            )
        run = run.model_copy(
            update={
                "status": status,
                "external_submission": external_submission,
                "aggregate_metrics": aggregate_metrics,
                "workload_results": workload_results,
                "updated_at": datetime.now(UTC),
            }
        )
        return await self._run_repository.update(run)

    async def _load_scenarios_for_plan(
        self,
        test_plan: TestPlanEntity,
    ) -> dict[str, ScenarioEntity]:
        scenarios: dict[str, ScenarioEntity] = {}
        for workload in test_plan.workloads:
            if workload.scenario_id in scenarios:
                continue
            scenarios[workload.scenario_id] = await self._scenario_repository.get(
                workload.scenario_id
            )
        return scenarios

    async def _load_endpoints_for_scenarios(
        self,
        scenarios: dict[str, ScenarioEntity],
    ) -> dict[str, EndpointEntity]:
        endpoints: dict[str, EndpointEntity] = {}
        for scenario in scenarios.values():
            for step in scenario.steps:
                if step.endpoint_id not in endpoints:
                    endpoints[step.endpoint_id] = await self._endpoint_repository.get(
                        step.endpoint_id
                    )
        return endpoints
