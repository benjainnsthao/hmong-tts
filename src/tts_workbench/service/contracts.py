"""Strict, versioned contracts for the bounded local inference service."""

from __future__ import annotations

import ipaddress
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from tts_workbench.inference.contracts import (
    DeviceRequest,
    GenerationSettings,
    RelativeArtifactPath,
    RunId,
)
from tts_workbench.models.schema import ModelId, PromptSetReference


class StrictServiceContract(BaseModel):
    """Reject undocumented fields and mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class ServiceFailureCategory(StrEnum):
    """Stable, sanitized service failure categories."""

    INVALID_REQUEST = "invalid_request"
    UNKNOWN_OR_UNAPPROVED_MODEL = "unknown_or_unapproved_model"
    SERVICE_NOT_READY = "service_not_ready"
    QUEUE_FULL = "queue_full"
    DEADLINE_TIMEOUT = "deadline_timeout"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    DEVICE_UNAVAILABLE = "device_unavailable"
    MODEL_LOAD_FAILURE = "model_load_failure"
    SYNTHESIS_FAILURE = "synthesis_failure"
    INVALID_WAVEFORM = "invalid_waveform"
    ARTIFACT_BOUNDARY_FAILURE = "artifact_boundary_failure"
    ARTIFACT_COLLISION = "artifact_collision"
    ARTIFACT_WRITE_FAILURE = "artifact_write_failure"
    UNEXPECTED_INTERNAL_FAILURE = "unexpected_internal_failure"


class QueueAdmissionState(StrictServiceContract):
    """Observable bounded-coordinator state without request identity."""

    schema_version: Literal[1] = 1
    admission: Literal["open", "full", "closed"]
    pending_capacity: int = Field(ge=1, le=100)
    pending_requests: int = Field(ge=0)
    active_requests: int = Field(ge=0, le=1)

    @model_validator(mode="after")
    def require_consistent_state(self) -> QueueAdmissionState:
        if self.pending_requests > self.pending_capacity:
            raise ValueError("pending requests cannot exceed capacity")
        if self.admission == "full" and self.pending_requests != self.pending_capacity:
            raise ValueError("full admission requires a full pending queue")
        if self.admission == "open" and self.pending_requests >= self.pending_capacity:
            raise ValueError("open admission requires remaining pending capacity")
        return self


class HealthResponse(StrictServiceContract):
    """Process health independent of model and device readiness."""

    schema_version: Literal[1] = 1
    status: Literal["healthy"] = "healthy"
    service_version: Annotated[str, Field(min_length=1, max_length=80)]


class ReadinessResponse(StrictServiceContract):
    """Sanitized admission, artifact, runtime, and model readiness."""

    schema_version: Literal[1] = 1
    status: Literal["ready", "not_ready"]
    admission_ready: bool
    artifact_root_ready: bool
    core_environment_ready: bool
    optional_runtime_ready: bool
    model_loaded: bool
    lazy_model_loading: Literal[True] = True
    queue: QueueAdmissionState
    failure_categories: tuple[ServiceFailureCategory, ...] = ()

    @model_validator(mode="after")
    def require_status_consistency(self) -> ReadinessResponse:
        required_ready = (
            self.admission_ready and self.artifact_root_ready and self.core_environment_ready
        )
        if (self.status == "ready") != required_ready:
            raise ValueError("readiness status must match required service boundaries")
        return self


class ModelProvenanceResponse(StrictServiceContract):
    """Audited public source references for one registry entry."""

    model_card_url: Annotated[str, Field(min_length=1, max_length=300)]
    license_url: Annotated[str, Field(min_length=1, max_length=300)]
    audit_reference: Annotated[str, Field(min_length=1, max_length=240)]
    audited_on: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]


class ModelMetadataResponse(StrictServiceContract):
    """Immutable model identity and policy copied from the audited registry."""

    model_id: ModelId
    provider: Annotated[str, Field(min_length=1, max_length=120)]
    repository: Annotated[str, Field(min_length=3, max_length=200)]
    immutable_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    documented_language_tag: Annotated[str, Field(pattern=r"^[a-z]{3}$")]
    language_tag_standard: Literal["ISO 639-3"]
    architecture: Literal["vits"]
    weight_license: Annotated[str, Field(min_length=1, max_length=120)]
    approved_use: Literal["local_noncommercial_inference"]
    redistribution_status: Literal["weights_not_redistributed"]
    prompt_set_reference: PromptSetReference
    language_quality_status: Literal["not_evaluated"]
    provenance: ModelProvenanceResponse


class ModelListResponse(StrictServiceContract):
    """Metadata-only listing of approved registry entries."""

    schema_version: Literal[1] = 1
    registry_schema_version: Literal[1]
    models: tuple[ModelMetadataResponse, ...]


class SynthesisRequest(StrictServiceContract):
    """Caller-controlled synthesis fields; artifact and provenance are service owned."""

    schema_version: Literal[1] = 1
    model_id: ModelId
    text: Annotated[str, Field(min_length=1, max_length=500)]
    requested_device: DeviceRequest = "auto"
    seed: int = Field(default=555, ge=0, le=2**63 - 1)
    generation_settings: GenerationSettings = Field(default_factory=GenerationSettings)


class SynthesisSuccessResponse(StrictServiceContract):
    """Root-relative artifact references for one committed inference run."""

    schema_version: Literal[1] = 1
    status: Literal["success"] = "success"
    run_id: RunId
    wav_path: RelativeArtifactPath
    manifest_path: RelativeArtifactPath


class SanitizedServiceFailure(StrictServiceContract):
    """Failure response that never includes prompt or backend exception content."""

    schema_version: Literal[1] = 1
    status: Literal["failure"] = "failure"
    category: ServiceFailureCategory
    message: Annotated[str, Field(min_length=1, max_length=160)]


def _relative_prefix(value: str) -> str:
    if "\\" in value:
        raise ValueError("artifact prefix must use forward slashes")
    path = PurePosixPath(value)
    raw_parts = value.split("/")
    if (
        path.is_absolute()
        or value.startswith("/")
        or any(part in {"", ".", ".."} for part in raw_parts)
    ):
        raise ValueError("artifact prefix must be normalized and root-relative")
    if path.suffix:
        raise ValueError("artifact prefix must identify a directory")
    return path.as_posix()


class ServiceConfig(StrictServiceContract):
    """Fail-closed local service configuration."""

    schema_version: Literal[2]
    host: Annotated[str, Field(min_length=2, max_length=45)]
    port: int = Field(ge=1, le=65535)
    max_input_characters: int = Field(ge=1, le=500)
    queue_capacity: int = Field(ge=1, le=100)
    queue_timeout_seconds: float = Field(gt=0.0, le=600.0, allow_inf_nan=False)
    request_timeout_seconds: float = Field(gt=0.0, le=600.0, allow_inf_nan=False)
    active_inference_operations: Literal[1]
    workers: Literal[1]
    model_instances: Literal[1]
    seeded_generation: Literal[True]
    public_deployment_enabled: Literal[False]
    normalization_endpoint_public: Literal[False]
    access_log: Literal[False]
    log_request_text: Literal[False]
    log_client_ip: Literal[False]
    artifact_output_prefix: Annotated[str, Field(min_length=1, max_length=160)]

    @field_validator("host")
    @classmethod
    def require_literal_loopback_address(cls, value: str) -> str:
        try:
            address = ipaddress.ip_address(value)
        except ValueError as exc:
            raise ValueError("host must be a literal loopback address") from exc
        if not address.is_loopback:
            raise ValueError("host must be loopback-only")
        return value

    @field_validator("artifact_output_prefix")
    @classmethod
    def require_relative_artifact_prefix(cls, value: str) -> str:
        return _relative_prefix(value)

    @model_validator(mode="after")
    def require_queue_deadline_within_request_deadline(self) -> ServiceConfig:
        if self.queue_timeout_seconds > self.request_timeout_seconds:
            raise ValueError("queue timeout cannot exceed request timeout")
        return self
