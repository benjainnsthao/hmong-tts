# M6 reproduction validation

Validation date: 2026-09-09

Branch: `rescope/audited-tts-workbench`

Baseline: `fb72a5e87f9b3841d29ff4a0717546646e188422`

Evidence scope: engineering reproduction and release-candidate validation only

## Safety and environment

- Repository origin, clean tree, branch ancestry, and protected refs: PASS.
- Required M5 baseline contained by the active remote branch: PASS.
- Local/remote protected `main` remained
  `fd1756485b1e1b75fd1efee5e37519fa8e255415`: PASS.
- Preservation branch was absent locally and was not created, changed, or
  pushed: PASS.
- Platform: Ubuntu 24.04 under WSL2, Linux x86-64, CPython 3.12.3, Git 2.43.0,
  uv 0.11.28.
- GPU: NVIDIA GeForce RTX 4070, driver 610.62 visible through WSL, 12,282 MiB
  reported; PyTorch CUDA build 13.0, compute capability 8.9.
- Supported CUDA dtype report: float32, float16, bfloat16. Both checkpoint
  executions resolved to CUDA/float32.
- External artifact/cache boundary and sanitized capability report: PASS.
- Driver, WSL kernel, firmware, and host security settings changed: no.

The driver version is retained only in this sanitized report as a compatibility
fact. No hostname, user, client address, environment value, cache path, or
absolute artifact path is recorded.

## Primary-source audit

Accessed 2026-09-09:

- uv Python support and frozen/offline CLI behavior:
  https://docs.astral.sh/uv/reference/policies/python/ and
  https://docs.astral.sh/uv/reference/cli/
- PyTorch Linux/CUDA/Python guidance and `torch==2.12.0` metadata:
  https://docs.pytorch.org/get-started/locally/ and
  https://pypi.org/project/torch/2.12.0/
- `transformers==5.13.1`, `safetensors==0.8.0`,
  `accelerate==1.14.0`, and `scipy==1.18.0` metadata:
  https://pypi.org/project/transformers/5.13.1/,
  https://pypi.org/project/safetensors/0.8.0/,
  https://pypi.org/project/accelerate/1.14.0/, and
  https://pypi.org/project/scipy/1.18.0/
- Exact English checkpoint:
  https://huggingface.co/facebook/mms-tts-eng/tree/c71de0fe7204c83f1c10820a7d696d0b450048ba
- Exact Vietnamese checkpoint:
  https://huggingface.co/facebook/mms-tts-vie/tree/b58928d033932a49aa8e3d6cf11625b25fe928d2
- Vietnamese prompt primary record/source and public-domain basis:
  https://vanban.chinhphu.vn/?classid=1&docid=171264&pageid=27160&typegroupid=1,
  https://datafiles.chinhphu.vn/cpp/files/vbpq/2013/12/hp.pdf, and
  https://www.wipo.int/wipolex/en/legislation/details/12011.

The checkpoint pages resolved the registered revisions, listed CC BY-NC 4.0,
and exposed safetensors files. The runtime packages support Python 3.12 under
their published metadata and the locked Linux x86-64 artifacts installed
successfully. Both public checkpoint repositories allowed unauthenticated exact
revision access and emitted only a rate-limit advisory; no token or credential
was required or recorded. Repository code remains all rights reserved pending
the M7 owner decision; checkpoint use remains local and non-commercial; weights
are not redistributed.

The Vietnamese prompt is an unmodified sentence from Article 1 of the 2013
Constitution published by the National Assembly of Vietnam. Vietnam IP Law
No. 50/2005/QH11 Article 15(2), as published by WIPO Lex, excludes legal
documents and official translations from copyright protection. Raw text stayed
outside Git. Registered reference:
`external:vietnam-constitution-2013-article-1`; SHA-256:
`b6919cd1f33ec808355462bfa29e8444f8525560f8223d0486e67b35f29854c5`.
Extraction used the ordinary WSL packages pdftotext 24.02.0, Tesseract 5.3.4,
and Vietnamese language data package 4.1.0-2; no OCR output is committed.

## Core reproduction

- `uv lock --check`: PASS; 85 locked packages.
- Clean frozen core synchronization: PASS; 41 packages, no MMS extra.
- Second clean frozen offline core synchronization from the external uv cache:
  PASS; 41 packages.
- Current checkout package install and version 0.5.0 import: PASS.
- Ordinary package, contract, configuration, service-schema, OpenAPI, and all
  eight help imports without PyTorch/Transformers: PASS.
- Active configuration and registry validation/listing: PASS; schema version 1,
  two exact immutable models.
- Format, Ruff, strict MyPy, privacy/artifact scan, synthetic suite with branch
  coverage, focused service coverage, in-process ASGI tests, and pre-commit:
  PASS. The synthetic suite contains 261 passing tests with 81.78% aggregate
  branch-aware coverage; 77 focused service tests pass with 96.65% branch-aware
  coverage.
- Wheel build, clean install, inventory inspection, old-package/old-command
  absence, and forbidden-content scan: PASS.

One ignored legacy bytecode-only namespace left by the pre-sync branch switch
was moved intact to the external M6 evidence area before the clean reproduction.
No tracked or authored work was deleted or overwritten.

