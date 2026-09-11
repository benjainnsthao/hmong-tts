# M7 release validation

The original audit sections below preserve the first candidate's measured
results. Its post-commit packaging failure, subsequent owner-directed push,
and corrected-candidate validation are recorded in the final **Corrective
validation supplement**. Initial package passes do not override that failure.
The operative current approval is `docs/m7_owner_approval.json`; previous
candidate approval is preserved separately and does not approve the correction.

Audit and execution date: **2026-09-10**. Workbench **1.0.0**.
Decision owner: **benjainnsthao**. Next review: **2026-12-09**, sooner for a
material security, dependency, licensing, or provenance issue.

This is measured release-candidate engineering evidence. The actual final
outcome and human acceptance are in `docs/m7_owner_approval.json`; no final
approval is inferred from this report. Only `release` with all technical gates
passed completes M7 as a public-release gate. Owner-approved original-code
licensing is a separate conversational decision dated **2026-09-10**.

## Repository and candidate identity

Repository: `hmong-tts`, origin `https://github.com/benjainnsthao/hmong-tts.git`,
active branch `rescope/audited-tts-workbench`. Work was performed in the
existing Linux workspace checkout; its absolute machine path is intentionally
excluded from public evidence.

Starting local and fetched remote active HEAD:
`32e55eed6c647fbe497e14973c768bf83f0a3a85` (completed M6).
Required M5 `fb72a5e87f9b3841d29ff4a0717546646e188422` is an ancestor of both.
Initial ahead/behind counts were 0/0; the working tree was clean. Origin,
remotes, branches, untracked/ignored boundaries, and graph were inspected,
then `git fetch --prune origin` refreshed remote references. No switch,
fast-forward, clone, merge, or history rewriting was needed. Ignored
pre-existing local work was preserved.

Remote main was explicitly queried and equals
`fd1756485b1e1b75fd1efee5e37519fa8e255415`; local main matches. The protected
local preservation branch was absent, which is recorded as absence rather
than claimed matching evidence. No protected branch was modified.

The complete candidate identity and changed-file inventory are in
`m7_candidate_manifest.json` and the file list below. The manifest binds the
starting commit, sorted candidate file names/modes/SHA-256 values, and its
own reproducible digest. Only the self-referential manifest and normalized
actual-owner-approval object are excluded as specified in
`docs/m7_release_decision.md`. It contains no claim to its own final Git SHA.

Pre-execution runtime-source/configuration digest:
`2d1de43c47ed34734d47419494c1d1ffafe01249ec33908bb5d78cd7af3f30b7`.
This hashes compact sorted-key JSON entries for every tracked file in `src/`,
`configs/`, `pyproject.toml`, and `uv.lock`, with each entry's path and SHA-256.
The external `runtime-source-manifest.json` records the full list. Final
candidate content matches that inventory; documentation and review tooling
were added afterward without changing measured runtime/configuration bytes.

## Licensing, primary sources, and dependency corrections

- Exact standard Apache-2.0 text, NOTICE, THIRD_PARTY_NOTICES.md, SPDX package
  metadata, and wheel/sdist license inclusion are reviewed. The owner confirmed
  authority and commercial reuse of covered original code on 2026-09-10.
  This is conversational approval, not a cryptographic signature or final
  release approval. Third-party and historical rights remain intact.
- `docs/license_matrix.md` records current immutable model cards/API access,
  CC BY-NC 4.0 terms, exact cached snapshot/safetensors identities, official
  Vietnamese prompt/source/hash, current legal basis, and distribution policy.
  Both models are public/ungated at the exact revisions; no token or alternate
  source was needed.
- The retained Vietnamese prompt hash and official source PDF match M6.
  Current Article 15(2) review includes 2009, 2019, 2022, and 2025 amendments;
  Law 131/2025/QH15 adds clause 4 without replacing clause 2. Source attribution
  is retained; raw text/PDF/OCR remains external. No prompt substitution,
  correction, translation, or new Vietnamese text was used.
