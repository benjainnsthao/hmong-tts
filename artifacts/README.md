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

## Temporary legacy-variable policy

For the 0.2 migration window only:

- canonical variable only: accepted;
- legacy `HMONG_TTS_DATA_ROOT` only: accepted with a deprecation warning;
- both variables resolving to the same path: canonical wins and a warning asks
  the user to remove the legacy variable;
- both variables resolving to different paths: rejected.

Missing, relative, repository-local, symlinked, nonexistent, and escaping paths
fail closed. Validation reports expose only pass/fail status and never print the
resolved absolute artifact root.

Generated audio and third-party weights must never be committed or
redistributed by this project. No private speaker data is in the active scope.

The original private recording-data layout is historical documentation at
`docs/history/white_hmong_single_speaker/private_data_layout.md`.
