# White Hmong single-speaker TTS

Research/portfolio implementation of the consented, single-speaker MVP in
[`WHITE_HMONG_TTS_PROJECT_PLAN.md`](WHITE_HMONG_TTS_PROJECT_PLAN.md). The only
training voice is the primary speaker; the second speaker is reserved for
independent review and evaluation.

Phase 0 is complete, and Phase 1 has not started. The repository contains no
real recordings, completed consent records, speaker identity, or private
evaluation data. Language-specific choices are not implemented until
native-speaker validation is recorded.

## Bootstrap

The reproducible target is Ubuntu 24.04 under WSL2 on an x86-64 machine with an
RTX 4070. Python 3.12 and `uv` 0.11.x are pinned by `pyproject.toml` and
`uv.lock`.

```bash
sudo apt-get update
sudo apt-get install -y python3 curl git ffmpeg
cp .env.example .env
# Set HMONG_TTS_DATA_ROOT to an absolute encrypted/private path outside this repo.
bash scripts/bootstrap.sh
uv run hmong-tts-env --require-data-root
uv run hmong-tts-config-check
uv run hmong-tts-privacy-scan
uv run pytest
```

On Linux, the bootstrap installs the exact pinned `uv` release from Astral's
versioned standalone installer when needed. It does not write to the
PEP 668-managed system Python or modify shell profiles.

PowerShell setup for governance and tests is also supported:

```powershell
Copy-Item .env.example .env
# Set HMONG_TTS_DATA_ROOT to an absolute private path outside this repo.
./scripts/bootstrap.ps1
uv run hmong-tts-env --require-data-root
uv run pytest
```

Do not install the GPU/model extra until the environment report confirms
Linux x86-64, CUDA-visible PyTorch, and the expected GPU. The documented MMS
machine handoff is in
[`docs/gpu_machine_handoff.md`](docs/gpu_machine_handoff.md); implementation
details are in [`docs/mms_smoke_test.md`](docs/mms_smoke_test.md).

## Private-data boundary

All sensitive or bulky artifacts belong below `HMONG_TTS_DATA_ROOT`, which must
resolve outside the repository. See [`data/README.md`](data/README.md) and
[`docs/privacy_and_consent.md`](docs/privacy_and_consent.md). The privacy scanner
runs in tests, pre-commit, and CI and scans both tracked and untracked files.

## Current status

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md). This repository has no public-use
license yet; no permission to copy, redistribute, deploy, or distribute model
weights is granted. See [`LICENSE`](LICENSE) and
[`docs/license_matrix.md`](docs/license_matrix.md).

The next-phase sequence, terminal/outside responsibility map, and copyable
governance-only Step 1 authorization are in
[`docs/phase1_governance_handoff.md`](docs/phase1_governance_handoff.md). No
recording may begin until signed consent and recording-readiness Gates A–D pass.
