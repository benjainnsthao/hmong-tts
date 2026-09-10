# License and provenance matrix

Active M7 audit date: 2026-09-10. Historical source sections retain their original dates.

M7 original-code approval: benjainnsthao, conversational owner decision
on 2026-09-10; authority and commercial reuse confirmed. This is not a
cryptographic signature or final release approval. See `m7_owner_approval.json`.
Status meanings: **approved** means eligible only for the scoped local use;
**blocked** means it must not be downloaded/used for this project yet. This is
an engineering audit, not legal advice.

| Artifact | Exact revision/version | Code license | Weight/model license | Known training-data lineage/restrictions | Output restrictions | Redistribution status | Use status |
|---|---|---|---|---|---|---|---|
| This repository | M7 candidate, `audited-tts-workbench` v1.0.0 | Apache-2.0 for covered original code; LICENSE/NOTICE define scope | n/a | Original synthetic fixtures and public metadata; no speaker data | No automatic output license | Original code/config/tests/docs and sanitized evidence; no external runtime artifacts | Code licensing approved; final outcome in M7 owner record |
| Workbench model registry | schema v1, `configs/models/registry.yaml` | Project code-license status above | n/a | Metadata transcribed from the audited primary sources below; contains no weights | No language-quality claim; every active entry is `not_evaluated` | Metadata only; third-party weights are not bundled | Approved active control |
| FastAPI service framework | `fastapi==0.136.3` | MIT | Does not change checkpoint license | Runtime framework; no training data or model weights | Determined by checkpoint/consent, not framework | Code per MIT; no cloud/standard extra installed | Approved for bounded local service |
| Starlette ASGI framework | `starlette==1.3.1` | BSD-3-Clause | Does not change checkpoint license | Direct compatibility pin for FastAPI; no training data or model weights | Determined by checkpoint/consent | Code per BSD-3-Clause | Approved for bounded local service |
| Uvicorn ASGI server | `uvicorn==0.46.0` | BSD-3-Clause | Does not change checkpoint license | Local loopback server; no training data or model weights | Determined by checkpoint/consent | Code per BSD-3-Clause; standard extra not installed | Approved for one-worker local service |
| HTTPX in-process test client | `httpx==0.28.1` | BSD-3-Clause | n/a | Development/test dependency only; no external network used by M5 tests | n/a | Code per BSD-3-Clause | Approved for in-process ASGI tests |
| uv environment/lock tool | `uv==0.11.28` required range `<0.12` | Dual MIT or Apache-2.0 | n/a | Environment tool only | n/a | Tool is not bundled in the project wheel | Approved for frozen core and MMS reproduction |
| Transformers MMS/VITS runtime | `transformers==5.13.1` | Apache-2.0 | Does not change checkpoint license | Runtime library; no training data | Determined by checkpoint/consent, not library alone | Code per Apache-2.0 | Approved for pinned smoke path |
| PyTorch runtime | `torch==2.13.0` | BSD-style | Does not change checkpoint license | Runtime library; no training data | Determined by checkpoint/consent | Code per upstream license | Approved for x86-64 Linux smoke path |
| safetensors runtime | `safetensors==0.8.0` | Apache-2.0 | Does not change checkpoint license | Safe tensor serialization runtime; no training data | Determined by checkpoint/consent | Code per Apache-2.0 | Approved; M7 requires safetensors and tests no pickle fallback |
| Accelerate (removed) | former 1.14.0 | Apache-2.0 | n/a | Unused helper with an unpatched advisory | n/a | Not in M7 dependencies or packages | Removed; see M7 dependency audit |
| SciPy runtime | `scipy==1.18.0` | BSD | Does not change checkpoint license | Numerical runtime; no training data | Determined by checkpoint/consent | Code per BSD terms | Approved in locked Linux x86-64 MMS group |
| PyTorch CUDA wheel dependencies | exact `nvidia-*-cu13`, CUDA toolkit, Triton, and related versions/hashes in `uv.lock` | Package-specific NVIDIA/proprietary or upstream terms; no project relicense asserted | Does not change checkpoint license | Binary runtime components resolved transitively by locked PyTorch | Determined by checkpoint and component terms | Installed in the external environment; not bundled or redistributed by this project | Approved for scoped local CUDA execution only; M7 component audit in `m7_dependency_audit.md` |
| Meta MMS collection/full training checkpoints | `facebook/mms-tts@44cc7fb408064ef9ea6e7c59130d88cac1274671` | The MMS-specific README states CC BY-NC 4.0 for MMS code and weights; the surrounding Fairseq repository is MIT | CC BY-NC 4.0 | MMS paper describes a dataset based on readings of publicly available religious texts. Source-recording rights are not itemized per TTS checkpoint in the model card; treat lineage as non-commercial and incomplete for commercial clearance. | No project claim that raw outputs are automatically relicensed; workbench use remains non-commercial. | Attribution required; commercial use prohibited; the workbench does not redistribute weights | Approved as collection-level provenance; training use is deferred |
| MMS Vietnamese checkpoint | `facebook/mms-tts-vie@b58928d033932a49aa8e3d6cf11625b25fe928d2` | Transformers runtime Apache-2.0 | CC BY-NC 4.0 | Same MMS lineage above. No transfer to or support for White Hmong is claimed **[NV]**. | Local non-commercial inference; language quality is `not_evaluated` | The workbench does not redistribute weights | Registered for local inference with the revalidated M7 external prompt gate |
| Retained M6 / revalidated M7 Vietnamese prompt | `external:vietnam-constitution-2013-article-1`; SHA-256 `b6919cd1f33ec808355462bfa29e8444f8525560f8223d0486e67b35f29854c5` | Not covered by copyright under Vietnam IP Law No. 50/2005/QH11 Article 15(2), which excludes legal documents and official translations | n/a | One unmodified sentence from Article 1 of the 2013 Constitution; issuer/publisher: National Assembly of Vietnam / Government Portal | Scoped local non-commercial synthesis demonstration; prompt text remains external | Raw prompt is not distributed in Git or wheel | Approved for scoped M7 local engineering demonstration after current-source/hash gate |
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

