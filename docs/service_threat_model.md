# Local service threat model

Scope: Milestone M5's loopback-only development service. This document covers
the application boundary implemented in this repository. It does not approve a
public deployment or replace an operating-system security review.

## Assets

- third-party checkpoint access and optional model cache;
- generated WAV and success-manifest artifacts;
- transient caller prompt text;
- audited registry and policy metadata;
- process/GPU memory and the single model owner; and
- service availability on the local machine.

Raw prompts are transient input. They are not manifest, report, or log fields.
Weights, cache, and generated audio remain below the external artifact root and
outside Git.

## Trust boundaries

1. A process on the same host sends JSON over a loopback socket.
2. FastAPI validates the narrow external request.
3. The service resolves registry provenance and creates the output path.
4. The bounded coordinator crosses into the synchronous M3 executor.
5. The lazy adapter may cross into optional PyTorch/Transformers and the model
   cache only after explicit serving acknowledgement and accepted work.
6. The atomic store crosses into the external artifact root.

Loopback is not authentication. Another local user/process, browser process,
malware, proxy, tunnel, container port mapping, or misconfigured host can
potentially reach or expose a local port.

## Controls and residual risks

| Threat | Implemented control | Residual risk / operator duty |
|---|---|---|
| Public exposure | Only literal loopback IPs validate; public deployment is fixed false; no deployment/tunnel configuration | Do not proxy, tunnel, container-map, or firewall-publish the port |
| Unauthorized local caller | No CORS, cookies, sessions, or browser support; narrow JSON schema | Loopback has no authentication; use OS account/firewall isolation and stop the service when unused |
| Prompt disclosure | No request body logging; sanitized validation; raw text excluded from responses/manifests | Prompt exists transiently in process/model memory; local debuggers/crash tooling remain out of scope |
| Client tracking | Uvicorn access log and client-address logging disabled; no analytics/telemetry | Network stack and OS may still observe local connections |
| Path traversal | Caller cannot submit paths; prefix is normalized/root-relative; M3 artifact boundary revalidates | Operator controls the external root and its filesystem permissions |
| Registry bypass | Caller cannot submit repository/revision/provider/prompt provenance; model ID resolves before load | Registry and license audit freshness remains an M7 supply-chain gate |
| Resource exhaustion | Maximum text length, finite pending queue, one active operation, one worker, one model owner | Repeated local requests can still consume CPU/GPU/time; no authentication or per-client rate limit exists |
| Queue starvation | FIFO admission and pre-execution deadline | A long active backend call delays all queued work |
| Unsafe cancellation | Queued work can expire safely; active work is explicitly non-preemptive; shutdown waits | A hung native/model call can delay shutdown and requires process-level operator intervention |
| Partial artifacts | M3 structural validation and manifest-last atomic transaction with rollback | OS/storage failure outside documented atomic guarantees remains possible |
| Backend exception disclosure | Stable categories/messages; unexpected failures become generic 500 | Internal logs from third-party runtimes must not be enabled with sensitive prompts |
| Multi-owner GPU races | One Uvicorn worker, coordinator owner, active operation, model instance, and adapter | Launching multiple independent service processes is outside the in-process control |
| Capability overclaim | Registry returns `not_evaluated`; docs separate engineering evidence | Users may still misuse outputs; no linguistic-quality evidence exists |

## Shutdown and failure invariants

- New requests are rejected after admission closes.
- Pending requests are resolved as sanitized failures.
- Expired pending requests never invoke the adapter or create artifacts.
- Active synchronous execution is not force-cancelled or reported cancelled.
- The adapter unloads only after active work completes.
- A failure never returns a success artifact reference.
- A success manifest never intentionally refers to a missing/invalid WAV.

## Explicit exclusions

M5 adds no TLS, authentication, authorization database, public CORS policy,
reverse proxy, cloud manifest, public rate limiter, distributed queue,
multi-worker scaling, UI, browser client, or production fake backend. Those
would change the threat model and require separate authorization.

M5 also adds no model download during validation, real audio, native-language
prompt, language normalization, pronunciation scoring, or capability claim.
White Hmong adaptation and NV-001 through NV-008 remain deferred **[NV]**.

## M6 real-backend check

M6 exercised the unchanged boundary with one temporary loopback process and
the locked real MMS backend. Both registered models completed serial CUDA
requests. An unknown model returned its generic category without prompt echo or
artifact creation. Server output contained startup/shutdown lifecycle messages
but no access/client record, prompt, backend exception, or artifact path.
Shutdown drained the coordinator, unloaded the adapter, exited, and left no
listener. This evidence mitigates implementation/lifecycle risk but does not
change any residual operator duty or approve public deployment.

## M7 review requirement

REL-SERVICE-001 is mitigated by the M5 controls and synthetic evidence, but M7
must re-audit the exact release commit, dependency advisories, configuration,
package contents, claims, and intended distribution mode. Any public or
non-loopback deployment requires a new security design; this threat model does
not approve it.

## M7 re-audit and residual exhaustion limits

M7 repeats configuration/schema/OpenAPI, synthetic ASGI, lifecycle/FIFO,
shutdown, expiry, sanitization, and real-backend controls against the corrected
locked dependencies. Both approved prompts ran on CUDA through one service;
an unknown model was rejected before execution, with no partial artifact or
prompt echo. Shutdown reached unloaded adapter state, zero active/pending
requests, and a stopped listener. Small allocator/runtime buffers can remain
until process exit; unloaded state does not mean all CUDA runtime memory is zero.

The 500-character limit applies after JSON parsing. There is no hard HTTP-body
byte limit, output-duration ceiling, request-rate limit, disk quota, or safe
active-native-call cancellation. Positive but very small speaking rates can
cause disproportionate work despite the character bound. The finite FIFO
bounds admitted pending inference, not every HTTP parser/connection resource.
The scoped service therefore requires trusted local clients, approved prompts,
and ordinary generation settings. Loopback is not authentication. Other local
processes, hostile callers, compromised dependencies, and resource exhaustion
remain residual risks for explicit owner acceptance; this is not a public
service security design. No destructive exhaustion experiment was performed.

Starlette and PyTorch advisories were corrected, unused vulnerable Accelerate
removed, and transitive setuptools constrained; see `m7_dependency_audit.md`.
Registry-only sources and safetensors-only model loading do not guarantee that
native runtimes or every upstream artifact are vulnerability-free. The complete
proposed disposition is REL-SERVICE-001 in `release_risk_register.md`.
