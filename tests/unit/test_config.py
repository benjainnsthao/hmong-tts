from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from tts_workbench.config.loader import DEFAULT_CONFIG_FILES, load_all_configs, load_config


def test_all_committed_configs_parse(repository_root: Path) -> None:
    loaded = load_all_configs(repository_root)
    assert set(loaded) == set(DEFAULT_CONFIG_FILES)


def test_unknown_configuration_field_is_rejected(tmp_path: Path) -> None:
    config = {
        "schema_version": 1,
        "host": "127.0.0.1",
        "port": 8000,
        "max_input_characters": 500,
        "max_normalized_tokens": 500,
        "workers": 1,
        "gpu_queue_concurrency": 1,
        "request_timeout_seconds": 30.0,
        "model_instances": 1,
        "seeded_generation": True,
        "public_deployment_enabled": False,
        "normalization_endpoint_public": False,
        "log_request_text": False,
        "log_client_ip": False,
        "unexpected": "fail closed",
    }
    path = tmp_path / "inference.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_config("inference", path)


@pytest.fixture
def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]
