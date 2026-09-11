# M7 reproduction and retained evidence

Audit/execution date: 2026-09-10. Workbench 1.0.0, Python 3.12,
Linux/WSL x86-64. Public owner licensing approval is separately dated
2026-09-10; final disposition is in `m7_owner_approval.json`.
All commands run from the repository unless stated otherwise. Never put
machine-local variable values in Git. Collision-rejecting inference/report
commands need new output labels on a later reproduction.

## External boundary and environments

Reuse an existing external directory for `TTS_WORKBENCH_ARTIFACT_ROOT`.
Do not create it inside Git, follow a symlink into Git, or overwrite M6 data.
The approved legacy variable is removed; see `m7_migration.md`.

```bash
set -e
: "${TTS_WORKBENCH_ARTIFACT_ROOT:?set an existing external directory}"
export HF_HOME="${TTS_WORKBENCH_ARTIFACT_ROOT}/cache/huggingface"
export TORCH_HOME="${TTS_WORKBENCH_ARTIFACT_ROOT}/cache/torch"
export UV_CACHE_DIR="${TTS_WORKBENCH_ARTIFACT_ROOT}/cache/uv"
export PRE_COMMIT_HOME="${TTS_WORKBENCH_ARTIFACT_ROOT}/cache/pre-commit"
export PYTHONDONTWRITEBYTECODE=1
export M7_LABEL="m7/$(date -u +%Y%m%dT%H%M%SZ)"
export M7_RUN="${TTS_WORKBENCH_ARTIFACT_ROOT}/${M7_LABEL}"
mkdir -p "${M7_RUN}"/{audit,logs,prompts,environment,tooling,packages}
export M7_CORE_DIR="$(mktemp -d -t tts-workbench-m7-core.XXXXXX)"
export M7_MMS_DIR="$(mktemp -d -t tts-workbench-m7-mms.XXXXXX)"
```

The measured run uses label `m7/20260910T122457Z`. Environments are temporary
external directories. HF/Torch caches are shared with retained M6; generated
M7 output is separate. No drivers, kernels, firmware, OS, or security settings
are changed. Sanitized capability evidence is in the M7 validation report.

## Clean core before optional MMS installation/import

