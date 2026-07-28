"""Deterministic local-service fakes kept outside the production package."""

from __future__ import annotations

from dataclasses import dataclass, field

from tts_workbench.environment.contracts import (
    ArtifactRootCapability,
    CommandCapability,
    CudaCapability,
    EnvironmentCapabilityReport,
    OptionalPackageCapability,
    OsCapability,
    PythonCapability,
    ReadinessCapability,
)
from tts_workbench.inference.contracts import InferenceRequest, InferenceResult
from tts_workbench.service.contracts import QueueAdmissionState
from tts_workbench.service.coordinator import CoordinatorFailure


def service_environment(
    *,
    artifact_ready: bool = True,
    core_ready: bool = True,
    optional_runtime_ready: bool = False,
) -> EnvironmentCapabilityReport:
    """Return a sanitized environment report without probing the machine."""

    optional = OptionalPackageCapability(
        available=optional_runtime_ready,
        version="fixture-runtime" if optional_runtime_ready else None,
    )
    cpu = ReadinessCapability(
        ready=optional_runtime_ready and artifact_ready and core_ready,
        failure_reasons=()
        if optional_runtime_ready and artifact_ready and core_ready
        else ("pytorch_unavailable",),
    )
    cuda = ReadinessCapability(
        ready=False,
        failure_reasons=("cuda_runtime_unavailable",),
    )
    return EnvironmentCapabilityReport(
        python=PythonCapability(
            version="3.12.13",
            implementation="CPython",
            supported=core_ready,
        ),
        os=OsCapability(
            system="FixtureOS",
            release="fixture",
            architecture="x86_64",
            is_wsl=False,
        ),
        git=CommandCapability(
            available=core_ready,
            version="git fixture" if core_ready else None,
        ),
        ffmpeg=CommandCapability(available=False),
        artifact_root=ArtifactRootCapability(
            valid=artifact_ready,
            failure_reason=None if artifact_ready else "invalid",
        ),
        pytorch=optional,
        transformers=optional,
        cuda=CudaCapability(available=False),
        cpu_supported_dtypes=("float32",) if optional_runtime_ready else (),
        core=ReadinessCapability(
            ready=core_ready,
            failure_reasons=() if core_ready else ("python_version_unsupported",),
        ),
        cpu_inference=cpu,
        cuda_inference=cuda,
        core_ready=core_ready,
        cpu_inference_ready=cpu.ready,
        cuda_inference_ready=False,
    )


@dataclass
class ImmediateCoordinator:
    """Fake coordinator for application routing and lifecycle tests."""

    result: InferenceResult
    failure: CoordinatorFailure | None = None
    admission: str = "open"
    requests: list[InferenceRequest] = field(default_factory=list)
    start_count: int = 0
    shutdown_count: int = 0

    @property
    def state(self) -> QueueAdmissionState:
        return QueueAdmissionState(
            admission=self.admission,  # type: ignore[arg-type]
            pending_capacity=2,
            pending_requests=2 if self.admission == "full" else 0,
            active_requests=0,
        )

    async def start(self) -> None:
        self.start_count += 1

    async def submit(self, request: InferenceRequest) -> InferenceResult:
        self.requests.append(request)
        if self.failure is not None:
            raise self.failure
        return self.result

    async def shutdown(self) -> None:
        self.admission = "closed"
        self.shutdown_count += 1
