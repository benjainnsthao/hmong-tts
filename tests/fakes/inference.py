"""Synthetic fakes for inference tests; never imported by runtime code."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tts_workbench.inference.adapter import (
    DependencyUnavailableError,
    DeviceUnavailableError,
    ModelLoadError,
    SynthesisError,
)
from tts_workbench.inference.contracts import (
    AdapterIdentity,
    AdapterRuntime,
    AdapterState,
    DeviceRequest,
    GenerationSettings,
    WaveformResult,
)
from tts_workbench.models.schema import ModelRegistry


def synthetic_registry() -> ModelRegistry:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "models": [
            {
                "model_id": "fixture-eng",
                "provider": "Synthetic Provider",
                "repository": "synthetic/fixture-eng",
                "revision": "1" * 40,
                "documented_language_tag": "eng",
                "language_tag_standard": "ISO 639-3",
                "architecture": "vits",
                "weight_license": "Apache-2.0",
                "approved_use": "local_noncommercial_inference",
                "redistribution_status": "weights_not_redistributed",
                "prompt_set_reference": "builtin:synthetic-fixture-v1",
                "language_quality_status": "not_evaluated",
                "provenance": {
                    "model_card_url": "https://example.test/model-card",
                    "license_url": "https://example.test/license",
                    "audit_reference": "docs/license_matrix.md",
                    "audited_on": "2026-07-14",
                },
            },
            {
                "model_id": "fixture-vie",
                "provider": "Synthetic Provider",
                "repository": "synthetic/fixture-vie",
                "revision": "2" * 40,
                "documented_language_tag": "vie",
                "language_tag_standard": "ISO 639-3",
                "architecture": "vits",
                "weight_license": "Apache-2.0",
                "approved_use": "local_noncommercial_inference",
                "redistribution_status": "weights_not_redistributed",
                "prompt_set_reference": "external:audited-public-vie-prompt-required",
                "language_quality_status": "not_evaluated",
                "provenance": {
                    "model_card_url": "https://example.test/model-card-vie",
                    "license_url": "https://example.test/license",
                    "audit_reference": "docs/license_matrix.md",
                    "audited_on": "2026-07-14",
                },
            },
        ],
    }
    return ModelRegistry.model_validate(payload)


@dataclass
class FakeBackend:
    waveform: WaveformResult = field(
        default_factory=lambda: WaveformResult(
            samples=(0.0, 0.25, -0.25, 0.0),
            sample_rate=16000,
        )
    )
    fail_load: bool = False
    fail_synthesis: bool = False
    reject_cuda: bool = False
    load_calls: list[tuple[str, str, DeviceRequest]] = field(default_factory=list)
    synthesis_calls: list[tuple[str, int, GenerationSettings]] = field(default_factory=list)
    unload_count: int = 0

    def load(
        self,
        *,
        repository: str,
        revision: str,
        requested_device: DeviceRequest,
    ) -> AdapterRuntime:
        self.load_calls.append((repository, revision, requested_device))
        if self.fail_load:
            raise ModelLoadError("synthetic load failure")
        if requested_device == "cuda" and self.reject_cuda:
            raise DeviceUnavailableError("synthetic CUDA rejection")
        resolved = "cpu" if requested_device == "auto" else requested_device
        return AdapterRuntime(
            requested_device=requested_device,
            resolved_device=resolved,
            dtype="float32",
        )

    def synthesize(
        self,
        *,
        text: str,
        seed: int,
        generation_settings: GenerationSettings,
    ) -> WaveformResult:
        self.synthesis_calls.append((text, seed, generation_settings))
        if self.fail_synthesis:
            raise SynthesisError("synthetic synthesis failure")
        return self.waveform

    def unload(self) -> None:
        self.unload_count += 1


class FakeAdapter:
    identity = AdapterIdentity(adapter_id="fake-vits", implementation_version="1.0.0")

    def __init__(
        self,
        *,
        waveform: WaveformResult | None = None,
        fail_load: bool = False,
        fail_dependency: bool = False,
        fail_synthesis: bool = False,
        reject_cuda: bool = False,
    ) -> None:
        self.waveform = waveform or WaveformResult(
            samples=(0.0, 0.125, -0.125, 0.0),
            sample_rate=16000,
        )
        self.fail_load = fail_load
        self.fail_dependency = fail_dependency
        self.fail_synthesis = fail_synthesis
        self.reject_cuda = reject_cuda
        self.load_calls: list[tuple[str, DeviceRequest]] = []
        self.synthesis_calls: list[tuple[str, str, int, GenerationSettings]] = []
        self.unload_count = 0
        self._loaded_model_id: str | None = None
        self._runtime: AdapterRuntime | None = None

    @property
    def state(self) -> AdapterState:
        if self._loaded_model_id is None or self._runtime is None:
            return AdapterState(lifecycle="unloaded")
        return AdapterState(
            lifecycle="loaded",
            loaded_model_id=self._loaded_model_id,
            runtime=self._runtime,
        )

    def load(self, model_id: str, requested_device: DeviceRequest) -> AdapterRuntime:
        self.load_calls.append((model_id, requested_device))
        if self.fail_dependency:
            raise DependencyUnavailableError("synthetic dependency failure")
        if self.fail_load:
            raise ModelLoadError("synthetic load failure")
        if requested_device == "cuda" and self.reject_cuda:
            raise DeviceUnavailableError("synthetic CUDA rejection")
        resolved = "cpu" if requested_device == "auto" else requested_device
        self._loaded_model_id = model_id
        self._runtime = AdapterRuntime(
            requested_device=requested_device,
            resolved_device=resolved,
            dtype="float32",
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
        self.synthesis_calls.append((model_id, text, seed, generation_settings))
        if self.fail_synthesis:
            raise SynthesisError("synthetic synthesis failure")
        return self.waveform

    def unload(self) -> None:
        self.unload_count += 1
        self._loaded_model_id = None
        self._runtime = None
