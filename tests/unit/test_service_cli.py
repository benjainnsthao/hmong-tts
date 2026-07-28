from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

from tts_workbench.service import cli as service_cli


def test_service_metadata_commands_are_offline_and_lazy(
    capsys: pytest.CaptureFixture[str],
) -> None:
    sys.modules.pop("torch", None)
    sys.modules.pop("transformers", None)

    assert service_cli.main(["schema"]) == 0
    assert '"synthesis_request"' in capsys.readouterr().out
    assert service_cli.main(["validate-config"]) == 0
    assert "PASS service: schema_version=2" in capsys.readouterr().out
    assert service_cli.main(["openapi"]) == 0
    openapi = json.loads(capsys.readouterr().out)
    assert "/v1/synthesize" in openapi["paths"]
    assert "torch" not in sys.modules
    assert "transformers" not in sys.modules


def test_service_run_fails_closed_without_model_access_acknowledgement(
    capsys: pytest.CaptureFixture[str],
) -> None:
    called = False

    def forbidden_runner(*_args: object, **_kwargs: object) -> None:
        nonlocal called
        called = True

    assert service_cli.main(["run"], server_runner=forbidden_runner) == 2
    assert "--acknowledge-model-access is required" in capsys.readouterr().err
    assert not called


def test_acknowledged_service_launch_uses_one_loopback_worker_without_access_log() -> None:
    captured: dict[str, object] = {}

    def runner(app: object, **settings: object) -> None:
        captured["app"] = app
        captured.update(settings)

    assert (
        service_cli.main(
            ["run", "--acknowledge-model-access"],
            server_runner=runner,
        )
        == 0
    )
    assert captured["host"] == "127.0.0.1"
    assert captured["workers"] == 1
    assert captured["access_log"] is False
    assert "app" in captured


def test_invalid_nonloopback_configuration_never_reaches_server(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = yaml.safe_load(Path("configs/inference/local.yaml").read_text(encoding="utf-8"))
    config["host"] = "0.0.0.0"
    path = tmp_path / "service.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    called = False

    def forbidden_runner(*_args: object, **_kwargs: object) -> None:
        nonlocal called
        called = True

    assert (
        service_cli.main(
            [
                "run",
                "--config",
                str(path),
                "--acknowledge-model-access",
            ],
            server_runner=forbidden_runner,
        )
        == 2
    )
    assert "SERVICE CONFIG ERROR" in capsys.readouterr().err
    assert not called
