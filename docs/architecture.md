# Workbench architecture — milestone M3

The repository now has a provider-neutral inference data plane alongside the
M2 metadata control plane and external artifact boundary. It remains a
library/CLI workbench, not an HTTP service.

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

external artifact root
  TTS_WORKBENCH_ARTIFACT_ROOT
  model cache / weights / generated WAV + manifest / future benchmarks
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

M3 performs structural commit-safety validation only: finite non-empty samples,
positive sample rate, mono 16-bit PCM, successful reopen, and matching positive
frame metadata. Waveform QC, benchmarks, generalized environment readiness, and
service/application layers remain future milestones.

No runtime success or manifest field is linguistic-quality evidence. No
application layer may embed White Hmong normalization or capability rules while
NV-001 through NV-008 remain deferred **[NV]**.

The ordered delivery plan and milestone acceptance criteria are in
`docs/implementation_roadmap.md`.
