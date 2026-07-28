# Audited pretrained TTS workbench

Phase A of a possible future community-validated Hmong language-learning
application. This repository currently demonstrates audited public-checkpoint
registry, inference, evaluation, benchmarking, and local-deployment
infrastructure using non-Hmong models.

It does **not** claim White Hmong support, pronunciation accuracy, linguistic
correctness, or readiness for a Hmong learning application. White Hmong
adaptation and NV-001 through NV-008 remain deferred **[NV]**.

The original consented, single-speaker White Hmong TTS project is preserved on
the local branch `archive/white-hmong-single-speaker-tts-v0.1` at commit
`fd1756485b1e1b75fd1efee5e37519fa8e255415`. A browsable historical copy is
indexed in
[`docs/history/white_hmong_single_speaker/`](docs/history/white_hmong_single_speaker/README.md).

## Current milestone

Milestone M5 adds a bounded localhost-only FastAPI service around the M3
inference executor and M4 readiness boundaries. The distribution is
`audited-tts-workbench` 0.4.0 with eight `tts-workbench-*` commands.

Ordinary imports and CI do not import PyTorch or Transformers. The optional real
MMS backend imports them only when explicitly loaded; synthetic tests use
dependency-injected fakes and do not access weights or a network.

```powershell
python -m uv run tts-workbench-models validate
python -m uv run tts-workbench-models list
python -m uv run tts-workbench-qc schema
python -m uv run tts-workbench-benchmark schema
python -m uv run tts-workbench-env --json
python -m uv run tts-workbench-serve validate-config
python -m uv run tts-workbench-serve openapi
```

The registry accepts only immutable 40-character revisions, audited license
metadata, approved local non-commercial inference, no project redistribution
of weights, and `language_quality_status: not_evaluated`.

Both registry lookup and prompt-provenance matching occur before backend load.
Unknown models, path escapes, and prompt-reference mismatches therefore fail
without invoking an ML runtime.

QC thresholds are conservative engineering sanity checks, not language-quality
criteria. Benchmark reports separate cold model loading from warm synthesis,
exclude configured warmups from aggregates, and use deterministic nearest-rank
p95. No real checkpoint was executed to validate M4. See
[`docs/waveform_qc.md`](docs/waveform_qc.md) and
[`docs/benchmarking.md`](docs/benchmarking.md).

The service exposes only `GET /health`, `GET /ready`, `GET /v1/models`, and
`POST /v1/synthesize`. It accepts no artifact path, repository, revision,
prompt-provenance override, client identity, or normalization option. One
bounded FIFO coordinator owns exactly one active inference operation and one
adapter/model owner. Pending overflow and pre-execution expiry fail without
calling the adapter or creating artifacts. See
[`docs/local_service.md`](docs/local_service.md) and
[`docs/service_threat_model.md`](docs/service_threat_model.md).

Actual serving is blocked unless the operator supplies
`--acknowledge-model-access`. Configuration accepts only literal loopback
addresses, one Uvicorn worker, disabled access/request/client logging, and
public deployment disabled. Localhost is a development boundary, not a
complete authentication system.

## Reproducible core

```powershell
python -m uv sync --frozen
python -m uv run tts-workbench-config
python -m uv run tts-workbench-models validate
python -m uv run tts-workbench-privacy-scan
python -m uv run pytest --cov=tts_workbench --cov-branch
```

The optional MMS stack is large and remains platform-gated. Registry validation
and all ordinary tests run without PyTorch, Transformers, a GPU, network
access, or downloaded weights.

## Artifact boundary

Generated audio, model weights, model caches, and benchmark artifacts stay
outside Git. `TTS_WORKBENCH_ARTIFACT_ROOT` is canonical. A legacy variable is
accepted with a visible deprecation warning for the 0.2 migration window only;
conflicting values fail closed. See
[`artifacts/README.md`](artifacts/README.md).

Each successful M3 inference transaction writes a mono PCM WAV and publishes
its `.manifest.json` last as the commit marker. Manifests contain a SHA-256
prompt hash, audited model/runtime metadata, structural audio facts, and only
artifact-root-relative paths. They exclude raw prompts and machine identity.
See [`docs/inference_contract.md`](docs/inference_contract.md).

M4 analyzes WAVs and writes QC or benchmark JSON only through separate
artifact-root-relative, collision-rejecting atomic report transactions. QC
never changes whether an M3 artifact is committed.

M5 generates collision-resistant output names below the configured
`service/runs` prefix. Successful HTTP responses contain only the existing
root-relative WAV and manifest references. Rejected, full, expired, invalid,
or failed requests publish no success artifact.

## Licensing

The registered MMS checkpoints are CC BY-NC 4.0 and approved only for scoped
local non-commercial inference. The workbench does not redistribute their
weights. This repository itself remains all rights reserved until the owner
makes a separate code-license decision. See
[`docs/license_matrix.md`](docs/license_matrix.md).

## Status and limitations

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md),
[`docs/model_registry.md`](docs/model_registry.md), and
[`docs/architecture.md`](docs/architecture.md). The ordered implementation
milestones, acceptance criteria, and future Hmong-learning-application boundary
are documented in
[`docs/implementation_roadmap.md`](docs/implementation_roadmap.md).
Remaining release risks and the final M7 closure/owner-decision gate are in
[`docs/release_risk_register.md`](docs/release_risk_register.md).
