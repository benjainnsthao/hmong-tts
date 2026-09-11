# M7 release decision record

Audit date: **2026-09-10**. Public decision owner: **benjainnsthao**.
Intended outcome: **release**, conditional on the completed technical gates,
explicit approval of this candidate and all residual dispositions, and exact
committed-state validation before the authorized active-branch push.

The actual human decision for the corrected candidate is the `release_approval`
object in [`m7_owner_approval.json`](m7_owner_approval.json). Its status remains
`pending` until new approval; no final approval, signature, or acceptance is inferred from the
implementation, the code-license choice, or the intention to release.
`preview` and `do_not_release` remain available owner outcomes. Only an
approved `release` with all gates passing completes M7 as a public-release gate.

## Candidate identity and binding method

Starting corrective-work commit:
`61e0ce5f9c7b21bd805b87f0420d9b22f2677c03`.
Completed-M6 ancestor: `32e55eed6c647fbe497e14973c768bf83f0a3a85`.
Required M5 ancestor: `fb72a5e87f9b3841d29ff4a0717546646e188422`.
Active branch: `rescope/audited-tts-workbench`.
Candidate version: **1.0.0**; MMS adapter implementation: **1.0.1**.

[`m7_candidate_manifest.json`](../reports/validation/m7_candidate_manifest.json)
is the complete review file inventory and candidate SHA-256. Reproduce it with
`python scripts/release_manifest.py`; `--write` creates a new candidate for
review. The method enumerates sorted tracked plus nonignored untracked files,
records POSIX executable modes and SHA-256 of file contents, then hashes
compact sorted-key ASCII JSON containing schema version, starting commit,
and that file list. Missing tracked files represent explicit deletions.

Two narrowly defined self-reference/approval exclusions apply:

1. The manifest itself is excluded; its digest is computed over its payload
   without the `candidate_sha256` field.
2. Only `release_approval` in `docs/m7_owner_approval.json` is normalized to JSON
   null. All its other fields, this decision statement, the risk proposals,
   source, configurations, tests, lock, notices, and evidence are bound.

After approval only that normalized object may change: it records the actual
owner statement, date, method, approved digest, selected outcome, and exact
risk-disposition mapping. No source/package payload change is authorized by
this exclusion. The approved digest must match the manifest, and every
unexcluded byte must still verify before and after the corrective commit. This is a
review identity, not a digital signature or proof of the owner's identity.

The final full Git SHA is reported after committing in the handoff. That
commit carries this decision record and the actual approval; a commit cannot
contain its own literal final SHA. Clean-checkout verification binds that SHA
to this reviewed file manifest, with the documented approval-only difference.

## Previous approval and corrective authorization

The owner approved the earlier candidate with `i approve and select release`
on 2026-09-10. Commit `61e0ce5f9c7b21bd805b87f0420d9b22f2677c03` carries that
decision. Clean-worktree validation then found an extra `.git` pointer in its
sdist containing a private absolute path. The archive remained external and
unpublished; the pointer was not committed. Other archive members and the
wheel matched the reviewed build. The initial validation failure is retained.

After being informed of the failure, the owner explicitly requested `push to
git`; only the active branch was pushed. That instruction did not complete
the failed public-release gate. The owner subsequently authorized one additional
corrective M7 commit, preserving the existing commit without rewriting history,
and explicitly required new approval of the changed candidate. These earlier
decisions are preserved outside the normalized approval field in
`previous_candidate_decisions` and `corrective_commit_authorization`.

The correction excludes Git administrative directories and pointer files from
both archive types and tests actual builds with synthetic metadata. Version
1.0.0 remains an unpublished candidate: runtime source, dependency lock, model
registry, and inference behavior are unchanged. Revalidated packages and the
documented runtime-evidence comparison support this corrected candidate;
technical correction is not a proposed acceptance of the packaging defect.

## Audience, current capability, and distribution

The long-term purpose is useful speech technology for the Hmong community.
The current release is a local reproducible TTS engineering workbench, with
registered English and Vietnamese demonstrations. Recruiters are a secondary
audience for the engineering methods and evidence.

Permitted public candidate material is original source, configuration,
tests/fakes, build/CI/reproduction scripts, original documentation, notices,
and sanitized factual engineering evidence. Covered original project code
is Apache-2.0, including commercial reuse, under the owner's authority and
conversational approval of **2026-09-10**. Existing third-party licenses,
attributions, and historical rights remain intact. No blanket retrospective
or model/data/output relicense is implied.

