"""Registry-owned Orpheus/SNAC adapter for restricted local research.

Heavyweight packages (PyTorch, Transformers, safetensors, SNAC) are imported only
inside the optional backend's ``load``. The core package never needs them.
The language model loads only safetensors at its registered immutable revision;
the SNAC codec loads only a locally converted safetensors file whose SHA-256 is
pinned in the registry. No pickle loading, remote code, quantization or automatic
precision change happens here.
"""

from __future__ import annotations

import gc
import hashlib
import importlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from tts_workbench.artifacts.paths import get_artifact_root
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
    ResolvedDevice,
    WaveformResult,
)
from tts_workbench.models.schema import ModelComponent, ModelRegistry

ORPHEUS_ADAPTER_IDENTITY = AdapterIdentity(
    adapter_id="orpheus-snac",
    implementation_version="0.1.0",
)
ORPHEUS_ARCHITECTURE = "orpheus_llama_snac"

# Token layout of the Orpheus 3B fine-tunes (canopyai/Orpheus-TTS reference inference).
BEGIN_OF_TEXT = 128000
END_OF_TEXT = 128009
START_OF_SPEECH = 128257
END_OF_SPEECH = 128258
START_OF_HUMAN = 128259
END_OF_HUMAN = 128260
AUDIO_TOKEN_OFFSET = 128266
CODEBOOK_SIZE = 4096
FRAME_TOKENS = 7
SNAC_SAMPLE_RATE = 24000
SNAC_SAMPLES_PER_FRAME = 2048
# Position of each of the seven frame tokens in SNAC's three codebook layers.
_FRAME_LAYERS = (0, 1, 2, 2, 1, 2, 2)


class OrpheusSettings(BaseModel):
    """One fixed, fingerprinted Orpheus configuration; never changed after a failure."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal[1] = 1
    voice: Annotated[str, Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,31}$")] | None = None
    temperature: float = Field(default=0.6, gt=0.0, le=1.5, allow_inf_nan=False)
    top_p: float = Field(default=0.95, gt=0.0, le=1.0, allow_inf_nan=False)
    # The reference passes no top_k, so Transformers' default of 50 applies; keep it explicit.
    top_k: int = Field(default=50, ge=1, le=1000)
    repetition_penalty: float = Field(default=1.1, ge=1.0, le=2.0, allow_inf_nan=False)
    max_new_tokens: int = Field(default=1024, ge=FRAME_TOKENS, le=1024)
    max_input_characters: int = Field(default=256, ge=1, le=256)
    max_generation_seconds: float = Field(default=60.0, gt=0.0, le=60.0, allow_inf_nan=False)
    max_audio_seconds: float = Field(default=30.0, gt=0.0, le=30.0, allow_inf_nan=False)
    dtype: Literal["bfloat16", "float32"] = "bfloat16"

    def fingerprint(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OrpheusGeneration:
    """Non-sensitive facts about the most recent generation, for trial records."""

    prompt_token_count: int
    new_token_count: int
    speech_token_count: int
    frame_count: int
    trimmed_token_count: int


def build_prompt_ids(text_ids: Sequence[int]) -> list[int]:
    """Wrap tokenizer output exactly as the reference: SOH, text (with BOS), EOT, EOH."""
    if not text_ids or text_ids[0] != BEGIN_OF_TEXT:
        raise SynthesisError("Orpheus tokenizer did not produce the expected BOS token")
    return [START_OF_HUMAN, *text_ids, END_OF_TEXT, END_OF_HUMAN]


def extract_speech_codes(new_token_ids: Sequence[int]) -> tuple[list[int], int]:
    """Return SNAC codes from generated tokens and the number of trimmed trailing tokens.

    Generation must end speech explicitly: a token-cap or time-cap stop is a
    failed attempt, never a clipped usable sample. Every code must fall inside
    the codebook slot its frame position requires.
    """
    starts = [i for i, token in enumerate(new_token_ids) if token == START_OF_SPEECH]
    if not starts:
        raise SynthesisError("Orpheus generation did not start speech")
    tail = list(new_token_ids[starts[-1] + 1 :])
    if END_OF_SPEECH not in tail:
        raise SynthesisError("Orpheus generation stopped before end of speech")
    speech = tail[: tail.index(END_OF_SPEECH)]
    usable = len(speech) - len(speech) % FRAME_TOKENS
    if usable == 0:
        raise SynthesisError("Orpheus generation produced no complete audio frame")
    codes = []
    for index, token in enumerate(speech[:usable]):
        code = token - AUDIO_TOKEN_OFFSET - (index % FRAME_TOKENS) * CODEBOOK_SIZE
        if not 0 <= code < CODEBOOK_SIZE:
            raise SynthesisError("Orpheus generation produced a malformed audio frame")
        codes.append(code)
    return codes, len(speech) - usable


def redistribute_codes(codes: Sequence[int]) -> tuple[list[int], list[int], list[int]]:
    """Split validated frame codes into SNAC's coarse, middle and fine layers."""
    if not codes or len(codes) % FRAME_TOKENS:
        raise SynthesisError("SNAC codes must contain complete frames")
    layers: tuple[list[int], list[int], list[int]] = ([], [], [])
    for index, code in enumerate(codes):
        layers[_FRAME_LAYERS[index % FRAME_TOKENS]].append(code)
    return layers


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def default_codec_root() -> Path:
    """Content-addressed external location of locally converted codec weights."""
    return get_artifact_root() / "converted-weights" / "sha256"


