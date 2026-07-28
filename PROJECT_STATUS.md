# Project status

Last updated: 2026-07-28

## Current milestone

- Project: audited pretrained multi-language TTS inference, benchmarking, and
  local-deployment workbench.
- Milestone: **M2 active identity and artifact namespace — complete**.
- Active branch: `rescope/audited-tts-workbench`.
- Preserved baseline: `archive/white-hmong-single-speaker-tts-v0.1` at
  `fd1756485b1e1b75fd1efee5e37519fa8e255415`.
- M2 changes remain local; no M2 commit, branch update, merge, or tag has been
  pushed.

## Approved scope

Build reusable TTS infrastructure using properly licensed public non-Hmong
checkpoints. The long-term purpose is to support a possible future
community-validated Hmong learning application.

The current project makes no White Hmong support, pronunciation, or linguistic
correctness claim. White Hmong adaptation and NV-001 through NV-008 remain
deferred **[NV]**.

## M1 deliverables

- Strict registry schema version 1.
- Immutable checkpoint revisions and required provenance.
- Registered English and Vietnamese MMS/VITS checkpoints.
- Required local non-commercial use and no-weight-redistribution policy.
- Required `language_quality_status: not_evaluated`.
- Metadata-only `validate` and `list` commands.
- MMS smoke path reads repository and revision from the registry.
- Synthetic tests for mutable revisions, missing provenance, duplicate
  identities, unapproved use, unknown licenses, and capability overclaims.

## M1 validation

- Frozen lock check and offline core synchronization: PASS.
- Formatting and linting: PASS.
- Strict source typing: PASS.
- Active inference configuration validation: PASS.
- Model-registry validation and listing: PASS; two entries.
- Privacy/artifact scan: PASS; no forbidden material.
- Complete synthetic suite: PASS; 54 tests, 54% branch-aware aggregate
  coverage.
- No model weights, model cache, generated audio, training, service, or network
  model access was used.

## M2 deliverables

- Neutral `tts_workbench` Python package with no compatibility import package.
- `audited-tts-workbench` distribution version 0.2.0.
- Five active `tts-workbench-*` CLI entry points; no legacy CLI entry points.
- Canonical `TTS_WORKBENCH_ARTIFACT_ROOT`.
- Temporary warning-based compatibility for the legacy artifact-root variable,
  with conflicting paths rejected.
- Active `artifacts.paths` API and artifact-oriented exception/constant names.
- Neutral repository-root detection requiring `pyproject.toml` and
  `configs/models/registry.yaml`.
- Active artifact documentation moved to `artifacts/README.md`.
- Synthetic identity, compatibility, boundary, and root-detection tests.

## M2 validation

- Frozen lock validation: PASS.
- Offline frozen core synchronization: PASS; local distribution replaced with
  `audited-tts-workbench==0.2.0`.
- Formatting and Ruff lint: PASS.
- Strict source typing: PASS; 15 source files.
- Active configuration validation: PASS.
- Model-registry validation and listing: PASS; schema version 1, two unchanged
  entries.
- Privacy/artifact scan: PASS; 87 candidate files, no forbidden material.
- Complete synthetic suite: PASS; 68 tests, 61% branch-aware aggregate
  coverage.
- Full pre-commit suite: PASS.
- Package smoke: `tts_workbench` imports at 0.2.0 and the old import is
  unavailable.
- CLI smoke: all five `tts-workbench-*` help paths pass and no old executable
  entry point remains.
- Obsolete-identifier and `git diff --check` audits: PASS.
- No model weights, model cache, audio, network model access, M3 adapter,
  benchmark, service, or application code was used or added.

## Preserved historical work

The completed White Hmong single-speaker Phase 0 validation remains unchanged
in `reports/validation/`. Recording, consent, private-data, training, and native
human-evaluation plans are historical material indexed in
`docs/history/white_hmong_single_speaker/`.

The unresolved native-validation register remains active only as deferred
future-work evidence in `docs/deferred/white_hmong_native_validation.md`.

## Explicitly not started

- Reusable inference-engine milestone.
- Benchmark runner or metrics.
- Local inference API or service.
- New checkpoint or dependency downloads.
- White Hmong text handling, prompts, normalization, adaptation, or evaluation.
- Recording, private speaker data, consent execution, or training.

## Open risks and blockers

- **LICENSE-001:** no project code license is granted; public redistribution
  requires an owner decision.
- Registered MMS weights are CC BY-NC 4.0 and remain non-commercial.
- Vietnamese inference still requires an independently audited public prompt;
  the project invents none.
- The legacy artifact-root variable remains accepted only for the documented
  0.2 migration window and must be removed in a later breaking release.
- Environment readiness remains training-oriented and RTX-4070-specific; a
  general CPU/GPU inference capability report is a later milestone.
- No registered model has language quality evidence from this workbench.

## Next executable task

After M2 review and separate authorization, begin M3 by defining a fake-backed
provider-neutral inference adapter and atomic run-manifest contract. Do not
download or execute model weights, add waveform benchmarking, or begin a local
service during the synthetic M3 entry slice.
