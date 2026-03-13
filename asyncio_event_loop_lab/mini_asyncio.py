from __future__ import annotations

import collections
import errno
import heapq
import inspect
import os
import selectors
import socket
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Coroutine, Deque, Generic, TypeVar, cast

Callback = Callable[..., Any]
T = TypeVar("T")
_SENTINEL = object()
_running_loop: EventLoop | None = None


class CancelledError(Exception):
    """Raised when a Future or Task is cancelled."""


class InvalidStateError(RuntimeError):
    """Raised when a Future result is requested before completion."""


@dataclass(slots=True)
class Handle:
    callback: Callback
    args: tuple[Any, ...]
    cancelled: bool = False

    def cancel(self) -> None:
        self.cancelled = True


@dataclass(order=True, slots=True)
class TimerHandle:
    when: float
    sequence: int
    callback: Callback = field(compare=False)
    args: tuple[Any, ...] = field(compare=False)
    cancelled: bool = field(default=False, compare=False)

    def cancel(self) -> None:
        self.cancelled = True


class Future(Generic[T]):
    """A minimal Future implementation that Tasks can await."""

    def __init__(self, loop: EventLoop):
        self._loop = loop
        self._done = False
        self._cancelled = False
        self._result: Any = _SENTINEL
        self._exception: BaseException | None = None
        self._callbacks: list[Callable[[Future[T]], None]] = []

    def done(self) -> bool:
        return self._done

    def cancelled(self) -> bool:
        return self._cancelled

    def add_done_callback(self, callback: Callable[[Future[T]], None]) -> None:
        if self._done:
            self._loop.call_soon(callback, self)
            return
        self._callbacks.append(callback)

    def remove_done_callback(self, callback: Callable[[Future[T]], None]) -> int:
        removed = 0
        kept: list[Callable[[Future[T]], None]] = []
        for registered in self._callbacks:
            if registered is callback:
                removed += 1
            else:
                kept.append(registered)
        self._callbacks = kept
        return removed

    def cancel(self) -> bool:
        if self._done:
            return False
        self._cancelled = True
        self._done = True
        self._schedule_callbacks()
        return True

    def result(self) -> T:
        if not self._done:
            raise InvalidStateError("Future result is not ready")
        if self._cancelled:
            raise CancelledError("Future was cancelled")
        if self._exception is not None:
            raise self._exception
        return cast(T, self._result)

    def exception(self) -> BaseException | None:
        if not self._done:
            raise InvalidStateError("Future result is not ready")
        if self._cancelled:
            raise CancelledError("Future was cancelled")
        return self._exception

    def set_result(self, result: T) -> None:
        if self._done:
            raise InvalidStateError("Cannot set_result on a completed Future")
        self._result = result
        self._done = True
        self._schedule_callbacks()

    def set_exception(self, exception: BaseException) -> None:
        if self._done:
            raise InvalidStateError("Cannot set_exception on a completed Future")
        self._exception = exception
        self._done = True
        self._schedule_callbacks()

    def _schedule_callbacks(self) -> None:
        callbacks, self._callbacks = self._callbacks, []
        for callback in callbacks:
            self._loop.call_soon(callback, self)

    def __await__(self):  # type: ignore[override]
        if not self._done:
            yield self
        return self.result()

    def __repr__(self) -> str:
        state = "cancelled" if self._cancelled else "done" if self._done else "pending"
        return f"<Future state={state}>"


