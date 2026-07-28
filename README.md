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

Milestone M2 establishes the neutral `tts_workbench` Python package, the
`audited-tts-workbench` 0.2.0 distribution, the `tts-workbench-*` CLI namespace,
and a canonical external artifact boundary. The completed model registry remains
metadata-only and never downloads model weights.

```powershell
python -m uv run tts-workbench-models validate
python -m uv run tts-workbench-models list
```

The registry accepts only immutable 40-character revisions, audited license
metadata, approved local non-commercial inference, no project redistribution
of weights, and `language_quality_status: not_evaluated`.

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
