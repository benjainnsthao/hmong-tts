from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from tests.fakes.inference import synthetic_registry
from tests.fakes.m4 import BenchmarkAdapter, SequenceClock, StaticResourceObserver
from tts_workbench.benchmark.contracts import (
    BenchmarkRequest,
    BenchmarkSettings,
    ResourceMemoryObservation,
)
from tts_workbench.benchmark.runner import (
    BenchmarkRunError,
    BenchmarkRunner,
    nearest_rank_percentile,
)
from tts_workbench.environment.contracts import (
    ArtifactRootCapability,
    CommandCapability,
    CudaCapability,
    EnvironmentCapabilityReport,
    OptionalPackageCapability,
    OsCapability,
    PythonCapability,
    ReadinessCapability,
)
from tts_workbench.evaluation.contracts import M4FailureCategory
from tts_workbench.inference.contracts import GenerationSettings, WaveformResult
from tts_workbench.inference.execution import prompt_sha256

PROMPT = "synthetic benchmark marker"


def environment_report() -> EnvironmentCapabilityReport:
    core = ReadinessCapability(ready=True)
    cpu = ReadinessCapability(ready=True)
    cuda = ReadinessCapability(
        ready=False,
        failure_reasons=("cuda_runtime_unavailable", "cuda_device_unavailable"),
    )
    return EnvironmentCapabilityReport(
        python=PythonCapability(
            version="3.12.10",
            implementation="CPython",
            supported=True,
        ),
        os=OsCapability(
            system="FixtureOS",
            release="1.0",
            architecture="x86_64",
            is_wsl=False,
        ),
        git=CommandCapability(available=True, version="git version fixture"),
        ffmpeg=CommandCapability(available=False),
        artifact_root=ArtifactRootCapability(valid=True),
        pytorch=OptionalPackageCapability(available=True, version="fixture-torch"),
        transformers=OptionalPackageCapability(
            available=True,
            version="fixture-transformers",
        ),
        cuda=CudaCapability(available=False),
        cpu_supported_dtypes=("float32",),
        core=core,
        cpu_inference=cpu,
        cuda_inference=cuda,
        core_ready=True,
        cpu_inference_ready=True,
        cuda_inference_ready=False,
    )


def memory(
    cpu: int = 1024,
    cuda_allocated: int = 0,
    cuda_reserved: int = 0,
) -> ResourceMemoryObservation:
    return ResourceMemoryObservation(
        cpu_availability="available",
        cpu_peak_rss_bytes=cpu,
        cuda_availability="available",
        cuda_allocated_bytes=cuda_allocated,
        cuda_reserved_bytes=cuda_reserved,
    )


def settings(**changes: object) -> BenchmarkSettings:
    payload: dict[str, object] = {
        "warmup_iterations": 1,
        "measured_repetitions": 3,
        "maximum_repetitions": 5,
        "seed": 77,
        "generation_settings": {
            "noise_scale": 0.5,
            "noise_scale_duration": 0.6,
            "speaking_rate": 1.25,
        },
        "requested_device": "cpu",
        "observe_memory": True,
        "report_output_path": "benchmark/report.json",
        "failure_handling": "continue",
    }
    payload.update(changes)
    return BenchmarkSettings.model_validate(payload)


def request(**changes: object) -> BenchmarkRequest:
    payload: dict[str, object] = {
        "model_id": "fixture-eng",
        "text": PROMPT,
        "prompt_set_reference": "builtin:synthetic-fixture-v1",
        "settings": settings(),
    }
    payload.update(changes)
    return BenchmarkRequest.model_validate(payload)


def make_runner(
    adapter: BenchmarkAdapter,
    clock_values: list[float],
    *,
    observer: StaticResourceObserver | None = None,
) -> BenchmarkRunner:
    return BenchmarkRunner(
        registry=synthetic_registry(),
        adapter=adapter,
        environment_collector=environment_report,
        resource_observer=observer or StaticResourceObserver(observations=[memory()]),
        clock=SequenceClock(clock_values),
        workbench_version="0.3.0-fixture",
    )