```bash
uv lock --check
UV_PROJECT_ENVIRONMENT="${M7_CORE_DIR}/online" \
  uv sync --frozen --python 3.12
UV_PROJECT_ENVIRONMENT="${M7_CORE_DIR}/offline" \
  uv sync --frozen --offline --python 3.12
export CORE_PYTHON="${M7_CORE_DIR}/offline/bin/python"
export UV_PROJECT_ENVIRONMENT="${M7_CORE_DIR}/offline"
export COVERAGE_FILE="${M7_RUN}/tooling/coverage-aggregate"
export MYPY_CACHE_DIR="${M7_RUN}/tooling/mypy"
export RUFF_CACHE_DIR="${M7_RUN}/tooling/ruff"
uv build --out-dir "${M7_RUN}/packages"
uv pip install --python "${CORE_PYTHON}" --reinstall --no-deps \
  "${M7_RUN}/packages/audited_tts_workbench-1.0.0-py3-none-any.whl"
"${CORE_PYTHON}" - <<'PY'
import importlib.util, sys
import tts_workbench, tts_workbench.inference, tts_workbench.service
import tts_workbench.benchmark, tts_workbench.qc
assert tts_workbench.__version__ == '1.0.0'
for name in ('torch', 'transformers', 'hmong_tts'):
    assert importlib.util.find_spec(name) is None
assert 'torch' not in sys.modules and 'transformers' not in sys.modules
PY
for command in config env mms-smoke privacy-scan models qc serve benchmark; do
  "${M7_CORE_DIR}/offline/bin/tts-workbench-${command}" --help >/dev/null
done
"${M7_CORE_DIR}/offline/bin/tts-workbench-config"
"${M7_CORE_DIR}/offline/bin/tts-workbench-models" validate
"${M7_CORE_DIR}/offline/bin/tts-workbench-models" list --json
"${M7_CORE_DIR}/offline/bin/tts-workbench-qc" validate-config
"${M7_CORE_DIR}/offline/bin/tts-workbench-benchmark" validate-config
"${M7_CORE_DIR}/offline/bin/tts-workbench-benchmark" validate-config \
  --config configs/benchmark/cuda.yaml
"${M7_CORE_DIR}/offline/bin/tts-workbench-serve" validate-config
"${M7_CORE_DIR}/offline/bin/tts-workbench-serve" schema >/dev/null
"${M7_CORE_DIR}/offline/bin/tts-workbench-serve" openapi >/dev/null
"${M7_CORE_DIR}/offline/bin/tts-workbench-env" --json --require-core \
  --require-artifact-root --output "${M7_RUN}/environment/core.json"
"${M7_CORE_DIR}/offline/bin/tts-workbench-privacy-scan" --require-artifact-root
"${M7_CORE_DIR}/offline/bin/ruff" format --check .
"${M7_CORE_DIR}/offline/bin/ruff" check .
"${M7_CORE_DIR}/offline/bin/mypy" src
"${CORE_PYTHON}" -m pytest --cov=tts_workbench --cov-branch \
  --cov-fail-under=78 --cov-report=term-missing \
  --cov-report="json:${M7_RUN}/coverage-aggregate.json" \
  --basetemp "${M7_RUN}/tooling/pytest-aggregate" \
  -o "cache_dir=${M7_RUN}/tooling/pytest-cache"
COVERAGE_FILE="${M7_RUN}/tooling/coverage-service" \
  "${CORE_PYTHON}" -m pytest tests/unit/test_service*.py \
  --cov=tts_workbench.service --cov-branch --cov-fail-under=90 \
  --cov-report="json:${M7_RUN}/coverage-service.json" \
  --basetemp "${M7_RUN}/tooling/pytest-service" \
  -o "cache_dir=${M7_RUN}/tooling/pytest-cache-service"
"${M7_CORE_DIR}/offline/bin/pre-commit" run --all-files
```

The online core population accesses package/build hosts, not model hosts.
The separate offline sync uses only populated caches and does not install
optional ML packages. A subsequent package installation validates the actual
wheel. If source changes after building, rebuild/reinstall before testing;
an older installed wheel is not evidence for changed source. The final run
repeats all affected gates against the final candidate.

No-acknowledgement smoke, benchmark `run --model mms-eng`, and service `run`
commands must return exit 2 before backend execution. Canonical-only migration,
legacy-only failure, literal-loopback rejection, lazy imports, old-package/CLI
absence, schemas, FIFO/timeout/shutdown, privacy, and in-process ASGI behavior
are also covered by the complete synthetic suite.

## Current source audit and separate MMS environment

Before checkpoint access, review `m7_dependency_audit.md` and the active
`license_matrix.md`: exact PyPI metadata/advisories, Python/uv/runtime
compatibility, the two immutable cards and CC BY-NC terms, prompt provenance,
Apache/third-party notices, and permitted distribution scope. Query exact
`https://pypi.org/pypi/<name>/<locked-version>/json` records, including their
`vulnerabilities` and `yanked` fields. Save full responses only externally.
A current response is necessary; an earlier audit is not a perpetual clearance.

```bash
UV_PROJECT_ENVIRONMENT="${M7_MMS_DIR}/env" UV_LINK_MODE=copy \
  uv sync --frozen --extra mms --python 3.12
export MMS_PYTHON="${M7_MMS_DIR}/env/bin/python"
"${M7_MMS_DIR}/env/bin/tts-workbench-env" --json --require-core \
  --require-artifact-root --require-cuda-inference \
  --output "${M7_RUN}/environment/cuda.json"
"${M7_MMS_DIR}/env/bin/tts-workbench-mms-smoke" --preflight-only
```

