from __future__ import annotations

import importlib
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.fakes.inference import FakeBackend, synthetic_registry
from tts_workbench.inference.adapter import (
    DependencyUnavailableError,
    DeviceUnavailableError,
    ModelLoadError,
    SynthesisError,
    UnknownModelError,
)
from tts_workbench.inference.contracts import GenerationSettings, WaveformResult
from tts_workbench.inference.mms_vits import MmsVitsAdapter, TransformersMmsBackend


def test_adapter_forwards_registry_identity_device_seed_and_settings() -> None:
    registry = synthetic_registry()
    backend = FakeBackend()
    adapter = MmsVitsAdapter(registry, backend_factory=lambda: backend)
    settings = GenerationSettings(
        noise_scale=0.5,
        noise_scale_duration=0.6,
        speaking_rate=1.25,
    )

    runtime = adapter.load("fixture-eng", "cuda")
    waveform = adapter.synthesize(
        model_id="fixture-eng",
        text="synthetic prompt marker",
        seed=77,
        generation_settings=settings,
    )

    entry = registry.by_id("fixture-eng")
    assert backend.load_calls == [(entry.repository, entry.revision, "cuda")]
    assert backend.synthesis_calls == [("synthetic prompt marker", 77, settings)]
    assert runtime.requested_device == "cuda"
    assert runtime.resolved_device == "cuda"
    assert waveform.sample_rate == 16000
    assert adapter.state.lifecycle == "loaded"
    assert adapter.state.loaded_model_id == "fixture-eng"


@pytest.mark.parametrize(
    ("requested", "resolved"),
    [("auto", "cpu"), ("cpu", "cpu"), ("cuda", "cuda")],
)
def test_adapter_preserves_each_explicit_device_request(
    requested: str,
    resolved: str,
) -> None:
    backend = FakeBackend()
    adapter = MmsVitsAdapter(synthetic_registry(), backend_factory=lambda: backend)

    runtime = adapter.load("fixture-eng", requested)  # type: ignore[arg-type]

    assert runtime.requested_device == requested
    assert runtime.resolved_device == resolved


def test_adapter_explicit_unload_clears_observable_state() -> None:
    backend = FakeBackend()
    adapter = MmsVitsAdapter(synthetic_registry(), backend_factory=lambda: backend)
    adapter.load("fixture-eng", "cpu")

    adapter.unload()

    assert backend.unload_count == 1
    assert adapter.state.lifecycle == "unloaded"
    assert adapter.state.loaded_model_id is None


def test_loading_same_model_and_device_reuses_owned_backend() -> None:
    backend = FakeBackend()
    adapter = MmsVitsAdapter(synthetic_registry(), backend_factory=lambda: backend)

    first = adapter.load("fixture-eng", "cpu")
    second = adapter.load("fixture-eng", "cpu")

    assert first == second
    assert len(backend.load_calls) == 1
    assert backend.unload_count == 0


def test_model_switch_unloads_old_backend_before_loading_new() -> None:
    events: list[str] = []

    class ObservedBackend(FakeBackend):
        def __init__(self, name: str) -> None:
            super().__init__()
            self.name = name

        def load(
            self,
            *,
            repository: str,
            revision: str,
            requested_device: str,
        ):  # type: ignore[no-untyped-def]
            events.append(f"load:{self.name}")
            return super().load(
                repository=repository,
                revision=revision,
                requested_device=requested_device,  # type: ignore[arg-type]
            )

        def unload(self) -> None:
            events.append(f"unload:{self.name}")
            super().unload()

    backends: Iterator[FakeBackend] = iter([ObservedBackend("first"), ObservedBackend("second")])
    adapter = MmsVitsAdapter(synthetic_registry(), backend_factory=lambda: next(backends))

    adapter.load("fixture-eng", "cpu")
    adapter.load("fixture-vie", "cpu")

    assert events == ["load:first", "unload:first", "load:second"]
    assert adapter.state.loaded_model_id == "fixture-vie"


def test_unknown_model_is_rejected_before_backend_factory() -> None:
    factory_calls = 0

    def factory() -> FakeBackend:
        nonlocal factory_calls
        factory_calls += 1
        return FakeBackend()

    adapter = MmsVitsAdapter(synthetic_registry(), backend_factory=factory)

    with pytest.raises(UnknownModelError):
        adapter.load("missing-model", "cpu")
    assert factory_calls == 0