class Task(Future[T]):
    """Drive a coroutine forward every time the awaited Future completes."""

    def __init__(self, coro: Coroutine[Any, Any, T], loop: EventLoop, name: str):
        if not inspect.iscoroutine(coro):
            raise TypeError(f"Task requires a coroutine object, got {type(coro)!r}")
        super().__init__(loop=loop)
        self._coro = coro
        self._name = name
        self._fut_waiter: Future[Any] | None = None
        self._cancel_requested = False
        self._loop.call_soon(self._step)

    def get_name(self) -> str:
        return self._name

    def cancel(self) -> bool:
        if self.done():
            return False
        self._cancel_requested = True
        if self._fut_waiter is not None:
            cancelled = self._fut_waiter.cancel()
            if cancelled:
                return True
        self._loop.call_soon(self._step, _SENTINEL, CancelledError())
        return True

    def _step(self, value: Any = _SENTINEL, exc: BaseException | None = None) -> None:
        if self.done():
            return

        if isinstance(exc, CancelledError):
            self._cancel_requested = False
        if self._cancel_requested and exc is None:
            exc = CancelledError()
            self._cancel_requested = False

        try:
            if exc is not None:
                yielded = self._coro.throw(exc)
            elif value is _SENTINEL:
                yielded = self._coro.send(None)
            else:
                yielded = self._coro.send(value)
        except StopIteration as stop:
            self.set_result(cast(T, stop.value))
            return
        except CancelledError:
            super().cancel()
            return
        except Exception as error:  # noqa: BLE001 - educational loop catches task failures.
            self.set_exception(error)
            return

        fut = self._convert_yielded_to_future(yielded)
        if fut is None:
            self.set_exception(TypeError(f"Task got unsupported awaitable: {yielded!r}"))
            return
        if fut is self:
            self.set_exception(RuntimeError("Task cannot await itself"))
            return

        self._fut_waiter = fut
        fut.add_done_callback(self._wakeup)

    def _convert_yielded_to_future(self, yielded: Any) -> Future[Any] | None:
        if isinstance(yielded, Future):
            if yielded._loop is not self._loop:
                raise RuntimeError("Cross-loop await is not allowed")
            return yielded
        if inspect.iscoroutine(yielded):
            return self._loop.create_task(cast(Coroutine[Any, Any, Any], yielded))
        if inspect.isawaitable(yielded):
            awaitable = cast(Awaitable[Any], yielded)

            async def _bridge() -> Any:
                return await awaitable

            return self._loop.create_task(_bridge())
        return None

    def _wakeup(self, future: Future[Any]) -> None:
        if self.done():
            return

        self._fut_waiter = None
        if future.cancelled():
            self._loop.call_soon(self._step, _SENTINEL, CancelledError())
            return

        try:
            result = future.result()
        except Exception as error:  # noqa: BLE001 - propagate failure into awaiting task.
            self._loop.call_soon(self._step, _SENTINEL, error)
        else:
            self._loop.call_soon(self._step, result, None)

    def __repr__(self) -> str:
        state = "cancelled" if self.cancelled() else "done" if self.done() else "pending"
        return f"<Task name={self._name!r} state={state}>"


