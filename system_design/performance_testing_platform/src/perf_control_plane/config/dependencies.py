from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

import httpx
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from perf_control_plane.config.settings import Settings, get_settings
from perf_control_plane.domain.ports.execution_gateway import ExecutionGateway
from perf_control_plane.domain.ports.repositories import (
    EndpointRepository,
    FolderRepository,
    RunRepository,
    SavedTestConfigRepository,
    ScenarioRepository,
)
from perf_control_plane.domain.services.compiler_service import CompilerService
from perf_control_plane.domain.services.endpoint_service import EndpointService
from perf_control_plane.domain.services.run_service import RunService
from perf_control_plane.domain.services.scenario_service import ScenarioService
from perf_control_plane.domain.services.test_config_service import TestConfigService
from perf_control_plane.domain.use_cases.endpoints_use_case import EndpointUseCase
from perf_control_plane.domain.use_cases.runs_use_case import RunUseCase
from perf_control_plane.domain.use_cases.scenarios_use_case import ScenarioUseCase
from perf_control_plane.domain.use_cases.test_configs_use_case import TestConfigUseCase
from perf_control_plane.infrastructure.database import DatabaseManager
from perf_control_plane.infrastructure.execution_gateway import HttpExecutionGateway
from perf_control_plane.infrastructure.repositories import (
    SqlAlchemyEndpointRepository,
    SqlAlchemyFolderRepository,
    SqlAlchemyRunRepository,
    SqlAlchemySavedTestConfigRepository,
    SqlAlchemyScenarioRepository,
)


class ApplicationContainer:
    def __init__(self) -> None:
        self.settings = Settings.from_env()
        self.database = DatabaseManager(self.settings.database_url)
        self.http_client: httpx.AsyncClient | None = None
        self._started = False

    async def startup(self) -> None:
        if self._started:
            return
        refreshed_settings = Settings.from_env()
        if refreshed_settings.database_url != self.database.database_url:
            await self.database.dispose()
            self.database = DatabaseManager(refreshed_settings.database_url)
        self.settings = refreshed_settings
        await self.database.create_schema()
        self.http_client = httpx.AsyncClient(timeout=self.settings.http_timeout_seconds)
        self._started = True

    async def shutdown(self) -> None:
        if self.http_client is not None:
            await self.http_client.aclose()
            self.http_client = None
        await self.database.dispose()
        self._started = False


container = ApplicationContainer()


def get_app_settings() -> Settings:
    return container.settings


async def get_session() -> AsyncIterator[AsyncSession]:
    async with container.database.session_factory() as session:
        yield session


def get_endpoint_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EndpointRepository:
    return SqlAlchemyEndpointRepository(session)


def get_scenario_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScenarioRepository:
    return SqlAlchemyScenarioRepository(session)


def get_run_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RunRepository:
    return SqlAlchemyRunRepository(session)


def get_folder_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FolderRepository:
    return SqlAlchemyFolderRepository(session)


def get_saved_test_config_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SavedTestConfigRepository:
    return SqlAlchemySavedTestConfigRepository(session)


def get_compiler_service() -> CompilerService:
    return CompilerService()


def get_execution_gateway(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ExecutionGateway:
    return HttpExecutionGateway(
        settings=settings,
        http_client=container.http_client,
    )


def get_endpoint_service(
    repository: Annotated[EndpointRepository, Depends(get_endpoint_repository)],
) -> EndpointService:
    return EndpointService(repository)


def get_scenario_service(
    scenario_repository: Annotated[ScenarioRepository, Depends(get_scenario_repository)],
    endpoint_repository: Annotated[EndpointRepository, Depends(get_endpoint_repository)],
) -> ScenarioService:
    return ScenarioService(
        scenario_repository=scenario_repository,
        endpoint_repository=endpoint_repository,
    )


def get_run_service(
    run_repository: Annotated[RunRepository, Depends(get_run_repository)],
    scenario_repository: Annotated[ScenarioRepository, Depends(get_scenario_repository)],
    endpoint_repository: Annotated[EndpointRepository, Depends(get_endpoint_repository)],
    compiler_service: Annotated[CompilerService, Depends(get_compiler_service)],
    execution_gateway: Annotated[ExecutionGateway, Depends(get_execution_gateway)],
) -> RunService:
    return RunService(
        run_repository=run_repository,
        scenario_repository=scenario_repository,
        endpoint_repository=endpoint_repository,
        compiler_service=compiler_service,
        execution_gateway=execution_gateway,
    )


def get_test_config_service(
    folder_repository: Annotated[FolderRepository, Depends(get_folder_repository)],
    saved_config_repository: Annotated[
        SavedTestConfigRepository,
        Depends(get_saved_test_config_repository),
    ],
    scenario_repository: Annotated[ScenarioRepository, Depends(get_scenario_repository)],
    run_repository: Annotated[RunRepository, Depends(get_run_repository)],
    run_service: Annotated[RunService, Depends(get_run_service)],
) -> TestConfigService:
    return TestConfigService(
        folder_repository=folder_repository,
        saved_config_repository=saved_config_repository,
        scenario_repository=scenario_repository,
        run_repository=run_repository,
        run_service=run_service,
    )


def get_endpoint_use_case(
    service: Annotated[EndpointService, Depends(get_endpoint_service)],
) -> EndpointUseCase:
    return EndpointUseCase(service)


def get_scenario_use_case(
    service: Annotated[ScenarioService, Depends(get_scenario_service)],
) -> ScenarioUseCase:
    return ScenarioUseCase(service)


def get_run_use_case(
    service: Annotated[RunService, Depends(get_run_service)],
) -> RunUseCase:
    return RunUseCase(service)


def get_test_config_use_case(
    service: Annotated[TestConfigService, Depends(get_test_config_service)],
) -> TestConfigUseCase:
    return TestConfigUseCase(service)


DEndpointUseCase = Annotated[EndpointUseCase, Depends(get_endpoint_use_case)]
DScenarioUseCase = Annotated[ScenarioUseCase, Depends(get_scenario_use_case)]
DRunUseCase = Annotated[RunUseCase, Depends(get_run_use_case)]
DTestConfigUseCase = Annotated[TestConfigUseCase, Depends(get_test_config_use_case)]
