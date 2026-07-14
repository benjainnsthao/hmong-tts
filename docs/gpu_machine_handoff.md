# RTX 4070 machine handoff — next executable step

Purpose: pull this repository onto the intended graphics-card PC, validate the
target environment, and run the pinned English MMS inference smoke test that is
the only open Phase 0 engineering gate.

This step downloads a multi-gigabyte PyTorch/CUDA environment and an
approximately 145 MB MMS checkpoint. It does not use or authorize any real
speaker recording. Do not add the generated WAV, model cache, environment
secrets, or private paths to Git.

## 1. Verify Windows, WSL2, and GPU visibility

From PowerShell on the graphics-card PC:

```powershell
wsl --status
wsl -d Ubuntu -- uname -m
wsl -d Ubuntu -- nvidia-smi
```

Required result:

- WSL version 2;
- `uname -m` reports `x86_64`;
- `nvidia-smi` lists an NVIDIA GeForce RTX 4070 with approximately 12 GB VRAM.

If `nvidia-smi` fails in WSL, update/install the NVIDIA Windows driver with WSL
CUDA support. Do not install a separate Linux display driver inside WSL.

## 2. Clone or update the repository inside Ubuntu

For a first checkout:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip git ffmpeg
mkdir -p "$HOME/src"
cd "$HOME/src"
git clone https://github.com/benjainnsthao/hmong-tts.git
cd hmong-tts
git switch main
git pull --ff-only origin main
git status --short --branch
```

For an existing clean checkout:

```bash
cd "$HOME/src/hmong-tts"
git switch main
git status --short
git pull --ff-only origin main
```

Stop if `git status --short` reports unexpected local changes. Do not discard
them automatically.

## 3. Provision the external private root

Choose an absolute, access-controlled location outside the clone. Replace the
example path below with the intended encrypted/private storage location:

```bash
export HMONG_TTS_DATA_ROOT="$HOME/hmong-tts-private"
export HF_HOME="$HMONG_TTS_DATA_ROOT/cache/huggingface"
mkdir -p "$HMONG_TTS_DATA_ROOT" "$HF_HOME"
```

For later recording, confirm the underlying drive and backups satisfy
`docs/recording_readiness_checklist.md`; this smoke-only directory is not by
itself approval for speaker data.

## 4. Bootstrap and run the pre-download gates

```bash
bash scripts/bootstrap.sh
uv run hmong-tts-env --require-data-root
uv run hmong-tts-privacy-scan --require-data-root
git status --short
```

Expected result: bootstrap, configurations, privacy checks, and 27 synthetic
tests pass; the working tree remains clean except for any intentionally created
ignored `.env` file.

## 5. Install the locked MMS stack and validate CUDA

```bash
uv sync --frozen --extra mms
mkdir -p "$HMONG_TTS_DATA_ROOT/runs/phase0"
uv run hmong-tts-env \
  --require-training \
  --output "$HMONG_TTS_DATA_ROOT/runs/phase0/environment-target.json"
```

The environment command must report:

- `training_ready: true`;
- Python 3.12;
- Linux `x86_64` under WSL2;
- FFmpeg and Git available;
- CUDA-enabled PyTorch;
- `expected_rtx_4070_present: true`.

Do not continue if any requirement fails.

## 6. Run the pinned English MMS smoke test

```bash
uv run hmong-tts-mms-smoke \
  --model facebook/mms-tts-eng \
  --device cuda \
  --output smoke/mms-eng.wav

ffprobe -v error \
  -show_entries stream=codec_name,sample_rate,channels,duration \
  -of default=noprint_wrappers=1 \
  "$HMONG_TTS_DATA_ROOT/smoke/mms-eng.wav"
```

The CLI pins checkpoint revision
`c71de0fe7204c83f1c10820a7d696d0b450048ba`, rejects output outside
`HMONG_TTS_DATA_ROOT`, checks for finite samples, and reopens the generated WAV
to validate its structure.

Pass criteria:

- the CLI prints a line beginning with `PASS model=facebook/mms-tts-eng`;
- the output is mono PCM WAV at 16 kHz with positive duration;
- the model cache and WAV remain outside the repository;
- `git status --short` remains clean.

## 7. Return the Phase 0 evidence

Provide the project lead with:

1. the MMS CLI `PASS` line;
2. the `ffprobe` output;
3. `environment-target.json` after checking it contains no unexpected private data;
4. `git rev-parse HEAD`.

Do not return or commit the generated WAV, Hugging Face cache, machine username,
absolute private path, IP address, or credentials. After this evidence passes,
the engineering task is to update `reports/validation/phase0-validation.md`,
mark the MMS item complete in `PROJECT_STATUS.md`, and begin Phase 1 only up to
the signed-consent and native-validation gates.
