from __future__ import annotations

from abc import ABC, abstractmethod

from perf_control_plane.domain.entities.runs import (
    ExecutorSubmissionEntity,
)
from perf_control_plane.domain.entities.test_plans import CompiledTestPlanBundleEntity


class ExecutionGateway(ABC):
    @abstractmethod
    async def submit_run(
        self,
        bundle: CompiledTestPlanBundleEntity,
    ) -> ExecutorSubmissionEntity:
        raise NotImplementedError
