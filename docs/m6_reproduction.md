# M6 reproduction and authorized-hardware procedure

Milestone M6 was executed on 2026-09-09 as an engineering release-candidate
demonstration. It is not a release approval and it provides no pronunciation,
naturalness, intelligibility, linguistic-correctness, or cross-device
equivalence finding.

All commands below run in WSL/Linux x86-64 with CPython 3.12. Generated files,
model snapshots, and caches remain outside Git. Replace the placeholder with an
existing external directory and do not publish its resolved value.

```bash
export TTS_WORKBENCH_ARTIFACT_ROOT="<external-artifact-root>"
export HF_HOME="${TTS_WORKBENCH_ARTIFACT_ROOT}/cache/huggingface"
export TORCH_HOME="${TTS_WORKBENCH_ARTIFACT_ROOT}/cache/torch"
export UV_CACHE_DIR="${TTS_WORKBENCH_ARTIFACT_ROOT}/cache/uv"
mkdir -p "${HF_HOME}" "${TORCH_HOME}" "${UV_CACHE_DIR}" \
  "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/prompts" \
  "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/runs" \
  "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/qc" \
  "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/benchmarks"
```

Never print or commit the resolved environment values. Do not place the
external directory below the repository.

## Clean core reproduction

The first synchronization may populate only the locked core/development cache.
The second environment proves that the same lock can synchronize offline. No
MMS extra, model host, PyTorch, Transformers, checkpoint, or audio is used.

```bash
M6_CORE_DIR="$(mktemp -d /tmp/tts-workbench-m6-core.XXXXXX)"
uv lock --check

UV_PROJECT_ENVIRONMENT="${M6_CORE_DIR}/online" \
  uv sync --frozen

UV_PROJECT_ENVIRONMENT="${M6_CORE_DIR}/offline" UV_OFFLINE=1 \
  uv sync --frozen

CORE_PYTHON="${M6_CORE_DIR}/offline/bin/python"
"${CORE_PYTHON}" -c \
  "import importlib.util; assert importlib.util.find_spec('torch') is None; assert importlib.util.find_spec('transformers') is None"
"${CORE_PYTHON}" -c \
  "import sys, tts_workbench, tts_workbench.service.contracts; assert 'torch' not in sys.modules; assert 'transformers' not in sys.modules"

"${M6_CORE_DIR}/offline/bin/tts-workbench-config"
"${M6_CORE_DIR}/offline/bin/tts-workbench-models" validate
"${M6_CORE_DIR}/offline/bin/tts-workbench-models" list
"${M6_CORE_DIR}/offline/bin/tts-workbench-privacy-scan"
"${CORE_PYTHON}" -m pytest --cov=tts_workbench --cov-branch \
  --cov-report=term-missing
```

Run Ruff formatting/lint, strict MyPy, pre-commit, all eight command help paths,
service schema/OpenAPI metadata paths, and the package-content scans described
in `reports/validation/m6_reproduction_validation.md`. Build the wheel outside
Git, inspect it, and reinstall that wheel into the clean core environment:

```bash
uv build --wheel --out-dir "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/wheel"
"${CORE_PYTHON}" -m zipfile -l \
  "${TTS_WORKBENCH_ARTIFACT_ROOT}"/m6/wheel/*.whl
uv pip install --python "${CORE_PYTHON}" --reinstall --no-deps \
  "${TTS_WORKBENCH_ARTIFACT_ROOT}"/m6/wheel/*.whl
"${CORE_PYTHON}" -c "import tts_workbench; assert tts_workbench.__version__ == '0.5.0'"
```

## Separate locked MMS environment

This is intentionally a second environment. Do not upgrade individual
packages or install an unregistered checkpoint source.

```bash
M6_MMS_DIR="$(mktemp -d /tmp/tts-workbench-m6-mms.XXXXXX)"
UV_PROJECT_ENVIRONMENT="${M6_MMS_DIR}/env" UV_LINK_MODE=copy \
  uv sync --frozen --extra mms
MMS_PYTHON="${M6_MMS_DIR}/env/bin/python"

"${M6_MMS_DIR}/env/bin/tts-workbench-env" --json \
  --output "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/environment.json" \
  --require-artifact-root --require-core --require-cpu-inference \
  --require-cuda-inference
"${M6_MMS_DIR}/env/bin/tts-workbench-mms-smoke" --preflight-only
```

The 2026-09-09 run resolved `torch==2.12.0+cu130`,
`transformers==5.13.1`, `safetensors==0.8.0`, `accelerate==1.14.0`,
and `scipy==1.18.0` from `uv.lock`. PyTorch reported the RTX 4070 and CUDA
before any checkpoint execution. No driver or WSL kernel change was made.

## Vietnamese prompt provenance gate

The registered reference is
`external:vietnam-constitution-2013-article-1`. Its publisher/author is the
National Assembly of Vietnam, and the primary record is the Government Portal
entry for the 2013 Constitution, issued 2013-11-28. The source scan is the
portal's attached PDF. WIPO Lex's English rendering of Vietnam Intellectual
Property Law No. 50/2005/QH11, Article 15(2), excludes legal documents and
their official translations from copyright protection. This is the
public-domain basis for the scoped local, non-commercial demonstration.

