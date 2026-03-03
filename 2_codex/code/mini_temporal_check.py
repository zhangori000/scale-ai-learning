from __future__ import annotations

import asyncio
import importlib.util
import pathlib
import sys


def load_module_from_path(module_name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).with_name("mini_temporal_starter.py")
    mod = load_module_from_path("mini_temporal_target", target)
    wf_cls = mod.DemoWorkflow

    assert getattr(wf_cls, "__mini_workflow_name__", None) == "demo-workflow", "wrong workflow name metadata"
    assert getattr(wf_cls, "__mini_run_method__", None) == "on_task_create", "wrong run metadata"

    signals = getattr(wf_cls, "__mini_signal_methods__", None)
    assert isinstance(signals, dict), "signal metadata must be dict"
    assert signals.get("RECEIVE_EVENT") == "on_task_event_send", "missing signal mapping"

    async def run_checks():
        wf = wf_cls()
        out = await getattr(wf, wf_cls.__mini_run_method__)({"task_id": "t-123"})
        assert out == "created:t-123", "run method behavior changed unexpectedly"
        await getattr(wf, signals["RECEIVE_EVENT"])({"type": "message"})

    asyncio.run(run_checks())
    print("all checks passed")


if __name__ == "__main__":
    main()
