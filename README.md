# Audited pretrained TTS workbench

The long-term purpose is useful speech technology for the Hmong community.
This release scope is a reproducible **local engineering workbench**, with
registered English and Vietnamese demonstrations. Recruiters are a secondary
audience for its engineering methods and evidence.

M7 does **not** establish Hmong support, pronunciation accuracy, linguistic
correctness, perceptual quality, or application readiness. White Hmong work
and NV-001 through NV-008 remain deferred **[NV]**. Community-language support
requires a separately authorized phase with community participation,
appropriate licensing, and native-speaker validation.

The historical single-speaker project is preserved at commit
`fd1756485b1e1b75fd1efee5e37519fa8e255415`, with a browsable record under
[`docs/history/white_hmong_single_speaker/`](docs/history/white_hmong_single_speaker/README.md).
The preservation branch is protected when present; this checkout did not have
that local branch at M7 discovery.

## M7 release audit

The validated distribution is `audited-tts-workbench` **1.0.0**, with eight
`tts-workbench-*` commands. The
[release decision](docs/m7_release_decision.md),
[owner approval record](docs/m7_owner_approval.json), and
[validation evidence](reports/validation/m7_release_validation.md) distinguish
measured results from final human acceptance. M7's public-release gates are
complete at commit `e4ebfad89383522c26d64a00563a44afe1aab5ba`, with the owner's
approved `release` disposition, successful exact-commit validation, active-branch
push, and [passing CI](https://github.com/benjainnsthao/hmong-tts/actions/runs/34558588222).

The first M7 commit was pushed at the owner's request after its clean-worktree
sdist failed a privacy check. The packaging correction and its renewed approval
are tracked in the decision record; the earlier approval applies to the previous
candidate. The correction passed package and privacy checks in clean ordinary
and Git worktree checkouts. Packages and GitHub releases have not been published.

See [post-M7 next steps](docs/post_m7_next_steps.md) for the completed handoff,
maintenance dates, proposed community scoping work, and the separate
authorization needed for integration, publication, or future development.

The audit reproduces both immutable checkpoints on an RTX 4070 using
CUDA/float32, bounded CPU diagnostics, structural QC, timing benchmarks, and
the real local service. These observations establish engineering behavior on
one environment; they do not establish language quality or cross-device
waveform/timing equivalence.

## Try the local browser dashboard

The dashboard provides text entry, an English example, speech generation,
audio playback and seeking, WAV downloads, and the last eight results from
the current page. Device, seed, and speed controls are under Advanced settings.

Install once from the repository on Linux/WSL x86-64 with Python 3.12 and uv:

```bash
UV_PROJECT_ENVIRONMENT="$HOME/.local/share/tts-workbench/venv" \
  uv sync --frozen --extra mms --python 3.12
```

Then launch:

```bash
bash scripts/launch-local.sh
```

Open **http://127.0.0.1:8000/**. Choose **Load example**, **Generate speech**,
then press play. The launcher acknowledges local model access; first generation
may download/load the voice and take longer. Stop with Ctrl-C after generation.

Defaults keep the environment at `$HOME/.local/share/tts-workbench/venv` and
artifacts at `$HOME/tts-workbench-artifacts`, with model caches below that root.
Existing environment/root/cache settings are respected. An explicitly set
artifact root must already exist. No Node build, separate frontend server, or
external CDN is required. See [dashboard usage and testing](apps/README.md).

Use text you own or have permission to test. Custom English text is recorded
as unreviewed. Vietnamese requires the retained external prompt and the source
review in [M7 reproduction](docs/m7_reproduction.md); no Vietnamese example is
bundled. Model use remains local and noncommercial; local downloads do not
authorize publication. **Hmong speech is not implemented.**

This browser feature is subsequent development. M7's release commit, manifest,
and owner approval remain evidence for the historical release.

## Reproduce the core

Use Python 3.12 on Linux/WSL x86-64. Set `UV_PROJECT_ENVIRONMENT` to an external
virtual environment before synchronization. Complete external-environment,
cache, offline, package, and runtime commands are in
[`docs/m7_reproduction.md`](docs/m7_reproduction.md).

```bash
uv sync --frozen
uv run --frozen tts-workbench-config
uv run --frozen tts-workbench-models validate
uv run --frozen tts-workbench-models list
uv run --frozen tts-workbench-qc schema
uv run --frozen tts-workbench-benchmark schema
uv run --frozen tts-workbench-serve validate-config
uv run --frozen tts-workbench-serve openapi
uv run --frozen tts-workbench-env --json
uv run --frozen tts-workbench-privacy-scan
uv run --frozen pytest --cov=tts_workbench --cov-branch --cov-fail-under=78
```

Ordinary imports, all eight help commands, metadata operations, and synthetic
tests work without PyTorch, Transformers, model downloads, or a GPU. The MMS
extra is separate and large. Its imports and checkpoint access are explicit.
The registry alone selects repositories and immutable revisions; no caller
can select an alternative source. Model weights load through safetensors,
with no fallback to pickle weights.

## Local service and engineering evidence

The service supports `GET /health`, `GET /ready`, `GET /v1/models`, and
`POST /v1/synthesize`. It requires model-access acknowledgement, literal
loopback binding, one Uvicorn worker, one model owner, one active inference
operation, and a finite FIFO queue. Access, prompt, and client logging are
disabled. The caller cannot choose repositories, revisions, or artifact paths.

Loopback is not authentication. Use this service only with trusted local
clients and approved prompts. Input character and queue limits do not impose
a hard HTTP-body, total-work, output-duration, or disk quota. Queue deadlines
apply before execution; active native calls are not safely preemptible and
shutdown waits for them. See [local service](docs/local_service.md) and its
[threat model](docs/service_threat_model.md).

QC retains the M4 thresholds and `engineering_sanity_check` labels.
Benchmarks distinguish cold loading, excluded warmup, measured repetitions,
median, nearest-rank p95, real-time factor, failures, and observable memory.
No MOS, ASR, pronunciation, speaker similarity, or language-ranking metric is
claimed. See [QC](docs/waveform_qc.md), [benchmarking](docs/benchmarking.md),
and the [M7 engineering summary](docs/m7_portfolio_summary.md).

## Artifacts and compatibility

`TTS_WORKBENCH_ARTIFACT_ROOT` must name an existing absolute directory outside
the repository. `HF_HOME` and `TORCH_HOME` must also remain external. Weights,
caches, raw prompts/source material, WAVs, and detailed reports stay outside
Git and release packages. Each WAV has an atomic success manifest containing
its checksum, prompt hash, registry/runtime/settings metadata, and only
root-relative artifact references.

**Breaking change:** version 1.0.0 removes `HMONG_TTS_DATA_ROOT` support.
Legacy-only configuration fails as an unset canonical root; if both are set,
only the canonical variable is used. See [migration](docs/m7_migration.md),
[artifact retention](artifacts/README.md), and [changelog](CHANGELOG.md).

## License and distribution

Covered original project code is **Apache-2.0**, including commercial reuse,
under the owner's conversational approval dated **2026-09-10**. Read
[LICENSE](LICENSE), [NOTICE](NOTICE), and
[third-party notices](THIRD_PARTY_NOTICES.md) for scope and attribution.

Apache-2.0 does not relicense third-party code, model weights, data, or outputs.
Both registered MMS checkpoints remain **CC BY-NC 4.0**, approved here only for
local non-commercial inference; their weights and generated audio are not
redistributed. Training-data lineage is not commercially cleared. The public
candidate contains original code, configuration, tests, documentation, and
sanitized engineering evidence. Package publication or deployment is a
separate authorization. See the [license/provenance matrix](docs/license_matrix.md).

All risk dispositions and limitations are in the
[release risk register](docs/release_risk_register.md). Next review:
**2026-12-09**, sooner for a material security, dependency, licensing, or
provenance issue. M1–M6 validation reports and the deferred native-validation
record remain historical evidence, unchanged by M7.
