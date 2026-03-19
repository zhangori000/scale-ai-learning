from __future__ import annotations

from perf_control_plane.domain.entities.runs import PerfTestRunEntity
from perf_control_plane.domain.entities.test_configs import (
    FolderDetailsEntity,
    SavedTestConfigDetailsEntity,
    SavedTestConfigEntity,
    TestConfigFolderEntity,
)
from perf_control_plane.domain.entities.test_plans import TestPlanEntity
from perf_control_plane.domain.services.test_config_service import TestConfigService


class TestConfigUseCase:
    def __init__(self, service: TestConfigService) -> None:
        self._service = service

    async def create_folder(
        self,
        folder: TestConfigFolderEntity,
    ) -> TestConfigFolderEntity:
        return await self._service.create_folder(folder)

    async def list_folders(self) -> list[TestConfigFolderEntity]:
        return await self._service.list_folders()

    async def get_folder_details(self, folder_id: str) -> FolderDetailsEntity:
        return await self._service.get_folder_details(folder_id)

    async def create_saved_config(
        self,
        config: SavedTestConfigEntity,
    ) -> SavedTestConfigEntity:
        return await self._service.create_saved_config(config)

    async def list_saved_configs(self) -> list[SavedTestConfigEntity]:
        return await self._service.list_saved_configs()

    async def list_saved_configs_by_folder(
        self,
        folder_id: str,
    ) -> list[SavedTestConfigEntity]:
        return await self._service.list_saved_configs_by_folder(folder_id)

    async def get_saved_config(self, config_id: str) -> SavedTestConfigEntity:
        return await self._service.get_saved_config(config_id)

    async def get_saved_config_details(
        self,
        config_id: str,
        *,
        recent_run_limit: int = 10,
    ) -> SavedTestConfigDetailsEntity:
        return await self._service.get_saved_config_details(
            config_id,
            recent_run_limit=recent_run_limit,
        )

    async def submit_run_from_saved_config(
        self,
        config_id: str,
        *,
        requested_by: str,
        test_plan_override: TestPlanEntity | None = None,
    ) -> PerfTestRunEntity:
        return await self._service.submit_run_from_saved_config(
            config_id,
            requested_by=requested_by,
            test_plan_override=test_plan_override,
        )
