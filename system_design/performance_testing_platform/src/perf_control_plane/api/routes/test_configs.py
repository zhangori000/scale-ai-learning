from __future__ import annotations

from fastapi import APIRouter

from perf_control_plane.api.routes.run_configuration_mapper import to_test_plan
from perf_control_plane.api.schemas.runs import RunResponse
from perf_control_plane.api.schemas.test_configs import (
    FolderCreateRequest,
    FolderDetailsResponse,
    FolderResponse,
    RunFromSavedConfigRequest,
    SavedTestConfigCreateRequest,
    SavedTestConfigDetailsResponse,
    SavedTestConfigResponse,
)
from perf_control_plane.config.dependencies import DTestConfigUseCase
from perf_control_plane.domain.entities.test_configs import (
    SavedTestConfigEntity,
    TestConfigFolderEntity,
)

router = APIRouter(prefix="", tags=["test-configs"])


@router.post("/folders", response_model=FolderResponse)
async def create_folder(
    request: FolderCreateRequest,
    use_case: DTestConfigUseCase,
) -> FolderResponse:
    folder = TestConfigFolderEntity(
        id="",
        name=request.name,
        owner_eid=request.owner_eid,
        owner_name=request.owner_name,
        description=request.description,
    )
    created = await use_case.create_folder(folder)
    return FolderResponse.model_validate(created)


@router.get("/folders", response_model=list[FolderResponse])
async def list_folders(use_case: DTestConfigUseCase) -> list[FolderResponse]:
    folders = await use_case.list_folders()
    return [FolderResponse.model_validate(item) for item in folders]


@router.get("/folders/{folder_id}", response_model=FolderDetailsResponse)
async def get_folder_details(
    folder_id: str,
    use_case: DTestConfigUseCase,
) -> FolderDetailsResponse:
    details = await use_case.get_folder_details(folder_id)
    return FolderDetailsResponse.model_validate(details)


@router.post("/saved-configs", response_model=SavedTestConfigResponse)
async def create_saved_config(
    request: SavedTestConfigCreateRequest,
    use_case: DTestConfigUseCase,
) -> SavedTestConfigResponse:
    config = SavedTestConfigEntity(
        id="",
        folder_id=request.folder_id,
        owner_eid=request.owner_eid,
        owner_name=request.owner_name,
        name=request.name,
        description=request.description,
        plan_template=to_test_plan(request.plan_template),
    )
    created = await use_case.create_saved_config(config)
    return SavedTestConfigResponse.model_validate(created)


@router.get("/saved-configs", response_model=list[SavedTestConfigResponse])
async def list_saved_configs(
    use_case: DTestConfigUseCase,
    folder_id: str | None = None,
) -> list[SavedTestConfigResponse]:
    configs = (
        await use_case.list_saved_configs_by_folder(folder_id)
        if folder_id is not None
        else await use_case.list_saved_configs()
    )
    return [SavedTestConfigResponse.model_validate(item) for item in configs]


@router.get("/saved-configs/{config_id}", response_model=SavedTestConfigDetailsResponse)
async def get_saved_config_details(
    config_id: str,
    use_case: DTestConfigUseCase,
) -> SavedTestConfigDetailsResponse:
    details = await use_case.get_saved_config_details(config_id)
    return SavedTestConfigDetailsResponse.model_validate(details)


@router.post("/saved-configs/{config_id}/run", response_model=RunResponse)
async def run_saved_config(
    config_id: str,
    request: RunFromSavedConfigRequest,
    use_case: DTestConfigUseCase,
) -> RunResponse:
    run = await use_case.submit_run_from_saved_config(
        config_id,
        requested_by=request.requested_by,
        test_plan_override=(
            to_test_plan(request.test_plan_override)
            if request.test_plan_override is not None
            else None
        ),
    )
    return RunResponse.model_validate(run)
