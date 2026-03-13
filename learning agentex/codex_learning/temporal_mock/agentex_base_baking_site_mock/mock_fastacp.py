from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable


AsyncHandler = Callable[[Any], Awaitable[None]]


@dataclass(frozen=True)
class AsyncACPConfig:
    type: str = "base"


class BaseAsyncACP:
    """
    Tiny learning version of Base Async ACP.

    - Decorators register three async handlers.
    - dispatch(route, params) emulates Agentex routing ACP operations to handlers.
    """

    def __init__(self, config: AsyncACPConfig) -> None:
        self.config = config
        self._on_task_create: AsyncHandler | None = None
        self._on_task_event_send: AsyncHandler | None = None
        self._on_task_cancel: AsyncHandler | None = None

    def on_task_create(self, fn: AsyncHandler) -> AsyncHandler:
        self._on_task_create = fn
        return fn

    def on_task_event_send(self, fn: AsyncHandler) -> AsyncHandler:
        self._on_task_event_send = fn
        return fn

    def on_task_cancel(self, fn: AsyncHandler) -> AsyncHandler:
        self._on_task_cancel = fn
        return fn

    async def handle_task_create(self, params: Any) -> None:
        if self._on_task_create is None:
            raise RuntimeError("Missing @acp.on_task_create handler")
        await self._on_task_create(params)

    async def handle_task_event_send(self, params: Any) -> None:
        if self._on_task_event_send is None:
            raise RuntimeError("Missing @acp.on_task_event_send handler")
        await self._on_task_event_send(params)

    async def handle_task_cancel(self, params: Any) -> None:
        if self._on_task_cancel is None:
            raise RuntimeError("Missing @acp.on_task_cancel handler")
        await self._on_task_cancel(params)

    async def dispatch(self, route: str, params: Any) -> None:
        if route == "task/create":
            await self.handle_task_create(params)
            return
        if route == "event/send":
            await self.handle_task_event_send(params)
            return
        if route == "task/cancel":
            await self.handle_task_cancel(params)
            return
        raise ValueError(f"Unknown ACP route: {route}")


class FastACP:
    @staticmethod
    def create(acp_type: str, config: AsyncACPConfig) -> BaseAsyncACP:
        if acp_type != "async":
            raise ValueError(f"Only async is supported in this mock, got: {acp_type}")
        if config.type != "base":
            raise ValueError(f"Only base config is supported in this mock, got: {config.type}")
        return BaseAsyncACP(config=config)
