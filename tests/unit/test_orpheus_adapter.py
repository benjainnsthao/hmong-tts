from __future__ import annotations

import hashlib
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from pydantic import ValidationError

from tests.fakes.inference import FakeBackend, synthetic_registry, synthetic_registry_with_orpheus
from tts_workbench.inference import orpheus
from tts_workbench.inference.adapter import (
    AdapterLifecycleError,
    DependencyUnavailableError,
    DeviceUnavailableError,
    ModelLoadError,
    SynthesisError,
    UnknownModelError,
)
from tts_workbench.inference.contracts import (
    AdapterRuntime,
    DeviceRequest,
    GenerationSettings,
    WaveformResult,
)
from tts_workbench.inference.mms_vits import MmsVitsAdapter
from tts_workbench.inference.orpheus import (
    AUDIO_TOKEN_OFFSET,
    BEGIN_OF_TEXT,
    CODEBOOK_SIZE,
    END_OF_HUMAN,
    END_OF_SPEECH,
    END_OF_TEXT,
    START_OF_HUMAN,
    START_OF_SPEECH,
    OrpheusAdapter,
    OrpheusGeneration,
    OrpheusSettings,
    TransformersOrpheusBackend,
    build_prompt_ids,
    extract_speech_codes,
    redistribute_codes,
)
from tts_workbench.models.schema import ModelComponent


def frame(*codes: int) -> list[int]:
    """Encode one seven-code frame the way the model emits audio tokens."""
    return [AUDIO_TOKEN_OFFSET + slot * CODEBOOK_SIZE + code for slot, code in enumerate(codes)]


def test_prompt_matches_reference_wrapping_and_requires_bos() -> None:
    assert build_prompt_ids([BEGIN_OF_TEXT, 11, 12]) == [
        START_OF_HUMAN,
        BEGIN_OF_TEXT,
        11,
        12,
        END_OF_TEXT,
        END_OF_HUMAN,
    ]
    for ids in ([], [11, 12]):
        with pytest.raises(SynthesisError, match="BOS"):
            build_prompt_ids(ids)


def test_speech_codes_use_last_start_and_require_explicit_end() -> None:
    first = frame(1, 2, 3, 4, 5, 6, 7)
    second = frame(4095, 0, 10, 11, 12, 13, 14)
    tokens = [START_OF_SPEECH, *frame(9, 9, 9, 9, 9, 9, 9), START_OF_SPEECH, *first, *second]
    codes, trimmed = extract_speech_codes([*tokens, END_OF_SPEECH, 1, 2])
    assert codes == [1, 2, 3, 4, 5, 6, 7, 4095, 0, 10, 11, 12, 13, 14]
    assert trimmed == 0
    with pytest.raises(SynthesisError, match="before end of speech"):
        extract_speech_codes(tokens)
    with pytest.raises(SynthesisError, match="did not start"):
        extract_speech_codes([*first, END_OF_SPEECH])


def test_speech_codes_trim_partial_frames_like_reference_and_count_them() -> None:
    tokens = [START_OF_SPEECH, *frame(1, 2, 3, 4, 5, 6, 7), *frame(8, 8, 8)[:3], END_OF_SPEECH]
    codes, trimmed = extract_speech_codes(tokens)
    assert codes == [1, 2, 3, 4, 5, 6, 7]
    assert trimmed == 3
    with pytest.raises(SynthesisError, match="no complete"):
        extract_speech_codes([START_OF_SPEECH, *frame(1, 2, 3)[:3], END_OF_SPEECH])


@pytest.mark.parametrize("slot", range(7))
def test_codes_outside_their_frame_slot_are_rejected(slot: int) -> None:
    tokens = frame(1, 2, 3, 4, 5, 6, 7)
    tokens[slot] = AUDIO_TOKEN_OFFSET + ((slot + 1) % 7) * CODEBOOK_SIZE
    with pytest.raises(SynthesisError, match="malformed"):
        extract_speech_codes([START_OF_SPEECH, *tokens, END_OF_SPEECH])


def test_non_audio_tokens_inside_speech_are_malformed() -> None:
    tokens = [START_OF_SPEECH, *frame(1, 2, 3, 4, 5, 6, 7)]
    tokens[3] = END_OF_TEXT
    with pytest.raises(SynthesisError, match="malformed"):
        extract_speech_codes([*tokens, END_OF_SPEECH])