def test_benchmark_contracts_are_strict_frozen_and_bounded() -> None:
    configured = settings()
    with pytest.raises(ValidationError):
        BenchmarkSettings.model_validate({**configured.model_dump(), "unexpected": True})
    with pytest.raises(ValidationError):
        configured.seed = 1  # type: ignore[misc]
    with pytest.raises(ValidationError):
        settings(measured_repetitions=6)
    with pytest.raises(ValidationError):
        settings(warmup_iterations=3, measured_repetitions=3, maximum_repetitions=5)
    with pytest.raises(ValidationError):
        ResourceMemoryObservation(
            cpu_availability="unavailable",
            cpu_peak_rss_bytes=1,
            cuda_availability="unavailable",
        )


def test_deterministic_cold_warm_timings_warmup_exclusion_and_rtf() -> None:
    waveforms = [
        WaveformResult(samples=(0.1,) * 10, sample_rate=10),
        WaveformResult(samples=(0.1,) * 20, sample_rate=10),
        WaveformResult(samples=(0.1,) * 20, sample_rate=10),
        WaveformResult(samples=(0.1,) * 20, sample_rate=10),
    ]
    adapter = BenchmarkAdapter(waveforms=waveforms)
    report = make_runner(
        adapter,
        [0, 2, 10, 10.5, 20, 21, 30, 32, 40, 43],
    ).run(request())

    assert report.status == "completed"
    assert report.cold_load_seconds == 2
    assert [item.synthesis_seconds for item in report.observations] == [0.5, 1, 2, 3]
    assert report.aggregates.measured_success_count == 3
    assert report.aggregates.median_synthesis_seconds == 2
    assert report.aggregates.p95_synthesis_seconds == 3
    assert report.aggregates.median_real_time_factor == 1
    assert report.aggregates.p95_real_time_factor == 1.5
    assert report.observations[0].phase == "warmup"
    assert report.runtime is not None
    assert report.runtime.workbench_version == "0.3.0-fixture"


def test_registry_identity_prompt_hash_and_forwarded_settings_are_exact() -> None:
    adapter = BenchmarkAdapter(waveforms=[WaveformResult(samples=(0.1,) * 10, sample_rate=10)])
    configured = settings(warmup_iterations=0, measured_repetitions=1)
    report = make_runner(adapter, [0, 1, 2, 2.25]).run(request(settings=configured))
    entry = synthetic_registry().by_id("fixture-eng")
    rendered = json.dumps(report.model_dump(mode="json"), sort_keys=True)

    assert report.model.model_id == entry.model_id
    assert report.model.repository == entry.repository
    assert report.model.immutable_revision == entry.revision
    assert report.model.prompt_set_reference == entry.prompt_set_reference
    assert report.prompt_sha256 == prompt_sha256(PROMPT)
    assert PROMPT not in rendered
    assert '"text"' not in rendered
    assert adapter.load_calls == [("fixture-eng", "cpu")]
    assert adapter.synthesis_calls == [
        (
            "fixture-eng",
            PROMPT,
            77,
            GenerationSettings(
                noise_scale=0.5,
                noise_scale_duration=0.6,
                speaking_rate=1.25,
            ),
        )
    ]
    assert report.requested_device == "cpu"
    assert report.resolved_device == "cpu"


def test_measured_failure_aggregation_and_continue_behavior() -> None:
    adapter = BenchmarkAdapter(
        waveforms=[WaveformResult(samples=(0.1,) * 10, sample_rate=10)],
        fail_synthesis_calls={2},
    )
    report = make_runner(
        adapter,
        [0, 1, 2, 2.1, 3, 3.2, 4, 4.3, 5, 5.4],
    ).run(request())

    assert report.status == "partial"
    assert report.aggregates.measured_success_count == 2
    assert report.aggregates.measured_failure_count == 1
    assert report.aggregates.failure_counts == {M4FailureCategory.SYNTHESIS_FAILURE: 1}
    assert len(adapter.synthesis_calls) == 4


