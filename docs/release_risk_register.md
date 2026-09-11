# Release risk register

This register is the authoritative input to Milestone M7. It separates risks
that engineering can close from decisions or evidence that require the owner,
authorized hardware, public-source review, or future community participation.

M6 completion does not close these risks. The M7 assessment below retains each
original risk and acceptance criterion and supplies proposed dispositions.
The dated human decision in [m7_owner_approval.json](m7_owner_approval.json)
is authoritative for final status: while its release approval is `pending`,
the corrected candidate has no final approval. Previous approvals remain
preserved for their identified candidate only. Once newly approved,
its explicit risk-disposition mapping adopts the reviewed proposals; release
completion additionally requires exact committed-state validation and push.
The record is a named conversational sign-off, not a cryptographic signature.
No severity or acceptance criterion is reduced to close a risk.

Audit date: 2026-09-10. Decision owner for every item: **benjainnsthao**.
Next review for every item: **2026-12-09**, sooner for a material security,
dependency, licensing, or provenance issue. Owner approval of code licensing
on 2026-09-10 is separate from the pending final release decision.

## Status and disposition rules

- `open`: required evidence or decision is missing.
- `mitigated`: engineering controls exist, but final release evidence is
  incomplete.
- `accepted`: the owner explicitly accepts a bounded residual risk with a
  rationale, affected scope, user-facing limitation, and review date.
- `deferred`: excluded from the release scope by an explicit owner decision,
  with a future trigger and review date.
- `closed`: required evidence and acceptance criteria are satisfied.

Only `closed`, `accepted`, or `deferred` items may enter an M7 release decision.
Release blockers cannot be merely omitted. An accepted or deferred item must
identify the approving human; a commit message alone is not approval.

## Audited risks and unchanged acceptance criteria

### REL-LIC-001 — project code license

- M6 status (historical audit input): `open`; release blocker for a reusable public release.
- Risk: the repository grants no public code license.
- Required closure: the owner selects a reviewed code license and updates the
  repository/license matrix, or records `private/local-only` and does not
  present the project as reusable public software.
- Evidence: exact license text, owner decision date, covered files, third-party
  notices, and release-mode statement.
- Human gate: owner/legal decision.

M7 assessment (2026-09-10):

- Proposed disposition: `closed`; pending explicit final owner approval.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: Covered original project code, original build/test/configuration material, and public candidate notices.
- Evidence: Exact standard Apache-2.0 text, version 1.0.0 metadata, NOTICE, THIRD_PARTY_NOTICES.md, and wheel/sdist inclusion/content review; docs/license_matrix.md.
- Rationale: The owner confirmed authority and commercial reuse on 2026-09-10. Original-code licensing is already approved conversationally; no third-party or historical blanket relicense is asserted.
- User-facing limitation: Apache-2.0 does not license weights, source recordings, raw prompts, or generated audio.

### REL-LIC-002 — checkpoint use and redistribution

- M6 status (historical audit input): `mitigated`; pending M7 final audit.
- Risk: registered MMS weights are CC BY-NC 4.0, non-commercial, and unsuitable
  for a release that implies unrestricted commercial use.
- Existing control: registry permits only local non-commercial inference and
  `weights_not_redistributed`.
- Required closure: re-audit each immutable revision and upstream license at
  release time; keep weights external; state the non-commercial boundary in
  CLI/API/release documentation. Any replacement or commercial model choice is
  a separate owner-approved scope and license decision.
- Evidence: current primary-source URLs/access dates, immutable revisions,
  license matrix, package contents, and tracked-weight scan.

M7 assessment (2026-09-10):

- Proposed disposition: `accepted`; pending explicit final owner approval.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: Only the two registered MMS checkpoints, local non-commercial inference; no weight or audio distribution.
- Evidence: Exact revision cards/API access, cached safetensors hashes matching upstream, CC BY-NC 4.0 terms, package scans; docs/license_matrix.md.
- Rationale: The operational and distribution boundary is verified. Individual training-recording rights remain insufficiently itemized for commercial clearance; accepting this scoped use does not grant those rights.
- User-facing limitation: Model use remains non-commercial. No commercial model/output clearance, weight redistribution, or dataset relicense is supplied.

