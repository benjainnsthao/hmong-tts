# Provider-neutral benchmarking

Milestone M4 benchmarks one explicitly selected audited registry entry through
the existing `TTSAdapter`. Synthetic fakes validate orchestration and
arithmetic; they do not establish real-model or device performance.

## Timing semantics

Cold-load duration starts immediately before `adapter.load` and ends
immediately after it returns or fails. Registry/request validation,
environment collection, memory observation, and report serialization are not
included.

Warm synthesis duration starts immediately before `adapter.synthesize` and
ends when it returns. Structural waveform validation, memory observation,
aggregation, unload, and report serialization are not included. Configured
warmup calls execute through the same adapter but are excluded from every
aggregate.

Generated audio duration is sample count divided by sample rate. Real-time
factor is synthesis seconds divided by generated audio seconds. Medians use the
ordinary sorted-sample median. p95 uses deterministic nearest rank:

```text
sorted_values[ceil(0.95 * N) - 1]
```

Only successful measured observations contribute timing and real-time-factor
aggregates. Structured measured failures contribute failure counts. A
successful load with any measured failure or an early `stop` is `partial`; all
configured measured repetitions succeeding is `completed`; load failure is
`failed`.

These timings do not promise cross-device timing equivalence or waveform
identity. Reports never rank models or languages and contain no quality score.

## Configuration and forwarding

`configs/benchmark/default.yaml` is strict schema version 1. Local defaults are
one excluded warmup, three measured repetitions, a hard maximum of ten, seed
555, the committed MMS/VITS generation settings, `auto` device selection,
point-in-time memory requested, `benchmarks/latest.json`, and `continue`
failure handling.

`configs/benchmark/cuda.yaml` preserves the same bounded repetitions, seed,
generation settings, memory observation, and failure handling while requiring
the intended `cuda` device. It exists for explicit authorized-hardware evidence
and does not change the portable default.

The runner injects clock, adapter, registry, resource observer, and environment
collector seams. It resolves an approved immutable model and matching prompt
reference before adapter load. The same model ID, device request, seed, and
generation settings are forwarded on every call.

The report includes:

- schema/evidence version and status;
- exact immutable registry and adapter identity;
- SHA-256 prompt hash, never prompt text;
- requested/resolved device, dtype, seed, and generation settings;
- Python/workbench and supplied optional backend versions;
- sanitized complete environment capabilities;
- cold load duration;
- warmup and measured observations;
- generated duration and real-time factor;
- measured median, nearest-rank p95, success/failure counts; and
- optional point-in-time memory before load, after load, after each synthesis,
  and after unload.

## Resource observations

CPU memory uses standard-library peak resident-set information where available.
CUDA allocated/reserved memory is read only from an already-imported runtime;
the observer never imports PyTorch solely for memory reporting. Missing
measurements are `unavailable`, not zero. Disabled observation is
`not_requested`. This is not continuous monitoring or telemetry.

Reports exclude raw prompts, absolute paths, users/hosts/addresses, credentials,
environment values, private identifiers, process arguments, model-cache paths,
and linguistic conclusions.

## CLI gate

```text
tts-workbench-benchmark schema
tts-workbench-benchmark validate-config
tts-workbench-benchmark run --model mms-eng --acknowledge-model-access
```

Schema, configuration, and help operations require no ML dependencies.
Execution fails closed unless `--acknowledge-model-access` is supplied. Models
without the registered built-in synthetic prompt require an
artifact-root-relative `--prompt-file` whose public license/provenance was
independently audited. Reports use the same atomic artifact-root JSON store as
QC.

M4 implementation and validation did not invoke the execution command, import
the optional ML runtime, download weights, or run a real checkpoint.

## M6 authorized-hardware observations

M6 separately executed the CUDA configuration on an RTX 4070 with PyTorch
2.12.0+cu130, Transformers 5.13.1, float32, seed 555, one excluded warmup,
and three successful measured repetitions per exact checkpoint. The English
run recorded 2.374749 seconds cold load, 0.044189 seconds median synthesis,
0.044990 seconds p95, 0.018290 median RTF, and 0.018622 p95 RTF. The
Vietnamese run recorded 2.337115 seconds cold load, 0.111316 seconds median
synthesis, 0.114130 seconds p95, 0.009596 median RTF, and 0.009839 p95 RTF.
Both failure counts were zero and CPU/CUDA memory observations were available.
The immutable snapshots were already present in the external model cache;
"cold load" retains the M4 definition of one fresh adapter/model load and does
not include checkpoint download time.

These are point-in-time engineering measurements for one environment, not a
cross-language ranking or quality finding. Full reports remain external; see
`reports/validation/m6_reproduction_validation.md` for sanitized evidence.
