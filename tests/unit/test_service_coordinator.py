from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from uuid import UUID

import pytest

from tts_workbench.inference.contracts import InferenceRequest, InferenceResult
from tts_workbench.service.contracts import ServiceFailureCategory
from tts_workbench.service.coordinator import (
    BoundedInferenceCoordinator,
    CoordinatorFailure,
)


def request(seed: int) -> InferenceRequest:
    return InferenceRequest(
        model_id="fixture-eng",
        text="synthetic queue marker",
        prompt_set_reference="builtin:synthetic-fixture-v1",
        requested_device="cpu",
        seed=seed,
        output_wav_path=f"service/{seed}.wav",
    )


@dataclass
class RecordingWorker:
    seeds: list[int] = field(default_factory=list)

    def execute(self, item: InferenceRequest) -> InferenceResult:
        self.seeds.append(item.seed)
        run_id = UUID(int=item.seed, version=4)
        return InferenceResult(
            run_id=str(run_id),
            status="success",
            wav_path=item.output_wav_path,
            manifest_path=item.output_wav_path.removesuffix(".wav") + ".manifest.json",
        )


async def _schedule_until(predicate: object) -> None:
    for _ in range(20):
        if predicate():  # type: ignore[operator]
            return
        await asyncio.sleep(0)
    raise AssertionError("deterministic coordinator state was not reached")


def test_fifo_order_and_exactly_one_active_execution() -> None:
    async def scenario() -> None:
        worker = RecordingWorker()
        started: asyncio.Queue[int] = asyncio.Queue()
        releases = {seed: asyncio.Event() for seed in (1, 2, 3)}
        active = 0
        maximum_active = 0

        async def controlled_execute(work):  # type: ignore[no-untyped-def]
            nonlocal active, maximum_active
            seed = int(work.args[0].seed)
            active += 1
            maximum_active = max(maximum_active, active)
            started.put_nowait(seed)
            await releases[seed].wait()
            try:
                return work()
            finally:
                active -= 1

        coordinator = BoundedInferenceCoordinator(
            worker=worker,
            pending_capacity=2,
            queue_timeout_seconds=30,
            execute_async=controlled_execute,
        )
        await coordinator.start()
        first = asyncio.create_task(coordinator.submit(request(1)))
        assert await started.get() == 1
        second = asyncio.create_task(coordinator.submit(request(2)))
        third = asyncio.create_task(coordinator.submit(request(3)))
        await _schedule_until(lambda: coordinator.state.pending_requests == 2)
        assert coordinator.state.admission == "full"
        assert coordinator.state.active_requests == 1

        releases[1].set()
        assert await started.get() == 2
        releases[2].set()
        assert await started.get() == 3
        releases[3].set()
        await asyncio.gather(first, second, third)
        await coordinator.shutdown()

        assert worker.seeds == [1, 2, 3]
        assert maximum_active == 1
        assert str(coordinator.state.admission) == "closed"

    asyncio.run(scenario())


def test_queue_full_and_closed_admission_are_stable() -> None:
    async def scenario() -> None:
        worker = RecordingWorker()
        active_started = asyncio.Event()
        release = asyncio.Event()

        async def blocked_execute(work):  # type: ignore[no-untyped-def]
            active_started.set()
            await release.wait()
            return work()

        coordinator = BoundedInferenceCoordinator(
            worker=worker,
            pending_capacity=1,
            queue_timeout_seconds=30,
            execute_async=blocked_execute,
        )
        with pytest.raises(CoordinatorFailure) as not_started:
            await coordinator.submit(request(1))
        assert not_started.value.category == ServiceFailureCategory.SERVICE_NOT_READY

        await coordinator.start()
        await coordinator.start()
        first = asyncio.create_task(coordinator.submit(request(1)))
        await active_started.wait()
        second = asyncio.create_task(coordinator.submit(request(2)))
        await _schedule_until(lambda: coordinator.state.pending_requests == 1)
        with pytest.raises(CoordinatorFailure) as full:
            await coordinator.submit(request(3))
        assert full.value.category == ServiceFailureCategory.QUEUE_FULL

        release.set()
        await asyncio.gather(first, second)
        await coordinator.shutdown()
        await coordinator.shutdown()
        with pytest.raises(CoordinatorFailure) as closed:
            await coordinator.submit(request(4))
        assert closed.value.category == ServiceFailureCategory.SERVICE_NOT_READY

    asyncio.run(scenario())


def test_expired_queued_request_never_invokes_worker() -> None:
    async def scenario() -> None:
        worker = RecordingWorker()
        active_started = asyncio.Event()
        release = asyncio.Event()
        now = [0.0]

        async def blocked_execute(work):  # type: ignore[no-untyped-def]
            active_started.set()
            await release.wait()
            return work()

        coordinator = BoundedInferenceCoordinator(
            worker=worker,
            pending_capacity=1,
            queue_timeout_seconds=5,
            clock=lambda: now[0],
            execute_async=blocked_execute,
        )
        await coordinator.start()
        first = asyncio.create_task(coordinator.submit(request(1)))
        await active_started.wait()
        second = asyncio.create_task(coordinator.submit(request(2)))
        await _schedule_until(lambda: coordinator.state.pending_requests == 1)
        now[0] = 10.0
        release.set()
        await first
        with pytest.raises(CoordinatorFailure) as expired:
            await second
        assert expired.value.category == ServiceFailureCategory.DEADLINE_TIMEOUT
        assert worker.seeds == [1]
        await coordinator.shutdown()

    asyncio.run(scenario())


