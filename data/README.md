# External artifact boundary

This repository directory intentionally contains no audio, weights, caches, or
benchmark artifacts.

During this transitional milestone, the existing `HMONG_TTS_DATA_ROOT`
environment variable remains the enforced external root. Despite its legacy
name, it is used only for public model caches, generated non-Hmong smoke audio,
and future workbench artifacts. No private speaker data is in scope.

```text
$HMONG_TTS_DATA_ROOT/
├── cache/models/
├── smoke/
├── runs/
└── benchmarks/
```

The value must be an absolute existing path outside the Git repository.
Generated audio and third-party weights must never be committed or
redistributed by this project.

The original private recording-data layout is historical documentation at
`docs/history/white_hmong_single_speaker/private_data_layout.md`.
