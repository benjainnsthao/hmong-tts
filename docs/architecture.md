# Workbench architecture — milestone M5

The repository has a provider-neutral M3 inference data plane, an M4
engineering-evidence plane, and a bounded M5 localhost service. The service is
an application boundary around the existing executor; it is not a public
deployment or language-learning application.

```text
caller on the same host
  |
  +--> GET /health
  +--> GET /ready
  +--> GET /v1/models -------> audited ModelRegistry (metadata only)
  +--> POST /v1/synthesize
             |
             +--> strict SynthesisRequest
             |      no path/repository/revision/provenance override
             |
             +--> registry lookup + service-owned output UUID
             |
             +--> BoundedInferenceCoordinator
                    pending FIFO capacity: configured and finite
                    active operations: exactly one
                    |
                    +--> InferenceExecutor
                           registry/prompt check + prompt hash + timing
                           |
                           +--> one TTSAdapter owner
                           |      |
                           |      +--> MmsVitsAdapter
                           |             +--> test fake backend (tests only)
                           |             +--> lazy optional real backend
                           |
                           +--> structural waveform validation
                           |
                           +--> AtomicArtifactStore
                                  WAV first
                                  success manifest last (commit marker)

M4 side paths
  committed WAV --> WaveformQcAnalyzer --> AtomicJsonReportStore
  registry + adapter --> BenchmarkRunner --> AtomicJsonReportStore

external artifact root
  TTS_WORKBENCH_ARTIFACT_ROOT/
    service/runs/<uuid>.wav
    service/runs/<uuid>.manifest.json
    qc/*.json
    benchmarks/*.json
```

## Ownership and lifecycle

`create_app` performs no module-level registry, model, CUDA, or provider
initialization. Its lifespan factory creates one registry view, one
`MmsVitsAdapter`, one `InferenceExecutor`, and one
`BoundedInferenceCoordinator`. The adapter remains unloaded until the first
accepted synthesis request.

Startup opens coordinator admission. Shutdown closes admission first, rejects
pending work with a sanitized service failure, waits for an active synchronous
backend call to return, then unloads the adapter. The service never claims to
cancel an in-flight GPU/model operation. This non-preemptive shutdown prevents
concurrent ownership and avoids publishing a misleading cancellation result.

The coordinator has one background owner task, a finite FIFO pending queue, and
at most one active executor call. Queue capacity counts pending work, not the
active item. A queued deadline is checked by both a timer seam and immediately
before execution. Expired queued work never reaches `InferenceExecutor` and
therefore cannot create an artifact.

## API and execution boundaries

The external request contains only model ID, text, requested device, seed, and
the three existing MMS/VITS generation settings. The service derives prompt
provenance from the registry and generates the output path under its configured
root-relative prefix. Callers cannot supply a path, URL, repository, revision,
credential, provider object, environment value, language-normalization option,
or client identity.

The internal `InferenceRequest`, `InferenceResult`, adapter lifecycle, run
manifest, waveform validation, and atomic transaction remain the M3 contracts.
M5 adds `artifact_collision` so HTTP can distinguish a safe 409 collision from
an internal write failure without exposing filesystem details.

`GET /health` reports application process health only. `GET /ready` separately
reports admission, artifact-root, core-environment, optional-runtime, lazy model
state, and queue state. An unloaded lazy model is not a readiness failure.
`GET /v1/models` copies registry identity and policy without model access.
Provider language tags remain provenance metadata and never become workbench
quality claims.

## Privacy and local security

The service configuration accepts only literal loopback IP addresses, exactly
one Uvicorn worker, one model owner, one active operation, disabled public
deployment, disabled access logging, and disabled request/client logging. The
application installs no CORS, cookie, session, authentication database,
analytics, telemetry, browser, tunnel, or deployment middleware.

Default validation errors are replaced because framework validation details can
contain submitted input. Every service error has a stable category, generic
message, and documented HTTP status. Responses and logs do not echo prompts,
backend exceptions, client addresses, absolute paths, environment values, or
cache locations.

Loopback binding is a development boundary, not authentication. Other local
processes or users may be able to reach a loopback port. The operator must use
host OS controls and must not expose the port through a proxy, tunnel,
container mapping, or firewall rule. See `docs/service_threat_model.md`.

## Preserved M3/M4 boundaries

The adapter exposes only identity, state, load, synthesize, and unload.
PyTorch/Transformers imports remain inside explicit real-backend loading. The
manifest is published after the WAV and remains the success commit marker.
M4 QC remains a separate engineering-sanity pass and never changes M3 commit
status.

No runtime, HTTP, manifest, QC, or benchmark success is linguistic-quality
evidence. M5 used only fakes and pytest-temporary synthetic WAVs. It provides no
real-model performance result and establishes no White Hmong capability.
NV-001 through NV-008 remain deferred **[NV]**.