def test_backend_load_and_device_failures_leave_adapter_unloaded() -> None:
    load_backend = FakeBackend(fail_load=True)
    load_adapter = MmsVitsAdapter(
        synthetic_registry(),
        backend_factory=lambda: load_backend,
    )
    with pytest.raises(ModelLoadError):
        load_adapter.load("fixture-eng", "cpu")
    assert load_adapter.state.lifecycle == "unloaded"

    device_backend = FakeBackend(reject_cuda=True)
    device_adapter = MmsVitsAdapter(
        synthetic_registry(),
        backend_factory=lambda: device_backend,
    )
    with pytest.raises(DeviceUnavailableError):
        device_adapter.load("fixture-eng", "cuda")
    assert device_adapter.state.lifecycle == "unloaded"


def test_failed_model_switch_does_not_retain_old_loaded_state() -> None:
    first = FakeBackend()
    second = FakeBackend(fail_load=True)
    backends: Iterator[FakeBackend] = iter((first, second))
    adapter = MmsVitsAdapter(
        synthetic_registry(),
        backend_factory=lambda: next(backends),
    )
    adapter.load("fixture-eng", "cpu")

    with pytest.raises(ModelLoadError):
        adapter.load("fixture-vie", "cpu")

    assert first.unload_count == 1
    assert adapter.state.lifecycle == "unloaded"


def test_backend_synthesis_failure_is_stable() -> None:
    backend = FakeBackend(fail_synthesis=True)
    adapter = MmsVitsAdapter(synthetic_registry(), backend_factory=lambda: backend)
    adapter.load("fixture-eng", "cpu")

    with pytest.raises(SynthesisError):
        adapter.synthesize(
            model_id="fixture-eng",
            text="synthetic prompt marker",
            seed=7,
            generation_settings=GenerationSettings(),
        )


@pytest.mark.parametrize(
    "waveform",
    [
        WaveformResult(samples=(), sample_rate=16000),
        WaveformResult(samples=(float("nan"),), sample_rate=16000),
        WaveformResult(samples=(0.0,), sample_rate=0),
    ],
)
def test_fake_backend_can_return_structurally_invalid_waveforms(
    waveform: WaveformResult,
) -> None:
    backend = FakeBackend(waveform=waveform)
    adapter = MmsVitsAdapter(synthetic_registry(), backend_factory=lambda: backend)
    adapter.load("fixture-eng", "cpu")

    assert (
        adapter.synthesize(
            model_id="fixture-eng",
            text="synthetic prompt marker",
            seed=7,
            generation_settings=GenerationSettings(),
        )
        == waveform
    )


def test_real_backend_reports_missing_optional_dependencies_without_import_at_module_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = TransformersMmsBackend()

    def unavailable(name: str):
        raise ImportError(name)

    monkeypatch.setattr(importlib, "import_module", unavailable)
    with pytest.raises(DependencyUnavailableError):
        backend.load(
            repository="synthetic/fixture-eng",
            revision="1" * 40,
            requested_device="cpu",
        )


def test_real_backend_unload_drops_state_and_releases_cuda_cache() -> None:
    empty_cache_calls = 0

    def empty_cache() -> None:
        nonlocal empty_cache_calls
        empty_cache_calls += 1

    backend = TransformersMmsBackend()
    backend._torch = SimpleNamespace(  # noqa: SLF001
        cuda=SimpleNamespace(is_available=lambda: True, empty_cache=empty_cache)
    )
    backend._transformers = object()  # noqa: SLF001
    backend._tokenizer = object()  # noqa: SLF001
    backend._model = object()  # noqa: SLF001

    backend.unload()

    assert backend._torch is None  # noqa: SLF001
    assert backend._transformers is None  # noqa: SLF001
    assert backend._tokenizer is None  # noqa: SLF001
    assert backend._model is None  # noqa: SLF001
    assert empty_cache_calls == 1


def test_package_contract_and_adapter_imports_are_lazy(
    repository_root: Path,
) -> None:
    code = (
        "import sys\n"
        "import tts_workbench\n"
        "import tts_workbench.inference.contracts\n"
        "import tts_workbench.inference.mms_vits\n"
        "assert 'torch' not in sys.modules\n"
        "assert 'transformers' not in sys.modules\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
