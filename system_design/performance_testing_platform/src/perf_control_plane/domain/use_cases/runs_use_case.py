from __future__ import annotations

from perf_control_plane.domain.entities.runs import (
    LatestMetricsEntity,
    PerfTestRunEntity,
    RunStatus,
)
from perf_control_plane.domain.entities.test_plans import (
    TestPlanEntity,
    WorkloadExecutionResultEntity,
)
from perf_control_plane.domain.services.run_service import RunService


class RunUseCase:
    def __init__(self, service: RunService) -> None:
        self._service = service

    async def submit_test_plan(
        self,
        *,
        test_plan: TestPlanEntity,
        requested_by: str,
    ) -> PerfTestRunEntity:
        return await self._service.submit_test_plan(
            test_plan=test_plan,
            requested_by=requested_by,
        )

    async def list_runs(self) -> list[PerfTestRunEntity]:
        return await self._service.list_runs()

    async def list_recent_runs(self, limit: int) -> list[PerfTestRunEntity]:
        return await self._service.list_recent_runs(limit)

    async def get_run(self, run_id: str) -> PerfTestRunEntity:
        return await self._service.get_run(run_id)

    async def rerun(self, run_id: str) -> PerfTestRunEntity:
        return await self._service.rerun(run_id)

    async def record_executor_update(
        self,
        *,
        run_id: str,
        status: RunStatus,
        report_url: str | None,
        status_url: str | None,
        aggregate_metrics: LatestMetricsEntity | None,
        workload_results: list[WorkloadExecutionResultEntity],
    ) -> PerfTestRunEntity:
        return await self._service.record_executor_update(
            run_id=run_id,
            status=status,
            report_url=report_url,
            status_url=status_url,
            aggregate_metrics=aggregate_metrics,
            workload_results=workload_results,
        )