- Primary record: https://vanban.chinhphu.vn/?classid=1&docid=171264&pageid=27160&typegroupid=1
- Primary source scan: https://datafiles.chinhphu.vn/cpp/files/vbpq/2013/12/hp.pdf
- Legal-basis source: https://www.wipo.int/wipolex/en/legislation/details/12011
- Accessed: 2026-09-09
- Prompt SHA-256:
  `b6919cd1f33ec808355462bfa29e8444f8525560f8223d0486e67b35f29854c5`

The prompt text is deliberately absent from Git. The recorded extraction used
the unmodified first sentence of Article 1 from the official scan. These
commands keep source material and OCR output external and emit only a hash:
Ubuntu needs the ordinary `poppler-utils`, `tesseract-ocr`, and
`tesseract-ocr-vie` packages for this extraction.

```bash
curl -fsSL \
  "https://datafiles.chinhphu.vn/cpp/files/vbpq/2013/12/hp.pdf" \
  -o "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/prompts/constitution-2013-source.pdf"
mkdir -p "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/prompts/ocr-pages"
pdftoppm -f 1 -l 5 -jpeg -r 160 \
  "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/prompts/constitution-2013-source.pdf" \
  "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/prompts/ocr-pages/page"
for image in "${TTS_WORKBENCH_ARTIFACT_ROOT}"/m6/prompts/ocr-pages/page-*.jpg; do
  base="${image%.jpg}"
  tesseract "${image}" "${base}" -l vie 2>/dev/null
done
sed -n '43,46p' \
  "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/prompts/ocr-pages/page-01.txt" \
  | tr '\n' ' ' | sed -E 's/[[:space:]]+/ /g; s/^ //; s/ $//' \
  > "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/prompts/vie-prompt.txt"
printf '\n' >> "${TTS_WORKBENCH_ARTIFACT_ROOT}/m6/prompts/vie-prompt.txt"
"${MMS_PYTHON}" -c \
  "from pathlib import Path; import hashlib, os; p=Path(os.environ['TTS_WORKBENCH_ARTIFACT_ROOT'])/'m6/prompts/vie-prompt.txt'; print(hashlib.sha256(p.read_text(encoding='utf-8').strip().encode()).hexdigest())"
```

If the hash differs, do not run Vietnamese inference and re-audit the source;
do not manually correct, translate, or replace the text.

## Immutable CUDA inference, QC, and benchmarks

Model access is explicitly acknowledged. The repository/revision pair is
resolved only through `configs/models/registry.yaml`.

```bash
"${M6_MMS_DIR}/env/bin/tts-workbench-mms-smoke" \
  --acknowledge-model-access --model mms-eng --device cuda --seed 555 \
  --output m6/runs/mms-eng.wav
"${M6_MMS_DIR}/env/bin/tts-workbench-mms-smoke" \
  --acknowledge-model-access --model mms-vie \
  --text-file m6/prompts/vie-prompt.txt --device cuda --seed 555 \
  --output m6/runs/mms-vie.wav

"${M6_MMS_DIR}/env/bin/tts-workbench-qc" analyze \
  --input m6/runs/mms-eng.wav --output m6/qc/mms-eng.json
"${M6_MMS_DIR}/env/bin/tts-workbench-qc" analyze \
  --input m6/runs/mms-vie.wav --output m6/qc/mms-vie.json

"${M6_MMS_DIR}/env/bin/tts-workbench-benchmark" run \
  --acknowledge-model-access --model mms-eng \
  --config configs/benchmark/cuda.yaml \
  --output m6/benchmarks/mms-eng.json
"${M6_MMS_DIR}/env/bin/tts-workbench-benchmark" run \
  --acknowledge-model-access --model mms-vie \
  --prompt-file m6/prompts/vie-prompt.txt \
  --config configs/benchmark/cuda.yaml \
  --output m6/benchmarks/mms-vie.json
```

Each adapter owns at most one model. Explicit unload clears model/tokenizer
references, triggers collection, and releases unused CUDA cache before the next
owner or process shutdown.

## Real loopback service demonstration

Use two shells in the same locked MMS environment. The configuration enforces
loopback-only binding, one worker, one model owner, one active operation, a
finite FIFO queue, and disabled access logging.

```bash
# shell 1
"${M6_MMS_DIR}/env/bin/tts-workbench-serve" run \
  --acknowledge-model-access

# shell 2
"${MMS_PYTHON}" scripts/probe_local_service.py \
  --vie-prompt-file m6/prompts/vie-prompt.txt
```

The probe calls health, readiness, and registry metadata; safely rejects one
unknown model; verifies rejection creates no artifact; then executes both
registered models on CUDA. It never prints prompt text. Stop shell 1 with
Ctrl-C and verify no service process or listener remains.

## Retention and non-claims

Keep raw prompts, official-source downloads, OCR intermediates, model caches,
WAVs, run manifests, full environment reports, QC JSON, benchmark JSON, and
service outputs under the external root. They are local review evidence, not
Git or wheel content. Regenerate to a new path because every report/artifact
store rejects collisions.

M6 validates reproducibility, registry resolution, CUDA execution, transaction
integrity, structural waveform sanity, bounded timing, and local-service
controls on one machine. It does not validate any language, speaker, or
application. Only M7 may audit final risks and determine disposition.
