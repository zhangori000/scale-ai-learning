from __future__ import annotations

from abc import ABC, abstractmethod

from perf_control_plane.domain.entities.endpoints import EndpointEntity
from perf_control_plane.domain.entities.runs import PerfTestRunEntity
from perf_control_plane.domain.entities.scenarios import ScenarioEntity
from perf_control_plane.domain.entities.test_configs import (
    SavedTestConfigEntity,
    TestConfigFolderEntity,
)


class EndpointRepository(ABC):
    @abstractmethod
    async def create(self, endpoint: EndpointEntity) -> EndpointEntity:
        raise NotImplementedError

    @abstractmethod
    async def get(self, endpoint_id: str) -> EndpointEntity:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[EndpointEntity]:
        raise NotImplementedError


class ScenarioRepository(ABC):
    @abstractmethod
    async def create(self, scenario: ScenarioEntity) -> ScenarioEntity:
        raise NotImplementedError

    @abstractmethod
    async def get(self, scenario_id: str) -> ScenarioEntity:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[ScenarioEntity]:
        raise NotImplementedError

    @abstractmethod
    async def set_starred(self, scenario_id: str, starred: bool) -> ScenarioEntity:
        raise NotImplementedError

    @abstractmethod
    async def list_starred(self) -> list[ScenarioEntity]:
        raise NotImplementedError


class RunRepository(ABC):
    @abstractmethod
    async def create(self, run: PerfTestRunEntity) -> PerfTestRunEntity:
        raise NotImplementedError

    @abstractmethod
    async def update(self, run: PerfTestRunEntity) -> PerfTestRunEntity:
        raise NotImplementedError

    @abstractmethod
    async def get(self, run_id: str) -> PerfTestRunEntity:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[PerfTestRunEntity]:
        raise NotImplementedError

    @abstractmethod
    async def list_recent(self, limit: int) -> list[PerfTestRunEntity]:
        raise NotImplementedError

    @abstractmethod
    async def list_recent_by_saved_config(
        self,
        saved_config_id: str,
        limit: int,
    ) -> list[PerfTestRunEntity]:
        raise NotImplementedError


class FolderRepository(ABC):
    @abstractmethod
    async def create(self, folder: TestConfigFolderEntity) -> TestConfigFolderEntity:
        raise NotImplementedError

    @abstractmethod
    async def get(self, folder_id: str) -> TestConfigFolderEntity:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[TestConfigFolderEntity]:
        raise NotImplementedError


class SavedTestConfigRepository(ABC):
    @abstractmethod
    async def create(self, config: SavedTestConfigEntity) -> SavedTestConfigEntity:
        raise NotImplementedError

    @abstractmethod
    async def get(self, config_id: str) -> SavedTestConfigEntity:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[SavedTestConfigEntity]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_folder(self, folder_id: str) -> list[SavedTestConfigEntity]:
        raise NotImplementedError
