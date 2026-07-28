from __future__ import annotations

import tomllib
from pathlib import Path

import yaml


def test_production_service_has_no_public_browser_deployment_or_fake_mode(
    repository_root: Path,
) -> None:
    service_root = repository_root / "src/tts_workbench/service"
    rendered = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(service_root.glob("*.py"))
    )
    forbidden = (
        "CORSMiddleware",
        "allow_origins",
        "0.0.0.0",
        "analytics",
        "telemetry",
        "cloud deployment",
        "ngrok",
        "production_fake",
        "fake_backend",
        "gradio",
        "streamlit",
    )
    assert all(value.casefold() not in rendered.casefold() for value in forbidden)


def test_service_dependencies_are_minimal_and_do_not_install_framework_extras(
    repository_root: Path,
) -> None:
    metadata = tomllib.loads((repository_root / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = metadata["project"]["dependencies"]
    assert "fastapi==0.136.3" in dependencies
    assert "starlette==1.0.0" in dependencies
    assert "uvicorn==0.46.0" in dependencies
    assert all("fastapi[" not in dependency for dependency in dependencies)
    assert all("uvicorn[" not in dependency for dependency in dependencies)
    assert "httpx==0.28.1" in metadata["dependency-groups"]["dev"]


def test_committed_service_configuration_is_fail_closed(
    repository_root: Path,
) -> None:
    config = yaml.safe_load(
        (repository_root / "configs/inference/local.yaml").read_text(encoding="utf-8")
    )
    assert config["schema_version"] == 2
    assert config["host"] == "127.0.0.1"
    assert config["workers"] == 1
    assert config["model_instances"] == 1
    assert config["active_inference_operations"] == 1
    assert config["public_deployment_enabled"] is False
    assert config["access_log"] is False
    assert config["log_request_text"] is False
    assert config["log_client_ip"] is False


def test_m5_documents_and_release_risk_state_are_present(
    repository_root: Path,
) -> None:
    local_service = (repository_root / "docs/local_service.md").read_text(encoding="utf-8")
    threat_model = (repository_root / "docs/service_threat_model.md").read_text(encoding="utf-8")
    risk_register = (repository_root / "docs/release_risk_register.md").read_text(encoding="utf-8")
    for required in (
        "loopback",
        "not authentication",
        "non-preempt",
        "language_quality_status: not_evaluated",
    ):
        assert required.casefold() in (local_service + threat_model).casefold()
    service_risk = risk_register.split("REL-SERVICE-001", maxsplit=1)[1].split(
        "###",
        maxsplit=1,
    )[0]
    assert "`mitigated`" in service_risk
    assert "pending the final M7" in service_risk
