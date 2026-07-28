"""Run a registry-pinned, non-Hmong MMS inference smoke test outside the repository."""

from __future__ import annotations

import argparse
import platform
import sys
from collections.abc import Sequence
from pathlib import Path

from tts_workbench.artifacts.paths import (
    ArtifactBoundaryError,
    get_artifact_root,
    require_under_artifact_root,
)
from tts_workbench.artifacts.transaction import AtomicArtifactStore
from tts_workbench.inference.contracts import InferenceRequest
from tts_workbench.inference.execution import InferenceExecutor
from tts_workbench.inference.mms_vits import MmsVitsAdapter
from tts_workbench.models.registry import load_model_registry
from tts_workbench.models.schema import ModelRegistry

BUILTIN_SYNTHETIC_PROMPTS = {
    "builtin:project-synthetic-eng-smoke-v1": "this is a synthetic inference test",
}


def preflight_failures() -> list[str]:
    failures = []
    if platform.system() != "Linux":
        failures.append("the documented MMS environment is Linux/WSL2")
    if platform.machine().lower() not in {"x86_64", "amd64"}:
        failures.append("the locked MMS/CUDA path targets x86-64")
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except (ImportError, OSError) as exc:
        failures.append(f"MMS dependencies are unavailable ({type(exc).__name__})")
    return failures


def build_parser(registry: ModelRegistry) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        choices=sorted(model.model_id for model in registry.models),
        default="mms-eng",
    )
    parser.add_argument(
        "--text-file",
        type=Path,
        help="UTF-8 prompt with independent public-license/provenance review",
    )
    parser.add_argument("--output", type=Path, default=Path("smoke/mms-output.wav"))
    parser.add_argument("--seed", type=int, default=555)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--preflight-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    registry = load_model_registry()
    args = build_parser(registry).parse_args(argv)
    model_entry = registry.by_id(args.model)
    failures = preflight_failures()
    if failures:
        print("MMS smoke preflight failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 2
    if args.preflight_only:
        print("MMS smoke preflight passed.")
        return 0

    builtin_text = BUILTIN_SYNTHETIC_PROMPTS.get(model_entry.prompt_set_reference)
    if builtin_text is None and args.text_file is None:
        print(
            f"{args.model} requires --text-file with independent public prompt provenance; "
            "no language text is invented.",
            file=sys.stderr,
        )
        return 2
    try:
        artifact_root = get_artifact_root()
        output_path = require_under_artifact_root(args.output, artifact_root=artifact_root)
        text_path = (
            require_under_artifact_root(args.text_file, artifact_root=artifact_root)
            if args.text_file
            else None
        )
    except ArtifactBoundaryError as exc:
        print(f"ARTIFACT BOUNDARY ERROR: {exc}", file=sys.stderr)
        return 2
    try:
        text = text_path.read_text(encoding="utf-8").strip() if text_path else builtin_text
    except (OSError, UnicodeError):
        print("Smoke-test prompt file could not be read as UTF-8.", file=sys.stderr)
        return 2
    if not text:
        print("Smoke-test text is empty.", file=sys.stderr)
        return 2
    output_display = output_path.relative_to(artifact_root).as_posix()
    request = InferenceRequest(
        model_id=args.model,
        text=text,
        prompt_set_reference=model_entry.prompt_set_reference,
        requested_device=args.device,
        seed=args.seed,
        output_wav_path=output_display,
    )
    adapter = MmsVitsAdapter(registry)
    executor = InferenceExecutor(
        registry=registry,
        adapter=adapter,
        artifact_store=AtomicArtifactStore(artifact_root),
    )
    try:
        result = executor.execute(request)
    finally:
        adapter.unload()
    if result.status == "failure":
        assert result.failure is not None
        print(
            f"MMS smoke failed: category={result.failure.category.value}",
            file=sys.stderr,
        )
        return 2
    print(
        f"PASS model_id={args.model} repository={model_entry.repository} "
        f"revision={model_entry.revision} output={result.wav_path} "
        f"manifest={result.manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
