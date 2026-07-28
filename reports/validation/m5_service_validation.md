# M5 bounded local service validation

Validation date: 2026-07-28

Branch: `rescope/audited-tts-workbench`

M4 starting commit: `87b8e4f844232a502ae5674dd64e2e6a0caa81af`

Preliminary risk-documentation commit: recorded in branch history as
`docs: add final release risk milestone`

M5 implementation commit: recorded in branch history as
`feat: complete M5 bounded local service`

## Scope

Validated the strict localhost service contracts, application lifespan,
single-owner bounded FIFO coordinator, M3 executor integration, registry
metadata projection, service-owned artifact paths, sanitized error mapping,
CLI acknowledgement/configuration controls, and release package.

Validation used only project metadata, test fakes, in-process ASGI calls, and
pytest-temporary synthetic WAVs. It did not install the optional MMS group,
download or execute a checkpoint, access a model host, use CUDA/GPU, start a
persistent server, bind a live external port, or use real/external/
native-language content.

## Dependency and license audit

Primary project metadata and license texts were reviewed on 2026-07-28:

- FastAPI 0.136.3 — MIT, Python >=3.10;
- Starlette 1.0.0 — BSD-3-Clause, Python >=3.10;
- Uvicorn 0.46.0 — BSD-3-Clause, Python >=3.10; and
- HTTPX 0.28.1 — BSD-3-Clause, Python 3.12 classified, development tests only.

The lock contains exact versions. FastAPI standard/cloud extras and Uvicorn
standard extras are absent. Checkpoint identity, checkpoint license, approved
use, and redistribution policy are unchanged. Source URLs are recorded in
`docs/license_matrix.md`.

## Automated gates

| Gate | Result |
|---|---|
| Ref safety and M4 ancestry | PASS |
| Frozen lock check | PASS — 85 packages resolved without lock changes |
| Frozen offline core sync | PASS — 42 packages checked, no MMS extra |
| Ruff formatting | PASS — 70 files |
| Ruff lint | PASS |
| Strict source MyPy | PASS — 40 source files |
| Active configuration validation | PASS — inference schema 2; benchmark/QC schema 1 |
| Registry validate/list | PASS — schema 1, two immutable entries |
| Privacy/artifact scan | PASS — 139 candidate files |
| Complete synthetic suite | PASS — 258 tests |
| Aggregate branch-aware coverage | PASS — 81.57% (minimum 78%) |
| Focused service suite | PASS — 77 tests |
| Focused service branch-aware coverage | PASS — 96.65% (minimum 90%) |
| Application/error mapping coverage | PASS — 100% |
| Coordinator coverage | PASS — 95% |
| Service contract coverage | PASS — 96% |
| In-process ASGI endpoints/lifecycle | PASS |
| Full pre-commit suite | PASS |
| Package/service import without optional ML | PASS |
| Eight CLI `--help` paths | PASS |
| Service schema/config/OpenAPI metadata operations | PASS |
| Model-access acknowledgement gate | PASS; no server launched |
| Old package and old CLI absence | PASS |
| Tracked audio/weight/cache and >1 MiB scan | PASS |
| Wheel build/content/metadata inspection | PASS |
| Active service/public/native-language scope scans | PASS |
| Historical evidence and deferred NV preservation | PASS |
| Git whitespace checks | PASS |

## Service behavior evidence

- `/health` remains independent of model, CUDA, and artifact readiness.
- `/ready` separates admission, artifact, core environment, optional runtime,
  lazy loaded-model state, and finite queue state.
- `/v1/models` copies exact audited registry metadata and preserves
  `language_quality_status: not_evaluated`.
- `/v1/synthesize` derives prompt provenance and UUID output paths inside the
  service, then routes through the existing M3 executor.
- Unknown models fail before load. Invalid/default framework responses do not
  echo submitted text.
- The pending queue is finite and FIFO; full, closed, caller-cancelled, and
  expired pending work never reaches the executor.
- Exactly one executor call is active. Shutdown rejects pending work, waits
  non-preemptively for active work, and unloads the adapter.
- Every M3/service failure maps to a stable sanitized HTTP category/status.
- Successful integration commits the WAV and manifest through the M3 atomic
  transaction. Failed integration leaves no artifact file.

## Privacy and package evidence

Responses, logs, manifests, and reports contain no raw prompt, backend
exception, absolute artifact root, username, hostname, client address, request
header, credential, environment value, cache path, or private identifier.
Uvicorn access logging is disabled and there is no CORS, UI, browser,
analytics, telemetry, tunnel, cloud deployment, or production fake mode.

The built wheel was `audited_tts_workbench-0.4.0-py3-none-any.whl`. It contained
only `tts_workbench` source, distribution metadata/license, and eight entry
points. It contained no tests, docs, audio, weights, caches, bytecode, or
private data. The temporary build directory was removed after inspection.

## Preservation and limitations

Local/remote `main` and the local preservation branch were verified against
`fd1756485b1e1b75fd1efee5e37519fa8e255415`. Existing historical validation
reports and `docs/deferred/white_hmong_native_validation.md` were unchanged.
NV-001 through NV-008 remain deferred **[NV]**.

M5 supplies contract and synthetic systems evidence only. It does not establish
real checkpoint execution, performance, pronunciation, intelligibility,
naturalness, linguistic correctness, White Hmong capability, or readiness for
a Hmong learning application. Loopback is not authentication. M6 reproduction
and authorized hardware evidence are next; M7 remains the only release-risk
disposition and release-decision gate.
