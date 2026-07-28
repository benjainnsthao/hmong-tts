"""Provider-neutral cold-load and warm-synthesis benchmark orchestration."""

from __future__ import annotations

import math
import platform
import statistics
import time
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from typing import Any

from pydantic import ValidationError

from tts_workbench import __version__
from tts_workbench.benchmark.contracts import (
    BenchmarkAggregates,
    BenchmarkObservation,
    BenchmarkReport,
    BenchmarkRequest,
    ResourceMemoryObservation,
)
from tts_workbench.benchmark.resources import ResourceObserver
from tts_workbench.environment.contracts import EnvironmentCapabilityReport
from tts_workbench.evaluation.contracts import M4FailureCategory, M4FailureDetail
from tts_workbench.inference.adapter import (
    AdapterLifecycleError,
    DependencyUnavailableError,
    DeviceUnavailableError,
    ModelLoadError,
    SynthesisError,
    TTSAdapter,
    UnknownModelError,
)
from tts_workbench.inference.contracts import ManifestModel, ManifestRuntime
from tts_workbench.inference.execution import prompt_sha256
from tts_workbench.inference.waveform import InvalidWaveformError, validate_waveform
from tts_workbench.models.schema import ModelEntry, ModelRegistry

Clock = Callable[[], float]
EnvironmentCollector = Callable[[], EnvironmentCapabilityReport]


class BenchmarkRunError(ValueError):
    """Structured pre-execution benchmark failure with no partial report."""

    def __init__(self, category: M4FailureCategory, message: str) -> None:
        super().__init__(message)
        self.failure = M4FailureDetail(category=category, message=message)


def nearest_rank_percentile(values: Sequence[float], percentile: float) -> float:
    """Return the deterministic nearest-rank percentile for non-empty values."""

    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0.0 < percentile <= 1.0:
        raise ValueError("percentile must be in (0, 1]")
    ordered = sorted(values)
    return ordered[math.ceil(percentile * len(ordered)) - 1]


def _manifest_model(entry: ModelEntry) -> ManifestModel:
    return ManifestModel(
        model_id=entry.model_id,
        provider=entry.provider,
        repository=entry.repository,
        immutable_revision=entry.revision,
        architecture=entry.architecture,
        documented_language_tag=entry.documented_language_tag,
        weight_license=entry.weight_license,
        approved_use=entry.approved_use,
        redistribution_status=entry.redistribution_status,
        prompt_set_reference=entry.prompt_set_reference,
        language_quality_status=entry.language_quality_status,
    )


def _unavailable_memory() -> ResourceMemoryObservation:
    return ResourceMemoryObservation(
        cpu_availability="unavailable",
        cuda_availability="unavailable",
    )


def _failure_for_exception(exc: Exception, *, phase: str) -> M4FailureDetail:
    categories: tuple[tuple[type[Exception], M4FailureCategory], ...] = (
        (UnknownModelError, M4FailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL),
        (DependencyUnavailableError, M4FailureCategory.DEPENDENCY_UNAVAILABLE),
        (DeviceUnavailableError, M4FailureCategory.DEVICE_UNAVAILABLE),
        (ModelLoadError, M4FailureCategory.MODEL_LOAD_FAILURE),
        (SynthesisError, M4FailureCategory.SYNTHESIS_FAILURE),
        (InvalidWaveformError, M4FailureCategory.INVALID_WAVEFORM),
        (AdapterLifecycleError, M4FailureCategory.SYNTHESIS_FAILURE),
    )
    category = next(
        (mapped for error_type, mapped in categories if isinstance(exc, error_type)),
        M4FailureCategory.MODEL_LOAD_FAILURE
        if phase == "load"
        else M4FailureCategory.SYNTHESIS_FAILURE,
    )
    return M4FailureDetail(
        category=category,
        message=(
            "Adapter model load failed within the benchmark boundary."
            if phase == "load"
            else "Adapter synthesis failed within the benchmark boundary."
        ),
    )


