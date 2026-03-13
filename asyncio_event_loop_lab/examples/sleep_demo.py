from __future__ import annotations

import time

from asyncio_event_loop_lab.mini_asyncio import gather, run, sleep


async def worker(name: str, delay: float) -> str:
    print(f"{name}: started, sleeping {delay:.1f}s")
    await sleep(delay)
    print(f"{name}: finished")
    return f"{name}-done"


async def main() -> None:
    started = time.perf_counter()
    results = await gather(
        worker("task-A", 1.5),
        worker("task-B", 0.5),
        worker("task-C", 1.0),
    )
    elapsed = time.perf_counter() - started

    print(f"\nresults: {results}")
    print(f"elapsed: {elapsed:.2f}s")
    print("If tasks were sequential this would be ~3.0s.")


if __name__ == "__main__":
    run(main())