Actual runtime: torch 2.13.0+cu130, transformers 5.13.1, CUDA build 13.0,
RTX 4070 visible, float32 selected. Advertised float16/bfloat16 support is
capability metadata, not evidence of model execution at those precisions.

## Vietnamese provenance gate

Use only the retained `m6/prompts/vie-prompt.txt`, copied unchanged into this
run's `prompts/vie-prompt.txt`. Re-download the Government Portal source PDF
and compare it with the retained M6 scan. Refresh the current Article 15(2)
legal-document exclusion and amendment audit described in `license_matrix.md`.
The M7 source download needed an ordinary retry; the final PDF matched M6.

```bash
curl -fsSL --retry 2 --max-time 90 \
  https://datafiles.chinhphu.vn/cpp/files/vbpq/2013/12/hp.pdf \
  -o "${M7_RUN}/prompts/constitution-2013-source.pdf"
cp "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/prompts/vie-prompt.txt" \
  "${M7_RUN}/prompts/vie-prompt.txt"
"${CORE_PYTHON}" - <<'PY'
import hashlib, os
from pathlib import Path
run = Path(os.environ['M7_RUN'])
text = (run / 'prompts/vie-prompt.txt').read_text(encoding='utf-8').strip()
assert hashlib.sha256(text.encode()).hexdigest() == (
    'b6919cd1f33ec808355462bfa29e8444f8525560f8223d0486e67b35f29854c5')
assert hashlib.sha256((run / 'prompts/constitution-2013-source.pdf').read_bytes()).hexdigest() == (
    '4036ec0b5843fbdd0596b75b6d6c99efa5e1b8c5936c27b9c829396a024767bb')
print('PASS: approved prompt and source identities')
PY
```

If retained text is unavailable, recover the same approved material using
`m6_reproduction.md`'s external extraction method and require the same hash.
Do not invent, translate, correct, or substitute text. Stop before Vietnamese
inference if source, legal basis, or hash verification fails. Nothing in these
commands automatically licenses another prompt. The English input is the
existing project-authored synthetic fixture under its documented policy.

## CUDA inference, repeats, QC, benchmarks, and CPU diagnostics

Every model source resolves only through `configs/models/registry.yaml`.
Fixed seed: 555. Generation: noise_scale 0.667,
noise_scale_duration 0.8, speaking_rate 1.0. Only the two registered
checkpoints are authorized. Each adapter owns at most one model and unloads
before handoff/process shutdown.

```bash
for model in mms-eng mms-vie; do
  prompt_args=()
  if [ "${model}" = mms-vie ]; then
    prompt_args=(--text-file "${M7_LABEL}/prompts/vie-prompt.txt")
  fi
  for suffix in '' '-repeat'; do
    "${M7_MMS_DIR}/env/bin/tts-workbench-mms-smoke" \
      --acknowledge-model-access --model "${model}" --device cuda --seed 555 \
      "${prompt_args[@]}" --output "${M7_LABEL}/runs/${model}${suffix}.wav"
  done
  "${M7_MMS_DIR}/env/bin/tts-workbench-qc" analyze \
    --input "${M7_LABEL}/runs/${model}.wav" \
    --output "${M7_LABEL}/qc/${model}.json"
  benchmark_prompt_args=()
  if [ "${model}" = mms-vie ]; then
    benchmark_prompt_args=(--prompt-file "${M7_LABEL}/prompts/vie-prompt.txt")
  fi
  "${M7_MMS_DIR}/env/bin/tts-workbench-benchmark" run \
    --acknowledge-model-access --model "${model}" \
    --config configs/benchmark/cuda.yaml "${benchmark_prompt_args[@]}" \
    --output "${M7_LABEL}/benchmarks/${model}.json"
done
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 "${MMS_PYTHON}" - <<'PY'
import os, torch
from tts_workbench.inference.mms_smoke import main
torch.set_num_threads(2)
torch.set_num_interop_threads(2)
label = os.environ['M7_LABEL']
for model in ('mms-eng', 'mms-vie'):
    args = ['--acknowledge-model-access', '--model', model, '--device', 'cpu',
            '--seed', '555', '--output', f'{label}/cpu/{model}.wav']
    if model == 'mms-vie':
        args += ['--text-file', f'{label}/prompts/vie-prompt.txt']
    assert main(args) == 0
PY
```

