from __future__ import annotations

from typing import Any, Callable


def run(fn: Callable[..., Any]) -> Callable[..., Any]:
    setattr(fn, "__mini_is_run__", True)
    return fn


def signal(name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        signal_name = name or fn.__name__
        setattr(fn, "__mini_signal_name__", signal_name)
        return fn

    return decorator


def defn(name: str | None = None) -> Callable[[type], type]:
    def decorator(cls: type) -> type:
        workflow_name = name or cls.__name__
        setattr(cls, "__mini_workflow_name__", workflow_name)

        run_methods: list[str] = []
        signal_methods: dict[str, str] = {}

        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if getattr(attr, "__mini_is_run__", False):
                run_methods.append(attr_name)
            signal_name = getattr(attr, "__mini_signal_name__", None)
            if signal_name is not None:
                signal_methods[signal_name] = attr_name

        if len(run_methods) != 1:
            raise ValueError(
                f"{cls.__name__} must define exactly one @run method, found {len(run_methods)}"
            )

        setattr(cls, "__mini_run_method__", run_methods[0])
        setattr(cls, "__mini_signal_methods__", signal_methods)
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
    print("workflow name:", getattr(DemoWorkflow, "__mini_workflow_name__", None))
    print("run method:", getattr(DemoWorkflow, "__mini_run_method__", None))
    print("signals:", getattr(DemoWorkflow, "__mini_signal_methods__", None))
