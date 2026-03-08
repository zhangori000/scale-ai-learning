from __future__ import annotations

"""
This file mirrors docs' `acp.py`.

Its job is protocol mapping:
- task/create -> Temporal client start_workflow
- event/send  -> Temporal client signal_workflow
"""

from dataclasses import dataclass
from typing import Any

from temporal_runtime import TemporalClient
from acp_types import CreateTaskParams, SendEventParams
from workflow import SignalName


@dataclass(frozen=True)
class TemporalACPConfig:
    type: str = "temporal"
    task_queue: str = "agentex-temporal-task-queue"


class TemporalACP:
    def __init__(
        self,
        temporal_client: TemporalClient,
        workflow_cls: type[Any],
        config: TemporalACPConfig,
    ) -> None:
        self.temporal_client = temporal_client
        self.workflow_cls = workflow_cls
        self.config = config

        # In this learning mock we map task_id -> workflow_id 1:1.
        self.task_to_workflow_id: dict[str, str] = {}

    def on_task_create(self, params: CreateTaskParams) -> str:
        workflow_id = params.task.id
        started_id = self.temporal_client.start_workflow(
            workflow_cls=self.workflow_cls,
            run_params=params,
            task_queue=self.config.task_queue,
            workflow_id=workflow_id,
        )
        self.task_to_workflow_id[params.task.id] = started_id
        return started_id

    def on_task_event_send(self, params: SendEventParams) -> None:
        workflow_id = self.task_to_workflow_id[params.task.id]
        self.temporal_client.signal_workflow(
            workflow_id=workflow_id,
            signal_name=SignalName.RECEIVE_EVENT,
            payload=params,
        )


class FastACP:
    @staticmethod
    def create(
        acp_type: str,
        config: TemporalACPConfig,
        temporal_client: TemporalClient,
        workflow_cls: type[Any],
    ) -> TemporalACP:
        if acp_type != "async":
            raise ValueError(f"Only async is supported in this mock, got: {acp_type}")
        if config.type != "temporal":
            raise ValueError(f"Only temporal config is supported in this mock, got: {config.type}")
        return TemporalACP(
            temporal_client=temporal_client,
            workflow_cls=workflow_cls,
            config=config,
        )
