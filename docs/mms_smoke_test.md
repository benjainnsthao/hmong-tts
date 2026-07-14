# Pinned MMS inference smoke test

This path verifies model download, pinned provenance, tokenizer/model loading,
deterministic inference, finite samples, and a valid mono WAV. It does not test
White Hmong pronunciation or authorize recording/training.

## Preconditions

- x86-64 Ubuntu 24.04, preferably WSL2 on the RTX 4070 machine;
- NVIDIA Windows driver exposing the GPU to WSL (`nvidia-smi` works in WSL);
- Python 3.12, Git, and `uv` 0.11.x;
- absolute external `HMONG_TTS_DATA_ROOT` with private storage;
- explicit approval for the multi-gigabyte PyTorch/CUDA dependency install and
  approximately 145 MB per MMS safetensors checkpoint.

The two eligible model revisions and CC BY-NC 4.0 terms are recorded in
`docs/license_matrix.md`. Do not substitute a branch name or another checkpoint.

## Commands on the target machine

```bash
export HMONG_TTS_DATA_ROOT=/absolute/private/hmong-tts
uv sync --frozen --extra mms
uv run hmong-tts-env --require-training \
  --output reports/validation/environment-target.json
uv run hmong-tts-mms-smoke \
  --model facebook/mms-tts-eng \
  --device cuda \
  --output smoke/mms-eng.wav
```

`--output` is resolved below `HMONG_TTS_DATA_ROOT`; repository WAV output is
rejected. The English prompt is a punctuation-free version of the official
Transformers documentation example and is not a White Hmong validation case.

For the Vietnamese candidate, provide an independently sourced/reviewed UTF-8
Vietnamese prompt outside Git; the tool intentionally invents none:

```bash
uv run hmong-tts-mms-smoke \
  --model facebook/mms-tts-vie \
  --text-file "$HMONG_TTS_DATA_ROOT/smoke/vie_prompt.txt" \
  --device cuda \
  --output smoke/mms-vie.wav
```

Pass evidence is the command’s `PASS` line plus the environment JSON. Listen
only for gross runtime corruption; no cross-language quality conclusion is made.

## Current machine result

On 2026-07-14, preflight is blocked: Windows and WSL are ARM64, no RTX 4070 or
NVIDIA driver is visible, and PyTorch/CUDA are absent. The large optional extra
was therefore not downloaded. See `reports/validation/phase0-validation.md`.