### REL-PROMPT-001 — Vietnamese prompt provenance

- M6 status (historical audit input): `mitigated`; pending M7 final audit.
- Risk: prompt provenance could be incomplete, mutable, or disclosed with raw
  text/private location.
- M6 control: an unmodified sentence from Article 1 of Vietnam's 2013
  Constitution was sourced from the official National Assembly/Government
  Portal scan. Vietnam IP Law No. 50/2005/QH11 Article 15(2), published by WIPO
  Lex, excludes legal documents and official translations from copyright
  protection. Registry reference and SHA-256 are committed; prompt/source
  material remains external.
- Required closure: M7 re-audits the primary record, source scan, legal basis,
  hash, absence of raw text, and intended release documentation.
- Evidence: `docs/m6_reproduction.md`, `docs/license_matrix.md`, and
  `reports/validation/m6_reproduction_validation.md`.

M7 assessment (2026-09-10):

- Proposed disposition: `closed`; pending explicit final owner approval.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: The retained single approved Vietnamese legal-document sentence for local engineering demonstration.
- Evidence: Official 2013 source PDF matches M6 byte for byte; prompt reference/hash match; current Article 15(2) basis including 2022/2025 amendments; docs/license_matrix.md and external audit/prompt-legal-update.json.
- Rationale: The primary record, unchanged prompt, source attribution, legal basis, and external-only boundary passed before Vietnamese inference. No text substitution was made.
- User-facing limitation: This scoped legal-document basis is not a global license for arbitrary Vietnamese text or generated outputs.

### REL-RUNTIME-001 — real checkpoint and intended-hardware evidence

- M6 status (historical audit input): `mitigated`; pending M7 final audit.
- Risk: runtime evidence can drift from the registered checkpoints, frozen
  environment, or intended hardware.
- M6 control: explicitly authorized execution reproduced the separate locked
  MMS environment and ran inference, QC, bounded benchmarks, and the real
  loopback service for both immutable revisions on requested/resolved CUDA with
  an RTX 4070.
- Required closure: M7 re-audits the exact release commit and retained external
  evidence against the documented environment and registry.
- Evidence: sanitized environment report, run manifests, QC reports, benchmark
  reports, commands, checkpoint revisions, dependency versions, and failure
  resolution record.
- Release rule: without both demonstrations, label the result
  `contract-validated preview`, not a validated runtime release.
- Human gate: final release-scope approval remains M7 work.

M7 assessment (2026-09-10):

- Proposed disposition: `closed`; pending explicit final owner approval.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: Registered mms-eng and mms-vie on the measured RTX 4070/Linux WSL/Python 3.12 environment.
- Evidence: M7 validation report, runtime-source digest, immutable identities, both CUDA runs/repeats/QC/benchmarks, eight WAV/manifest pairs, and two-model real service.
- Rationale: The candidate source/configuration/dependency digest binds measured requested/resolved CUDA/float32 behavior. Exact committed contents are verified again before push.
- User-facing limitation: Two engineering demonstrations do not establish Hmong support, language quality, or another platform/device.

### REL-PORT-001 — portability and resource observability

- M6 status (historical audit input): `mitigated`; pending M7 final audit.
- Risk: CPU/CUDA readiness and memory availability vary by OS, runtime build,
  driver, and device; unavailable measurements do not prove zero usage.
- Required closure: validate core operation on the supported CPU-only
  environment and inference on intended CUDA hardware; document unavailable
  resource fields and platform exclusions.
- Evidence: sanitized capability matrix, frozen dependency versions, target
  hardware report, separate clean core/MMS environments, actual CPU/CUDA memory
  availability, and documented support boundaries.
- Residual limitation: no cross-device timing or waveform equivalence claim.

M7 assessment (2026-09-10):

