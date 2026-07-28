# Registry-pinned MMS inference smoke test

This retained path verifies optional dependency availability, audited registry
lookup, tokenizer/model loading at an immutable revision, seeded inference,
finite samples, and a valid mono WAV outside Git.

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
uv run tts-workbench-mms-smoke \
  --model mms-eng \
  --device cuda \
  --output smoke/mms-eng.wav
```

The built-in English input is a project-authored synthetic runtime fixture. It
is not a pronunciation or language-quality evaluation prompt.

## Vietnamese external-prompt policy

The workbench contains no invented Vietnamese text. A future authorized run
must provide a public prompt with independently reviewed license/provenance:

```bash
uv run tts-workbench-mms-smoke \
  --model mms-vie \
  --text-file "$TTS_WORKBENCH_ARTIFACT_ROOT/smoke/audited-vie-prompt.txt" \
  --device cuda \
  --output smoke/mms-vie.wav
```

The current smoke CLI does not yet create a complete prompt/run manifest; that
belongs to the reusable inference-adapter milestone.

## Historical evidence

The 2026-07-21 Phase 0 run validated the same pinned English checkpoint revision
on an x86-64 WSL2 RTX 4070. That evidence remains unchanged in
`reports/validation/phase0-validation.md`. The rescope milestone performs no
new model download or synthesis.
