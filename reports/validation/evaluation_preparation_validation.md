# Evaluation preparation and real dashboard validation

Date: **2026-09-25 UTC**. Starting branch:
`rescope/audited-tts-workbench`, dashboard commit `b30cd9a`.
This report records local follow-up validation completed before committing or
pushing. The owner subsequently authorized committing and pushing these changes
to the active branch. This is not a new M7 release or linguistic approval.

## Starting evidence and preserved work

Read project status, post-M7 next steps, the untracked pack guide, dashboard
instructions, and M4–M7/dashboard validation evidence. No applicable `AGENTS.md`
was found in the checkout or its parent directories. The initial tracked tree
was clean; the only untracked work was:

- `docs/hmong_evaluation_pack.md`;
- `src/tts_workbench/evaluation/prompt_set.py`; and
- `tests/unit/test_evaluation_prompt_set.py`.

Those files were reviewed and copied to external evidence before editing;
none was discarded. Their original 98 tests passed. Historical reports, M7
approval/manifests, the native-validation register, registry, lockfile, and
production inference/dashboard code remain unchanged. No Git staging, commit,
or push occurred during the validation described here. The later owner
instruction authorizes their commit/push; history rewriting, package
publication, and public deployment remain outside this work.

## Tooling and human-preparation results

The original validator already retained exact decoded UTF-8 text, rejected
unknown fields/duplicate JSON keys/invalid types, sanitized errors, required
consistent review status/reference metadata, and rejected exact text overlap
across splits. The review added:

- A local input boundary rejecting files within Git checkouts (including
  worktree pointer files) or exported project trees, with lexical/resolved
  checks for symlink indirection and sanitized path errors.
- Independent `--require-target-shape` validation for 20 development and 10
  held-out cases, exact uniqueness within splits, and all four category labels
  in each split. Small pending drafts still work with ordinary validation.
- A deterministic full-pack fingerprint binding text, ordering, references,
  review metadata, and split assignment, plus category counts by split.
- Regression checks for the boundary, composition gate, fingerprint changes,
  and independence of composition from recorded review status.

Exact-text tests cover whitespace, CRLF, case, digit sequences, punctuation,
synthetic tone-letter sequences, escaped/unescaped Unicode, composed/decomposed
forms, and exact UTF-8 hashes. Success/failure checks preserve original file
bytes; tests check no raw text/reference/path/unknown-key leakage in diagnostics.
The validator neither imports ML nor accesses the network during validation.

Prepared the [collection/review handoff](../../docs/hmong_collection_review.md),
updated the [pack guide](../../docs/hmong_evaluation_pack.md), and created an
external blank 30-slot draft. Every slot has empty text/references and is
`pending`; it intentionally fails validation. The owner confirmed **no real
pack exists**. No Hmong content, reviewer decision, linguistic acceptance,
participant commitment, or permission verification is claimed.

`--require-reviewed` checks claims recorded in metadata. It cannot verify
record existence, truth, reviewer independence, text rights, or pronunciation.
Exact separation cannot detect near duplicates. Humans must reconcile review
records/hashes, assess coverage, define acceptance criteria, and protect the
held-out set. The current English/Vietnamese input trimming/tokenizers are not
an approved exact-text Hmong evaluation frontend.

## Automated checks

Used the existing external Python 3.12 environment. Playwright 1.63.0 and its
four-package dependency closure were installed offline into a separate external
test-tool directory; the project lock/runtime environment was not changed.

| Check | Result |
|---|---|
| Focused prompt-set suite | **121 passed** |
| Full suite, including optional Chromium tests | **431 passed**, no skips |
| Aggregate branch-aware coverage | **84.99%** (existing gate: 78%) |
| Prompt-module branch-aware coverage in full suite | **98.20%** |
| Ruff lint and format | PASS; 85 Python files formatted |
| Strict source typing | PASS; 45 source files |
| Offline lock check | PASS; 83 resolved packages, no lock change |
| Installed dependency consistency | PASS; 82 external runtime packages checked |
| Inference/QC/benchmark configuration and model registry | PASS; exactly two unchanged registered models |
| Pre-commit hooks, including untracked candidate files | PASS |
| Repository privacy/artifact and whitespace checks | PASS |

The full suite uses synthetic prompts/backends/audio, including its four
Chromium workflows, and includes installed-wheel dashboard/package tests.
The real-model checks below were separate and are not included in this test
count or coverage. One existing Starlette/httpx TestClient deprecation warning
was emitted; no dependency was substituted to suppress it.

Reproduction uses the external environment's Python, Ruff, MyPy, and CLI tools:

```bash
uv lock --check --offline
uv pip check --python "$WORKBENCH_PYTHON"
"$WORKBENCH_PYTHON" -m ruff check .
"$WORKBENCH_PYTHON" -m ruff format --check .
"$WORKBENCH_PYTHON" -m mypy src
"$WORKBENCH_PYTHON" -m pytest tests/unit/test_evaluation_prompt_set.py -q
```

For the full suite, put the external Playwright tool directory on `PYTHONPATH`
alongside the checkout's `src`, set `COVERAGE_FILE` outside Git, and use:

```bash
"$WORKBENCH_PYTHON" -m pytest --cov=tts_workbench --cov-branch \
  --cov-report=term-missing -q -p no:cacheprovider \
  --basetemp="$VALIDATION_ROOT/pytest"
```

`--basetemp` must designate a disposable external test directory, not retained
evidence or private records. This run retained detailed logs/coverage separately.

## Current runtime and bounded real English workflow

