from __future__ import annotations

import os
from functools import lru_cache

from perf_control_plane.domain.entities.base import BaseModel


class Settings(BaseModel):
    app_name: str = "perf-control-plane"
    environment: str = "local"
    database_url: str = (
        "sqlite+aiosqlite:///./system_design/performance_testing_platform/perf_control_plane.db"
    )
    executor_mode: str = "stub"
    executor_base_url: str = "http://localhost:8081"
    executor_submit_path: str = "/runs"
    http_timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("PERF_CONTROL_PLANE_APP_NAME", cls.model_fields["app_name"].default),
            environment=os.getenv("PERF_CONTROL_PLANE_ENVIRONMENT", cls.model_fields["environment"].default),
            database_url=os.getenv("PERF_CONTROL_PLANE_DATABASE_URL", cls.model_fields["database_url"].default),
            executor_mode=os.getenv("PERF_CONTROL_PLANE_EXECUTOR_MODE", cls.model_fields["executor_mode"].default),
            executor_base_url=os.getenv(
                "PERF_CONTROL_PLANE_EXECUTOR_BASE_URL",
                cls.model_fields["executor_base_url"].default,
            ),
            executor_submit_path=os.getenv(
                "PERF_CONTROL_PLANE_EXECUTOR_SUBMIT_PATH",
                cls.model_fields["executor_submit_path"].default,
            ),
            http_timeout_seconds=float(
                os.getenv(
                    "PERF_CONTROL_PLANE_HTTP_TIMEOUT_SECONDS",
                    cls.model_fields["http_timeout_seconds"].default,
                )
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
