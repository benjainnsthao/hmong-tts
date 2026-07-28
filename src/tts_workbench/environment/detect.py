"""Collect sanitized core, CPU-inference, and CUDA-inference capabilities."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tts_workbench.artifacts.paths import (
    ARTIFACT_ROOT_ENV,
    LEGACY_ARTIFACT_ROOT_ENV,
    ArtifactBoundaryError,
    find_repository_root,
    get_artifact_root,
)
from tts_workbench.environment.contracts import (
    ArtifactRootCapability,
    CommandCapability,
    CudaCapability,
    DeviceCapability,
    DTypeName,
    EnvironmentCapabilityReport,
    OptionalPackageCapability,
    OsCapability,
    PythonCapability,
)
from tts_workbench.environment.readiness import build_environment_report


@dataclass(frozen=True)
class RuntimeSnapshot:
    """Sanitized optional-runtime facts returned by an injectable collector."""

    pytorch: OptionalPackageCapability
    transformers: OptionalPackageCapability
    cuda: CudaCapability


CommandCollector = Callable[[Sequence[str]], CommandCapability]
SystemCollector = Callable[[], tuple[PythonCapability, OsCapability]]
ArtifactCollector = Callable[[Path], ArtifactRootCapability]
RuntimeCollector = Callable[[], RuntimeSnapshot]


def _safe_version_line(value: str, fallback: str = "unreadable") -> str:
    line = value.strip().splitlines()[0].strip() if value.strip() else fallback
    lowered = line.casefold()
    if any(marker in lowered for marker in (":\\", "/home/", "\\users\\", "file://")):
        return fallback
    return line[:160] or fallback


def _run_version(command: Sequence[str]) -> CommandCapability:
    executable = shutil.which(command[0])
    if executable is None:
        return CommandCapability(available=False)
    try:
        result = subprocess.run(
            [executable, *command[1:]],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return CommandCapability(available=True, version="unreadable")
    return CommandCapability(
        available=True,
        version=_safe_version_line(result.stdout or result.stderr),
    )


def _system_state() -> tuple[PythonCapability, OsCapability]:
    release = platform.release()[:120] or "unknown"
    is_wsl = "microsoft" in release.casefold() or bool(os.environ.get("WSL_DISTRO_NAME"))
    python = PythonCapability(
        version=platform.python_version(),
        implementation=platform.python_implementation(),
        supported=sys.version_info[:2] == (3, 12),
    )
    operating_system = OsCapability(
        system=platform.system()[:40] or "unknown",
        release=release,
        architecture=platform.machine().casefold()[:40] or "unknown",
        is_wsl=is_wsl,
    )
    return python, operating_system


def _artifact_state(repository_root: Path) -> ArtifactRootCapability:
    try:
        get_artifact_root(repository_root=repository_root)
    except ArtifactBoundaryError:
        configured = bool(
            os.environ.get(ARTIFACT_ROOT_ENV, "").strip()
            or os.environ.get(LEGACY_ARTIFACT_ROOT_ENV, "").strip()
        )
        return ArtifactRootCapability(
            valid=False,
            failure_reason="invalid" if configured else "not_configured",
        )
    return ArtifactRootCapability(valid=True)


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)[:80]
    except (importlib.metadata.PackageNotFoundError, OSError, ValueError):
        return None


def _device_capabilities(torch: Any) -> tuple[DeviceCapability, ...]:
    devices: list[DeviceCapability] = []
    for index in range(int(torch.cuda.device_count())):
        properties = torch.cuda.get_device_properties(index)
        dtypes: list[DTypeName] = ["float32", "float16"]
        if bool(torch.cuda.is_bf16_supported()):
            dtypes.append("bfloat16")
        devices.append(
            DeviceCapability(
                name=str(properties.name)[:120],
                memory_mib=max(1, round(int(properties.total_memory) / (1024**2))),
                supported_dtypes=tuple(dtypes),
            )
        )
    return tuple(devices)


def _optional_runtime_state() -> RuntimeSnapshot:
    torch_version = _distribution_version("torch")
    transformers_version = _distribution_version("transformers")
    transformers_available = False
    if transformers_version is not None:
        try:
            importlib.import_module("transformers")
        except (ImportError, OSError, RuntimeError):
            pass
        else:
            transformers_available = True
    if torch_version is None:
        return RuntimeSnapshot(
            pytorch=OptionalPackageCapability(available=False),
            transformers=OptionalPackageCapability(
                available=transformers_available,
                version=transformers_version if transformers_available else None,
            ),
            cuda=CudaCapability(available=False),
        )
    try:
        torch = importlib.import_module("torch")
    except (ImportError, OSError, RuntimeError):
        return RuntimeSnapshot(
            pytorch=OptionalPackageCapability(available=False),
            transformers=OptionalPackageCapability(
                available=transformers_available,
                version=transformers_version if transformers_available else None,
            ),
            cuda=CudaCapability(available=False),
        )

    try:
        cuda_available = bool(torch.cuda.is_available())
    except (AttributeError, RuntimeError, TypeError, ValueError):
        cuda_available = False
    cuda_build = getattr(getattr(torch, "version", None), "cuda", None)
    cuda = CudaCapability(
        available=False,
        build_version=str(cuda_build)[:40] if cuda_build else None,
    )
    if cuda_available:
        try:
            devices = _device_capabilities(torch)
        except (AttributeError, RuntimeError, TypeError, ValueError):
            devices = ()
        if devices:
            cuda = CudaCapability(
                available=True,
                build_version=str(cuda_build or "unknown")[:40],
                devices=devices,
            )
    return RuntimeSnapshot(
        pytorch=OptionalPackageCapability(available=True, version=torch_version),
        transformers=OptionalPackageCapability(
            available=transformers_available,
            version=transformers_version if transformers_available else None,
        ),
        cuda=cuda,
    )


def collect_environment(
    *,
    repository_root: Path | None = None,
    command_collector: CommandCollector = _run_version,
    system_collector: SystemCollector = _system_state,
    artifact_collector: ArtifactCollector = _artifact_state,
    runtime_collector: RuntimeCollector = _optional_runtime_state,
) -> EnvironmentCapabilityReport:
    """Collect an injectable report without hostnames, usernames, or absolute paths."""

    root = repository_root or find_repository_root()
    python, operating_system = system_collector()
    git = command_collector(("git", "--version"))
    ffmpeg = command_collector(("ffmpeg", "-version"))
    artifact_root = artifact_collector(root)
    runtime = runtime_collector()
    return build_environment_report(
        python=python,
        operating_system=operating_system,
        git=git,
        ffmpeg=ffmpeg,
        artifact_root=artifact_root,
        pytorch=runtime.pytorch,
        transformers=runtime.transformers,
        cuda=runtime.cuda,
    )


def training_failures(report: EnvironmentCapabilityReport) -> list[str]:
    """Deprecated compatibility view of CUDA-inference readiness."""

    warnings.warn(
        "training readiness was replaced by generalized CUDA-inference readiness",
        FutureWarning,
        stacklevel=2,
    )
    return list(report.cuda_inference.failure_reasons)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the capability report as JSON")
    parser.add_argument("--output", type=Path, help="write the sanitized JSON report")
    parser.add_argument("--require-artifact-root", action="store_true")
    parser.add_argument("--require-core", action="store_true")
    parser.add_argument("--require-cpu-inference", action="store_true")
    parser.add_argument("--require-cuda-inference", action="store_true")
    parser.add_argument(
        "--require-training",
        action="store_true",
        help="deprecated alias for --require-cuda-inference",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = collect_environment()
    rendered = json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if args.require_artifact_root and not report.artifact_root.valid:
        return 2
    if args.require_core and not report.core_ready:
        return 2
    if args.require_cpu_inference and not report.cpu_inference_ready:
        return 2
    if args.require_cuda_inference and not report.cuda_inference_ready:
        return 2
    if args.require_training:
        warnings.warn(
            "--require-training is deprecated; use --require-cuda-inference",
            FutureWarning,
            stacklevel=1,
        )
        if not report.cuda_inference_ready:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
