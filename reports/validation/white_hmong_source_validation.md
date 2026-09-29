# Published-source White Hmong preparation validation

Date: **2026-09-28 UTC**. This is subsequent local development, not an M7 release
approval, language acceptance or publication. No commit or push was performed
during the task; `prompt.md` remains untracked and was not changed. The owner
subsequently authorized committing and pushing this work on 2026-09-29, after
a review that made the blind answer key private from creation and marked
packet source text as `lang="hmn"` (28 workflow tests).

## Completed outcome

- **136 source items collected**, 53 with retained published meanings; selected
  **30 distinct cases: 20 development / 10 held-out**, with the proposed 8/6/4/2
  and 4/2/2/2 category allocations. No generated filler sentences.
- Sources: 14 Wiktionary usage examples, 8 Clark examples from the licensed
  publisher PDF, and 8 Tatoeba text examples. Retained source snapshots, immutable
  revisions where available, access times, text/meaning, licenses, attribution,
  transcription records and fingerprints outside Git. English Tatoeba meaning
  pages were also reconciled; current ownership is not misreported as authorship.
- All **30 source snapshot hashes and dates** reconcile. Text-license records
  support local synthesis subject to conditions; public model/voice/audio/service
  rights remain unresolved. Structural checks do not authenticate permission.
- Draft v2 passes the unchanged target-shape validator. The companion audit finds
  **44 related within-split pairs, zero cross-split heuristic flags**, and source
  shares of 14/8/8. Held-out source concentration is 8/10 Wiktionary.
- **30 pending / zero reviewed**. The real `--require-reviewed` invocation exits
  **2 as expected**. No human reviewer identity, approval, score or freeze was
  fabricated. Eighteen source/context flags remain; twelve cases have only
  provisional source-supported checks.
- Published RPA references and nine development lexical comparisons were
  retained. A reserve revision added absent `-m` coverage before any candidate
  outputs existed. Both splits have b/j/v/s/g/m and unmarked ending candidates;
  `-d` and a validated minimal-tone-pair inventory remain explicit coverage gaps.
- Four ordinary Google Translate UI checks on **development only**: two
  provisional agreements, two tense/aspect discrepancies. Original source text
  is unchanged. Google's documented `hmn` label is Hmong without an exclusive
  White Hmong guarantee. No credentials, billing, login/consent action, private
  endpoint or back-translation was used.
- Refreshed immutable voice/dependency/license research and hardware preflight.
  **Zero eligible candidates, zero weight downloads, zero new ML dependencies,
  zero Hmong synthesis attempts or candidate audio.** No latency, peak inference
  memory, waveform-QC pass or perceptual result is claimed.
- Prepared an external 20-case browser packet, attribution, proposed rubric,
  empty score sheet, separate key and bounded experiment/finalist procedure.
  It explicitly says **awaiting eligible audio**.

See [source evidence and workflow](../../docs/hmong_evaluation_pack.md),
[the consolidated review decisions](../../docs/hmong_collection_review.md) and
[primary-source model audit](../../docs/hmong_voice_decision.md) for citations,
limitations and specific blockers. Published text may have appeared in model
pretraining; the reserve is held out only from this project's tuning.

## Implementation and checks

New offline modules:

- `tts_workbench.evaluation.source_audit`: strict companion records, pack/text/
  reference and Google-input hash binding, comparison-only normalization,
  heuristic near-duplicate/template checks, explicit family separation, source
  concentration and separate evidence fingerprint. It never approves a case.
- `tts_workbench.evaluation.listening`: development-only exports, at most two
  fixed configurations / 25 clips each, external paths and separate key,
  input fingerprints/permission-record checks, bounded mono PCM16 reads,
  randomized labels/order, native playback and empty CSV scores. Raw source text
  is HTML-escaped and exported IDs are constrained for spreadsheet safety.