def test_codes_redistribute_into_snac_layers() -> None:
    coarse, middle, fine = redistribute_codes([1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 14, 15, 16, 17])
    assert coarse == [1, 11]
    assert middle == [2, 5, 12, 15]
    assert fine == [3, 4, 6, 7, 13, 14, 16, 17]
    for codes in ([], [1, 2, 3]):
        with pytest.raises(SynthesisError):
            redistribute_codes(codes)


def test_settings_are_bounded_strict_and_fingerprinted() -> None:
    default = OrpheusSettings()
    assert default.fingerprint() == OrpheusSettings().fingerprint()
    assert default.fingerprint() != OrpheusSettings(temperature=0.5).fingerprint()
    assert (default.temperature, default.top_p, default.top_k) == (0.6, 0.95, 50)
    assert (default.repetition_penalty, default.max_new_tokens, default.dtype) == (
        1.1,
        1024,
        "bfloat16",
    )
    for invalid in (
        {"max_new_tokens": 1025},
        {"max_input_characters": 257},
        {"max_generation_seconds": 61.0},
        {"max_audio_seconds": 31.0},
        {"dtype": "float16"},
        {"voice": "bad voice"},
        {"temperature": "0.6"},
        {"quantization": "8bit"},
    ):
        with pytest.raises(ValidationError):
            OrpheusSettings.model_validate(invalid)


@dataclass
class FakeOrpheusBackend:
    fail_load: Exception | None = None
    fail_synthesis: Exception | None = None
    load_calls: list[tuple[str, str, ModelComponent, Path, DeviceRequest]] = field(
        default_factory=list
    )
    synthesis_calls: list[tuple[str, int]] = field(default_factory=list)
    unload_count: int = 0

    def load(
        self,
        *,
        repository: str,
        revision: str,
        codec: ModelComponent,
        codec_path: Path,
        requested_device: DeviceRequest,
    ) -> AdapterRuntime:
        self.load_calls.append((repository, revision, codec, codec_path, requested_device))
        if self.fail_load is not None:
            raise self.fail_load
        return AdapterRuntime(
            requested_device=requested_device,
            resolved_device="cpu" if requested_device == "auto" else requested_device,
            dtype="bfloat16",
        )

    def synthesize(self, *, text: str, seed: int) -> tuple[WaveformResult, OrpheusGeneration]:
        self.synthesis_calls.append((text, seed))
        if self.fail_synthesis is not None:
            raise self.fail_synthesis
        return (
            WaveformResult(samples=(0.0, 0.1, -0.1), sample_rate=24000),
            OrpheusGeneration(10, 16, 14, 2, 0),
        )

    def unload(self) -> None:
        self.unload_count += 1


def adapter_with(
    backend: FakeOrpheusBackend, tmp_path: Path, settings: OrpheusSettings | None = None
) -> tuple[OrpheusAdapter, list[OrpheusSettings]]:
    received: list[OrpheusSettings] = []

    def factory(chosen: OrpheusSettings) -> FakeOrpheusBackend:
        received.append(chosen)
        return backend

    adapter = OrpheusAdapter(
        synthetic_registry_with_orpheus(),
        settings=settings,
        backend_factory=factory,
        codec_root=lambda: tmp_path,
    )
    return adapter, received


def test_adapter_forwards_registry_identity_codec_pin_and_settings(tmp_path: Path) -> None:
    backend = FakeOrpheusBackend()
    settings = OrpheusSettings(temperature=0.4)
    adapter, received = adapter_with(backend, tmp_path, settings)

    runtime = adapter.load("fixture-orpheus", "cuda")
    waveform = adapter.synthesize(
        model_id="fixture-orpheus",
        text="synthetic marker",
        seed=19,
        generation_settings=GenerationSettings(),
    )

    ((repository, revision, codec, codec_path, device),) = backend.load_calls
    assert (repository, revision, device) == ("synthetic/fixture-orpheus", "3" * 40, "cuda")
    assert codec.loaded_sha256 == "b" * 64
    assert codec_path == tmp_path / f"{'b' * 64}.safetensors"
    assert received == [settings] and adapter.settings is settings
    assert backend.synthesis_calls == [("synthetic marker", 19)]
    assert waveform.sample_rate == 24000
    assert adapter.last_generation == OrpheusGeneration(10, 16, 14, 2, 0)
    assert runtime.dtype == "bfloat16"
    assert adapter.identity.adapter_id == "orpheus-snac"
    assert adapter.state.loaded_model_id == "fixture-orpheus"


