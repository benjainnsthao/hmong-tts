from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from tts_workbench.inference.contracts import (
    AdapterIdentity,
    AdapterRuntime,
    AdapterState,
    FailureCategory,
    FailureDetail,
    GenerationSettings,
    InferenceRequest,
    InferenceResult,
    ManifestAudio,
    ManifestModel,
    ManifestRuntime,
    ManifestTimings,
    RunManifest,
)
from tts_workbench.inference.execution import prompt_sha256

RUN_ID = "12345678-1234-4123-8123-123456789abc"
REVISION = "1" * 40


def valid_request() -> dict[str, object]:
    return {
        "schema_version": 1,
        "model_id": "fixture-eng",
        "text": "synthetic prompt marker",
        "prompt_set_reference": "builtin:synthetic-fixture-v1",
        "requested_device": "cpu",
        "seed": 7,
        "generation_settings": {
            "noise_scale": 0.667,
            "noise_scale_duration": 0.8,
            "speaking_rate": 1.0,
        },
        "output_wav_path": "runs/fixture.wav",
    }


def valid_manifest() -> dict[str, object]:
    timestamp = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)
    return {
        "manifest_schema_version": 1,
        "run_id": RUN_ID,
        "status": "success",
        "started_at": timestamp,
        "completed_at": timestamp,
        "adapter": {
            "schema_version": 1,
            "adapter_id": "fake-vits",
            "implementation_version": "1.0.0",
        },
        "registry_schema_version": 1,
        "model": {
            "model_id": "fixture-eng",
            "provider": "Synthetic Provider",
            "repository": "synthetic/fixture-eng",
            "immutable_revision": REVISION,
            "architecture": "vits",
            "documented_language_tag": "eng",
            "weight_license": "Apache-2.0",
            "approved_use": "local_noncommercial_inference",
            "redistribution_status": "weights_not_redistributed",
            "prompt_set_reference": "builtin:synthetic-fixture-v1",
            "language_quality_status": "not_evaluated",
        },
        "prompt_sha256": "a" * 64,
        "requested_device": "cpu",
        "resolved_device": "cpu",
        "dtype": "float32",
        "seed": 7,
        "generation_settings": {},
        "runtime": {
            "python_version": "3.12.0",
            "workbench_version": "0.2.0",
        },
        "timings": {
            "model_load_seconds": 0.1,
            "synthesis_seconds": 0.2,
        },
        "audio": {
            "sample_rate": 16000,
            "channel_count": 1,
            "sample_count": 4,
            "duration_seconds": 0.00025,
            "wav_sha256": "b" * 64,
        },
        "wav_path": "runs/fixture.wav",
    }


@pytest.mark.parametrize("contract", [valid_request(), valid_manifest()])
def test_versioned_contracts_forbid_extra_fields(contract: dict[str, object]) -> None:
    contract["unexpected"] = True
    model = InferenceRequest if "text" in contract else RunManifest
    with pytest.raises(ValidationError):
        model.model_validate(contract)


def test_request_is_frozen_and_generation_settings_are_bounded() -> None:
    request = InferenceRequest.model_validate(valid_request())
    with pytest.raises(ValidationError):
        request.seed = 8
    with pytest.raises(ValidationError):
        GenerationSettings(speaking_rate=0)


@pytest.mark.parametrize(
    "path",
    [
        "../escaped.wav",
        "/absolute.wav",
        "runs/../escaped.wav",
        r"runs\windows.wav",
        "runs/not-wave.json",
    ],
)
def test_request_rejects_noncanonical_or_escaping_output_paths(path: str) -> None:
    payload = valid_request()
    payload["output_wav_path"] = path
    with pytest.raises(ValidationError):
        InferenceRequest.model_validate(payload)


def test_adapter_state_enforces_lifecycle_invariants() -> None:
    runtime = AdapterRuntime(
        requested_device="auto",
        resolved_device="cpu",
        dtype="float32",
    )
    assert AdapterState(lifecycle="loaded", loaded_model_id="fixture-eng", runtime=runtime)
    with pytest.raises(ValidationError):
        AdapterState(lifecycle="loaded")
    with pytest.raises(ValidationError):
        AdapterState(
            lifecycle="unloaded",
            loaded_model_id="fixture-eng",
            runtime=runtime,
        )


def test_inference_result_enforces_success_and_failure_shapes() -> None:
    success = InferenceResult(
        run_id=RUN_ID,
        status="success",
        wav_path="runs/fixture.wav",
        manifest_path="runs/fixture.manifest.json",
    )
    failure = InferenceResult(
        run_id=RUN_ID,
        status="failure",
        failure=FailureDetail(
            category=FailureCategory.SYNTHESIS_FAILURE,
            message="waveform synthesis failed",
        ),
    )
    assert success.failure is None
    assert failure.wav_path is None
    with pytest.raises(ValidationError):
        InferenceResult(run_id=RUN_ID, status="success")


def test_manifest_schema_is_strict_versioned_and_contains_no_prompt_field() -> None:
    manifest = RunManifest.model_validate(valid_manifest())
    assert manifest.manifest_schema_version == 1
    assert "text" not in RunManifest.model_fields
    assert "prompt_text" not in RunManifest.model_fields
    assert set(ManifestModel.model_fields) == {
        "model_id",
        "provider",
        "repository",
        "immutable_revision",
        "architecture",
        "documented_language_tag",
        "weight_license",
        "approved_use",
        "redistribution_status",
        "prompt_set_reference",
        "language_quality_status",
    }
    assert set(ManifestRuntime.model_fields) >= {"python_version", "workbench_version"}
    assert set(ManifestTimings.model_fields) == {
        "model_load_seconds",
        "synthesis_seconds",
    }
    assert set(ManifestAudio.model_fields) >= {"sample_rate", "wav_sha256"}
    assert manifest.adapter == AdapterIdentity(
        adapter_id="fake-vits",
        implementation_version="1.0.0",
    )


def test_manifest_requires_utc_ordered_timestamps() -> None:
    payload = valid_manifest()
    payload["started_at"] = datetime(2026, 7, 28, 12, 0)
    with pytest.raises(ValidationError):
        RunManifest.model_validate(payload)

    payload = valid_manifest()
    payload["completed_at"] = datetime(2026, 7, 28, 11, 59, tzinfo=UTC)
    with pytest.raises(ValidationError):
        RunManifest.model_validate(payload)


def test_prompt_hash_is_stable_and_content_sensitive() -> None:
    assert prompt_sha256("synthetic prompt") == prompt_sha256("synthetic prompt")
    assert prompt_sha256("synthetic prompt") != prompt_sha256("synthetic prompt changed")
