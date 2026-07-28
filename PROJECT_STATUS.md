# Project status

Last updated: 2026-07-28

## Current milestone

- Project: audited pretrained multi-language TTS inference, benchmarking, and
  local-deployment workbench.
- Milestone: **M4 waveform QC, benchmarking, and environment capabilities —
  complete**.
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

## M4 deliverables

- Frozen, extra-forbid, schema-version-1 QC threshold, rule, report, benchmark,
  resource-observation, environment-capability, and M4 failure contracts.
- Deterministic in-memory and artifact-WAV QC for readable mono PCM16 input,
  structural facts, finite samples, peak/clipping, RMS, DC offset, and
  leading/trailing/total near-silence.
- Strict active `configs/qc/default.yaml` thresholds, included verbatim in
  every QC report and labeled `engineering_sanity_check`.
- Separate M3 commit safety and M4 QC: a committed WAV is never accepted or
  rejected retroactively by QC.
- Atomic artifact-root-relative JSON report storage with closed neighboring
  temporary files, collision rejection, deterministic serialization, and
  rollback after serialization or replacement failure.
- Provider-neutral benchmark orchestration with injected clocks, adapters,
  registry, environment collector, and resource observer.
- Separate cold-load timing; excluded warmups; measured median, nearest-rank
  p95, generated duration, real-time factor, and structured failure counts.
- Strict small local `configs/benchmark/default.yaml`, prompt hashing, exact
  immutable registry identity, runtime/device/settings metadata, and no raw
  prompt.
- Optional point-in-time CPU/CUDA memory observations; unavailable values are
  `unavailable`, never zero, and no telemetry is collected.
- Generalized `core_ready`, `cpu_inference_ready`, and
  `cuda_inference_ready` environment report with no RTX-model requirement.
  The old `--require-training` behavior is an explicit deprecated alias for
  CUDA-inference readiness.
- `tts-workbench-qc` and `tts-workbench-benchmark`, bringing the active total
  to seven offline-help-safe commands.
- Synthetic M4 defect, timing, memory, readiness, privacy, CLI, schema, and
  atomicity tests. Test fakes remain outside the production package.

## M4 validation

- Frozen lock validation and offline frozen core synchronization: PASS.
- Formatting, Ruff, and strict source MyPy: PASS.
- Active QC, benchmark, inference, and registry configuration/metadata
  validation: PASS.
- Privacy/artifact scan: PASS.
- Complete synthetic suite: PASS; 180 tests and 78% aggregate branch-aware
  coverage.
- Focused new-core branch coverage: PASS; 44 tests and 96% branch-aware
  coverage across QC calculation, benchmark orchestration, and environment
  readiness calculation.
- Full pre-commit, package import, lazy optional-import, seven-command help,
  old-identity, tracked-audio/weight, historical-evidence, deferred-NV, and Git
  whitespace checks: PASS.
- No weights, model cache, network model access, optional ML runtime, real
  audio, native-language content, FastAPI, HTTP, queue/concurrency, UI,
  perceptual/linguistic scoring, or M5 code was used or added.

## Preserved historical work

The completed White Hmong single-speaker Phase 0 validation remains unchanged
in `reports/validation/`. Recording, consent, private-data, training, and native
human-evaluation plans are historical material indexed in
`docs/history/white_hmong_single_speaker/`.

The unresolved native-validation register remains active only as deferred
future-work evidence in `docs/deferred/white_hmong_native_validation.md`.

## Explicitly not started

- M5 local inference API or service.
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
- CPU/CUDA inference readiness is capability evidence only; it does not prove a
  model will fit or execute successfully for every prompt or runtime build.
- QC defaults are conservative project sanity checks, not universal audio
  quality thresholds.
- Fake-backed benchmark tests validate orchestration and arithmetic, not
  real-device performance.
- No registered model has language quality evidence from this workbench.
- The optional real MMS backend is contract-tested through fakes but has not
  downloaded or executed either registered checkpoint during M3.

## Next executable task

Begin M5 by defining a bounded, fake-adapter local service contract around the
stable M3 inference and M4 capability/report boundaries. Start with strict
request/result/error and readiness schemas before adding any HTTP framework.
Do not download or execute model weights, bind publicly, or add application or
White Hmong language behavior without separate authorization.
