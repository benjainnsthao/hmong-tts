# Workbench environment capabilities

Registry validation, configuration checks, privacy scanning, QC, benchmark
contract tests, linting, typing, and the synthetic suite require only the
locked Python 3.12 core environment. They do not require PyTorch, Transformers,
CUDA, network access, model downloads, or real audio.

The optional MMS dependency group remains restricted to Linux x86-64.
Historical RTX 4070 reports remain unchanged under `reports/validation/`; they
are evidence about one machine, not an active readiness requirement.

## Readiness levels

`tts-workbench-env` emits strict sanitized schema version 1:

- `core_ready` requires supported Python 3.12 and Git;
- `cpu_inference_ready` additionally requires a valid external artifact root
  and importable optional PyTorch and Transformers runtimes; and
- `cuda_inference_ready` additionally requires an observable CUDA runtime and
  at least one device.

FFmpeg status is reported but is not a core or MMS inference prerequisite.
CUDA absence does not fail core or CPU readiness. No RTX 4070 or other device
model name is required.

The report includes Python implementation/version/support, OS/release/
architecture and WSL state, Git and FFmpeg availability/version, artifact-root
validity, optional package versions, CUDA build/device/memory facts where
observable, and supported dtype labels. It excludes artifact paths, usernames,
hostnames, addresses, process arguments, environment values, credentials, and
model-cache paths.

Collectors are injected in tests. Production optional imports are lazy and run
only when environment capability collection is explicitly invoked. Ordinary
contract imports and every CLI `--help` path leave PyTorch and Transformers
unimported.

## Commands and exit gates

```text
tts-workbench-env --json
tts-workbench-env --require-artifact-root
tts-workbench-env --require-core
tts-workbench-env --require-cpu-inference
tts-workbench-env --require-cuda-inference
```

The retained `--require-training` option is a deprecated, warning-emitting alias
for `--require-cuda-inference`. Training readiness is no longer the primary
active contract.

Readiness means the reported prerequisites were observable at collection time.
It does not prove model fit, execution success, timing, waveform quality,
pronunciation, or linguistic correctness.

## M5 service readiness

`GET /ready` exposes only sanitized readiness booleans and bounded queue state.
It distinguishes service admission, artifact-root readiness, core-environment
readiness, optional CPU/CUDA runtime readiness, and adapter loaded state. A
lazy unloaded adapter is not a failure: optional runtime readiness may be false
while the metadata/control service remains ready to admit work. A later
synthesis request can still return `dependency_unavailable` or
`device_unavailable`.

The readiness response does not include OS identity, device name, package
paths, environment values, the artifact root, hostname, username, or client
address. `GET /health` is intentionally independent of CUDA, model load, and
artifact readiness.

## M6 observed environment

The sanitized 2026-09-09 authorized-hardware report recorded Ubuntu 24.04
under WSL2, Linux x86-64, CPython 3.12.3, Git 2.43.0, and uv 0.11.28. The
separate frozen MMS environment installed workbench 0.5.0, PyTorch 2.12.0
with CUDA build 13.0, Transformers 5.13.1, safetensors 0.8.0, Accelerate
1.14.0, and SciPy 1.18.0.

The NVIDIA driver was visible through WSL without modification. PyTorch
reported one NVIDIA GeForce RTX 4070 with 12,282 MiB, CUDA capability 8.9,
and float32, float16, and bfloat16 support. Both real adapters resolved to
CUDA/float32. Core, CPU-inference, CUDA-inference, and external-artifact
readiness were true at collection time.

These facts describe one run. They do not establish support for another
driver, device, OS, dtype, or timing profile, and they make no cross-device
waveform-equivalence claim. The full report remains outside Git; the sanitized
summary is in `reports/validation/m6_reproduction_validation.md`.
