from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tts_workbench.environment.contracts import (
    ArtifactRootCapability,
    CommandCapability,
    CudaCapability,
    DeviceCapability,
    EnvironmentCapabilityReport,
    OptionalPackageCapability,
    OsCapability,
    PythonCapability,
)
from tts_workbench.environment.detect import (
    RuntimeSnapshot,
    collect_environment,
    main,
    training_failures,
)


def system_state(
    *,
    supported: bool = True,
) -> tuple[PythonCapability, OsCapability]:
    return (
        PythonCapability(
            version="3.12.10" if supported else "3.11.9",
            implementation="CPython",
            supported=supported,
        ),
        OsCapability(
            system="FixtureOS",
            release="fixture-release",
            architecture="x86_64",
            is_wsl=False,
        ),
    )


def commands(*, git: bool = True, ffmpeg: bool = False) -> object:
    def collect(command: tuple[str, ...]) -> CommandCapability:
        available = git if command[0] == "git" else ffmpeg
        return CommandCapability(
            available=available,
            version=f"{command[0]} fixture" if available else None,
        )

    return collect


def runtime(
    *,
    pytorch: bool = False,
    transformers: bool = False,
    cuda: bool = False,
    device_name: str = "Generic CUDA Device",
) -> RuntimeSnapshot:
    return RuntimeSnapshot(
        pytorch=OptionalPackageCapability(
            available=pytorch,
            version="fixture-torch" if pytorch else None,
        ),
        transformers=OptionalPackageCapability(
            available=transformers,
            version="fixture-transformers" if transformers else None,
        ),
        cuda=CudaCapability(
            available=cuda,
            build_version="fixture-cuda" if cuda else None,
            devices=(
                DeviceCapability(
                    name=device_name,
                    memory_mib=8192,
                    supported_dtypes=("float32", "float16"),
                ),
            )
            if cuda
            else (),
        ),
    )


def report_for(
    tmp_path: Path,
    *,
    supported_python: bool = True,
    git: bool = True,
    artifact_valid: bool = True,
    runtime_state: RuntimeSnapshot | None = None,
) -> EnvironmentCapabilityReport:
    return collect_environment(
        repository_root=tmp_path,
        command_collector=commands(git=git),  # type: ignore[arg-type]
        system_collector=lambda: system_state(supported=supported_python),
        artifact_collector=lambda _: ArtifactRootCapability(
            valid=artifact_valid,
            failure_reason=None if artifact_valid else "invalid",
        ),
        runtime_collector=lambda: runtime_state or runtime(),
    )


def test_environment_contract_is_strict_frozen_and_versioned(tmp_path: Path) -> None:
    report = report_for(tmp_path)
    assert report.report_schema_version == 1
    with pytest.raises(ValidationError):
        EnvironmentCapabilityReport.model_validate({**report.model_dump(), "hostname": "forbidden"})
    with pytest.raises(ValidationError):
        report.core_ready = False  # type: ignore[misc]


def test_core_only_environment_does_not_require_ffmpeg_cuda_or_rtx(
    tmp_path: Path,
) -> None:
    report = report_for(tmp_path)
    assert report.core_ready
    assert not report.cpu_inference_ready
    assert not report.cuda_inference_ready
    assert not report.ffmpeg.available
    assert "pytorch_unavailable" in report.cpu_inference.failure_reasons
    rendered = json.dumps(report.model_dump(mode="json")).casefold()
    assert "rtx 4070" not in rendered


def test_cpu_ready_environment_is_not_cuda_ready(tmp_path: Path) -> None:
    report = report_for(
        tmp_path,
        runtime_state=runtime(pytorch=True, transformers=True),
    )
    assert report.core_ready
    assert report.cpu_inference_ready
    assert not report.cuda_inference_ready
    assert report.cpu_supported_dtypes == ("float32",)
    assert CudaCapability(available=False, build_version="fixture-build").build_version


def test_generic_cuda_device_is_ready_without_model_specific_requirement(
    tmp_path: Path,
) -> None:
    report = report_for(
        tmp_path,
        runtime_state=runtime(pytorch=True, transformers=True, cuda=True),
    )
    assert report.cuda_inference_ready
    assert report.cuda.devices[0].name == "Generic CUDA Device"
    assert report.cuda.devices[0].memory_mib == 8192


def test_broken_environment_reports_sanitized_failure_reasons(tmp_path: Path) -> None:
    report = report_for(
        tmp_path,
        supported_python=False,
        git=False,
        artifact_valid=False,
    )
    assert not report.core_ready
    assert report.core.failure_reasons == (
        "python_version_unsupported",
        "git_unavailable",
    )
    assert "artifact_root_invalid" in report.cpu_inference.failure_reasons


def test_report_has_no_artifact_path_or_private_machine_fields(tmp_path: Path) -> None:
    report = report_for(tmp_path)
    rendered = json.dumps(report.model_dump(mode="json"), sort_keys=True)
    assert str(tmp_path.resolve()) not in rendered
    assert all(
        forbidden not in rendered.casefold()
        for forbidden in ("hostname", "username", "ip_address", "environment_variable")
    )


def test_deprecated_training_view_maps_to_cuda_readiness(tmp_path: Path) -> None:
    report = report_for(
        tmp_path,
        runtime_state=runtime(pytorch=True, transformers=True),
    )
    with pytest.warns(FutureWarning, match="generalized CUDA-inference"):
        failures = training_failures(report)
    assert failures == ["cuda_runtime_unavailable", "cuda_device_unavailable"]
    assert all("RTX" not in failure for failure in failures)


def test_deprecated_cli_flag_is_explicit_and_enforced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = report_for(
        tmp_path,
        runtime_state=runtime(pytorch=True, transformers=True),
    )
    monkeypatch.setattr(
        "tts_workbench.environment.detect.collect_environment",
        lambda: report,
    )
    with pytest.warns(FutureWarning, match="deprecated"):
        exit_code = main(["--require-training"])
    assert exit_code == 2
    assert '"cuda_inference_ready": false' in capsys.readouterr().out


def test_injected_collectors_avoid_optional_package_imports(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imported: list[str] = []

    def reject_import(name: str) -> None:
        imported.append(name)
        raise AssertionError("optional import should not run")

    monkeypatch.setattr(
        "tts_workbench.environment.detect.importlib.import_module",
        reject_import,
    )
    report = report_for(tmp_path)
    assert report.core_ready
    assert imported == []
