"""Verify retained M7 WAV/report integrity and same-environment comparisons."""

from __future__ import annotations

import argparse
import hashlib
import json
import wave
from pathlib import Path

from tts_workbench.artifacts.paths import get_artifact_root, require_under_artifact_root
from tts_workbench.benchmark.contracts import BenchmarkReport
from tts_workbench.inference.contracts import RunManifest
from tts_workbench.models.registry import load_model_registry
from tts_workbench.qc.contracts import WaveformQcReport

PROMPT_HASHES = {
    "mms-eng": "f8cc7678783377f15fd576e51b2b1fffdf969a591415c3858f816042a1194892",
    "mms-vie": "b6919cd1f33ec808355462bfa29e8444f8525560f8223d0486e67b35f29854c5",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-prefix", type=Path, required=True)
    args = parser.parse_args()
    root = get_artifact_root()
    run = require_under_artifact_root(args.run_prefix, artifact_root=root)
    registry = load_model_registry()
    results = []
    manifests = [
        path
        for directory in ("runs", "cpu", "service/runs")
        for path in (run / directory).glob("*.manifest.json")
    ]
    for path in sorted(manifests):
        raw = path.read_text(encoding="utf-8")
        manifest = RunManifest.model_validate_json(raw)
        model = manifest.model.model_id
        entry = registry.by_id(model)
        assert manifest.model.repository == entry.repository
        assert manifest.model.immutable_revision == entry.revision
        assert manifest.prompt_sha256 == PROMPT_HASHES[model]
        assert manifest.model.prompt_set_reference == entry.prompt_set_reference
        assert manifest.model.language_quality_status == "not_evaluated"
        assert manifest.runtime.workbench_version == "1.0.0"
        assert manifest.adapter.implementation_version == "1.0.1"
        assert manifest.seed == 555 and manifest.dtype == "float32"
        assert manifest.requested_device == manifest.resolved_device
        service = path.is_relative_to(run / "service")
        base = run if service else root
        wav = require_under_artifact_root(Path(manifest.wav_path), artifact_root=base)
        assert wav == path.with_suffix("").with_suffix(".wav")
        digest = hashlib.sha256(wav.read_bytes()).hexdigest()
        assert digest == manifest.audio.wav_sha256
        with wave.open(str(wav), "rb") as reader:
            assert reader.getnchannels() == manifest.audio.channel_count == 1
            assert reader.getsampwidth() == 2 and reader.getcomptype() == "NONE"
            assert reader.getframerate() == manifest.audio.sample_rate == 16000
            assert reader.getnframes() == manifest.audio.sample_count
            assert reader.getnframes() / reader.getframerate() == manifest.audio.duration_seconds
            assert len(reader.readframes(reader.getnframes())) == reader.getnframes() * 2
        results.append({"model": model, "device": manifest.resolved_device, "service": service})
    assert len(results) == 8
    comparisons = []
    for model in PROMPT_HASHES:
        first = RunManifest.model_validate_json((run / f"runs/{model}.manifest.json").read_text())
        repeat = RunManifest.model_validate_json(
            (run / f"runs/{model}-repeat.manifest.json").read_text()
        )
        for field in (
            "model",
            "adapter",
            "runtime",
            "seed",
            "generation_settings",
            "prompt_sha256",
            "requested_device",
            "resolved_device",
            "dtype",
        ):
            assert getattr(first, field) == getattr(repeat, field)
        comparisons.append(
            {
                "model": model,
                "wav_bytes_equal": first.audio.wav_sha256 == repeat.audio.wav_sha256,
                "frame_count_equal": first.audio.sample_count == repeat.audio.sample_count,
            }
        )
        qc = WaveformQcReport.model_validate_json((run / f"qc/{model}.json").read_text())
        assert qc.evidence_scope == "engineering_sanity_check"
        assert qc.overall_status == "qc_passing"
        benchmark = BenchmarkReport.model_validate_json(
            (run / f"benchmarks/{model}.json").read_text()
        )
        assert benchmark.status == "completed" and benchmark.model == first.model
        assert benchmark.prompt_sha256 == first.prompt_sha256
        assert benchmark.aggregates.measured_success_count == 3
        assert benchmark.aggregates.measured_failure_count == 0
    print(json.dumps({"verified_pairs": results, "same_environment": comparisons}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
