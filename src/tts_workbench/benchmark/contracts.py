"""Strict versioned contracts for provider-neutral M4 benchmarking."""

from __future__ import annotations

from collections import Counter
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from tts_workbench.environment.contracts import EnvironmentCapabilityReport
from tts_workbench.evaluation.contracts import (
    EvidenceScope,
    M4FailureCategory,
    M4FailureDetail,
    StrictM4Contract,
)
from tts_workbench.inference.contracts import (
    AdapterIdentity,
    DeviceRequest,
    GenerationSettings,
    ManifestModel,
    ManifestRuntime,
    ResolvedDevice,
    Sha256Digest,
)
from tts_workbench.models.schema import ModelId, PromptSetReference
from tts_workbench.qc.contracts import validate_relative_json_path

MemoryAvailability = Literal["available", "unavailable", "not_requested"]


class ResourceMemoryObservation(StrictM4Contract):
    """One provider-neutral memory snapshot; unavailable is never encoded as zero."""

    schema_version: Literal[1] = 1
    cpu_availability: MemoryAvailability
    cpu_peak_rss_bytes: int | None = Field(default=None, gt=0)
    cuda_availability: MemoryAvailability
    cuda_allocated_bytes: int | None = Field(default=None, ge=0)
    cuda_reserved_bytes: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_values_only_when_available(self) -> ResourceMemoryObservation:
        if (self.cpu_availability == "available") != (self.cpu_peak_rss_bytes is not None):
            raise ValueError("CPU availability and value must agree")
        cuda_values_present = (
            self.cuda_allocated_bytes is not None and self.cuda_reserved_bytes is not None
        )
        if (self.cuda_availability == "available") != cuda_values_present:
            raise ValueError("CUDA availability and values must agree")
        return self


class BenchmarkSettings(StrictM4Contract):
    """Bounded benchmark settings loaded from the active M4 configuration."""

    schema_version: Literal[1] = 1
    warmup_iterations: int = Field(ge=0, le=20)
    measured_repetitions: int = Field(ge=1, le=50)
    maximum_repetitions: int = Field(ge=1, le=50)
    seed: int = Field(ge=0, le=2**63 - 1)
    generation_settings: GenerationSettings
    requested_device: DeviceRequest
    observe_memory: bool
    report_output_path: str
    failure_handling: Literal["continue", "stop"]

    @field_validator("report_output_path")
    @classmethod
    def validate_report_path(cls, value: str) -> str:
        return validate_relative_json_path(value)

    @model_validator(mode="after")
    def enforce_repetition_ceiling(self) -> BenchmarkSettings:
        if self.warmup_iterations + self.measured_repetitions > self.maximum_repetitions:
            raise ValueError("warmup and measured repetitions cannot exceed maximum repetitions")
        return self


class BenchmarkRequest(StrictM4Contract):
    """One explicitly selected model benchmark request; prompt text is never reported."""

    schema_version: Literal[1] = 1
    model_id: ModelId
    text: Annotated[str, Field(min_length=1, max_length=500, pattern=r"^.*\S.*$")]
    prompt_set_reference: PromptSetReference
    settings: BenchmarkSettings


class BenchmarkObservation(StrictM4Contract):
    """One warmup or measured synthesis attempt."""

    observation_index: int = Field(ge=0)
    phase: Literal["warmup", "measured"]
    status: Literal["success", "failure"]
    synthesis_seconds: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    generated_audio_seconds: float | None = Field(default=None, gt=0.0, allow_inf_nan=False)
    real_time_factor: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    memory: ResourceMemoryObservation
    failure: M4FailureDetail | None = None

    @model_validator(mode="after")
    def require_success_or_failure_shape(self) -> BenchmarkObservation:
        values = (
            self.synthesis_seconds,
            self.generated_audio_seconds,
            self.real_time_factor,
        )
        if self.status == "success" and (any(value is None for value in values) or self.failure):
            raise ValueError("successful observations require timings and no failure")
        if self.status == "failure" and (
            any(value is not None for value in values) or not self.failure
        ):
            raise ValueError("failed observations require one failure and no timings")
        return self


class BenchmarkAggregates(StrictM4Contract):
    """Measured-only aggregates; warmups are explicitly excluded."""

    measured_success_count: int = Field(ge=0)
    measured_failure_count: int = Field(ge=0)
    median_synthesis_seconds: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    p95_synthesis_seconds: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    median_real_time_factor: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    p95_real_time_factor: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    failure_counts: dict[M4FailureCategory, int]

    @model_validator(mode="after")
    def require_aggregate_shape(self) -> BenchmarkAggregates:
        metrics = (
            self.median_synthesis_seconds,
            self.p95_synthesis_seconds,
            self.median_real_time_factor,
            self.p95_real_time_factor,
        )
        if self.measured_success_count == 0 and any(value is not None for value in metrics):
            raise ValueError("no-success aggregates cannot contain timing metrics")
        if self.measured_success_count > 0 and any(value is None for value in metrics):
            raise ValueError("successful aggregates require all timing metrics")
        if sum(self.failure_counts.values()) != self.measured_failure_count:
            raise ValueError("failure counts must equal measured failure count")
        if any(value <= 0 for value in self.failure_counts.values()):
            raise ValueError("failure counts must be positive")
        return self


class BenchmarkReport(StrictM4Contract):
    """Sanitized benchmark evidence with no prompt or machine identity."""

    report_schema_version: Literal[1] = 1
    evidence_scope: EvidenceScope = "engineering_sanity_check"
    status: Literal["completed", "partial", "failed"]
    registry_schema_version: Literal[1]
    model: ManifestModel
    adapter: AdapterIdentity
    prompt_sha256: Sha256Digest
    requested_device: DeviceRequest
    resolved_device: ResolvedDevice | None = None
    dtype: Annotated[str, Field(min_length=1, max_length=40)] | None = None
    seed: int = Field(ge=0, le=2**63 - 1)
    generation_settings: GenerationSettings
    warmup_iterations: int = Field(ge=0)
    measured_repetitions: int = Field(ge=1)
    failure_handling: Literal["continue", "stop"]
    runtime: ManifestRuntime | None = None
    environment: EnvironmentCapabilityReport
    cold_load_seconds: float = Field(ge=0.0, allow_inf_nan=False)
    memory_before_load: ResourceMemoryObservation
    memory_after_load: ResourceMemoryObservation
    memory_after_unload: ResourceMemoryObservation
    observations: tuple[BenchmarkObservation, ...]
    aggregates: BenchmarkAggregates
    load_failure: M4FailureDetail | None = None

    @model_validator(mode="after")
    def require_consistent_report(self) -> BenchmarkReport:
        if self.status == "failed":
            if (
                self.load_failure is None
                or self.resolved_device is not None
                or self.runtime is not None
            ):
                raise ValueError("failed load reports require one load failure and no runtime")
        else:
            if (
                self.load_failure is not None
                or self.resolved_device is None
                or self.runtime is None
            ):
                raise ValueError("loaded reports require runtime metadata and no load failure")
        measured = [item for item in self.observations if item.phase == "measured"]
        success_count = sum(item.status == "success" for item in measured)
        failures = Counter(
            item.failure.category
            for item in measured
            if item.status == "failure" and item.failure is not None
        )
        if success_count != self.aggregates.measured_success_count:
            raise ValueError("measured success count does not match observations")
        if dict(failures) != self.aggregates.failure_counts:
            raise ValueError("measured failure counts do not match observations")
        return self
