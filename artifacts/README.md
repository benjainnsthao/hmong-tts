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
└── benchmarks/
```

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