| Check | Result |
|---|---|
| Complete core suite | **454 passed**, 85.38% aggregate branch-aware coverage (78% required) |
| New workflow tests | **27 passed**; stale evidence, duplicate/family leakage, source/translation preservation, held-out rejection, permission/hash failures, blind labels, PCM preservation, empty packets, checkout boundaries and rollback |
| Existing prompt validator tests | **121 passed**, unchanged review semantics; included in full suite |
| Existing browser suite | **4 passed** using the previously isolated Playwright tools; core run's one optional-module skip resolved by this separate run |
| New browser packet probe | Actual 20-text/zero-audio draft renders correctly; synthetic-only two-candidate packet passes native WAV playback and seeking |
| Ruff format / lint | PASS, 88 Python files formatted |
| Strict MyPy | PASS, 47 source files |
| Frozen lock / installed dependencies | Offline lock check PASS; 82 installed packages compatible; no dependency edits |
| Config / registry / QC / service configuration | PASS; existing registry still has two entries |
| Privacy / artifact boundary / whitespace | PASS; no real sentences, WAVs, weights, snapshots or detailed source records added to Git |
| Historical/protection integrity | Ten selected M7/NV/validator/loader/registry/dependency files byte-identical to HEAD; historical M7 approvals/manifests untouched |

The first browser probe hit Playwright's string-predicate `eval` restriction
under the packet's content security policy. The probe was corrected to poll via
browser evaluation; the content security policy was retained. Playback and seek
then passed. This was a test-harness issue, not Hmong inference evidence.
The core suite retains an existing Starlette HTTPX deprecation warning.

The new tools do not fetch models, call translation APIs, import optional ML
runtimes, change the production service, or add CLI entry points. Existing model
loading remains safetensors-only. Packet paths are guarded for trusted local
use, not adversarial concurrent filesystem races or same-user access isolation.

## External artifacts and identities

Root: `/root/tts-workbench-artifacts/white-hmong-20260928/`.
`ACTIVE_ARTIFACTS.json` identifies current files; earlier draft/evidence/packet
versions and failed probe artifacts are retained.

| Artifact | Root-relative path |
|---|---|
| Master draft | `custodian/draft-v2.json` |
| Source/permission/meaning/Google records | `custodian/draft-v2-evidence-v2.json` |
| Protected reserve | `custodian/held-out-v2.json` and `held-out-v2-evidence-v2.json` |
| Development-only input | `development/development-v1.json` and `development-v1-evidence-v3.json` |
| Source-backed language comparisons | `development/language-checks.json` |
| One human review packet | `review/REVIEW_PACKET.md` |
| Browser packet / scores | `review/listening-v2/index.html` and `scores.csv` |
| Answer key | `custodian/listening-v2-key.json` (mode 0600) |
| Candidate decisions / preflight | `research/candidate-decisions.json`, `resource-preflight.json` |
| Raw research / source retention | `research/`, candidate inventories in `custodian/` |
| Structural / source checks | `validation/structural-v2.json`, `source-audit-final-attributed.json`, `review-gate.json` |
| Tests / coverage / browser | `validation/full-tests.log`, `coverage.json`, `focused-final.log`, `browser-tests.log`, `browser-packet-result.json` |

Fingerprints use the existing canonical validated-pack algorithm and the new
independent companion-evidence fingerprint:

- Full draft: `36ac5a2023b19843aa52e26f70c45a426b238bf32711e7d5a886bde5de83bc8e`.
- Full evidence: `5084179d469f73809e921680e8f04c249deb8c332354dd41172b91f04bb615d3`.
- Development pack: `43976ad1f081c37024b34fe010466a0e6dd13e103a7119b996381e079adb5af9`.
- Development evidence: `ab6ca110afeaf4f08a0bc583a9e12bf89aedc2b8a46000a22bee025c19c6dd01`.

All authorized independent preparation is complete. Model experiments remain
blocked by concrete rights/artifact prerequisites, and final language acceptance
requires real fluent review. Recommended next action: review the prepared packet,
starting with ambiguities and prospective criteria, while keeping model execution
deferred. Training, adaptation, recording and deployment were not started.