def test_shutdown_rejects_pending_and_does_not_preempt_active_work() -> None:
    async def scenario() -> None:
        worker = RecordingWorker()
        active_started = asyncio.Event()
        release = asyncio.Event()

        async def blocked_execute(work):  # type: ignore[no-untyped-def]
            active_started.set()
            await release.wait()
            return work()

        coordinator = BoundedInferenceCoordinator(
            worker=worker,
            pending_capacity=2,
            queue_timeout_seconds=30,
            execute_async=blocked_execute,
        )
        await coordinator.start()
        active = asyncio.create_task(coordinator.submit(request(1)))
        await active_started.wait()
        pending = asyncio.create_task(coordinator.submit(request(2)))
        await _schedule_until(lambda: coordinator.state.pending_requests == 1)
        shutdown = asyncio.create_task(coordinator.shutdown())
        await _schedule_until(lambda: coordinator.state.admission == "closed")
        assert not active.done()
        with pytest.raises(CoordinatorFailure) as rejected:
            await pending
        assert rejected.value.category == ServiceFailureCategory.SERVICE_NOT_READY
        assert worker.seeds == []

        release.set()
        await active
        await shutdown
        assert worker.seeds == [1]

    asyncio.run(scenario())


def test_unexpected_executor_failure_is_sanitized() -> None:
    async def scenario() -> None:
        async def fail_execute(_work):  # type: ignore[no-untyped-def]
            raise RuntimeError("private backend marker")

        coordinator = BoundedInferenceCoordinator(
            worker=RecordingWorker(),
            pending_capacity=1,
            queue_timeout_seconds=30,
            execute_async=fail_execute,
        )
        await coordinator.start()
        with pytest.raises(CoordinatorFailure) as failure:
            await coordinator.submit(request(1))
        assert failure.value.category == ServiceFailureCategory.UNEXPECTED_INTERNAL_FAILURE
        assert "private backend marker" not in str(failure.value)
        await coordinator.shutdown()

    asyncio.run(scenario())


def test_pending_caller_cancellation_removes_work_without_execution() -> None:
    async def scenario() -> None:
        worker = RecordingWorker()
        active_started = asyncio.Event()
        release = asyncio.Event()

        async def blocked_execute(work):  # type: ignore[no-untyped-def]
            active_started.set()
            await release.wait()
            return work()

        coordinator = BoundedInferenceCoordinator(
            worker=worker,
            pending_capacity=1,
            queue_timeout_seconds=30,
            execute_async=blocked_execute,
        )
        await coordinator.start()
        active = asyncio.create_task(coordinator.submit(request(1)))
        await active_started.wait()
        pending = asyncio.create_task(coordinator.submit(request(2)))
        await _schedule_until(lambda: coordinator.state.pending_requests == 1)

        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
        assert coordinator.state.pending_requests == 0

        release.set()
        await active
        await coordinator.shutdown()
        assert worker.seeds == [1]

    asyncio.run(scenario())


def test_expiry_timer_rejects_queued_work_without_waiting_or_execution() -> None:
    async def scenario() -> None:
        worker = RecordingWorker()
        active_started = asyncio.Event()
        release = asyncio.Event()
        expiry_events: list[asyncio.Event] = []

        async def controlled_sleep(_delay: float) -> None:
            event = asyncio.Event()
            expiry_events.append(event)
            await event.wait()

        async def blocked_execute(work):  # type: ignore[no-untyped-def]
            active_started.set()
            await release.wait()
            return work()

        coordinator = BoundedInferenceCoordinator(
            worker=worker,
            pending_capacity=1,
            queue_timeout_seconds=30,
            sleeper=controlled_sleep,
            execute_async=blocked_execute,
        )
        await coordinator.start()
        active = asyncio.create_task(coordinator.submit(request(1)))
        await active_started.wait()
        expiry_count_before_pending = len(expiry_events)
        pending = asyncio.create_task(coordinator.submit(request(2)))
        await _schedule_until(lambda: coordinator.state.pending_requests == 1)
        await _schedule_until(lambda: len(expiry_events) > expiry_count_before_pending)

        expiry_events[-1].set()
        with pytest.raises(CoordinatorFailure) as expired:
            await pending
        assert expired.value.category == ServiceFailureCategory.DEADLINE_TIMEOUT

        release.set()
        await active
        await coordinator.shutdown()
        assert worker.seeds == [1]

    asyncio.run(scenario())


def test_start_after_shutdown_is_rejected() -> None:
    async def scenario() -> None:
        coordinator = BoundedInferenceCoordinator(
            worker=RecordingWorker(),
            pending_capacity=1,
            queue_timeout_seconds=1,
        )
        await coordinator.shutdown()
        with pytest.raises(CoordinatorFailure) as failure:
            await coordinator.start()
        assert failure.value.category == ServiceFailureCategory.SERVICE_NOT_READY

    asyncio.run(scenario())


def test_coordinator_rejects_unbounded_or_invalid_configuration() -> None:
    with pytest.raises(ValueError):
        BoundedInferenceCoordinator(
            worker=RecordingWorker(),
            pending_capacity=0,
            queue_timeout_seconds=1,
        )
    with pytest.raises(ValueError):
        BoundedInferenceCoordinator(
            worker=RecordingWorker(),
            pending_capacity=1,
            queue_timeout_seconds=0,
        )