- `docs/m7_dependency_audit.md` records all 84 current exact upstream metadata
  queries (82 locked dependencies plus Hatchling and uv). All succeeded; no
  selected version was yanked and no advisory remained in their returned
  vulnerability lists. This is a dated advisory check, not proof of no defects.
- M7 fixes Starlette 1.0.0 to 1.3.1, PyTorch 2.12.0 to 2.13.0, and setuptools
  81.0.0 to 83.0.0; removes unused vulnerable Accelerate and unneeded psutil;
  and accepts only PyTorch-required CUDA toolkit/Triton transitive changes.
  No other dependency or checkpoint is substituted. CI/hook pins resolve to
  the same selected code at immutable commits.

## Sanitized environment and portability

| Observation | Measured result |
|---|---|
| Distribution/OS | Ubuntu 24.04.1 LTS, WSL2, Linux x86-64 |
| Kernel identification | 6.18.33.2-microsoft-standard-WSL2 |
| Python / Git / uv | 3.12.3 / 2.43.0 / 0.11.28 |
| Workbench / adapter | 1.0.0 / mms-vits 1.0.1 |
| PyTorch / Transformers | 2.13.0+cu130 / 5.13.1 |
| safetensors / SciPy | 0.8.0 / 1.18.0 |
| Driver visibility / CUDA build | 610.62 visible through WSL / 13.0 |
| Intended GPU | NVIDIA GeForce RTX 4070, 12,282 MiB |
| Runtime preflight free/total GPU bytes | 11,630,804,992 / 12,878,086,144 |
| Reported supported dtypes | float32, float16, bfloat16 |
| Actually executed dtype | float32 on CUDA and CPU |
| Clean core readiness | core true; CPU-model false; CUDA-model false |
| Separate MMS readiness | core, CPU-model, and CUDA-model true |

Clean core and optional MMS environments are separate Python 3.12 temporary
environments. Core contains neither torch nor transformers. Optional imports
are absent from ordinary package/help/metadata paths. Capability collection
is explicit. CUDA absence does not prevent core operation.

The optional MMS environment installs from the corrected frozen lock and
executes both checkpoints. No driver/kernel/firmware/host-security change was
needed. Native Windows, macOS, ARM, other accelerators/drivers, reduced-precision
model execution, and cross-device performance are unvalidated. CPU diagnostics
are bounded local observations, not a broad portability certification.

## Real inference and integrity

| Model | Registered repository | Immutable revision |
|---|---|---|
| mms-eng | facebook/mms-tts-eng | c71de0fe7204c83f1c10820a7d696d0b450048ba |
| mms-vie | facebook/mms-tts-vie | b58928d033932a49aa8e3d6cf11625b25fe928d2 |

Model access was explicitly acknowledged for every smoke, benchmark, and
service run. Source resolution used only the registry. Safetensors is required;
no pickle alternative or caller-selected repository/revision is used. Both
cached weight hashes match upstream LFS identity, as recorded in the license
matrix. One model is owned per adapter; unload runs after execution.

Seed 555; noise_scale 0.667; noise_scale_duration 0.8; speaking_rate 1.0.
Requested and resolved direct device: cuda. Runtime/dtype/model/adapter and
prompt-reference/hash fields agree across the paired runs.

| Direct CUDA observation | mms-eng | mms-vie |
|---|---:|---:|
| Sample frames | 38656 | 185600 |
| Sample rate, Hz | 16000 | 16000 |
| Channels | 1 | 1 |
| Duration, seconds | 2.416 | 11.6 |
| Cold load, seconds | 4.992860 | 5.697397 |
| Synthesis, seconds | 0.645719 | 1.542471 |

Direct CUDA WAV SHA-256:

- mms-eng: `ed5a5ecf8a6d6da6ed783026516af6acbb25a91b29e7415fbc28471c9bc5dc01`.
- mms-vie: `85cd0d92185d1eaa20d86b63803965ba38f600b496e46057e29151ac18ae60f3`.

Prompt SHA-256:

- English original synthetic fixture:
  `f8cc7678783377f15fd576e51b2b1fffdf969a591415c3858f816042a1194892`.
- Vietnamese approved external legal-document sentence:
  `b6919cd1f33ec808355462bfa29e8444f8525560f8223d0486e67b35f29854c5`.