## M6 refreshed sources (accessed 2026-09-09)

- uv 0.11.28-compatible Python support and frozen/offline behavior:
  https://docs.astral.sh/uv/reference/policies/python/,
  https://docs.astral.sh/uv/reference/cli/, and
  https://github.com/astral-sh/uv/tree/0.11.28
- PyTorch platform/CUDA guidance and exact 2.12.0 package metadata, Python
  classifiers, and BSD-3-Clause declaration:
  https://docs.pytorch.org/get-started/locally/ and
  https://pypi.org/project/torch/2.12.0/
- Exact optional package metadata:
  https://pypi.org/project/transformers/5.13.1/,
  https://pypi.org/project/safetensors/0.8.0/,
  https://pypi.org/project/accelerate/1.14.0/, and
  https://pypi.org/project/scipy/1.18.0/
- Exact checkpoint pages, immutable revisions, CC BY-NC 4.0 metadata, and
  available safetensors objects:
  https://huggingface.co/facebook/mms-tts-eng/tree/c71de0fe7204c83f1c10820a7d696d0b450048ba
  and
  https://huggingface.co/facebook/mms-tts-vie/tree/b58928d033932a49aa8e3d6cf11625b25fe928d2
- Vietnamese prompt record and official source scan:
  https://vanban.chinhphu.vn/?classid=1&docid=171264&pageid=27160&typegroupid=1
  and https://datafiles.chinhphu.vn/cpp/files/vbpq/2013/12/hp.pdf
- Vietnam IP Law No. 50/2005/QH11 and Article 15(2) public-domain basis for
  legal documents: https://www.wipo.int/wipolex/en/legislation/details/12011

The locked environment installed successfully on CPython 3.12/Linux x86-64.
Both checkpoint cache snapshots matched the registered revision names and
contained the safetensors object without downloading the pickle alternative.
No package, model, prompt, or generated-output license is inferred beyond the
primary-source statements above. That M6 observation is historical. The owner subsequently approved covered
original code under Apache-2.0 on 2026-09-10; M7 final disposition remains a
separate approval.

## Audit rule

Before any new checkpoint is downloaded, add its repository, immutable revision,
license text/link, training-data lineage, output terms, and redistribution status
here. Record downloaded file hashes in a private run manifest. A mutable branch
name or a code license alone is insufficient.

## M7 current model, prompt, and distribution audit

All following sources were accessed on **2026-09-10**. The active registry
still contains exactly two checkpoints. Collection/fine-tuning/fallback rows
above document historical provenance or deferred candidates, not permission
to access or execute any additional model during M7. Their old access dates
are not represented as refreshed audits.

