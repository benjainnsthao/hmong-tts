# Bounded local inference service and browser dashboard

The local browser feature extends the completed M5–M7 service. Launch with
`bash scripts/launch-local.sh` after the installation in
[dashboard usage](../apps/README.md), then open the printed loopback URL.
The existing acknowledged service command also serves the dashboard. This
development does not modify M7's approval records.

Milestone M5 exposes the stable M3 executor through a localhost-only FastAPI
application. It is intended for controlled local development. It is not a
public deployment, authentication system, language-learning application, or
statement of model/language quality.

## Offline metadata operations

These commands validate or render metadata without starting Uvicorn, importing
PyTorch/Transformers, accessing a checkpoint, or requiring CUDA:

```text
tts-workbench-serve schema
tts-workbench-serve validate-config
tts-workbench-serve openapi
```

Actual serving requires an explicit acknowledgement:

```text
tts-workbench-serve run --acknowledge-model-access
```

The active configuration is `configs/inference/local.yaml`, schema version 2.
Only literal loopback hosts are accepted. Worker count, active inference
operations, and model instances are fixed at one. Public deployment, access
logging, request-text logging, and client-address logging are fixed off.

Schema version 2 replaces the unused M1 normalization-token limit and
GPU-named concurrency field with provider-neutral active-operation, finite
queue, queue/request deadline, access-log, and service-owned output-prefix
controls.

The acknowledgement authorizes lazy local checkpoint access after a request is
accepted. It does not override the registry license, prompt-provenance,
artifact-root, device, or redistribution controls.

## Endpoints

### `GET /health`

Returns process/application health and the workbench version. It does not
require an artifact root, loaded model, optional runtime, or CUDA. It contains
no machine or client identity.

### `GET /ready`

Returns `ready` only when admission is open, the external artifact root is
valid, and core environment readiness passes. It reports these required
boundaries separately from:

- optional CPU/CUDA runtime readiness;
- lazy adapter loaded/unloaded state; and
- queue admission, finite pending capacity, pending count, and active count.

An unloaded lazy model is not itself a readiness failure. A ready service may
still return `dependency_unavailable` or `device_unavailable` when synthesis
first requests an optional backend/device.

### `GET /v1/models`

Lists only audited registry entries. Each response copies the immutable
repository/revision identity, provider-documented language tag, architecture,
weight license, approved use, redistribution status, prompt-set reference,
audit provenance, and `language_quality_status: not_evaluated`. This endpoint
does not contact the model host or load a checkpoint.

### `POST /v1/synthesize`

The strict request accepts:

- schema version 1;
- registered model ID;
- non-empty text within the configured limit;
- `auto`, `cpu`, or `cuda`;
- a non-negative seed; and
- `noise_scale`, `noise_scale_duration`, and `speaking_rate`.

It does not accept artifact paths, URLs, repository/revision overrides,
prompt-provenance overrides, provider configuration, environment values,
credentials, client identity, arbitrary metadata, or normalization fields.

The service looks up the registry entry, derives its prompt reference, generates a
UUID output name below `service/runs`, and submits the internal M3 request to
the bounded coordinator. A success response contains only run ID and
artifact-root-relative WAV/manifest references.

Custom English input records `user_supplied_unreviewed` provenance; exact
built-in fixture content records `builtin_fixture`. The retained Vietnamese
reference requires the exact approved prompt hash and records
`retained_external_fixture`. The external source/provenance review still applies.
New manifests use schema 2 with explicit provenance; historical schema 1
manifests remain readable. No caller-supplied provenance override is accepted.

### Browser and result routes

- `GET /`: packaged dashboard; `/ui/app.js` and `/ui/styles.css` are its assets.
- `GET /v1/ui-config`: configured input limit, English example, retained
  Vietnamese hash, history limit, and conservative UI speaking-speed range.
- `GET /v1/runs/{run_id}`: sanitized timing, audio, device, model, seed, speed,
  prompt-provenance, and language-quality metadata.
- `GET /v1/runs/{run_id}/audio`: verified WAV with single byte-range support
  for seeking; `?download=true` requests a local WAV download.

An in-memory index maps the latest 64 successful run IDs to actual executor
results. Run IDs and filenames are independent. Restart clears the index;
neither eviction nor browser history clearing deletes artifacts. No disk
directory is scanned or listed. Both audio and metadata require the matching
completion manifest, WAV checksum, and structural metadata. Descriptor-based
reads reject symlink components and traversal, including replacement races
during opening. Nonregular files, manifests over 64 KiB, and WAVs over 32 MiB
are not served. Unavailable or invalid results return sanitized 404 responses.
The artifact root is never mounted as a static directory.