Eight real WAV/manifest pairs (four direct CUDA, two bounded CPU, two service)
pass schema validation, WAV reopening, PCM16/mono/16 kHz, full frame-byte
count, duration, checksum, registry revision/source, prompt reference/hash,
seed/device/dtype/runtime, and manifest consistency checks. Success manifests
are published last by the existing atomic transaction. No raw prompt or
absolute private path is present in the inspected manifests/logs.

Same-environment comparison: both models' paired CUDA WAV checksums and frame
counts match exactly. Identity/settings metadata is equal, with timestamps,
run identifiers, output labels, and timings intentionally excluded from the
comparison. CPU checksums differ from CUDA here. No cross-device byte identity
or timing promise is made. `scripts/verify_m7_artifacts.py` reproduces the checks.

Bounded CPU diagnostics: one approved prompt per model, two intra-op and two
inter-op threads, requested/resolved CPU/float32. English load/synthesis were
4.042842/0.863824 seconds; Vietnamese 0.823721/2.751428 seconds. Both succeed
with valid artifacts and unload. Reused process/import/cache state makes
these diagnostics unsuitable as a comparative CPU cold-load benchmark.

## Structural QC and bounded benchmarks

Both QC reports are `qc_passing`: all 14 rules pass under unchanged M4
thresholds and every rule/report retains `engineering_sanity_check` scope.
No threshold was altered. QC establishes waveform structure and limited
amplitude/silence sanity, not pronunciation, naturalness, intelligibility,
linguistic correctness, or speaker quality.

Both benchmark reports are `completed`: one excluded warmup, three measured
repetitions, maximum ten, same seed/settings, explicit CUDA/float32.

| Benchmark measure | mms-eng | mms-vie |
|---|---:|---:|
| Cold load, seconds | 4.330681 | 4.311691 |
| Excluded warmup, seconds | 0.593946 | 0.614761 |
| Audio duration, seconds | 2.416000 | 11.600000 |
| Median synthesis, seconds | 0.040165 | 0.145120 |
| Nearest-rank p95 synthesis, seconds | 0.041138 | 0.158158 |
| Median real-time factor | 0.016625 | 0.012510 |
| p95 real-time factor | 0.017027 | 0.013634 |
| Measured successes / failures | 3 / 0 | 3 / 0 |

All observed CPU/CUDA memory fields were available on this machine. CPU peak
RSS after benchmark completion: 1,799,016,448 bytes (English) and 1,800,040,448
bytes (Vietnamese). These are process lifetime high-water marks, not model
memory. CUDA allocated/reserved just after model load: 146,383,872/161,480,704
bytes (English), 146,427,904/161,480,704 bytes (Vietnamese). After unload both
reported 8,519,680/20,971,520 bytes; remaining runtime/allocator buffers are
not an owned model or a claim that all memory returned to zero. Measurements
are point observations, not peak device/system use. Missing measurements on
other environments must be `unavailable`, never fabricated zeros.

Three repetitions and different prompts support descriptive local timings,
not language rankings or deployment capacity. No MOS, ASR, pronunciation,
SNR, PESQ, STOI, speaker-similarity, or other perceptual/language metric is added.

## Real local service and security controls

The existing production service ran with literal loopback binding, one Uvicorn
worker/process, one adapter/model owner and active operation, FIFO capacity 2,
30-second pre-execution queue/request deadlines, max input 500 characters,
access/request/client logging disabled, and an external nested M7 artifact root.

- Health and readiness succeeded; the registry exposed exactly both models.
- Both English and Vietnamese approved prompts synthesized successfully on
  CUDA, switching through the single owner; responses/manifests had no prompt echo.
- An unknown model returned the sanitized `unknown_or_unapproved_model` category
  and HTTP 404, with no new partial or success artifact.
- The probe completed before SIGINT. Uvicorn exited 0; adapter state was
  `unloaded`; queue admission was `closed` with zero active/pending requests;
  a connection check confirmed the loopback listener had stopped. No persistent
  server or public binding was introduced.
