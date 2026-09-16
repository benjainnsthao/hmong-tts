"""Verify installed wheel assets without the source checkout on the import path."""

import os
import subprocess
import sys
import tarfile
from pathlib import Path


def test_installed_wheel_serves_dashboard_assets(repository_root: Path, tmp_path: Path) -> None:
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "UV_OFFLINE": "1"}
    build = subprocess.run(
        ["uv", "build", "--offline", "--out-dir", str(tmp_path / "dist")],
        cwd=repository_root,
        env=environment,
        capture_output=True,
    )
    assert build.returncode == 0, "populate the pinned build cache before packaging tests"
    with tarfile.open(next((tmp_path / "dist").glob("*.tar.gz"))) as archive:
        for name in ("index.html", "styles.css", "app.js"):
            assert any(member.name.endswith("/service/static/" + name) for member in archive)
    wheel = next((tmp_path / "dist").glob("*.whl"))
    target = tmp_path / "installed"
    install = subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            sys.executable,
            "--target",
            str(target),
            "--no-deps",
            "--offline",
            str(wheel),
        ],
        env=environment,
        capture_output=True,
    )
    assert install.returncode == 0
    script = """
import json, os
from pathlib import Path
from fastapi.testclient import TestClient
import tts_workbench
from tts_workbench.service.application import create_app
from tts_workbench.service.contracts import ServiceConfig
assert Path(tts_workbench.__file__).is_relative_to(Path(os.environ['PYTHONPATH']))
config = ServiceConfig.model_validate_json(os.environ['TTS_TEST_CONFIG'])
client = TestClient(create_app(config), base_url='http://127.0.0.1:8000')
assert 'Local TTS Workbench' in client.get('/').text
for name in ('styles.css', 'app.js'):
    response = client.get('/ui/' + name)
    assert response.status_code == 200 and len(response.content) > 100
client.close()
"""
    from tts_workbench.service.cli import _load_service_config

    config = _load_service_config(repository_root / "configs/inference/local.yaml")
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        capture_output=True,
        env={**environment, "PYTHONPATH": str(target), "TTS_TEST_CONFIG": config.model_dump_json()},
    )
    assert result.returncode == 0, result.stderr.decode()
