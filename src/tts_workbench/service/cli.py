"""Validate, inspect, or explicitly launch the bounded local inference service."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import ValidationError

from tts_workbench.artifacts.paths import find_repository_root
from tts_workbench.config.loader import load_config
from tts_workbench.service.application import create_app
from tts_workbench.service.contracts import (
    HealthResponse,
    ModelListResponse,
    ReadinessResponse,
    SanitizedServiceFailure,
    ServiceConfig,
    SynthesisRequest,
    SynthesisSuccessResponse,
)

DEFAULT_SERVICE_CONFIG = Path("configs/inference/local.yaml")
ServerRunner = Callable[..., None]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("schema", help="print strict service contract schemas")
    validate = subparsers.add_parser(
        "validate-config",
        help="validate the local service configuration",
    )
    validate.add_argument("--config", type=Path, default=DEFAULT_SERVICE_CONFIG)
    openapi = subparsers.add_parser(
        "openapi",
        help="print OpenAPI metadata without starting a service",
    )
    openapi.add_argument("--config", type=Path, default=DEFAULT_SERVICE_CONFIG)
    run = subparsers.add_parser("run", help="launch one loopback-only Uvicorn worker")
    run.add_argument("--config", type=Path, default=DEFAULT_SERVICE_CONFIG)
    run.add_argument(
        "--acknowledge-model-access",
        action="store_true",
        help="explicitly authorize lazy local model access while serving",
    )
    return parser


def _config_path(path: Path) -> Path:
    return path if path.is_absolute() else find_repository_root() / path


def _load_service_config(path: Path) -> ServiceConfig:
    return cast(ServiceConfig, load_config("inference", _config_path(path)))


def _run_uvicorn(app: Any, **settings: Any) -> None:
    import uvicorn

    uvicorn.run(app, **settings)


def _schema_payload() -> dict[str, object]:
    return {
        "config": ServiceConfig.model_json_schema(),
        "health": HealthResponse.model_json_schema(),
        "readiness": ReadinessResponse.model_json_schema(),
        "models": ModelListResponse.model_json_schema(),
        "synthesis_request": SynthesisRequest.model_json_schema(),
        "synthesis_success": SynthesisSuccessResponse.model_json_schema(),
        "failure": SanitizedServiceFailure.model_json_schema(),
    }


def main(
    argv: Sequence[str] | None = None,
    *,
    server_runner: ServerRunner = _run_uvicorn,
) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "schema":
        print(json.dumps(_schema_payload(), indent=2, sort_keys=True))
        return 0
    try:
        config = _load_service_config(args.config)
    except (OSError, ValueError, ValidationError, yaml.YAMLError):
        print("SERVICE CONFIG ERROR: configuration validation failed.", file=sys.stderr)
        return 2
    if args.command == "validate-config":
        print(
            f"PASS service: schema_version={config.schema_version} "
            f"host={config.host} workers={config.workers}"
        )
        return 0
    app = create_app(config)
    if args.command == "openapi":
        print(json.dumps(app.openapi(), indent=2, sort_keys=True))
        return 0
    if not args.acknowledge_model_access:
        print(
            "SERVICE BLOCKED: --acknowledge-model-access is required.",
            file=sys.stderr,
        )
        return 2
    server_runner(
        app,
        host=config.host,
        port=config.port,
        workers=1,
        access_log=False,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
