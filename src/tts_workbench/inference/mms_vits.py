"""Registry-owned MMS/VITS adapter with a lazy optional Transformers backend."""

from __future__ import annotations

import gc
import importlib
from collections.abc import Callable, Iterable, Mapping
from typing import Any, Protocol, SupportsFloat, cast

from tts_workbench.inference.adapter import (
    AdapterLifecycleError,
    DependencyUnavailableError,
    DeviceUnavailableError,
    ModelLoadError,
    SynthesisError,
    UnknownModelError,
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

MMS_VITS_ADAPTER_IDENTITY = AdapterIdentity(
    adapter_id="mms-vits",
    implementation_version="1.0.0",
)


class MmsBackend(Protocol):
    """Provider-specific runtime seam used by the provider-neutral adapter."""

    def load(
        self,
        *,
        repository: str,
        revision: str,
        requested_device: DeviceRequest,
    ) -> AdapterRuntime:
        """Load one immutable MMS/VITS checkpoint."""

    def synthesize(
        self,
        *,
        text: str,
        seed: int,
        generation_settings: GenerationSettings,
    ) -> WaveformResult:
        """Return an uncommitted waveform."""

    def unload(self) -> None:
        """Release provider-specific model and tokenizer state."""


class TransformersMmsBackend:
    """Optional real backend; imports heavyweight ML packages only during load."""

    def __init__(self) -> None:
        self._torch: Any | None = None
        self._transformers: Any | None = None
        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self._runtime: AdapterRuntime | None = None

    def load(
        self,
        *,
        repository: str,
        revision: str,
        requested_device: DeviceRequest,
    ) -> AdapterRuntime:
        self.unload()
        try:
            torch_module = importlib.import_module("torch")
            transformers_module = importlib.import_module("transformers")
        except (ImportError, OSError) as exc:
            raise DependencyUnavailableError(
                "optional MMS runtime dependencies are unavailable"
            ) from exc

        cuda_available = bool(torch_module.cuda.is_available())
        resolved_device = (
            "cuda" if requested_device == "auto" and cuda_available else requested_device
        )
        if resolved_device == "auto":
            resolved_device = "cpu"
        if resolved_device == "cuda" and not cuda_available:
            raise DeviceUnavailableError("requested CUDA device is unavailable")

        try:
            tokenizer = transformers_module.VitsTokenizer.from_pretrained(
                repository,
                revision=revision,
            )
            model = transformers_module.VitsModel.from_pretrained(
                repository,
                revision=revision,
            )
            model = model.to(resolved_device)
        except Exception as exc:
            self.unload()
            raise ModelLoadError("MMS/VITS backend could not load the registered model") from exc

        dtype = str(getattr(model, "dtype", "unknown")).removeprefix("torch.")
        runtime = AdapterRuntime(
            requested_device=requested_device,
            resolved_device=resolved_device,
            dtype=dtype,
            pytorch_version=str(torch_module.__version__),
            transformers_version=str(transformers_module.__version__),
        )
        self._torch = torch_module
        self._transformers = transformers_module
        self._tokenizer = tokenizer
        self._model = model
        self._runtime = runtime
        return runtime

    def synthesize(
        self,
        *,
        text: str,
        seed: int,
        generation_settings: GenerationSettings,
    ) -> WaveformResult:
        if (
            self._torch is None
            or self._transformers is None
            or self._tokenizer is None
            or self._model is None
            or self._runtime is None
        ):
            raise AdapterLifecycleError("MMS/VITS backend is not loaded")

        try:
            self._model.noise_scale = generation_settings.noise_scale
            self._model.noise_scale_duration = generation_settings.noise_scale_duration
            self._model.speaking_rate = generation_settings.speaking_rate
            inputs = self._tokenizer(text=text, return_tensors="pt").to(
                self._runtime.resolved_device
            )
            self._transformers.set_seed(seed)
            with self._torch.no_grad():
                output = self._model(**cast(Mapping[str, Any], inputs))
            raw_samples = output.waveform[0].detach().float().cpu().tolist()
            samples = tuple(float(sample) for sample in cast(Iterable[SupportsFloat], raw_samples))
            sample_rate = int(self._model.config.sampling_rate)
        except AdapterLifecycleError:
            raise
        except Exception as exc:
            raise SynthesisError("MMS/VITS backend synthesis failed") from exc
        return WaveformResult(samples=samples, sample_rate=sample_rate, channel_count=1)

    def unload(self) -> None:
        torch_module = self._torch
        self._model = None
        self._tokenizer = None
        self._runtime = None
        self._transformers = None
        self._torch = None
        gc.collect()
        if torch_module is not None:
            try:
                if bool(torch_module.cuda.is_available()):
                    torch_module.cuda.empty_cache()
            except (AttributeError, RuntimeError, TypeError, ValueError):
                pass


class MmsVitsAdapter:
    """One-model-at-a-time MMS/VITS adapter selected only through a registry."""

    def __init__(
        self,
        registry: ModelRegistry,
        *,
        backend_factory: Callable[[], MmsBackend] = TransformersMmsBackend,
    ) -> None:
        self._registry = registry
        self._backend_factory = backend_factory
        self._backend: MmsBackend | None = None
        self._loaded_model_id: str | None = None
        self._runtime: AdapterRuntime | None = None

    @property
    def identity(self) -> AdapterIdentity:
        return MMS_VITS_ADAPTER_IDENTITY

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
        try:
            entry = self._registry.by_id(model_id)
        except KeyError as exc:
            raise UnknownModelError("model ID is not present in the audited registry") from exc

        if (
            self._loaded_model_id == model_id
            and self._runtime is not None
            and self._runtime.requested_device == requested_device
        ):
            return self._runtime

        self.unload()
        backend = self._backend_factory()
        try:
            runtime = backend.load(
                repository=entry.repository,
                revision=entry.revision,
                requested_device=requested_device,
            )
        except (
            DependencyUnavailableError,
            DeviceUnavailableError,
            ModelLoadError,
        ):
            backend.unload()
            raise
        except Exception as exc:
            backend.unload()
            raise ModelLoadError("MMS/VITS backend could not load the registered model") from exc

        self._backend = backend
        self._loaded_model_id = model_id
        self._runtime = runtime
        return runtime

    def synthesize(
        self,
        *,
        model_id: str,
        text: str,
        seed: int,
        generation_settings: GenerationSettings,
    ) -> WaveformResult:
        if self._backend is None or self._loaded_model_id != model_id:
            raise AdapterLifecycleError("requested model is not loaded by this adapter")
        try:
            return self._backend.synthesize(
                text=text,
                seed=seed,
                generation_settings=generation_settings,
            )
        except (AdapterLifecycleError, SynthesisError):
            raise
        except Exception as exc:
            raise SynthesisError("MMS/VITS backend synthesis failed") from exc

    def unload(self) -> None:
        backend = self._backend
        self._backend = None
        self._loaded_model_id = None
        self._runtime = None
        if backend is not None:
            backend.unload()
