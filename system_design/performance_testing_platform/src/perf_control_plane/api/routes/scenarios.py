from __future__ import annotations

from fastapi import APIRouter

from perf_control_plane.api.schemas.scenarios import (
    ScenarioCreateRequest,
    ScenarioResponse,
    ScenarioStarResponse,
)
from perf_control_plane.config.dependencies import DScenarioUseCase
from perf_control_plane.domain.entities.scenarios import ScenarioEntity, ScenarioStepEntity

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("", response_model=ScenarioResponse)
async def create_scenario(
    request: ScenarioCreateRequest,
    use_case: DScenarioUseCase,
) -> ScenarioResponse:
    scenario = ScenarioEntity(
        id="",
        name=request.name,
        owner_eid=request.owner_eid,
        owner_name=request.owner_name,
        description=request.description,
        is_starred=request.is_starred,
        steps=[
            ScenarioStepEntity(
                name=step.name,
                endpoint_id=step.endpoint_id,
                description=step.description,
            )
            for step in request.steps
        ],
    )
    created = await use_case.create_scenario(scenario)
    return ScenarioResponse.model_validate(created)


@router.get("", response_model=list[ScenarioResponse])
async def list_scenarios(use_case: DScenarioUseCase) -> list[ScenarioResponse]:
    scenarios = await use_case.list_scenarios()
    return [ScenarioResponse.model_validate(item) for item in scenarios]


@router.get("/starred", response_model=list[ScenarioResponse])
async def list_starred_scenarios(
    use_case: DScenarioUseCase,
) -> list[ScenarioResponse]:
    scenarios = await use_case.list_starred_scenarios()
    return [ScenarioResponse.model_validate(item) for item in scenarios]


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    use_case: DScenarioUseCase,
) -> ScenarioResponse:
    scenario = await use_case.get_scenario(scenario_id)
    return ScenarioResponse.model_validate(scenario)


@router.post("/{scenario_id}/star", response_model=ScenarioStarResponse)
async def star_scenario(
    scenario_id: str,
    use_case: DScenarioUseCase,
) -> ScenarioStarResponse:
    scenario = await use_case.set_starred(scenario_id=scenario_id, starred=True)
    return ScenarioStarResponse(id=scenario.id, is_starred=scenario.is_starred)


@router.post("/{scenario_id}/unstar", response_model=ScenarioStarResponse)
async def unstar_scenario(
    scenario_id: str,
    use_case: DScenarioUseCase,
) -> ScenarioStarResponse:
    scenario = await use_case.set_starred(scenario_id=scenario_id, starred=False)
    return ScenarioStarResponse(id=scenario.id, is_starred=scenario.is_starred)
