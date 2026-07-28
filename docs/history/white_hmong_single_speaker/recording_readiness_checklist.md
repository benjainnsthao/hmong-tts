# Recording-readiness gate

No dry-run or production recording may begin until the applicable gate is
checked, dated, and stored in a private session record below
`HMONG_TTS_DATA_ROOT`. This repository copy is a blank checklist.

## Gate A — consent and roles (required before any recording)

- [ ] Primary speaker signed the completed consent record; it is outside Git.
- [ ] Recording participation and model training are separately authorized.
- [ ] Demo, sample, weight, commercial, retention, withdrawal, credit, and
  future-use choices are explicit rather than inferred.
- [ ] Primary speaker is assigned only the pseudonym `spk01` in engineering data.
- [ ] Second speaker understands the independent reviewer role and is not a
  training speaker for the MVP.
- [ ] Identity mappings and contact details are encrypted separately from audio.

## Gate B — privacy and file flow (required before any recording)

- [ ] `HMONG_TTS_DATA_ROOT` is an absolute path outside this repository.
- [ ] `uv run hmong-tts-env --require-data-root` passes.
- [ ] Raw, processed, metadata, evaluation, checkpoint, and consent directories
  match `data/README.md`; consent is separate from audio.
- [ ] Primary recording storage is access-controlled.
- [ ] Encrypted external-drive backup is available.
- [ ] Encrypted off-site/private-cloud backup is available and approved.
- [ ] SHA-256 manifest generation and verification have been rehearsed.
- [ ] `uv run hmong-tts-privacy-scan` passes before and after the rehearsal.

## Gate C — language and prompts (required before the dry run)

- [ ] Target variety and speaker orthography are recorded in NV-001. **[NV]**
- [ ] Dry-run prompts are authored/licensed and approved by the native speakers.
  **[NV]**
- [ ] Every uncertain pronunciation, tone, spelling, number, abbreviation, or
  borrowed-word choice is marked unresolved rather than guessed. **[NV]**
- [ ] Prompts contain no real names, contact details, or unnecessarily sensitive text.

## Gate D — recording setup (required before the dry run)

- [ ] Mono, 48 kHz, 24-bit PCM WAV is configured.
- [ ] AGC, noise suppression, compression, reverb removal, and live normalization are off.
- [ ] Microphone, interface, cable, stand, room, and software preset are logged.
- [ ] Microphone is approximately 15–20 cm away, slightly off-axis, with pop filter.
- [ ] Chair, stand, and microphone positions are physically marked.
- [ ] Ordinary speech peaks are approximately -12 to -6 dBFS.
- [ ] A 30-second room-tone capture is planned at session start and end.
- [ ] Five calibration prompts are selected for repeat use. **[NV]**
- [ ] File naming was tested with `spk01_sYYYYMMDD_uNNNNNN_takeNN.wav`.
- [ ] Session blocks, breaks, daily cap, fatigue stop rules, and health logging are understood.

## Gate E — dry-run exit (required before production recording)

- [ ] A consented 5–10-minute dry run was recorded; no production prompts were used.
- [ ] Every take and transcript was manually reviewed by the second speaker.
- [ ] Headers, mono channel, 48 kHz, 24-bit depth, clipping, peak, noise, silence,
  duration, naming, duplicate, and checksum checks pass or have explicit resolutions.
- [ ] Immutable primary copy and both encrypted backups match the SHA-256 manifest.
- [ ] The raw master remained unchanged; processing outputs are reproducible.
- [ ] No speaker name, consent record, audio, private rating, or absolute private path
  appears in Git or hosted experiment tracking.
- [ ] Recording/setup defects from the dry run are closed.
- [ ] Primary speaker confirms comfort and willingness to continue.

Private gate record ID: ____________________
Reviewed by pseudonymous IDs: ____________________
Decision/date: ____________________
