from __future__ import annotations

from datetime import UTC, datetime
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from perf_control_plane.domain.entities.endpoints import EndpointEntity
from perf_control_plane.domain.entities.runs import PerfTestRunEntity
from perf_control_plane.domain.entities.scenarios import ScenarioEntity
from perf_control_plane.domain.entities.test_configs import (
    SavedTestConfigEntity,
    TestConfigFolderEntity,
)
from perf_control_plane.domain.exceptions import NotFoundError
from perf_control_plane.infrastructure.models import (
    EndpointModel,
    FolderModel,
    RunModel,
    SavedTestConfigModel,
    ScenarioModel,
)

ModelT = TypeVar("ModelT")


class SqlAlchemyRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _commit(self) -> None:
        await self._session.commit()


class SqlAlchemyEndpointRepository(SqlAlchemyRepository[EndpointModel]):
    async def create(self, endpoint: EndpointEntity) -> EndpointEntity:
        model = EndpointModel(**endpoint.to_dict())
        self._session.add(model)
        await self._commit()
        await self._session.refresh(model)
        return EndpointEntity.from_model(model)

    async def get(self, endpoint_id: str) -> EndpointEntity:
        model = await self._session.get(EndpointModel, endpoint_id)
        if model is None:
            raise NotFoundError(f"endpoint not found: {endpoint_id}")
        return EndpointEntity.from_model(model)

    async def list(self) -> list[EndpointEntity]:
        rows = await self._session.execute(
            select(EndpointModel).order_by(EndpointModel.service_name)
        )
        return [EndpointEntity.from_model(item) for item in rows.scalars().all()]


