# Decision records

## D-0001 — External private-data root

- Date: 2026-07-14
- Decision: all real audio, identity/consent records, private text/ratings,
  checkpoints, and generated WAV files must live below an absolute external
  `HMONG_TTS_DATA_ROOT`. Repository-local data roots and symlinks are rejected.
- Alternatives: an ignored repository `data/` directory; Git LFS; a public
  artifact store.
- Evidence: authoritative plan privacy rules and the inability of `.gitignore`
  alone to protect force-adds, history, hosted trackers, or identity mappings.
- Native-validation status: not applicable.
- Consequences: scripts fail closed without a valid root; synthetic fixtures
  are the only test data; users must provision encrypted external storage.

## D-0002 — Pinned MMS candidates remain provisional

- Date: 2026-07-14
- Decision: retain the plan’s `facebook/mms-tts-vie` primary candidate and
  `facebook/mms-tts-eng` control at immutable revisions recorded in the license
  matrix. Do not claim transfer quality; choose only through the blind pilot.
- Alternatives: choose Vietnamese without a control; choose Piper/F5/XTTS now;
  train from scratch.
- Evidence: official MMS cards expose compact 36.3M-parameter VITS inference
  checkpoints, the recipe supports generator/discriminator fine-tuning, and the
  collection has no listed `mww`, `hnj`, or `hmn` TTS entry as audited.
- Native-validation status: **[NV]** required for the eventual A/B judgment and
  all language behavior.
- Consequences: local research remains non-commercial under CC BY-NC 4.0;
  distribution is not assumed; both initializations use the identical pilot.

## D-0003 — Reproducible core versus heavyweight MMS environment

- Date: 2026-07-14
- Decision: pin Python 3.12 and `uv` 0.11.x. Keep governance/test dependencies
  in the default lock and the large x86-64 Linux MMS stack in an explicit
  optional extra.
- Alternatives: use the host Python 3.13; unpinned `pip install`; install GPU
  packages in every CI job.
- Evidence: current host is Windows ARM64/Python 3.13, WSL is ARM64/Python 3.12,
  and current official PyTorch Windows guidance lists Python 3.9–3.12 while the
  target CUDA workflow is Linux/WSL. GPU/model packages are large and not needed
  to prove Phase 0 privacy/config gates.
- Native-validation status: not applicable.
- Consequences: ordinary tests are portable; MMS installation is explicit and
  platform-gated; training requires an x86-64 CUDA-visible machine.

## D-0004 — No code-license grant before owner choice

- Date: 2026-07-14
- Decision: use the default all-rights-reserved state rather than silently
  selecting an open-source license.
- Alternatives: MIT, Apache-2.0, GPL-3.0, or another reviewed license.
- Evidence: the plan requires a license matrix but does not authorize a specific
  project code license; the operating rules reserve material licensing changes
  for the owner.
- Native-validation status: not applicable.
- Consequences: local implementation can continue; public redistribution is
  blocked until the owner explicitly selects a license.

## D-0005 — No language rules in Phase 0

- Date: 2026-07-14
- Decision: typed config records the plan’s character/lowercase baseline but
  marks normalization blocked. No White Hmong characters, tone mappings,
  number/abbreviation readings, variants, or prompts are encoded yet.
- Alternatives: infer rules from general linguistic references or another
  language’s tokenizer.
- Evidence: authoritative plan requires native approval and warns that other
  normalizers may remove meaningful final letters.
- Native-validation status: **[NV]** open items NV-001 through NV-008.
- Consequences: Phase 1 schema work may proceed, but prompts, golden cases, and
  production normalization cannot pass until native review is recorded.

## D-0006 — Rescope to an audited public-checkpoint TTS workbench

- Date: 2026-07-28
- Decision: preserve the completed single-speaker White Hmong TTS Phase 0 and
  rescope active development to inference, evaluation, benchmarking, and local
  deployment infrastructure using properly licensed public non-Hmong
  checkpoints. The original repository state is preserved on local branch
  `archive/white-hmong-single-speaker-tts-v0.1` at commit
  `fd1756485b1e1b75fd1efee5e37519fa8e255415`.
- Alternatives: continue immediately into consent/recording/training; reduce the
  repository to a provenance audit; abandon the prior work.
- Evidence: recording, private-data coordination, training, and native
  listening evaluation exceed the revised solo-development constraints, while
  the existing MMS inference, configuration, environment, boundary, privacy,
  CI, and test work directly supports an inference workbench.
- Native-validation status: **[NV]** NV-001 through NV-008 remain deferred and
  unresolved. The workbench makes no White Hmong support or correctness claim.