- Proposed disposition: `accepted`; pending explicit final owner approval.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: Clean CPU-only core; separate locked MMS runtime on this Linux/WSL x86-64 machine.
- Evidence: Sanitized core/CUDA capability reports, two-thread CPU model diagnostics, measured memory availability and environment summary in the M7 report.
- Rationale: Core operation is established independently of optional model execution. CPU/CUDA execution was measured locally; other platforms, drivers, precision modes, and system memory visibility remain unvalidated.
- User-facing limitation: Native Windows, macOS, ARM, other accelerators, and cross-device timing/waveform equivalence are excluded. Unobservable fields remain unavailable.

### REL-REPRO-001 — deterministic settings versus cross-device equivalence

- M6 status (historical audit input): `mitigated`; pending M7 final audit.
- Risk: fixed seeds/settings improve same-environment reproduction but do not
  guarantee byte-identical waveforms or timing across devices/runtime versions.
- Required closure: record exact model, revision, adapter, dependency, device,
  dtype, seed, and settings for every release demonstration; reproduce within
  the same environment; retain the cross-device limitation.
- Evidence: paired manifests/reports and a documented comparison method.
- Permitted disposition: `accepted` as an explicit release limitation.

M7 assessment (2026-09-10):

- Proposed disposition: `accepted`; pending explicit final owner approval.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: Seed/settings/adapter/runtime/model identity in the documented same-environment procedure.
- Evidence: Paired CUDA manifests for both models match identity/settings and WAV checksums; scripts/verify_m7_artifacts.py; external integrity-verification.json.
- Rationale: Identical bytes were observed for these paired runs, not guaranteed for future kernels, devices, dependencies, or process timing. No threshold was weakened to obtain this result.
- User-facing limitation: Fixed seeds and locks do not promise cross-device byte-identical audio or timing; small bounded benchmarks are descriptive samples.

### REL-QC-001 — engineering QC is not language quality

- M6 status (historical audit input): `mitigated`; pending M7 final audit.
- Risk: QC pass or runtime success could be misrepresented as naturalness,
  intelligibility, pronunciation, or linguistic evidence.
- Existing control: every M4 rule/report uses
  `evidence_scope: engineering_sanity_check`.
- Required closure: audit all CLI/API/release text and sample/report labels;
  preserve the limitations notice; add no linguistic acceptance threshold.
- Evidence: unchanged M4 thresholds, two M6 structural reports, claims scan,
  documentation review, and release checklist.
- Residual limitation: objective waveform checks can miss perceptual or
  linguistic failures.

M7 assessment (2026-09-10):

- Proposed disposition: `accepted`; pending explicit final owner approval.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: Engineering waveform sanity and bounded timing evidence only.
- Evidence: M4 config bytes/thresholds preserved, two qc_passing reports, all rules engineering_sanity_check, CLI/API/docs claim review; M7 report.
- Rationale: Engineering checks passed but cannot establish perceptual or linguistic correctness. The owner is asked to accept that limited evidence scope, not a language-quality conclusion.
- User-facing limitation: No MOS, ASR, pronunciation, intelligibility, naturalness, SNR/PESQ/STOI, speaker-similarity, or language ranking is asserted.

### REL-SERVICE-001 — bounded local-service security and exhaustion

- M6 status (historical audit input): `mitigated` by M5, pending the final M7 release audit.
- Implemented control: strict service/configuration contracts, literal
  loopback-only binding, one worker/model owner/active inference operation,
  finite FIFO pending capacity, pre-execution expiry, non-preemptive active
  semantics, input limits, service-owned paths, sanitized errors, disabled
  access/request/client logging, and no CORS/public-deployment mode.
- Evidence: `docs/local_service.md`, `docs/service_threat_model.md`,
  `reports/validation/m5_service_validation.md`, schema/OpenAPI/configuration
  gates, focused branch coverage, in-process ASGI tests, queue/shutdown tests,
  negative binding/privacy/package scans, and the M6 real-backend loopback
  demonstration with clean shutdown.
- Residual limitation: loopback is not authentication; another local process
  may reach the port, long native/model calls are not safely preemptible, and
  repeated local calls can still consume resources.
- M7 closure rule: re-audit the exact release commit and dependency advisories;
  confirm intended release mode and claims. Any public/non-loopback deployment
  requires a new security design and is not approved by M5.

M7 assessment (2026-09-10):

