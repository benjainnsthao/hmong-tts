"""Detect whether a machine satisfies the Phase 0 and training prerequisites."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from hmong_tts.data.paths import DataBoundaryError, find_repository_root, get_data_root


@dataclass(frozen=True)
class CommandState:
    available: bool
    version: str | None


def _run_version(command: Sequence[str]) -> CommandState:
    executable = shutil.which(command[0])
    if executable is None:
        return CommandState(False, None)
    try:
        result = subprocess.run(
            [executable, *command[1:]],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return CommandState(True, "unreadable")
    output = (result.stdout or result.stderr).strip().splitlines()
    return CommandState(True, output[0] if output else "unknown")


def _gpu_state() -> dict[str, Any]:
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return {"nvidia_smi": False, "devices": [], "expected_rtx_4070_present": False}
    result = subprocess.run(
        [
            executable,
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    devices = []
    for line in result.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 3:
            devices.append({"name": parts[0], "memory_mib": parts[1], "driver": parts[2]})
    return {
        "nvidia_smi": result.returncode == 0,
        "devices": devices,
        "expected_rtx_4070_present": any("RTX 4070" in item["name"] for item in devices),
    }


def _torch_state() -> dict[str, Any]:
    try:
        import torch
    except (ImportError, OSError) as exc:
        return {"installed": False, "error": type(exc).__name__}
    cuda_available = bool(torch.cuda.is_available())
    devices = []
    if cuda_available:
        for index in range(torch.cuda.device_count()):
            properties = torch.cuda.get_device_properties(index)
            devices.append(
                {
                    "name": properties.name,
                    "memory_mib": round(properties.total_memory / (1024**2)),
                }
            )
    return {
        "installed": True,
        "version": torch.__version__,
        "cuda_build": torch.version.cuda,
        "cuda_available": cuda_available,
        "devices": devices,
    }


def collect_environment(*, repository_root: Path | None = None) -> dict[str, Any]:
    root = repository_root or find_repository_root()
    is_wsl = "microsoft" in platform.release().lower() or bool(os.environ.get("WSL_DISTRO_NAME"))
    python_version = platform.python_version()
    python_supported = sys.version_info[:2] == (3, 12)
    machine = platform.machine().lower()
    system = platform.system()
    data_root: dict[str, Any]
    try:
        get_data_root(repository_root=root)
    except DataBoundaryError as exc:
        data_root = {"valid": False, "reason": str(exc)}
    else:
        data_root = {"valid": True, "reason": None}

    uv_command = os.environ.get("UV", "uv")
    uv_state = _run_version((uv_command, "--version"))
    return {
        "os": {
            "system": system,
            "release": platform.release(),
            "machine": machine,
            "wsl": is_wsl,
        },
        "python": {
            "version": python_version,
            "supported": python_supported,
            "implementation": platform.python_implementation(),
        },
        "uv": asdict(uv_state),
        "git": asdict(_run_version(("git", "--version"))),
        "ffmpeg": asdict(_run_version(("ffmpeg", "-version"))),
        "cuda_toolkit": asdict(_run_version(("nvcc", "--version"))),
        "gpu": _gpu_state(),
        "pytorch": _torch_state(),
        "data_root": data_root,
    }


def training_failures(report: dict[str, Any]) -> list[str]:
    failures = []
    if report["os"]["system"] != "Linux":
        failures.append("training target requires Linux/WSL2")
    if report["os"]["machine"] not in {"x86_64", "amd64"}:
        failures.append("prebuilt CUDA training stack requires x86-64")
    if not report["os"]["wsl"] and report["os"]["system"] == "Linux":
        # Native Linux is supported even though WSL2 is the documented default.
        pass
    if not report["python"]["supported"]:
        failures.append("Python 3.12 is required")
    if not report["git"]["available"]:
        failures.append("Git is unavailable")
    if not report["ffmpeg"]["available"]:
        failures.append("FFmpeg is unavailable")
    if not report["gpu"]["expected_rtx_4070_present"]:
        failures.append("RTX 4070 is not visible to nvidia-smi")
    torch_state = report["pytorch"]
    if not torch_state.get("installed"):
        failures.append("PyTorch is not installed")
    elif not torch_state.get("cuda_available"):
        failures.append("PyTorch cannot access CUDA")
    if not report["data_root"]["valid"]:
        failures.append("HMONG_TTS_DATA_ROOT is not a valid external directory")
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    parser.add_argument("--output", type=Path, help="write the JSON report to this path")
    parser.add_argument("--require-data-root", action="store_true")
    parser.add_argument("--require-training", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = collect_environment()
    failures = training_failures(report)
    payload = {**report, "training_ready": not failures, "training_failures": failures}
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if args.require_data_root and not report["data_root"]["valid"]:
        return 2
    if args.require_training and failures:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
