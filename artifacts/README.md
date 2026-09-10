# External artifact boundary

This repository directory intentionally contains no audio, weights, caches, or
benchmark artifacts.

`TTS_WORKBENCH_ARTIFACT_ROOT` is the canonical environment variable. It must
name an absolute existing directory outside this Git repository.

```text
$TTS_WORKBENCH_ARTIFACT_ROOT/
├── cache/models/
├── smoke/
├── runs/
│   ├── <run>.wav
│   └── <run>.manifest.json
├── qc/
│   └── <report>.json
└── benchmarks/
    └── <report>.json
```

## M3 inference transaction

Inference output paths are normalized artifact-root-relative POSIX paths and
must end in `.wav`. The paired success manifest uses the same name with
`.manifest.json`. Absolute paths, `..` escapes, repository-local roots,
symlinked roots, and existing WAV/manifest destinations fail closed.

The writer creates temporary files beside the final destinations and closes
them before replacement for Windows compatibility. It structurally validates
the WAV, computes its SHA-256 checksum, serializes the strict manifest, commits
the WAV, and publishes the success manifest last. The manifest is therefore the
transaction commit marker. If validation, serialization, or replacement fails,
temporary files and any WAV committed by that failed transaction are removed.
An existing successful run is never overwritten.

Manifests expose only artifact-root-relative paths. They do not contain the
absolute artifact root, raw prompt text, user or host identity, client
addresses, credentials, or private identifiers.

## M4 JSON report transactions

QC input WAVs and QC/benchmark output reports use normalized
artifact-root-relative paths only. Reports are serialized deterministically to
a closed temporary file beside the destination, then published by atomic
replacement. Existing destinations are rejected; there is no default
overwrite. Serialization and replacement failures remove temporary and
transaction-owned destination files, so callers never receive partial success.

QC reports contain effective thresholds, measured waveform facts, stable rule
results, and only the root-relative source WAV name. Benchmark reports contain
the prompt SHA-256, immutable registry identity, adapter/runtime/settings,
environment capabilities, timings, aggregates, and optional point-in-time
memory. Neither report contains raw prompts, absolute paths, machine/client
identity, credentials, environment values, private identifiers, cache paths,
or linguistic-quality conclusions.

Synthetic test WAVs and reports exist only under pytest temporary directories.

## M5 service transactions

The caller never supplies an artifact path. The service generates a UUID and
builds a normalized path below the configured `service/runs` prefix, then
delegates to the unchanged M3 atomic WAV/manifest transaction. A successful
HTTP response returns only root-relative WAV and manifest references.

Malformed, unknown-model, not-ready, full-queue, expired, dependency/device,
load, synthesis, waveform, boundary, collision, and write failures return no
success artifact reference. Work that expires while queued never calls the M3
executor. An in-flight operation is not force-cancelled; it either completes
the normal atomic transaction or returns a structured failure.

## Version 1.0.0 canonical-variable policy

Only `TTS_WORKBENCH_ARTIFACT_ROOT` is read. The legacy
`HMONG_TTS_DATA_ROOT` variable has no effect, including when supplied alone.
See [migration](../docs/m7_migration.md).

Missing, relative, repository-local, symlinked, nonexistent, and escaping paths
fail closed. Validation reports expose only pass/fail status and never print the
resolved absolute artifact root.

Generated audio and third-party weights must never be committed or
redistributed by this project. No private speaker data is in the active scope.

## M6 external evidence layout

M6 additionally uses these external-only subtrees:

```text
TTS_WORKBENCH_ARTIFACT_ROOT/
  cache/
    huggingface/
    torch/
    uv/
  m6/
    prompts/       official source, OCR intermediates, raw prompt
    runs/          direct WAV/manifest pairs
    qc/            full structural reports
    benchmarks/    full bounded timing/resource reports
    wheel/         inspected candidate wheel
    environment.json
  service/runs/    temporary real-service WAV/manifest pairs
```

Only root-relative labels, registry identities, checksums, versions, sanitized
measurements, source URLs, and pass/fail outcomes may be copied into committed
M6 evidence. The raw prompt, its source/OCR files, checkpoints, caches, audio,
complete reports, run identifiers, resolved roots, and machine-local details
remain external. Model access uses `HF_HOME` and `TORCH_HOME` below the same
boundary; uv downloads use an external `UV_CACHE_DIR`.

The external M6 directory is local review evidence and is not a release
artifact. Retention/deletion is an operator decision after M7; this repository
does not implement an automatic destructive cleanup command.

The original private recording-data layout is historical documentation at
`docs/history/white_hmong_single_speaker/private_data_layout.md`.

## M7 retention and privacy policy

M7 reuses the retained external root and adds `m7/20260910T122457Z/` without
changing M6 evidence. Its `audit/`, `prompts/`, `runs/`, `cpu/`, `qc/`,
`benchmarks/`, `service/runs/`, `environment/`, `logs/`, `tooling/`, and
`packages/` hold detailed local evidence. The service temporarily uses the M7
run directory as a nested canonical root so its default `service/runs` prefix
cannot overwrite retained M6 output. Shared HF/Torch/uv caches stay external.

Retain M6 and M7 raw evidence through the 2026-12-09 risk review and until the
owner has resolved any material audit issue. There is no automatic deletion.
After review the owner may choose retention or deletion under the applicable
licenses; neither Git history rewriting nor cache/audio publication is implied.
Use local access controls and avoid automatic cloud sharing of this boundary.

The public distribution scope is original code and sanitized documentation,
configuration, tests, checksums, and factual measurement summaries. Detailed
raw logs, model files, generated audio, prompt/source/OCR text, environments,
and complete runtime reports are local review material. Never copy machine
account names, hostnames, addresses, environment values, process arguments,
credentials, or absolute private paths into public evidence. The specifically
approved public decision-owner handle is permitted only in governance records.

M7's expanded audit found a personal-provider email in existing Git commit
metadata, distinct from repository file contents. The address is not copied
into public reports. Its continued historical visibility requires explicit
owner disposition; use the verified public GitHub no-reply identity for the
new M7 commit. This policy does not authorize rewriting prior commits.