- Synthetic ASGI and FIFO/lifecycle tests validate queue fullness, ordering,
  pre-execution expiry, serialization, non-preemptive active work, sanitized
  failures, and shutdown. No destructive exhaustion or unsafe cancellation was used.

Loopback is not authentication. Character/FIFO bounds are not HTTP-body byte,
output-duration, request-rate, or disk quotas. Tiny positive speaking rates
can amplify work. Only trusted local clients and ordinary generation settings
are in the proposed scope; native active calls cannot be safely preempted.
`docs/service_threat_model.md` and REL-SERVICE-001 explicitly submit those
limits for owner acceptance. Dependency advisories were reviewed/corrected.

## Required validation outcomes

| Gate | Candidate outcome |
|---|---|
| Safe discovery, origin/branch/graph, clean start, fetch/prune, ancestry/protected refs | PASS; refreshed before review |
| Current license/provenance/model availability/dependency advisory audit | PASS with explicit bounded residual proposals |
| Frozen lock validation | PASS, corrected 83-entry lock |
| Clean online core cache population, then frozen offline synchronization | PASS, 41 installed core/dev packages; no model host access |
| Build/install current wheel in clean core | PASS; optional ML absent |
| Separate locked MMS environment and capability reports | PASS; both CPU and intended CUDA diagnostics measured |
| Format / Ruff / strict MyPy | PASS |
| All active config families, benchmark CUDA variant, registry/list | PASS |
| Full synthetic suite, branch-aware coverage | **266 passed; 83.0972%**, floor 78% |
| Focused service/ASGI suite, branch-aware coverage | **77 passed; 96.6549%**, floor 90% |
| Full pre-commit suite | PASS; repeated after final staging |
| Ordinary/lazy imports, all eight help commands, old package/CLI absence | PASS |
| Service schema/config/OpenAPI metadata operations | PASS without model access |
| Acknowledgement and literal-loopback fail-closed checks | PASS; no-ack commands return 2 |
| Canonical-only root and legacy-only failure/absence tests | PASS |
| Both immutable CUDA runs/repeats, WAV/manifest integrity | PASS; eight pairs total including CPU/service |
| Both structural QC and bounded benchmark reports | PASS, zero measured benchmark failures |
| Real service and clean shutdown | PASS, both models and safe rejection |
| Artifact/cache/environment external boundaries | PASS; retained M6 not overwritten |
| Candidate/staged file privacy and historical file-content scan | PASS; final staging audit below |
| Existing Git author/committer metadata | FINDING: personal-provider email in 14 prior commits; explicit owner disposition required |
| Wheel/sdist content, package metadata, exact license/notices | PASS; final inventory below |
| Historical M1–M6 reports, deferred NV record, M4 thresholds | Byte-for-byte unchanged |
| Active claims and scope audit | PASS; no Hmong or linguistic-quality claim |
| Working/staged whitespace checks | PASS |
| Final named owner decision, one commit, exact-commit checkout validation, push | Gated on actual final owner approval; not yet performed at candidate review |

One test-only Starlette deprecation warning remains: its HTTPX test-client
adapter recommends HTTPX2. The pinned existing HTTPX tests pass. No unrelated
client migration is performed; this warning is recorded, not hidden.

## Ordinary failure resolutions and honest limits

- Official PDF download timed out on the first attempt; a bounded ordinary
  retry succeeded and produced the retained source's exact hash. Some WIPO
  signed download links failed; authoritative Government Portal scans supplied
  the current amendment evidence, including a visual page check.
- The initial archive-inspection loop included uv's non-archive directory marker;
  the verifier was restricted to wheel/tar.gz files and inspection reran successfully.
- The first artifact-verifier draft also traversed synthetic test artifacts and
  assumed the wrong QC status spelling. Restricting verification to the three
  real-run directories and using the existing `qc_passing` schema label fixed
  the verifier; all eight actual pairs then passed. No runtime/QC result changed.
- The new executable-mode manifest test initially failed on the mounted artifact
  filesystem, which does not honor chmod as expected. Its mode test now uses
  a native external temporary directory. The focused test and complete suite
  reran successfully. Candidate file-mode evidence is taken from the native
  Linux repository filesystem.
