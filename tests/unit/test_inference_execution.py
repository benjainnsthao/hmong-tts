from __future__ import annotations

import hashlib
import json
import os
import wave
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from tests.fakes.inference import FakeAdapter, synthetic_registry
from tts_workbench.artifacts.paths import ARTIFACT_ROOT_ENV
from tts_workbench.artifacts.transaction import (
    ArtifactCollisionError,
    ArtifactWriteError,
    AtomicArtifactStore,
)
from tts_workbench.inference import waveform as waveform_module
from tts_workbench.inference.contracts import (
    FailureCategory,
    GenerationSettings,
    RunManifest,
    WaveformResult,
)
from tts_workbench.inference.execution import InferenceExecutor, prompt_sha256

RUN_UUID = UUID("12345678-1234-4123-8123-123456789abc")
PROMPT = "synthetic prompt marker"


def request_payload(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "model_id": "fixture-eng",
        "text": PROMPT,
        "prompt_set_reference": "builtin:synthetic-fixture-v1",
        "requested_device": "auto",
        "seed": 77,
        "generation_settings": {
            "noise_scale": 0.5,
            "noise_scale_duration": 0.6,
            "speaking_rate": 1.25,
        },
        "output_wav_path": "runs/fixture.wav",
    }
    payload.update(changes)
    return payload


def make_executor(
    tmp_path: Path,
    adapter: FakeAdapter,
    *,
    store: AtomicArtifactStore | None = None,
) -> InferenceExecutor:
    clock_values: Iterator[float] = iter((10.0, 10.25, 20.0, 20.5))
    now_values: Iterator[datetime] = iter(
        (
            datetime(2026, 7, 28, 12, 0, tzinfo=UTC),
            datetime(2026, 7, 28, 12, 0, tzinfo=UTC) + timedelta(seconds=1),
        )
    )
    return InferenceExecutor(
        registry=synthetic_registry(),
        adapter=adapter,
        artifact_store=store or AtomicArtifactStore(tmp_path),
        clock=lambda: next(clock_values),
        now=lambda: next(now_values),
        run_id_factory=lambda: RUN_UUID,
        workbench_version="0.2.0",
    )


def read_manifest(path: Path) -> tuple[dict[str, object], str]:
    rendered = path.read_text(encoding="utf-8")
    return json.loads(rendered), rendered