The two immutable MMS checkpoints remain CC BY-NC 4.0, for local
non-commercial inference only. Weights, installed dependency binaries,
training data, raw prompt/source/OCR text, generated WAVs, caches,
environments, and detailed raw reports/logs remain external and undistributed.
Outputs receive no Apache grant merely because original workbench code uses
Apache-2.0. Source attribution and the prompt's scoped legal basis are in the
[license matrix](license_matrix.md).

M7 does not establish Hmong support, linguistic correctness, pronunciation,
intelligibility, perceptual quality, or readiness for a Hmong application.
NV-001 through NV-008 remain unchanged and unresolved. Actual
community-language support requires a separately authorized phase with
community participation, appropriate licensing, and native-speaker validation.
No language, application, deployment, training, or community-data phase starts
under this decision.

## Evidence and proposed risk dispositions

The [M7 validation report](../reports/validation/m7_release_validation.md)
records measured environment/runtime/QC/benchmark/service results, required
checks, ordinary failure resolutions, privacy boundaries, and retained evidence
references. The [dependency audit](m7_dependency_audit.md) and
[license/provenance matrix](license_matrix.md) record exact primary sources,
versions/revisions, dates, rights, corrections, and remaining ambiguity.

| Risk | Proposed final disposition |
|---|---|
| REL-LIC-001 | `closed` |
| REL-LIC-002 | `accepted` |
| REL-PROMPT-001 | `closed` |
| REL-RUNTIME-001 | `closed` |
| REL-PORT-001 | `accepted` |
| REL-REPRO-001 | `accepted` |
| REL-QC-001 | `accepted` |
| REL-SERVICE-001 | `accepted` |
| REL-COMPAT-001 | `closed` |
| REL-SUPPLY-001 | `accepted` |
| REL-PRIV-001 | `accepted` |
| REL-LANG-001 | `deferred` |

Each item's unchanged acceptance criteria, affected scope, evidence, rationale,
user-facing limitation, and owner/review date are in the
[release risk register](release_risk_register.md). No release blocker is
omitted or accepted merely to close a gate.

The residual acceptance requested is limited to: non-commercial model use
with incomplete source-recording commercial clearance; one measured platform
and float32 execution; same-environment observations without cross-device
waveform/timing guarantees; structural QC without language/perceptual
validation; a trusted-local-client service without authentication, total
resource quotas, or active-call preemption; and dated upstream/dependency
availability, metadata, native-runtime, and undiscovered-vulnerability risk.
The audit also found a personal-provider email identity in existing Git
author/committer metadata across 14 prior commits. It is absent from candidate
file contents and is not reproduced here. Preserved history keeps that address
visible; approval of the public owner handle does not authorize that disclosure.
The owner explicitly accepted this existing exposure for the previous candidate.
That decision is preserved; the changed candidate asks for adoption of the same
bounded residual disposition. Use the already-approved verified GitHub no-reply
identity for the corrective commit, without rewriting historical commits.
If the owner does not accept continued historical visibility, `release` is
unsupported under the current no-rewrite constraint; choose `preview` with an
explicit restricted audience or `do_not_release`. This finding is not removed
from the record or relabeled as a clean history scan.

White Hmong/community work is explicitly deferred with the future trigger above.

Next risk review: **2026-12-09**, sooner for a material security, dependency,
licensing, or provenance issue. Retain external M6/M7 evidence through that
review and until material audit issues are resolved; deletion/publication
requires an explicit owner choice under the applicable rights.

## Statement submitted for the owner's named approval

The owner is asked to approve this complete statement with the concrete digest
shown in the candidate manifest and choose `release`, `preview`, or
`do_not_release`:

> As benjainnsthao, I approve the identified M7 candidate, the distribution and
> capability scope in this decision record, and each proposed risk disposition
> in the reviewed register. I accept only the stated residual limitations and
> explicitly accept the already-present historical commit-email exposure and
> the proposed no-reply identity for the new commit. I confirm the White Hmong/
> community-work deferral. I select the stated final
> outcome, with next review on 2026-12-09 or sooner for a material issue.

The owner's actual response is transcribed accurately into the approval record;
no one signs on the owner's behalf. The roadmap's signed-decision requirement
is handled by the owner's explicit named conversational sign-off, identified
as such, with no invented cryptographic signature. Licensing approval alone
is insufficient. Any requested content change requires affected validation and
review of a new digest before approval.

After approval: create the one additional authorized commit with message
`fix: exclude Git metadata from M7 release packages`, validate that exact
committed tree in a clean ordinary checkout and a Git worktree, and normally
push only the active branch. Any post-commit validation failure or upstream
divergence triggers a stop without pushing; no further corrective commit or
history rewriting is authorized. No merge, tag, package publication, GitHub
release, deployment, or pull request is authorized.
