# License and provenance matrix

Audit date: 2026-07-28
Status meanings: **approved** means eligible only for the scoped local use;
**blocked** means it must not be downloaded/used for this project yet. This is
an engineering audit, not legal advice.

| Artifact | Exact revision/version | Code license | Weight/model license | Known training-data lineage/restrictions | Output restrictions | Redistribution status | Use status |
|---|---|---|---|---|---|---|---|
| This repository | working tree, `audited-tts-workbench` v0.4.0 | No license granted; all rights reserved pending owner decision | n/a | Synthetic fixtures and public metadata only; no speaker data | n/a | Not permitted | Local development only |
| Workbench model registry | schema v1, `configs/models/registry.yaml` | Project code-license status above | n/a | Metadata transcribed from the audited primary sources below; contains no weights | No language-quality claim; every active entry is `not_evaluated` | Metadata only; third-party weights are not bundled | Approved active control |
| FastAPI service framework | `fastapi==0.136.3` | MIT | Does not change checkpoint license | Runtime framework; no training data or model weights | Determined by checkpoint/consent, not framework | Code per MIT; no cloud/standard extra installed | Approved for bounded local service |
| Starlette ASGI framework | `starlette==1.0.0` | BSD-3-Clause | Does not change checkpoint license | Direct compatibility pin for FastAPI; no training data or model weights | Determined by checkpoint/consent | Code per BSD-3-Clause | Approved for bounded local service |
| Uvicorn ASGI server | `uvicorn==0.46.0` | BSD-3-Clause | Does not change checkpoint license | Local loopback server; no training data or model weights | Determined by checkpoint/consent | Code per BSD-3-Clause; standard extra not installed | Approved for one-worker local service |
| HTTPX in-process test client | `httpx==0.28.1` | BSD-3-Clause | n/a | Development/test dependency only; no external network used by M5 tests | n/a | Code per BSD-3-Clause | Approved for in-process ASGI tests |
| Transformers MMS/VITS runtime | `transformers==5.13.1` | Apache-2.0 | Does not change checkpoint license | Runtime library; no training data | Determined by checkpoint/consent, not library alone | Code per Apache-2.0 | Approved for pinned smoke path |
| PyTorch runtime | `torch==2.12.0` | BSD-style | Does not change checkpoint license | Runtime library; no training data | Determined by checkpoint/consent | Code per upstream license | Approved for x86-64 Linux smoke path |
| Meta MMS collection/full training checkpoints | `facebook/mms-tts@44cc7fb408064ef9ea6e7c59130d88cac1274671` | The MMS-specific README states CC BY-NC 4.0 for MMS code and weights; the surrounding Fairseq repository is MIT | CC BY-NC 4.0 | MMS paper describes a dataset based on readings of publicly available religious texts. Source-recording rights are not itemized per TTS checkpoint in the model card; treat lineage as non-commercial and incomplete for commercial clearance. | No project claim that raw outputs are automatically relicensed; workbench use remains non-commercial. | Attribution required; commercial use prohibited; the workbench does not redistribute weights | Approved as collection-level provenance; training use is deferred |
| MMS Vietnamese checkpoint | `facebook/mms-tts-vie@b58928d033932a49aa8e3d6cf11625b25fe928d2` | Transformers runtime Apache-2.0 | CC BY-NC 4.0 | Same MMS lineage above. No transfer to or support for White Hmong is claimed **[NV]**. | Local non-commercial inference; language quality is `not_evaluated` | The workbench does not redistribute weights | Registered for local inference; external audited public prompt required |
| MMS English checkpoint | `facebook/mms-tts-eng@c71de0fe7204c83f1c10820a7d696d0b450048ba` | Transformers runtime Apache-2.0 | CC BY-NC 4.0 | Same MMS lineage above | Local non-commercial inference; language quality is `not_evaluated` | The workbench does not redistribute weights | Registered for local inference with a synthetic smoke fixture |
| MMS fine-tuning recipe | `ylacombe/finetune-hf-vits@6f3f51f4d667f5c3eef89484d151ffd39d2c2b89` | MIT | Recipe documentation says MMS derivatives inherit CC BY-NC 4.0 | Community-maintained recipe; not itself a training dataset. Hosted Hub/W&B steps must be disabled for private data. | Follows base checkpoint and speaker consent | Recipe code per MIT; resulting project weights not approved for distribution | Revision audited; execution deferred to pilot/training environment |
| Piper fallback implementation | `OHF-Voice/piper1-gpl@49fab2fd5c1511aadc8020524d8ea31cfbb5b238` (latest release observed: v1.4.2) | GPL-3.0 | Per-voice license varies; no voice selected | Official docs require checking each voice model card; checkpoint and dataset lineage is not inherited from the code license alone. | Voice-specific; project consent still applies | No checkpoint redistribution until a specific voice lineage audit | Code audited; all weights blocked |
| F5-TTS v1 candidate | code `SWivid/F5-TTS@91f499635cb4f8b8a926e83f1839f5338bc2ef87`; HF model repo `84e5a410d9cead4de2f847e7c9369a6440bdfaca` | MIT | CC BY-NC 4.0 | Official repository says pretrained models inherit the non-commercial restriction from Emilia, an in-the-wild dataset. | Non-commercial; voice/reference consent independently required | No project redistribution approved | Blocked; post-MVP only |
| XTTS-v2 candidate | `coqui/XTTS-v2@6c2b0d75eae4b7047358e3b6bd9325f857d43f77` (license file tag v2.0.3) | Coqui TTS code must be separately audited at the chosen revision | Coqui Public Model License 1.0.0 | Model card does not provide a per-item commercial-clearance chain sufficient for this project audit | CPML expressly limits both model and outputs to non-commercial use | No project redistribution approved | Blocked; benchmark only and no White Hmong support claimed |
| OpenVoice V2 candidate | `myshell-ai/OpenVoice@74a1d147b17a8c3092dd5430504bd83ef6c7eb23` | MIT | Current official README says V1/V2 MIT | Full base-TTS/training-data lineage is not sufficiently itemized for project clearance; it does not itself solve White Hmong text pronunciation. | Project speaker/reference consent still required | No checkpoint selected or approved | Blocked; optional post-MVP conversion layer only |

