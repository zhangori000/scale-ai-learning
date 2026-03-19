from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from perf_control_plane.api.routes.endpoints import router as endpoints_router
from perf_control_plane.api.routes.runs import router as runs_router
from perf_control_plane.api.routes.scenarios import router as scenarios_router
from perf_control_plane.api.routes.test_configs import router as test_configs_router
from perf_control_plane.config.dependencies import container
from perf_control_plane.domain.exceptions import DomainError


@asynccontextmanager
async def lifespan(_: FastAPI):
    await container.startup()
    try:
        yield
    finally:
        await container.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Performance Testing Control Plane",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(endpoints_router)
    app.include_router(scenarios_router)
    app.include_router(runs_router)
    app.include_router(test_configs_router)

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(DomainError)
    async def handle_domain_error(
        _: Request,
        exc: DomainError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.code, "message": exc.message},
        )

    return app