- Known dependency findings were fixed, not accepted away. Scope remains one
  trusted-local platform and dated upstream evidence; no claim is made that
  pattern scans or advisory databases find every possible vulnerability/secret.

## Privacy, retention, packages, and final candidate inspection

The relevant reachable-history scan inspected **309 unique file blobs** and
found no flagged artifacts, credentials, or actual private paths in file contents.
The expanded metadata audit separately found one personal-provider email identity
in author/committer fields across **14 existing commits**. The address is not
reproduced or newly committed in a file. Approval of the public owner handle
does not approve this existing disclosure. REL-PRIV-001 is release-blocking
until explicit owner acceptance of continued historical visibility; history
rewriting is not authorized. A verified GitHub no-reply author/committer identity
is prepared for the new M7 commit. Historical
reports and NV-001 through NV-008 are unchanged. The runtime privacy check
inspected 24 real reports/logs and found no prompt echo, actual private
path/machine value, or HTTP access-log entry. Normal Uvicorn startup/shutdown
messages remain external; no client identity or process identifiers are copied
into public evidence. Only the approved public owner handle is used in governance.

Weights, caches, audio, raw prompts, PDFs/OCR, environments, full logs/reports,
and local package archives are outside Git. Public packages contain original
source and applicable project notices; no upstream dependency/model binaries
are bundled. LICENSE equals the official Apache text byte for byte. Both
archives carry LICENSE, NOTICE, THIRD_PARTY_NOTICES.md and correct Apache
metadata; tar header identities are empty. Wheel package-source bytes are
compared with the candidate and sdist contents are inspected without unsafe
extraction. Package hashes and member inventories remain external because
embedding a package's own hash in its included report would be self-referential.

Final archive inspection: **PASS**, wheel 47 files and sdist 159 files, including
all three exact notices and no forbidden artifacts/private values. The complete
candidate contains 158 files including the manifest. Installed-dependency
consistency passes in both environments; all 82 actual MMS distributions match
the frozen lock and neither Accelerate nor psutil remains. Candidate source,
local documentation links, license bytes, historical preservation, package
contents, staged byte equality, and privacy are rechecked after final staging.
The expanded historical commit-email finding remains an explicit human gate,
not a passed no-disclosure history check.

## External artifact references

All references below are relative to `TTS_WORKBENCH_ARTIFACT_ROOT`, with run
prefix `m7/20260910T122457Z/`:

- `audit/`: exact source/advisory metadata, license source, hashes, privacy/history
  summaries, source/legal-basis scans and external OCR evidence.
- `environment/core.json`, `environment/cuda.json`, and
  `environment/runtime-preflight.json`: separate sanitized capabilities.
- `runs/mms-eng.wav`, `runs/mms-vie.wav`, `runs/*-repeat.wav` and paired
  `.manifest.json`: direct CUDA and same-environment comparison.
- `cpu/mms-eng.wav`, `cpu/mms-vie.wav` and manifests; `cpu-diagnostics.json`.
- `qc/mms-eng.json`, `qc/mms-vie.json`: full engineering QC.
- `benchmarks/mms-eng.json`, `benchmarks/mms-vie.json`: all raw observations.
- `service/runs/`: two generated WAV/manifest pairs, with identifiers external;
  `service-probe.json`, `service-shutdown.json`, `service-process-check.json`.
- `runtime-source-manifest.json`, `integrity-verification.json`, `core-checks.json`,
  `runtime-checks.json`, `coverage-aggregate.json`, `coverage-service.json`.
- `logs/`, `tooling/`, `packages-final/`: detailed logs, temporary synthetic
  validation data, and final inspected local release archives.

Shared model/runtime caches remain under external `cache/`. Raw prompts and
source material are retained under this run's `prompts/` and `audit/`.
The service temporarily treats the M7 run directory itself as the canonical
root, so its manifest paths start with `service/runs/` inside that nested root.
Exact reproducible commands are in `docs/m7_reproduction.md`; retention through
the next risk review is defined in `artifacts/README.md`.

## Changed and added files

