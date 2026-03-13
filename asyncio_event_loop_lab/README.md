# Asyncio Event Loop Lab

This folder contains a from-scratch asyncio-style runtime focused on learning:

- `Future`: stores eventual results and callback chains.
- `Task`: wraps a coroutine and repeatedly advances it (`send`/`throw`).
- `EventLoop`: runs ready callbacks, timer callbacks, and I/O callbacks.
- `sleep`, `gather`, and non-blocking socket helpers.

The implementation is intentionally small and explicit, not production-ready.

## Folder Layout

- `mini_asyncio.py`: core event loop implementation.
- `examples/sleep_demo.py`: timer queue + cooperative task switching.
- `examples/cancellation_demo.py`: task cancellation mechanics.
- `examples/socket_http_demo.py`: selector-driven non-blocking socket I/O.

## Run The Demos

From the repository root:

```bash
python -m asyncio_event_loop_lab.examples.sleep_demo
python -m asyncio_event_loop_lab.examples.cancellation_demo
python -m asyncio_event_loop_lab.examples.socket_http_demo
```

## How This Mirrors CPython Asyncio

1. Coroutines pause by yielding awaitables.
2. `Task` converts yielded objects into `Future`s and attaches wakeup callbacks.
3. `Future` completion schedules callbacks back onto the loop’s ready queue.
4. The loop repeatedly:
   - runs ready callbacks,
   - wakes due timers from a min-heap,
   - polls file descriptors with `selectors`.

That cycle is the core of how `asyncio` multiplexes many logical tasks on one thread.

## What Is Simplified

- No thread-safe scheduling (`call_soon_threadsafe`).
- No subprocess APIs, transports/protocols, or executors.
- Minimal cancellation semantics compared with stdlib `asyncio`.
- No debug mode, context variables, or task groups.

Use this code as a readable model of internals, then compare line-by-line with `asyncio/base_events.py` and `asyncio/tasks.py` in CPython.