class EventLoop:
    """A small event loop that mirrors core asyncio mechanics."""

    def __init__(self) -> None:
        self._ready: Deque[Handle] = collections.deque()
        self._scheduled: list[TimerHandle] = []
        self._selector = selectors.DefaultSelector()
        self._readers: dict[Any, tuple[Callback, tuple[Any, ...]]] = {}
        self._writers: dict[Any, tuple[Callback, tuple[Any, ...]]] = {}
        self._stopping = False
        self._closed = False
        self._timer_sequence = 0
        self._task_sequence = 0

    def __enter__(self) -> EventLoop:
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        self.close()

    def time(self) -> float:
        return time.monotonic()

    def call_soon(self, callback: Callback, *args: Any) -> Handle:
        self._check_closed()
        handle = Handle(callback=callback, args=args)
        self._ready.append(handle)
        return handle

    def call_later(self, delay: float, callback: Callback, *args: Any) -> TimerHandle:
        self._check_closed()
        when = self.time() + max(0.0, delay)
        return self.call_at(when, callback, *args)

    def call_at(self, when: float, callback: Callback, *args: Any) -> TimerHandle:
        self._check_closed()
        handle = TimerHandle(when=when, sequence=self._next_timer_sequence(), callback=callback, args=args)
        heapq.heappush(self._scheduled, handle)
        return handle

    def create_future(self) -> Future[Any]:
        self._check_closed()
        return Future(loop=self)

    def create_task(self, coro: Coroutine[Any, Any, T], name: str | None = None) -> Task[T]:
        self._check_closed()
        task_name = name or f"task-{self._next_task_sequence()}"
        return Task(coro=coro, loop=self, name=task_name)

    def run_forever(self) -> None:
        self._check_closed()
        self._set_as_running()
        self._stopping = False
        try:
            while not self._stopping:
                if self._is_idle():
                    break
                self._run_once()
        finally:
            self._stopping = False
            self._unset_running()

    def run_until_complete(self, awaitable: Awaitable[T] | Future[T]) -> T:
        future = ensure_future(awaitable, loop=self)
        future.add_done_callback(lambda _future: self.stop())
        self.run_forever()
        if not future.done():
            raise RuntimeError("Event loop stopped before completion")
        return future.result()

    def stop(self) -> None:
        self._stopping = True

    def close(self) -> None:
        if self._closed:
            return

        self._ready.clear()
        self._scheduled.clear()
        self._readers.clear()
        self._writers.clear()
        self._selector.close()
        self._closed = True

    def add_reader(self, fileobj: Any, callback: Callback, *args: Any) -> None:
        self._check_closed()
        self._readers[fileobj] = (callback, args)
        self._sync_selector_interest(fileobj)

    def remove_reader(self, fileobj: Any) -> bool:
        existed = self._readers.pop(fileobj, None) is not None
        if existed:
            self._sync_selector_interest(fileobj)
        return existed

    def add_writer(self, fileobj: Any, callback: Callback, *args: Any) -> None:
        self._check_closed()
        self._writers[fileobj] = (callback, args)
        self._sync_selector_interest(fileobj)

    def remove_writer(self, fileobj: Any) -> bool:
        existed = self._writers.pop(fileobj, None) is not None
        if existed:
            self._sync_selector_interest(fileobj)
        return existed

    async def sock_accept(self, sock: socket.socket) -> tuple[socket.socket, tuple[Any, ...]]:
        self._check_closed()
        sock.setblocking(False)
        fut = self.create_future()

        def on_readable() -> None:
            if fut.done():
                return
            try:
                conn, addr = sock.accept()
            except (BlockingIOError, InterruptedError):
                return
            except Exception as error:  # noqa: BLE001 - surface socket failures.
                fut.set_exception(error)
                return
            conn.setblocking(False)
            fut.set_result((conn, addr))

        self.add_reader(sock, on_readable)
        try:
            return await fut
        finally:
            self.remove_reader(sock)

    async def sock_connect(self, sock: socket.socket, address: tuple[str, int]) -> None:
        self._check_closed()
        sock.setblocking(False)
        error_code = sock.connect_ex(address)
        if error_code in (0, errno.EISCONN):
            return
        if error_code not in (errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EALREADY):
            raise OSError(error_code, os.strerror(error_code))

        fut = self.create_future()

        def on_writable() -> None:
            if fut.done():
                return
            result_code = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if result_code != 0:
                fut.set_exception(OSError(result_code, os.strerror(result_code)))
                return
            fut.set_result(None)

        self.add_writer(sock, on_writable)
        try:
            await fut
        finally:
            self.remove_writer(sock)

    async def sock_recv(self, sock: socket.socket, nbytes: int) -> bytes:
        self._check_closed()
        sock.setblocking(False)
        fut = self.create_future()

        def on_readable() -> None:
            if fut.done():
                return
            try:
                data = sock.recv(nbytes)
            except (BlockingIOError, InterruptedError):
                return
            except Exception as error:  # noqa: BLE001 - surface socket failures.
                fut.set_exception(error)
                return
            fut.set_result(data)

        self.add_reader(sock, on_readable)
        try:
            return await fut
        finally:
            self.remove_reader(sock)

    async def sock_sendall(self, sock: socket.socket, data: bytes) -> None:
        self._check_closed()
        sock.setblocking(False)
        view = memoryview(data)
        sent = 0

        while sent < len(view):
            fut = self.create_future()

            def on_writable() -> None:
                nonlocal sent
                if fut.done():
                    return
                try:
                    bytes_sent = sock.send(view[sent:])
                except (BlockingIOError, InterruptedError):
                    return
                except Exception as error:  # noqa: BLE001 - surface socket failures.
                    fut.set_exception(error)
                    return

                if bytes_sent == 0:
                    fut.set_exception(RuntimeError("Socket connection closed during send"))
                    return
                sent += bytes_sent
                fut.set_result(None)

            self.add_writer(sock, on_writable)
            try:
                await fut
            finally:
                self.remove_writer(sock)

    def _run_once(self) -> None:
        self._transfer_due_timers()
        timeout = self._compute_timeout()
        events = self._poll_io(timeout)
        self._process_io_events(events)
        self._transfer_due_timers()

        ready_count = len(self._ready)
        for _ in range(ready_count):
            handle = self._ready.popleft()
            if handle.cancelled:
                continue
            self._run_handle(handle)

    def _run_handle(self, handle: Handle) -> None:
        try:
            handle.callback(*handle.args)
        except Exception as error:  # noqa: BLE001 - educational loop logs callback failures.
            print("mini_asyncio callback error:", file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__)

    def _transfer_due_timers(self) -> None:
        now = self.time()
        while self._scheduled and self._scheduled[0].when <= now:
            timer = heapq.heappop(self._scheduled)
            if timer.cancelled:
                continue
            self._ready.append(Handle(callback=timer.callback, args=timer.args))

    def _compute_timeout(self) -> float | None:
        if self._ready:
            return 0.0
        if self._scheduled:
            return max(0.0, self._scheduled[0].when - self.time())
        if self._selector.get_map():
            return None
        return 0.0

    def _poll_io(self, timeout: float | None) -> list[tuple[selectors.SelectorKey, int]]:
        if not self._selector.get_map():
            if timeout and timeout > 0:
                time.sleep(timeout)
            return []
        return self._selector.select(timeout)

    def _process_io_events(self, events: list[tuple[selectors.SelectorKey, int]]) -> None:
        for key, mask in events:
            fileobj = key.fileobj
            if mask & selectors.EVENT_READ:
                reader = self._readers.get(fileobj)
                if reader is not None:
                    callback, args = reader
                    self.call_soon(callback, *args)
            if mask & selectors.EVENT_WRITE:
                writer = self._writers.get(fileobj)
                if writer is not None:
                    callback, args = writer
                    self.call_soon(callback, *args)

    def _sync_selector_interest(self, fileobj: Any) -> None:
        mask = 0
        if fileobj in self._readers:
            mask |= selectors.EVENT_READ
        if fileobj in self._writers:
            mask |= selectors.EVENT_WRITE

        try:
            self._selector.get_key(fileobj)
            already_registered = True
        except KeyError:
            already_registered = False

        if mask == 0:
            if already_registered:
                self._selector.unregister(fileobj)
            return

        if already_registered:
            self._selector.modify(fileobj, mask)
        else:
            self._selector.register(fileobj, mask)

    def _check_closed(self) -> None:
        if self._closed:
            raise RuntimeError("Event loop is closed")

    def _is_idle(self) -> bool:
        return not self._ready and not self._scheduled and not self._selector.get_map()

    def _next_timer_sequence(self) -> int:
        self._timer_sequence += 1
        return self._timer_sequence

    def _next_task_sequence(self) -> int:
        self._task_sequence += 1
        return self._task_sequence

    def _set_as_running(self) -> None:
        global _running_loop
        if _running_loop is self:
            raise RuntimeError("This event loop is already running")
        if _running_loop is not None:
            raise RuntimeError("Cannot run a new event loop while another loop is running")
        _running_loop = self

    def _unset_running(self) -> None:
        global _running_loop
        if _running_loop is self:
            _running_loop = None


