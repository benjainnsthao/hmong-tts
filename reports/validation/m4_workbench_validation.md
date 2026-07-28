# M4 workbench validation

Date: 2026-07-28

Scope: non-linguistic waveform QC, deterministic fake-backed benchmarking, and
generalized environment capability reporting. This is new M4 evidence;
historical validation reports were not modified.

## Environment

- Python: 3.12.13
- Platform family: Windows, x86-64
- Dependency mode: locked core and development groups only
- Optional MMS group: not installed for M4 validation
- Network, model weights/caches, GPU execution, real audio, external audio, and
  native-language content: not used

## Commands and results

```text
git fetch --prune origin
git status --short --branch
git rev-parse HEAD
git rev-parse origin/rescope/audited-tts-workbench
git rev-parse main
git rev-parse archive/white-hmong-single-speaker-tts-v0.1
git rev-list --left-right --count HEAD...origin/rescope/audited-tts-workbench
```

PASS before implementation: clean M3 start, active local/remote HEAD
`793cd026663cb387213af336633d5b5d8806d5f5`, zero divergence, and unchanged
`main`/archive at `fd1756485b1e1b75fd1efee5e37519fa8e255415`.

```text
python -m uv lock --check
python -m uv sync --frozen --offline
python -m uv run ruff format --check .
python -m uv run ruff check .
python -m uv run mypy src
```

PASS. Lock change is limited to the local distribution version from 0.2.0 to
0.3.0; no dependency was added.

```text
python -m uv run tts-workbench-config
python -m uv run tts-workbench-models validate
python -m uv run tts-workbench-models list --json
python -m uv run tts-workbench-privacy-scan
```

PASS. Benchmark, inference, and QC schema version 1 configurations parse. The
unchanged registry has two immutable entries. The privacy/artifact scan passes.

```text
python -m uv run pytest --cov=tts_workbench --cov-branch --cov-report=term-missing -q
```

PASS: 180 fully synthetic tests; 78% aggregate branch-aware coverage.

```text
python -m uv run pytest tests/unit/test_waveform_qc.py \
  tests/unit/test_benchmark.py tests/unit/test_environment.py \
  --cov=tts_workbench.qc.analysis \
  --cov=tts_workbench.benchmark.runner \
  --cov=tts_workbench.environment.readiness \
  --cov-branch --cov-report=term-missing -q
```

PASS: 44 focused tests; 96% combined branch-aware coverage for new core M4
calculation/orchestration modules.

```text
python -m uv run pre-commit run --all-files
python -c "<package/lazy-import assertions>"
tts-workbench-{config,env,mms-smoke,models,privacy-scan,qc,benchmark} --help
tts-workbench-qc schema
tts-workbench-qc validate-config
tts-workbench-benchmark schema
tts-workbench-benchmark validate-config
git diff --check
git diff --cached --check
```

PASS. All seven help paths and M4 metadata operations ran offline without
importing PyTorch or Transformers.

## Scope and preservation audit

- No FastAPI/HTTP service, queue, concurrency, UI, deployment, or M5 code.
- No model download/execution or optional ML import during validation.
- No tracked audio, checkpoint, weight, tensor, cache, or private artifact.
- No LUFS, SNR, PESQ, STOI, MOS, ASR, pronunciation, perceptual, or
  linguistic-quality implementation.
- No White Hmong prompt, rule, tag, normalization, or capability claim.
- M3 inference/registry/artifact behavior remains regression-tested.
- Existing historical evidence and
  `docs/deferred/white_hmong_native_validation.md` were unchanged.
- NV-001 through NV-008 remain unresolved and deferred **[NV]**.
