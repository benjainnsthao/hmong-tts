# Audited TTS workbench implementation roadmap

Status: approved direction; milestone M3 complete

## Purpose

Build an audited, reusable TTS platform that demonstrates the inference,
evaluation, benchmarking, and local-deployment components needed by a possible
future community-validated Hmong language-learning application.

Initial releases use properly licensed public non-Hmong checkpoints only to
validate the platform. They do not claim White Hmong support, pronunciation
accuracy, linguistic correctness, or readiness for use in a Hmong learning
application.

White Hmong adaptation and NV-001 through NV-008 remain deferred **[NV]**.

## Operating boundaries

- No recording, private speaker data, consent execution, voice cloning,
  adaptation, fine-tuning, or training.
- No White Hmong normalization rules, prompts, inference demonstrations, or
  capability claims.
- Use only audited public checkpoints, properly sourced public prompts, and
  project-authored synthetic fixtures.
- Pin model weights to immutable revisions.
- Keep weights, caches, generated audio, and benchmark artifacts outside Git.
- Do not redistribute third-party model weights.
- Do not treat runtime success or waveform health as evidence of pronunciation
  or language quality.
- Keep ordinary CI independent of network access, model weights, PyTorch, CUDA,
  and native-language review.
- Require separate authorization before model download, public deployment, or a
  future Hmong adaptation phase.

## Delivery strategy

Each milestone should be independently reviewable and should end with a clean
commit, passing CI, updated status, and explicit limitations. Prefer one branch
and pull request per milestone after the current rescope branch is reviewed.

Recommended sequence:

```text
M1 registry
  -> M2 identity and artifact namespace
  -> M3 inference adapter and run manifest
  -> M4 waveform QC, benchmarking, and environment capabilities
  -> M5 bounded local inference service
  -> M6 reproduction and portfolio evidence
  -> deferred community-validated Hmong phase [NV]
```

Do not begin the local service before the inference and benchmark contracts are
stable.

## Milestone M1 — audited model registry

Status: **complete**

Delivered:

- strict registry schema version 1;
- immutable English and Vietnamese MMS checkpoint identities;
- required model, language-tag, architecture, license, use, redistribution,
  prompt-reference, quality-status, and provenance fields;
- fail-closed rejection of mutable revisions, duplicate identities, unknown
  licenses, unapproved use, missing provenance, extra capability fields, and
  positive language-quality claims;
- metadata-only registry validation and listing commands;
- registry-backed MMS smoke model selection; and
- comprehensive synthetic tests without weight downloads.

The active registry is `configs/models/registry.yaml`. Every current entry uses
`language_quality_status: not_evaluated`.

## Milestone M2 — active identity and artifact namespace

Goal: remove misleading legacy names before the code surface grows.

Estimated effort: 3–5 focused hours.

Status: **complete**

### Delivered

- The active Python package is `tts_workbench`.
- The distribution is `audited-tts-workbench` version 0.2.0.
- Active commands use the `tts-workbench-*` namespace.
- Neutral repository detection requires `pyproject.toml` and
  `configs/models/registry.yaml`.
- `TTS_WORKBENCH_ARTIFACT_ROOT` is canonical.
- The legacy artifact-root variable is accepted only for one migration window
  and always emits an explicit warning.
- Imports, scripts, CI, tests, and active documentation use the neutral
  namespace.
- Historical paths and terminology remain unchanged inside the archive and
  validation evidence.

### Acceptance criteria

- No active package, CLI, configuration, or root-detection contract implies
  current Hmong TTS capability.
- The external artifact boundary still rejects relative paths, repository-local
  roots, symlinks or escapes covered by the existing policy.
- Registry, configuration, privacy, lint, typing, and all synthetic tests pass.
- Historical validation reports and the preservation branch remain unchanged.
- No model or optional inference dependency is downloaded.

Validation passed with a frozen lock, offline frozen core sync, formatting,
lint, strict typing, active configuration and registry checks, privacy/artifact
scanning, 68 synthetic tests, 61% branch-aware aggregate coverage, full
pre-commit, package/CLI smoke tests, and an obsolete-identifier audit.

## Milestone M3 — reusable inference adapter and run manifest

Goal: turn the MMS smoke implementation into a provider-neutral, testable
inference engine.

