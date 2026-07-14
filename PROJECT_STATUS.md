# Project status

Last updated: 2026-07-14

## Current milestone and phase

- Milestone: **M0 Governance and reproducible environment**
- Phase: **Phase 0 — independent deliverables complete; target-hardware gate blocked**
- Gate state: all repository/privacy/config/test/provenance requirements pass;
  actual pinned MMS inference remains unexecuted because the available Windows
  and WSL environments are ARM64 and expose no RTX 4070/CUDA.
- Phase 1: not started; the plan forbids advancing while the Phase 0 inference
  gate is open.

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
- [ ] Actual MMS checkpoint synthesis produces a validated WAV on the intended
  x86-64 RTX 4070 WSL environment. **BLOCKED: that environment is not available here.**
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
- Synthetic unit suite and Phase 0 validation report.

## Active work

None that can safely close the current gate on this ARM64/no-GPU machine.

## Failed checks

- MMS preflight on Windows: expected failure (not Linux, ARM64, dependencies absent).
- MMS preflight on WSL2: expected failure (ARM64, dependencies absent).
- No unresolved ordinary repository check failure. Initial formatting, typing,
  and dependency-group issues were fixed and revalidated.

## Blockers

- **P0-HW-001:** intended x86-64 WSL2 RTX 4070 execution environment is not
  accessible; actual MMS inference cannot be validated here.
- **P1-CONSENT-001:** signed participant consent is required before any dry-run
  or production recording; completed record must remain outside Git.
- **P1-NV-001:** NV-001 through NV-008 require the two native speakers before
  language inventory, prompts, normalizer rules, or evaluation equivalences.
- **LICENSE-001:** project code-license selection requires owner approval before
  public redistribution; current state grants no license.

## Human actions required

Immediate Phase 0 action: make the intended x86-64 RTX 4070 WSL2 environment
available, then run the exact commands in `docs/mms_smoke_test.md` (the optional
MMS install is multi-gigabyte) and return the `PASS` line plus environment JSON.

Before recording: review/adapt and sign the private copy of
`docs/templates/consent_template.md`, then complete Gates A–D of
`docs/recording_readiness_checklist.md` outside the repository.

## Next executable task

On target hardware, install the locked `mms` extra, run
`hmong-tts-env --require-training`, synthesize the pinned English MMS smoke WAV,
inspect its header/finite samples, and attach the non-sensitive result to the
validation report. If it passes, close Phase 0 and begin Phase 1 only with
native-reviewed inventory/schema work; do not record until signed consent and
all recording gates pass.

## Open native-validation items

**[NV]** NV-001 target variety; NV-002 orthographic/token inventory; NV-003
punctuation/casing/segmentation; NV-004 numbers; NV-005 abbreviations; NV-006
variants/names/borrowings; NV-007 inventory/prompt coverage; NV-008 evaluation
equivalences and provisional thresholds. No language rule has been invented.
