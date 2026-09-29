# White Hmong collection and review handoff

**Update 2026-09-29:** development audio now exists from the locally tested
Hmong Orpheus model (research only; see the [voice decision](hmong_voice_decision.md)).
The smallest human step is the owner's five-clip quick check,
`review/quick-check/index.html` (about 10 minutes), saved as
`review/quick-check/verdict.json`. The full 20-clip packet
`review/listening-v2-audio/` is optional. That check is one listener's
judgment, not the independent fluent review described below, which is still
required before any quality claim. The rest of this handoff is unchanged.

Updated **2026-09-28**. The published-source draft is complete: 20 development
and 10 held-out cases, **zero human approvals**. The previous September 25 blank
collection remains historical evidence. No participant was contacted, no speaker
was recorded, and no participant commitment has been inferred.

The owner no longer needs to arrange authorship of thirty sentences. Start with
[this prepared pack and source evidence](hmong_evaluation_pack.md). The remaining
human work is language acceptance, specific ambiguities and eventual model rights.
Keep sentences, translations, identities, decisions and scores outside Git.

## One review packet

External root: `/root/tts-workbench-artifacts/white-hmong-20260928/`.
Open `review/REVIEW_PACKET.md` first and `review/listening-v2/index.html` for the
20 development texts, published meanings and blank score sheet. There are
**zero audio clips** because no model cleared its prerequisites. The page says
it is awaiting eligible audio; it is not a listening result.

| Decision | Prepared evidence and recommended choice | Acceptance still needed |
|---|---|---|
| Local model route | [Current shortlist](hmong_voice_decision.md): keep Orpheus as a research lead, but defer execution until its Llama terms, voice/data provenance and safe codec artifacts are resolved. F5 lacks model terms; Yuhalu requires payment/agreement. | Owner disposition of the concrete rights questions. No agreement acceptance or outreach is delegated by this task. |
| Ambiguous meanings | D04 and D09 have Google tense/aspect differences from published English glosses. Preserve both observations; assess context instead of changing Hmong spelling automatically. | Fluent judgment of the intended reading and acceptable alternatives. |
| Transcription and pronunciation | Prioritize Clark page transcriptions, D11's published loanword/number form and D12's emphatic reduplication. Retain source hyphens and record tokenizer changes in any later trial. | Independent confirmation of exact text, variety, intended reading and critical sound distinctions. |
| Coverage and split | Counts/categories pass; related families stay together; zero cross-split heuristic flags. Reserve source concentration is 8/10 Wiktionary. No selected `-d` token or independently validated minimal-tone-pair inventory. | Decide whether a source-backed replacement is needed for contextual `-d` or a specific contrast, and check paraphrases. Do not invent filler or reopen established RPA conventions. |
| Rubric | Use the proposed anchors below and reject unresolved meaning-changing errors. Agree criteria before hearing any model audio. | Actual reviewer/owner acceptance, recorded prospectively; blank decisions mean pending. |
| Final listening | No audio yet. After development review selects a fixed permitted configuration, run one final held-out pass. | A separate fluent reviewer must accept language quality; engineering QC and translation agreement cannot do so. |

All 30 exact cases still require final independent review. Priority flags reduce
repetitive investigation; they do not exempt the unflagged cases. The owner can
supply this packet privately to an existing willing fluent reviewer. This task
does not contact them or require a recording speaker to create new material.

## Coverage and custody

| Primary category | Development | Held-out |
|---|---|---|
| Everyday | 8 | 4 |
| Tone | 6 | 2 |
| Pronunciation | 4 | 2 |
| Punctuation | 2 | 2 |
| Total | **20** | **10** |

These are screening labels, not proof of a complete linguistic inventory.
Martha Ratliff's [White Hmong RPA description](https://wold.clld.org/vocabulary/25)
and [Clark's study](https://doi.org/10.15144/PL-A77.175) are the starting references.
They describe tone spellings, consonant distinctions, spacing/hyphen conventions
and contextual emphasis; different descriptions of `-d` should be interpreted
in context, not treated as evidence that established spelling needs redesign.

The protected master is `custodian/draft-v2.json`; its companion source records
are `draft-v2-evidence-v2.json`. The reserve and its meanings remain in that directory.
The operator receives only `development/development-v1.json` and
`development-v1-evidence-v3.json`. The collection operation saw source candidates
before assigning the split; no reserve text has been used for model selection,
inference or Google checks. Mode 0700 protects against other users, not processes
running as the same user. An actual human custodian and access decisions are
still unassigned. The listening tool independently rejects any held-out case.

Published sentences can occur in training corpora. This reserve is held out
from **our** tuning, not certified absent from pretraining. If its outputs later
guide tuning, retire it and obtain a fresh reviewed reserve before a final claim.

## Proposed listening rubric — human acceptance pending

Listen once without consulting the English meaning, then compare against the
published meaning and accepted variants. Score each dimension separately:

| Dimension | What to judge |
|---|---|
| Intelligibility | Is the exact sentence understandable without guessing from the gloss? |
| Tone and meaning | Are lexical distinctions and contextual tone/phonation acceptable? Identify the affected syllable and any meaning change. |
| Pronunciation | Consonants, aspiration/prenasalization, vowels, nasalization, omissions and repetitions. Accept documented regional variants. |
| Phrasing | Sentence endings, questions, pauses and emphasis match the accepted reading. |
| Naturalness | Ease of listening, rhythm and consistency, without substituting voice preference for correctness. |

Proposed common anchors: **1** major problems; **2** repeated problems;
**3** understandable with effort; **4** minor problems; **5** no noticed problems.
Add a separate critical-error/uncertainty field. A missing or failed clip stays a
failure, never a zero quality score or a silently omitted observation.

Recommended acceptance rule for review: no unresolved meaning-changing error,
no missing final cases, and fluent confirmation that each final sentence is
usable for the agreed purpose. Numeric pass thresholds remain unset until the
reviewer justifies and accepts them. Preserve independent judgments and
adjudication; do not average away a critical disagreement. These criteria derive
from the reference distinctions but have **not** been accepted by a human.

## Complete the evidence, then freeze

1. Review the exact decoded text and its hash against the published source.
   Source records already contain attribution, license, access date and meaning.
   Where transcription is flagged, compare the retained image, not just OCR.
2. Record reviewer role and independence, actual date, variety/RPA scope,
   intended meaning, accepted alternatives, coverage, approve/revise/reject/
   uncertain, and reasons. Keep private identities in a separate restricted map.
3. Keep `review_status: pending` and no review reference until actual approval.
   After approval, record `reviewed` with its real external reference. A text
   change creates a new version and renewed review; never rewrite the source.
4. Reconcile permission records separately: current text-license evidence
   supports local text synthesis subject to conditions. It does not license a
   model, voice, recordings, training, public audio or a hosted service.
5. Independently check semantic duplicates, templates, contrast families and
   source concentration, then agree the rubric before listening to outputs.
6. Run both final pack flags, verify the source/evidence fingerprints, and record
   the actual owner/reviewer freeze decisions. Structural flags only validate
   claims in records; they do not authenticate the decisions.
7. For final evaluation, freeze candidate and codec revisions, configuration,
   frontend, seed, dependency environment and rubric first. The custodian then
   releases only that final reserve pass; log all attempts and failures. Any
   change after seeing reserve errors requires a new reserve for a final claim.

No pack is frozen yet. NV-001 through NV-008 remain open. The smallest human
step is one independent review of the prepared packet, beginning with the
flagged development cases and proposed criteria; no sentence-authoring or
recording session is needed to start that review.