One warmup is excluded, three measured repetitions are aggregated, maximum
repetitions is ten. Report cold load separately; do not compare these two
prompts as language rankings. CPU diagnostics are one short approved request
per model with two intra/inter-op threads, not a CPU benchmark/support matrix.
CPU and CUDA WAV checksums differ here, illustrating the stated portability
limit; CUDA repeats within the same environment matched byte for byte.

## Real loopback service and observed unload

Use two shells with the same environment variables. The nested root preserves
default service output-prefix behavior while isolating M7 artifacts. The
server-runner seam observes the production adapter after Uvicorn shuts down;
it injects no fake backend or alternate model source.

```bash
# Shell 1: stop with Ctrl-C only after the probe completes and work is idle.
TTS_WORKBENCH_ARTIFACT_ROOT="${M7_RUN}" "${MMS_PYTHON}" - <<'PY'
import json, os
from pathlib import Path
import uvicorn
from tts_workbench.service.cli import main

def observe_shutdown(app, **settings):
    uvicorn.run(app, **settings)
    runtime = app.state.runtime
    state = runtime.coordinator.state
    result = {'adapter_lifecycle': runtime.adapter.state.lifecycle,
              'active_requests': state.active_requests,
              'pending_requests': state.pending_requests,
              'admission': state.admission}
    (Path(os.environ['M7_RUN']) / 'service-shutdown.json').write_text(json.dumps(result))
    assert result['adapter_lifecycle'] == 'unloaded'
    assert state.active_requests == state.pending_requests == 0
main(['run', '--acknowledge-model-access'], server_runner=observe_shutdown)
PY
# Shell 2, while the service is ready:
TTS_WORKBENCH_ARTIFACT_ROOT="${M7_RUN}" "${MMS_PYTHON}" \
  scripts/probe_local_service.py --vie-prompt-file prompts/vie-prompt.txt
```

The probe checks health/readiness/registry, rejects an unknown model without
artifact creation or prompt echo, then executes both approved prompts on CUDA.
The M7 harness confirmed the loopback port was unused before startup, polled
readiness, ran this probe, sent SIGINT only after the probe finished, awaited
exit 0, and confirmed the port was closed afterward. It recorded unloaded
adapter state, closed queue, and zero active/pending operations. There was one
worker/process; no access logging or persistent listener. No active native
call was cancelled and no destructive exhaustion test was run.

## Integrity, candidate identity, and release checks

```bash
"${MMS_PYTHON}" scripts/verify_m7_artifacts.py --run-prefix "${M7_LABEL}"
python3 scripts/release_manifest.py
uv lock --check
git diff --check
# After explicit file review/staging, before the final owner review:
"${M7_CORE_DIR}/offline/bin/tts-workbench-privacy-scan" --require-artifact-root
git diff --cached --check
```

The artifact verifier reopens eight real WAV/manifest pairs, validates schemas,
registry revision/source, prompt hash, seed/device/dtype/version, duration,
frames/channels/rate/checksum, QC/benchmark status, and paired-run identity.
Logs/manifests are additionally checked for prompt echo and actual private
path/identity values. Candidate, staged, history, package-content/license,
old-package/CLI, no-weight/audio/cache/raw-prompt, and protected-ref checks are
recorded in the validation report. Wheel/sdist are inspected as archives,
never blindly extracted into the repository.

