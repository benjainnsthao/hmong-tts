# Decision records

## D-0001 — External private-data root

- Date: 2026-07-14
- Decision: all real audio, identity/consent records, private text/ratings,
  checkpoints, and generated WAV files must live below an absolute external
  `HMONG_TTS_DATA_ROOT`. Repository-local data roots and symlinks are rejected.
- Alternatives: an ignored repository `data/` directory; Git LFS; a public
  artifact store.
- Evidence: authoritative plan privacy rules and the inability of `.gitignore`
  alone to protect force-adds, history, hosted trackers, or identity mappings.
- Native-validation status: not applicable.
- Consequences: scripts fail closed without a valid root; synthetic fixtures
  are the only test data; users must provision encrypted external storage.

## D-0002 — Pinned MMS candidates remain provisional

- Date: 2026-07-14
- Decision: retain the plan’s `facebook/mms-tts-vie` primary candidate and
  `facebook/mms-tts-eng` control at immutable revisions recorded in the license
  matrix. Do not claim transfer quality; choose only through the blind pilot.
- Alternatives: choose Vietnamese without a control; choose Piper/F5/XTTS now;
  train from scratch.
- Evidence: official MMS cards expose compact 36.3M-parameter VITS inference
  checkpoints, the recipe supports generator/discriminator fine-tuning, and the
  collection has no listed `mww`, `hnj`, or `hmn` TTS entry as audited.
- Native-validation status: **[NV]** required for the eventual A/B judgment and
  all language behavior.
- Consequences: local research remains non-commercial under CC BY-NC 4.0;
  distribution is not assumed; both initializations use the identical pilot.

## D-0003 — Reproducible core versus heavyweight MMS environment

- Date: 2026-07-14
- Decision: pin Python 3.12 and `uv` 0.11.x. Keep governance/test dependencies
  in the default lock and the large x86-64 Linux MMS stack in an explicit
  optional extra.
- Alternatives: use the host Python 3.13; unpinned `pip install`; install GPU
  packages in every CI job.
- Evidence: current host is Windows ARM64/Python 3.13, WSL is ARM64/Python 3.12,
  and current official PyTorch Windows guidance lists Python 3.9–3.12 while the
  target CUDA workflow is Linux/WSL. GPU/model packages are large and not needed
  to prove Phase 0 privacy/config gates.
- Native-validation status: not applicable.
- Consequences: ordinary tests are portable; MMS installation is explicit and
  platform-gated; training requires an x86-64 CUDA-visible machine.

## D-0004 — No code-license grant before owner choice

- Date: 2026-07-14
- Decision: use the default all-rights-reserved state rather than silently
  selecting an open-source license.
- Alternatives: MIT, Apache-2.0, GPL-3.0, or another reviewed license.
- Evidence: the plan requires a license matrix but does not authorize a specific
  project code license; the operating rules reserve material licensing changes
  for the owner.
- Native-validation status: not applicable.
- Consequences: local implementation can continue; public redistribution is
  blocked until the owner explicitly selects a license.

## D-0005 — No language rules in Phase 0

- Date: 2026-07-14
- Decision: typed config records the plan’s character/lowercase baseline but
  marks normalization blocked. No White Hmong characters, tone mappings,
  number/abbreviation readings, variants, or prompts are encoded yet.
- Alternatives: infer rules from general linguistic references or another
  language’s tokenizer.
- Evidence: authoritative plan requires native approval and warns that other
  normalizers may remove meaningful final letters.
- Native-validation status: **[NV]** open items NV-001 through NV-008.
- Consequences: Phase 1 schema work may proceed, but prompts, golden cases, and
  production normalization cannot pass until native review is recorded.