- Proposed disposition: `accepted`; pending explicit final owner approval.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: Existing trusted-client, loopback-only local development service with the two approved model demonstrations.
- Evidence: M7 service re-audit, strict config/OpenAPI/ASGI and FIFO/lifecycle/timeout tests, focused coverage, both real models, safe rejection, unloaded adapter/closed queue/stopped listener; docs/service_threat_model.md.
- Rationale: Controls bound model ownership, admitted pending inference, and pre-execution expiry. Loopback is not authentication; HTTP parsing, total work/output duration, repeated requests, and disk consumption have no complete quota. Very small positive speaking rates can amplify work. Active native calls remain non-preemptible.
- User-facing limitation: Use only trusted local clients, approved prompts, and ordinary generation settings. No public binding, hostile-client resilience, hard active-call deadline, safe forced cancellation, or zero-memory-after-unload promise.

### REL-COMPAT-001 — legacy artifact-root variable

- M6 status (historical audit input): `open` for a stable public release.
- Risk: `HMONG_TTS_DATA_ROOT` remains a warning-based 0.2 migration bridge and
  creates long-term naming/configuration ambiguity.
- Required closure: remove the legacy variable in a documented breaking
  release and test canonical-only behavior.
- Permitted temporary disposition: an owner-approved preview may retain it only
  with a versioned removal date and visible warning.
- Evidence: migration notes, absence tests, configuration docs, and changelog.

M7 assessment (2026-09-10):

- Proposed disposition: `closed`; pending explicit final owner approval.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: Version 1.0.0 canonical external artifact-root configuration.
- Evidence: Production legacy selector/warning removed; canonical-only and legacy-only absence tests; docs/m7_migration.md and CHANGELOG.md.
- Rationale: The owner approved removal for a stable public release. The major version identifies the breaking change while preserving retained data and historical reports.
- User-facing limitation: Existing launchers must set TTS_WORKBENCH_ARTIFACT_ROOT; supplying only HMONG_TTS_DATA_ROOT fails.

### REL-SUPPLY-001 — upstream and dependency drift

- M6 status (historical audit input): `mitigated`; pending M7 final audit.
- Risk: model cards, licenses, model-host availability, APIs, dependencies,
  drivers, and optional runtime behavior can change.
- Existing control: immutable model revisions and frozen Python lock.
- Required closure: refresh primary-source audits/access dates, verify
  checkpoint availability without changing revisions, validate the frozen lock
  offline, review dependency advisories, and record accepted exceptions.
- Evidence: refreshed license matrix/registry audit, lock verification,
  dependency inventory, exact cached checkpoint snapshot identities,
  safetensors selection, and source URLs/access dates.
- Human/external gate: network source review; any material license/model change
  requires owner approval.

M7 assessment (2026-09-10):

- Proposed disposition: `accepted`; pending explicit final owner approval.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: Exact locked Python stack, immutable registered model snapshots, reviewed build/CI/hooks, external NVIDIA components.
- Evidence: 84 current exact PyPI records with no reported remaining advisories/yanks; targeted corrections and full inventory in docs/m7_dependency_audit.md; frozen offline sync; safe tensor hashes and runtime evidence.
- Rationale: Known audited affected versions were corrected or removed. Upstream availability, changing advisories/licenses, transitive hosted-hook environments, native binaries, driver behavior, and incomplete CUDA metapackage license metadata remain bounded external dependencies. No redistribution right is inferred for omitted metadata.
- User-facing limitation: Locks and cached hashes do not ensure future availability or absence of undiscovered vulnerabilities. This audit is dated and is not a commercial-clearance or full binary-source audit.

### REL-PRIV-001 — release artifact and report privacy

- M6 status (historical audit input): `mitigated`; pending M7 final audit.
- Risk: weights, generated audio, prompts, caches, credentials, private paths,
  or machine/client identifiers could enter Git or release packages.
- Required closure: run privacy, tracked-artifact, package-content, report
  schema, absolute-path, credential, and history scans at the exact release
  commit.
- Evidence: M6 privacy/tracked-artifact/report/package scans and wheel inventory
  showing no forbidden material; repeat against the exact M7 release commit.

