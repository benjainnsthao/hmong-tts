# White Hmong voice research and recording decision

Research date: **2026-09-25**. Target: **White Hmong (Hmoob Dawb), RPA**.
Intended eventual use: public noncommercial speech generation. Current approval
still covers only local English/Vietnamese checkpoints. This is a research
shortlist and proposed experiment, not candidate approval or a training plan
that has been executed. No new candidate weights, datasets, recordings, or
containers were downloaded; no participant was contacted.

**Recommendation:** finish the human-reviewed pack, then resolve the rights
and runtime prerequisites for one Hmong-labelled Orpheus candidate before a
small development-only listening experiment. Do not commit to recording a
training corpus yet. Keep MMS/VITS adaptation as a separate fallback proposal.
There is presently insufficient evidence to select a usable White Hmong voice.

## Candidates and approaches

| Route | Target variety/script and quality evidence | Code, model/data rights and public noncommercial fit | Hardware and data needs | Current disposition |
|---|---|---|---|---|
| **Pakorn2112/Orpheus-TTS-hmong-3b** | Card explicitly advertises Hmong Daw. RPA coverage and sentence-level results from independent fluent raters are not documented there. No quality has been demonstrated by this project. [Model card](https://huggingface.co/Pakorn2112/Orpheus-TTS-hmong-3b) | Weights declare Apache-2.0; card describes research/educational release and unresolved dataset rights for commercial use. No itemized Hmong training-data license or speaker authorization was located. Upstream code is Apache-2.0, but the declared base chain includes Llama; reconcile applicable base terms and data/voice rights before approving public use. [Orpheus code](https://github.com/canopyai/Orpheus-TTS), [base metadata](https://huggingface.co/canopylabs/orpheus-3b-0.1-ft), [Llama terms](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct/blob/main/LICENSE.txt) | 3B BF16 model with SNAC 24 kHz; card claims single-GPU real-time inference without a measured VRAM minimum. No new speaker recording should be required for a fixed existing-voice trial if its voice selection and rights are documented. Training-data size is unspecified. | Best-matched research lead, **blocked pending rights/runtime review**. Do not accept the card's quality claims as evaluation results. |
| **Local Voice / YangNobody12 Hmong F5-TTS distribution** | Advertises Hmong; the inspected deployment guide does not establish White Hmong/RPA scope, a native-review protocol, or scores. [Distribution guide](https://github.com/YangNobody12/hmong-TTS/blob/main/F5TTS-model/README.md) | Repository code is MIT and describes a commercial-permission condition. No exact bundled checkpoint identity, separate Hmong dataset license, or speaker permissions were located. Upstream F5 code is MIT; its pretrained weights have an Emilia-derived NC restriction. Those facts do not clear the derivative or its outputs. [Project](https://github.com/YangNobody12/hmong-TTS), [upstream terms](https://github.com/SWivid/F5-TTS#license) | Guide recommends NVIDIA GPU and 2–3 GB free disk, permits slower CPU use; VRAM minimum unknown. Docker packaging adds a separate dependency audit. Establish whether inference requires reference speech and what permits its use before testing; none is supplied here. | Secondary lead only after immutable artifact, data, reference-voice, and license evidence. No container pull. |
| **Yuhalu 2.0 concatenative voice** | Manual explicitly documents White Hmong and Blue Hmong in RPA. It describes syllable/word concatenation and a tone-related substitution that needs independent fluent assessment. No controlled White Hmong sentence evaluation was located. [Manual](https://yuhalu.org/help/UserManual.html) | Proprietary software/audio resources. EULA allows lawful output under the selected plan but restricts redistribution and training/cloning from internal resources. A personal/community license does not itself establish permission to offer a public hosted TTS service. [EULA §§4–7](https://yuhalu.org/eula.php) | Java desktop application; GPU is not listed as required in the manual. No measured minimum RAM/latency was located. Existing audio bank avoids new project recordings for evaluation, but is not a reusable training corpus. | Possible non-neural comparison if the owner resolves availability and suitable licensing. The plans page calls its displayed offers testing-only/not yet purchasable. [Plans](https://yuhalu.org/plans.html) |
| **MMS/VITS adaptation with newly permitted White Hmong data** | Current MMS collection listing contains no exact `mww`, `hnj`, or `hmn`, or Hmong-named entry. Existing `eng`/`vie` models are engineering baselines, not Hmong candidates. [Collection](https://huggingface.co/facebook/mms-tts) | Recipe MIT; MMS weights/derivatives CC BY-NC 4.0, separate from Transformers code. Base religious-reading lineage lacks itemized source rights in the inspected card. New recordings/transcripts need their own permissions; public outputs/derivative distribution need explicit review beyond the project's current local-only use. [Recipe and license note](https://github.com/ylacombe/finetune-hf-vits), [MMS-specific notice](https://github.com/facebookresearch/fairseq/blob/main/examples/mms/README.md), [CC terms](https://creativecommons.org/licenses/by-nc/4.0/legalcode) | Recipe describes one-GPU fine-tuning and discriminator conversion. Transcribed, aligned, clean White Hmong audio plus a reviewer-approved tokenizer/inventory are needed. Published small-sample recipe claims concern other demonstrated languages, not Hmong sufficiency. RTX 4070 training fit and corpus size remain unmeasured. | Plausible adaptation experiment only after approved data and frontend design. Requires separate training authorization and an isolated audited environment. |

These observations distinguish a publisher's support claim from demonstrated
quality. No inspected source supplied a reproducible White Hmong sentence pack,
independent fluent-rater protocol, per-tone error analysis, and acceptance
decision together. That is a limit of this search, not proof that no human
testing has occurred. Public demos, download counts, and automatic ASR scores
cannot substitute for the project's fluent review.

Two further checks narrowed the shortlist. The current
[OmniVoice language table](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md)
also has no exact `mww`, `hnj`, or `hmn`, or Hmong-named entry; a large language
count is not White Hmong evidence. The indexed
[Xuajpaj2026 Orpheus repository](https://huggingface.co/Xuajpaj2026/orpheus-hmong-tts)
returned HTTP 401 through both page and metadata access, so its current content,
availability, and license could not be verified. It is not a selected alternative.
ASR and machine-translation coverage are not TTS capability.

## Reproducible research identity and unresolved runtime details

Metadata-only API observations (external copies retained; **no weight access**):

| Artifact | Observed immutable revision | What remains to audit |
|---|---|---|
| [Hmong Orpheus metadata](https://huggingface.co/api/models/Pakorn2112/Orpheus-TTS-hmong-3b) | `464d34449a778b1a6d9506bc10bd4e00f752c5c8` | Full license chain, dataset/voice rights, RPA/tokenizer behavior, speaker selection, complete inference recipe |
| [Orpheus base metadata](https://huggingface.co/api/models/canopylabs/orpheus-3b-0.1-ft) | `4206a56e5a68cf6cf96900a8a78acd3370c02eb6` | Trace through the declared Unsloth base as well; this observed ancestor is not a substitute base checkpoint |
| [SNAC codec metadata](https://huggingface.co/api/models/hubertsiuzdak/snac_24khz) | `d73ad176a12188fcf4f360ba3bf2c2fbbe8f58ec` | MIT declaration; listed weight is `pytorch_model.bin`, not safetensors; require an audited safe-loading/artifact decision before execution |
| [Hmong F5 distribution source](https://github.com/YangNobody12/hmong-TTS/tree/1a88f6b9d39ed2c2772736849c240390667b96b2) | `1a88f6b9d39ed2c2772736849c240390667b96b2` | Mutable Docker tag is not an immutable model identity; obtain digest and component inventory |
| [MMS fine-tuning recipe](https://github.com/ylacombe/finetune-hf-vits/tree/6f3f51f4d667f5c3eef89484d151ffd39d2c2b89) | `6f3f51f4d667f5c3eef89484d151ffd39d2c2b89` | Training discriminator/base artifacts, dependencies, text frontend, local-only data paths and disabled uploads/trackers |

The [SNAC card](https://huggingface.co/hubertsiuzdak/snac_24khz) documents mono
24 kHz speech decoding with a 19.8M-parameter codec. The current workbench only
supports MMS/VITS and requires safetensors for that backend. Orpheus and F5 are
not registry-compatible drop-ins; do not change registry revisions or weaken
the existing load policy to fit a candidate.

As a planning estimate, 3 billion BF16 parameters alone occupy about 6 GB
(decimal), before codec, activations, KV cache, framework, and workspace. This
arithmetic is **not a measured 12 GB fit**. Use a separate process and short
inputs to establish memory and generation bounds in a later approved trial.
Do not assume quantization preserves tone quality or automatically switch
precision when a run fails. Record such a change as a different configuration.

## Proposed bounded candidate experiment — not executed

Prerequisites are the completed [human pack and records](hmong_collection_review.md),
an independently agreed rubric, resolved local-evaluation permissions for the
candidate and any reference voice, an exact artifact/code/dependency inventory,
and owner authorization for candidate access and local execution. A future
public-use decision is separate. Unresolved rights are a stop condition even
if samples sound good.

1. Select the Hmong Orpheus revision above only if those gates clear. Include
   at most one additional cleared candidate; no fallback downloading. Set a
   maximum **one-hour GPU execution budget**, one process, and batch size one
   on the available RTX 4070. Reserve ample memory; stop on OOM or repeated
   generation failures and report them instead of changing configuration.
2. The custodian supplies only the **20 development cases** and their approved
   hashes. Confirm exact decoded text at runner input. Inspect tokenizer and
   preprocessing behavior on development text with the fluent reviewer; never
   silently strip tone letters, normalize, transliterate, or substitute spellings.
   Preserve original text and record any approved model-input transformation.
3. Fix one seed/settings/voice configuration per candidate before listening.
   Try four preselected development cases, one per primary category. Bound each
   generation to **60 seconds wall time and 30 seconds generated audio** in an
   isolated worker; verify termination/unload behavior before the batch. A
   timeout or truncated result is a failure, not a usable short sample. The
   current non-preemptive service alone does not provide these execution caps.
4. If runtime checks and the reviewer-defined early stop conditions pass,
   generate the other 16 cases. Permit only five predeclared repeat cases for
   stability, at most **25 generations per candidate, 50 total**. Keep failures
   and every attempt; do not pick the best of many seeds. The 10 held-out cases
   remain unopened by the experiment operator.
5. Randomize anonymous clip order for independent listening. The separate
   fluent reviewer judges intelligibility, meaning-changing tone/pronunciation
   errors, acceptable variants, phrasing/punctuation, and naturalness using
   the rubric agreed before outputs. The speaker can provide a second judgment;
   preserve disagreement and adjudication rather than averaging it away.
6. Retain exact model/codec revisions and hashes, settings, prompt/pack hashes,
   runtime/device/peak memory, timing, waveform checks, failures, randomized
   labels, and human judgments outside Git. Publish only sanitized aggregates
   if separately authorized. Structural QC is engineering evidence only.
7. Choose whether to use, adapt, collect data, or stop based on the table below.
   Only after freezing the finalist, frontend, settings, rubric, and rights
   review may the custodian authorize a **single final pass on the 10 held-out
   cases**. If those outputs drive tuning, replace the reserve before another
   final claim. Thirty sentences cannot establish broad community acceptance.

## Recording and training decision

| Route | Evidence that would justify the next proposal | Required human decisions, permissions, resources, and quality criteria |
|---|---|---|
| Use an existing voice | Development results meet the prospectively agreed fluent-review criteria, show no unresolved critical error, and run within owner-set latency/memory bounds. A frozen finalist subsequently meets held-out criteria. | Fluent reviewers accept the stated variety/uses and document limits; owner accepts rights and voice provenance for the intended public service/output, operational costs, and attribution. Public deployment still needs its own security/authorization review. No recording is needed just to change voice identity unless explicitly requested. |
| Adapt a model | A cleared base shows useful development intelligibility but repeatable, well-characterized deficits that a reviewed frontend or specific data can plausibly address. A bounded pilot can compare before/after on development cases. | Reviewer-approved RPA inventory and error taxonomy; separately permitted paired speech/text with actual speaker choices for adaptation and intended outputs; base/discriminator/codec licenses; isolated training stack, GPU/memory/time/storage budget; owner-defined pilot stop rule. Any frontend rules need language evidence. Keep evaluation cases out of training/reference material. |
| Collect recordings for a pilot | No cleared existing voice meets needs, or adaptation fails for identifiable coverage/data reasons and no suitable permitted corpus exists. Participants and reviewers decide that the gap merits new data. | Explicit recording and model-training permissions, separate choices for public synthetic audio, real samples, and weights; compensation, credit/anonymity, retention, access, withdrawal limits, and voice-misuse expectations. A willing speaker and separate reviewer, quiet space, microphone/interface, editing/transcription time, storage, and GPU budget are required. |
| Defer or stop | Rights remain unresolved, fluent review cannot support acceptance, critical distinctions remain unreliable, or cost exceeds the agreed bounds. | Owner and participants document the reason; preserve the evidence, avoid capability claims, and decide whether a narrower use case is worthwhile. Do not use more recordings as an automatic answer to a licensing or language-scope problem. |

If recording is later chosen, propose a **small separately approved pilot of
30–60 minutes of usable aligned speech** as a budget hypothesis, not an
established sufficiency threshold. Use separate recording prompts selected by
humans from observed development gaps, excluding all evaluation cases and near
duplicates. Measure usable yield, transcription accuracy, coverage, and learning
progress before proposing hours of data. The reviewer must decide acceptable
linguistic coverage and accuracy; no numerical tone, pronunciation, naturalness,
or MOS pass threshold is imposed here. The owner must approve the actual amount
of effort, and the speaker can decline. Full training from scratch is not
justified by this evidence or the 30-sentence evaluation sample.

NV-001 through NV-008 remain open. The next owner action is completing the
external 20/10 pack and its records with the willing speaker and separate
reviewer, then reviewing this bounded candidate-access proposal and its
unresolved rights questions. Research authorization has not authorized any
candidate-weight download, recruitment, recording, training, public output, or deployment.
