# Private data layout (documentation only)

This directory intentionally contains no data. Do not add symlinks to private
data. Configure an absolute external `HMONG_TTS_DATA_ROOT` with this layout:

```text
$HMONG_TTS_DATA_ROOT/
├── consent/                 # encrypted, separately access-controlled records
├── identity/                # encrypted speaker-ID mapping; no ML tooling access
├── raw/spk01/               # immutable 48 kHz/24-bit mono masters
├── processed/spk01/         # derived 16 kHz model inputs
├── metadata/private/        # transcripts, session logs, review state
├── manifests/               # checksums, processing and split manifests
├── evaluation/private/      # hidden prompts, ratings, transcriptions
├── checkpoints/             # model/optimizer/RNG states
├── cache/models/            # audited public base checkpoints
├── runs/                    # local/offline tracker and generated grids
├── smoke/                   # generated MMS smoke WAV files
└── backups/manifests/       # verification records, not the backup media itself
```

Validate before use:

```bash
uv run hmong-tts-env --require-data-root
uv run hmong-tts-privacy-scan --require-data-root
```

Real data must not be used in automated tests; tests create synthetic temporary
fixtures only.
