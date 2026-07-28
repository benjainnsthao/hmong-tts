"""Load and validate all versioned YAML configurations."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

import yaml

from tts_workbench.artifacts.paths import find_repository_root
from tts_workbench.config.schema import CONFIG_MODELS, StrictModel

DEFAULT_CONFIG_FILES = {
    "inference": Path("configs/inference/local.yaml"),
}


def load_config(kind: str, path: Path) -> StrictModel:
    if kind not in CONFIG_MODELS:
        raise ValueError(f"Unknown config kind: {kind}")
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return CONFIG_MODELS[kind].model_validate(payload)


def load_all_configs(repository_root: Path | None = None) -> dict[str, StrictModel]:
    root = repository_root or find_repository_root()
    return {kind: load_config(kind, root / path) for kind, path in DEFAULT_CONFIG_FILES.items()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--schema",
        choices=sorted(CONFIG_MODELS),
        help="print the JSON Schema for one configuration kind",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.schema:
        print(json.dumps(CONFIG_MODELS[args.schema].model_json_schema(), indent=2, sort_keys=True))
        return 0
    configs = load_all_configs()
    for kind, config in configs.items():
        print(f"PASS {kind}: schema_version={config.model_dump()['schema_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
