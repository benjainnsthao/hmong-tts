"""Strict generalized environment-capability report contracts."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from tts_workbench.evaluation.contracts import StrictM4Contract

ReadinessFailure = Literal[
    "python_version_unsupported",
    "git_unavailable",
    "artifact_root_invalid",
    "pytorch_unavailable",
    "transformers_unavailable",
    "cpu_runtime_unavailable",
    "cuda_runtime_unavailable",
    "cuda_device_unavailable",
]
MeasurementAvailability = Literal["available", "unavailable"]
DTypeName = Literal["float32", "float16", "bfloat16"]


class CommandCapability(StrictM4Contract):
    available: bool
    version: (
        Annotated[
            str,
            Field(min_length=1, max_length=160, pattern=r"^[^\r\n]+$"),
        ]
        | None
    ) = None

    @model_validator(mode="after")
    def require_version_only_when_available(self) -> CommandCapability:
        if self.available != (self.version is not None):
            raise ValueError("command availability and version must agree")
        return self


class PythonCapability(StrictM4Contract):
    version: Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+")]
    implementation: Annotated[
        str,
        Field(min_length=1, max_length=40, pattern=r"^[^\r\n]+$"),
    ]
    supported: bool


class OsCapability(StrictM4Contract):
    system: Annotated[str, Field(min_length=1, max_length=40, pattern=r"^[^\r\n]+$")]
    release: Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[^\r\n]+$")]
    architecture: Annotated[
        str,
        Field(min_length=1, max_length=40, pattern=r"^[^\r\n]+$"),
    ]
    is_wsl: bool


class ArtifactRootCapability(StrictM4Contract):
    valid: bool
    failure_reason: Literal["not_configured", "invalid"] | None = None

    @model_validator(mode="after")
    def require_reason_only_for_failure(self) -> ArtifactRootCapability:
        if self.valid == (self.failure_reason is not None):
            raise ValueError("artifact-root validity and failure reason must agree")
        return self


class OptionalPackageCapability(StrictM4Contract):
    available: bool
    version: (
        Annotated[
            str,
            Field(min_length=1, max_length=80, pattern=r"^[^\r\n]+$"),
        ]
        | None
    ) = None

    @model_validator(mode="after")
    def require_version_only_when_available(self) -> OptionalPackageCapability:
        if self.available != (self.version is not None):
            raise ValueError("package availability and version must agree")
        return self


class DeviceCapability(StrictM4Contract):
    name: Annotated[
        str,
        Field(min_length=1, max_length=120, pattern=r"^[^\r\n]+$"),
    ]
    memory_mib: int = Field(gt=0)
    supported_dtypes: tuple[DTypeName, ...]


class CudaCapability(StrictM4Contract):
    available: bool
    build_version: Annotated[str, Field(min_length=1, max_length=40)] | None = None
    devices: tuple[DeviceCapability, ...] = ()

    @model_validator(mode="after")
    def require_consistent_cuda_state(self) -> CudaCapability:
        if self.available and (self.build_version is None or not self.devices):
            raise ValueError("available CUDA requires a build version and at least one device")
        if not self.available and self.devices:
            raise ValueError("unavailable CUDA cannot report device details")
        return self


class ReadinessCapability(StrictM4Contract):
    ready: bool
    failure_reasons: tuple[ReadinessFailure, ...] = ()

    @model_validator(mode="after")
    def require_consistent_readiness(self) -> ReadinessCapability:
        if self.ready == bool(self.failure_reasons):
            raise ValueError("readiness and failure reasons must agree")
        if len(set(self.failure_reasons)) != len(self.failure_reasons):
            raise ValueError("readiness failure reasons must be unique")
        return self


class EnvironmentCapabilityReport(StrictM4Contract):
    """Sanitized capability metadata with no host or absolute-path fields."""

    report_schema_version: Literal[1] = 1
    python: PythonCapability
    os: OsCapability
    git: CommandCapability
    ffmpeg: CommandCapability
    artifact_root: ArtifactRootCapability
    pytorch: OptionalPackageCapability
    transformers: OptionalPackageCapability
    cuda: CudaCapability
    cpu_supported_dtypes: tuple[DTypeName, ...]
    core: ReadinessCapability
    cpu_inference: ReadinessCapability
    cuda_inference: ReadinessCapability
    core_ready: bool
    cpu_inference_ready: bool
    cuda_inference_ready: bool

    @model_validator(mode="after")
    def require_readiness_aliases_to_match(self) -> EnvironmentCapabilityReport:
        if (
            self.core_ready != self.core.ready
            or self.cpu_inference_ready != self.cpu_inference.ready
            or self.cuda_inference_ready != self.cuda_inference.ready
        ):
            raise ValueError("readiness aliases must match structured readiness records")
        return self