def test_adapter_refuses_non_orpheus_and_unknown_models_before_backend(tmp_path: Path) -> None:
    backend = FakeOrpheusBackend()
    adapter, received = adapter_with(backend, tmp_path)
    for model_id in ("fixture-eng", "missing"):
        with pytest.raises(UnknownModelError):
            adapter.load(model_id, "cpu")
    assert received == [] and adapter.state.lifecycle == "unloaded"


def test_mms_adapter_refuses_restricted_orpheus_entry() -> None:
    adapter = MmsVitsAdapter(
        synthetic_registry_with_orpheus(), backend_factory=lambda: FakeBackend()
    )
    with pytest.raises(UnknownModelError, match="VITS"):
        adapter.load("fixture-orpheus", "cpu")
    assert adapter.load("fixture-eng", "cpu").resolved_device == "cpu"


def test_vits_generation_settings_are_rejected_not_ignored(tmp_path: Path) -> None:
    backend = FakeOrpheusBackend()
    adapter, _ = adapter_with(backend, tmp_path)
    adapter.load("fixture-orpheus", "cpu")
    with pytest.raises(SynthesisError, match="VITS"):
        adapter.synthesize(
            model_id="fixture-orpheus",
            text="synthetic",
            seed=1,
            generation_settings=GenerationSettings(noise_scale=0.3),
        )
    assert backend.synthesis_calls == []


def test_lifecycle_reuse_unload_and_unloaded_synthesis(tmp_path: Path) -> None:
    backend = FakeOrpheusBackend()
    adapter, received = adapter_with(backend, tmp_path)
    with pytest.raises(AdapterLifecycleError):
        adapter.synthesize(
            model_id="fixture-orpheus", text="x", seed=1, generation_settings=GenerationSettings()
        )
    first = adapter.load("fixture-orpheus", "cpu")
    assert adapter.load("fixture-orpheus", "cpu") is first
    assert len(received) == 1
    adapter.unload()
    assert backend.unload_count == 1
    assert adapter.state.lifecycle == "unloaded"


@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        (DependencyUnavailableError("synthetic"), DependencyUnavailableError),
        (DeviceUnavailableError("synthetic"), DeviceUnavailableError),
        (ModelLoadError("synthetic"), ModelLoadError),
        (RuntimeError("synthetic private detail"), ModelLoadError),
    ],
)
def test_load_failures_are_stable_and_leave_adapter_unloaded(
    tmp_path: Path, failure: Exception, expected: type[Exception]
) -> None:
    backend = FakeOrpheusBackend(fail_load=failure)
    adapter, _ = adapter_with(backend, tmp_path)
    with pytest.raises(expected) as error:
        adapter.load("fixture-orpheus", "cuda")
    assert "private detail" not in str(error.value)
    assert backend.unload_count == 1
    assert adapter.state.lifecycle == "unloaded"


@pytest.mark.parametrize(
    "failure", [SynthesisError("synthetic"), RuntimeError("synthetic private detail")]
)
def test_synthesis_failures_are_stable_and_clear_last_generation(
    tmp_path: Path, failure: Exception
) -> None:
    backend = FakeOrpheusBackend()
    adapter, _ = adapter_with(backend, tmp_path)
    adapter.load("fixture-orpheus", "cpu")
    adapter.synthesize(
        model_id="fixture-orpheus", text="ok", seed=1, generation_settings=GenerationSettings()
    )
    backend.fail_synthesis = failure
    with pytest.raises(SynthesisError) as error:
        adapter.synthesize(
            model_id="fixture-orpheus", text="x", seed=1, generation_settings=GenerationSettings()
        )
    assert "private detail" not in str(error.value)
    assert adapter.last_generation is None


def codec_component(digest: str) -> ModelComponent:
    (entry,) = synthetic_registry_with_orpheus().by_architecture("orpheus_llama_snac")
    return entry.components[0].model_copy(update={"loaded_sha256": digest})


def test_real_backend_checks_codec_pin_before_importing_ml_packages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    imported: list[str] = []
    monkeypatch.setattr(orpheus.importlib, "import_module", imported.append)
    weights = tmp_path / "codec.safetensors"
    weights.write_bytes(b"synthetic codec bytes")
    backend = TransformersOrpheusBackend(OrpheusSettings())
    for path, digest in (
        (weights, "0" * 64),
        (tmp_path / "missing.safetensors", hashlib.sha256(b"").hexdigest()),
    ):
        with pytest.raises(ModelLoadError, match="codec"):
            backend.load(
                repository="synthetic/fixture-orpheus",
                revision="3" * 40,
                codec=codec_component(digest),
                codec_path=path,
                requested_device="cpu",
            )
    assert imported == []


