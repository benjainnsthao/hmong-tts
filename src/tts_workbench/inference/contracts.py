"""Versioned provider-neutral inference and run-manifest contracts."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from tts_workbench.inference.prompts import PromptProvenance
from tts_workbench.models.schema import ModelId, PromptSetReference

Sha256Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
RunId = Annotated[
    str,
    Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"),
]
RelativeArtifactPath = Annotated[str, Field(min_length=1, max_length=240)]
DeviceRequest = Literal["auto", "cpu", "cuda"]
ResolvedDevice = Literal["cpu", "cuda"]


class StrictContract(BaseModel):
    """Reject undocumented fields and mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class FailureCategory(StrEnum):
    """Stable, non-sensitive inference failure categories."""

    INVALID_REQUEST = "invalid_request"
    UNKNOWN_OR_UNAPPROVED_MODEL = "unknown_or_unapproved_model"
    ARTIFACT_BOUNDARY_FAILURE = "artifact_boundary_failure"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    DEVICE_UNAVAILABLE = "device_unavailable"
    MODEL_LOAD_FAILURE = "model_load_failure"
    SYNTHESIS_FAILURE = "synthesis_failure"
    INVALID_WAVEFORM = "invalid_waveform"
    ARTIFACT_COLLISION = "artifact_collision"
    ARTIFACT_WRITE_FAILURE = "artifact_write_failure"


class GenerationSettings(StrictContract):
    """MMS/VITS generation controls supported by the current adapter."""

    noise_scale: float = Field(default=0.667, ge=0.0, le=2.0, allow_inf_nan=False)
    noise_scale_duration: float = Field(default=0.8, ge=0.0, le=2.0, allow_inf_nan=False)
    speaking_rate: float = Field(default=1.0, gt=0.0, le=4.0, allow_inf_nan=False)


def _validate_relative_artifact_path(value: str, *, required_suffix: str | None = None) -> str:
    if "\\" in value:
        raise ValueError("artifact paths must use forward slashes")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value.startswith("/")
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("artifact path must be a normalized artifact-root-relative path")
    if required_suffix is not None and not value.lower().endswith(required_suffix):
        raise ValueError(f"artifact path must end in {required_suffix}")
    return path.as_posix()


class InferenceRequest(StrictContract):
    """Validated input to provider-neutral synthesis."""

    schema_version: Literal[1] = 1
    model_id: ModelId
    text: Annotated[str, Field(min_length=1, max_length=500)]
    prompt_set_reference: PromptSetReference
    requested_device: DeviceRequest = "auto"
    seed: int = Field(default=555, ge=0, le=2**63 - 1)
    generation_settings: GenerationSettings = Field(default_factory=GenerationSettings)
    output_wav_path: RelativeArtifactPath

    @field_validator("output_wav_path")
    @classmethod
    def require_relative_wav_path(cls, value: str) -> str:
        return _validate_relative_artifact_path(value, required_suffix=".wav")


class AdapterIdentity(StrictContract):
    """Stable public identity of one adapter implementation."""

    schema_version: Literal[1] = 1
    adapter_id: Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
    implementation_version: Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+$")]


class AdapterRuntime(StrictContract):
    """Runtime metadata reported by a successfully loaded backend."""

    requested_device: DeviceRequest
    resolved_device: ResolvedDevice
    dtype: Annotated[str, Field(min_length=1, max_length=40)]
    pytorch_version: Annotated[str, Field(min_length=1, max_length=80)] | None = None
    transformers_version: Annotated[str, Field(min_length=1, max_length=80)] | None = None


class AdapterState(StrictContract):
    """Observable lifecycle state without provider-specific objects."""

    schema_version: Literal[1] = 1
    lifecycle: Literal["unloaded", "loaded"]
    loaded_model_id: ModelId | None = None
    runtime: AdapterRuntime | None = None

    @model_validator(mode="after")
    def require_consistent_lifecycle(self) -> AdapterState:
        if self.lifecycle == "loaded" and (self.loaded_model_id is None or self.runtime is None):
            raise ValueError("loaded adapter state requires model and runtime metadata")
        if self.lifecycle == "unloaded" and (
            self.loaded_model_id is not None or self.runtime is not None
        ):
            raise ValueError("unloaded adapter state cannot retain model or runtime metadata")
        return self


