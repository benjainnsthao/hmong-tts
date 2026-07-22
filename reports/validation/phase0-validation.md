# Phase 0 validation report

Initial validation date: 2026-07-14
Target-hardware closure date: 2026-07-21
Milestone: M0 Governance and reproducible environment
Data: synthetic fixtures, a pinned public English MMS checkpoint, and an
external generated English smoke WAV; no speaker data

## Environment

Two machine-readable reports were generated without host/user names:

- `reports/validation/environment-current.json`: managed CPython 3.12.13 on
  Windows ARM64; Git and pinned `uv` available; external test data root valid;
  FFmpeg, NVIDIA/CUDA, RTX 4070, and PyTorch absent.
- `reports/validation/environment-wsl-current.json`: Ubuntu 24.04.3 WSL2 on
  `aarch64`, Python 3.12.3 and Git available; `uv`, FFmpeg, NVIDIA/CUDA, RTX
  4070, and PyTorch absent.

The empty validation roots were in the OS temporary directory and `/tmp`; they
are not approved recording storage.

### Target-hardware closure on 2026-07-21

Windows PowerShell confirmed that the selected Ubuntu distribution was running
under WSL version 2. Inside that distribution, `uname -m` reported `x86_64`, and
`nvidia-smi` reported an NVIDIA GeForce RTX 4070 with 12,282 MiB VRAM.

The pinned `uv` 0.11.28 bootstrap and frozen MMS synchronization passed. The
external environment report recorded Python 3.12.3, Git and FFmpeg available,
PyTorch 2.12.0+cu130 with CUDA available, the expected RTX 4070 present, no
training failures, and `training_ready: true`. The standalone CUDA toolkit was
not available; this did not prevent the locked CUDA-enabled PyTorch build from
passing the training-readiness gate. Review confirmed that the report contains
no private path, username, hostname, IP address, credential, or unexpected
identifying information.

## Commands and results

| Command | Result |
|---|---|
| `python -m uv lock` | PASS; Python 3.12 environment and 82-package universal lock resolved, including platform-gated MMS extra |
| `scripts/bootstrap.ps1` | PASS; frozen sync, pre-commit install, config check, privacy scan, and all tests completed |
| `python -m uv run hmong-tts-config-check` | PASS; data, model, train, eval, inference schema v1 parsed |
| `python -m uv run hmong-tts-privacy-scan` | PASS; 70 Git candidate files, zero findings |
| `python -m uv run ruff check .` | PASS |
| `python -m uv run ruff format --check .` | PASS; 23 Python files formatted |
| `python -m uv run mypy src` | PASS; strict mode, 12 source files |
| `python -m uv run pytest --cov=hmong_tts --cov-report=term-missing` | PASS; 27 synthetic tests, 52% branch-aware aggregate coverage |
| `python -m uv run hmong-tts-env --require-data-root --output reports/validation/environment-current.json` | PASS; external root accepted and no absolute root emitted |
| `HMONG_TTS_DATA_ROOT=<repo> python -m uv run hmong-tts-env --require-data-root` | EXPECTED FAIL; repository-local data root rejected |
| Windows `python -m uv run hmong-tts-mms-smoke --preflight-only` | EXPECTED FAIL; not Linux, ARM64, MMS dependencies absent |
| WSL `PYTHONPATH=src python3 scripts/smoke_mms_inference.py --preflight-only` | EXPECTED FAIL; ARM64 and MMS dependencies absent |

### Target-hardware commands and results

| Command | Result |
|---|---|
| PowerShell `wsl --status` and `wsl -l -v` | PASS; Ubuntu running under WSL version 2 |
| Ubuntu `uname -m` and `nvidia-smi` | PASS; x86_64 NVIDIA GeForce RTX 4070 with 12,282 MiB VRAM |
| `bash scripts/bootstrap.sh` | PASS; pinned `uv` 0.11.28, frozen core sync, configuration/privacy checks, and 27 synthetic tests |
| `uv sync --frozen --extra mms` | PASS; locked MMS and CUDA-enabled PyTorch environment synchronized |
| `uv run hmong-tts-env --require-training --output <redacted-private-root>/runs/phase0/environment-target.json` | PASS; `training_ready: true`, CUDA-enabled PyTorch, expected RTX 4070 present, no training failures |
| `uv run hmong-tts-mms-smoke --model facebook/mms-tts-eng --device cuda --output smoke/mms-eng.wav` | PASS; pinned revision, 16 kHz, 33,280 samples |
| `ffprobe` on `<redacted-private-root>/smoke/mms-eng.wav` | PASS; mono PCM signed 16-bit little-endian WAV, 16 kHz, 2.080000 seconds |

Accepted MMS evidence:

```text
PASS model=facebook/mms-tts-eng revision=c71de0fe7204c83f1c10820a7d696d0b450048ba rate=16000 samples=33280 output=<redacted-private-root>/smoke/mms-eng.wav
```

Exact `ffprobe` result:

```text
codec_name=pcm_s16le
sample_rate=16000
channels=1
duration=2.080000
```

Validated repository commit:

```text
246cda2a529237932fdb5621032e85ca503bdcb9
```

## Privacy and boundary coverage

Synthetic unit tests verify rejection of WAV/FLAC/model extensions, renamed WAV
magic bytes, completed-consent names, email/phone/SSN patterns, AWS/Hugging Face
token patterns, external known identifiers, repository-local roots, relative
roots, and output path escape. Clean synthetic text and an external root pass.

Manual negative validation confirmed that setting `HMONG_TTS_DATA_ROOT` to the
repository fails closed. No real audio, speaker identity, completed consent,
private evaluation, checkpoint, or credential was used or found.

## Initial failures and resolutions

- Format check initially reported 22 unformatted Python files; `ruff format .`
  corrected them and the final check passes.
- Initial strict typing found float-literal annotations, optional ML imports,
  missing YAML stubs, and one abstract schema attribute. Thresholds now use an
  exact-value Pydantic validator, optional modules have scoped type settings,
  YAML stubs are locked, and config reporting uses validated dumps. Final mypy passes.
- Initial `uv sync` found that the development set was declared as an optional
  extra while configured as a default group. It is now a PEP 735 dependency
  group; frozen bootstrap passes.

## Model and license evidence

Primary-source/API checks on 2026-07-14 recorded immutable revisions for the
MMS collection, Vietnamese and English inference checkpoints, fine-tuning
recipe, and every alternative in `docs/license_matrix.md`. The pinned MMS list
contains `eng` and `vie` and contains no exact `mww`, `hnj`, or `hmn` entry.
Both selected MMS initializations are CC BY-NC 4.0; no commercial or weight
distribution permission is inferred.

## Resolved target-hardware gate

The 2026-07-14 ARM64/no-GPU results remain historical evidence explaining why
the target-hardware gate could not be completed in the original execution
contexts. On 2026-07-21, the intended x86-64 WSL2 RTX 4070 machine passed the
locked environment validation and generated the accepted pinned English MMS
WAV. P0-HW-001 is resolved, and Phase 0 is complete.

The WAV, environment report, and Hugging Face/model cache remained below the
approved private root and outside Git. The target-hardware execution used no
speaker data and performed no recording, training, Vietnamese or White Hmong
inference, credential creation or configuration, Phase 1 work, status-file
update, commit, or push. This documentation closure did not regenerate or alter
the accepted external evidence.
