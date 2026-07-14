# Native-validation register

No row is approved. Proposed options describe review outcomes, not language
rules; the reviewers must supply the actual language evidence.

| Decision ID | Question | Proposed options | Affected code/data | Reviewer | Status | Decision date |
|---|---|---|---|---|---|---|
| NV-001 | What exact White Hmong variety, RPA conventions, and speaker-specific scope will the model document? | Approve a reviewer-written scope; revise it; reject ambiguous scope | dataset statement, model card, all prompts | `spk01` + `reviewer02` | Open | — |
| NV-002 | Which characters and multicharacter sequences are meaningful, including every tone-bearing symbol, and what must be preserved? | Approve reviewer-supplied inventory; revise; collect evidence | tokenizer vocabulary, normalizer, golden tests | `spk01` + `reviewer02` | Open | — |
| NV-003 | Which punctuation, casing, whitespace, clause boundaries, and mixed-language cases have unambiguous supported behavior? | Approve per-case behavior; reject input; mark unsupported | normalizer and API validation | `spk01` + `reviewer02` | Open | — |
| NV-004 | How are numbers, dates, times, money, measures, ordinals, and digit sequences read in each approved context? | Approve explicit context rule; reject ambiguous form; require written-out input | number normalizer and golden cases | `spk01` + `reviewer02` | Open | — |
| NV-005 | Which abbreviations are supported and are they read as a word, letters, or an expanded phrase? | Add reviewer-approved allowlist entry; reject; require full phrase | abbreviation allowlist and tests | `spk01` + `reviewer02` | Open | — |
| NV-006 | Which spelling variants, names, place names, and borrowed-word forms are accepted? | Approve mapping/reading with provenance; keep distinct; reject from public input | variants, prompts, tokenizer, evaluation equivalence | `spk01` + `reviewer02` | Open | — |
| NV-007 | Does the linguistic inventory and prompt set cover the target distinctions without invalid or unnatural examples? | Approve; revise/re-record; remove item | inventory, set-cover output, all splits | `spk01` + `reviewer02` | Open | — |
| NV-008 | Are diagnostic categories, acceptable-equivalence rules, and provisional human thresholds valid before model errors are inspected? | Freeze as proposed; revise prospectively; defer release | evaluation schemas, rubrics, scoring | `spk01` + `reviewer02` | Open | — |
