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