def new_event_loop() -> EventLoop:
    return EventLoop()


def get_running_loop() -> EventLoop:
    if _running_loop is None:
        raise RuntimeError("No running event loop")
    return _running_loop


def ensure_future(awaitable: Awaitable[T] | Future[T], loop: EventLoop | None = None) -> Future[T]:
    if isinstance(awaitable, Future):
        if loop is not None and awaitable._loop is not loop:
            raise RuntimeError("Future belongs to a different event loop")
        return awaitable

    target_loop = loop or get_running_loop()
    if inspect.iscoroutine(awaitable):
        return target_loop.create_task(cast(Coroutine[Any, Any, T], awaitable))
    if inspect.isawaitable(awaitable):
        wrapped = cast(Awaitable[T], awaitable)

        async def _bridge() -> T:
            return await wrapped

        return target_loop.create_task(_bridge())
    raise TypeError(f"Expected awaitable or Future, got {type(awaitable)!r}")


def run(awaitable: Awaitable[T]) -> T:
    loop = new_event_loop()
    try:
        return loop.run_until_complete(awaitable)
    finally:
        loop.close()


async def sleep(delay: float, result: T | None = None) -> T | None:
    loop = get_running_loop()
    fut = loop.create_future()
    timer = loop.call_later(delay, fut.set_result, result)
    try:
        return await fut
    finally:
        timer.cancel()


async def gather(*awaitables: Awaitable[T] | Future[T]) -> list[T]:
    loop = get_running_loop()
    tasks = [ensure_future(awaitable, loop=loop) for awaitable in awaitables]
    if not tasks:
        return []

    collector = loop.create_future()
    results: list[T | None] = [None] * len(tasks)
    remaining = len(tasks)

    def on_done(index: int, task: Future[T]) -> None:
        nonlocal remaining
        if collector.done():
            return
        if task.cancelled():
            collector.set_exception(CancelledError("A gathered task was cancelled"))
            return
        try:
            results[index] = task.result()
        except Exception as error:  # noqa: BLE001 - propagate first failure.
            collector.set_exception(error)
            return
        remaining -= 1
        if remaining == 0:
            collector.set_result(cast(list[T], results))

    for idx, task in enumerate(tasks):
        task.add_done_callback(lambda done, idx=idx: on_done(idx, cast(Future[T], done)))

    try:
        return await collector
    except CancelledError:
        for task in tasks:
            task.cancel()
        raise