Runtime evidence is bound to the pre-execution sorted path/SHA-256 inventory
of `src/`, `configs/`, `pyproject.toml`, and `uv.lock`. Its compact sorted-key
JSON digest is recorded in the M7 report. The packaging correction changes
only Hatch archive exclusions within that inventory's `pyproject.toml` entry:
all runtime source/configuration bytes, the lock, and parsed project/build-system
metadata still match. The corrective supplement records this comparison and
wheel runtime-byte equality (the README updates metadata); it does not claim the original whole-file digest is unchanged.
The complete review manifest then binds those files plus tests/docs/evidence,
with only the explicit self-reference/actual-owner-approval exclusions in
`m7_release_decision.md`. Revalidate affected gates after any content change.
A later exact-commit checkout check and normal active-branch push occur only
after the owner's new final approval. One additional corrective commit is
authorized; preserve the original commit without amending or rewriting it.

## Packaging regression and checkout comparison

Hatchling remains pinned to 1.29.0. Explicit `exclude = [".git"]` patterns on
both wheel and sdist targets exclude Git directories and worktree pointer files
at any depth. Reviewed 2026-09-10: [Hatch file selection](https://hatch.pypa.io/1.16/config/build/#patterns).
No build-system or dependency upgrade accompanies this correction.

Populate the pinned build cache with the normal core build, then run the real
archive regression tests offline. They use synthetic Git metadata at the
project root and inside the package, check both archive types and all notices,
and keep builds under pytest's external temporary root:

```bash
uv build --out-dir "${M7_RUN}/packages"
"${CORE_PYTHON}" -m pytest tests/unit/test_release_packaging.py \
  --basetemp "${M7_CORE_DIR}/packaging-tests" \
  -o "cache_dir=${M7_RUN}/tooling/packaging-pytest-cache"
```

For exact-commit verification, create a separate ordinary clone and a detached
worktree beneath a new native external temporary directory. No commit, branch
rewrite, or change to the original worktree is needed:

```bash
export M7_CHECKOUTS="$(mktemp -d -t tts-workbench-package-check.XXXXXX)"
git clone --no-hardlinks --single-branch --branch rescope/audited-tts-workbench \
  . "${M7_CHECKOUTS}/ordinary"
git -C "${M7_CHECKOUTS}/ordinary" worktree add --detach \
  "${M7_CHECKOUTS}/worktree" HEAD
uv build --offline "${M7_CHECKOUTS}/ordinary" \
  --out-dir "${M7_RUN}/packages-ordinary"
uv build --offline "${M7_CHECKOUTS}/worktree" \
  --out-dir "${M7_RUN}/packages-worktree"
cmp "${M7_RUN}/packages-ordinary/audited_tts_workbench-1.0.0-py3-none-any.whl" \
  "${M7_RUN}/packages-worktree/audited_tts_workbench-1.0.0-py3-none-any.whl"
cmp "${M7_RUN}/packages-ordinary/audited_tts_workbench-1.0.0.tar.gz" \
  "${M7_RUN}/packages-worktree/audited_tts_workbench-1.0.0.tar.gz"
```

Before approval, the same checkout comparison overlays each candidate file
onto these isolated checkouts, preserving `.git`, then verifies every copied
file/mode against the review manifest. After committing, use clean checkouts
of the exact approved commit without overlays. Archive inspection must reject
any `.git` path component, unsafe path, link, unexpected member, private value,
audio/weight/cache/prompt content, missing notice, or source-byte mismatch.
Compare sdist members to the complete candidate inventory plus generated
`PKG-INFO`; compare wheel source, metadata, entry points, and notices. Keep
full inventories, archive hashes, and failure logs external. Do not publish
the retained defective archive or its pointer content.

For repeated installation of rebuilt local wheels, bypass the distribution
cache to avoid a mounted-filesystem rename collision observed in this audit.
This command accesses neither dependency indexes nor model hosts:

```bash
uv pip install --offline --no-cache --python "${CORE_PYTHON}" \
  --reinstall --no-deps \
  "${M7_RUN}/packages-ordinary/audited_tts_workbench-1.0.0-py3-none-any.whl"
```