Host headers must identify the configured loopback address or `localhost` at
the configured port. If present, Origin must exactly match that HTTP Host
origin. Cross-site and same-site-but-not-same-origin fetches are rejected.
Trusted CLI clients may omit Origin; POST requests must use JSON. Proxy-header
interpretation is disabled and no broad CORS policy is enabled.

Responses use `Cache-Control: no-store`, same-origin content and resource
policies, no-referrer, no-sniff, and anti-framing headers. The UI uses safe text
rendering and page-memory history, without persistent prompt/audio storage.
Local downloads do not grant publication rights. Global queue counts do not
describe an individual request's progress; disconnects do not cancel inference.

## Queue, deadline, and shutdown semantics

There is one finite FIFO queue and exactly one active inference operation.
Capacity counts pending requests; the active request is separate.

- Admission closed: reject with `service_not_ready`.
- Pending queue at capacity: reject immediately with `queue_full`.
- Queued deadline reached: remove and reject with `deadline_timeout`; do not
  call the adapter or create artifacts.
- Execution started: run non-preemptively through the synchronous M3 executor.
- Shutdown: close admission, reject all pending work, wait for active work, and
  unload the adapter.

`queue_timeout_seconds` cannot exceed `request_timeout_seconds`. M5 applies the
deadline while work is pending. It deliberately does not claim safe
cancellation of an in-flight model/GPU call. A caller disconnect also cannot
prove that synchronous backend execution stopped.

## Stable status mapping

| Category | HTTP | Meaning |
|---|---:|---|
| `invalid_request` | 422 | Strict validation or configured text limit failed |
| `unknown_or_unapproved_model` | 404 | Model ID is absent from the audited registry |
| `service_not_ready` | 503 | Admission or a required boundary is closed |
| `queue_full` | 429 | Finite pending capacity is exhausted |
| `deadline_timeout` | 504 | Work expired before execution began |
| `dependency_unavailable` | 503 | Optional ML runtime is unavailable |
| `device_unavailable` | 503 | Requested device cannot be used |
| `model_load_failure` | 503 | Audited model could not be loaded |
| `synthesis_failure` | 500 | Backend synthesis failed |
| `invalid_waveform` | 500 | M3 structural waveform validation failed |
| `artifact_boundary_failure` | 500 | Service-owned destination failed its boundary |
| `artifact_collision` | 409 | Generated success destination already exists |
| `artifact_write_failure` | 500 | Atomic WAV/manifest transaction failed |
| `unexpected_internal_failure` | 500 | Unexpected failure was sanitized |

Messages are fixed and generic. FastAPI's default validation response is
overridden because it can include submitted input. Neither normal responses
nor failures echo raw text, backend exceptions, absolute paths, request
headers, environment values, usernames, hostnames, or client addresses.

## Artifacts and privacy

M5 reuses the M3 atomic transaction: the WAV is committed first and the success
manifest last. The manifest remains the commit marker and stores only the
prompt SHA-256, not raw text. Rejected, invalid, queue-full, expired, and failed
requests publish no success response or partial transaction.

Uvicorn access logging is disabled. The application adds no CORS, cookies,
sessions, analytics, telemetry, authentication database, or request logging.
See `docs/service_threat_model.md` for the residual local-process and operator
risks.

## Evidence limitations

M5 validation used injected fakes, in-process ASGI calls, and synthetic WAVs
inside pytest temporary directories. That remains the ordinary regression and
CI boundary.

M6 temporarily launched the same production application on the configured
loopback interface with explicit model-access acknowledgement, one Uvicorn
worker, access logging disabled, and the external artifact root. It verified
health, readiness, both registry records, a sanitized unknown-model rejection,
and successful CUDA synthesis for both exact registered checkpoints. The
rejection echoed no prompt and created no artifact; normal server output held
no access/client record. Shutdown drained work, unloaded the adapter, exited,
and left no listener. `scripts/probe_local_service.py` reproduces the requests
without printing prompts.

HTTP success, registry inclusion, runtime readiness, and an atomic manifest do
not establish pronunciation, naturalness, intelligibility, linguistic
correctness, or White Hmong capability. NV-001 through NV-008 remain deferred
**[NV]**.

## M7 release evidence

Both immutable English and Vietnamese checkpoints were exercised on CUDA with
approved prompts, followed by a safe rejection and clean shutdown. Exact
commands and evidence are in `m7_reproduction.md` and
`../reports/validation/m7_release_validation.md`. Public release of the
workbench code does not authorize publicly binding this service or commercial
use of MMS. Trusted local clients must observe the body/work/disk exhaustion
limitations in `service_threat_model.md`; queue capacity is not a complete
resource quota. Final owner acceptance is recorded in `m7_owner_approval.json`.
