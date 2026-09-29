# White Hmong evaluation pack

The target is **White Hmong (Hmoob Dawb)** written in **Romanized Popular
Alphabet (RPA)**. The intended eventual use is public, noncommercial speech
generation. Published, licensed text supplies the draft; a separate fluent
reviewer still decides language acceptance. New recordings are not a
prerequisite for preparing sentences or evaluating an eligible existing voice.

Prepare a fixed, human-reviewed sentence pack to evaluate candidate voices
before committing to substantial recording or training. Start with a collection
target of **20 development sentences and 10 held-out sentences**. Ordinary
validation permits small pending drafts; `--require-target-shape` checks the
30-case collection target separately from `--require-reviewed`.
This work does not establish Hmong model support or approve any deferred
[native-validation decisions](deferred/white_hmong_native_validation.md).

As of **2026-09-28**, external **draft v2 contains 20 development and 10 held-out
cases**, selected from 136 collected items (53 with retained published meanings).
The source collections are Wiktionary (14), Clark's licensed linguistic study
(8), and Tatoeba (8). Original source snapshots, licenses, access dates,
attributions, meanings, transcription notes and per-text hashes stay external.
The full draft passes the unchanged target-shape validator and the source audit;
all 30 review fields remain **pending**. It is **not frozen for final evaluation**.

The current local task permits research, preparation and bounded experiments
when prerequisites clear. The [voice decision](hmong_voice_decision.md) records
why zero candidates currently qualify. The [review handoff](hmong_collection_review.md)
consolidates the remaining decisions. The September 25 blank draft is retained
as historical preparation, not the current pack.

Current external root: `/root/tts-workbench-artifacts/white-hmong-20260928/`.
The master is `custodian/draft-v2.json`, with `draft-v2-evidence-v2.json` and its
summary beside it. Development operators receive only
`development/development-v1.json` and `development-v1-evidence-v3.json`.
The reserve is `custodian/held-out-v2.json`. The full pack SHA-256 is
`36ac5a2023b19843aa52e26f70c45a426b238bf32711e7d5a886bde5de83bc8e`.
Draft v1 and its evidence remain preserved; v2 replaces one reserve example
to include an absent `-m` marker, before any candidate outputs existed.

## Preparation workflow

1. Start with published White Hmong/RPA examples with explicit reuse terms and
   meanings. Preserve exact original text, source version and license evidence.
   Use established orthographic references; do not reopen RPA conventions or
   ask a speaker to invent every sentence. Record specific ambiguities,
   transcription issues and variety differences for fluent review. Category
   labels are proposed coverage, not a validated contrast inventory.
2. Assign opaque case IDs and retain source and permission-tracking records
   outside Git. Keep participant identities and any completed permission
   documents in those separate records. Document permissions for the relevant
   text, recording, and eventual public use before the corresponding activity.
   Willingness, noncommercial intent, and a populated reference are not grants
   of permission. A permission reference may identify an unresolved tracking
   record; it does not mean permission has been obtained.
3. A fluent reviewer reviews the exact sentences, published meanings,
   pronunciation expectations, contrasts, and
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
| `text` | Exact sourced or contributed sentence, as a nonempty string |
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

## Published sources and language checks

