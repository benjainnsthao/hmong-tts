# Phase 0 validation report

Date: 2026-07-14
Milestone: M0 Governance and reproducible environment
Data: synthetic fixtures and empty temporary external roots only

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

## Unresolved gate

Actual MMS waveform generation was not run because both available execution
contexts are ARM64 and expose no NVIDIA GPU/CUDA/PyTorch. Installing the large
x86-64 CUDA stack here would not make the absent RTX 4070 visible. The exact
target command and pinned revisions are in `docs/mms_smoke_test.md`.

Phase 0 independent engineering checks pass. The milestone remains blocked on
one target-hardware inference result; Phase 1 has not been advanced because the
Phase 0 inference gate is not yet closed.