- Consequences: historical recording/training material is non-operative;
  generated audio, weights, and caches remain external; a future Hmong learning
  application requires a separately authorized, community-validated phase.

## D-0007 — Fail-closed audited model registry

- Date: 2026-07-28
- Decision: replace hardcoded eligible MMS checkpoint references with schema
  version 1 of a metadata-only registry. Active entries require immutable
  40-character revisions, primary-source provenance, an audited license,
  `local_noncommercial_inference`, `weights_not_redistributed`, and
  `language_quality_status: not_evaluated`.
- Alternatives: keep a Python dictionary; allow mutable tags or branches; infer
  license/capability status from a provider name; download first and audit later.
- Evidence: the Phase 0 license matrix already treats immutable identity,
  license, lineage, and use scope as independent gates. A strict registry makes
  those gates executable without downloading weights.
- Native-validation status: not applicable to registry mechanics. Registered
  English and Vietnamese language tags are provider metadata, not quality
  findings and not evidence about White Hmong.
- Consequences: missing provenance, duplicate identities, unapproved use,
  unknown license placeholders, and positive language-quality claims fail
  validation. New licenses and use categories require an explicit schema and
  audit decision.

## D-0008 — Neutral active identity with a bounded artifact-root migration

- Date: 2026-07-28
- Decision: rename the active `hmong_tts` package to `tts_workbench`, the
  distribution to `audited-tts-workbench` version 0.2.0, and every active CLI
  to the `tts-workbench-*` namespace. Make
  `TTS_WORKBENCH_ARTIFACT_ROOT` canonical and rename the active boundary API
  from `data.paths`/`DataBoundaryError` to
  `artifacts.paths`/`ArtifactBoundaryError`.
- Compatibility: `HMONG_TTS_DATA_ROOT` is accepted for the 0.2 migration window
  only. Legacy-only configuration warns; matching canonical/legacy values use
  the canonical value and warn; conflicting resolved values fail closed. No
  active Python import or CLI compatibility alias is provided.
- Repository identity: active root detection requires both `pyproject.toml` and
  `configs/models/registry.yaml`, not the archived White Hmong project-plan
  pointer.
- Alternatives: retain the misleading active namespace; provide permanent
  import and CLI aliases; remove the artifact-root legacy variable without a
  migration window; rewrite all historical examples.
- Evidence: inference, benchmarking, and service surfaces will multiply active
  names, so the breaking migration is least costly before M3. A short
  environment-variable bridge protects existing external artifact locations
  without preserving a misleading code API.
- Historical policy: archived documents and validation reports retain their
  original terminology so they remain accurate snapshots of the work that
  produced them. They are not active instructions.
- Native-validation status: **[NV]** unchanged. Neutral naming is an
  infrastructure correction and does not establish White Hmong support,
  pronunciation accuracy, linguistic correctness, or learning-application
  readiness.
- Consequences: active users must import `tts_workbench` and use the new CLI
  names. The legacy artifact-root variable must be removed in a later breaking
  release after the warning window.

## D-0009 — Provider-neutral inference and manifest commit marker

- Date: 2026-07-28
- Decision: define strict schema-version-1 inference contracts and a
  provider-neutral `TTSAdapter` lifecycle. Implement MMS/VITS behind that
  boundary, with PyTorch and Transformers imported only by the optional backend
  during explicit load.
- Ownership: one adapter instance owns at most one loaded backend/model.
  Switching model or requested device unloads old state first. Repository and
  immutable revision come only from the audited registry.
- Artifact decision: publish the validated WAV first and its strict success
  manifest last. The manifest is the commit marker; a failed validation,
  serialization, or replacement removes temporary files and any WAV owned by
  the failed transaction.
- Privacy decision: manifests retain a SHA-256 prompt hash and
  artifact-root-relative paths, but exclude raw prompts, absolute paths, machine
  identity, addresses, credentials, and private identifiers. This supports
  provenance without turning manifests or logs into content/location records.
- Test strategy: ordinary tests use dependency-injected synthetic fake backends
  and pytest temporary WAVs. This exercises registry routing, lifecycle,
  failures, device/seed/settings forwarding, WAV structure, checksums, and
  rollback without network, weights, PyTorch, Transformers, CUDA, real audio,
  or native-language content.
- Alternatives: retain a monolithic Transformers smoke function; expose
  provider objects to callers; write the manifest before audio; store prompt
  text and absolute paths for convenience; use a real checkpoint in CI.
- Native-validation status: **[NV]** unchanged. Infrastructure execution and
  structural WAV validity provide no White Hmong capability, pronunciation,
  naturalness, linguistic-correctness, or learning-application evidence.
- Consequences: M4 can add waveform QC and benchmarking against a stable
  manifest boundary. M5 service work remains blocked until those library
  contracts are reviewed.

