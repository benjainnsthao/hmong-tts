# White Hmong evaluation pack

The target is **White Hmong (Hmoob Dawb)** written in **Romanized Popular
Alphabet (RPA)**. The intended eventual use is public, noncommercial speech
generation. This workflow is for a willing recording speaker and a separate
fluent pronunciation reviewer. Willingness or availability does not establish
documented recording or publication permission.

Prepare a fixed, human-reviewed sentence pack to evaluate candidate voices
before committing to substantial recording or training. Start with a collection
target of **20 development sentences and 10 held-out sentences**. Ordinary
validation permits small pending drafts; `--require-target-shape` checks the
30-case collection target separately from `--require-reviewed`.
This work does not establish Hmong model support or approve any deferred
[native-validation decisions](deferred/white_hmong_native_validation.md).

As of **2026-09-25**, the owner confirms that no real pack exists. No sentence,
participant decision, permission, or human review has been supplied here. Use
the [collection and review handoff](hmong_collection_review.md) for the proposed
coverage allocation, blank record fields, role instructions, and freeze checks.
The [candidate research and decision plan](hmong_voice_decision.md) describes
the later experiment; no candidate access or training is authorized by this guide.

## Preparation workflow

1. The speaker and independent reviewer agree on the target variety and RPA
   conventions, then supply actual Hmong examples. Include everyday language,
   reviewer-chosen tone and pronunciation contrasts, and basic punctuation
   such as sentence endings, questions, and pauses. The reviewer determines
   whether each example is natural, meaningful, and useful for evaluation;
   this guide supplies no Hmong sentences or linguistic rules.
2. Assign opaque case IDs and retain source and permission-tracking records
   outside Git. Keep participant identities and any completed permission
   documents in those separate records. Document permissions for the relevant
   text, recording, and eventual public use before the corresponding activity.
   Willingness, noncommercial intent, and a populated reference are not grants
   of permission. A permission reference may identify an unresolved tracking
   record; it does not mean permission has been obtained.
3. The speaker checks intended readings and the independent fluent reviewer
   reviews the exact sentences, pronunciation expectations, contrasts, and
   punctuation. Record decisions and revisions externally. Keep each case
   `pending` until its human review is complete. Only humans decide approval;
   after their approval, record `reviewed` with the external review reference.
   Any later text change requires renewed review and updated records.
4. Assign development and held-out splits before comparing candidate voices.
   Use development cases for iteration. Reserve held-out cases for final
   evaluation; do not use them for training, tuning, repeated model selection,
   or choosing diagnostic rules after seeing model errors. Humans must also
   check for paraphrases and near duplicates across the splits.
5. Run ordinary validation during preparation, then both final-pack flags when
   the human-reviewed pack is ready to freeze. Retain the exact pack, its
   sanitized summary, and matching review records externally so future
   evaluations can use the same sentences. Reconcile each text hash with the
   exact version humans reviewed. No recording or synthesis is part of this
   preparation command.

## File format

Use a UTF-8 JSON object. Unknown fields are rejected at both levels. Duplicate
JSON object keys, nonstandard numeric constants, and values of the wrong type
are also rejected; values are not coerced.

| Top-level field | Required value |
|---|---|
| `schema_version` | Integer `1` |
| `target_variety` | `"White Hmong (Hmoob Dawb)"` |
| `writing_system` | `"RPA"` |
| `intended_use` | `"public_noncommercial"` |
| `cases` | Nonempty list of case objects |

| Case field | Requirement |
|---|---|
| `id` | Unique, nonempty string; use an opaque, non-sensitive label |
| `text` | Exact human-supplied sentence, as a nonempty string |
| `split` | `"development"` or `"held_out"` |
| `category` | `"everyday"`, `"tone"`, `"pronunciation"`, or `"punctuation"` |
| `source_reference` | Nonempty opaque reference to an external source record |
| `permission_reference` | Nonempty opaque reference to an external permission record or tracking record |
| `review_status` | `"pending"` or `"reviewed"` |
| `review_reference` | Nonempty external review-record reference when reviewed; omit or use `null` when pending |

