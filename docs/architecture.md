# Workbench architecture — milestone M4

The repository has a provider-neutral inference data plane plus an M4
evaluation plane. It remains a library/CLI workbench, not an HTTP service.

```text
public repository
  audited-tts-workbench / tts_workbench
  configs/models/registry.yaml
             |
             v
  strict schema + policy validation
             |
             +--> models validate / models list
             |
             +--> InferenceRequest
                       |
                       v
                 InferenceExecutor
                 | registry lookup + prompt hash + timing
                 |
                 +--> TTSAdapter protocol
                 |      |
                 |      +--> MmsVitsAdapter
                 |             |
                 |             +--> injected fake backend (tests)
                 |             +--> lazy optional Transformers backend
                 |
                 +--> structural waveform validation
                 |
                 +--> AtomicArtifactStore
                              |
                              +--> WAV (published first)
                              +--> success manifest (commit marker, last)
                              |
                              +--> WaveformQcAnalyzer (separate read-only pass)
                                      |
                                      +--> AtomicJsonReportStore

  ModelRegistry + TTSAdapter
             |
             +--> BenchmarkRunner
                    injected clock / resource observer / environment collector
                    |
                    +--> cold load
                    +--> excluded warmups
                    +--> measured warm synthesis + aggregate JSON

external artifact root
  TTS_WORKBENCH_ARTIFACT_ROOT
  model cache / weights / generated WAV + manifests / QC + benchmarks
```

The registry, license matrix, environment report, and artifact boundary remain
separate controls:

- the registry decides which immutable artifacts are eligible for scoped use;
- the license matrix records the supporting audit and limitations;
- environment detection establishes what the local machine can execute; and
- the external boundary prevents weights and generated audio from entering Git.

The adapter protocol exposes only identity, lifecycle state, load, synthesize,
and unload. Callers never receive tokenizer, model, tensor, or Transformers
objects. Each `MmsVitsAdapter` owns at most one loaded backend. Loading a
different model or changing the requested device unloads the old backend first;
loading the same model/device pair reuses the owned backend.

The executor rejects registry-invalid or unknown model IDs, prompt-reference
mismatches, and invalid artifact destinations before backend loading. The
MMS/VITS backend resolves repository and immutable revision only from the
validated registry. PyTorch and Transformers imports remain inside its explicit
load method.

The artifact writer creates closed temporary files beside their destinations,
reopens and validates the mono PCM WAV, serializes a strict schema-version-1
manifest, replaces the WAV, and replaces the manifest last. A failed
serialization, validation, or replacement removes temporary files and any WAV
owned by that failed transaction.

Repository-root detection requires the neutral committed markers
`pyproject.toml` and `configs/models/registry.yaml`; it does not depend on the
archived White Hmong project-plan pointer.

M3 still performs structural commit-safety validation only: finite non-empty
samples, positive sample rate, mono 16-bit PCM, successful reopen, and matching
positive frame metadata. M4 QC is a separate read-only analysis. It can label a
structurally valid committed artifact `qc_failing`, but it does not alter the
M3 transaction or success manifest.

`WaveformQcAnalyzer` accepts an in-memory `WaveformResult` or reopens an
artifact-root-relative WAV. The fixed rule order and configured thresholds
produce engineering-sanity-check evidence only. The generic JSON report store
serializes deterministically into a closed neighboring temporary file, rejects
collisions, and atomically replaces the destination.

`BenchmarkRunner` selects exactly one registry entry before adapter load.
Clock, adapter, registry, environment collector, and point-in-time resource
observer are injected. Cold load is timed separately; warmups execute but are
excluded from measured median and nearest-rank p95. No production fake, thread,
queue, process, HTTP lifecycle, or continuous telemetry exists.

Environment collection now builds a strict sanitized report with independent
core, CPU-inference, and CUDA-inference readiness. CUDA absence is not a core
failure, and no GPU product name is required. PyTorch and Transformers remain
lazy optional imports.

M4 contracts and report stores expose no raw prompt, absolute artifact root,
host/user/client identity, credential, private identifier, or model-cache path.
The M5 service/application layer remains unimplemented.

No runtime success or manifest field is linguistic-quality evidence. No
application layer may embed White Hmong normalization or capability rules while
NV-001 through NV-008 remain deferred **[NV]**.

The ordered delivery plan and milestone acceptance criteria are in
`docs/implementation_roadmap.md`.
