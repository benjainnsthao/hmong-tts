# White Hmong single-speaker TTS project plan

Recommendation: build the MVP around a compact character-based VITS model, provisionally initialized from `facebook/mms-tts-vie`, and compare it against an English MMS initialization during the pilot. Keep Piper/VITS as the operational fallback.

This is a research/portfolio path, not yet a commercial model: MMS weights are CC BY-NC 4.0. As of July 14, 2026, I also verified that Meta’s public MMS repository does not expose checkpoints under `mww`, `hnj`, or `hmn`. MMS supports 1,107 languages as a family, but its TTS checkpoints are separate per language rather than one universal multilingual model. [Meta MMS model card](https://huggingface.co/facebook/mms-tts), [Transformers MMS documentation](https://huggingface.co/docs/transformers/model_doc/mms).

## Conventions and assumptions

- **[E] Essential:** required for the MVP.
- **[O] Optional:** stretch or post-MVP work.
- **[NV] Native validation:** a White-Hmong-specific decision that must be approved by the speakers.
- **Assumption:** the project targets one explicitly documented White Hmong variety and the Romanized Popular Alphabet used by the primary speaker. **[NV]**
- **Assumption:** a non-commercial public demo is acceptable for the first release.
- **Assumption:** training will use Linux or WSL2. This is safer than native Windows for Cython alignment components.
- **Assumption:** the project can collect at least six hours of accepted speech over the summer.
- Raw audio, identities, consent records, and private ratings will stay outside Git and outside public artifact stores.

---

# 1. Recommended system architecture

## MVP

A single-speaker, 16 kHz neural TTS system with:

- 6–8 hours of accepted primary-speaker recordings.
- A deterministic, tested RPA text-normalization pipeline.
- A character-based tokenizer that preserves all validated tone-bearing orthographic symbols. **[NV]**
- Full fine-tuning of MMS/VITS on the RTX 4070.
- A versioned FastAPI inference service.
- A simple web interface that accepts text and returns WAV audio.
- Human evaluation led by the second parent.
- Public code, documentation, reports, and selected consented examples.
- Initially, no public raw dataset and no automatic assumption that model weights may be redistributed.

## Architecture

```text
                       TRAINING
48 kHz/24-bit masters
        │
        ├── checksums + encrypted private backup
        │
        ▼
transcript review ──► audio QC ──► 16 kHz processed WAV
        │                  │
        └──────────► versioned manifest
                           │
                           ▼
                    MMS/VITS fine-tuning
                           │
                 checkpoint + tokenizer
                           │
                           ▼
                 model card + evaluation


                       INFERENCE
RPA text
   │
   ▼
length/safety validation
   │
   ▼
deterministic normalization ──► normalization audit record
   │
   ▼
character tokenizer
   │
   ▼
single-speaker VITS generator
   │
   ▼
PCM audio ──► output loudness/peak control ──► WAV response
```

The production API should never contain a second, inconsistent text-normalization implementation. Training, evaluation, CLI inference, API inference, and the demo must all import the same normalization package.

## Recommended model configuration

- Base: `facebook/mms-tts-vie`, subject to the pilot A/B decision.
- Control checkpoint: MMS English character model.
- Output: 16 kHz, matching MMS configuration. The published English MMS configuration uses 16 kHz. [MMS configuration](https://huggingface.co/facebook/mms-tts-eng/blob/main/config.json)
- Tokenization: lowercase character/grapheme baseline.
- Fine-tuning: generator and discriminator, using the full MMS training checkpoint or converted discriminator.
- Precision: FP16 initially; BF16 only after a stable smoke test.
- Per-device batch: begin at 4, reduce to 2 if necessary.
- Gradient accumulation: start at 8, giving an effective batch of approximately 32 at batch 4.
- Maximum training duration: initially 10 seconds per utterance.
- Length bucketing and cached resampling.
- Full fine-tuning rather than LoRA: the complete training model is only about 83M parameters, and parameter-efficient GAN fine-tuning is less established. Gradient checkpointing is a fallback for OOM, not a default.

The official Fairseq MMS documentation links to the Hugging Face VITS fine-tuning recipe, which supports generator/discriminator training and experiment tracking. Pin a tested commit because it is a community-maintained recipe rather than a polished Transformers training example. [MMS fine-tuning reference](https://github.com/facebookresearch/fairseq/tree/main/examples/mms), [VITS/MMS fine-tuning recipe](https://github.com/ylacombe/finetune-hf-vits).

## Stretch goals

- **[O][NV]** Validated grapheme units for multicharacter orthographic sequences.
- **[O][NV]** A linguist/native-reviewed pronunciation representation.
- **[O]** 10–12 hours of accepted speech.
- **[O]** Piper ONNX export for faster CPU deployment.
- **[O]** F5-TTS character-tokenizer experiment after the VITS MVP.
- **[O]** Audio watermarking, but only if tests show no damage to tone or intelligibility.
- **[O]** Translation-to-speech integration.
- **[O]** Second-speaker or multispeaker model.

## Speaker roles

- The retired parent is the only training voice for the MVP.
- The second parent reviews training transcripts and conducts the principal independent listening evaluation.
- The primary speaker may diagnose errors but should not be the only evaluator of their own model.
- Keep final evaluation prompts hidden from the second parent until transcription/listening evaluation when feasible.

Adding the second parent to training becomes useful only when:

1. The single-speaker MVP already meets its thresholds.
2. The product actually needs voice choice or multispeaker robustness.
3. The second speaker separately consents to training and distribution.
4. At least 1–2 clean hours can be recorded for that speaker.
5. Additional independent evaluators can be recruited; once the second parent is in training, they no longer provide clean speaker-independent evaluation.

---

# 2. Model comparison

| Model | White Hmong status | Adaptation and expected quality | License | 12 GB fit | Recommendation |
|---|---|---|---|---|---|
| **MMS/VITS** | MMS has 1,107 per-language models, but no public `mww`, `hnj`, or `hmn` directory was found. | Compact character VITS. Mature inference; a workable generator/discriminator fine-tuning recipe exists. A Vietnamese initialization gives Latin-character and tonal-speech exposure, but transfer must be demonstrated, not assumed. **[NV]** | CC BY-NC 4.0 for code/weights in the MMS release. | **Good.** 36.3M generator; about 83M for training components. | **Primary.** Compare `vie` and `eng` initialization in the pilot. [Vietnamese checkpoint](https://huggingface.co/facebook/mms-tts-vie) |
| **Piper/VITS** | No built-in White Hmong model, but it supports custom text symbols and different-language warm starts. | Usually less expressive than larger cloning systems, but efficient and highly deployable. Current docs explicitly support fine-tuning from another language and vocoder-only warm starts. | Current implementation is GPL-3.0; each base voice/checkpoint has separate licensing that must be audited. | **Good.** Maintainers report training on GPUs with 8 GB. | **Fallback.** Use custom text tokens and a clean-license checkpoint or vocoder warm start. [Piper training guide](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/TRAINING.md) |
| **F5-TTS v1** | Base is principally Chinese/English; no official White Hmong support. | Potentially more natural than VITS and flexible for character-token fine-tuning, but new-language adaptation generally needs more data and compute. | Code MIT; released base weights CC BY-NC because of training data. | **Marginal but possible** with FP16, very small frame batches, and accumulation; substantially slower. | Post-MVP quality experiment, not the first system. [Official repository](https://github.com/SWivid/F5-TTS), [model license](https://huggingface.co/SWivid/F5-TTS) |
| **XTTS-v2** | Officially supports 16 languages, not White Hmong. | Strong voice cloning in supported languages. Official implementation trains only the GPT encoder; adding a new language/tokenizer is not a supported beginner path. | CPML: only non-commercial use of both model and outputs. | Likely workable with careful settings, but less predictable than VITS. | Benchmark only. Do not base the MVP on an unsupported language. [XTTS documentation](https://docs.coqui.ai/en/latest/models/xtts.html), [CPML text](https://huggingface.co/coqui/XTTS-v2/blob/main/LICENSE.txt) |
| **OpenVoice V2** | Claims broad voice conversion, but native base TTS is limited to six languages. | It converts a base TTS voice’s tone color; it does not solve White Hmong text pronunciation by itself. | MIT. | Good for inference. | Optional voice-conversion layer only after a competent Hmong base TTS exists. [Official repository](https://github.com/myshell-ai/OpenVoice) |

### Primary recommendation

Start with MMS/VITS initialized from `facebook/mms-tts-vie`, but make that choice provisional:

- Compare it with an English MMS character checkpoint on exactly the same 30–45-minute pilot.
- Choose using blinded native judgments, not linguistic intuition.
- Do not claim that Vietnamese and White Hmong share transferable tone behavior; the checkpoint is merely an initialization candidate. **[NV]**

### Fallback

If neither MMS initialization produces intelligible pilot speech after scaling the pilot to roughly two hours, move to Piper medium:

- Use `phoneme_type=text` or explicit IDs rather than pretending an existing eSpeak language is White Hmong.
- Start from a different-language medium checkpoint when symbol compatibility permits.
- Otherwise use Piper’s vocoder-only warm start, which deliberately excludes the input embedding layer.
- Audit the complete checkpoint and dataset license lineage before distributing weights.

---

# 3. Dataset and recording plan

## Dataset targets

| Stage | Accepted audio | Approximate utterances | Purpose |
|---|---:|---:|---|
| Dry run | 5–10 minutes | 50–80 | Recording and file-flow test |
| Pilot | 30–45 minutes | 250–400 | Complete processing/training/evaluation test |
| Intermediate | 2 hours | 1,200–1,800 | Confirm new-language transfer |
| MVP | 6–8 hours | 4,000–6,000 | Primary model |
| Stretch | 10–12 hours | 7,000–9,000 | Rare coverage and naturalness improvement |

These are targets, not quotas. Fewer clean, verified recordings are more valuable than more inconsistent recordings.

## Pilot recording phase

The pilot must exercise every production component:

1. Obtain signed consent and assign pseudonymous speaker IDs.
2. Build a native-reviewed pilot prompt set.
3. Record 30–45 accepted minutes across at least two sessions.
4. Review every transcript and take.
5. Run the final-style normalization and audio pipeline.
6. Create permanent train/development/test IDs.
7. Train short English- and Vietnamese-initialized MMS runs.
8. Synthesize the same 20–30 held-out prompts.
9. Have the second parent perform blind recognition and error labeling.
10. Produce `reports/pilot-v0.1.md`.

Pilot exit criteria:

- At least 90% of recorded prompts survive manual review.
- No clipping, naming, privacy, normalization, or split-integrity defects remain.
- Training runs for at least 2,000 optimizer steps without OOM, NaN, or broken alignment.
- One model produces recognizable speech on at least 60% of pilot test words.
- Every artifact can be regenerated from a clean environment using private data paths.
- If intelligibility is below 60%, expand to two hours before rejecting the architecture.

## Recording protocol

### Equipment and environment

- Record immutable masters as mono, 48 kHz, 24-bit PCM WAV.
- Disable AGC, noise suppression, compression, reverb removal, and live normalization.
- Use one microphone, interface, stand, cable, room, and software preset.
- Position the microphone approximately 15–20 cm from the mouth, slightly off-axis, with a pop filter.
- Mark chair, stand, and microphone positions physically.
- During setup, target ordinary speech peaks around −12 to −6 dBFS.
- Record 30 seconds of room tone at the beginning and end.
- Close fans and noisy applications; log unavoidable noise.
- Preferred noise floor: below approximately −50 dBFS; preferred speech-to-noise ratio: at least 30 dB. Treat these as QC guides, not reasons to overprocess audio.

### Session structure and fatigue

- Use 20–25 minute speaking blocks.
- Take a 5–10 minute break between blocks.
- Cap voiced recording at approximately 45–60 minutes per day.
- Stop for hoarseness, throat discomfort, repeated errors, reduced energy, or frustration.
- Log illness, allergies, unusual fatigue, and time of day.
- Begin each session with five repeated calibration prompts; compare their level and spectral profile to previous sessions.
- Do not use pitch shifting or time stretching for augmentation; it could corrupt tone evidence.

### File naming

Use no real names:

```text
spk01_s20260720_u000123_take01.wav
```

Metadata should include:

```text
utterance_id
speaker_id
session_id
prompt_id
take_number
original_text
normalized_text
recorded_at
review_status
reviewer_id
equipment_profile
notes
sha256
```

### Backups and privacy

- Immutable primary copy on the recording machine.
- Encrypted external-drive backup after every session.
- Encrypted off-site/private-cloud backup after checksum verification.
- Maintain SHA-256 manifests.
- Keep consent documents in a separate encrypted location.
- Public code refers to `$HMONG_TTS_DATA_ROOT`; it never contains absolute family paths.
- Add CI checks that fail if WAV, FLAC, consent PDFs, email addresses, or known speaker identifiers enter Git.

## Prompt-selection strategy

Do not begin with random sentences. Build `linguistic_inventory.csv` first.

Required fields:

```text
feature_id
category
orthographic_form
example_candidates
validated_reading
speaker_variety
source
license
reviewer_status
notes
```

The inventory should cover, after native validation:

- **[NV]** Consonant and vowel distinctions used by the target speaker.
- **[NV]** All tone-marker spellings and tone contrasts.
- **[NV]** Allowed syllable structures and orthographic sequences.
- **[NV]** Common words, function words, and productive sentence patterns.
- **[NV]** Numbers, dates, times, money, measurements, ordinals, and phone-number-style readings.
- **[NV]** Personal and place names appropriate for a public demo.
- **[NV]** Borrowed words and whether they are adapted or pronounced closer to the source language.
- **[NV]** Spelling variants that the project will accept.
- Questions, statements, lists, short commands, and longer explanatory sentences.
- Short, medium, and long utterances, mostly producing 2–10 seconds of audio.

Use a greedy set-cover script to select prompts that add uncovered features while avoiding needless repetition. Native speakers approve the resulting list; the algorithm does not define the language.

Split by normalized prompt hash and feature group, not by audio file after recording:

- Train: approximately 90%.
- Development: approximately 5%.
- Test: approximately 5%, with at least 100 sentences for the final evaluation.
- Maintain a separate balanced diagnostic set for pronunciation and tone. **[NV]**
- Prevent paraphrases and nearly identical minimal contrasts from leaking across train/test unless the evaluation explicitly studies generalization.

## Consent and distribution

The consent form should contain independent choices for:

- Recording participation.
- Training a model.
- Publicly sharing selected audio examples.
- Hosting a public demo.
- Distributing model weights.
- Commercial use.
- Using the voice in future translation or education applications.
- Preferred credit or anonymity.
- Retention period and contact process.
- Withdrawal before and after public release.

Withdrawal terms must be candid:

- Before public release, delete covered private recordings, processed derivatives, and unpublished checkpoints.
- After release, remove hosted artifacts and mark releases withdrawn.
- Explain that downloaded weights or audio cannot reliably be recalled from third parties.
- Because of that asymmetry, launch the demo before publishing downloadable weights.

Voice-misuse protections:

- Prominent “synthetic voice, used with consent” notice.
- Model-card prohibited uses: impersonation, fraud, deceptive political/media content, harassment, and bypassing consent.
- Rate limits, text-length limits, one inference worker, abuse reporting, and a kill switch.
- Short log retention with no unnecessary text or IP retention.
- WAV metadata identifying the model and release.
- No claim that phrase blocklists or watermarks make misuse impossible.

---

# 4. Processing, training, and inference pipeline

## Text normalization

Maintain three text forms:

1. `original_text`: exactly what the prompt author wrote.
2. `normalized_text`: deterministic model input.
3. `spoken_form`: reviewer-approved intended reading.

Pipeline:

1. Unicode normalization, initially NFC.
2. Normalize spaces and explicitly approved typographic punctuation.
3. Lowercase for the MMS baseline while retaining original display text.
4. Segment long input at reviewed sentence/clause boundaries.
5. Expand numbers using deterministic, context-specific rules. **[NV]**
6. Expand only allowlisted abbreviations. Record whether each is read as a word, letters, or a full phrase. **[NV]**
7. Apply only approved spelling-variant mappings, preserving provenance. **[NV]**
8. Preserve every validated tone-marker letter; never remove a final letter merely because another language’s normalizer treats it as silent. **[NV]**
9. Audit every character against the tokenizer vocabulary.
10. Reject or return a clear warning for unknown characters, ambiguous number formats, URLs, emoji, or unsupported mixed-language input.

Write golden tests:

```text
input → normalized output → spoken form → validation status
```

At least 100 golden cases should cover punctuation, capitalization, numbers, abbreviations, spelling variants, names, borrowed words, and tone-marker preservation. **[NV]**

## Audio processing

1. Preserve the 48 kHz/24-bit raw master unchanged.
2. Decode to floating-point mono.
3. Detect DC offset, clipping, channel problems, and corrupt headers.
4. Resample once to the model rate using a high-quality fixed resampler:
   - MMS: 16 kHz.
   - Piper fallback: normally 22.05 kHz.
5. Trim only leading/trailing non-speech:
   - approximately 50–150 ms leading context;
   - approximately 100–250 ms trailing context.
6. Preserve internal pauses.
7. Avoid denoising unless a separately tested rescue pipeline is necessary.
8. Apply consistent session-level gain or conservative loudness normalization, not aggressive per-clip peak normalization.
9. Keep training audio below clipping; perform separate web-output loudness adjustment.
10. Write a processing manifest containing tool versions, parameters, source checksum, and output checksum.

Automatic invalid-sample flags:

- Duration outside 1–12 seconds for the baseline.
- Clipped sample ratio above 0.1%.
- Peak at or above approximately −1 dBFS.
- Estimated SNR below 25–30 dB.
- Excess leading/trailing silence.
- Too little detected speech.
- Empty or out-of-vocabulary transcript.
- Duplicate text/audio/checksum.
- Extreme duration-to-character ratio.
- Session-level loudness or spectral outlier.
- Non-finite samples or resampling failure.

Flags should send samples to review; they should not silently delete them.

### Alignment and transcript validation

There is no verified Hmong Daw forced aligner in this plan. Therefore:

- Record one prompt per file.
- Use VAD only to detect boundaries and suspicious silence.
- Have the second parent review transcript/audio agreement.
- Use model attention/alignment plots after the first VITS run to identify collapsed or skipped samples.
- Treat multilingual ASR or forced alignment as diagnostic unless it is independently validated for this speaker and variety.

## Reproducible training

Every run writes a `run_manifest.json` containing:

- Git commit.
- Dirty-worktree status.
- Base model name and exact revision.
- Base model license.
- Data-manifest hash.
- Train/dev/test split hash.
- Normalizer version.
- Tokenizer/vocabulary hash.
- Full configuration.
- Python and package lock hash.
- CUDA, driver, GPU, and PyTorch versions.
- Random seeds.
- Start/end times.
- Maximum VRAM.
- Parent checkpoint.
- Generated evaluation-grid paths.

Initial runtime settings:

```yaml
precision: fp16
per_device_batch_size: 4
gradient_accumulation_steps: 8
max_audio_seconds: 10
length_bucketing: true
gradient_clip_norm: 1.0
learning_rate: 1.0e-5
save_every_optimizer_steps: 500
evaluate_every_optimizer_steps: 250
keep_best_checkpoints: 3
keep_latest_checkpoint: true
```

Use recipe-compatible optimizer and loss defaults initially. Change only one meaningful variable per controlled experiment.

Checkpoint files must include generator, discriminator, optimizers, scaler, scheduler, global step, and RNG state so interrupted runs truly resume. Generate the same fixed listening grid at every saved evaluation point.

Use local MLflow or offline Weights & Biases. Never upload private audio or unapproved text to a hosted tracker.

## Small experiment matrix

Use successive halving: discard clearly broken runs early.

| Experiment | Data | Variable | Budget | Decision |
|---|---:|---|---:|---|
| P0 | 30–45 min | MMS `vie` vs `eng` initialization | 2,000 steps each | Pick initialization by blind listening |
| P1 | 30–45 min | LR `1e-5` vs `5e-5` | 2,000 steps each | Reject unstable or overfit LR |
| S1 | 0.5 h | Winning configuration | 5,000 steps | Establish learning curve |
| S2 | 2 h | Same configuration | 8,000–12,000 steps | Confirm intelligible new-language transfer |
| S3 | 6 h | Same configuration | Until plateau | Main candidate |
| C1 | 6 h | Early/middle/late checkpoints | No extra training | Human checkpoint selection |
| T1 **[O][NV]** | 6 h | Character vs validated grapheme tokens | One additional run | Test data-efficiency hypothesis |
| F1 **[O]** | 6–8 h | Piper fallback or F5-TTS | Only after MVP gate | Architecture comparison |

The 0.5-, 2-, and 6-hour sets must be nested and coverage-balanced so the size comparison is meaningful.

## Inference API and demo

FastAPI contract:

```http
POST /v1/synthesize
Content-Type: application/json

{
  "text": "...",
  "speed": 1.0,
  "seed": 1234,
  "format": "wav"
}
```

Also provide:

- `GET /health`
- `GET /ready`
- `GET /v1/model-info`
- `POST /v1/normalize` for debugging, disabled or restricted in public deployment if necessary.

Implementation requirements:

- Pydantic request validation.
- Hard character and normalized-token limits.
- Single model instance loaded at startup.
- One GPU inference queue.
- Seeded generation.
- Cache key based on normalized text, parameters, and model hash.
- Structured error responses for unknown characters and ambiguous text.
- Request timeout and cancellation.
- Unit tests using a tiny mocked synthesizer.
- Integration test checking that a real model returns a valid WAV header and finite samples.

A Gradio interface can call this API for the MVP. Keeping Gradio separate from model logic communicates stronger engineering discipline than embedding all processing in the UI.

---

# 5. Evaluation protocol and acceptance thresholds

## Evaluation design

Use three systems in randomized, hidden order:

1. Natural held-out recordings as the upper reference.
2. The selected baseline or early checkpoint.
3. The final candidate.

Keep loudness comparable. Do not identify which system produced a clip.

Evaluation sets:

- 100 novel held-out sentences for intelligibility.
- At least 160 balanced diagnostic items for tone and pronunciation. **[NV]**
- 30 common application sentences.
- 20 numbers/names/borrowings items. **[NV]**
- 20 long or difficult stress-test inputs.
- 10 deliberately invalid inputs for API behavior.

Run evaluation in short blocks to avoid listener fatigue.

## Human acceptance thresholds

These are project targets and must be finalized after the pilot. **[NV]**

| Dimension | Method | MVP threshold |
|---|---|---:|
| Intelligibility | Second parent blindly transcribes 100 outputs | Normalized character error rate ≤10%; word accuracy ≥85% |
| Pronunciation | Word/syllable acceptable–incorrect labels | ≥90% acceptable overall |
| Tone accuracy | Balanced diagnostic judgments | ≥90% overall and ≥80% in every validated category |
| Naturalness | 1–5 MOS with anchored examples | Mean ≥3.5 |
| Speaker similarity | 1–5 comparison with real reference | Mean ≥4.0 |
| Catastrophic failures | Skipped, repeated, unintelligible, or collapsed outputs | <2% |
| Long-input robustness | 20 stress inputs | ≥18 complete without truncation or repetition |
| API reliability | 100 valid requests | ≥99 succeed |
| GPU latency | Warm RTX 4070, ordinary short sentence | Real-time factor ≤0.5 |
| Training memory | Logged maximum | ≤11.5 GB without OOM |

Before computing CER/WER, define native-approved equivalence rules for acceptable spelling variants. Do not tune those rules after seeing model errors.

With only two native listeners, MOS results are a case study, not a population estimate. Report raw ratings, disagreement, bootstrap intervals by utterance, and the number of raters. Recruiting five or more additional fluent listeners is a valuable stretch goal.

## Objective metrics and limitations

| Metric | Use | Limitation |
|---|---|---|
| Duration ratio and real-time factor | Deployment performance and truncation detection | Says nothing about linguistic correctness |
| Clipping, loudness, F0 dropout | Automated regression testing | Good audio statistics can coexist with wrong speech |
| Mel-cepstral distortion with DTW | Spectral comparison against the same held-out sentence | Penalizes legitimate timing/prosody variation |
| F0 contour distance/correlation | Diagnostic tone/prosody comparison **[NV]** | Pitch trackers fail on some voice qualities; tone may not be represented by F0 alone |
| Speaker-embedding cosine similarity | Compare synthetic/real speaker identity | Embedding models may be biased by language, age, microphone, and recording condition |
| UTMOS/DNSMOS | Automated quality trend | Training languages and degradation assumptions may not represent White Hmong |
| ASR CER/WER | Only if a Hmong system is validated first | An inaccurate ASR system measures its own errors, not TTS intelligibility |
| PESQ/STOI/SI-SDR | Not a headline TTS metric | Designed around aligned reference/degradation settings, not alternative valid speech realizations |

Human transcription and native tone/pronunciation judgments are the primary evidence. Objective metrics are regression signals.

---

# 6. Repository and GitHub structure

```text
hmong-tts/
├── README.md
├── LICENSE
├── MODEL_LICENSE.md
├── CITATION.cff
├── CONTRIBUTING.md
├── SECURITY.md
├── pyproject.toml
├── uv.lock
├── Makefile
├── .env.example
├── .gitignore
├── configs/
│   ├── data/
│   ├── model/
│   ├── train/
│   ├── eval/
│   └── inference/
├── src/hmong_tts/
│   ├── text/
│   │   ├── normalize.py
│   │   ├── numbers.py
│   │   ├── vocabulary.py
│   │   └── validation.py
│   ├── audio/
│   │   ├── process.py
│   │   ├── qc.py
│   │   └── loudness.py
│   ├── data/
│   │   ├── manifests.py
│   │   └── splits.py
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   └── api/
├── apps/
│   └── gradio_app.py
├── scripts/
│   ├── build_manifest.py
│   ├── process_audio.py
│   ├── audit_tokenizer.py
│   ├── train.py
│   ├── synthesize_eval_set.py
│   └── benchmark.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── golden_text/
│   └── fixtures/
├── eval/
│   ├── public_prompts/
│   ├── rubrics/
│   └── schemas/
├── docs/
│   ├── architecture.md
│   ├── recording_protocol.md
│   ├── text_normalization.md
│   ├── privacy_and_consent.md
│   ├── threat_model.md
│   ├── model_card.md
│   └── dataset_statement.md
├── reports/
│   ├── pilot-v0.1.md
│   ├── experiment-matrix.md
│   └── final-evaluation.md
├── samples/
│   └── README.md
├── data/
│   └── README.md
└── .github/
    ├── workflows/
    ├── ISSUE_TEMPLATE/
    └── pull_request_template.md
```

`data/README.md` documents the expected private layout but contains no audio.

## Tests

- Normalization golden tests.
- Tone-marker preservation tests. **[NV]**
- Number/abbreviation expansion tests. **[NV]**
- Tokenizer OOV test.
- Manifest schema and checksum tests.
- Split-leakage and duplicate-text tests.
- Audio duration, sample-rate, channel, clipping, and finite-value tests.
- API schema and WAV-response tests.
- Configuration-load and dry-run training tests.
- CI privacy scan.

## GitHub project communication

Milestones:

- **M0 Governance and reproducible environment**
- **M1 Pilot dataset**
- **M2 Six-hour dataset**
- **M3 Baseline and ablations**
- **M4 Evaluation and demo**
- **M5 v1.0 portfolio release**

Issue labels:

```text
area:data
area:text
area:audio
area:training
area:evaluation
area:api
area:docs
native-validation
privacy
license
experiment
blocked
good-first-issue
```

Releases:

- `v0.1.0`: repository, normalizer skeleton, recording protocol.
- `v0.2.0`: reproducible pilot and report.
- `v0.3.0`: six-hour model candidate.
- `v0.9.0`: evaluation/demo release candidate.
- `v1.0.0`: accepted MVP.

Recruiter-facing evidence should include:

- A two-minute system demonstration.
- Architecture diagram.
- Public experiment table, including failed hypotheses.
- VRAM and latency benchmark.
- Reproducible configuration and environment lock.
- Model card, dataset statement, consent approach, and misuse threat model.
- CI badge and tests.
- A release with a clear license matrix for code, model, samples, and external checkpoints.

---

# 7. Phased summer-to-school-year roadmap

| Phase | Deliverables | Effort | Dependencies | Validation | Completion criteria |
|---|---|---:|---|---|---|
| **0. Governance and setup, week 1** | Consent draft, privacy layout, repository, dependency lock, base-model/license audit | 12–18 hours | Speaker discussion; WSL2/CUDA | Clean clone, unit tests, consent review | Inference works; no private files in Git; consent signed before recording |
| **1. Linguistic design and pilot, weeks 2–3** | Inventory v0.1, 250–400 prompts, 30–45 accepted minutes, processing pipeline, two MMS runs | 25–35 engineering hours plus recording | Phase 0; microphone calibration; native review | Blind pilot listening and pipeline rerun | Pilot exit criteria met and primary initialization chosen |
| **2. Production recording, weeks 4–9** | 6–8 accepted hours, reviewed transcripts, session reports, fixed splits | 45–70 engineering/review hours; roughly 12–20 speaker hours | Stable protocol and pilot model | Automated QC plus second-parent review | ≥6 accepted hours; 100% reviewed; test set sealed |
| **3. Baseline training, weeks 7–10** | 0.5-, 2-, and 6-hour runs; checkpoint grids; run manifests | 20–30 engineering hours plus GPU time | Incremental dataset releases | Dev listening, alignment plots, no hidden test use | Six-hour run is stable and exceeds pilot intelligibility |
| **4. Controlled experiments, weeks 10–13** | Initialization, learning-rate, size, and checkpoint comparison report | 25–40 hours | Stable baseline | Fixed blinded evaluation subset | One configuration chosen with documented evidence |
| **5. Final evaluation and API, weeks 13–16** | Listening study, metrics, FastAPI service, web demo, benchmark | 35–50 hours | Frozen model and hidden test set | Acceptance table, API tests, load test | All critical thresholds pass or deviations are documented |
| **6. School-year release, weeks 17–20** | Model card, dataset statement, demo video, threat model, v1.0 release | 15–25 hours | Consent re-confirmation; license review | Fresh-machine reproduction and release checklist | MVP definition of done satisfied |
| **7. Post-MVP [O]** | Piper/F5 comparison, validated grapheme tokenizer, extra raters, translation integration | Open-ended | Successful v1.0 | Separate ablation studies | Each stretch feature earns its own release |

Recording and training phases may overlap, but test prompts must remain sealed and all experiments must use versioned data snapshots.

---

# 8. Risk register

| Risk | Probability / impact | Early signal | Mitigation and fallback |
|---|---|---|---|
| MMS transfer fails to learn White Hmong pronunciation | Medium / High | Pilot remains unintelligible after 2 hours | Compare two initializations; audit tokens; move to Piper custom-text VITS; later try F5 |
| Tone categories collapse | Medium / High | Diagnostic confusions concentrate by category | Increase balanced prompt coverage **[NV]**; inspect F0/phonation; validated grapheme tokens; collect targeted rerecordings |
| Tokenizer removes meaningful letters | Medium / High | OOV or normalization audit failures | Block training until vocabulary coverage is 100%; golden preservation tests **[NV]** |
| Recording inconsistency | Medium / High | Calibration prompts drift by session | Fixed setup, calibration prompts, session-level QC, rerecord affected sessions |
| Speaker fatigue changes delivery | Medium / Medium | Error rate, pitch, or energy drifts within sessions | Short blocks, breaks, session cap, stop rules |
| Transcript errors | Medium / High | Alignment failures or repeated listening disputes | Independent review, issue-based correction log, immutable manifest versions |
| Test leakage | Medium / High | Similar normalized prompts across splits | Hash and similarity checks; seal test manifest before training |
| GAN instability or OOM | Medium / Medium | NaNs, discriminator spikes, >11.5 GB usage | Batch 2, accumulation, shorter samples, FP16 scaler, restore last good checkpoint |
| Automatic metrics mislead | High / Medium | Metric improves while listeners prefer older model | Human evaluation remains the selection criterion |
| Only two evaluators | High / Medium | Large disagreement or unstable MOS | Report limitation; adjudicate errors; recruit additional native listeners as stretch |
| Non-commercial base license blocks product use | High / High | Plans expand beyond portfolio/demo | Maintain license matrix; use Piper/clean-license VITS path or train clean model before commercialization |
| Public weights enable misuse | Medium / High | Speaker expresses concern or abuse appears | Demo-first release, rate limits, disclosure, delayed/no weights, takedown process |
| Speaker withdraws | Low–Medium / High | Consent changes | Staged releases; delete unpublished derivatives; clearly document limits after distribution |
| Private audio enters Git or experiment tracker | Medium / High | Large-file or PII scan alert | External data root, encrypted private storage, pre-commit/CI privacy scanners |
| Orthographic or dialect scope is unclear | Medium / High | Reviewers disagree on valid readings | Define model scope in the dataset statement and model card **[NV]**; reject ambiguous prompts |

---

# 9. Detailed first two weeks

| Day | Task | Deliverable and completion test |
|---|---|---|
| **1** | Create repository, privacy boundary, issue board, and milestones | Clean repo; WAV/PII CI scan; private data root documented |
| **2** | Draft consent, model-distribution options, withdrawal terms, and threat model | Both speakers understand and approve roles; no recording before signature |
| **3** | Install WSL2/CUDA environment; pin Python/PyTorch; run `mms-tts-vie` and English inference | Both checkpoints synthesize; GPU and package versions logged |
| **4** | Download/convert training checkpoints and discriminator; run a tiny training smoke test | Ten batches complete and resume from checkpoint succeeds |
| **5** | Build `linguistic_inventory.csv` with both speakers | Inventory has source, status, and unresolved-question fields; no invented rules **[NV]** |
| **6** | Create 350 pilot prompt candidates and run set-cover selection | Every selected prompt is licensed/authored, categorized, and native-reviewed **[NV]** |
| **7** | Implement normalization v0.1 and tokenizer audit | At least 100 golden tests; 100% normalized character coverage |
| **8** | Calibrate recording setup; record 5–10-minute dry run | Noise, clipping, distance, file naming, and fatigue protocol pass |
| **9** | Process the dry run and review every sample with the second parent | Rejected samples have explicit reasons; complete manifest regenerates |
| **10** | Record pilot session 1, approximately 20–25 accepted minutes | Checksums and two backups complete before ending the day |
| **11** | Record pilot session 2 and targeted rerecordings | Total 30–45 accepted minutes across two sessions |
| **12** | Freeze splits; run complete processing; produce QC report | No duplicate/leaked prompts; all clips reviewed |
| **13** | Train `vie` and `eng` pilot runs with identical settings | Both reach 2,000 steps or failures have actionable root causes |
| **14** | Generate blinded evaluation grid; second parent transcribes/rates; write pilot report | Primary initialization selected or explicit two-hour fallback gate triggered |

At the end of week two, the important result is not a polished voice. It is proof that consent, recording, normalization, QC, training, evaluation, and reproducibility form one functioning pipeline.

---

# 10. Final MVP definition of done

The project is complete only when all essential items below are true:

- [ ] Written consent explicitly covers the deployed demo and any distributed artifacts.
- [ ] Primary speaker is the only training speaker.
- [ ] At least six hours of accepted, reviewed, single-speaker audio exist privately.
- [ ] Raw masters, PII, and consent records have never entered the public repository.
- [ ] Every language-specific normalization and prompt-coverage decision has native approval. **[NV]**
- [ ] The normalizer has at least 100 golden tests and preserves all validated tone-marker text.
- [ ] Train/dev/test manifests are immutable, checksummed, and leakage-audited.
- [ ] A fresh environment can reproduce processing and training from versioned configuration.
- [ ] Training stays within 12 GB VRAM and resumes correctly after interruption.
- [ ] Initialization, dataset-size, and checkpoint experiments are documented.
- [ ] The final model meets the intelligibility, tone, pronunciation, naturalness, similarity, reliability, and failure-rate thresholds—or the release is honestly labeled experimental with failed criteria.
- [ ] Human results are reported separately from unvalidated automatic metrics.
- [ ] FastAPI and the web demo synthesize valid WAV audio from White Hmong text.
- [ ] The public demo discloses that the output is synthetic and consented.
- [ ] Rate limits, input limits, abuse reporting, and a shutdown mechanism exist.
- [ ] Code, base weights, final weights, samples, and data each have an explicit license/status.
- [ ] README, architecture document, recording protocol, experiment report, model card, dataset statement, privacy document, and threat model are complete.
- [ ] CI passes unit, integration, privacy, configuration, and API tests.
- [ ] A tagged `v1.0.0` release and short demonstration video communicate the engineering outcome.

The strongest portfolio story is not “I trained a Hmong voice.” It is: “I built a consented low-resource speech system, demonstrated where multilingual transfer worked or failed, created language-aware evaluation with native speakers, respected licensing and privacy constraints, and shipped a reproducible service on consumer hardware.”
