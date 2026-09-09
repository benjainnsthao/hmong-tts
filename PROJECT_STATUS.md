# Project status

Last updated: 2026-09-09

## Current milestone

- Project: audited pretrained multi-language TTS inference, benchmarking, and
  local-deployment workbench.
- Milestone: **M6 reproduction and portfolio evidence — complete**.
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

## M5 deliverables

- Frozen, extra-forbid service configuration and health, readiness, queue,
  model, synthesis, success, and sanitized-failure contracts.
- FastAPI application factory with lifespan-owned registry, one lazy
  `MmsVitsAdapter`, one M3 `InferenceExecutor`, and one bounded coordinator.
- `GET /health`, `GET /ready`, `GET /v1/models`, and
  `POST /v1/synthesize`; no normalization endpoint.
- One bounded FIFO pending queue, exactly one active inference operation,
  deterministic full/closed/expiry states, and non-preemptive in-flight
  shutdown.
- Registry-owned prompt provenance and service-owned root-relative output
  names; callers cannot supply paths, repositories, revisions, provider
  settings, or identity metadata.
- Sanitized validation and runtime errors with stable HTTP mappings and no raw
  prompt, backend exception, client address, or absolute path.
- Loopback-literal host validation, one Uvicorn worker, no CORS, no access log,
  no request/client logging, no public deployment setting, and an explicit
  model-access acknowledgement gate.
- `tts-workbench-serve` metadata-only `schema`, `validate-config`, and
  `openapi` operations, bringing the active total to eight commands.
- FastAPI 0.136.3, Starlette 1.0.0, Uvicorn 0.46.0, and test-only HTTPX
  0.28.1, all pinned and audited for Python 3.12 and permissive code licenses.
- Test fakes remain outside the production package; no production fake-model
  mode exists.

## M5 validation

- Frozen lock and frozen offline core synchronization: PASS.
- Formatting, Ruff, and strict source MyPy: PASS.
- Active configuration, registry metadata-only listing, privacy/artifact scan,
  package import, OpenAPI, and eight-command help gates: PASS.
- Complete synthetic suite and aggregate branch-aware coverage: PASS; see
  `reports/validation/m5_service_validation.md`.
- Focused service branch coverage: PASS; application/error mapping,
  coordinator, contracts, CLI, and in-process ASGI tests exceed the M5 gate.
- Full pre-commit, release-package inspection, tracked-audio/weight/cache,
  old-identity, historical-evidence, deferred-NV, and Git whitespace checks:
  PASS.
- No checkpoint, optional ML runtime, model-host access, persistent public
  server, real audio, external/native-language content, CORS, UI, M6
  demonstration, or M7 release decision was used.

## M6 deliverables

- Distribution version 0.5.0 and a dedicated locked CUDA benchmark config.
- Fresh clean Python 3.12 core synchronization online and offline without the
  MMS extra or heavyweight optional imports.
- Separate frozen `mms` environment with PyTorch 2.12.0+cu130, Transformers
  5.13.1, safetensors 0.8.0, Accelerate 1.14.0, and SciPy 1.18.0.
- Sanitized WSL/Linux x86-64, dependency, driver-visibility, CUDA, RTX 4070,
  memory, and dtype evidence.
- Refreshed primary-source dependency and exact-revision checkpoint audit.
- Externally retained Vietnamese prompt from an official National Assembly
  legal document, registered provenance reference, public-domain basis, and
  SHA-256 only in Git; no raw prompt text is committed.
- Explicit model-access acknowledgement on direct MMS execution as well as
  benchmark and service execution.
- Successful real CUDA inference for both exact registered checkpoints with
  atomic WAV/manifest publication, reopen/checksum/identity validation, and
  explicit adapter unload.
- Unchanged structural QC thresholds and bounded one-warmup/three-measurement
  benchmarks for both demonstrations, including observable CPU/CUDA memory.
- Real one-worker loopback service demonstration covering health, readiness,
  model metadata, both models, sanitized rejection, no prompt/access logging,
  shutdown, and no persistent listener.
- Reproducible operator instructions, sanitized validation evidence, and a
  concise portfolio-facing engineering summary.

## M6 validation

- Repository synchronization, M5 ancestry, protected refs, and clean-start
  checks: PASS.
- Frozen lock, online/offline clean core environments, package install, lazy
  imports, configurations, registry metadata, privacy, synthetic coverage,
  focused service coverage, in-process ASGI, pre-commit, help/metadata paths,
  old-identity absence, wheel build/inventory, and package install: PASS.
- Optional MMS lock reproduction and CUDA capability gates: PASS on an RTX
  4070 under WSL2 without driver or kernel modification.
- Exact English and Vietnamese checkpoint resolution, CUDA inference,
  WAV/manifest integrity, structural QC, and bounded benchmarks: PASS.
- Real loopback service and clean shutdown: PASS.
- Tracked artifact, prompt/privacy, historical-evidence, deferred-NV, active
  scope, and whitespace scans: PASS.
- Detailed results: `reports/validation/m6_reproduction_validation.md`.

M6 is engineering evidence, not language-quality evidence or release approval.

## Preserved historical work

The completed White Hmong single-speaker Phase 0 validation remains unchanged
in `reports/validation/`. Recording, consent, private-data, training, and native
human-evaluation plans are historical material indexed in
`docs/history/white_hmong_single_speaker/`.

The unresolved native-validation register remains active only as deferred
future-work evidence in `docs/deferred/white_hmong_native_validation.md`.

## Explicitly not started

- M7 final risk disposition or release decision.
- White Hmong text handling, prompts, normalization, adaptation, or evaluation.
- Recording, private speaker data, consent execution, or training.

## Open risks and blockers

The authoritative register is
[`docs/release_risk_register.md`](docs/release_risk_register.md). It tracks:

- public code-license and release-mode decisions;
- CC BY-NC checkpoint use/redistribution and upstream provenance;
- M7 re-audit of the independently sourced Vietnamese prompt;
- M7 final audit of real-checkpoint/intended-hardware and portability evidence;
- cross-device reproducibility limitations;
- QC-versus-language-quality claim boundaries;
- final M7 audit of the mitigated M5 service controls;
- removal of the legacy artifact-root variable;
- dependency/model-host drift and final supply-chain review;
- release artifact/report privacy; and
- the explicitly deferred White Hmong/community-validation boundary **[NV]**.

M6 provides runtime and reproduction evidence and mitigates the corresponding
risks pending M7 final audit. M7 is the final risk-disposition and
release-decision milestone. A public reusable release remains blocked until
its release-blocking items are closed.

## Next executable task

Begin M7 from the completed M6 release-candidate evidence. Re-audit and
disposition every release risk, obtain the required human code-license/release
decisions, and select a release disposition only in that milestone. Preserve
the deferred White Hmong boundary and NV-001 through NV-008.