Estimated effort: 10–16 focused hours.

Status: **complete**

### Delivered

- Typed, frozen, extra-forbid request, result, adapter identity/state, waveform,
  and success-manifest contracts use schema version 1.
- The provider-neutral `TTSAdapter` protocol exposes only identity, lifecycle,
  load, synthesize, and unload.
- `MmsVitsAdapter` selects repository/revision only through the schema-version-1
  audited registry and owns at most one loaded model/backend.
- PyTorch and Transformers imports occur only inside the optional real backend's
  explicit load method.
- Explicit `cpu`, `cuda`, and `auto` requests, seed, dtype, MMS/VITS generation
  settings, and optional backend versions are preserved.
- Registry lookup, prompt-provenance matching, and artifact validation happen
  before backend loading.
- The existing MMS smoke command now consumes the adapter and execution
  contracts and writes a WAV plus manifest.
- WAV and manifest publication is atomic, collision-rejecting, and
  rollback-tested; the manifest is published last as the commit marker.
- Raw prompt text, client/machine identity, and absolute paths are excluded from
  returned results, logs, and manifests.
- Ordinary tests use test-only fake adapters/backends and temporary synthetic
  WAVs.

### Run-manifest contract

Every successful synthesis should record:

- schema version and unique run ID;
- registry model ID, provider, repository, and immutable revision;
- weight license, approved use, redistribution status, and language-quality
  status;
- prompt-set reference and prompt-content hash;
- runtime, Python, PyTorch, and Transformers versions when installed;
- device, dtype, seed, and generation parameters;
- start time, model-load time, and synthesis duration;
- sample rate, sample count, channel count, and output duration;
- WAV checksum and artifact-root-relative path; and
- pass/fail status plus a structured failure category.

The manifest does not copy prompt content.

### Acceptance criteria

- Both registered model IDs route through the same adapter contract.
- Unknown, unapproved, or registry-invalid models fail before model loading.
- Outputs cannot escape the artifact root.
- A failed run leaves no partial WAV or success manifest.
- Same-environment repeatability is characterized without promising
  cross-device bit identity.
- Unit tests require no network, GPU, PyTorch, Transformers, or weights.
- Optional real-checkpoint tests remain explicitly marked and disabled by
  default.

Validation passed with a frozen lock, offline frozen core sync, formatting,
Ruff, strict MyPy, active configuration and registry commands, privacy scanning,
123 synthetic tests, 74% branch-aware aggregate coverage, full pre-commit,
package/lazy-import checks, five CLI help checks, and old-identity/preservation
audits. No real-checkpoint automated test exists; the optional smoke command
still requires separately authorized dependencies, weights, and execution.

## Milestone M4 — waveform QC, benchmarking, and environment capabilities

Goal: demonstrate reproducible ML-systems evaluation without making linguistic
quality claims.

Estimated effort: 14–21 focused hours.

### Waveform QC

Add objective checks for:

- WAV readability and non-empty output;
- channel count, sample rate, sample width, and duration;
- finite samples;
- peak amplitude and clipping ratio;
- RMS level and DC offset;
- leading, trailing, and total near-silence ratio; and
- empty, corrupt, or nearly silent failure cases.

Thresholds must be identified as engineering sanity checks rather than
universal TTS-quality standards.

### Benchmarking

Measure and report:

- cold model-load time;
- warm synthesis latency;
- real-time factor;
- median and p95 timing over repeated runs;
- success and structured failure counts;
- CPU memory and CUDA memory where observable; and
- complete environment metadata.

Benchmark English and Vietnamese separately within their documented checkpoint
contexts. Do not produce cross-language pronunciation or quality rankings.

### Environment refactor

Replace the retained training-oriented readiness result with:

- `core_ready`;
- `cpu_inference_ready`;
- `cuda_inference_ready`;
- available device names and memory;
- available/supported dtype information;
- optional dependency status;
- FFmpeg status; and
- artifact-root validity.

The RTX 4070 result remains historical evidence, not a universal requirement.

### Testing and real-model gate

- Generate synthetic good and deliberately faulty waveforms during tests.
- Keep audio fixtures temporary and outside Git.
- Run all QC and report-schema tests without model weights.
- Require separate authorization before downloading and executing the two
  registered MMS checkpoints.
