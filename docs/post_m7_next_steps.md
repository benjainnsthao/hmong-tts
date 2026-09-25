# Next steps after M7

Documented: **2026-09-11 UTC**. Public decision owner: **benjainnsthao**.
Original status: planning documentation only. See the dated update below for
the subsequent local work authorized by the owner; M7 approval is unchanged.

M7 is complete. The recommended next development step is a separately
authorized community scoping phase that establishes whose needs the project
should serve and what evidence would justify language work. Release maintenance
continues independently. Repository integration and publication are optional
owner decisions.

## Authorized preparation update — 2026-09-25

The local dashboard was completed after this original plan. The current task
also authorizes finishing evaluation-pack tooling, preparing White Hmong/RPA
collection and review instructions, checking the existing registered models
locally, and researching a Hmong voice or adaptation route. The initial task authorized no
commit, push, publication, deployment, new candidate weights, recruitment,
recording, or training. The owner subsequently authorized committing and
pushing these preparation changes to the active branch. The other exclusions
remain in effect.

Completed local results and exact gaps are in
[project status](../PROJECT_STATUS.md) and the
[new validation report](../reports/validation/evaluation_preparation_validation.md).
The [pack guide](hmong_evaluation_pack.md),
[human handoff](hmong_collection_review.md), and
[voice decision plan](hmong_voice_decision.md) are ready for owner review.
The owner confirms there is no real pack yet. Blank external slots remain
pending; no language or permission decisions are inferred from validation.

The immediate human action is preparing and independently reviewing 20
development and 10 held-out sentences and their permissions outside Git.
The broader community charter below remains proposed; these materials neither
claim participant agreement nor close the native-validation register.

## Completed M7 baseline