[Martha Ratliff's White Hmong vocabulary](https://wold.clld.org/vocabulary/25)
explicitly describes RPA, final tone letters, nasal-vowel spelling and variable
hyphen/word-spacing conventions. [Clark's publisher edition](https://openresearch-repository.anu.edu.au/bitstreams/71c4c413-61b7-4dd3-a5b8-73e61c9e11a8/download)
identifies its variety scope and licenses the chapter CC BY-SA 4.0 (p.175).
Eight examples were transcribed from page images; the original PDF and OCR are
retained. Gloss-alignment spacing becomes single lexical spaces, explicitly
recorded as transcription, with printed spelling and punctuation preserved.
Separately attributed quotations and other-language examples were not selected.

Wiktionary examples are original usage-example elements under
[Wikimedia's content terms](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use#7._Licensing_of_Content),
with permanent revision links and CC BY-SA 4.0 attribution. Its lexical entries
often share Heimbach/Ratliff sources; they are not independent reviews.
[Tatoeba's text terms](https://tatoeba.org/en/terms_of_use#section-6) and each
selected page specify CC BY 2.0 FR. Original contributor attribution was recovered
from the public logs despite current ownership being unset. No source audio was
downloaded. Thirty local-synthesis records are license-supported; public audio,
service, voice and model rights still require separate reconciliation.

Nine development lexical comparisons and the RPA-reference comparisons are
retained in `development/language-checks.json`. They support word senses and
spelling interpretation, not complete sentence or pronunciation acceptance.
Both splits contain candidate final letters `b/j/v/s/g/m` and unmarked forms.
Neither contains `-d`; there is no independently validated minimal-tone-pair
inventory. This is an explicit coverage question for the reviewer, not a claim
that a marker count proves phonetic coverage. Suspect source spelling, fragments
and unverified translations remain excluded in the candidate inventory.

The [Google language table](https://docs.cloud.google.com/translate/docs/languages)
and current Translate UI label `hmn` as **Hmong**, without promising exclusive
White Hmong coverage. Four original development sentences were checked through
the ordinary public UI: two provisional agreements and two tense/aspect
discrepancies. Results, timestamps and snapshots remain separate from the source;
no Google-produced Hmong or back-translation was used as confirmation. The
[Cloud API requires credentials and billing](https://docs.cloud.google.com/translate/docs/setup),
so no Cloud account, billable call or integration was enabled. Future API use
requires an already authorized account/budget and explicit `hmn` to `en`
requests on permitted development text. There is no assumed Google dictionary
or accessible underlying training corpus.

## Source audit and listening preparation

The companion schema lives in `tts_workbench.evaluation.source_audit`. It binds
one source record to each exact text, source/permission reference and pack hash,
and fingerprints the evidence separately. It checks duplicate records,
normalized duplicates, heuristic near duplicates/templates, manually recorded
families and source concentration. Normalization is comparison-only and retains
tone letters; source text never changes. Heuristics cannot find every paraphrase.
Source-group labels must be opaque because they appear in the report, like pack IDs.

```bash
python -m tts_workbench.evaluation.source_audit \
  --input /absolute/external/path/draft-v2.json \
  --evidence /absolute/external/path/draft-v2-evidence-v2.json \
  --require-separated

python -m tts_workbench.evaluation.listening \
  --input /absolute/external/path/development-v1.json \
  --evidence /absolute/external/path/development-v1-evidence-v3.json \
  --output /absolute/external/path/new-listening-directory \
  --key /absolute/external/path/separate-private-key.json
```

The final audit records 44 within-split related pairs and **zero cross-split
flags**. Eighteen cases have explicit language/context flags; twelve have only
source-supported checks. All thirty still need final independent review.
The reserve is concentrated in Wiktionary (8/10); publisher counts are not
independent-author counts. Review source concentration and semantic overlap
before freezing. Published text may have appeared in model pretraining:
held-out from this project's tuning does not mean unseen by the model.

The listening command refuses held-out inputs, checkout-local paths, changed
text/WAV hashes, unresolved text permissions for clips and more than two fixed
candidate configurations. It exports native browser playback, published meanings,
attribution and blank CSV scores; random labels and the shuffle seed stay in a
separate key. `--clips` accepts a `ClipInventory` JSON with the development pack
hash and records containing candidate/configuration identity, case/text hashes,
absolute external WAV path and WAV SHA-256. Bounds are 25 clips per configuration,
50 total, and mono PCM16 at 8–48 kHz, at most 30 seconds per clip. It copies PCM
without embedded source metadata. It does not generate or assess linguistic quality.

With no eligible audio it creates a clearly labelled **awaiting audio** packet,
with zero candidates/clips and unfilled scores. The current one is
`review/listening-v2/index.html`. Source/permission checks and the proposed
rubric remain visible. No freeze or approval is inferred from generating a packet.
The directory guard is for trusted local use, not hostile concurrent filesystem
changes; mode 0700 and development-only exports do not isolate the same Unix user.
