# Registry-pinned MMS inference smoke test

This retained command now uses the M3 provider-neutral request, adapter,
execution, structural waveform, and atomic artifact contracts. It verifies
optional dependency availability, audited registry lookup, tokenizer/model
loading at an immutable revision, seeded inference, and a valid mono WAV plus
success manifest outside Git.

It does not test pronunciation, naturalness, language correctness, or White
Hmong support. It does not train or redistribute a model.

## Metadata-only checks

These commands require no network, weight download, PyTorch, or GPU:

```text
tts-workbench-models validate
tts-workbench-models list
```

## Optional inference preconditions

- Linux x86-64;
- the locked `mms` dependency group;
- a valid external `TTS_WORKBENCH_ARTIFACT_ROOT`;
- acceptance of the registered checkpoint license and download size; and
- explicit authorization for weight download and inference.

The canonical artifact-root variable was introduced in milestone M2. Model
caches and generated audio must stay outside Git.

## English synthetic smoke fixture

```bash
uv sync --frozen --extra mms
uv run --frozen --extra mms tts-workbench-mms-smoke \
  --acknowledge-model-access --model mms-eng \
  --device cuda \
  --output smoke/mms-eng.wav
```

The built-in English input is a project-authored synthetic runtime fixture. It
is not a pronunciation or language-quality evaluation prompt.

On success, the command creates:

```text
smoke/mms-eng.wav
smoke/mms-eng.manifest.json
```

The manifest contains the prompt's SHA-256 hash, not the prompt text. It is
published after the WAV and acts as the transaction commit marker. Reusing the
same output path is rejected rather than overwritten.

## Vietnamese external-prompt policy

The workbench contains no invented Vietnamese text. M7 revalidates the retained
M6 prompt against its official source and exact hash; follow the gate in
`m7_reproduction.md` before inference:

```bash
uv run --frozen --extra mms tts-workbench-mms-smoke \
  --acknowledge-model-access --model mms-vie \
  --text-file "${M7_LABEL}/prompts/vie-prompt.txt" \
  --device cuda \
  --output smoke/mms-vie.wav
```

The text file remains external to the repository and its contents are not
logged or copied into the manifest.

## Ordinary synthetic validation

Unit tests inject fake backends and generate WAVs only inside pytest temporary
directories. They require no optional ML dependency, CUDA device, network,
model weight, external prompt, native-language content, or real audio.

## Historical evidence

The 2026-07-21 Phase 0 run validated the same pinned English checkpoint revision
on an x86-64 WSL2 RTX 4070. That evidence remains unchanged in
`reports/validation/phase0-validation.md`. M6 and M7 separately record
authorized execution at their own versions; those runs confer no Hmong capability.
