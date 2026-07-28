"""Inspect benchmark contracts or run one explicitly authorized registered model."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import yaml
from pydantic import ValidationError

from tts_workbench.artifacts.json_report import (
    AtomicJsonReportStore,
    JsonReportCollisionError,
    JsonReportWriteError,
)
from tts_workbench.artifacts.paths import (
    ArtifactBoundaryError,
    find_repository_root,
    get_artifact_root,
    require_under_artifact_root,
)
from tts_workbench.benchmark.contracts import (
    BenchmarkReport,
    BenchmarkRequest,
    BenchmarkSettings,
)
from tts_workbench.benchmark.resources import DefaultResourceObserver
from tts_workbench.benchmark.runner import BenchmarkRunError, BenchmarkRunner
from tts_workbench.config.loader import load_config
from tts_workbench.environment.detect import collect_environment
from tts_workbench.inference.mms_smoke import BUILTIN_SYNTHETIC_PROMPTS
from tts_workbench.inference.mms_vits import MmsVitsAdapter
from tts_workbench.models.registry import load_model_registry

DEFAULT_BENCHMARK_CONFIG = Path("configs/benchmark/default.yaml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("schema", help="print strict benchmark request/report schemas")
    validate = subparsers.add_parser("validate-config", help="validate benchmark YAML")
    validate.add_argument("--config", type=Path, default=DEFAULT_BENCHMARK_CONFIG)
    run = subparsers.add_parser("run", help="run one registered model benchmark")
    run.add_argument("--model", required=True)
    run.add_argument(
        "--prompt-file",
        type=Path,
        help="artifact-root-relative independently audited public prompt",
    )
    run.add_argument("--config", type=Path, default=DEFAULT_BENCHMARK_CONFIG)
    run.add_argument("--output", help="artifact-root-relative .json override")
    run.add_argument("--json", action="store_true", help="print the sanitized report JSON")
    run.add_argument(
        "--acknowledge-model-access",
        action="store_true",
        help="explicitly authorize local model access for this run",
    )
    return parser


def _config_path(path: Path) -> Path:
    return path if path.is_absolute() else find_repository_root() / path


def _load_settings(path: Path) -> BenchmarkSettings:
    return cast(BenchmarkSettings, load_config("benchmark", _config_path(path)))


def _prompt_for_model(reference: str, prompt_file: Path | None) -> str:
    builtin = BUILTIN_SYNTHETIC_PROMPTS.get(reference)
    if builtin is not None:
        if prompt_file is not None:
            raise ValueError("a built-in audited prompt does not accept an override")
        return builtin
    if prompt_file is None:
        raise ValueError("this model requires an independently audited public prompt file")
    if prompt_file.is_absolute():
        raise ValueError("prompt path must be artifact-root-relative")
    root = get_artifact_root()
    path = require_under_artifact_root(prompt_file, artifact_root=root)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("audited public prompt file was empty")
    return text


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "schema":
        payload = {
            "request": BenchmarkRequest.model_json_schema(),
            "report": BenchmarkReport.model_json_schema(),
            "settings": BenchmarkSettings.model_json_schema(),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    try:
        settings = _load_settings(args.config)
    except (OSError, ValueError, ValidationError, yaml.YAMLError):
        print("BENCHMARK CONFIG ERROR: configuration validation failed.", file=sys.stderr)
        return 2
    if args.command == "validate-config":
        print(f"PASS benchmark: schema_version={settings.schema_version}")
        return 0
    if not args.acknowledge_model_access:
        print(
            "BENCHMARK BLOCKED: --acknowledge-model-access is required.",
            file=sys.stderr,
        )
        return 2

    try:
        registry = load_model_registry()
        entry = registry.by_id(args.model)
        text = _prompt_for_model(entry.prompt_set_reference, args.prompt_file)
        if args.output is not None:
            payload = settings.model_dump(mode="python")
            payload["report_output_path"] = args.output
            settings = BenchmarkSettings.model_validate(payload)
        request = BenchmarkRequest(
            model_id=entry.model_id,
            text=text,
            prompt_set_reference=entry.prompt_set_reference,
            settings=settings,
        )
        report_store = AtomicJsonReportStore()
        report_store.validate_destination(settings.report_output_path)
        adapter = MmsVitsAdapter(registry)
        report = BenchmarkRunner(
            registry=registry,
            adapter=adapter,
            environment_collector=collect_environment,
            resource_observer=DefaultResourceObserver(requested=settings.observe_memory),
        ).run(request)
        output_path = report_store.write(report, settings.report_output_path)
    except (
        ArtifactBoundaryError,
        BenchmarkRunError,
        JsonReportCollisionError,
        JsonReportWriteError,
        KeyError,
        OSError,
        UnicodeError,
        ValueError,
    ):
        print("BENCHMARK ERROR: execution or report commitment failed.", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))
    else:
        print(
            f"BENCHMARK {report.status}: successes="
            f"{report.aggregates.measured_success_count} failures="
            f"{report.aggregates.measured_failure_count} report={output_path.as_posix()}"
        )
    return 0 if report.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
