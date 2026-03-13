from __future__ import annotations

from asyncio_event_loop_lab.mini_asyncio import CancelledError, get_running_loop, run, sleep


async def ticker() -> None:
    tick = 0
    try:
        while True:
            print(f"tick {tick}")
            tick += 1
            await sleep(0.3)
    except CancelledError:
        print("ticker: cancellation received, running cleanup")
        raise


async def main() -> None:
    loop = get_running_loop()
    task = loop.create_task(ticker(), name="ticker-task")
    loop.call_later(1.2, task.cancel)

    try:
        await task
    except CancelledError:
        print("main: observed task cancellation")


if __name__ == "__main__":
    run(main())