class BenchmarkRunner:
    """Measure one registered adapter/model pair using injected deterministic seams."""

    def __init__(
        self,
        *,
        registry: ModelRegistry,
        adapter: TTSAdapter,
        environment_collector: EnvironmentCollector,
        resource_observer: ResourceObserver,
        clock: Clock = time.perf_counter,
        workbench_version: str = __version__,
    ) -> None:
        self._registry = registry
        self._adapter = adapter
        self._environment_collector = environment_collector
        self._resource_observer = resource_observer
        self._clock = clock
        self._workbench_version = workbench_version

    @staticmethod
    def _memory(observer: ResourceObserver) -> ResourceMemoryObservation:
        try:
            return observer.observe()
        except (OSError, RuntimeError, TypeError, ValueError):
            return _unavailable_memory()

    @staticmethod
    def _validated_request(
        request: BenchmarkRequest | Mapping[str, Any],
    ) -> BenchmarkRequest:
        if isinstance(request, BenchmarkRequest):
            return request
        try:
            return BenchmarkRequest.model_validate(request)
        except (ValidationError, TypeError, ValueError) as exc:
            raise BenchmarkRunError(
                M4FailureCategory.INVALID_REQUEST,
                "Benchmark request validation failed.",
            ) from exc

    def run(self, request: BenchmarkRequest | Mapping[str, Any]) -> BenchmarkReport:
        """Run cold load, excluded warmups, and measured warm synthesis."""

        validated = self._validated_request(request)
        try:
            entry = self._registry.by_id(validated.model_id)
        except KeyError as exc:
            raise BenchmarkRunError(
                M4FailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL,
                "Model is not approved by the audited registry.",
            ) from exc
        if validated.prompt_set_reference != entry.prompt_set_reference:
            raise BenchmarkRunError(
                M4FailureCategory.INVALID_REQUEST,
                "Prompt provenance did not match the registered model.",
            )

        model = _manifest_model(entry)
        environment = self._environment_collector()
        memory_before = self._memory(self._resource_observer)
        load_start = self._clock()
        try:
            adapter_runtime = self._adapter.load(
                entry.model_id,
                validated.settings.requested_device,
            )
        except (
            AdapterLifecycleError,
            DependencyUnavailableError,
            DeviceUnavailableError,
            ModelLoadError,
            UnknownModelError,
            OSError,
            RuntimeError,
        ) as exc:
            cold_load = max(0.0, self._clock() - load_start)
            memory_after_load = self._memory(self._resource_observer)
            with suppress(AdapterLifecycleError, OSError, RuntimeError):
                self._adapter.unload()
            memory_after_unload = self._memory(self._resource_observer)
            return BenchmarkReport(
                status="failed",
                registry_schema_version=self._registry.schema_version,
                model=model,
                adapter=self._adapter.identity,
                prompt_sha256=prompt_sha256(validated.text),
                requested_device=validated.settings.requested_device,
                seed=validated.settings.seed,
                generation_settings=validated.settings.generation_settings,
                warmup_iterations=validated.settings.warmup_iterations,
                measured_repetitions=validated.settings.measured_repetitions,
                failure_handling=validated.settings.failure_handling,
                environment=environment,
                cold_load_seconds=cold_load,
                memory_before_load=memory_before,
                memory_after_load=memory_after_load,
                memory_after_unload=memory_after_unload,
                observations=(),
                aggregates=BenchmarkAggregates(
                    measured_success_count=0,
                    measured_failure_count=0,
                    failure_counts={},
                ),
                load_failure=_failure_for_exception(exc, phase="load"),
            )

        cold_load = max(0.0, self._clock() - load_start)
        memory_after_load = self._memory(self._resource_observer)
        observations: list[BenchmarkObservation] = []
        stop_requested = False
        try:
            for phase, repetitions in (
                ("warmup", validated.settings.warmup_iterations),
                ("measured", validated.settings.measured_repetitions),
            ):
                if stop_requested:
                    break
                for index in range(repetitions):
                    synthesis_start = self._clock()
                    try:
                        waveform = self._adapter.synthesize(
                            model_id=entry.model_id,
                            text=validated.text,
                            seed=validated.settings.seed,
                            generation_settings=validated.settings.generation_settings,
                        )
                        synthesis_seconds = max(0.0, self._clock() - synthesis_start)
                        metadata = validate_waveform(waveform)
                    except (
                        AdapterLifecycleError,
                        InvalidWaveformError,
                        SynthesisError,
                        OSError,
                        RuntimeError,
                        ValueError,
                    ) as exc:
                        self._clock()
                        observations.append(
                            BenchmarkObservation(
                                observation_index=index,
                                phase=phase,  # type: ignore[arg-type]
                                status="failure",
                                memory=self._memory(self._resource_observer),
                                failure=_failure_for_exception(exc, phase="synthesis"),
                            )
                        )
                        if validated.settings.failure_handling == "stop":
                            stop_requested = True
                            break
                    else:
                        observations.append(
                            BenchmarkObservation(
                                observation_index=index,
                                phase=phase,  # type: ignore[arg-type]
                                status="success",
                                synthesis_seconds=synthesis_seconds,
                                generated_audio_seconds=metadata.duration_seconds,
                                real_time_factor=(synthesis_seconds / metadata.duration_seconds),
                                memory=self._memory(self._resource_observer),
                            )
                        )
        finally:
            with suppress(AdapterLifecycleError, OSError, RuntimeError):
                self._adapter.unload()
        memory_after_unload = self._memory(self._resource_observer)

        measured = [item for item in observations if item.phase == "measured"]
        successes = [item for item in measured if item.status == "success"]
        failures = [item for item in measured if item.status == "failure"]
        synthesis_values = [
            item.synthesis_seconds for item in successes if item.synthesis_seconds is not None
        ]
        real_time_values = [
            item.real_time_factor for item in successes if item.real_time_factor is not None
        ]
        failure_counts = Counter(
            item.failure.category for item in failures if item.failure is not None
        )
        aggregates = BenchmarkAggregates(
            measured_success_count=len(successes),
            measured_failure_count=len(failures),
            median_synthesis_seconds=(
                statistics.median(synthesis_values) if synthesis_values else None
            ),
            p95_synthesis_seconds=(
                nearest_rank_percentile(synthesis_values, 0.95) if synthesis_values else None
            ),
            median_real_time_factor=(
                statistics.median(real_time_values) if real_time_values else None
            ),
            p95_real_time_factor=(
                nearest_rank_percentile(real_time_values, 0.95) if real_time_values else None
            ),
            failure_counts=dict(failure_counts),
        )
        fully_completed = len(measured) == validated.settings.measured_repetitions and not failures
        runtime = ManifestRuntime(
            python_version=platform.python_version(),
            workbench_version=self._workbench_version,
            pytorch_version=adapter_runtime.pytorch_version,
            transformers_version=adapter_runtime.transformers_version,
        )
        return BenchmarkReport(
            status="completed" if fully_completed else "partial",
            registry_schema_version=self._registry.schema_version,
            model=model,
            adapter=self._adapter.identity,
            prompt_sha256=prompt_sha256(validated.text),
            requested_device=validated.settings.requested_device,
            resolved_device=adapter_runtime.resolved_device,
            dtype=adapter_runtime.dtype,
            seed=validated.settings.seed,
            generation_settings=validated.settings.generation_settings,
            warmup_iterations=validated.settings.warmup_iterations,
            measured_repetitions=validated.settings.measured_repetitions,
            failure_handling=validated.settings.failure_handling,
            runtime=runtime,
            environment=environment,
            cold_load_seconds=cold_load,
            memory_before_load=memory_before,
            memory_after_load=memory_after_load,
            memory_after_unload=memory_after_unload,
            observations=tuple(observations),
            aggregates=aggregates,
        )
