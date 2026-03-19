from __future__ import annotations

from perf_control_plane.domain.entities.runs import PerfTestRunEntity
from perf_control_plane.domain.entities.test_configs import (
    FolderDetailsEntity,
    SavedTestConfigDetailsEntity,
    SavedTestConfigEntity,
    TestConfigFolderEntity,
)
from perf_control_plane.domain.entities.test_plans import ScenarioWorkloadEntity, TestPlanEntity
from perf_control_plane.domain.ports.repositories import (
    FolderRepository,
    RunRepository,
    SavedTestConfigRepository,
    ScenarioRepository,
)
from perf_control_plane.domain.services.run_service import RunService
from perf_control_plane.utils.ids import new_id


class TestConfigService:
    def __init__(
        self,
        folder_repository: FolderRepository,
        saved_config_repository: SavedTestConfigRepository,
        scenario_repository: ScenarioRepository,
        run_repository: RunRepository,
        run_service: RunService,
    ) -> None:
        self._folder_repository = folder_repository
        self._saved_config_repository = saved_config_repository
        self._scenario_repository = scenario_repository
        self._run_repository = run_repository
        self._run_service = run_service

    async def create_folder(
        self,
        folder: TestConfigFolderEntity,
    ) -> TestConfigFolderEntity:
        return await self._folder_repository.create(
            folder.model_copy(update={"id": new_id("folder")})
        )

    async def list_folders(self) -> list[TestConfigFolderEntity]:
        return await self._folder_repository.list()

    async def get_folder_details(self, folder_id: str) -> FolderDetailsEntity:
        folder = await self._folder_repository.get(folder_id)
        configs = await self._saved_config_repository.list_by_folder(folder_id)
        return FolderDetailsEntity(folder=folder, configs=configs)

    async def create_saved_config(
        self,
        config: SavedTestConfigEntity,
    ) -> SavedTestConfigEntity:
        await self._folder_repository.get(config.folder_id)
        plan_template = await self._enrich_plan_with_scenario_names(config.plan_template)
        return await self._saved_config_repository.create(
            config.model_copy(
                update={
                    "id": new_id("config"),
                    "plan_template": plan_template,
                }
            )
        )

    async def list_saved_configs(self) -> list[SavedTestConfigEntity]:
        return await self._saved_config_repository.list()

    async def list_saved_configs_by_folder(
        self,
        folder_id: str,
    ) -> list[SavedTestConfigEntity]:
        await self._folder_repository.get(folder_id)
        return await self._saved_config_repository.list_by_folder(folder_id)

    async def get_saved_config(self, config_id: str) -> SavedTestConfigEntity:
        return await self._saved_config_repository.get(config_id)

    async def get_saved_config_details(
        self,
        config_id: str,
        *,
        recent_run_limit: int = 10,
    ) -> SavedTestConfigDetailsEntity:
        config = await self._saved_config_repository.get(config_id)
        recent_runs = await self._run_repository.list_recent_by_saved_config(
            saved_config_id=config_id,
            limit=recent_run_limit,
        )
        return SavedTestConfigDetailsEntity(config=config, recent_runs=recent_runs)

    async def submit_run_from_saved_config(
        self,
        config_id: str,
        *,
        requested_by: str,
        test_plan_override: TestPlanEntity | None = None,
    ) -> PerfTestRunEntity:
        config = await self._saved_config_repository.get(config_id)
        test_plan = (
            await self._enrich_plan_with_scenario_names(test_plan_override)
            if test_plan_override is not None
            else config.plan_template
        )
        return await self._run_service.submit_test_plan(
            test_plan=test_plan,
            requested_by=requested_by,
            saved_config_id=config.id,
        )

    async def _enrich_plan_with_scenario_names(
        self,
        plan_template: TestPlanEntity | None,
    ) -> TestPlanEntity:
        if plan_template is None:
            raise ValueError("plan_template is required")

        workloads: list[ScenarioWorkloadEntity] = []
        for workload in plan_template.workloads:
            scenario = await self._scenario_repository.get(workload.scenario_id)
            workloads.append(
                workload.model_copy(update={"scenario_name": scenario.name})
            )
        return plan_template.model_copy(update={"workloads": workloads})
