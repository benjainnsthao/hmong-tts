# Waveform QC engineering checks

Milestone M4 QC provides deterministic non-linguistic engineering evidence. A
pass is not evidence of naturalness, pronunciation, intelligibility,
linguistic correctness, language support, or learning-application readiness.

M3 structural validation remains the artifact commit-safety boundary. M4 is a
separate read-only analysis of an in-memory `WaveformResult` or a committed
artifact-root-relative WAV.

## Input and numeric semantics

Committed WAV analysis supports uncompressed mono signed PCM16 only. Each
little-endian signed integer sample is divided by 32768, producing the
normalized interval `[-1.0, 32767/32768]`. Unsupported compression/sample
width, corrupt data, empty audio, wrong channels, and unconfigured sample rates
produce structured `structurally_invalid` reports.

Floating-point in-memory samples retain their supplied scale. Empty, nonfinite,
wrong-channel, and invalid/unconfigured-rate waveforms are structurally invalid.
An otherwise safe calculation failure is `analysis_failure`.

The fixed rule order reports:

1. WAV readability;
2. channel count;
3. sample width;
4. sample rate;
5. minimum frame count;
6. minimum duration;
7. finite samples;
8. absolute peak;
9. clipping ratio;
10. minimum RMS;
11. absolute DC offset;
12. leading near-silence ratio;
13. trailing near-silence ratio; and
14. total near-silence ratio.

Every rule is `pass`, `fail`, or `not_applicable` and includes observed value,
threshold/expected value, unit, sanitized explanation, and
`evidence_scope: engineering_sanity_check`. Reports distinguish
`structurally_invalid`, `qc_failing`, `qc_passing`, and `analysis_failure`.

## Active thresholds

`configs/qc/default.yaml` is strict schema version 1:

| Setting | Default | Boundary |
|---|---:|---|
| expected channels | 1 | exact |
| expected sample width | 2 bytes | exact |
| allowed sample rates | 16000 Hz | membership |
| clipping amplitude | 0.999 | `abs(sample) >=` counts |
| maximum clipping ratio | 0.001 | pass at `<=` |
| minimum RMS | 0.01 | pass at `>=` |
| maximum absolute DC | 0.05 | pass at `<=` |
| near-silence amplitude | 0.005 | `abs(sample) <=` counts |
| maximum leading ratio | 0.20 | pass at `<=` |
| maximum trailing ratio | 0.20 | pass at `<=` |
| maximum total ratio | 0.60 | pass at `<=` |
| minimum frames | 160 | pass at `>=` |
| minimum duration | 0.01 seconds | pass at `>=` |

RMS is `sqrt(sum(sample^2)/N)`. DC offset is the arithmetic mean. Leading and
trailing silence count consecutive near-silence samples from each edge. Total
near-silence counts qualifying samples anywhere. Ratios divide by sample count;
edge durations divide edge sample count by sample rate.

These defaults are conservative project sanity checks chosen to catch obvious
structural/level defects in local MMS-style 16 kHz output. They are
configuration, not universal TTS acceptance criteria. Every report embeds the
effective threshold object so results remain interpretable after configuration
changes.

## CLI and reports

```text
tts-workbench-qc schema
tts-workbench-qc validate-config
tts-workbench-qc analyze --input runs/example.wav --output qc/example.json
tts-workbench-qc analyze --input runs/example.wav --output qc/example.json --json
```

Input/output paths are artifact-root-relative. JSON reports are written below
`TTS_WORKBENCH_ARTIFACT_ROOT` through a closed neighboring temporary file and
atomic replacement. Existing destinations are rejected. Report serialization
or replacement failure leaves no partial report.

Exit code 0 means `qc_passing`; exit code 1 means a completed non-pass report;
exit code 2 means configuration, boundary, analysis invocation, collision, or
report-commit failure. Output never prints raw audio or the absolute artifact
root.

M4 deliberately excludes LUFS, SNR, PESQ, STOI, MOS, ASR, pronunciation,
linguistic, and perceptual scoring.

## M6 authorized-hardware observations

The unchanged thresholds above were applied to both M6 CUDA artifacts. Both
WAVs reopened as mono 16 kHz PCM16 and produced `qc_passing` with zero failed
rules. The English artifact contained 38,656 frames (2.416 seconds), peak
0.738586, RMS 0.110700, zero clipping ratio, and total near-silence ratio
0.331255. The Vietnamese artifact contained 185,600 frames (11.600 seconds),
peak 0.829498, RMS 0.102642, zero clipping ratio, and total near-silence ratio
0.288513.

These observations indicate only that the configured structural/level checks
passed. Full JSON and WAV files remain outside Git; the sanitized table is in
`reports/validation/m6_reproduction_validation.md`.