## D-0010 — M4 engineering evidence, deterministic benchmarks, and readiness

- Date: 2026-07-28
- Evidence scope: every QC rule and QC/benchmark report is explicitly
  `engineering_sanity_check`. Structural validity and configured QC pass/fail
  are not linguistic, pronunciation, intelligibility, naturalness, perceptual,
  or learning-application evidence.
- Threshold decision: use strict schema-version-1 configuration and embed the
  complete effective thresholds in every report. PCM16 is normalized by signed
  sample divided by 32768. Clipping and near-silence sample membership are
  inclusive; configured maxima pass at `<=` and minima pass at `>=`.
- Threshold alternatives: hardcode values, omit thresholds from results, or
  describe defaults as universal TTS quality limits. These were rejected
  because results must remain reproducible and the numeric defaults have no
  universal linguistic or perceptual authority.
- Timing decision: measure `adapter.load` alone as cold load and each
  `adapter.synthesize` call alone as warm synthesis. Execute configured warmups
  but exclude them from aggregates. Compute p95 by deterministic nearest rank,
  `sorted[ceil(0.95*N)-1]`; use successful measured observations only.
- Test strategy: injected clocks, adapters, waveforms, registry, environment
  collectors, memory observations, and report failures validate benchmark/QC
  behavior without sleeping, network access, weights, optional ML libraries,
  real audio, or production fake modes.
- Resource decision: collect point-in-time CPU peak resident memory through
  standard-library facilities where available and CUDA allocation/reservation
  only from an already-imported runtime. Report missing values as
  `unavailable`, never zero; collect no continuous telemetry.
- Readiness decision: replace active RTX/training-oriented readiness with
  independent `core_ready`, `cpu_inference_ready`, and
  `cuda_inference_ready`. CUDA and a particular GPU name are not core
  requirements. Retain `--require-training` only as a warning-emitting
  deprecated alias for CUDA-inference readiness; preserve historical hardware
  reports unchanged.
- Privacy decision: QC and benchmark reports use only artifact-root-relative
  paths and SHA-256 prompt provenance. They exclude raw prompts, absolute
  roots/cache paths, users, hosts, addresses, credentials, environment values,
  private identifiers, and linguistic conclusions. JSON reports use
  collision-rejecting atomic external-artifact transactions.
- Alternatives: place QC in the M3 commit transaction, use a real checkpoint
  for implementation tests, use interpolation-based percentiles, require GPU
  telemetry, or preserve RTX 4070 as a universal gate. These were rejected to
  preserve M3 compatibility, offline determinism, clear timing semantics,
  optional dependencies, and generalized capability reporting.
- Native-validation status: **[NV]** NV-001 through NV-008 remain deferred and
  unchanged. M4 contains no White Hmong prompt, text rule, tag, normalization,
  pronunciation rule, or capability finding.
- Consequences: M4 provides reproducible systems-level contracts for a future
  bounded local service. It establishes no Hmong capability and provides no
  real-model performance result. M5 may begin at these stable interfaces but
  must not treat QC or benchmark completion as language-quality evidence.

## D-0011 — Separate release-candidate evidence from final risk disposition

- Date: 2026-07-28
- Decision: add M7 as the final release gate and make
  `docs/release_risk_register.md` its authoritative input. M5 builds the bounded
  service and M6 produces reproduction/portfolio evidence; neither alone may
  declare a validated public release.
- Disposition rule: every risk must be `closed`, or explicitly `accepted` or
  `deferred` by a named human owner with scope, rationale, user-facing
  limitation, and review date. Open release blockers force `preview` or
  `do_not_release`.
- Human gates: the owner must decide the code license/release mode, authorize
  real checkpoint/hardware execution, approve public prompt provenance, and
  sign the final release decision. Engineering documentation cannot substitute
  for those decisions.
- Alternatives: treat M6 as automatically releasable; leave risks as an
  unowned narrative list; require every limitation to be technically
  eliminated; fold future White Hmong validation into the infrastructure
  release.
- Evidence: M4 closed its implementation gates while code licensing, real-model
  execution, Vietnamese prompt provenance, stable compatibility cleanup,
  service controls, supply-chain freshness, and release claims remain distinct
  risks with different owners and closure evidence.
- Native-validation status: **[NV]** unchanged. REL-LANG-001 is deferred from
  the infrastructure release; M7 must preserve the no-capability claim and
  cannot close NV-001 through NV-008 without a separately authorized
  community/native-validation phase.
- Consequences: the project has a bounded final milestone that can produce
  `release`, `preview`, or `do_not_release`. A public release cannot silently
  inherit unresolved risks from M5/M6.