| Observation | Current result |
|---|---|
| Platform | Linux x86-64 under WSL; Python 3.12.3 |
| CPU / system memory | 20 logical CPUs / approximately 15.5 GiB |
| GPU / driver | RTX 4070, 12,282 MiB / 610.62; CUDA tensor check passed |
| External runtime | PyTorch 2.13.0+cu130; Transformers 5.13.1; safetensors 0.8.0; SciPy 1.18.0 |
| Existing checkout environment | Older PyTorch 2.12.0 observed; preserved and not used for real checks |
| Browser | Playwright 1.63.0; Chromium 153.0.8010.12, headless |
| Model | `facebook/mms-tts-eng@c71de0fe7204c83f1c10820a7d696d0b450048ba` |
| Cached safetensors SHA-256 | `69cf8b651c1493f1801dfd2311c298d694a38357bc9a1e41f410491ea6f0e1be`, matches the M7 audit |
| Prompt | Existing `builtin:project-synthetic-eng-smoke-v1`, unchanged |
| Prompt SHA-256 | `f8cc7678783377f15fd576e51b2b1fffdf969a591415c3858f816042a1194892` |

Launched the **unchanged production service CLI**, with explicit
`--acknowledge-model-access`, one loopback worker, a private ephemeral port,
default queue/character limits, access logging disabled, and a fresh external
artifact directory. `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` forced the
existing exact snapshot; telemetry was disabled. No new model weights were
downloaded. CPU execution used two OMP/MKL threads.

The external Playwright harness generated exactly two English clips using the
dashboard's fixture and advanced controls:

| Device / dtype | Seed | Speaking rate | Frames at 16 kHz | Audio duration | Model load | Synthesis |
|---|---:|---:|---:|---:|---:|---:|
| CUDA / float32 | 555 | 1.0 | 38,656 | 2.416 s | 5.1214 s | 1.4154 s |
| CPU / float32 | 556 | 1.2 | 34,048 | 2.128 s | 0.5393 s | 0.5540 s |

These are two engineering observations with different settings and shared
process/cache state, **not comparative performance benchmarks**.

Both clips passed:

- Actual production MMS synthesis, committed schema-2 manifests, exact registry
  identity, `builtin_fixture` provenance, prompt hash, seed/speed/device checks.
- WAV reopening as nonempty mono PCM16, 16 kHz, frame/duration consistency, and
  matching manifest/file/download SHA-256.
- Browser playback with an advancing media clock, seek to the midpoint, local
  WAV download, and HTTP 206 byte-range/content/no-store checks.
- Switching between both session results with the matching audio URL, device,
  metadata, and clip title.
- Clear/reload behavior, empty local/session storage and Cache Storage, mobile
  width without overflow, and no browser script errors.

For useful errors, the harness changed an outgoing model ID to an unregistered
one while allowing the **real server** to return its 404; the dashboard displayed
the actionable unavailable-voice message and wrote no extra artifacts. Real API
requests also returned sanitized 422 for malformed input and 404 for unavailable
audio. No fake error response was substituted in this real run. The Vietnamese
UI blocked generation without the exact retained fixture. Queue-full, missing
runtime, device failure, and disconnect scenarios remain synthetic-suite evidence.

The first harness attempt used Playwright `fill()` on a range slider and failed
before inference. The harness was corrected to dispatch the slider input event;
the second complete attempt passed. Both evidence directories/logs were retained.
This was a probe error, not a production-code change.

After each attempt the service received SIGINT and shut down. The successful
process exited zero, and a connection check found no remaining listener. Its
service log and manifests contained no prompt echo, private artifact root,
rejected request marker, backend traceback, or HTTP access records. Detailed
logs, run identifiers, audio, downloads, and tooling remain external.

Playback verifies decoding and media behavior, **not audible human listening,
pronunciation, intelligibility, or White Hmong support**. Firefox/Safari and
manual assistive-technology testing were not performed. The M4 structural QC
thresholds were not changed; this run checked artifact integrity, not a new
perceptual or linguistic quality metric.

## Vietnamese gap and remaining decisions

The default external artifact/cache locations had no retained approved
`m6/prompts/vie-prompt.txt` or exact Vietnamese snapshot. The owner confirmed
the retained material is unavailable here and requested documenting the block.
No Vietnamese request or new Vietnamese text was synthesized. The registered
identity remains `facebook/mms-tts-vie@b58928d033932a49aa8e3d6cf11625b25fe928d2`.
To repeat this workflow, recover the retained prompt/source/permission evidence
and verify the approved prompt hash
`b6919cd1f33ec808355462bfa29e8444f8525560f8223d0486e67b35f29854c5`, follow the
[source/provenance checks](../../docs/m7_reproduction.md), and provide the exact
audited snapshot/runtime under the established local-use scope. Historical
M6/M7 Vietnamese inference success is preserved, not re-counted as this check.

The [research/decision document](../../docs/hmong_voice_decision.md) compares
current primary-source candidates, licenses, hardware/data needs, and missing
native-review evidence. Its recommended experiment is development-only, after
human pack completion and candidate rights/runtime authorization; all 10
held-out cases stay reserved. No Hmong candidate was downloaded or executed.
No recording or training decision has been made for participants.

## External evidence and next owner action

Root-relative evidence prefix: `evaluation-prep-20260925/` beneath the current
external artifact root. `tooling/` retains the incoming untracked files and
probe scripts; `logs/` and coverage files retain checks; `real-dashboard/` is
the pre-inference harness failure; `real-dashboard-02/` holds the successful
run, summary, WAV/manifest pairs and downloads; `research/` holds metadata-only
source observations; `collection/` holds the blank pending draft. None is a
release artifact. The previous M6/M7 root is not claimed to have been recovered.

The owner should arrange completion of the external draft with the willing
speaker and separate fluent reviewer using the handoff, including actual text
permissions, exact-text review, near-duplicate checks, and an agreed rubric.
Only then review a bounded candidate-access experiment; no training corpus or
Hmong voice selection is justified yet.
