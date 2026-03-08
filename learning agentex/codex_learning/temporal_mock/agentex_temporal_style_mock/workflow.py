from __future__ import annotations

"""
This file mirrors the docs' `workflow.py`.
It contains workflow definition + run/signal methods only.
"""

from mock_temporalio import workflow
from temporal_runtime import call_activity
from acp_types import CreateTaskParams, SendEventParams


class SignalName:
    RECEIVE_EVENT = "event/send"


@workflow.defn(name="my-agent-workflow")
class MyAgentWorkflow:
    def __init__(self) -> None:
        self._task_id: str | None = None
        self._pending_events: list[str] = []
        self._complete_task = False

    @workflow.run
    def on_task_create(self, params: CreateTaskParams):
        """
        Entrypoint: initialize state, send welcome message, then wait for events.

        NOTE: Real Temporal uses `async def` + `await`.
        This teaching mock uses generator `yield` for pause/resume.
        """

        self._task_id = params.task.id

        yield call_activity(
            "create_message",
            task_id=params.task.id,
            author="agent",
            content="Hello! Task created.",
        )

        while not self._complete_task:
            # Wait until any signal handler appends an event.
            yield workflow.wait_condition(
                lambda: len(self._pending_events) > 0,
                description="wait for incoming event signal",
            )

            user_text = self._pending_events.pop(0)
            yield call_activity(
                "create_message",
                task_id=params.task.id,
                author="agent",
                content=f"You said: {user_text}",
            )

            if user_text.strip().lower() in {"done", "complete", "stop"}:
                self._complete_task = True

        yield call_activity(
            "create_message",
            task_id=params.task.id,
            author="agent",
            content="Task completed.",
        )
        return "Task completed"

    @workflow.signal(name=SignalName.RECEIVE_EVENT)
    def on_task_event_send(self, params: SendEventParams) -> None:
        """Signal handler: append event payload so run method can consume it."""

        self._pending_events.append(params.event.content.content)


@workflow.defn(name="coinbase-briefing-workflow")
class CoinbaseWorkflow:
    def __init__(self) -> None:
        self._task_id: str | None = None
        self._pending_events: list[str] = []
        self._complete_task = False
        self._symbols: list[str] = ["BTC", "ETH", "SOL"]

    @workflow.run
    def on_task_create(self, params: CreateTaskParams):
        self._task_id = params.task.id
        if params.params and isinstance(params.params.get("symbols"), list):
            self._symbols = [str(x).upper() for x in params.params["symbols"]]

        yield call_activity(
            "create_message",
            task_id=params.task.id,
            author="agent",
            content=f"Coinbase briefing workflow started for symbols: {', '.join(self._symbols)}",
        )

        while not self._complete_task:
            yield workflow.wait_condition(
                lambda: len(self._pending_events) > 0,
                description="wait for event/send for coinbase workflow",
            )
            user_text = self._pending_events.pop(0).strip().lower()

            if user_text in {"done", "stop", "complete"}:
                self._complete_task = True
                continue

            if user_text.startswith("scan"):
                summary = yield call_activity(
                    "fetch_briefing",
                    source="coinbase",
                    symbols=self._symbols,
                )
                sentiment = yield call_activity("analyze_sentiment", text=summary)
                yield call_activity(
                    "create_message",
                    task_id=params.task.id,
                    author="agent",
                    content=f"[Coinbase] {summary} | sentiment={sentiment}",
                )
            else:
                yield call_activity(
                    "create_message",
                    task_id=params.task.id,
                    author="agent",
                    content="Coinbase workflow understood commands: scan, done",
                )

        yield call_activity(
            "create_message",
            task_id=params.task.id,
            author="agent",
            content="Coinbase workflow completed.",
        )
        return "Coinbase workflow completed"

    @workflow.signal(name=SignalName.RECEIVE_EVENT)
    def on_task_event_send(self, params: SendEventParams) -> None:
        self._pending_events.append(params.event.content.content)


@workflow.defn(name="coindesk-briefing-workflow")
class CoindeskWorkflow:
    def __init__(self) -> None:
        self._task_id: str | None = None
        self._pending_events: list[str] = []
        self._complete_task = False
        self._topics: list[str] = ["ETF", "REGULATION"]

    @workflow.run
    def on_task_create(self, params: CreateTaskParams):
        self._task_id = params.task.id
        if params.params and isinstance(params.params.get("topics"), list):
            self._topics = [str(x).upper() for x in params.params["topics"]]

        yield call_activity(
            "create_message",
            task_id=params.task.id,
            author="agent",
            content=f"Coindesk briefing workflow started for topics: {', '.join(self._topics)}",
        )

        while not self._complete_task:
            yield workflow.wait_condition(
                lambda: len(self._pending_events) > 0,
                description="wait for event/send for coindesk workflow",
            )
            user_text = self._pending_events.pop(0).strip().lower()

            if user_text in {"done", "stop", "complete"}:
                self._complete_task = True
                continue

            if user_text.startswith("scan"):
                summary = yield call_activity(
                    "fetch_briefing",
                    source="coindesk",
                    symbols=self._topics,
                )
                sentiment = yield call_activity("analyze_sentiment", text=summary)
                yield call_activity(
                    "create_message",
                    task_id=params.task.id,
                    author="agent",
                    content=f"[Coindesk] {summary} | sentiment={sentiment}",
                )
            else:
                yield call_activity(
                    "create_message",
                    task_id=params.task.id,
                    author="agent",
                    content="Coindesk workflow understood commands: scan, done",
                )

        yield call_activity(
            "create_message",
            task_id=params.task.id,
            author="agent",
            content="Coindesk workflow completed.",
        )
        return "Coindesk workflow completed"

    @workflow.signal(name=SignalName.RECEIVE_EVENT)
    def on_task_event_send(self, params: SendEventParams) -> None:
        self._pending_events.append(params.event.content.content)
