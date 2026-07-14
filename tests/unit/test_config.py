from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from hmong_tts.config.loader import DEFAULT_CONFIG_FILES, load_all_configs, load_config


def test_all_committed_configs_parse(repository_root: Path) -> None:
    loaded = load_all_configs(repository_root)
    assert set(loaded) == set(DEFAULT_CONFIG_FILES)


def test_unknown_configuration_field_is_rejected(tmp_path: Path) -> None:
    config = {
        "schema_version": 1,
        "precision": "fp16",
        "per_device_batch_size": 4,
        "gradient_accumulation_steps": 8,
        "max_audio_seconds": 10,
        "length_bucketing": True,
        "gradient_clip_norm": 1,
        "learning_rate": 0.00001,
        "save_every_optimizer_steps": 500,
        "evaluate_every_optimizer_steps": 250,
        "keep_best_checkpoints": 3,
        "keep_latest_checkpoint": True,
        "seed": 1234,
        "tracker_mode": "local_or_offline_only",
        "sealed_test_set_for_selection": False,
        "unexpected": "fail closed",
    }
    path = tmp_path / "train.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_config("train", path)


@pytest.fixture
def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]
