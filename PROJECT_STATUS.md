# Project status

Last updated: 2026-07-28

## Current milestone

- Project: audited pretrained multi-language TTS inference, benchmarking, and
  local-deployment workbench.
- Milestone: **M1 audited model-registry vertical slice — complete**.
- Active branch: `rescope/audited-tts-workbench`.
- Preserved baseline: `archive/white-hmong-single-speaker-tts-v0.1` at
  `fd1756485b1e1b75fd1efee5e37519fa8e255415`.
- No branch or tag has been pushed by this rescope.

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
- The `hmong_tts` package name and `HMONG_TTS_DATA_ROOT` variable are
  transitional names that should be migrated separately.
- Environment readiness remains training-oriented and RTX-4070-specific; a
  general CPU/GPU inference capability report is a later milestone.
- No registered model has language quality evidence from this workbench.

## Next executable task

After review and separate authorization, extract a reusable MMS inference
adapter and run-manifest contract. Do not begin the local service milestone
before the adapter and benchmark boundaries are approved.
