from __future__ import annotations

from statistics import mean
from typing import Any

import httpx

from perf_control_plane.config.settings import Settings
from perf_control_plane.domain.entities.runs import (
    ExecutorSubmissionEntity,
    LatestMetricsEntity,
)
from perf_control_plane.domain.entities.test_plans import (
    CompiledTestPlanBundleEntity,
    WorkloadExecutionResultEntity,
)
from perf_control_plane.domain.ports.execution_gateway import ExecutionGateway
from perf_control_plane.utils.ids import new_id


class HttpExecutionGateway(ExecutionGateway):
    def __init__(
        self,
        *,
        settings: Settings,
        http_client: httpx.AsyncClient | None,
    ) -> None:
        self._settings = settings
        self._http_client = http_client

    async def submit_run(
        self,
        bundle: CompiledTestPlanBundleEntity,
    ) -> ExecutorSubmissionEntity:
        if self._settings.executor_mode == "stub" or self._http_client is None:
            external_run_id = new_id("external")
            workload_results = self._build_stub_workload_results(bundle, external_run_id)
            aggregate_metrics = LatestMetricsEntity(
                actual_scenario_starts_per_second=sum(
                    item.actual_scenario_starts_per_second or 0
                    for item in workload_results
                ),
                actual_requests_per_second=sum(
                    item.actual_requests_per_second or 0
                    for item in workload_results
                ),
                error_rate=mean(item.error_rate or 0 for item in workload_results),
                p95_ms=mean(item.p95_ms or 0 for item in workload_results),
                p99_ms=mean(item.p99_ms or 0 for item in workload_results),
            )
            return ExecutorSubmissionEntity(
                external_run_id=external_run_id,
                status_url=f"{self._settings.executor_base_url}/runs/{external_run_id}",
                report_url=f"{self._settings.executor_base_url}/reports/{external_run_id}",
                raw_response={
                    "executor_mode": self._settings.executor_mode,
                    "submitted_bundle": bundle.to_dict(exclude_none=True),
                },
                aggregate_metrics=aggregate_metrics,
                workload_results=workload_results,
            )

        response = await self._http_client.post(
            f"{self._settings.executor_base_url.rstrip('/')}{self._settings.executor_submit_path}",
            json=bundle.to_dict(exclude_none=True),
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        return ExecutorSubmissionEntity(
            external_run_id=payload.get("external_run_id", new_id("external")),
            status_url=payload.get("status_url"),
            report_url=payload.get("report_url"),
            raw_response=payload,
        )

    def _build_stub_workload_results(
        self,
        bundle: CompiledTestPlanBundleEntity,
        external_run_id: str,
    ) -> list[WorkloadExecutionResultEntity]:
        workload_results: list[WorkloadExecutionResultEntity] = []
        for index, workload in enumerate(bundle.workloads):
            first_band = workload.load_bands[0]
            actual_scenario_rate = round(first_band.scenario_starts_per_second * 0.97, 2)
            actual_request_rate = round(
                actual_scenario_rate * max(len(workload.resolved_steps), 1),
                2,
            )
            workload_results.append(
                WorkloadExecutionResultEntity(
                    workload_name=workload.workload_name,
                    scenario_id=workload.scenario_id,
                    scenario_name=workload.scenario_name,
                    role=workload.role,
                    status="completed",
                    actual_scenario_starts_per_second=actual_scenario_rate,
                    actual_requests_per_second=actual_request_rate,
                    error_rate=round(0.001 * (index + 1), 4),
                    p95_ms=150.0 + (index * 20.0),
                    p99_ms=210.0 + (index * 25.0),
                    status_url=f"{self._settings.executor_base_url}/runs/{external_run_id}/workloads/{index}",
                    report_url=f"{self._settings.executor_base_url}/reports/{external_run_id}/workloads/{index}",
                )
            )
        return workload_results