All nonempty strings must contain a non-whitespace character and be encodable
as UTF-8. References identify records; do not embed participant identities or
completed permission documents in the pack. IDs appear in summaries, so do not
use sentences, private references, or participant names as IDs. The validator
cannot determine whether an ID or reference contains private information.

The structural JSON schema is available through
`tts_workbench.evaluation.prompt_set.PromptSet.model_json_schema()`. The loader
also checks unique IDs and exact text separation across splits. There are no
minimum category quotas or required counts per split in ordinary validation.
Identical text within one split is permitted during preparation; identical
text across development and held-out is always rejected. The optional target
gate requires exactly 20 development and 10 held-out cases, distinct exact
texts within each split, and all four category labels in each split. Labels
do not prove actual linguistic coverage; humans still check near duplicates.

## Offline validation

In the existing project Python environment, run:

```bash
python -m tts_workbench.evaluation.prompt_set validate \
  --input /absolute/external/path/evaluation.json

python -m tts_workbench.evaluation.prompt_set validate \
  --input /absolute/external/path/evaluation.json \
  --require-reviewed --require-target-shape
```

Keep real prompts, source records, permission records, and review records
outside Git and release packages, following the
[external artifact policy](../artifacts/README.md). The command requires an
absolute input path outside Git checkouts and exported workbench trees. Both
lexical and resolved ancestors are checked, including worktree `.git` files
and symlinks into a checkout. This is a local guard, not protection against a
concurrent filesystem change, hard links, or later copying a file into Git.
It does not require an artifact-root environment variable, fetch references,
download models, import optional ML libraries, use a GPU, or generate audio.
No package entry point or production inference behavior is changed.

Success exits `0` and prints deterministic JSON containing the total case
count, counts by split, review status, and category within split (including
zero counts), and each case ID with its `text_sha256`, in input order. It also
prints `pack_sha256`, which binds the validated metadata, case ordering, split
assignment, references, review status, and exact text. This hashes UTF-8 JSON
from `model_dump(mode="json")`, with sorted keys, no extra separator spaces,
and `ensure_ascii=False`; omitted optional fields use their validated defaults.
It is independent of source JSON formatting. Retain the summary externally
and reconcile it with the human records; a changed fingerprint is not
automatically an approved new version. Validation errors exit `2`,
write sanitized diagnostics to stderr, and produce no summary. Case diagnostics
use zero-based indices and field names; unknown field names are redacted.
Malformed JSON reports a line and column when available. Raw sentences,
reference values, and input paths are not printed. The input file is never
modified on success or failure.

Text is preserved exactly as decoded from JSON: no trimming, case folding,
Unicode normalization, transliteration, spelling correction, tone-marker
removal, or number expansion. Hashes are SHA-256 of those exact UTF-8 text
bytes, not of the JSON file. Different JSON escape spellings of the same
decoded string produce the same hash; changes in decoded whitespace or Unicode
representation can produce different hashes. Hashes are fingerprints, not
anonymization or proof of human approval.

The validator checks structure and recorded metadata only. It cannot detect
paraphrases, judge correct Hmong or pronunciation, measure speech quality, or
verify the existence or truth of review and permission references. Passing
`--require-reviewed` means all cases claim completed review with references;
it does not establish linguistic approval or legal permission. Likewise,
`--require-target-shape` proves counts and labels only. Neither flag verifies
record existence, reviewer independence, permission scope, or authenticity.

The current English/Vietnamese dashboard trims outer whitespace and uses
model-specific tokenizers. It is not an exact-text Hmong evaluation runner.
A future candidate runner must compare the approved text hash at input,
record any model preprocessing, and have fluent reviewers assess its effect
before making a White Hmong capability claim.

The next human step is **preparing and reviewing the real sentence pack** with
the willing speaker and separate fluent reviewer, retaining the pack and its
records outside Git.