def test_real_backend_reports_missing_optional_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unavailable(name: str) -> object:
        raise ImportError(name)

    monkeypatch.setattr(orpheus.importlib, "import_module", unavailable)
    weights = tmp_path / "codec.safetensors"
    weights.write_bytes(b"synthetic codec bytes")
    with pytest.raises(DependencyUnavailableError):
        TransformersOrpheusBackend(OrpheusSettings()).load(
            repository="synthetic/fixture-orpheus",
            revision="3" * 40,
            codec=codec_component(hashlib.sha256(b"synthetic codec bytes").hexdigest()),
            codec_path=weights,
            requested_device="cpu",
        )


def test_real_backend_rejects_unloaded_synthesis() -> None:
    with pytest.raises(AdapterLifecycleError):
        TransformersOrpheusBackend(OrpheusSettings()).synthesize(text="x", seed=1)


def test_real_backend_source_has_no_pickle_remote_code_or_quantization_path() -> None:
    source = Path(orpheus.__file__).read_text(encoding="utf-8")
    assert "use_safetensors=True" in source
    for forbidden in (
        "torch.load(",
        "weights_only",
        "trust_remote_code",
        "load_in_8bit",
        "load_in_4bit",
        "from_pretrained(codec",
        "SNAC.from_pretrained",
        "device_map",
        "accelerate",
        '"auto"\n                dtype',
    ):
        assert forbidden not in source


def test_orpheus_module_imports_no_heavy_runtime() -> None:
    code = (
        "import sys\n"
        "import tts_workbench.inference.orpheus\n"
        "import tts_workbench.benchmark.cli\n"
        "for name in ('torch', 'transformers', 'safetensors', 'snac'):\n"
        "    assert name not in sys.modules, name\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_committed_mms_registry_behavior_is_unchanged_for_vits_only_registries() -> None:
    registry = synthetic_registry()
    assert registry.schema_version == 1
    assert registry.by_architecture("orpheus_llama_snac") == ()
    assert [entry.model_id for entry in registry.by_architecture("vits")] == [
        "fixture-eng",
        "fixture-vie",
    ]


class _Tensor:
    def __init__(self, values: list[list[int]] | list[float]) -> None:
        self.values = values

    def __getitem__(self, key: tuple[int, slice]) -> _Tensor:
        row, columns = key
        return _Tensor(self.values[row][columns])  # type: ignore[index]

    def tolist(self) -> list[object]:
        return list(self.values)

    def reshape(self, _: int) -> _Tensor:
        return self

    def float(self) -> _Tensor:
        return self

    def cpu(self) -> _Tensor:
        return self


class _Context:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *_: object) -> None:
        return None