def test_stop_behavior_omits_later_repetitions() -> None:
    adapter = BenchmarkAdapter(
        waveforms=[WaveformResult(samples=(0.1,) * 10, sample_rate=10)],
        fail_synthesis_calls={1},
    )
    configured = settings(failure_handling="stop")
    report = make_runner(
        adapter,
        [0, 1, 2, 2.1, 3, 3.2],
    ).run(request(settings=configured))
    assert report.status == "partial"
    assert report.aggregates.measured_failure_count == 1
    assert len(adapter.synthesis_calls) == 2


def test_load_failure_is_structured_and_unloads() -> None:
    adapter = BenchmarkAdapter(
        waveforms=[WaveformResult(samples=(0.1,), sample_rate=10)],
        fail_load=True,
    )
    report = make_runner(adapter, [0, 1]).run(request())

    assert report.status == "failed"
    assert report.load_failure is not None
    assert report.load_failure.category == M4FailureCategory.MODEL_LOAD_FAILURE
    assert report.observations == ()
    assert report.aggregates.measured_success_count == 0
    assert adapter.unload_count == 1


def test_unknown_model_and_prompt_mismatch_are_rejected_before_loading() -> None:
    adapter = BenchmarkAdapter(waveforms=[WaveformResult(samples=(0.1,), sample_rate=10)])
    runner = make_runner(adapter, [])
    with pytest.raises(BenchmarkRunError) as unknown:
        runner.run(
            {
                **request().model_dump(),
                "model_id": "missing-model",
            }
        )
    assert unknown.value.failure.category == M4FailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL
    with pytest.raises(BenchmarkRunError) as mismatch:
        runner.run(
            {
                **request().model_dump(),
                "prompt_set_reference": "external:different-reference",
            }
        )
    assert mismatch.value.failure.category == M4FailureCategory.INVALID_REQUEST
    assert adapter.load_calls == []


def test_memory_observations_preserve_available_and_unavailable_states() -> None:
    available = memory(cpu=2048, cuda_allocated=128, cuda_reserved=256)
    unavailable = ResourceMemoryObservation(
        cpu_availability="unavailable",
        cuda_availability="unavailable",
    )
    observer = StaticResourceObserver(observations=[available, unavailable])
    adapter = BenchmarkAdapter(waveforms=[WaveformResult(samples=(0.1,) * 10, sample_rate=10)])
    configured = settings(warmup_iterations=0, measured_repetitions=1)
    report = make_runner(
        adapter,
        [0, 1, 2, 3],
        observer=observer,
    ).run(request(settings=configured))
    assert report.memory_before_load == available
    assert report.memory_after_load == unavailable
    assert report.observations[0].memory == unavailable
    assert report.memory_after_unload == unavailable


def test_resource_observer_exception_becomes_unavailable() -> None:
    class FailingObserver:
        def observe(self) -> ResourceMemoryObservation:
            raise OSError("synthetic observation failure")

    adapter = BenchmarkAdapter(waveforms=[WaveformResult(samples=(0.1,) * 10, sample_rate=10)])
    configured = settings(warmup_iterations=0, measured_repetitions=1)
    runner = BenchmarkRunner(
        registry=synthetic_registry(),
        adapter=adapter,
        environment_collector=environment_report,
        resource_observer=FailingObserver(),
        clock=SequenceClock([0, 1, 2, 3]),
    )
    report = runner.run(request(settings=configured))
    assert report.memory_before_load.cpu_availability == "unavailable"
    assert report.memory_before_load.cpu_peak_rss_bytes is None


def test_nearest_rank_percentile_is_deterministic() -> None:
    assert nearest_rank_percentile([4.0, 1.0, 3.0, 2.0], 0.5) == 2.0
    assert nearest_rank_percentile([4.0, 1.0, 3.0, 2.0], 0.95) == 4.0
    with pytest.raises(ValueError):
        nearest_rank_percentile([], 0.95)
    with pytest.raises(ValueError):
        nearest_rank_percentile([1.0], 0.0)
