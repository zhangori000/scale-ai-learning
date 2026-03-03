from __future__ import annotations

from typing import Any, Callable


def run(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Mark a method as the workflow run method.
    TODO: attach metadata to fn and return it.
    """
    return fn


def signal(name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Mark a method as a signal handler.
    TODO: attach metadata to fn and return it.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        return fn

    return decorator


def defn(name: str | None = None) -> Callable[[type], type]:
    """
    Mark a class as a workflow definition.

    Required class metadata:
    - __mini_workflow_name__: str
    - __mini_run_method__: str
    - __mini_signal_methods__: dict[str, str]
    """

    def decorator(cls: type) -> type:
        # TODO:
        # 1) set workflow name
        # 2) find methods marked with @run (must be exactly one)
        # 3) find methods marked with @signal
        # 4) attach required metadata and return cls
        return cls

    return decorator


@defn(name="demo-workflow")
class DemoWorkflow:
    @run
    async def on_task_create(self, payload: dict[str, Any]) -> str:
        return f"created:{payload['task_id']}"

    @signal(name="RECEIVE_EVENT")
    async def on_task_event_send(self, payload: dict[str, Any]) -> None:
        print(f"signal:{payload['type']}")


if __name__ == "__main__":
    # Quick manual peek at class-level metadata once you implement decorators.
    print("workflow name:", getattr(DemoWorkflow, "__mini_workflow_name__", None))
    print("run method:", getattr(DemoWorkflow, "__mini_run_method__", None))
    print("signals:", getattr(DemoWorkflow, "__mini_signal_methods__", None))