## Availability audit

The pinned MMS collection model card lists `eng` and `vie`. Exact ISO-code list
searches on 2026-07-14 found no `mww`, `hnj`, or `hmn` entry. Therefore there is
no approved claim of a public White Hmong/Hmong Daw MMS TTS checkpoint. MMS TTS
uses separate per-language checkpoints rather than a single universal TTS model.

## Primary sources (accessed 2026-07-14)

- MMS collection/model card and license: https://huggingface.co/facebook/mms-tts
- Vietnamese checkpoint at audited revision: https://huggingface.co/facebook/mms-tts-vie/tree/b58928d033932a49aa8e3d6cf11625b25fe928d2
- English checkpoint at audited revision: https://huggingface.co/facebook/mms-tts-eng/tree/c71de0fe7204c83f1c10820a7d696d0b450048ba
- Official MMS paper/project description: https://ai.meta.com/research/publications/scaling-speech-technology-to-1000-languages/
- Fairseq MMS instructions/license statement: https://github.com/facebookresearch/fairseq/blob/main/examples/mms/README.md
- Fairseq repository license: https://github.com/facebookresearch/fairseq/blob/main/LICENSE
- Transformers MMS documentation: https://huggingface.co/docs/transformers/model_doc/mms
- Fine-tuning recipe and derivative-license note: https://github.com/ylacombe/finetune-hf-vits
- Piper code, voice warning, and training path: https://github.com/OHF-Voice/piper1-gpl and https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/TRAINING.md
- F5-TTS code/weight statement: https://github.com/SWivid/F5-TTS
- XTTS-v2 CPML text: https://huggingface.co/coqui/XTTS-v2/blob/v2.0.3/LICENSE.txt
- OpenVoice V2 README/license statement: https://github.com/myshell-ai/OpenVoice
- PyTorch install/platform guidance and pinned-version commands: https://pytorch.org/get-started/locally/ and https://pytorch.org/get-started/previous-versions/

## M5 service sources (accessed 2026-07-28)

- FastAPI 0.136.3 package metadata, Python compatibility, dependencies, and
  MIT license: https://github.com/fastapi/fastapi/blob/0.136.3/pyproject.toml
  and https://github.com/fastapi/fastapi/blob/0.136.3/LICENSE
- Starlette 1.0.0 package metadata, Python compatibility, and BSD-3-Clause
  license: https://github.com/Kludex/starlette/blob/1.0.0/pyproject.toml and
  https://github.com/Kludex/starlette/blob/1.0.0/LICENSE.md
- Uvicorn 0.46.0 package metadata, Python compatibility, and BSD-3-Clause
  license: https://github.com/Kludex/uvicorn/blob/0.46.0/pyproject.toml and
  https://github.com/Kludex/uvicorn/blob/0.46.0/LICENSE.md
- Uvicorn release notes: https://www.uvicorn.org/release-notes/
- HTTPX 0.28.1 package metadata, Python 3.12 classifier, and BSD-3-Clause
  license: https://github.com/encode/httpx/blob/0.28.1/pyproject.toml and
  https://github.com/encode/httpx/blob/0.28.1/LICENSE.md

## Audit rule

Before any new checkpoint is downloaded, add its repository, immutable revision,
license text/link, training-data lineage, output terms, and redistribution status
here. Record downloaded file hashes in a private run manifest. A mutable branch
name or a code license alone is insufficient.