class OrpheusBackend(Protocol):
    """Provider-specific runtime seam used by the provider-neutral adapter."""

    def load(
        self,
        *,
        repository: str,
        revision: str,
        codec: ModelComponent,
        codec_path: Path,
        requested_device: DeviceRequest,
    ) -> AdapterRuntime:
        """Load one immutable checkpoint and its pinned codec."""

    def synthesize(self, *, text: str, seed: int) -> tuple[WaveformResult, OrpheusGeneration]:
        """Return an uncommitted waveform and generation facts."""

    def unload(self) -> None:
        """Release model, tokenizer and codec state."""


class TransformersOrpheusBackend:
    """Optional real backend; imports heavyweight ML packages only during load."""

    def __init__(self, settings: OrpheusSettings) -> None:
        self._settings = settings
        self._torch: Any | None = None
        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self._codec: Any | None = None
        self._device: ResolvedDevice | None = None

    def load(
        self,
        *,
        repository: str,
        revision: str,
        codec: ModelComponent,
        codec_path: Path,
        requested_device: DeviceRequest,
    ) -> AdapterRuntime:
        self.unload()
        # Check the locally converted codec before importing any ML package.
        try:
            codec_matches = sha256_file(codec_path) == codec.loaded_sha256
        except OSError as exc:
            raise ModelLoadError("converted codec weights are unavailable") from exc
        if not codec_matches:
            raise ModelLoadError("converted codec weights do not match the registry pin")
        try:
            torch_module = importlib.import_module("torch")
            transformers_module = importlib.import_module("transformers")
            safetensors_torch = importlib.import_module("safetensors.torch")
            snac_module = importlib.import_module("snac")
            hub = importlib.import_module("huggingface_hub")
        except (ImportError, OSError) as exc:
            raise DependencyUnavailableError(
                "optional Orpheus runtime dependencies are unavailable"
            ) from exc

        cuda_available = bool(torch_module.cuda.is_available())
        device: ResolvedDevice = (
            "cuda"
            if requested_device == "cuda" or (requested_device == "auto" and cuda_available)
            else "cpu"
        )
        if device == "cuda" and not cuda_available:
            raise DeviceUnavailableError("requested CUDA device is unavailable")

        try:
            config_path = hub.hf_hub_download(
                codec.repository, "config.json", revision=codec.revision
            )
            with open(config_path, encoding="utf-8") as handle:
                codec_config = json.load(handle)
            codec_model = snac_module.SNAC(**codec_config)
            codec_model.load_state_dict(safetensors_torch.load_file(str(codec_path)), strict=True)
            codec_model = codec_model.eval().to(device)
            tokenizer = transformers_module.AutoTokenizer.from_pretrained(
                repository, revision=revision
            )
            # No placement map: that loader path needs the Accelerate package, which the
            # project excludes (GHSA-4j2p-28q2-5m79). Load on CPU in the fixed dtype, then move.
            model = transformers_module.LlamaForCausalLM.from_pretrained(
                repository,
                revision=revision,
                use_safetensors=True,
                dtype=getattr(torch_module, self._settings.dtype),
            )
            model = model.to(device).eval()
        except Exception as exc:
            self.unload()
            raise ModelLoadError("Orpheus backend could not load the registered model") from exc

        self._torch = torch_module
        self._tokenizer = tokenizer
        self._model = model
        self._codec = codec_model
        self._device = device
        return AdapterRuntime(
            requested_device=requested_device,
            resolved_device=device,
            dtype=self._settings.dtype,
            pytorch_version=str(torch_module.__version__),
            transformers_version=str(transformers_module.__version__),
        )

    def synthesize(self, *, text: str, seed: int) -> tuple[WaveformResult, OrpheusGeneration]:
        torch_module = self._torch
        if (
            torch_module is None
            or self._tokenizer is None
            or self._model is None
            or self._codec is None
            or self._device is None
        ):
            raise AdapterLifecycleError("Orpheus backend is not loaded")
        settings = self._settings
        if len(text) > settings.max_input_characters:
            raise SynthesisError("input exceeds the configured Orpheus character limit")
        prompt = f"{settings.voice}: {text}" if settings.voice else text
        try:
            text_ids = [int(token) for token in self._tokenizer(prompt)["input_ids"]]
            prompt_ids = build_prompt_ids(text_ids)
            input_ids = torch_module.tensor([prompt_ids], device=self._device)
            torch_module.manual_seed(seed)
            with torch_module.inference_mode():
                output = self._model.generate(
                    input_ids=input_ids,
                    attention_mask=torch_module.ones_like(input_ids),
                    max_new_tokens=settings.max_new_tokens,
                    max_time=settings.max_generation_seconds,
                    do_sample=True,
                    temperature=settings.temperature,
                    top_p=settings.top_p,
                    top_k=settings.top_k,
                    repetition_penalty=settings.repetition_penalty,
                    eos_token_id=END_OF_SPEECH,
                    pad_token_id=self._tokenizer.pad_token_id,
                    use_cache=True,
                )
            new_ids = [int(token) for token in output[0, len(prompt_ids) :].tolist()]
            codes, trimmed = extract_speech_codes(new_ids)
            frames = len(codes) // FRAME_TOKENS
            if frames * SNAC_SAMPLES_PER_FRAME > settings.max_audio_seconds * SNAC_SAMPLE_RATE:
                raise SynthesisError("Orpheus audio exceeds the configured duration limit")
            layers = [
                torch_module.tensor([layer], device=self._device)
                for layer in redistribute_codes(codes)
            ]
            with torch_module.inference_mode():
                audio = self._codec.decode(layers)
            samples = tuple(float(value) for value in audio.reshape(-1).float().cpu().tolist())
        except (AdapterLifecycleError, SynthesisError):
            raise
        except Exception as exc:
            raise SynthesisError("Orpheus backend synthesis failed") from exc
        record = OrpheusGeneration(
            prompt_token_count=len(prompt_ids),
            new_token_count=len(new_ids),
            speech_token_count=len(codes) + trimmed,
            frame_count=frames,
            trimmed_token_count=trimmed,
        )
        return WaveformResult(samples=samples, sample_rate=SNAC_SAMPLE_RATE), record

    def unload(self) -> None:
        torch_module = self._torch
        self._model = None
        self._codec = None
        self._tokenizer = None
        self._device = None
        self._torch = None
        gc.collect()
        if torch_module is not None:
            try:
                if bool(torch_module.cuda.is_available()):
                    torch_module.cuda.empty_cache()
            except (AttributeError, RuntimeError, TypeError, ValueError):
                pass