| Registered repository | Immutable revision | Cached safetensors SHA-256 |
|---|---|---|
| facebook/mms-tts-eng | c71de0fe7204c83f1c10820a7d696d0b450048ba | 69cf8b651c1493f1801dfd2311c298d694a38357bc9a1e41f410491ea6f0e1be |
| facebook/mms-tts-vie | b58928d033932a49aa8e3d6cf11625b25fe928d2 | 55ded90c3e57dc2814fa2cdfe3f9e7a5c28e1223b06c0a260a4495b080762ffd |

The exact [English model tree](https://huggingface.co/facebook/mms-tts-eng/tree/c71de0fe7204c83f1c10820a7d696d0b450048ba)
and [Vietnamese model tree](https://huggingface.co/facebook/mms-tts-vie/tree/b58928d033932a49aa8e3d6cf11625b25fe928d2),
raw cards at those revisions, and `/api/models/<repository>/revision/<revision>?blobs=true`
returned successfully without authentication. API `sha` matched each registry
revision; both were public/ungated and declared `cc-by-nc-4.0`. Cached snapshot
names and safetensors hashes matched upstream LFS metadata. Neither snapshot
contained a pickle weight file. The [pinned collection card](https://huggingface.co/facebook/mms-tts/blob/44cc7fb408064ef9ea6e7c59130d88cac1274671/README.md)
and [Fairseq MMS notice](https://github.com/facebookresearch/fairseq/blob/main/examples/mms/README.md)
preserve the MMS-specific NC boundary, independently of the surrounding
[Fairseq license](https://github.com/facebookresearch/fairseq/blob/main/LICENSE).
Read the [CC BY-NC 4.0 legal terms](https://creativecommons.org/licenses/by-nc/4.0/legalcode).
Individual source-recording rights remain insufficiently itemized for
commercial clearance. No training data is downloaded or redistributed.

The Vietnamese prompt remains the unmodified approved sentence identified by
`external:vietnam-constitution-2013-article-1` and SHA-256
`b6919cd1f33ec808355462bfa29e8444f8525560f8223d0486e67b35f29854c5`.
The National Assembly/Government Portal [official record](https://vanban.chinhphu.vn/?classid=1&docid=171264&pageid=27160&typegroupid=1)
and [source PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2013/12/hp.pdf)
were re-audited. The downloaded PDF SHA-256 was
`4036ec0b5843fbdd0596b75b6d6c99efa5e1b8c5936c27b9c829396a024767bb`,
matching the retained M6 source byte for byte. Prompt text, source, and OCR
remain external. Government Portal attribution is retained here; no prompt
was invented, corrected, translated, or substituted.

The legal basis is [Vietnam IP Law 50/2005/QH11, Article 15(2)](https://www.wipo.int/wipolex/en/legislation/details/12011),
which excludes legal documents and official translations from copyright
protection. The [2009](https://www.wipo.int/wipolex/en/legislation/details/6566),
[2019](https://www.wipo.int/wipolex/en/legislation/details/19536), and
[2022 amendments](https://datafiles.chinhphu.vn/cpp/files/vbpq/2022/07/07-2022-qh15..pdf)
were checked. [Law 93/2025/QH15](https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/7/93qh.signed.pdf),
Article 71(7), changes industrial-property/plant-variety provisions.
[Law 131/2025/QH15](https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/01/luat131-2025.pdf),
effective 2026-04-01, Article 1(7), adds clause 4 to Article 15 and leaves
clause 2 unchanged; the scanned page was visually checked after OCR.
This supports the scoped local legal-document demonstration. It is not a
blanket global public-domain claim or model/output rights clearance.

| Material | M7 permitted distribution/use |
|---|---|
| Covered original code, build/config/test scripts | Apache-2.0, including commercial reuse, preserving notices |
| Original documentation and sanitized factual evidence | Public candidate material; third-party excerpts/attribution retain their existing terms |
| Historical or third-party material | Existing rights/notices preserved; no blanket retrospective relicense |
| Installed Python/NVIDIA components | External local environment under each upstream license; not bundled in project packages |
| Registered model weights | Local non-commercial use only; external and undistributed |
| Raw prompts, official source PDFs, OCR | External audit evidence; not in Git/wheel/sdist |
| Generated audio and detailed raw reports | Retained locally; not distributed; no Apache model/output license inferred |
| Sanitized measurement summaries and hashes | Public engineering evidence, with no perceptual or language-quality claim |

Full exact dependency/advisory inventory: `m7_dependency_audit.md`. Original
code-license approval, proposed risk acceptance, and final release approval are
separate records. Review again on 2026-12-09 or sooner for a material issue.
