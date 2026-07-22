# Project status

Last updated: 2026-07-21

## Current milestone and phase

- Milestone: **M0 Governance and reproducible environment — complete**
- Phase: **Phase 0 — complete**
- Gate state: all repository/privacy/config/test/provenance requirements pass;
  pinned English MMS inference produced a validated external WAV on the intended
  x86-64 WSL2 RTX 4070 machine on 2026-07-21.
- Phase 1: **not started**; consent, native validation, and recording-readiness
  work require separate authorization.

## Phase 0 completion checklist

- [x] Professional initial Git repository and plan-aligned structure exist.
- [x] `HMONG_TTS_DATA_ROOT` is required, absolute, and enforced outside Git.
- [x] `.gitignore`, pre-commit, CI, magic-byte, credential, PII-pattern, consent,
  and external known-identifier privacy checks exist and pass.
- [x] Python 3.12 project, pinned `uv` version, frozen `uv.lock`, default dev
  group, and explicit platform-gated MMS dependency extra exist.
- [x] Windows and Linux/WSL bootstrap paths are documented; PowerShell bootstrap passes.
- [x] Environment detection covers Python, OS/WSL, Git, FFmpeg, CUDA toolkit,
  NVIDIA driver/GPU, PyTorch CUDA, RTX 4070 identity, and VRAM visibility.
- [x] Strict data/model/training/evaluation/inference configs parse.
- [x] Blank non-PII consent template covers all required independent choices,
  is labeled project documentation/not legal advice, and keeps completed records external.
- [x] Recording-readiness gate covers consent, privacy, recording, naming,
  backups, checksums, fatigue, native review, and dry-run exit.
- [x] Speaker-role document preserves one training voice and independent evaluation.
- [x] Base/alternative model licenses, revisions, lineage limits, output caution,
  and redistribution status are recorded from current primary sources.
- [x] Pinned MMS smoke implementation and exact target commands exist; outputs
  are forced below the private root.
- [x] Actual pinned English MMS checkpoint synthesis produced a validated mono
  16 kHz PCM WAV on the intended x86-64 RTX 4070 WSL2 environment.
- [x] 27 synthetic unit tests pass; no real data is used.
- [x] Privacy, configs, lint, format, strict typing, and ordinary tests pass.
- [x] No real speaker data, completed consent, identity, private rating,
  credential, or checkpoint is present.
- [x] Validation evidence is recorded in `reports/validation/`.

## Completed deliverables

- Repository/bootstrap/lock/CI/pre-commit foundation.
- Private path API and automated privacy scanner.
- Typed versioned starter configurations preserving authoritative thresholds.
- Consent, privacy, threat, recording-readiness, speaker-role, architecture,
  model-card, and dataset-statement documentation.
- Decision log, model/license matrix, and native-validation register.
- Cross-platform environment diagnostics and pinned MMS smoke CLI.
- Pull-to-validation RTX 4070 machine handoff with explicit pass evidence.
- Target-hardware validation with CUDA-enabled PyTorch, pinned English MMS
  synthesis, and external environment/WAV evidence.
- Synthetic unit suite and Phase 0 validation report.

## Active work

Phase 0 is complete. Phase 1 has not started.

## Failed checks

- Historical MMS preflight on the original Windows context: expected failure
  (not Linux, ARM64, dependencies absent).
- Historical MMS preflight on the original WSL2 context: expected failure
  (ARM64, dependencies absent).
- The historical hardware limitation was resolved by successful execution on
  the intended x86-64 WSL2 RTX 4070 machine on 2026-07-21.
- No unresolved ordinary repository check failure. Initial formatting, typing,
  and dependency-group issues were fixed and revalidated.

## Open blockers

- **P1-CONSENT-001:** signed participant consent is required before any dry-run
  or production recording; completed record must remain outside Git.
- **P1-NV-001:** NV-001 through NV-008 require the two native speakers before
  language inventory, prompts, normalizer rules, or evaluation equivalences.
- **LICENSE-001:** project code-license selection requires owner approval before
  public redistribution; current state grants no license.

## Closed blockers

- **P0-HW-001 (closed 2026-07-21):** the intended x86-64 WSL2 RTX 4070
  environment passed CUDA-enabled PyTorch validation and the pinned English MMS
  inference gate.

## Human actions required

Before any recording, review/adapt and sign the private copy of
`docs/templates/consent_template.md`, resolve the applicable native-validation
items with both speakers, and complete Gates A–D of
`docs/recording_readiness_checklist.md` outside the repository.

## Next executable task

After separate authorization, begin only consent/native-validation and
recording-readiness work: complete the private consent process, resolve NV-001 through
NV-008 with the two speakers, and complete recording-readiness Gates A–D. No
dry-run or production recording may begin until signed consent and every
applicable readiness gate pass.

## Open native-validation items

**[NV]** NV-001 target variety; NV-002 orthographic/token inventory; NV-003
punctuation/casing/segmentation; NV-004 numbers; NV-005 abbreviations; NV-006
variants/names/borrowings; NV-007 inventory/prompt coverage; NV-008 evaluation
equivalences and provisional thresholds. No language rule has been invented.
