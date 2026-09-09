# Inference contract — schema version 1

Milestone M3 defines the library-level, provider-neutral TTS execution
contract. M4 consumes its adapter and waveform boundaries. M5 projects the
same executor through a bounded local API without exposing caller-controlled
artifact or provider fields. None of these milestones is a language-quality
evaluator.

## Request and result boundary

`InferenceRequest` is frozen and rejects extra fields. It records:

- schema version 1;
- an audited registry model ID;
- non-empty input text, limited to the active 500-character boundary;
- the model's prompt-set or provenance reference;
- requested `auto`, `cpu`, or `cuda` execution;
- a non-negative seed;
- MMS/VITS `noise_scale`, `noise_scale_duration`, and `speaking_rate`; and
- a normalized artifact-root-relative `.wav` path.

The request contains no language normalizer, spelling mapping, tone handling,
or White Hmong text-processing field. A prompt-reference mismatch fails before
backend loading.

`InferenceResult` records a unique run ID and either:

- `success` with root-relative WAV and manifest paths; or
- `failure` with one sanitized structured category and no artifact paths.

It never echoes prompt content or an absolute artifact location.

## Adapter lifecycle

`TTSAdapter` exposes:

1. stable adapter identity and implementation version;
2. observable `loaded` or `unloaded` state;
3. explicit load by registered model ID and requested device;
4. synthesis from validated text, seed, and generation settings; and
5. explicit unload.

The interface exposes no provider tokenizer, model, tensor, or library object.
`MmsVitsAdapter` owns at most one backend/model. Loading a different model or
changing the requested device unloads the old backend before creating the new
one. Repeating the same model/device load reuses the owned backend. Unknown
model IDs are rejected through the audited registry before a backend factory is
called.

The production `TransformersMmsBackend` imports PyTorch and Transformers only
inside explicit load. Missing dependencies, unavailable CUDA, load failure, and
synthesis failure cross the boundary as stable adapter errors. Tests inject
small synthetic backends and never import the optional stack.

## Execution orchestration

`InferenceExecutor` performs, in order:

1. strict request validation;
2. audited registry lookup and prompt-reference comparison;
3. artifact destination validation and collision rejection;
4. adapter load and execution-layer timing;
5. synthesis and execution-layer timing;
6. SHA-256 prompt hashing;
7. M3 structural waveform validation; and
8. atomic WAV/manifest commit and result construction.

Unknown or unapproved models, prompt mismatches, and artifact escapes fail
before adapter loading. Timing and UUID/time sources are injectable for
deterministic tests.

## Run manifest

A successful `.manifest.json` is strict schema version 1 and records:

- unique run ID, success status, and UTC start/completion timestamps;
- adapter ID and implementation version;
- registry schema version;
- audited model ID, provider, repository, immutable revision, architecture,
  documented language tag, license, approved use, redistribution status,
  prompt reference, and language-quality status;
- SHA-256 prompt hash;
- requested/resolved device, dtype, seed, and generation settings;
- Python and workbench versions;
- PyTorch and Transformers versions only when the active backend reports them;
- model-load and synthesis durations measured by the execution layer;
- sample rate, mono channel count, sample count, duration, and WAV checksum; and
- artifact-root-relative WAV path.

Raw prompt text, absolute paths, usernames, hostnames, addresses, credentials,
private identifiers, and linguistic conclusions are not fields. Extra fields
are rejected.

## Atomic artifact semantics

The store validates roots and destinations with
`tts_workbench.artifacts.paths`. It creates parent and temporary files only
below the external root. Temporary files are beside their destinations and are
closed before `os.replace`, including on Windows.

The temporary WAV must reopen as non-empty mono uncompressed 16-bit PCM with
the expected positive sample rate and frame count. The success manifest is
serialized before publication. The WAV is replaced first and the manifest
last, making the manifest the commit marker. Serialization, validation, or
replacement failure removes temporary files and any WAV owned by that failed
transaction. Existing destinations are rejected and not overwritten.

## Failure categories

- `invalid_request`
- `unknown_or_unapproved_model`
- `artifact_boundary_failure`
- `dependency_unavailable`
- `device_unavailable`
- `model_load_failure`
- `synthesis_failure`
- `invalid_waveform`
- `artifact_collision`
- `artifact_write_failure`

Failures do not produce success manifests or partial WAVs. Returned messages
are generic and do not include prompt text, backend exception content, or
absolute paths.

## M4 consumers and deliberate limitations

M3 checks only the structure needed to commit a WAV safely: non-empty finite
samples, positive sample rate, mono PCM output, successful reopen, positive
frames, and expected rate/channel metadata.

M4 separately calculates configured peak/clipping, RMS, DC offset, and
near-silence engineering checks through `WaveformQcAnalyzer`; those results do
not participate in artifact commitment. M4 also reuses `TTSAdapter` for an
explicitly invoked one-model benchmark. It reports cold load, excluded warmups,
warm synthesis latency, generated duration, real-time factor, measured median,
nearest-rank p95, failure counts, and optional point-in-time memory.

Neither layer calculates loudness, LUFS, SNR, PESQ, STOI, MOS, ASR,
pronunciation, intelligibility, naturalness, linguistic correctness, or
perceptual scores. Ordinary development and CI do not download or execute a
model.

Seed, device, dtype, generation settings, and runtime versions are recorded to
support same-environment reproduction. M3 does not promise byte-identical
waveforms across different devices or runtime versions.

## M5 service projection

The external `SynthesisRequest` is narrower than `InferenceRequest`. It accepts
only registered model ID, non-empty bounded text, requested device, seed, and
existing `GenerationSettings`. The service derives the prompt-set reference
from the registry and creates a UUID-based path below its configured
artifact-root-relative prefix. Callers cannot submit an output path,
repository, revision, prompt reference, provider configuration, identity
metadata, or normalization option.

One bounded FIFO coordinator serializes accepted requests through one
`InferenceExecutor`. Full, closed, invalid, unknown-model, and expired queued
requests do not invoke the executor. Once execution begins, a synchronous
backend call is non-preemptive: request or shutdown logic does not claim that
an in-flight model/GPU call was cancelled.

Service responses expose only a run ID and root-relative WAV/manifest
references on success, or a stable sanitized category/message on failure.
Framework validation details are overridden so malformed requests cannot echo
the submitted text. HTTP status mappings and lifecycle details are defined in
`docs/local_service.md`.

The registered language tags are provider metadata. Runtime success, waveform
structure, and a manifest do not establish pronunciation, naturalness,
linguistic correctness, White Hmong capability, or readiness for a Hmong
learning application. White Hmong adaptation and NV-001 through NV-008 remain
deferred **[NV]**.

## M6 real-runtime evidence

Direct MMS execution now requires `--acknowledge-model-access`; preflight and
help remain metadata-only. On 2026-09-09 both registered immutable revisions
ran with requested/resolved CUDA, float32, seed 555, and the committed default
generation settings. Each output reopened as mono 16 kHz PCM16 and matched its
manifest frame count, duration, checksum, registry identity, and root-relative
path. The raw prompts and absolute artifact/cache roots were absent from the
manifests and ordinary output.

The optional backend owns one model/tokenizer pair, clears those references on
unload, performs collection, and releases unused CUDA cache. Runtime-context
memory that remains observable after unload is reported honestly by the
benchmark and is not interpreted as a retained adapter model. Full machine-local
artifacts remain outside Git; sanitized results are in
`reports/validation/m6_reproduction_validation.md`.
