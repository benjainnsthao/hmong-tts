# Release risk register

This register is the authoritative input to Milestone M7. It separates risks
that engineering can close from decisions or evidence that require the owner,
authorized hardware, public-source review, or future community participation.

M6 completion does not close these risks. Until M7 passes, the repository is an
engineering release candidate rather than a validated public release.

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

## Current risks

### REL-LIC-001 — project code license

- Current status: `open`; release blocker for a reusable public release.
- Risk: the repository grants no public code license.
- Required closure: the owner selects a reviewed code license and updates the
  repository/license matrix, or records `private/local-only` and does not
  present the project as reusable public software.
- Evidence: exact license text, owner decision date, covered files, third-party
  notices, and release-mode statement.
- Human gate: owner/legal decision.

### REL-LIC-002 — checkpoint use and redistribution

- Current status: `mitigated`; pending M7 final audit.
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

### REL-PROMPT-001 — Vietnamese prompt provenance

- Current status: `mitigated`; pending M7 final audit.
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

### REL-RUNTIME-001 — real checkpoint and intended-hardware evidence

- Current status: `mitigated`; pending M7 final audit.
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

### REL-PORT-001 — portability and resource observability

- Current status: `mitigated`; pending M7 final audit.
- Risk: CPU/CUDA readiness and memory availability vary by OS, runtime build,
  driver, and device; unavailable measurements do not prove zero usage.
- Required closure: validate core operation on the supported CPU-only
  environment and inference on intended CUDA hardware; document unavailable
  resource fields and platform exclusions.
- Evidence: sanitized capability matrix, frozen dependency versions, target
  hardware report, separate clean core/MMS environments, actual CPU/CUDA memory
  availability, and documented support boundaries.
- Residual limitation: no cross-device timing or waveform equivalence claim.

### REL-REPRO-001 — deterministic settings versus cross-device equivalence

- Current status: `mitigated`; pending M7 final audit.
- Risk: fixed seeds/settings improve same-environment reproduction but do not
  guarantee byte-identical waveforms or timing across devices/runtime versions.
- Required closure: record exact model, revision, adapter, dependency, device,
  dtype, seed, and settings for every release demonstration; reproduce within
  the same environment; retain the cross-device limitation.
- Evidence: paired manifests/reports and a documented comparison method.
- Permitted disposition: `accepted` as an explicit release limitation.

### REL-QC-001 — engineering QC is not language quality

- Current status: `mitigated`; pending M7 final audit.
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

### REL-SERVICE-001 — bounded local-service security and exhaustion

- Current status: `mitigated` by M5, pending the final M7 release audit.
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

### REL-COMPAT-001 — legacy artifact-root variable

- Current status: `open` for a stable public release.
- Risk: `HMONG_TTS_DATA_ROOT` remains a warning-based 0.2 migration bridge and
  creates long-term naming/configuration ambiguity.
- Required closure: remove the legacy variable in a documented breaking
  release and test canonical-only behavior.
- Permitted temporary disposition: an owner-approved preview may retain it only
  with a versioned removal date and visible warning.
- Evidence: migration notes, absence tests, configuration docs, and changelog.

### REL-SUPPLY-001 — upstream and dependency drift

- Current status: `mitigated`; pending M7 final audit.
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

### REL-PRIV-001 — release artifact and report privacy

- Current status: `mitigated`; pending M7 final audit.
- Risk: weights, generated audio, prompts, caches, credentials, private paths,
  or machine/client identifiers could enter Git or release packages.
- Required closure: run privacy, tracked-artifact, package-content, report
  schema, absolute-path, credential, and history scans at the exact release
  commit.
- Evidence: M6 privacy/tracked-artifact/report/package scans and wheel inventory
  showing no forbidden material; repeat against the exact M7 release commit.

### REL-LANG-001 — no White Hmong capability or community evidence

- Current status: `deferred` from the infrastructure release, pending explicit
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
