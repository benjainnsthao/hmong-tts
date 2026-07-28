from __future__ import annotations

import importlib
import struct
import sys
import wave
from collections.abc import Callable
from pathlib import Path

import pytest

from tts_workbench.artifacts.paths import ARTIFACT_ROOT_ENV
from tts_workbench.benchmark import cli as benchmark_cli
from tts_workbench.config.loader import main as config_main
from tts_workbench.environment.detect import main as environment_main
from tts_workbench.inference.mms_smoke import main as mms_smoke_main
from tts_workbench.models.registry import main as models_main
from tts_workbench.privacy.scan import main as privacy_main
from tts_workbench.qc import cli as qc_cli
from tts_workbench.service import cli as service_cli


@pytest.mark.parametrize(
    "main",
    [
        benchmark_cli.main,
        config_main,
        environment_main,
        mms_smoke_main,
        models_main,
        privacy_main,
        qc_cli.main,
        service_cli.main,
    ],
)
def test_all_eight_cli_help_paths_are_offline_and_do_not_import_optional_ml(
    main: Callable[[list[str]], int],
) -> None:
    sys.modules.pop("torch", None)
    sys.modules.pop("transformers", None)
    with pytest.raises(SystemExit) as result:
        main(["--help"])
    assert result.value.code == 0
    assert "torch" not in sys.modules
    assert "transformers" not in sys.modules


def test_metadata_only_schema_and_configuration_operations_are_offline(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert qc_cli.main(["schema"]) == 0
    assert '"report_schema_version"' in capsys.readouterr().out
    assert benchmark_cli.main(["schema"]) == 0
    assert '"cold_load_seconds"' in capsys.readouterr().out
    assert qc_cli.main(["validate-config"]) == 0
    assert "PASS qc" in capsys.readouterr().out
    assert benchmark_cli.main(["validate-config"]) == 0
    assert "PASS benchmark" in capsys.readouterr().out
    assert "torch" not in sys.modules
    assert "transformers" not in sys.modules


def test_benchmark_execution_fails_closed_without_acknowledgement(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert benchmark_cli.main(["run", "--model", "mms-eng"]) == 2
    assert "--acknowledge-model-access is required" in capsys.readouterr().err
    assert "torch" not in sys.modules
    assert "transformers" not in sys.modules


def test_qc_cli_writes_external_report_and_uses_stable_nonpass_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(ARTIFACT_ROOT_ENV, str(tmp_path))
    wav_path = tmp_path / "synthetic.wav"
    samples = (8192, -8192) * 80
    with wave.open(str(wav_path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    assert (
        qc_cli.main(
            [
                "analyze",
                "--input",
                "synthetic.wav",
                "--output",
                "qc/passing.json",
            ]
        )
        == 0
    )
    assert "qc_passing" in capsys.readouterr().out
    assert (tmp_path / "qc/passing.json").is_file()

    silent_path = tmp_path / "silent.wav"
    with wave.open(str(silent_path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(struct.pack("<160h", *([0] * 160)))
    assert (
        qc_cli.main(
            [
                "analyze",
                "--input",
                "silent.wav",
                "--output",
                "qc/failing.json",
            ]
        )
        == 1
    )
    assert "qc_failing" in capsys.readouterr().out
    assert (tmp_path / "qc/failing.json").is_file()


def test_old_cli_modules_remain_absent() -> None:
    importlib.invalidate_caches()
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("hmong_tts.cli")
