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

Milestone M3 establishes a provider-neutral, fake-testable inference engine.
It includes strict schema-versioned request/result contracts, an explicitly
loaded one-model-at-a-time adapter lifecycle, the first MMS/VITS adapter, and an
atomic WAV plus run-manifest transaction. The distribution remains
`audited-tts-workbench` 0.2.0 with the five `tts-workbench-*` commands.

Ordinary imports and CI do not import PyTorch or Transformers. The optional real
MMS backend imports them only when explicitly loaded; synthetic tests use
dependency-injected fakes and do not access weights or a network.

```powershell
python -m uv run tts-workbench-models validate
python -m uv run tts-workbench-models list
```

The registry accepts only immutable 40-character revisions, audited license
metadata, approved local non-commercial inference, no project redistribution
of weights, and `language_quality_status: not_evaluated`.

Both registry lookup and prompt-provenance matching occur before backend load.
Unknown models, path escapes, and prompt-reference mismatches therefore fail
without invoking an ML runtime.

## Reproducible core

```powershell
python -m uv sync --frozen
python -m uv run tts-workbench-config
python -m uv run tts-workbench-models validate
python -m uv run tts-workbench-privacy-scan
python -m uv run pytest
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