def test_success_copies_exact_registry_metadata_and_commits_valid_wav(
    tmp_path: Path,
) -> None:
    adapter = FakeAdapter()
    result = make_executor(tmp_path, adapter).execute(request_payload())

    assert result.status == "success"
    assert result.wav_path == "runs/fixture.wav"
    assert result.manifest_path == "runs/fixture.manifest.json"
    wav_path = tmp_path / result.wav_path
    manifest_path = tmp_path / result.manifest_path
    payload, rendered = read_manifest(manifest_path)
    entry = synthetic_registry().by_id("fixture-eng")

    assert payload["manifest_schema_version"] == 2
    assert payload["status"] == "success"
    assert payload["run_id"] == str(RUN_UUID)
    assert payload["adapter"] == {
        "schema_version": 1,
        "adapter_id": "fake-vits",
        "implementation_version": "1.0.0",
    }
    assert payload["registry_schema_version"] == 1
    assert payload["model"] == {
        "model_id": entry.model_id,
        "provider": entry.provider,
        "repository": entry.repository,
        "immutable_revision": entry.revision,
        "architecture": entry.architecture,
        "documented_language_tag": entry.documented_language_tag,
        "weight_license": entry.weight_license,
        "approved_use": entry.approved_use,
        "redistribution_status": entry.redistribution_status,
        "prompt_set_reference": entry.prompt_set_reference,
        "language_quality_status": entry.language_quality_status,
    }
    assert payload["requested_device"] == "auto"
    assert payload["resolved_device"] == "cpu"
    assert payload["dtype"] == "float32"
    assert payload["seed"] == 77
    assert payload["generation_settings"] == {
        "noise_scale": 0.5,
        "noise_scale_duration": 0.6,
        "speaking_rate": 1.25,
    }
    assert payload["timings"] == {
        "model_load_seconds": 0.25,
        "synthesis_seconds": 0.5,
    }
    runtime = payload["runtime"]
    assert isinstance(runtime, dict)
    assert "pytorch_version" not in runtime
    assert "transformers_version" not in runtime

    with wave.open(str(wav_path), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getsampwidth() == 2
        assert handle.getframerate() == 16000
        assert handle.getnframes() == 4
    wav_bytes = wav_path.read_bytes()
    audio = payload["audio"]
    assert isinstance(audio, dict)
    assert audio["wav_sha256"] == hashlib.sha256(wav_bytes).hexdigest()
    assert RunManifest.model_validate(payload)
    assert str(tmp_path.resolve()) not in rendered


def test_prompt_hash_is_stable_and_raw_prompt_is_absent_from_manifest(
    tmp_path: Path,
) -> None:
    result = make_executor(tmp_path, FakeAdapter()).execute(request_payload())
    assert result.manifest_path is not None
    payload, rendered = read_manifest(tmp_path / result.manifest_path)

    assert payload["prompt_sha256"] == prompt_sha256(PROMPT)
    assert PROMPT not in rendered
    assert "prompt_text" not in rendered
    assert '"text"' not in rendered


def test_manifest_excludes_private_machine_and_request_metadata(tmp_path: Path) -> None:
    private_marker = "private-prompt-marker"
    result = make_executor(tmp_path, FakeAdapter()).execute(request_payload(text=private_marker))
    assert result.manifest_path is not None
    _, rendered = read_manifest(tmp_path / result.manifest_path)
    forbidden_keys = (
        "username",
        "hostname",
        "ip_address",
        "credential",
        "client",
        "artifact_root",
    )

    assert private_marker not in rendered
    assert all(key not in rendered.casefold() for key in forbidden_keys)
    assert str(tmp_path.resolve()) not in rendered


def test_execution_forwards_model_seed_device_and_generation_settings(
    tmp_path: Path,
) -> None:
    adapter = FakeAdapter()
    settings = GenerationSettings(
        noise_scale=0.5,
        noise_scale_duration=0.6,
        speaking_rate=1.25,
    )

    result = make_executor(tmp_path, adapter).execute(request_payload())

    assert result.status == "success"
    assert adapter.load_calls == [("fixture-eng", "auto")]
    assert adapter.synthesis_calls == [
        ("fixture-eng", PROMPT, 77, settings),
    ]


def test_unknown_model_is_rejected_before_adapter_load(tmp_path: Path) -> None:
    adapter = FakeAdapter()

    result = make_executor(tmp_path, adapter).execute(request_payload(model_id="missing-model"))

    assert result.status == "failure"
    assert result.failure is not None
    assert result.failure.category == FailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL
    assert adapter.load_calls == []
    assert list(tmp_path.rglob("*")) == []


def test_prompt_provenance_mismatch_is_rejected_before_adapter_load(
    tmp_path: Path,
) -> None:
    adapter = FakeAdapter()

    result = make_executor(tmp_path, adapter).execute(
        request_payload(prompt_set_reference="external:different-reference")
    )

    assert result.status == "failure"
    assert result.failure is not None
    assert result.failure.category == FailureCategory.INVALID_REQUEST
    assert adapter.load_calls == []


def test_invalid_request_does_not_load_or_create_artifacts(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    payload = request_payload()
    payload["unexpected"] = True

    result = make_executor(tmp_path, adapter).execute(payload)

    assert result.status == "failure"
    assert result.failure is not None
    assert result.failure.category == FailureCategory.INVALID_REQUEST
    assert adapter.load_calls == []
    assert list(tmp_path.rglob("*")) == []


@pytest.mark.parametrize(
    "waveform",
    [
        WaveformResult(samples=(), sample_rate=16000),
        WaveformResult(samples=(float("nan"),), sample_rate=16000),
        WaveformResult(samples=(0.0,), sample_rate=0),
    ],
)
def test_invalid_waveforms_leave_no_success_artifacts(
    tmp_path: Path,
    waveform: WaveformResult,
) -> None:
    result = make_executor(tmp_path, FakeAdapter(waveform=waveform)).execute(request_payload())

    assert result.status == "failure"
    assert result.failure is not None
    assert result.failure.category == FailureCategory.INVALID_WAVEFORM
    assert not list(tmp_path.rglob("*.wav"))
    assert not list(tmp_path.rglob("*.manifest.json"))


@pytest.mark.parametrize(
    ("adapter", "category"),
    [
        (FakeAdapter(fail_dependency=True), FailureCategory.DEPENDENCY_UNAVAILABLE),
        (FakeAdapter(fail_load=True), FailureCategory.MODEL_LOAD_FAILURE),
        (FakeAdapter(fail_synthesis=True), FailureCategory.SYNTHESIS_FAILURE),
        (FakeAdapter(reject_cuda=True), FailureCategory.DEVICE_UNAVAILABLE),
    ],
)
def test_backend_failures_have_stable_categories_and_no_success_artifacts(
    tmp_path: Path,
    adapter: FakeAdapter,
    category: FailureCategory,
) -> None:
    device = "cuda" if adapter.reject_cuda else "cpu"
    result = make_executor(tmp_path, adapter).execute(request_payload(requested_device=device))

    assert result.status == "failure"
    assert result.failure is not None
    assert result.failure.category == category
    assert not list(tmp_path.rglob("*.wav"))
    assert not list(tmp_path.rglob("*.manifest.json"))


def test_artifact_boundary_failure_happens_before_adapter_load(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = FakeAdapter()
    store = AtomicArtifactStore(tmp_path)

    def reject_destination(_: str) -> None:
        from tts_workbench.artifacts.paths import ArtifactBoundaryError

        raise ArtifactBoundaryError("synthetic boundary rejection")

    monkeypatch.setattr(store, "validate_destination", reject_destination)
    result = make_executor(tmp_path, adapter, store=store).execute(request_payload())

    assert result.status == "failure"
    assert result.failure is not None
    assert result.failure.category == FailureCategory.ARTIFACT_BOUNDARY_FAILURE
    assert adapter.load_calls == []


def test_collision_is_rejected_without_overwriting_successful_run(tmp_path: Path) -> None:
    first = make_executor(tmp_path, FakeAdapter()).execute(request_payload())
    assert first.status == "success"
    assert first.wav_path is not None
    assert first.manifest_path is not None
    wav_before = (tmp_path / first.wav_path).read_bytes()
    manifest_before = (tmp_path / first.manifest_path).read_bytes()

    second = make_executor(tmp_path, FakeAdapter()).execute(request_payload())

    assert second.status == "failure"
    assert second.failure is not None
    assert second.failure.category == FailureCategory.ARTIFACT_COLLISION
    assert (tmp_path / first.wav_path).read_bytes() == wav_before
    assert (tmp_path / first.manifest_path).read_bytes() == manifest_before


def test_manifest_is_replaced_after_wav(tmp_path: Path) -> None:
    replacements: list[str] = []

    def observed_replace(source: Path, destination: Path) -> None:
        replacements.append(destination.name)
        os.replace(source, destination)

    store = AtomicArtifactStore(tmp_path, replace=observed_replace)
    result = make_executor(tmp_path, FakeAdapter(), store=store).execute(request_payload())

    assert result.status == "success"
    assert replacements == ["fixture.wav", "fixture.manifest.json"]


@pytest.mark.parametrize("fail_on_replace", [1, 2])
def test_replacement_failure_cleans_committed_and_temporary_files(
    tmp_path: Path,
    fail_on_replace: int,
) -> None:
    replacements = 0

    def failing_replace(source: Path, destination: Path) -> None:
        nonlocal replacements
        replacements += 1
        os.replace(source, destination)
        if replacements == fail_on_replace:
            raise OSError("synthetic replacement failure")

    store = AtomicArtifactStore(tmp_path, replace=failing_replace)
    result = make_executor(tmp_path, FakeAdapter(), store=store).execute(request_payload())

    assert result.status == "failure"
    assert result.failure is not None
    assert result.failure.category == FailureCategory.ARTIFACT_WRITE_FAILURE
    assert not list(tmp_path.rglob("*.wav"))
    assert not list(tmp_path.rglob("*.manifest.json"))
    assert not [path for path in tmp_path.rglob("*") if path.is_file()]


def test_manifest_serialization_failure_leaves_no_artifacts(tmp_path: Path) -> None:
    def fail_serialization(_: RunManifest) -> str:
        raise TypeError("synthetic serialization failure")

    store = AtomicArtifactStore(tmp_path, manifest_serializer=fail_serialization)
    result = make_executor(tmp_path, FakeAdapter(), store=store).execute(request_payload())

    assert result.status == "failure"
    assert result.failure is not None
    assert result.failure.category == FailureCategory.ARTIFACT_WRITE_FAILURE
    assert not [path for path in tmp_path.rglob("*") if path.is_file()]


def test_atomic_store_rejects_escape_and_absolute_destinations(tmp_path: Path) -> None:
    store = AtomicArtifactStore(tmp_path)

    with pytest.raises(ValueError):
        store.validate_destination("../escaped.wav")
    with pytest.raises(ValueError):
        store.validate_destination(str((tmp_path.parent / "absolute.wav").resolve()))


def test_atomic_store_uses_canonical_environment_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ARTIFACT_ROOT_ENV, str(tmp_path))
    store = AtomicArtifactStore()

    targets = store.validate_destination("runs/fixture.wav")

    assert targets.wav_path == (tmp_path / "runs/fixture.wav").resolve()
    assert targets.relative_wav_path == "runs/fixture.wav"


def test_atomic_store_surfaces_collision_directly(tmp_path: Path) -> None:
    existing = tmp_path / "runs/existing.wav"
    existing.parent.mkdir()
    existing.write_bytes(b"existing synthetic bytes")
    store = AtomicArtifactStore(tmp_path)

    with pytest.raises(ArtifactCollisionError):
        store.validate_destination("runs/existing.wav")


def test_atomic_store_wraps_manifest_build_failure(tmp_path: Path) -> None:
    store = AtomicArtifactStore(tmp_path)

    def fail_manifest(_: object) -> RunManifest:
        raise ValueError("synthetic manifest build failure")

    with pytest.raises(ArtifactWriteError):
        store.commit(
            relative_wav_path="runs/fixture.wav",
            waveform=WaveformResult(samples=(0.0,), sample_rate=16000),
            build_manifest=fail_manifest,
        )
    assert not [path for path in tmp_path.rglob("*") if path.is_file()]


def test_failed_wav_reopen_cleans_temporary_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = AtomicArtifactStore(tmp_path)

    def write_corrupt_wave(path: Path, samples: object, sample_rate: int) -> None:
        del samples, sample_rate
        path.write_bytes(b"synthetic corrupt WAV marker")

    monkeypatch.setattr(
        "tts_workbench.artifacts.transaction.write_pcm16_wave",
        write_corrupt_wave,
    )

    with pytest.raises(waveform_module.InvalidWaveformError):
        store.commit(
            relative_wav_path="runs/fixture.wav",
            waveform=WaveformResult(samples=(0.0,), sample_rate=16000),
            build_manifest=lambda _: pytest.fail("manifest builder must not run"),
        )
    assert not [path for path in tmp_path.rglob("*") if path.is_file()]
