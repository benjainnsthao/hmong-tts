"""Deterministic M4 fakes kept outside the production package."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from tts_workbench.benchmark.contracts import ResourceMemoryObservation
from tts_workbench.inference.adapter import ModelLoadError, SynthesisError
from tts_workbench.inference.contracts import (
    AdapterIdentity,
    AdapterRuntime,
    AdapterState,
    DeviceRequest,
    GenerationSettings,
    WaveformResult,
)


class SequenceClock:
    """Return configured values without sleeping."""

    def __init__(self, values: Iterable[float]) -> None:
        self._values = iter(values)

    def __call__(self) -> float:
        return next(self._values)


@dataclass
class StaticResourceObserver:
    """Return configured point-in-time resource values in order."""

    observations: list[ResourceMemoryObservation]
    calls: int = 0

    def observe(self) -> ResourceMemoryObservation:
        value = self.observations[min(self.calls, len(self.observations) - 1)]
        self.calls += 1
        return value


@dataclass
class BenchmarkAdapter:
    """Fake adapter supporting variable durations and selected failures."""

    waveforms: list[WaveformResult]
    fail_load: bool = False
    fail_synthesis_calls: set[int] = field(default_factory=set)
    load_calls: list[tuple[str, DeviceRequest]] = field(default_factory=list)
    synthesis_calls: list[tuple[str, str, int, GenerationSettings]] = field(default_factory=list)
    unload_count: int = 0
    identity: AdapterIdentity = AdapterIdentity(
        adapter_id="benchmark-fixture",
        implementation_version="1.2.3",
    )
    _runtime: AdapterRuntime | None = None
    _model_id: str | None = None

    @property
    def state(self) -> AdapterState:
        if self._runtime is None or self._model_id is None:
            return AdapterState(lifecycle="unloaded")
        return AdapterState(
            lifecycle="loaded",
            loaded_model_id=self._model_id,
            runtime=self._runtime,
        )

    def load(self, model_id: str, requested_device: DeviceRequest) -> AdapterRuntime:
        self.load_calls.append((model_id, requested_device))
        if self.fail_load:
            raise ModelLoadError("synthetic load failure")
        resolved = "cuda" if requested_device == "cuda" else "cpu"
        self._model_id = model_id
        self._runtime = AdapterRuntime(
            requested_device=requested_device,
            resolved_device=resolved,
            dtype="float32",
            pytorch_version="fixture-torch",
            transformers_version="fixture-transformers",
        )
        return self._runtime

    def synthesize(
        self,
        *,
        model_id: str,
        text: str,
        seed: int,
        generation_settings: GenerationSettings,
    ) -> WaveformResult:
        call_index = len(self.synthesis_calls)
        self.synthesis_calls.append((model_id, text, seed, generation_settings))
        if call_index in self.fail_synthesis_calls:
            raise SynthesisError("synthetic synthesis failure")
        waveform_index = call_index - sum(
            failed < call_index for failed in self.fail_synthesis_calls
        )
        return self.waveforms[min(waveform_index, len(self.waveforms) - 1)]

    def unload(self) -> None:
        self.unload_count += 1
        self._runtime = None
        self._model_id = None
