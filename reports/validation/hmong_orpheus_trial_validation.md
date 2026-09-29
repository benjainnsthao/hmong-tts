# Hmong Orpheus local research trial validation

Date: **2026-09-29 UTC**. Phase A of the owner's two-phase instruction: local
trial and listening gate. This is exploratory development evidence under owner
decisions D1–D6 ([record](../../docs/hmong_orpheus_owner_decision.json)). It is
not an M7 release approval, language acceptance, public-use clearance or
publication. The held-out reserve was never read. No Hmong text, transcript,
meaning or audio is committed.

## Outcome

- **Housekeeping:** reviewed and committed the September 28 source-audit and
  listening work (`c55ed2c`), after two fixes: the blind answer key is created
  with mode 0600 from its first byte, and packet source text is marked
  `lang="hmn"`. `AGENTS.md` does not exist in the repository or its history;
  that gap is recorded here.
- **Isolated runtime:** `/root/tts-workbench-artifacts/envs/orpheus`, a separate
  uv project with lock `dcdb7047…14ff2` (torch 2.13.0, transformers 5.13.1,
  safetensors 0.8.0, snac 1.2.1). Accelerate is excluded, as in M7. Plain
  Transformers generation, no vLLM. The main environment was not modified.
- **Checkpoints:** 25 pinned files verified against Hub LFS SHA-256 and sizes,
  stored in the external HF cache. SNAC was converted once (D3) with
  `weights_only=True` in a throwaway environment (269 float32 tensors, exact
  round trip): source `4b8164cc…bff40` → loaded `2db6ee7e…d138c`. The throwaway
  environment was then removed; its lock and script are retained.
- **Adapter and registry:** `OrpheusAdapter` follows the `TTSAdapter` lifecycle,
  imports its runtime lazily, verifies the codec digest before importing ML
  packages, and never unpickles, uses remote code, quantizes or changes
  precision. Registry schema 2 records the research-only entry, its owner
  decision, its upstream license and its pinned codec. The service, dashboard
  and MMS smoke CLI never list or route it; the MMS adapter refuses it.
- **Development generation (configuration A):** 20/20 cases succeeded;
  reproduced bit for bit under the final lock.
- **Early exit:** not triggered under the rule written before any ASR output.
- **Listening gate:** five-clip offline quick check and the 20-clip packet are
  ready; the owner's verdict is pending.

## Measured results

| Measure | Result |
|---|---|
| Fit, BF16 on RTX 4070 12 GB | 6.2 GiB allocated after load; peak 6.41 GiB allocated / 6.71 GiB reserved; device total peak about 8.0 GiB including other processes; 8.5 MB allocated after unload |
| Load | 21–22 s cold (CPU load then move), 4–8 s with a warm page cache; well within the 180 s deadline |
| Generation | 20/20 explicit end-of-speech; 0 trimmed tokens; audio 1.6–6.2 s; 136 GPU-seconds for the final-lock run (limit 3,600) |
| RTF | Median 1.82, max 2.24 across 20 cases; M4 benchmark (D16, 1 warmup + 3 measured, seed 555) median 1.78, p95 1.80 |
| M4 QC, committed thresholds | 20/20 `structurally_invalid` solely because 16 kHz is the only allowed rate |
| M4 QC, same thresholds with 24 kHz | 19/20 `qc_passing`; D07 leading silence 0.49 s (22% > 20%); clipping 0; RMS 0.047–0.139 |
| ASR proxy (TTS) | Median CER 0.086, mean 0.117; median WER 0.225; 5/20 exact; own-reference closest 20/20; mismatched-reference median CER 0.873 |
| ASR proxy (human baselines) | 20 dataset sentences: median CER 0.778 (fluent but unrelated output); 7 CC0 syllables: median CER 0.333 |
| Browser | Quick-check page and full packet over `file://` in headless Chromium, light and dark: all clips play and seek; export, restore and phone width (0 px overflow) pass; no console errors |
| D4 recheck | Hmong F5 revision and missing license unchanged; Yuhalu EULA v1.0 unchanged |

The ASR proxy used `Pakorn2112/whisper-model-large-hmong` (`MultiSpeech/`,
safetensors). It is the only Hmong-capable ASR found with acceptable terms:
MMS-1b-all and Omnilingual ASR have no Hmong language entry, and Omnilingual
ships pickle weights. The ASR is **not independent**: it comes from the same
publisher and possibly the same data. Its failure on the human sentence baseline
shows a strong language-model prior. The proxy measures **no tone correctness**
and does not replace listening. The early-exit rule declared the proxy
uninformative as a comparator when the human median CER exceeds 0.6.

## Implementation checks

| Check | Result |
|---|---|
| Complete core suite | **526 passed**, 1 optional browser skip; aggregate branch-aware coverage **86.94%** (Phase floor 85.38%) |
| New tests (71) | 41 Orpheus adapter/backend (fake runtime, token layout, bounds, lazy import, no pickle/remote code/placement map), 21 registry schema 2, 4 ASR proxy, 3 listening priority, 1 service filtering, 1 benchmark dispatch |
| Browser suite | 4 passed with the previously isolated Playwright tools |
| Ruff format / lint | PASS, 92 files |
| Strict MyPy | PASS, 49 source files |
| Config / registry | PASS; registry schema 2, 3 models |
| Lock / main environment | Frozen lock unchanged; main environment in sync, no changes |
| Privacy scan / pre-commit / diff check | PASS |
| Historical integrity | M1–M7 reports, approvals, manifests and NV records unchanged |

The first isolated lock included Accelerate 1.14.0, which M7 removed for
GHSA-4j2p-28q2-5m79 (sharded checkpoint loading). It was replaced before
commit. Without Accelerate, Transformers refuses device placement maps, so three
loads failed closed with sanitized `ModelLoadError` (record `r2`, retained).
The adapter now loads on CPU in fixed BF16 and moves to the device. The rerun
reproduced all 20 WAV hashes. The main Transformers generation path was
unchanged.

## External artifacts

Root: `/root/tts-workbench-artifacts/hmong-orpheus-20260929/` (see its README).
Reviewer pages: `/root/tts-workbench-artifacts/white-hmong-20260928/review/`.

| Artifact | Location |
|---|---|
| Quick check (5 clips) | `review/quick-check/index.html` → `verdict.json` |
| Full packet (20 clips, blank scores) | `review/listening-v2-audio/`; key in `custodian/` (0600) |
| Trial records, clip inventories | `records/trial-config-a*.json`, `records/clips-config-a.json` |
| QC, benchmark, ASR proxy | `qc/config-a/`, `benchmark/config-a-D16-r3.json`, `asr/asr-proxy-config-a.json` |
| Provenance | `provenance/` (downloads, verification, SNAC conversion, env identity) |
| Predeclared early-exit rule | `configurations/early-exit-rule.md` |

Gaps recorded rather than filled: two CC0 syllable files were unavailable
(HTTP 429); the only sentence-level human Hmong audio found is one speaker from
one YouTube-sourced dataset with unverified underlying rights; no independent
Hmong ASR exists among the checked models; the card documents no voices or
sampling settings, so one configuration was run.
