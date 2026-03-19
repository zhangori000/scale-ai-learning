from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class DatabaseManager:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.engine = create_async_engine(database_url, future=True)
        self._session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )

    @property
    def session_factory(self) -> async_sessionmaker:
        return self._session_factory

    async def create_schema(self) -> None:
        from perf_control_plane.infrastructure import models  # noqa: F401

        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        await self.engine.dispose()
