from __future__ import annotations

from perf_control_plane.domain.entities.endpoints import EndpointEntity
from perf_control_plane.domain.services.endpoint_service import EndpointService


class EndpointUseCase:
    def __init__(self, service: EndpointService) -> None:
        self._service = service

    async def create_endpoint(self, endpoint: EndpointEntity) -> EndpointEntity:
        return await self._service.create_endpoint(endpoint)

    async def list_endpoints(self) -> list[EndpointEntity]:
        return await self._service.list_endpoints()
