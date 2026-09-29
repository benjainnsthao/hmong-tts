# White Hmong voice research and recording decision

Refreshed **2026-09-28** from current primary sources. Target: **White Hmong
(Hmoob Dawb), RPA**. The owner authorized research, external text preparation,
local code/tests and bounded local trials when rights, loading and resources
permit. Publication, deployment, outreach, agreement acceptance, payment,
recording, adaptation and training remain outside this task.

**Recommendation: defer voice selection and keep the existing-voice route first.**
The published 20/10 draft and review packet are prepared. No candidate currently
clears all local-trial prerequisites, so **zero candidates were selected for
execution, zero weights downloaded and zero audio generated**. Keep Orpheus as
the closest variety-labelled research lead; do not propose recording or training
to solve its licensing or artifact-format gaps. There is no demonstrated usable
White Hmong voice in this project yet.

## Current comparison

| Route | Primary evidence and identity | Local trial | Eventual public use |
|---|---|---|---|
| **Pakorn2112/Orpheus-TTS-hmong-3b** | [Pinned card](https://huggingface.co/Pakorn2112/Orpheus-TTS-hmong-3b/blob/464d34449a778b1a6d9506bc10bd4e00f752c5c8/README.md) advertises Hmong Daw and Apache-2.0 research/educational use. Two BF16 safetensors shards total **6,601,763,560 bytes**; this is artifact size, not measured peak memory. | **Blocked.** Declared Unsloth/Orpheus lineage reaches Llama 3.2; the Apache label does not reconcile its upstream obligations. No existing owner acceptance of applicable Llama terms is recorded. Official SNAC weights are pickle-format only; no verified safetensors replacement. Speaker selection and itemized voice/data permissions remain undocumented in inspected materials. | Unresolved base terms, Hmong dataset/speaker rights, output/service conditions and fluent acceptance. Research permission is not public clearance. |
| **Pakorn2112/F5TTS-Hmong / Local Voice distribution** | [Model inventory](https://huggingface.co/Pakorn2112/F5TTS-Hmong/tree/c50fc0cc991bc0c4f22d86c7a6152730c667c0d5) identifies a **1,348,435,761-byte safetensors** checkpoint and vocabulary, with no model card/license declaration. [Distribution guide](https://github.com/YangNobody12/hmong-TTS/blob/1a88f6b9d39ed2c2772736849c240390667b96b2/F5TTS-model/README.md) names a mutable Docker tag. | **Blocked.** Repository MIT code does not grant rights to an unlicensed checkpoint. Docker-to-checkpoint identity, exact base, vocoder, reference audio/transcript, voice/data rights and complete dependencies are unresolved. White Hmong/RPA scope is not established by the generic Hmong label. | Upstream [F5 terms](https://github.com/SWivid/F5-TTS/blob/283252563dbf91be625e0c27926acfaac449186c/README.md#license) distinguish MIT code from Emilia-derived NC weights; neither clears this derivative, reference voice or outputs. |
| **Yuhalu 2.0** | [Manual](https://yuhalu.org/help/UserManual.html) explicitly covers White and Blue Hmong/RPA and concatenative synthesis. Current [plans](https://yuhalu.org/plans.html) describe annual subscriptions and payment/activation. | **Blocked under this task.** No existing entitlement or immutable installer identity is supplied. [EULA](https://yuhalu.org/eula.php), effective August 17, 2026, requires affirmative acceptance for subscription requests. No purchase, activation or agreement was attempted. | Software/audio-bank redistribution and training/cloning are restricted; plan output permission does not automatically authorize a hosted TTS service. |
| **MMS/VITS adaptation** | [MMS collection](https://huggingface.co/facebook/mms-tts) still lists no exact `mww`, `hnj`, `hmn` or Hmong entry. [Recipe](https://github.com/ylacombe/finetune-hf-vits/tree/6f3f51f4d667f5c3eef89484d151ffd39d2c2b89) is a possible future adaptation route. | **Not an existing Hmong voice.** Requires separately authorized training, permitted aligned audio and a reviewed frontend. Current English/Vietnamese registry entries remain engineering demonstrations. | MMS model NC terms, data/voice permissions and independent acceptance remain separate from recipe/code licensing. |

The older Yuhalu finding that displayed offers were testing-only is superseded:
that banner is now an HTML comment, while the visible page gives subscription
steps. No payment flow was entered. Model metadata and ordinary source documents
were fetched; source code was inspected as text and never remotely executed.

The [OmniVoice language table](https://github.com/k2-fsa/OmniVoice/blob/master/docs/languages.md)
still has no exact Hmong/code match in the retained snapshot. The previously
identified [Xuajpaj2026 repository](https://huggingface.co/Xuajpaj2026/orpheus-hmong-tts)
again returned HTTP 401. Neither is a cleared alternative. These searches do not
prove that no other Hmong voice exists. Publisher quality claims, demos and
model popularity do not substitute for independent fluent evaluation.

## Immutable chain and compatibility

Metadata, exact small config/card/license files, download failures, hashes and
access times are retained in the external `research/` folder. No authentication
was used to bypass a gated resource; base config HTTP 401 responses are recorded.

| Component | Observed immutable revision | Loading/dependency observation |
|---|---|---|
| Hmong Orpheus | `464d34449a778b1a6d9506bc10bd4e00f752c5c8` | Built-in `LlamaForCausalLM`, BF16, 28 layers; configuration uses `rope_parameters`. No checkpoint loading or compatibility pass is claimed. |
| Unsloth Orpheus | `eae2b6e5e429c81b95ac42a883ac64f126583d43` | [Declared base chain](https://huggingface.co/unsloth/orpheus-3b-0.1-ft/blob/eae2b6e5e429c81b95ac42a883ac64f126583d43/README.md); config names Transformers 4.53.1. Hmong card suggests Unsloth with auto dtype; do not adopt auto precision silently. |
| Canopy fine-tuned / pretrained | `4206a56e5a68cf6cf96900a8a78acd3370c02eb6` / `bf0cce99761b2f5857b3d85829691f696bf20cb0` | Gated bases; cards trace to Llama. These are provenance identities, not authorized downloads or substitute checkpoints. |
| Llama 3.2 3B Instruct | `0cb88a4f764b7a12671c53f0838cd831a0843b95` | [Community license](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct/blob/0cb88a4f764b7a12671c53f0838cd831a0843b95/LICENSE.txt) governs use/derivatives and carries an acceptable-use policy. Resolve applicability and owner acceptance; the task cannot accept it. |
| SNAC 24 kHz weights | `d73ad176a12188fcf4f360ba3bf2c2fbbe8f58ec` | [MIT-labelled inventory](https://huggingface.co/hubertsiuzdak/snac_24khz/tree/d73ad176a12188fcf4f360ba3bf2c2fbbe8f58ec): `pytorch_model.bin`, **79,488,254 bytes**, no safetensors. |
| SNAC code | `8f79a718f1ad71f94f79999f0071348227aff22e` | [Loader](https://github.com/hubertsiuzdak/snac/blob/8f79a718f1ad71f94f79999f0071348227aff22e/snac/snac.py) calls `torch.load`; requirements leave Torch, NumPy, einops and Hub unpinned. Modern Torch defaults do not satisfy this project's safetensors-only policy. No conversion/deserialization was attempted. |
| Orpheus code | `e64661fe6d02c414fc77c53578c9d64082614861` | [Setup](https://github.com/canopyai/Orpheus-TTS/blob/e64661fe6d02c414fc77c53578c9d64082614861/orpheus_tts_pypi/setup.py) depends on unpinned SNAC/vLLM; repository license is Apache-2.0 while a packaging classifier says MIT. Resolve and lock an isolated inference stack before use. |
| Hmong F5 / distribution | `c50fc0cc991bc0c4f22d86c7a6152730c667c0d5` / `1a88f6b9d39ed2c2772736849c240390667b96b2` | No evidence tying Docker contents to the HF artifact; no container pull. |
| Upstream F5 | `283252563dbf91be625e0c27926acfaac449186c` | [Dependencies](https://github.com/SWivid/F5-TTS/blob/283252563dbf91be625e0c27926acfaac449186c/pyproject.toml) include Torch/torchaudio, Transformers, Vocos and many broad ranges. Upstream supports Vocos/BigVGAN, but this derivative's actual vocoder and reference-voice identity are unknown. |

The inspected artifacts supply no itemized Hmong corpus rights, voice permission
record or independent sentence-level acceptance protocol. Absence in these
sources is a specific evidence gap, not an allegation about their creators.

Resource preflight on this host: RTX 4070, **12,282 MiB VRAM, 9,996 MiB free**
at the recorded observation; **15.52 GiB RAM, 13.92 GiB available**; approximately
**937 GiB disk free**. Orpheus's weight files alone occupy about 6.15 GiB.
The remaining space does not prove peak GPU/RAM fit or codec/generation speed.
Existing Python 3.12 / Torch 2.13.0 / Transformers 5.13.1 was inspected but not
changed. Candidate dependencies were not installed into it or into a new ML
environment, because eligibility failed before that step.

## Bounded experiment procedure, ready once prerequisites clear

The user's current authorization already permits qualifying local trials;
there is no new generic authorization gate. Resolve **specific** missing model/
base/codec/voice rights and safe immutable artifacts first. Public-use clearance
is separate. If language review is pending, label every run exploratory.

1. Select at most two eligible fixed configurations. Use external artifacts and
   a separate locked Python environment. Record model, codec, code and dependency
   revisions/hashes, exact device/dtype, seed, voice, frontend and every setting.
   No unreviewed remote code, pickle fallback, automatic quantization or precision
   change. Bound download size from the inventory before fetching weights.
2. Consume only `development/development-v1.json`. Check exact text hashes and
   source-use conditions; retain preprocessing/tokenizer observations separately.
   Start with one case per category, fixed before output inspection. Do not read
   the reserve, borrow its text as reference audio, or tune from its metadata.
3. Use one isolated worker, batch one, at most 256 input characters, 1,024 new
   model tokens, 30 seconds of audio and 60 seconds wall time per generation;
   allow a separate 180-second cold-load deadline and one-hour total GPU budget.
   Verify child-process termination/unload first. Capture worker peak RSS and
   GPU allocated/reserved peaks; keep unavailable observations as unavailable.
4. Stop on OOM or repeated failures. A timeout, token-cap truncation or audio-cap
   truncation is a failed attempt, not a usable clipped sample. Record a changed
   configuration separately instead of retrying silently. Complete at most 20
   unique development cases and five predeclared repeats per configuration,
   50 total attempts including failures. No best-seed selection.
5. Record load/inference latency, generated duration/RTF, resource peaks,
   waveform hashes and provenance, every failure and the unchanged workbench
   waveform QC results. QC/ASR can flag defects; neither proves pronunciation,
   tone, intelligibility, naturalness or White Hmong support.
6. Use the [listening exporter](hmong_evaluation_pack.md#source-audit-and-listening-preparation)
   to randomize candidate labels and clip order with a retained separate key.
   Review against the prospectively accepted rubric, preserving disagreements.
   The existing external packet has texts and empty scores but **no audio**.
7. After development-only selection, fix the candidate, environment, configuration,
   frontend and accepted criteria. Reconcile the complete reviewed pack and its
   permissions, record the freeze and release a single ten-case held-out pass.
   Report all ten results/failures. Tuning from those outputs retires this reserve.

Inference latency, memory peaks, waveform QC, audio quality and finalist scores
are **not measured**, not zero or passed. There is no audio requiring fluent
listening yet; there is source text and a rubric ready for fluent review.

## Next decision

Review the [single handoff packet](hmong_collection_review.md#one-review-packet).
Recommended disposition is **defer execution while retaining the existing-voice
lead**. An owner rights decision alone cannot resolve missing codec artifacts or
publisher data/voice evidence; do not present it as sufficient to start a trial.
No adaptation or recording pilot is justified by the current licensing blockers.
If a later cleared voice has repeatable linguistic deficits, propose bounded
adaptation with permitted separate data. A recording pilot is a separate later
proposal only if a demonstrated coverage/data gap warrants it; no training or
recording begins here. M7 approvals/manifests and NV-001 through NV-008 are unchanged.
