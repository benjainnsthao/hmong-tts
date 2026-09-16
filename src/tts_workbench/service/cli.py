"""Validate, inspect, or explicitly launch the bounded local inference service."""

from __future__ import annotations

import argparse
import json
import socket
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import ValidationError

from tts_workbench.artifacts.paths import (
    ArtifactBoundaryError,
    find_repository_root,
    get_artifact_root,
)
from tts_workbench.config.loader import load_config
from tts_workbench.environment.detect import collect_environment
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

    get_artifact_root()
    family = socket.AF_INET6 if ":" in settings["host"] else socket.AF_INET
    with socket.socket(family) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind((settings["host"], settings["port"]))
    environment = collect_environment()
    if not environment.cpu_inference_ready and not environment.cuda_inference_ready:
        print(
            "Speech runtime is unavailable. Install with uv sync --frozen --extra mms "
            "in the external environment, then restart. The dashboard can still show setup status."
        )
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
    host = f"[{config.host}]" if ":" in config.host else config.host
    print(f"Local TTS Workbench: http://{host}:{config.port}/", flush=True)
    print("Press Ctrl-C when finished. Shutdown waits for active generation.", flush=True)
    try:
        server_runner(
            app,
            host=config.host,
            port=config.port,
            workers=1,
            access_log=False,
            log_level="info",
            proxy_headers=False,
        )
    except ArtifactBoundaryError:
        print(
            "STARTUP ERROR: Set TTS_WORKBENCH_ARTIFACT_ROOT to an existing absolute "
            "directory outside the repository, then restart.",
            file=sys.stderr,
        )
        return 2
    except OSError:
        print(
            "STARTUP ERROR: The local port or output directory is unavailable. "
            "Stop any existing workbench, check directory permissions, or choose "
            "another port in the service configuration.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