- For Vietnamese, require a public prompt with independently reviewed
  license/provenance before inference.

### Acceptance criteria

- Every seeded synthetic defect is detected by its intended QC rule.
- Benchmark reports are schema-validated and contain no absolute private path or
  raw prompt text.
- Cold and warm timing are reported separately.
- Runtime and waveform results are labeled as non-linguistic evidence.
- Metadata reports may enter Git; generated audio and weights may not.

## Milestone M5 — bounded local inference service

Goal: expose the stable adapter through a local API suitable for a future
application client.

Estimated effort: 8–12 focused hours.

### Endpoints

- `GET /health`
- `GET /ready`
- `GET /v1/models`
- `POST /v1/synthesize`

Do not add a normalization endpoint while no validated language normalizer
exists.

### Controls

- Bind to localhost by default.
- Keep public deployment disabled.
- Use registry-approved models only.
- Enforce maximum input length, request timeout, and one bounded inference
  queue.
- Keep one explicit model-instance owner.
- Do not log request text or client IP addresses.
- Return or reference a run manifest for every successful result.
- Report `language_quality_status: not_evaluated` in model/API metadata.
- Provide a clear synthetic-audio and limitations notice.

### Acceptance criteria

- Fake-adapter API tests require no weight download.
- Queue overflow, timeout, invalid model, invalid input, and inference failure
  return stable error contracts.
- Health and readiness distinguish process health from model readiness.
- The service cannot enable a public bind through an undocumented setting.
- No endpoint claims White Hmong support or implements White Hmong
  normalization **[NV]**.

## Milestone M6 — reproduction and portfolio evidence

Goal: produce a credible, reviewable ML-engineering release candidate.

Estimated effort: 6–10 focused hours, excluding downloads and hardware runtime.

### Deliverables

- Fresh-clone core reproduction instructions.
- Reproducible inference and benchmark commands.
- Two audited MMS checkpoint demonstrations on authorized local hardware.
- Metadata-only benchmark and QC reports.
- CLI and local API documentation.
- Updated architecture, registry, threat model, and limitations documents.
- An explicit inventory of code, checkpoint, prompt, generated-output, and
  report licenses/status.
- A release checklist confirming that no weights or generated audio entered Git.

### Acceptance criteria

- A fresh core checkout passes without model downloads.
- An explicitly authorized inference environment reproduces the documented
  model revisions and manifests.
- Published reports clearly separate runtime/QC findings from linguistic
  quality.
- No third-party weights are bundled or redistributed.
- The owner makes an explicit project code-license decision before presenting
  the repository as a reusable public software release.
- White Hmong capability remains deferred **[NV]**.

## Future bridge to a Hmong learning application

The workbench should preserve extension points for:

- explicit language and variety metadata;
- a future community-reviewed language profile;
- native-validation evidence references;
- licensed vocabulary, sentence, and story prompt packages;
- offline/local operation for families or classrooms;
- application features such as vocabulary playback, story reading, and
  listening exercises; and
- capability states such as `runtime_validated`,
  `language_quality_not_evaluated`, and `community_validated`.

These extension points do not establish current support. A future Hmong phase
requires separate authorization, an appropriate checkpoint or adaptation/data
path, community participation, and resolution of the applicable NV-001 through
NV-008 decisions **[NV]**.

Do not send White Hmong text through the registered English or Vietnamese
models and present the output as a prototype Hmong voice.

## Remaining cross-cutting risks

- The repository currently grants no public code license.
- Registered MMS weights are CC BY-NC 4.0 and non-commercial.
- Registry metadata does not replace legal review or guarantee complete
  upstream training-data clearance.
- Provider APIs, runtime libraries, and model-host metadata can change.
- Deterministic seeds do not guarantee byte-identical output across devices or
  runtime versions.
- Objective audio checks can miss linguistic or perceptual failures.
- A local service still needs lifecycle, concurrency, resource-exhaustion, and
  logging controls.
- Future cultural-preservation value depends on community governance and
  language evidence, not infrastructure alone.

## Next executable task

Begin M4 with M3's committed `RunManifest` and `WaveformResult` boundaries:
define non-linguistic waveform QC report schemas and synthetic defect fixtures,
then add benchmark/environment capability contracts. Do not download or execute
weights without separate authorization, and do not begin FastAPI or application
work during M4.
