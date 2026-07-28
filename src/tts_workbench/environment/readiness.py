"""Pure generalized-readiness calculation separated from runtime collection."""

from __future__ import annotations

from tts_workbench.environment.contracts import (
    ArtifactRootCapability,
    CommandCapability,
    CudaCapability,
    EnvironmentCapabilityReport,
    OptionalPackageCapability,
    OsCapability,
    PythonCapability,
    ReadinessCapability,
    ReadinessFailure,
)


def build_environment_report(
    *,
    python: PythonCapability,
    operating_system: OsCapability,
    git: CommandCapability,
    ffmpeg: CommandCapability,
    artifact_root: ArtifactRootCapability,
    pytorch: OptionalPackageCapability,
    transformers: OptionalPackageCapability,
    cuda: CudaCapability,
) -> EnvironmentCapabilityReport:
    """Calculate three readiness levels from already-sanitized capability facts."""

    core_failures: list[ReadinessFailure] = []
    if not python.supported:
        core_failures.append("python_version_unsupported")
    if not git.available:
        core_failures.append("git_unavailable")

    cpu_failures = list(core_failures)
    if not artifact_root.valid:
        cpu_failures.append("artifact_root_invalid")
    if not pytorch.available:
        cpu_failures.append("pytorch_unavailable")
    if not transformers.available:
        cpu_failures.append("transformers_unavailable")

    cuda_failures = list(cpu_failures)
    if not cuda.available:
        cuda_failures.extend(("cuda_runtime_unavailable", "cuda_device_unavailable"))

    core = ReadinessCapability(
        ready=not core_failures,
        failure_reasons=tuple(core_failures),
    )
    cpu = ReadinessCapability(
        ready=not cpu_failures,
        failure_reasons=tuple(cpu_failures),
    )
    cuda_readiness = ReadinessCapability(
        ready=not cuda_failures,
        failure_reasons=tuple(cuda_failures),
    )
    return EnvironmentCapabilityReport(
        python=python,
        os=operating_system,
        git=git,
        ffmpeg=ffmpeg,
        artifact_root=artifact_root,
        pytorch=pytorch,
        transformers=transformers,
        cuda=cuda,
        cpu_supported_dtypes=("float32",),
        core=core,
        cpu_inference=cpu,
        cuda_inference=cuda_readiness,
        core_ready=core.ready,
        cpu_inference_ready=cpu.ready,
        cuda_inference_ready=cuda_readiness.ready,
    )
