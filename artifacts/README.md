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
└── benchmarks/
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