## Optional runtime and immutable checkpoint execution

Locked runtime: `audited-tts-workbench==0.5.0`, `torch==2.12.0+cu130`,
`transformers==5.13.1`, `safetensors==0.8.0`, `accelerate==1.14.0`, and
`scipy==1.18.0`. CUDA and artifact readiness gates passed before model access.

| Model | Repository and immutable revision | Prompt SHA-256 | CUDA/dtype | Frames / duration | WAV SHA-256 | Integrity |
|---|---|---|---|---:|---|---|
| `mms-eng` | `facebook/mms-tts-eng@c71de0fe7204c83f1c10820a7d696d0b450048ba` | `f8cc7678783377f15fd576e51b2b1fffdf969a591415c3858f816042a1194892` | CUDA / float32 | 38,656 / 2.416 s | `fbe87742c0e30496b0821b384f22a319ee12a9fb882e81daaa810301da5a2a1f` | PASS |
| `mms-vie` | `facebook/mms-tts-vie@b58928d033932a49aa8e3d6cf11625b25fe928d2` | `b6919cd1f33ec808355462bfa29e8444f8525560f8223d0486e67b35f29854c5` | CUDA / float32 | 185,600 / 11.600 s | `85cd0d92185d1eaa20d86b63803965ba38f600b496e46057e29151ac18ae60f3` | PASS |

Both WAVs reopened as mono 16 kHz PCM16. Frame counts, sample rate, channel
count, SHA-256, root-relative path, registry identity, requested/resolved
device, dtype, seed 555, generation settings, and manifest fields were mutually
consistent. Manifests and ordinary logs contained neither raw prompt nor
absolute path. Each adapter owned at most one model and unloaded explicitly.

## Structural QC and bounded benchmark

The unchanged `configs/qc/default.yaml` thresholds passed for both outputs.
These are structural engineering checks only.

| Model | Peak | RMS | DC offset | Clipping ratio | Total near-silence | Result |
|---|---:|---:|---:|---:|---:|---|
| `mms-eng` | 0.738586 | 0.110700 | -0.000331 | 0 | 0.331255 | `qc_passing` |
| `mms-vie` | 0.829498 | 0.102642 | 0.000176 | 0 | 0.288513 | `qc_passing` |

The dedicated CUDA config uses one excluded warmup and three measured
repetitions. Immutable snapshots were cache-resident after direct inference;
the M4 cold-load measurement covers a fresh adapter/model load, not network
download. Values describe this run only.

| Model | Cold load | Audio duration | Median synthesis | p95 synthesis | Median RTF | p95 RTF | Failures |
|---|---:|---:|---:|---:|---:|---:|---:|
| `mms-eng` | 2.374749 s | 2.416 s | 0.044189 s | 0.044990 s | 0.018290 | 0.018622 | 0 |
| `mms-vie` | 2.337115 s | 11.600 s | 0.111316 s | 0.114130 s | 0.009596 | 0.009839 | 0 |

CPU peak and CUDA allocated/reserved observations were available. After
explicit model unload and unused-cache release, the live PyTorch process still
reported 8,519,680 allocated bytes and 20,971,520 reserved bytes for its CUDA
runtime context; these observations are not reported as zero or interpreted as
a retained model.

## Real service demonstration

- Loopback-only configured bind, one Uvicorn worker, one model owner, one active
  operation, finite FIFO coordination, access logging disabled: PASS.
- `GET /health`: healthy.
- `GET /ready`: ready.
- `GET /v1/models`: both exact registry entries.
- `POST /v1/synthesize`: success for `mms-eng` and `mms-vie` on CUDA; two
  atomic WAV/manifest pairs committed outside Git.
- Unknown model rejection: sanitized 404 category
  `unknown_or_unapproved_model`; no request-text echo and no partial artifact.
- No access/client record, backend exception, prompt, or absolute artifact path
  appeared in service output: PASS.
- Shutdown waited, adapter unloaded, process exited, and no listener remained:
  PASS.

## Git completion and scope audit

- Candidate wheel: 45 members, eight expected command entry points, no old
  package/command, optional dependency, audio, weight, cache, raw prompt, or
  unexpected generated member; clean wheel-only install imported version 0.5.0.
- Format, Ruff, strict MyPy, complete synthetic/in-process ASGI suites,
  aggregate/focused coverage, full pre-commit, all metadata/help gates,
  protected-ref checks, and `git diff --check`: PASS.
- Staged privacy, raw-prompt, absolute/private-path, tracked-artifact,
  historical-evidence, deferred-NV, active-source-scope, and
  `git diff --cached --check` scans: PASS.
- Exactly one M6 commit was created and pushed only to
  `rescope/audited-tts-workbench`; local and remote active heads match and the
  working tree is clean. Protected refs remain unchanged.

No generated audio, model weights, cache data, raw prompt, machine identity,
private path, credential, or environment value is committed. Historical M1–M5
reports and NV-001 through NV-008 remain unchanged. Active source contains no
public bind, multi-owner/worker mode, unbounded queue, CORS, UI, analytics,
telemetry, tunnel, deployment, production fake, training/fine-tuning execution,
adaptation, perceptual/language metric, unsupported language claim, or M7
release disposition.

M6 creates a release candidate only. M7 is next and has not begun.
