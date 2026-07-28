"""Load, validate, and list audited public TTS checkpoints without downloading weights."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import yaml
from pydantic import ValidationError

from tts_workbench.artifacts.paths import find_repository_root
from tts_workbench.models.schema import ModelRegistry

DEFAULT_MODEL_REGISTRY_FILE = Path("configs/models/registry.yaml")


def load_model_registry(
    path: Path | None = None,
    *,
    repository_root: Path | None = None,
) -> ModelRegistry:
    """Load a registry from an explicit path or the committed default."""
    if path is None:
        root = repository_root or find_repository_root()
        registry_path = root / DEFAULT_MODEL_REGISTRY_FILE
    else:
        registry_path = path
    with registry_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{registry_path} must contain a YAML mapping")
    return ModelRegistry.model_validate(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, help="alternate registry YAML")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate schema, provenance, and policy fields")
    list_parser = subparsers.add_parser("list", help="list registered checkpoint metadata")
    list_parser.add_argument("--json", action="store_true", help="emit registry entries as JSON")
    return parser


def _render_table(registry: ModelRegistry) -> str:
    headings = (
        "MODEL_ID",
        "LANGUAGE",
        "ARCHITECTURE",
        "APPROVED_USE",
        "QUALITY",
        "REPOSITORY",
        "REVISION",
    )
    rows = [
        (
            model.model_id,
            model.documented_language_tag,
            model.architecture,
            model.approved_use,
            model.language_quality_status,
            model.repository,
            model.revision,
        )
        for model in sorted(registry.models, key=lambda item: item.model_id)
    ]
    return "\n".join("\t".join(row) for row in (headings, *rows))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        registry = load_model_registry(args.registry)
    except (OSError, ValueError, ValidationError, yaml.YAMLError) as exc:
        print(f"MODEL REGISTRY ERROR: {exc}", file=sys.stderr)
        return 2

    if args.command == "validate":
        print(
            f"PASS model_registry: schema_version={registry.schema_version} "
            f"models={len(registry.models)}"
        )
        return 0

    if args.json:
        payload = [model.model_dump(mode="json") for model in registry.models]
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_table(registry))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
