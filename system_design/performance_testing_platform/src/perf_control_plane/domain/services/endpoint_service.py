from __future__ import annotations

from perf_control_plane.domain.entities.endpoints import EndpointEntity
from perf_control_plane.domain.ports.repositories import EndpointRepository
from perf_control_plane.utils.ids import new_id


class EndpointService:
    def __init__(self, repository: EndpointRepository) -> None:
        self._repository = repository

    async def create_endpoint(self, endpoint: EndpointEntity) -> EndpointEntity:
        return await self._repository.create(
            endpoint.model_copy(update={"id": new_id("endpoint")})
        )

    async def list_endpoints(self) -> list[EndpointEntity]:
        return await self._repository.list()