The candidate manifest is authoritative for every reviewed file. M7 changes
are listed below; historical files and the deferred record are excluded.

Modified:

- `.github/workflows/ci.yml`
- `.pre-commit-config.yaml`
- `LICENSE`
- `PROJECT_STATUS.md`
- `README.md`
- `artifacts/README.md`
- `configs/models/registry.yaml`
- `docs/architecture.md`
- `docs/decisions.md`
- `docs/environment.md`
- `docs/implementation_roadmap.md`
- `docs/inference_contract.md`
- `docs/license_matrix.md`
- `docs/local_service.md`
- `docs/mms_smoke_test.md`
- `docs/model_registry.md`
- `docs/release_risk_register.md`
- `docs/service_threat_model.md`
- `docs/threat_model.md`
- `pyproject.toml`
- `src/tts_workbench/__init__.py`
- `src/tts_workbench/artifacts/__init__.py`
- `src/tts_workbench/artifacts/paths.py`
- `src/tts_workbench/environment/detect.py`
- `src/tts_workbench/inference/mms_smoke.py`
- `src/tts_workbench/inference/mms_vits.py`
- `tests/unit/test_artifact_boundary.py`
- `tests/unit/test_environment.py`
- `tests/unit/test_m4_cli.py`
- `tests/unit/test_mms_vits_adapter.py`
- `tests/unit/test_project_identity.py`
- `tests/unit/test_service_application.py`
- `tests/unit/test_service_contracts.py`
- `tests/unit/test_service_scope.py`
- `uv.lock`

Added:

- `CHANGELOG.md`
- `NOTICE`
- `THIRD_PARTY_NOTICES.md`
- `docs/m7_dependency_audit.md`
- `docs/m7_migration.md`
- `docs/m7_owner_approval.json`
- `docs/m7_portfolio_summary.md`
- `docs/m7_release_decision.md`
- `docs/m7_reproduction.md`
- `reports/validation/m7_candidate_manifest.json`
- `reports/validation/m7_release_validation.md`
- `scripts/release_manifest.py`
- `scripts/verify_m7_artifacts.py`
- `tests/unit/test_release_manifest.py`

## Final decision and post-approval handoff

Every risk has a reviewed proposal, scope, evidence, rationale, owner,
limitation, and 2026-12-09 review date in `docs/release_risk_register.md`:
four proposed closed, seven proposed accepted, one proposed deferred.
The privacy proposal specifically requires acceptance of the existing commit-email
exposure; without it, public `release` is not supported under the no-rewrite rule. The
actual owner-approved mapping and outcome are recorded only after receipt.
The original-code license date remains 2026-09-10 even if final approval is later.

No implementation commit or push is made before final approval. After approval,
the exact full SHA, clean-checkout validation, local/remote equality, M5/M6
ancestry, protected-reference checks, and push result are reported in the
handoff. The approved manifest remains verifiable with only its specified
approval-object normalization. No commit claims to contain its own literal SHA.

No merge, reset, rebase, force-push, history rewrite, tag, package publication,
GitHub release, deployment, pull request, new checkpoint, training, or later
community-language/application work is performed under M7. Stop after the
approved decision, necessary exact-commit validation, one commit, and normal
active-branch push.

## Corrective validation supplement — 2026-09-10

### Failure, authorization, and synchronization

The owner approved the original digest
`8e5e9d918c9570da40b914c03918f5b844fad13c133ff65f0edbb05281d02496`
with `i approve and select release`. The implementation was committed as
`61e0ce5f9c7b21bd805b87f0420d9b22f2677c03`. Clean detached-worktree validation
then found a 160th sdist file: a `.git` pointer containing a private absolute
path. The original ordinary-checkout sdist had 159 files. Its other members
and wheel matched the approved archives. Validation stopped at packaging;
the remaining clean-commit checks were not claimed to have passed.

That defective archive was retained externally and never committed or
published. The raw pointer is not reproduced here. After being informed of
the defect, the owner explicitly requested `push to git`; the active branch
was normally pushed. The selected `release` outcome did not complete the
failed technical gate. No additional commit or history rewrite occurred.