class FakeRuntime:
    """Minimal stand-ins for torch, transformers, safetensors, SNAC and the hub."""

    def __init__(self, config_path: Path, generated: list[int], *, cuda: bool = True) -> None:
        self.config_path = config_path
        self.generated = generated
        self.cuda_available = cuda
        self.generate_kwargs: dict[str, object] = {}
        self.tokenized: list[str] = []
        self.loaded: dict[str, object] = {}
        self.decoded: list[list[_Tensor]] = []
        self.seeds: list[int] = []
        self.empty_cache_calls = 0
        self.fail_decode = False

    def modules(self) -> dict[str, object]:
        runtime = self

        class Cuda:
            @staticmethod
            def is_available() -> bool:
                return runtime.cuda_available

            @staticmethod
            def empty_cache() -> None:
                runtime.empty_cache_calls += 1

        class Torch:
            __version__ = "fake-torch"
            cuda = Cuda
            bfloat16 = "bf16"
            float32 = "f32"

            @staticmethod
            def tensor(values: list[list[int]], device: str) -> _Tensor:
                return _Tensor(values)

            @staticmethod
            def ones_like(tensor: _Tensor) -> _Tensor:
                return tensor

            @staticmethod
            def manual_seed(seed: int) -> None:
                runtime.seeds.append(seed)

            @staticmethod
            def inference_mode() -> _Context:
                return _Context()

        class Tokenizer:
            pad_token_id = 128004

            def __call__(self, text: str) -> dict[str, list[int]]:
                runtime.tokenized.append(text)
                return {"input_ids": [BEGIN_OF_TEXT, 7, 8]}

        class Model:
            def eval(self) -> Model:
                return self

            def to(self, device: str) -> Model:
                runtime.loaded["model_device"] = device
                return self

            def generate(self, **kwargs: object) -> _Tensor:
                runtime.generate_kwargs = kwargs
                prompt = kwargs["input_ids"].values[0]  # type: ignore[attr-defined]
                return _Tensor([[*prompt, *runtime.generated]])

        class Loader:
            @staticmethod
            def from_pretrained(repository: str, **kwargs: object) -> object:
                runtime.loaded[repository] = kwargs
                return Model() if "use_safetensors" in kwargs else Tokenizer()

        class Transformers:
            __version__ = "fake-transformers"
            AutoTokenizer = Loader
            LlamaForCausalLM = Loader

        class Codec:
            def __init__(self, **config: object) -> None:
                runtime.loaded["codec_config"] = config

            def load_state_dict(self, state: object, strict: bool) -> None:
                runtime.loaded["codec_strict"] = strict

            def eval(self) -> Codec:
                return self

            def to(self, device: str) -> Codec:
                runtime.loaded["codec_device"] = device
                return self

            def decode(self, layers: list[_Tensor]) -> _Tensor:
                if runtime.fail_decode:
                    raise RuntimeError("synthetic private decoder detail")
                runtime.decoded.append(layers)
                return _Tensor([0.0, 0.5, -0.5])

        class Snac:
            SNAC = Codec

        class SafetensorsTorch:
            @staticmethod
            def load_file(path: str) -> dict[str, object]:
                runtime.loaded["codec_file"] = path
                return {}

        class Hub:
            @staticmethod
            def hf_hub_download(repository: str, name: str, revision: str) -> str:
                runtime.loaded["codec_config_source"] = (repository, name, revision)
                return str(runtime.config_path)

        return {
            "torch": Torch,
            "transformers": Transformers,
            "safetensors.torch": SafetensorsTorch,
            "snac": Snac,
            "huggingface_hub": Hub,
        }


def loaded_fake_backend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    generated: list[int],
    *,
    settings: OrpheusSettings | None = None,
    requested: DeviceRequest = "auto",
    cuda: bool = True,
) -> tuple[TransformersOrpheusBackend, FakeRuntime, AdapterRuntime]:
    config = tmp_path / "config.json"
    config.write_text('{"sampling_rate": 24000}', encoding="utf-8")
    weights = tmp_path / "codec.safetensors"
    weights.write_bytes(b"synthetic codec")
    fake = FakeRuntime(config, generated, cuda=cuda)
    monkeypatch.setattr(orpheus.importlib, "import_module", fake.modules().__getitem__)
    backend = TransformersOrpheusBackend(settings or OrpheusSettings())
    runtime = backend.load(
        repository="synthetic/fixture-orpheus",
        revision="3" * 40,
        codec=codec_component(hashlib.sha256(b"synthetic codec").hexdigest()),
        codec_path=weights,
        requested_device=requested,
    )
    return backend, fake, runtime


SPEECH = [128261, START_OF_SPEECH, *frame(1, 2, 3, 4, 5, 6, 7), END_OF_SPEECH]


def test_real_backend_loads_only_pinned_safetensors_and_generates_reference_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = OrpheusSettings(voice="speaker1")
    backend, fake, runtime = loaded_fake_backend(tmp_path, monkeypatch, SPEECH, settings=settings)

    assert (runtime.resolved_device, runtime.dtype) == ("cuda", "bfloat16")
    assert runtime.pytorch_version == "fake-torch"
    model_kwargs = fake.loaded["synthetic/fixture-orpheus"]
    assert model_kwargs == {"revision": "3" * 40, "use_safetensors": True, "dtype": "bf16"}
    assert fake.loaded["model_device"] == "cuda"
    assert fake.loaded["codec_strict"] is True
    assert fake.loaded["codec_device"] == "cuda"
    assert fake.loaded["codec_config"] == {"sampling_rate": 24000}
    assert fake.loaded["codec_config_source"] == (
        "synthetic/fixture-codec",
        "config.json",
        "4" * 40,
    )

    waveform, record = backend.synthesize(text="synthetic", seed=33)

    assert fake.tokenized == ["speaker1: synthetic"]
    assert fake.seeds == [33]
    kwargs = fake.generate_kwargs
    assert kwargs["input_ids"].values == [  # type: ignore[attr-defined]
        [START_OF_HUMAN, BEGIN_OF_TEXT, 7, 8, END_OF_TEXT, END_OF_HUMAN]
    ]
    assert {key: kwargs[key] for key in ("temperature", "top_p", "top_k")} == {
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 50,
    }
    assert kwargs["eos_token_id"] == END_OF_SPEECH
    assert kwargs["max_new_tokens"] == 1024 and kwargs["max_time"] == 60.0
    assert kwargs["do_sample"] is True and kwargs["pad_token_id"] == 128004
    assert [layer.values for layer in fake.decoded[0]] == [[[1]], [[2, 5]], [[3, 4, 6, 7]]]
    assert waveform == WaveformResult(samples=(0.0, 0.5, -0.5), sample_rate=24000)
    assert record == OrpheusGeneration(
        prompt_token_count=6,
        new_token_count=10,
        speech_token_count=7,
        frame_count=1,
        trimmed_token_count=0,
    )

    backend.unload()
    assert fake.empty_cache_calls == 1
    with pytest.raises(AdapterLifecycleError):
        backend.synthesize(text="synthetic", seed=1)


