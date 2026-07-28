"""Validate QC configuration or analyze an artifact-root-relative WAV."""

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
from tts_workbench.artifacts.paths import ArtifactBoundaryError, find_repository_root
from tts_workbench.config.loader import load_config
from tts_workbench.qc.analysis import WaveformQcAnalyzer
from tts_workbench.qc.contracts import QcThresholds, WaveformQcReport

DEFAULT_QC_CONFIG = Path("configs/qc/default.yaml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("schema", help="print the strict QC threshold/report schemas")
    validate = subparsers.add_parser("validate-config", help="validate a QC YAML file")
    validate.add_argument("--config", type=Path, default=DEFAULT_QC_CONFIG)
    analyze = subparsers.add_parser("analyze", help="analyze and atomically report one WAV")
    analyze.add_argument("--input", required=True, help="artifact-root-relative .wav path")
    analyze.add_argument("--output", required=True, help="artifact-root-relative .json path")
    analyze.add_argument("--config", type=Path, default=DEFAULT_QC_CONFIG)
    analyze.add_argument("--json", action="store_true", help="print the sanitized report JSON")
    return parser


def _config_path(path: Path) -> Path:
    return path if path.is_absolute() else find_repository_root() / path


def _load_thresholds(path: Path) -> QcThresholds:
    return cast(QcThresholds, load_config("qc", _config_path(path)))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "schema":
        payload = {
            "thresholds": QcThresholds.model_json_schema(),
            "report": WaveformQcReport.model_json_schema(),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    try:
        thresholds = _load_thresholds(args.config)
    except (OSError, ValueError, ValidationError, yaml.YAMLError):
        print("QC CONFIG ERROR: configuration validation failed.", file=sys.stderr)
        return 2
    if args.command == "validate-config":
        print(f"PASS qc: schema_version={thresholds.schema_version}")
        return 0

    try:
        report = WaveformQcAnalyzer(thresholds).analyze_artifact_wav(args.input)
        output_path = AtomicJsonReportStore().write(report, args.output)
    except (
        ArtifactBoundaryError,
        JsonReportCollisionError,
        JsonReportWriteError,
        OSError,
        ValueError,
    ):
        print("QC ERROR: analysis or report commitment failed.", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))
    else:
        failed_count = sum(rule.status == "fail" for rule in report.rules)
        print(
            f"QC {report.overall_status}: failed_rules={failed_count} "
            f"report={output_path.as_posix()}"
        )
    return 0 if report.overall_status == "qc_passing" else 1


if __name__ == "__main__":
    raise SystemExit(main())
