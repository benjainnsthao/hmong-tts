import json
from pathlib import Path

import pytest

from tts_workbench.artifacts.paths import ARTIFACT_ROOT_ENV, LEGACY_ARTIFACT_ROOT_ENV
from tts_workbench.environment.detect import collect_environment, training_failures


def test_training_readiness_requires_expected_gpu_and_tools() -> None:
    report = {
        "os": {"system": "Linux", "machine": "x86_64", "wsl": True},
        "python": {"supported": True},
        "git": {"available": True},
        "ffmpeg": {"available": False},
        "gpu": {"expected_rtx_4070_present": False},
        "pytorch": {"installed": False},
        "artifact_root": {"valid": False},
    }
    failures = training_failures(report)
    assert "FFmpeg is unavailable" in failures
    assert "RTX 4070 is not visible to nvidia-smi" in failures
    assert "PyTorch is not installed" in failures
    assert f"{ARTIFACT_ROOT_ENV} is not a valid external directory" in failures


def test_environment_report_does_not_expose_artifact_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    (repo / "configs/models").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
    (repo / "configs/models/registry.yaml").write_text(
        "schema_version: 1\nmodels: []\n",
        encoding="utf-8",
    )
    artifact_root = tmp_path / "external-artifacts"
    artifact_root.mkdir()
    monkeypatch.setenv(ARTIFACT_ROOT_ENV, str(artifact_root))
    monkeypatch.delenv(LEGACY_ARTIFACT_ROOT_ENV, raising=False)

    report = collect_environment(repository_root=repo)

    assert report["artifact_root"] == {"valid": True, "reason": None}
    assert str(artifact_root.resolve()) not in json.dumps(report)
