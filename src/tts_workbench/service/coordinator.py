"""One-owner bounded FIFO coordination for local inference."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from functools import partial
from typing import Literal, Protocol

from tts_workbench.inference.contracts import InferenceRequest, InferenceResult
from tts_workbench.service.contracts import (
    QueueAdmissionState,
    ServiceFailureCategory,
)

Clock = Callable[[], float]
Sleeper = Callable[[float], Awaitable[None]]
ExecuteAsync = Callable[[Callable[[], InferenceResult]], Awaitable[InferenceResult]]


class InferenceWorker(Protocol):
    """Synchronous M3 execution seam owned by the coordinator."""

    def execute(self, request: InferenceRequest) -> InferenceResult:
        """Execute exactly one validated inference request."""


class InferenceCoordinator(Protocol):
    """Application-facing bounded coordinator contract."""

    @property
    def state(self) -> QueueAdmissionState:
        """Return a non-identifying state snapshot."""

    async def start(self) -> None:
        """Open admission and start the single worker."""

    async def submit(self, request: InferenceRequest) -> InferenceResult:
        """Admit and execute one request or raise a stable coordinator failure."""

    async def shutdown(self) -> None:
        """Close admission, reject pending work, and await active work."""


class CoordinatorFailure(RuntimeError):
    """Stable coordinator failure without request or backend content."""

    def __init__(self, category: ServiceFailureCategory, message: str) -> None:
        super().__init__(message)
        self.category = category


async def _execute_in_thread(work: Callable[[], InferenceResult]) -> InferenceResult:
    return await asyncio.to_thread(work)


@dataclass(eq=False)
class _QueuedWork:
    request: InferenceRequest
    future: asyncio.Future[InferenceResult]
    deadline: float
    expiry_task: asyncio.Task[None] | None = None


class BoundedInferenceCoordinator:
    """Serialize a bounded FIFO queue through exactly one active worker call."""

    def __init__(
        self,
        *,
        worker: InferenceWorker,
        pending_capacity: int,
        queue_timeout_seconds: float,
        clock: Clock = time.monotonic,
        sleeper: Sleeper = asyncio.sleep,
        execute_async: ExecuteAsync = _execute_in_thread,
    ) -> None:
        if pending_capacity < 1:
            raise ValueError("pending capacity must be positive")
        if queue_timeout_seconds <= 0:
            raise ValueError("queue timeout must be positive")
        self._worker = worker
        self._capacity = pending_capacity
        self._queue_timeout = queue_timeout_seconds
        self._clock = clock
        self._sleeper = sleeper
        self._execute_async = execute_async
        self._condition = asyncio.Condition()
        self._pending: deque[_QueuedWork] = deque()
        self._active: _QueuedWork | None = None
        self._worker_task: asyncio.Task[None] | None = None
        self._accepting = False
        self._closed = False

    @property
    def state(self) -> QueueAdmissionState:
        if not self._accepting:
            admission: Literal["open", "full", "closed"] = "closed"
        elif len(self._pending) >= self._capacity:
            admission = "full"
        else:
            admission = "open"
        return QueueAdmissionState(
            admission=admission,
            pending_capacity=self._capacity,
            pending_requests=len(self._pending),
            active_requests=int(self._active is not None),
        )

    async def start(self) -> None:
        async with self._condition:
            if self._closed:
                raise CoordinatorFailure(
                    ServiceFailureCategory.SERVICE_NOT_READY,
                    "service admission is closed",
                )
            if self._worker_task is not None:
                return
            self._accepting = True
            self._worker_task = asyncio.create_task(
                self._worker_loop(),
                name="tts-workbench-inference-owner",
            )
            self._condition.notify_all()

    async def submit(self, request: InferenceRequest) -> InferenceResult:
        loop = asyncio.get_running_loop()
        async with self._condition:
            if not self._accepting or self._closed or self._worker_task is None:
                raise CoordinatorFailure(
                    ServiceFailureCategory.SERVICE_NOT_READY,
                    "service admission is closed",
                )
            if len(self._pending) >= self._capacity:
                raise CoordinatorFailure(
                    ServiceFailureCategory.QUEUE_FULL,
                    "inference queue is full",
                )
            item = _QueuedWork(
                request=request,
                future=loop.create_future(),
                deadline=self._clock() + self._queue_timeout,
            )
            self._pending.append(item)
            item.expiry_task = asyncio.create_task(self._expire(item))
            self._condition.notify_all()

        try:
            return await asyncio.shield(item.future)
        except asyncio.CancelledError:
            await self._remove_cancelled_pending(item)
            raise

    async def _remove_cancelled_pending(self, item: _QueuedWork) -> None:
        async with self._condition:
            with suppress(ValueError):
                self._pending.remove(item)
                self._cancel_expiry(item)
                if not item.future.done():
                    item.future.cancel()
                self._condition.notify_all()

    async def _expire(self, item: _QueuedWork) -> None:
        try:
            await self._sleeper(max(0.0, item.deadline - self._clock()))
        except asyncio.CancelledError:
            return
        async with self._condition:
            try:
                self._pending.remove(item)
            except ValueError:
                return
            if not item.future.done():
                item.future.set_exception(
                    CoordinatorFailure(
                        ServiceFailureCategory.DEADLINE_TIMEOUT,
                        "request expired before inference began",
                    )
                )
            self._condition.notify_all()

    @staticmethod
    def _cancel_expiry(item: _QueuedWork) -> None:
        if item.expiry_task is not None and not item.expiry_task.done():
            item.expiry_task.cancel()

    async def _worker_loop(self) -> None:
        while True:
            async with self._condition:
                await self._condition.wait_for(lambda: bool(self._pending) or not self._accepting)
                if not self._pending and not self._accepting:
                    return
                item = self._pending.popleft()
                if self._clock() >= item.deadline:
                    self._cancel_expiry(item)
                    if not item.future.done():
                        item.future.set_exception(
                            CoordinatorFailure(
                                ServiceFailureCategory.DEADLINE_TIMEOUT,
                                "request expired before inference began",
                            )
                        )
                    continue
                self._cancel_expiry(item)
                self._active = item
                self._condition.notify_all()

            try:
                result = await self._execute_async(partial(self._worker.execute, item.request))
            except Exception:
                failure: InferenceResult | CoordinatorFailure = CoordinatorFailure(
                    ServiceFailureCategory.UNEXPECTED_INTERNAL_FAILURE,
                    "inference execution failed unexpectedly",
                )
            else:
                failure = result

            async with self._condition:
                self._active = None
                if not item.future.done():
                    if isinstance(failure, CoordinatorFailure):
                        item.future.set_exception(failure)
                    else:
                        item.future.set_result(failure)
                self._condition.notify_all()

    async def shutdown(self) -> None:
        async with self._condition:
            if self._closed:
                task = self._worker_task
            else:
                self._accepting = False
                self._closed = True
                while self._pending:
                    item = self._pending.popleft()
                    self._cancel_expiry(item)
                    if not item.future.done():
                        item.future.set_exception(
                            CoordinatorFailure(
                                ServiceFailureCategory.SERVICE_NOT_READY,
                                "service shut down before inference began",
                            )
                        )
                self._condition.notify_all()
                task = self._worker_task
        if task is not None:
            await task