@pytest.mark.parametrize(
    ("requested", "cuda", "expected"),
    [("auto", False, "cpu"), ("cpu", True, "cpu"), ("cuda", True, "cuda")],
)
def test_real_backend_resolves_devices_without_precision_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    requested: DeviceRequest,
    cuda: bool,
    expected: str,
) -> None:
    settings = OrpheusSettings(dtype="float32")
    _, fake, runtime = loaded_fake_backend(
        tmp_path, monkeypatch, SPEECH, settings=settings, requested=requested, cuda=cuda
    )
    assert runtime.resolved_device == expected
    assert fake.loaded["model_device"] == fake.loaded["codec_device"] == expected
    assert fake.loaded["synthetic/fixture-orpheus"]["dtype"] == "f32"  # type: ignore[index]


def test_real_backend_rejects_unavailable_cuda(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(DeviceUnavailableError):
        loaded_fake_backend(tmp_path, monkeypatch, SPEECH, requested="cuda", cuda=False)


def test_real_backend_wraps_loader_failures_without_private_detail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "config.json"
    config.write_text("not json", encoding="utf-8")
    weights = tmp_path / "codec.safetensors"
    weights.write_bytes(b"synthetic codec")
    fake = FakeRuntime(config, SPEECH)
    monkeypatch.setattr(orpheus.importlib, "import_module", fake.modules().__getitem__)
    with pytest.raises(ModelLoadError) as error:
        TransformersOrpheusBackend(OrpheusSettings()).load(
            repository="synthetic/fixture-orpheus",
            revision="3" * 40,
            codec=codec_component(hashlib.sha256(b"synthetic codec").hexdigest()),
            codec_path=weights,
            requested_device="cpu",
        )
    assert "not json" not in str(error.value)


@pytest.mark.parametrize(
    ("generated", "text", "settings", "message"),
    [
        (SPEECH, "x" * 257, OrpheusSettings(), "character limit"),
        (SPEECH[:-1], "synthetic", OrpheusSettings(), "before end of speech"),
        (
            [START_OF_SPEECH, *frame(1, 2, 3, 4, 5, 6, 7) * 12, END_OF_SPEECH],
            "synthetic",
            OrpheusSettings(max_audio_seconds=1.0),
            "duration limit",
        ),
    ],
)
def test_real_backend_fails_instead_of_truncating_or_overrunning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    generated: list[int],
    text: str,
    settings: OrpheusSettings,
    message: str,
) -> None:
    backend, fake, _ = loaded_fake_backend(tmp_path, monkeypatch, generated, settings=settings)
    with pytest.raises(SynthesisError, match=message):
        backend.synthesize(text=text, seed=1)
    assert fake.decoded == []


def test_real_backend_sanitizes_decoder_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend, fake, _ = loaded_fake_backend(tmp_path, monkeypatch, SPEECH)
    fake.fail_decode = True
    with pytest.raises(SynthesisError) as error:
        backend.synthesize(text="synthetic", seed=1)
    assert "private" not in str(error.value)


def test_default_codec_root_is_content_addressed_under_external_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(orpheus, "get_artifact_root", lambda: tmp_path)
    assert orpheus.default_codec_root() == tmp_path / "converted-weights" / "sha256"
    weights = tmp_path / "w"
    weights.write_bytes(b"abc")
    assert orpheus.sha256_file(weights) == hashlib.sha256(b"abc").hexdigest()
