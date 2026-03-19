from __future__ import annotations

from perf_control_plane.domain.entities.scenarios import ScenarioEntity
from perf_control_plane.domain.exceptions import NotFoundError, ValidationError
from perf_control_plane.domain.ports.repositories import EndpointRepository, ScenarioRepository
from perf_control_plane.utils.ids import new_id


class ScenarioService:
    def __init__(
        self,
        scenario_repository: ScenarioRepository,
        endpoint_repository: EndpointRepository,
    ) -> None:
        self._scenario_repository = scenario_repository
        self._endpoint_repository = endpoint_repository

    async def create_scenario(self, scenario: ScenarioEntity) -> ScenarioEntity:
        for step in scenario.steps:
            try:
                await self._endpoint_repository.get(step.endpoint_id)
            except NotFoundError as exc:
                raise ValidationError(
                    f"scenario references unknown endpoint_id={step.endpoint_id}"
                ) from exc
        return await self._scenario_repository.create(
            scenario.model_copy(update={"id": new_id("scenario")})
        )

    async def get_scenario(self, scenario_id: str) -> ScenarioEntity:
        return await self._scenario_repository.get(scenario_id)

    async def list_scenarios(self) -> list[ScenarioEntity]:
        return await self._scenario_repository.list()

    async def list_starred_scenarios(self) -> list[ScenarioEntity]:
        return await self._scenario_repository.list_starred()

    async def set_starred(self, scenario_id: str, starred: bool) -> ScenarioEntity:
        return await self._scenario_repository.set_starred(
            scenario_id=scenario_id,
            starred=starred,
        )
