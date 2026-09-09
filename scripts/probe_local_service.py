"""Exercise the real loopback service without printing request text."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlparse

import httpx

from tts_workbench.artifacts.paths import get_artifact_root, require_under_artifact_root
from tts_workbench.inference.mms_smoke import BUILTIN_SYNTHETIC_PROMPTS
from tts_workbench.models.registry import load_model_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--vie-prompt-file",
        type=Path,
        required=True,
        help="artifact-root-relative audited prompt file",
    )
    return parser


def _require_loopback_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1"}:
        raise ValueError("service probe requires an HTTP loopback URL")
    if (
        parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("service probe base URL must not include a path or query")
    return value.rstrip("/")


def _post_synthesis(client: httpx.Client, *, model_id: str, text: str) -> dict[str, str]:
    response = client.post(
        "/v1/synthesize",
        json={
            "schema_version": 1,
            "model_id": model_id,
            "text": text,
            "requested_device": "cuda",
            "seed": 555,
        },
    )
    response.raise_for_status()
    raw = response.text
    if text in raw:
        raise RuntimeError("service response echoed request text")
    payload = response.json()
    if payload.get("status") != "success":
        raise RuntimeError("service synthesis did not return success")
    return payload


def _validate_committed_result(
    *,
    artifact_root: Path,
    model_id: str,
    text: str,
    response: dict[str, str],
) -> None:
    wav_path = require_under_artifact_root(Path(response["wav_path"]), artifact_root=artifact_root)
    manifest_path = require_under_artifact_root(
        Path(response["manifest_path"]), artifact_root=artifact_root
    )
    if not wav_path.is_file() or not manifest_path.is_file():
        raise RuntimeError("service success artifacts are missing")
    raw_manifest = manifest_path.read_text(encoding="utf-8")
    if text in raw_manifest:
        raise RuntimeError("service manifest retained request text")
    manifest = json.loads(raw_manifest)
    expected_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if manifest["model"]["model_id"] != model_id or manifest["prompt_sha256"] != expected_hash:
        raise RuntimeError("service manifest identity or prompt hash mismatch")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    base_url = _require_loopback_url(args.base_url)
    artifact_root = get_artifact_root()
    prompt_path = require_under_artifact_root(args.vie_prompt_file, artifact_root=artifact_root)
    vie_text = prompt_path.read_text(encoding="utf-8").strip()
    if not vie_text:
        raise ValueError("audited prompt file is empty")

    registry = load_model_registry()
    eng_entry = registry.by_id("mms-eng")
    vie_entry = registry.by_id("mms-vie")
    eng_text = BUILTIN_SYNTHETIC_PROMPTS[eng_entry.prompt_set_reference]
    run_root = artifact_root / "service" / "runs"

    with httpx.Client(base_url=base_url, timeout=60.0) as client:
        health = client.get("/health")
        ready = client.get("/ready")
        models = client.get("/v1/models")
        health.raise_for_status()
        ready.raise_for_status()
        models.raise_for_status()
        model_payload = models.json()
        if {entry["model_id"] for entry in model_payload["models"]} != {
            eng_entry.model_id,
            vie_entry.model_id,
        }:
            raise RuntimeError("service registry metadata mismatch")

        before_rejection = set(run_root.glob("*")) if run_root.is_dir() else set()
        rejected_text = "synthetic rejected request marker"
        rejected = client.post(
            "/v1/synthesize",
            json={"model_id": "unregistered-model", "text": rejected_text},
        )
        if rejected.status_code != 404:
            raise RuntimeError("unknown model was not rejected")
        if rejected_text in rejected.text:
            raise RuntimeError("rejected response echoed request text")
        rejection_payload = rejected.json()
        if rejection_payload.get("category") != "unknown_or_unapproved_model":
            raise RuntimeError("rejection category mismatch")
        after_rejection = set(run_root.glob("*")) if run_root.is_dir() else set()
        if after_rejection != before_rejection:
            raise RuntimeError("rejected request left a partial artifact")

        eng_result = _post_synthesis(client, model_id=eng_entry.model_id, text=eng_text)
        _validate_committed_result(
            artifact_root=artifact_root,
            model_id=eng_entry.model_id,
            text=eng_text,
            response=eng_result,
        )
        vie_result = _post_synthesis(client, model_id=vie_entry.model_id, text=vie_text)
        _validate_committed_result(
            artifact_root=artifact_root,
            model_id=vie_entry.model_id,
            text=vie_text,
            response=vie_result,
        )

    print(
        json.dumps(
            {
                "health": health.json()["status"],
                "ready": ready.json()["status"],
                "registered_models": 2,
                "rejection": rejection_payload["category"],
                "rejection_left_artifacts": False,
                "successful_models": [eng_entry.model_id, vie_entry.model_id],
                "prompt_echo": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
