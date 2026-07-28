# Project status

Last updated: 2026-07-28

## Current milestone

- Project: audited pretrained multi-language TTS inference, benchmarking, and
  local-deployment workbench.
- Milestone: **M3 reusable inference adapter and run manifest — complete**.
- Active branch: `rescope/audited-tts-workbench`.
- Preserved baseline: `archive/white-hmong-single-speaker-tts-v0.1` at
  `fd1756485b1e1b75fd1efee5e37519fa8e255415`.

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

## M3 deliverables

- Frozen, extra-forbid schema-version-1 inference request, generation setting,
  result, adapter identity/state, waveform, and success-manifest contracts.
- Provider-neutral `TTSAdapter` lifecycle with explicit load, synthesize,
  unload, observable state, and one owned model/backend per instance.
- Registry-owned `MmsVitsAdapter` with lazy PyTorch/Transformers imports and an
  injected fake-testable backend protocol.
- Explicit `auto`, `cpu`, and `cuda` handling with stable dependency, device,
  load, synthesis, waveform, boundary, and artifact failure categories.
- Request validation, registry/prompt-provenance lookup, prompt SHA-256 hashing,
  execution timing, structural validation, and result orchestration.
- Atomic mono PCM WAV and schema-version-1 success-manifest transaction with
  Windows-safe closed temporaries, manifest-last commit semantics, collision
  rejection, and rollback after validation/serialization/replacement failures.
- Root-relative manifest paths and no raw prompt, absolute root, client,
  machine, credential, private-identifier, or linguistic-quality fields.
- Existing `tts-workbench-mms-smoke` command refactored onto M3 contracts.
- Test-only deterministic fake adapter/backends and pytest-temporary synthetic
  WAVs; no production fake API.
- Active contract, architecture, registry, environment, smoke, artifact, status,
  roadmap, and decision documentation.

## M3 validation

- Frozen lock validation and offline frozen core synchronization: PASS.
- Formatting and Ruff lint: PASS.
- Strict source typing: PASS; 21 source files.
- Active configuration validation: PASS.
- Model-registry validation/listing: PASS; schema version 1, two unchanged
  entries.
- Privacy/artifact scan: PASS.
- Complete synthetic suite: PASS; 123 tests, 74% branch-aware aggregate
  coverage.
- Full pre-commit suite: PASS.
- Package and inference-contract imports: PASS without importing PyTorch or
  Transformers.
- CLI help: PASS for all five `tts-workbench-*` commands; no old package or CLI
  entry point exists.
- No weights, model cache, external audio, network model access, FastAPI,
  service, M4 QC/benchmarking, or application code was used or added.

## Preserved historical work

The completed White Hmong single-speaker Phase 0 validation remains unchanged
in `reports/validation/`. Recording, consent, private-data, training, and native
human-evaluation plans are historical material indexed in
`docs/history/white_hmong_single_speaker/`.

The unresolved native-validation register remains active only as deferred
future-work evidence in `docs/deferred/white_hmong_native_validation.md`.

## Explicitly not started

- M4 waveform QC beyond structural commit validation.
- Benchmark runner, benchmark metrics, or generalized inference readiness.
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
- The optional real MMS backend is contract-tested through fakes but has not
  downloaded or executed either registered checkpoint during M3.

## Next executable task

Begin M4 at the committed `WaveformResult` and `RunManifest` boundaries. Add
non-linguistic waveform QC schemas and synthetic defect fixtures first, followed
by benchmark and generalized environment-capability contracts. Do not download
or execute model weights without separate authorization, and do not begin M5
service or application work.
