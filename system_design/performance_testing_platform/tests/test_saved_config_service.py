from __future__ import annotations

import asyncio

from perf_control_plane.config.settings import Settings
from perf_control_plane.domain.entities.endpoints import EndpointEntity, HttpMethod, RiskClass
from perf_control_plane.domain.entities.load_profiles import (
    BudgetSegmentEntity,
    BudgetRampProfileEntity,
)
from perf_control_plane.domain.entities.runs import PerfTestRunEntity
from perf_control_plane.domain.entities.scenarios import (
    ScenarioEntity,
    ScenarioStepEntity,
)
from perf_control_plane.domain.entities.test_configs import (
    SavedTestConfigEntity,
    TestConfigFolderEntity as FolderEntityModel,
)
from perf_control_plane.domain.entities.test_plans import (
    ScenarioWorkloadEntity,
    TestPlanEntity as PlanTemplateEntity,
    WorkloadExecutionSettingsEntity,
    WorkloadRole,
)
from perf_control_plane.domain.ports.repositories import (
    EndpointRepository,
    FolderRepository,
    RunRepository,
    SavedTestConfigRepository,
    ScenarioRepository,
)
from perf_control_plane.domain.services.compiler_service import CompilerService
from perf_control_plane.domain.services.run_service import RunService
from perf_control_plane.domain.services.test_config_service import (
    TestConfigService as SavedConfigService,
)
from perf_control_plane.infrastructure.execution_gateway import HttpExecutionGateway


class InMemoryEndpointRepository(EndpointRepository):
    def __init__(self, endpoints: dict[str, EndpointEntity]) -> None:
        self._endpoints = endpoints

    async def create(self, endpoint: EndpointEntity) -> EndpointEntity:
        self._endpoints[endpoint.id] = endpoint
        return endpoint

    async def get(self, endpoint_id: str) -> EndpointEntity:
        return self._endpoints[endpoint_id]

    async def list(self) -> list[EndpointEntity]:
        return list(self._endpoints.values())


class InMemoryScenarioRepository(ScenarioRepository):
    def __init__(self, scenarios: dict[str, ScenarioEntity]) -> None:
        self._scenarios = scenarios

    async def create(self, scenario: ScenarioEntity) -> ScenarioEntity:
        self._scenarios[scenario.id] = scenario
        return scenario

    async def get(self, scenario_id: str) -> ScenarioEntity:
        return self._scenarios[scenario_id]

    async def list(self) -> list[ScenarioEntity]:
        return list(self._scenarios.values())

    async def set_starred(self, scenario_id: str, starred: bool) -> ScenarioEntity:
        scenario = self._scenarios[scenario_id]
        updated = scenario.model_copy(update={"is_starred": starred})
        self._scenarios[scenario_id] = updated
        return updated

    async def list_starred(self) -> list[ScenarioEntity]:
        return [item for item in self._scenarios.values() if item.is_starred]


class InMemoryRunRepository(RunRepository):
    def __init__(self) -> None:
        self._runs: dict[str, PerfTestRunEntity] = {}

    async def create(self, run: PerfTestRunEntity) -> PerfTestRunEntity:
        self._runs[run.id] = run
        return run

    async def update(self, run: PerfTestRunEntity) -> PerfTestRunEntity:
        self._runs[run.id] = run
        return run

    async def get(self, run_id: str) -> PerfTestRunEntity:
        return self._runs[run_id]

    async def list(self) -> list[PerfTestRunEntity]:
        return sorted(self._runs.values(), key=lambda item: item.created_at, reverse=True)

    async def list_recent(self, limit: int) -> list[PerfTestRunEntity]:
        return (await self.list())[:limit]

    async def list_recent_by_saved_config(
        self,
        saved_config_id: str,
        limit: int,
    ) -> list[PerfTestRunEntity]:
        runs = [
            item
            for item in self._runs.values()
            if item.saved_config_id == saved_config_id
        ]
        runs.sort(key=lambda item: item.created_at, reverse=True)
        return runs[:limit]


class InMemoryFolderRepository(FolderRepository):
    def __init__(self) -> None:
        self._folders = {}

    async def create(self, folder: FolderEntityModel) -> FolderEntityModel:
        self._folders[folder.id] = folder
        return folder

    async def get(self, folder_id: str) -> FolderEntityModel:
        return self._folders[folder_id]

    async def list(self) -> list[FolderEntityModel]:
        return list(self._folders.values())


class InMemorySavedConfigRepository(SavedTestConfigRepository):
    def __init__(self) -> None:
        self._configs = {}

    async def create(self, config: SavedTestConfigEntity) -> SavedTestConfigEntity:
        self._configs[config.id] = config
        return config

    async def get(self, config_id: str) -> SavedTestConfigEntity:
        return self._configs[config_id]

    async def list(self) -> list[SavedTestConfigEntity]:
        return list(self._configs.values())

    async def list_by_folder(self, folder_id: str) -> list[SavedTestConfigEntity]:
        return [
            item for item in self._configs.values() if item.folder_id == folder_id
        ]