M7 assessment (2026-09-10):

- Proposed disposition: `accepted`, after the packaging correction passes all applicable gates and the owner approves the corrected candidate. The previous candidate's historical-email acceptance is preserved; the package privacy defect is corrected, not accepted as a residual risk.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: Candidate tracked/staged files, relevant reachable history, public docs/reports, wheel/sdist, and external runtime boundary.
- Evidence: Privacy/credential/absolute-path/private-identifier and artifact scans, 309 original historical blobs, package inventory/notices, report/log prompt checks, preserved M1–M6 and NV records; M7 report and its corrective validation supplement. The failed clean-worktree archive is retained externally, alongside corrected ordinary/worktree builds and regression evidence.
- Rationale: No forbidden material was found in the reviewed candidate files or 309 scanned historical file blobs. Expanded author/committer metadata inspection found one personal-provider email identity across 14 existing commits. The raw address is not reproduced. Its continued visibility in preserved history is not covered by approval of the public owner handle. Weights, caches, prompts/source/OCR, audio, full logs/reports, and environments remain external. Scans are supplemented by file review and schema checks. The proposed mitigation is a verified public GitHub no-reply identity for the new M7 commit, with no history rewriting. Explicit final owner acceptance must cover the already-present historical metadata; no acceptance is assumed.
- User-facing limitation: The existing personal-provider email remains discoverable in prior Git commit metadata if this history is publicly released. It cannot be removed within the no-rewrite authorization. Raw evidence is retained locally through review; do not publish it automatically. Pattern scans cannot prove absence of every possible secret.

Corrective assessment (2026-09-10): the owner approved the historical-email
residual for the prior candidate. Its post-commit worktree sdist nevertheless
included a `.git` pointer containing a private absolute path. That failed
archive was neither committed nor published. After being informed, the owner
requested an active-branch push, then authorized one additional corrective
commit with new candidate approval. Explicit `.git` exclusions apply to both
archive types at any depth. Real-build regression tests cover administrative
directories and pointer files at the root and inside the package. Full
ordinary/worktree package inspection and exact committed-state validation
are required; the defect itself cannot be accepted away. The corrected
candidate remains subject to final owner review and post-approval checks.

### REL-LANG-001 — no White Hmong capability or community evidence

- M6 status (historical audit input): `deferred` from the infrastructure release, pending explicit
  owner confirmation at M7.
- Risk: infrastructure work could be presented as White Hmong support or
  cultural/language validation.
- Required disposition: preserve the no-capability claim and NV-001 through
  NV-008 as unresolved; exclude White Hmong prompts, rules, normalization,
  evaluation, and demonstrations.
- Future closure trigger: a separately authorized community-governed phase
  with appropriate model/data licensing and native-speaker validation.
- Evidence for this release: claims scan, unchanged deferred NV register, and
  explicit release limitations.

M7 assessment (2026-09-10):

- Proposed disposition: `deferred`; pending explicit final owner approval.
- Owner: benjainnsthao. Review: 2026-12-09, or sooner for a material issue.
- Scope: All White Hmong/community-language functionality and validation.
- Evidence: Unchanged docs/deferred/white_hmong_native_validation.md, preserved NV-001 through NV-008, active source and claim review; docs/m7_release_decision.md.
- Rationale: The long-term purpose remains useful speech technology for the Hmong community. Current English/Vietnamese engineering evidence cannot substitute for community participation or native validation.
- User-facing limitation: No Hmong capability or community validation is claimed. Future trigger: separately authorized community-governed work with appropriate licensing and native-speaker validation; no such work starts in M7.

## M7 release decision record

M7 must create a dated record containing:

- exact release commit and artifact inventory;
- `release`, `preview`, or `do_not_release`;
- intended audience and permitted use;
- code/model/prompt/output/report license dispositions;
- each risk's final status, owner, evidence reference, and review date;
- runtime/device scope and unsupported configurations;
- privacy and distribution confirmation;
- explicit non-linguistic and no-White-Hmong-capability statements; and
- signatures/approvals required by the chosen release mode.

If any release blocker remains open, the decision must be `preview` or
`do_not_release`.
