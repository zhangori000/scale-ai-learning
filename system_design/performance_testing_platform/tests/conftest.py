from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def configure_test_database(tmp_path: Path):
    os.environ["PERF_CONTROL_PLANE_DATABASE_URL"] = (
        f"sqlite+aiosqlite:///{tmp_path / 'perf_control_plane_test.db'}"
    )
    yield
    os.environ.pop("PERF_CONTROL_PLANE_DATABASE_URL", None)
