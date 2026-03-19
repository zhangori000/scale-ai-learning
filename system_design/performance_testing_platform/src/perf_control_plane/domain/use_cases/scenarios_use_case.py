from __future__ import annotations

from perf_control_plane.domain.entities.scenarios import ScenarioEntity
from perf_control_plane.domain.services.scenario_service import ScenarioService


class ScenarioUseCase:
    def __init__(self, service: ScenarioService) -> None:
        self._service = service

    async def create_scenario(self, scenario: ScenarioEntity) -> ScenarioEntity:
        return await self._service.create_scenario(scenario)

    async def get_scenario(self, scenario_id: str) -> ScenarioEntity:
        return await self._service.get_scenario(scenario_id)

    async def list_scenarios(self) -> list[ScenarioEntity]:
        return await self._service.list_scenarios()

    async def list_starred_scenarios(self) -> list[ScenarioEntity]:
        return await self._service.list_starred_scenarios()

    async def set_starred(self, scenario_id: str, starred: bool) -> ScenarioEntity:
        return await self._service.set_starred(scenario_id, starred)
