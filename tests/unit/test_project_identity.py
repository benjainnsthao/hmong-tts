from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

import pytest

import tts_workbench
from tts_workbench.config.loader import load_all_configs
from tts_workbench.models.registry import load_model_registry

EXPECTED_COMMANDS = {
    "tts-workbench-benchmark",
    "tts-workbench-config",
    "tts-workbench-env",
    "tts-workbench-mms-smoke",
    "tts-workbench-models",
    "tts-workbench-privacy-scan",
    "tts-workbench-qc",
    "tts-workbench-serve",
}


def load_project_metadata(repository_root: Path) -> dict[str, object]:
    return tomllib.loads((repository_root / "pyproject.toml").read_text(encoding="utf-8"))


def test_new_package_import_succeeds() -> None:
    assert tts_workbench.__version__ == "1.0.0"


def test_old_package_import_fails() -> None:
    importlib.invalidate_caches()
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("hmong_tts")


def test_distribution_and_build_identity_are_neutral(repository_root: Path) -> None:
    metadata = load_project_metadata(repository_root)
    project = metadata["project"]
    hatch = metadata["tool"]["hatch"]["build"]["targets"]["wheel"]

    assert project["name"] == "audited-tts-workbench"
    assert project["version"] == "1.0.0"
    assert hatch["packages"] == ["src/tts_workbench"]


def test_only_new_cli_entry_points_are_active(repository_root: Path) -> None:
    metadata = load_project_metadata(repository_root)
    scripts = metadata["project"]["scripts"]

    assert set(scripts) == EXPECTED_COMMANDS
    assert all(target.startswith("tts_workbench.") for target in scripts.values())


def test_active_configuration_and_registry_load_from_renamed_package(
    repository_root: Path,
) -> None:
    configs = load_all_configs(repository_root)
    registry = load_model_registry(repository_root=repository_root)

    assert set(configs) == {"benchmark", "inference", "qc"}
    assert {model.model_id for model in registry.models} == {"mms-eng", "mms-vie"}