class OrpheusAdapter:
    """One-model-at-a-time Orpheus adapter selected only through the registry."""

    def __init__(
        self,
        registry: ModelRegistry,
        *,
        settings: OrpheusSettings | None = None,
        backend_factory: Callable[[OrpheusSettings], OrpheusBackend] = (TransformersOrpheusBackend),
        codec_root: Callable[[], Path] = default_codec_root,
    ) -> None:
        self._registry = registry
        self._settings = settings or OrpheusSettings()
        self._backend_factory = backend_factory
        self._codec_root = codec_root
        self._backend: OrpheusBackend | None = None
        self._loaded_model_id: str | None = None
        self._runtime: AdapterRuntime | None = None
        self._last_generation: OrpheusGeneration | None = None

    @property
    def identity(self) -> AdapterIdentity:
        return ORPHEUS_ADAPTER_IDENTITY

    @property
    def settings(self) -> OrpheusSettings:
        return self._settings

    @property
    def last_generation(self) -> OrpheusGeneration | None:
        return self._last_generation

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
        if entry.architecture != ORPHEUS_ARCHITECTURE or entry.use_restrictions is None:
            raise UnknownModelError("model ID is not a restricted Orpheus registry entry")

        if (
            self._loaded_model_id == model_id
            and self._runtime is not None
            and self._runtime.requested_device == requested_device
        ):
            return self._runtime

        self.unload()
        (codec,) = entry.components
        backend = self._backend_factory(self._settings)
        try:
            codec_path = self._codec_root() / f"{codec.loaded_sha256}.safetensors"
            runtime = backend.load(
                repository=entry.repository,
                revision=entry.revision,
                codec=codec,
                codec_path=codec_path,
                requested_device=requested_device,
            )
        except (DependencyUnavailableError, DeviceUnavailableError, ModelLoadError):
            backend.unload()
            raise
        except Exception as exc:
            backend.unload()
            raise ModelLoadError("Orpheus backend could not load the registered model") from exc

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
        # VITS controls have no Orpheus meaning; reject rather than silently ignore them.
        if generation_settings != GenerationSettings():
            raise SynthesisError("VITS generation settings do not apply to Orpheus")
        self._last_generation = None
        try:
            waveform, record = self._backend.synthesize(text=text, seed=seed)
        except (AdapterLifecycleError, SynthesisError):
            raise
        except Exception as exc:
            raise SynthesisError("Orpheus backend synthesis failed") from exc
        self._last_generation = record
        return waveform

    def unload(self) -> None:
        backend = self._backend
        self._backend = None
        self._loaded_model_id = None
        self._runtime = None
        if backend is not None:
            backend.unload()