The owner then authorized exactly one additional corrective M7 commit,
preserving the existing commit and requiring new approval of the changed
candidate. `previous_candidate_decisions` retains the original approval
verbatim; `corrective_commit_authorization` records the new authority. Neither
is normalized out of the new candidate digest. The current approval is pending
until the owner reviews this complete correction.

Corrective work started clean, with local and fetched remote active HEAD both
at the first M7 commit. Fetch/prune required no synchronization change. M5
and M6 remain ancestors. Remote/local main retain
`fd1756485b1e1b75fd1efee5e37519fa8e255415`; the local preservation branch
remains absent. The correction uses isolated external ordinary/worktree
copies and does not modify protected references.

### Correction and regression evidence

Hatchling 1.29.0's default directory handling did not exclude a worktree's
`.git` file. Both wheel and sdist targets now explicitly set
`exclude = [".git"]`, covering administrative files/directories at any depth.
The [official Hatch pattern documentation](https://hatch.pypa.io/1.16/config/build/#patterns)
was inspected on 2026-09-10; behavior was tested with the repository's exact
pinned backend. No backend, runtime, dependency, or version upgrade was made.

Two real offline archive tests place synthetic Git directories or pointer
files at the project root and inside the package. They inspect both archives
without extraction, reject administrative names and canary/private temporary
bytes, and require the package and all three notices. Under the original
configuration the pointer case fails and the directory case passes. Under
the correction both pass. The expected failing regression log is retained.
CI now populates the pinned build cache before these offline tests.

Full builds from an actual ordinary clone and detached Git worktree contain
the same candidate bytes/modes. Their wheels match byte for byte, as do their
sdists. Inspection checks every member against the candidate inventory,
rejects Git metadata, unsafe paths, links, duplicates, unexpected members,
forbidden artifacts and private values, and validates source bytes, eight
entry points, metadata, exact notices, and empty tar owner/group identities.
Current wheel: **47 files**. Current sdist: **160 files**, comprising the
159-file candidate plus `PKG-INFO`; the added member relative to the original
ordinary candidate is the new regression test, not Git metadata.

Compared with the previously approved wheel, only `METADATA` and its `RECORD`
checksum change because the README now records the corrective release status.
Metadata headers, runtime source files, entry points, and notices are unchanged.
A first verifier assumed complete equality with the earlier wheel; the
comparison was corrected to check this explicit README-derived metadata delta.
Candidate-copy comparisons also required rebuilding after documentation
changed; final package validation uses the final copied inventory. These
verification adjustments did not change runtime behavior or hide a failed gate.

A repeated local wheel installation hit a uv rename error in the mounted
artifact-filesystem cache. Retrying that offline, no-dependency wheel install
with `--no-cache` succeeded without deleting caches or changing dependencies.
The original error log is retained as `logs/install-wheel-mounted-cache-failure.log`.

### Required gates and retained runtime evidence

| Corrective gate | Measured outcome |
|---|---|
| New clean Python 3.12 core, frozen offline sync | PASS; retained dependency caches, optional ML absent |
| Frozen lock, built-wheel install and dependency consistency | PASS; lock unchanged |
| Format, Ruff, strict MyPy | PASS |
| Eight help commands, imports/lazy imports, old package absence | PASS |
| All configurations, registry/list, service schema/OpenAPI | PASS |
| Model-access acknowledgement fail-closed paths | PASS; return code 2 |
| Aggregate synthetic/ASGI/compatibility/binding tests | **268 passed; 83.0972% branch-aware coverage**, floor 78% |
| Focused service tests | **77 passed; 96.6549% branch-aware coverage**, floor 90% |
| Original-config regression / corrected-config regression | Expected pointer failure reproduced / both cases pass |
| Complete core validation driver | **36 checks passed** |
| Full pre-commit and working/staged whitespace | PASS; repeated after final staging |
| Ordinary/worktree wheel and sdist inspection and equality | PASS; four archives, 47 wheel / 160 sdist files |
| Candidate/staged privacy, source identity, notices, links | PASS |
| Reachable historical file-content scan | **358 unique blobs**, no flagged contents |
| Git author/committer metadata | Same 14 prior commits with previously accepted personal-email exposure; raw value withheld |
| M1–M6 validation, NV-001–NV-008, M4 QC thresholds | Byte-for-byte unchanged |
| Retained real WAV/manifest/QC/benchmark integrity | PASS again for the eight retained pairs and both report sets |
| Retained optional MMS dependency consistency | PASS |
| Corrected candidate owner approval, corrective commit, clean exact-commit validation and push | Pending approval; not claimed complete |

The existing test-only Starlette/HTTPX deprecation warning remains documented.
No thresholds were weakened and no failure was converted into a runtime pass.

The original runtime-source digest remains a historical execution identity,
not the corrected whole-file digest. Comparing its complete inventory finds
only `pyproject.toml` changed. Parsed comparison proves its sole changes are
the two Hatch exclusions: `src/`, `configs/`, `uv.lock`, project metadata, and
build-system requirements are identical. The corrected wheel independently
confirms unchanged runtime bytes. Therefore the measured RTX 4070 CUDA/float32
executions, bounded CPU diagnostics, same-environment comparison, QC,
benchmarks, and real service/shutdown observations above remain applicable.
They were not remeasured solely for this packaging correction. Integrity was
rechecked against retained artifacts; no model, prompt, or measurement was
substituted. No active service was started during corrective packaging work.

### Current review and external evidence

Corrective file inventory (relative to the first M7 commit):

```text
.github/workflows/ci.yml
CHANGELOG.md
PROJECT_STATUS.md
README.md
artifacts/README.md
docs/decisions.md
docs/implementation_roadmap.md
docs/m7_owner_approval.json
docs/m7_portfolio_summary.md
docs/m7_release_decision.md
docs/m7_reproduction.md
docs/release_risk_register.md
pyproject.toml
reports/validation/m7_candidate_manifest.json
reports/validation/m7_release_validation.md
scripts/release_manifest.py
tests/unit/test_release_manifest.py
tests/unit/test_release_packaging.py
```

The candidate manifest now starts at
`61e0ce5f9c7b21bd805b87f0420d9b22f2677c03` and binds every corrected candidate
file/mode, including the prior decisions. Its reproducible digest is in
`m7_candidate_manifest.json`; the existing two narrow self-reference/current-
approval exclusions remain. No digest is embedded in its own included report.

Proposals remain four `closed`, seven `accepted`, and one `deferred`, with
benjainnsthao as owner and next review 2026-12-09 or sooner for a material
issue. REL-PRIV-001 now includes the corrected packaging defect and preserved
failure evidence. The defect itself is not submitted as an accepted residual;
the previously disclosed historical-email visibility remains an explicit
bounded residual. All other scopes and acceptance criteria are unchanged.

The corrected candidate requires new final owner approval. After approval,
create only the single authorized corrective commit, validate its exact tree
in clean ordinary and worktree checkouts, and normally push only the active
branch. Any post-commit validation failure requires a stop without pushing.
Only successful exact-commit validation and push following approved `release`
complete M7's public-release gate. The exact corrective SHA is reported in
the later handoff; this report does not claim to contain its own final SHA.

Correction evidence is relative to the external artifact root at
`m7/20260910T122457Z/correction-20260910T232407Z/`: `package-inventory.json`,
`core-checks.json`, `build-checks.json`, `coverage-aggregate.json`,
`coverage-service.json`, `audit/`, `environment/core.json`, `logs/`, and
`packages/ordinary/` plus `packages/worktree/`. Failed original committed-build
evidence remains separately under `m7/20260910T122457Z/committed/`, including
`postcommit-blocker.json` and the subsequent `push-handoff.json`. Package hashes
and full inventories stay external to avoid self-referential archive digests.

Public distribution remains covered original Apache-2.0 code and sanitized
engineering evidence only. Weights, caches, prompts/source, audio, detailed
raw reports/logs, environments, and the defective archive remain external
and undistributed. No private path or machine identity is included in the
candidate. No Hmong capability or linguistic-quality claim, later community
phase, training, deployment, publication, tag, merge, or PR is introduced.
