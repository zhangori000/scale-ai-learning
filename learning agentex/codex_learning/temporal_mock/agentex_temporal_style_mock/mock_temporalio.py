from __future__ import annotations

"""
Tiny "temporalio-like" decorator surface for learning.

This is NOT the real Temporal SDK. It only models a few concepts so you can map
docs examples to runtime behavior.
"""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class WaitCondition:
    """Represents "pause workflow until predicate() becomes True"."""

    predicate: Callable[[], bool]
    description: str = ""


class workflow:
    """Namespace matching `from temporalio import workflow` style."""

    @staticmethod
    def defn(name: str | None = None) -> Callable[[type[Any]], type[Any]]:
        """Mark a class as a workflow definition."""

        def decorator(cls: type[Any]) -> type[Any]:
            cls.__workflow_name__ = name or cls.__name__
            return cls

        return decorator

    @staticmethod
    def run(fn: Callable[..., Any]) -> Callable[..., Any]:
        """Mark a method as workflow entrypoint."""

        fn.__is_workflow_run__ = True
        return fn

    @staticmethod
    def signal(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Mark a method as signal handler for `name`."""

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            fn.__workflow_signal_name__ = name
            return fn

        return decorator

    @staticmethod
    def wait_condition(predicate: Callable[[], bool], description: str = "") -> WaitCondition:
        """
        In real Temporal this is awaited.
        In this teaching mock, workflow code yields this command.
        """

        return WaitCondition(predicate=predicate, description=description)
