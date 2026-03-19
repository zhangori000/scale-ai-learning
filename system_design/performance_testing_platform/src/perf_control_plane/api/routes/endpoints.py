from __future__ import annotations

from fastapi import APIRouter

from perf_control_plane.api.schemas.endpoints import (
    EndpointCreateRequest,
    EndpointResponse,
)
from perf_control_plane.config.dependencies import DEndpointUseCase
from perf_control_plane.domain.entities.endpoints import EndpointEntity

router = APIRouter(prefix="/endpoints", tags=["endpoints"])


@router.post("", response_model=EndpointResponse)
async def create_endpoint(
    request: EndpointCreateRequest,
    use_case: DEndpointUseCase,
) -> EndpointResponse:
    endpoint = await use_case.create_endpoint(
        EndpointEntity(
            id="",
            service_name=request.service_name,
            method=request.method,
            path=request.path,
            base_url=request.base_url,
            owner_team=request.owner_team,
            risk_class=request.risk_class,
            description=request.description,
        )
    )
    return EndpointResponse.model_validate(endpoint)


@router.get("", response_model=list[EndpointResponse])
async def list_endpoints(use_case: DEndpointUseCase) -> list[EndpointResponse]:
    endpoints = await use_case.list_endpoints()
    return [EndpointResponse.model_validate(item) for item in endpoints]