class SqlAlchemyScenarioRepository(SqlAlchemyRepository[ScenarioModel]):
    async def create(self, scenario: ScenarioEntity) -> ScenarioEntity:
        model = ScenarioModel(
            id=scenario.id,
            name=scenario.name,
            owner_eid=scenario.owner_eid,
            owner_name=scenario.owner_name,
            description=scenario.description,
            is_starred=scenario.is_starred,
            steps_json=[step.to_dict(exclude_none=True) for step in scenario.steps],
            created_at=scenario.created_at,
            updated_at=scenario.updated_at,
        )
        self._session.add(model)
        await self._commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get(self, scenario_id: str) -> ScenarioEntity:
        model = await self._session.get(ScenarioModel, scenario_id)
        if model is None:
            raise NotFoundError(f"scenario not found: {scenario_id}")
        return self._to_entity(model)

    async def list(self) -> list[ScenarioEntity]:
        rows = await self._session.execute(
            select(ScenarioModel).order_by(ScenarioModel.created_at.desc())
        )
        return [self._to_entity(item) for item in rows.scalars().all()]

    async def set_starred(self, scenario_id: str, starred: bool) -> ScenarioEntity:
        model = await self._session.get(ScenarioModel, scenario_id)
        if model is None:
            raise NotFoundError(f"scenario not found: {scenario_id}")
        model.is_starred = starred
        model.updated_at = datetime.now(UTC)
        await self._commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def list_starred(self) -> list[ScenarioEntity]:
        rows = await self._session.execute(
            select(ScenarioModel)
            .where(ScenarioModel.is_starred.is_(True))
            .order_by(ScenarioModel.updated_at.desc())
        )
        return [self._to_entity(item) for item in rows.scalars().all()]

    def _to_entity(self, model: ScenarioModel) -> ScenarioEntity:
        return ScenarioEntity(
            id=model.id,
            name=model.name,
            owner_eid=model.owner_eid,
            owner_name=model.owner_name,
            description=model.description,
            is_starred=model.is_starred,
            steps=model.steps_json,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SqlAlchemyRunRepository(SqlAlchemyRepository[RunModel]):
    async def create(self, run: PerfTestRunEntity) -> PerfTestRunEntity:
        model = self._to_model(run)
        self._session.add(model)
        await self._commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def update(self, run: PerfTestRunEntity) -> PerfTestRunEntity:
        model = await self._session.get(RunModel, run.id)
        if model is None:
            raise NotFoundError(f"run not found: {run.id}")
        updated_model = self._to_model(run)
        for attribute in (
            "test_plan_name",
            "saved_config_id",
            "environment",
            "requested_by",
            "status",
            "is_rerun",
            "plan_snapshot_json",
            "compiled_plan_json",
            "validation_notes_json",
            "external_submission_json",
            "aggregate_metrics_json",
            "workload_results_json",
            "updated_at",
        ):
            setattr(model, attribute, getattr(updated_model, attribute))
        await self._commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get(self, run_id: str) -> PerfTestRunEntity:
        model = await self._session.get(RunModel, run_id)
        if model is None:
            raise NotFoundError(f"run not found: {run_id}")
        return self._to_entity(model)

    async def list(self) -> list[PerfTestRunEntity]:
        rows = await self._session.execute(select(RunModel).order_by(RunModel.created_at.desc()))
        return [self._to_entity(item) for item in rows.scalars().all()]

    async def list_recent(self, limit: int) -> list[PerfTestRunEntity]:
        rows = await self._session.execute(
            select(RunModel).order_by(RunModel.created_at.desc()).limit(limit)
        )
        return [self._to_entity(item) for item in rows.scalars().all()]

    async def list_recent_by_saved_config(
        self,
        saved_config_id: str,
        limit: int,
    ) -> list[PerfTestRunEntity]:
        rows = await self._session.execute(
            select(RunModel)
            .where(RunModel.saved_config_id == saved_config_id)
            .order_by(RunModel.created_at.desc())
            .limit(limit)
        )
        return [self._to_entity(item) for item in rows.scalars().all()]

    def _to_model(self, run: PerfTestRunEntity) -> RunModel:
        return RunModel(
            id=run.id,
            test_plan_name=run.test_plan_name,
            saved_config_id=run.saved_config_id,
            environment=run.environment,
            requested_by=run.requested_by,
            status=run.status.value,
            is_rerun=run.is_rerun,
            plan_snapshot_json=run.plan_snapshot.to_dict(exclude_none=True),
            compiled_plan_json=run.compiled_plan.to_dict(exclude_none=True),
            validation_notes_json=run.validation_notes,
            external_submission_json=(
                run.external_submission.to_dict(exclude_none=True)
                if run.external_submission
                else None
            ),
            aggregate_metrics_json=(
                run.aggregate_metrics.to_dict(exclude_none=True)
                if run.aggregate_metrics
                else None
            ),
            workload_results_json=[
                item.to_dict(exclude_none=True) for item in run.workload_results
            ],
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    def _to_entity(self, model: RunModel) -> PerfTestRunEntity:
        return PerfTestRunEntity(
            id=model.id,
            test_plan_name=model.test_plan_name,
            saved_config_id=model.saved_config_id,
            environment=model.environment,
            requested_by=model.requested_by,
            status=model.status,
            is_rerun=model.is_rerun,
            plan_snapshot=model.plan_snapshot_json,
            compiled_plan=model.compiled_plan_json,
            validation_notes=model.validation_notes_json,
            external_submission=model.external_submission_json,
            aggregate_metrics=model.aggregate_metrics_json,
            workload_results=model.workload_results_json,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SqlAlchemyFolderRepository(SqlAlchemyRepository[FolderModel]):
    async def create(self, folder: TestConfigFolderEntity) -> TestConfigFolderEntity:
        model = FolderModel(**folder.to_dict())
        self._session.add(model)
        await self._commit()
        await self._session.refresh(model)
        return TestConfigFolderEntity.from_model(model)

    async def get(self, folder_id: str) -> TestConfigFolderEntity:
        model = await self._session.get(FolderModel, folder_id)
        if model is None:
            raise NotFoundError(f"folder not found: {folder_id}")
        return TestConfigFolderEntity.from_model(model)

    async def list(self) -> list[TestConfigFolderEntity]:
        rows = await self._session.execute(
            select(FolderModel).order_by(FolderModel.updated_at.desc())
        )
        return [TestConfigFolderEntity.from_model(item) for item in rows.scalars().all()]


class SqlAlchemySavedTestConfigRepository(SqlAlchemyRepository[SavedTestConfigModel]):
    async def create(self, config: SavedTestConfigEntity) -> SavedTestConfigEntity:
        model = SavedTestConfigModel(
            id=config.id,
            folder_id=config.folder_id,
            owner_eid=config.owner_eid,
            owner_name=config.owner_name,
            name=config.name,
            description=config.description,
            plan_template_json=config.plan_template.to_dict(exclude_none=True),
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
        self._session.add(model)
        await self._commit()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def get(self, config_id: str) -> SavedTestConfigEntity:
        model = await self._session.get(SavedTestConfigModel, config_id)
        if model is None:
            raise NotFoundError(f"saved test config not found: {config_id}")
        return self._to_entity(model)

    async def list(self) -> list[SavedTestConfigEntity]:
        rows = await self._session.execute(
            select(SavedTestConfigModel).order_by(SavedTestConfigModel.updated_at.desc())
        )
        return [self._to_entity(item) for item in rows.scalars().all()]

    async def list_by_folder(self, folder_id: str) -> list[SavedTestConfigEntity]:
        rows = await self._session.execute(
            select(SavedTestConfigModel)
            .where(SavedTestConfigModel.folder_id == folder_id)
            .order_by(SavedTestConfigModel.updated_at.desc())
        )
        return [self._to_entity(item) for item in rows.scalars().all()]

    def _to_entity(self, model: SavedTestConfigModel) -> SavedTestConfigEntity:
        return SavedTestConfigEntity(
            id=model.id,
            folder_id=model.folder_id,
            owner_eid=model.owner_eid,
            owner_name=model.owner_name,
            name=model.name,
            description=model.description,
            plan_template=model.plan_template_json,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