def _stub_gateway() -> HttpExecutionGateway:
    return HttpExecutionGateway(
        settings=Settings(
            executor_mode="stub",
            executor_base_url="https://stub-executor.example",
        ),
        http_client=None,
    )


def _endpoints() -> dict[str, EndpointEntity]:
    return {
        "ep_provision": EndpointEntity(
            id="ep_provision",
            service_name="ledger",
            method=HttpMethod.POST,
            path="/provision",
            owner_team="ledger",
            risk_class=RiskClass.MODERATE,
        ),
        "ep_post": EndpointEntity(
            id="ep_post",
            service_name="ledger",
            method=HttpMethod.POST,
            path="/post",
            owner_team="ledger",
            risk_class=RiskClass.MODERATE,
        ),
        "ep_eod": EndpointEntity(
            id="ep_eod",
            service_name="ledger",
            method=HttpMethod.POST,
            path="/end_of_day",
            owner_team="ledger",
            risk_class=RiskClass.EXPENSIVE,
        ),
    }


def test_saved_config_links_recent_plan_runs_and_stub_workload_metrics():
    async def scenario() -> None:
        setup_scenario = ScenarioEntity(
            id="scenario_setup",
            name="provision_accounts",
            owner_eid="eid_alice",
            owner_name="Alice",
            steps=[
                ScenarioStepEntity(
                    name="provision",
                    endpoint_id="ep_provision",
                ),
            ],
        )
        measured_scenario = ScenarioEntity(
            id="scenario_main",
            name="post_then_eod",
            owner_eid="eid_alice",
            owner_name="Alice",
            steps=[
                ScenarioStepEntity(
                    name="post",
                    endpoint_id="ep_post",
                ),
                ScenarioStepEntity(
                    name="eod",
                    endpoint_id="ep_eod",
                ),
            ],
        )
        scenario_repository = InMemoryScenarioRepository(
            {
                setup_scenario.id: setup_scenario,
                measured_scenario.id: measured_scenario,
            }
        )
        run_repository = InMemoryRunRepository()
        run_service = RunService(
            run_repository=run_repository,
            scenario_repository=scenario_repository,
            endpoint_repository=InMemoryEndpointRepository(_endpoints()),
            compiler_service=CompilerService(),
            execution_gateway=_stub_gateway(),
        )
        service = SavedConfigService(
            folder_repository=InMemoryFolderRepository(),
            saved_config_repository=InMemorySavedConfigRepository(),
            scenario_repository=scenario_repository,
            run_repository=run_repository,
            run_service=run_service,
        )

        folder = await service.create_folder(
            FolderEntityModel(
                id="",
                name="ledger-shared",
                owner_eid="eid_alice",
                owner_name="Alice",
                description="Reusable ledger plans",
            )
        )
        saved_config = await service.create_saved_config(
            SavedTestConfigEntity(
                id="",
                folder_id=folder.id,
                owner_eid="eid_alice",
                owner_name="Alice",
                name="east-coast-ramp",
                description="Baseline sequential plan",
                plan_template=PlanTemplateEntity(
                    name="ledger-vx-east",
                    environment="perf-cell-a",
                    workloads=[
                        ScenarioWorkloadEntity(
                            name="preload",
                            scenario_id=setup_scenario.id,
                            role=WorkloadRole.SETUP,
                            execution_settings=WorkloadExecutionSettingsEntity(
                                budget_segments=[
                                    BudgetSegmentEntity(
                                        share=1.0,
                                        scenario_starts_per_second=500,
                                    ),
                                ],
                                max_total_scenario_starts=25_000,
                            ),
                        ),
                        ScenarioWorkloadEntity(
                            name="measure",
                            scenario_id=measured_scenario.id,
                            role=WorkloadRole.MEASURED,
                            execution_settings=WorkloadExecutionSettingsEntity(
                                budget_ramp_profile=BudgetRampProfileEntity(
                                    part_count=3,
                                    initial_scenario_starts_per_second=1000,
                                    step_size=250,
                                ),
                                max_total_scenario_starts=120_000,
                            ),
                        ),
                    ],
                ),
            )
        )

        run = await service.submit_run_from_saved_config(
            saved_config.id,
            requested_by="bob",
        )
        details = await service.get_saved_config_details(saved_config.id)

        assert details.config.folder_id == folder.id
        assert details.config.plan_template.workloads[0].scenario_name == "provision_accounts"
        assert details.config.plan_template.workloads[1].scenario_name == "post_then_eod"
        assert run.status.value == "completed"
        assert run.aggregate_metrics is not None
        assert len(run.workload_results) == 2
        assert len(details.recent_runs) == 1
        assert details.recent_runs[0].saved_config_id == saved_config.id
        assert details.recent_runs[0].workload_results[1].p95_ms is not None

    asyncio.run(scenario())