| Item | Completed result |
|---|---|
| Release commit | [`e4ebfad89383522c26d64a00563a44afe1aab5ba`](https://github.com/benjainnsthao/hmong-tts/commit/e4ebfad89383522c26d64a00563a44afe1aab5ba) |
| Branch | `rescope/audited-tts-workbench`; local/remote HEAD matched at completion |
| Approved candidate SHA-256 | `19c700ebb04a7f3afc70fd1af8707a990f6390758d1e67d82a760ba9d2b02447` |
| Owner decision | Corrected candidate and residual risks approved for `release` on 2026-09-11 UTC; conversational approval, not a cryptographic signature |
| Committed validation | 37 core checks; 268 tests, 83.10% aggregate branch-aware coverage; 77 focused service tests, 96.65% coverage |
| Packages | Clean ordinary/worktree wheels and sdists matched approved archives byte for byte; Git metadata excluded; privacy checks passed |
| CI | [Completed successfully for the release commit](https://github.com/benjainnsthao/hmong-tts/actions/runs/34558588222) |
| Git boundaries | M5/M6 and the first M7 commit remain ancestors; local/remote main remained at the protected historical commit; preservation branch remained absent |
| Publication | Normal active-branch push completed; no tags, packages, GitHub release, pull request, merge, or deployment |

The [owner approval](m7_owner_approval.json),
[decision record](m7_release_decision.md),
[candidate manifest](../reports/validation/m7_candidate_manifest.json), and
[validation report](../reports/validation/m7_release_validation.md) are the
reviewed M7 records. Final committed-state and push evidence is retained under
the external artifact root at
`m7/20260910T122457Z/correction-20260910T232407Z/committed/`, including
`final-handoff.json`. The original failed sdist remains private evidence.

M7's manifest verifies the exact release checkout. Later documentation changes
are outside that approved candidate; do not regenerate its manifest or revise
its approval to imply retrospective acceptance of new files. Future release
candidates need their own identity and applicable validation. Preserve M1–M6
reports, M7 review records, and the deferred native-validation record.

## 1. Maintain the completed release and its evidence

Owner: **benjainnsthao**. Next risk review: **2026-12-09**, or sooner for a
material security, dependency, licensing, or provenance issue.

- Retain M6/M7 raw evidence through that review and until material audit issues
  are resolved, following the [artifact policy](../artifacts/README.md).
  Keep caches, environments, checkpoints, raw prompts/source material, audio,
  and detailed reports outside Git. Do not publish the failed archive.
- At review, revisit every item in the [risk register](release_risk_register.md),
  refresh relevant primary sources/advisories, and record evidence, owner,
  scope, disposition, and the next review date. Accepted risks remain bounded
  by the approved use; they are not permanent waivers.
- If a material issue requires a correction, obtain authorization for that
  work, preserve the current release, and validate the affected contracts and
  packages before proposing a new candidate. Do not silently change checkpoint
  revisions, dependencies, QC thresholds, or the distribution boundary.

Completion evidence for the review: a dated risk review with supporting source
references and an explicit disposition of any new finding. This document does
not claim that the future review has occurred or schedule an automated job.

## 2. Decide whether repository integration or publication is needed

Owner: **benjainnsthao**. Status: optional; separate authorization required.

The active branch and exact commit already provide a reviewable reference.
If a pull request is desired, authorize its preparation/opening separately.
A review package should identify the completed release, changes from protected
main, validation evidence, permitted distribution, and limitations. Opening a
pull request does not authorize a merge or modification of protected main.

Tags, package publication, and GitHub releases are separate choices with their
own explicit authorization. Before any distribution, inspect the exact intended
archive and its license/privacy contents; use the approved scope below. No
publication is required merely to proceed with community scoping.

## 3. Authorize a bounded community scoping phase

Broader community phase: **not started**. Bounded preparation is covered by
the dated update above. The owner must authorize the broader phase, and
community participants must help define its needs and decisions.
Participant and reviewer roles are not assigned by this document.

The proposed phase should produce a reviewable charter covering:

- The community use case, intended users, and intended language/variety scope,
  established with appropriate participants rather than inferred from current
  English/Vietnamese demonstrations.
- How participation and decisions will work, including native-review roles,
  consent, compensation where applicable, and participants' ability to decline.
- A rights and privacy plan for any later prompts, recordings, data, models,
  and outputs, including access, permitted use, retention, and redistribution.
- An evidence plan for the applicable
  [NV-001 through NV-008 decisions](deferred/white_hmong_native_validation.md),
  with unresolved questions left open until supported by actual native review.
- Bounded deliverables, resources, exclusions, and criteria for deciding
  whether a language-support phase should proceed, be revised, or stop.

First decision needed: whether to authorize preparation of this charter and
what community engagement it may include. Planning authorization must specify
whether outreach is permitted; it does not automatically authorize recruitment,
recording, data collection, or execution of consent agreements. No outreach or
community work has occurred under this next-steps task.

Completion requires an owner-reviewed charter and documented community input
within the authorized scope. It does not establish Hmong capability or close
native-validation items without their required evidence.

## 4. Gate language implementation and applications on that evidence

Status: deferred; requires later explicit authorization.

After the scoping decision, a proposed language-support phase must identify
an appropriate licensed model or data/adaptation route and the native-speaker
validation it requires. Metadata/source research is now authorized as described
above. Model access beyond the current registry, language rules, recording,
training, and adaptation remain separate future work.
Do not use the English or Vietnamese checkpoints as a claimed Hmong voice.

Any later learning application must state the capability it actually depends
on and demonstrate that capability with appropriate rights and community
validation. Public deployment also needs a separately authorized security
design: the current service assumes trusted local clients, loopback is not
authentication, and active native calls are not safely preemptible.

## Boundaries carried forward

The long-term purpose remains useful speech technology for the Hmong community;
recruiters are a secondary audience. Current capabilities are reproducible local
English/Vietnamese engineering demonstrations. Runtime, structural QC, and
benchmark success establish no Hmong support or linguistic/perceptual quality.
NV-001 through NV-008 remain unchanged and unresolved.

Covered original code is Apache-2.0, including commercial reuse, under the
owner's 2026-09-10 license approval. That license does not relicense third-party
code, model weights, data, or outputs. Both registered MMS checkpoints remain
local non-commercial use only, with external, undistributed weights. Public
material is limited to covered code and permitted sanitized documentation,
configuration, tests, notices, and factual engineering evidence; consult the
[license matrix](license_matrix.md) before any proposed distribution.

The two authorized M7 commits are already complete. The owner's subsequent
instruction separately authorizes committing and pushing the preparation
changes; it does not reopen or alter the historical M7 approval. No merge,
publication, outreach, recording, training, or deployment is authorized here.
