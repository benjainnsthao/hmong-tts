"""Provider-neutral adapter lifecycle and failure boundaries."""

from __future__ import annotations

from typing import Protocol

from tts_workbench.inference.contracts import (
    AdapterIdentity,
    AdapterRuntime,
    AdapterState,
    DeviceRequest,
    GenerationSettings,
    WaveformResult,
)


class AdapterError(RuntimeError):
    """Base class for sanitized adapter boundary failures."""


class UnknownModelError(AdapterError):
    """The requested model is not an approved registry entry."""


class DependencyUnavailableError(AdapterError):
    """An optional backend dependency cannot be imported."""


class DeviceUnavailableError(AdapterError):
    """The requested execution device cannot be used."""


class ModelLoadError(AdapterError):
    """The runtime backend could not load the registered model."""


class SynthesisError(AdapterError):
    """The loaded backend could not synthesize a waveform."""


class AdapterLifecycleError(AdapterError):
    """The adapter was used in an invalid lifecycle state."""


class TTSAdapter(Protocol):
    """Provider-neutral interface implemented by each TTS runtime adapter."""

    @property
    def identity(self) -> AdapterIdentity:
        """Return stable implementation identity."""

    @property
    def state(self) -> AdapterState:
        """Return observable loaded or unloaded state."""

    def load(self, model_id: str, requested_device: DeviceRequest) -> AdapterRuntime:
        """Load one approved registered model, unloading an old model if needed."""

    def synthesize(
        self,
        *,
        model_id: str,
        text: str,
        seed: int,
        generation_settings: GenerationSettings,
    ) -> WaveformResult:
        """Synthesize with the explicitly loaded model."""

    def unload(self) -> None:
        """Release all model state explicitly owned by this adapter."""