class WaveformResult(StrictContract):
    """Uncommitted mono waveform returned by an adapter."""

    schema_version: Literal[1] = 1
    samples: tuple[float, ...]
    sample_rate: int
    channel_count: int = 1


class FailureDetail(StrictContract):
    """Sanitized failure information safe to return to a caller."""

    category: FailureCategory
    message: Annotated[str, Field(min_length=1, max_length=160)]


class InferenceResult(StrictContract):
    """Success or failure returned by the execution layer."""

    schema_version: Literal[1] = 1
    run_id: RunId
    status: Literal["success", "failure"]
    wav_path: RelativeArtifactPath | None = None
    manifest_path: RelativeArtifactPath | None = None
    failure: FailureDetail | None = None

    @field_validator("wav_path")
    @classmethod
    def validate_optional_wav_path(cls, value: str | None) -> str | None:
        return (
            None
            if value is None
            else _validate_relative_artifact_path(value, required_suffix=".wav")
        )

    @field_validator("manifest_path")
    @classmethod
    def validate_optional_manifest_path(cls, value: str | None) -> str | None:
        return (
            None
            if value is None
            else _validate_relative_artifact_path(value, required_suffix=".manifest.json")
        )

    @model_validator(mode="after")
    def require_status_fields(self) -> InferenceResult:
        if self.status == "success":
            if self.wav_path is None or self.manifest_path is None or self.failure is not None:
                raise ValueError("successful result requires artifact paths and no failure")
        elif self.wav_path is not None or self.manifest_path is not None or self.failure is None:
            raise ValueError("failed result requires one failure and no artifact paths")
        return self


class ManifestModel(StrictContract):
    """Audited registry metadata copied into a successful manifest."""

    model_id: ModelId
    provider: str
    repository: str
    immutable_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    architecture: str
    documented_language_tag: Annotated[str, Field(pattern=r"^[a-z]{3}$")]
    weight_license: str
    approved_use: Literal["local_noncommercial_inference"]
    redistribution_status: Literal["weights_not_redistributed"]
    prompt_set_reference: PromptSetReference
    language_quality_status: Literal["not_evaluated"]


class ManifestRuntime(StrictContract):
    """Software versions that affect a synthesis run."""

    python_version: Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+")]
    workbench_version: Annotated[str, Field(min_length=1, max_length=80)]
    pytorch_version: Annotated[str, Field(min_length=1, max_length=80)] | None = None
    transformers_version: Annotated[str, Field(min_length=1, max_length=80)] | None = None


class ManifestTimings(StrictContract):
    """Execution-layer durations, excluding future M4 benchmarking."""

    model_load_seconds: float = Field(ge=0.0, allow_inf_nan=False)
    synthesis_seconds: float = Field(ge=0.0, allow_inf_nan=False)


class ManifestAudio(StrictContract):
    """Structural metadata for the committed mono PCM WAV."""

    sample_rate: int = Field(gt=0)
    channel_count: Literal[1]
    sample_count: int = Field(gt=0)
    duration_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    wav_sha256: Sha256Digest


class RunManifest(StrictContract):
    """Read historical v1 records and v2 records with explicit prompt provenance."""

    manifest_schema_version: Literal[1, 2] = 1
    prompt_provenance: PromptProvenance | None = None
    run_id: RunId
    status: Literal["success"]
    started_at: datetime
    completed_at: datetime
    adapter: AdapterIdentity
    registry_schema_version: Literal[1]
    model: ManifestModel
    prompt_sha256: Sha256Digest
    requested_device: DeviceRequest
    resolved_device: ResolvedDevice
    dtype: str
    seed: int = Field(ge=0, le=2**63 - 1)
    generation_settings: GenerationSettings
    runtime: ManifestRuntime
    timings: ManifestTimings
    audio: ManifestAudio
    wav_path: RelativeArtifactPath

    @field_validator("started_at", "completed_at")
    @classmethod
    def require_utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("manifest timestamps must be timezone-aware UTC values")
        return value

    @field_validator("wav_path")
    @classmethod
    def require_manifest_relative_wav_path(cls, value: str) -> str:
        return _validate_relative_artifact_path(value, required_suffix=".wav")

    @model_validator(mode="after")
    def require_timestamp_order(self) -> RunManifest:
        if self.manifest_schema_version == 2 and self.prompt_provenance is None:
            raise ValueError("version 2 requires actual prompt provenance")
        if self.completed_at < self.started_at:
            raise ValueError("completed_at cannot precede started_at")
        return self
