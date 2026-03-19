from __future__ import annotations

from fastapi import APIRouter

from perf_control_plane.api.routes.run_configuration_mapper import to_test_plan
from perf_control_plane.api.schemas.runs import (
    ExecutorUpdateRequest,
    RunCreateRequest,
    RunResponse,
)
from perf_control_plane.config.dependencies import DRunUseCase, DTestConfigUseCase
from perf_control_plane.domain.entities.test_plans import WorkloadExecutionResultEntity

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunResponse)
async def create_run(
    request: RunCreateRequest,
    run_use_case: DRunUseCase,
    test_config_use_case: DTestConfigUseCase,
) -> RunResponse:
    if request.saved_config_id is not None:
        created = await test_config_use_case.submit_run_from_saved_config(
            request.saved_config_id,
            requested_by=request.requested_by or "",
        )
    elif request.test_plan is not None:
        created = await run_use_case.submit_test_plan(
            test_plan=to_test_plan(request.test_plan),
            requested_by=request.requested_by or "",
        )
    else:
        raise ValueError("validated RunCreateRequest must provide test_plan or saved_config_id")
    return RunResponse.model_validate(created)


@router.get("", response_model=list[RunResponse])
async def list_runs(use_case: DRunUseCase) -> list[RunResponse]:
    runs = await use_case.list_runs()
    return [RunResponse.model_validate(item) for item in runs]


@router.get("/recent", response_model=list[RunResponse])
async def list_recent_runs(use_case: DRunUseCase) -> list[RunResponse]:
    runs = await use_case.list_recent_runs(limit=20)
    return [RunResponse.model_validate(item) for item in runs]


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, use_case: DRunUseCase) -> RunResponse:
    run = await use_case.get_run(run_id)
    return RunResponse.model_validate(run)


@router.post("/{run_id}/rerun", response_model=RunResponse)
async def rerun(run_id: str, use_case: DRunUseCase) -> RunResponse:
    run = await use_case.rerun(run_id)
    return RunResponse.model_validate(run)


@router.post("/{run_id}/executor-update", response_model=RunResponse)
async def update_from_executor(
    run_id: str,
    request: ExecutorUpdateRequest,
    use_case: DRunUseCase,
) -> RunResponse:
    run = await use_case.record_executor_update(
        run_id=run_id,
        status=request.status,
        report_url=request.report_url,
        status_url=request.status_url,
        aggregate_metrics=request.aggregate_metrics,
        workload_results=[
            WorkloadExecutionResultEntity.model_validate(item)
            for item in request.workload_results
        ],
    )
    return RunResponse.model_validate(run)
