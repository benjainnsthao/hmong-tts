# M7 dependency and supply audit

Access date: **2026-09-10**. Scope: every upstream package in the frozen lock,
plus pinned Hatchling and the actual uv executable version. This is an exact
version review, not a claim that dependencies have no undiscovered defects.
Raw primary metadata and advisory responses remain external under
`m7/20260910T122457Z/audit/`.

## Findings and narrowly scoped corrections

| Component | M6 version | M7 version/disposition | Evidence and reason |
|---|---|---|---|
| Starlette | 1.0.0 | 1.3.1 | Fixes the five applicable GHSA groups below; FastAPI 0.136.3 accepts the resulting pin |
| PyTorch | 2.12.0 | 2.13.0 | GHSA-rrmf-rvhw-rf47 reports a torch.jit.script memory-corruption fix in 2.13.0 |
| setuptools | 81.0.0 | 83.0.0, explicit uv constraint | GHSA-h35f-9h28-mq5c fixes Unicode-normalization exclusion behavior in source packaging |
| Accelerate | 1.14.0 | Removed | GHSA-4j2p-28q2-5m79 has no published fixed release; the adapter does not use this helper |
| psutil | 7.2.2 | Removed | Became unnecessary when Accelerate was removed; memory collection already uses the standard library |
| cuda-toolkit | 13.0.2 | 13.0.3.0 | Required by corrected PyTorch's CUDA 13.0.3 dependency; PyPI normalizes the distribution version |
| Triton | 3.7.0 | 3.7.1 | Required exactly by corrected PyTorch |
| Workbench | 0.5.0 | 1.0.0 | Approved breaking artifact-root migration and stable release candidate |

No other locked package changes. The lock has 83 entries including the
workbench, compared with 85 at M6. The initial audit queried 86 exact PyPI
metadata records (84 upstream lock entries, Hatchling, uv). The corrected audit
queried **84 records** (82 upstream lock entries, Hatchling, uv): every query
succeeded, no selected version was yanked, and the returned vulnerability
lists contained **zero advisories**. Alias duplicates in the initial response
were grouped by GHSA; they were not counted as distinct defects.

Primary advisory records inspected:

- [GHSA-86qp-5c8j-p5mr](https://github.com/advisories/GHSA-86qp-5c8j-p5mr):
  Starlette Host/URL authority inconsistencies; fixed in 1.0.1.
- [GHSA-wqp7-x3pw-xc5r](https://github.com/advisories/GHSA-wqp7-x3pw-xc5r):
  Windows StaticFiles UNC/NTLM exposure; fixed in 1.1.0. The release does not
  use StaticFiles or support Windows model execution, but retains no exception.
- [GHSA-x746-7m8f-x49c](https://github.com/advisories/GHSA-x746-7m8f-x49c):
  HTTPEndpoint method dispatch exposure; fixed in 1.1.0.
- [GHSA-jp82-jpqv-5vv3](https://github.com/advisories/GHSA-jp82-jpqv-5vv3):
  request-path URL authority poisoning; fixed in 1.3.0.
- [GHSA-82w8-qh3p-5jfq](https://github.com/advisories/GHSA-82w8-qh3p-5jfq):
  URL-encoded form limits; fixed in 1.3.1. This service accepts JSON; update
  still removes the affected dependency version.
- [GHSA-rrmf-rvhw-rf47](https://github.com/advisories/GHSA-rrmf-rvhw-rf47):
  PyTorch memory corruption. The advisory's narrative and displayed severity
  differ; M7 does not resolve that discrepancy by downgrading it. The fixed
  version is installed even though the adapter does not call torch.jit.script.
- [setuptools GHSA-h35f-9h28-mq5c](https://github.com/pypa/setuptools/security/advisories/GHSA-h35f-9h28-mq5c):
  build-source exclusion issue; constrained despite Linux execution scope.
- [Accelerate GHSA-4j2p-28q2-5m79](https://github.com/advisories/GHSA-4j2p-28q2-5m79)
  and [upstream issue 4067](https://github.com/huggingface/accelerate/issues/4067):
  sharded checkpoint path traversal/resource exhaustion. Removal was validated
  by both real registered VITS checkpoints, CPU diagnostics, and the service.

The relevant upstream [Starlette](https://github.com/Kludex/starlette/security/advisories)
and [PyTorch](https://github.com/pytorch/pytorch/security/advisories) advisory
indexes were also reviewed. A dated absence of listed advisories is not a
comprehensive security proof. Native code, host drivers, GPU runtime libraries,
package indexes, and unknown or newly disclosed vulnerabilities remain supply
risks. No model substitutions or unbounded/destructive vulnerability probes
were performed.

## Compatibility evidence

- [Python version status](https://devguide.python.org/versions/) and
  [uv's Python support](https://docs.astral.sh/uv/reference/policies/python/)
  support CPython 3.12; actual execution uses 3.12.3 and uv 0.11.28.
- [uv CLI reference](https://docs.astral.sh/uv/reference/cli/) documents frozen
  synchronization and offline operation. A clean core environment was populated
  before a second frozen offline sync, with no model-host access during core
  synchronization. Separate locked MMS installation subsequently passed.
- Exact PyPI metadata below accepts Python 3.12. FastAPI 0.136.3 requires
  Starlette >=0.46.0 without a conflicting upper bound. Real imports, ASGI tests,
  strict typing, package installation, and serving validate the selected pair.
- [PyTorch install guidance](https://docs.pytorch.org/get-started/locally/),
  exact 2.13.0 metadata, and the actual wheel/runtime confirm Linux x86-64
  CUDA 13.0 compatibility. The generic selector can lag release metadata;
  measured installed versions are authoritative for this evidence.
- [NVIDIA CUDA 13 release notes](https://docs.nvidia.com/cuda/archive/13.0.2/cuda-toolkit-release-notes/index.html)
  document the driver family requirement. WSL exposes driver 610.62 and an
  RTX 4070; CUDA availability and both real model runs pass without host changes.
- [Transformers 5.13.1 VITS documentation](https://huggingface.co/docs/transformers/v5.13.1/en/model_doc/vits)
  matches VitsTokenizer/VitsModel. Generation uses the same seed/settings as M6.
  Adapter 1.0.1 now requires safetensors, with no pickle fallback.

## Licenses and exact inventory

Each row links the version-specific primary PyPI metadata actually queried;
its SHA-256 and full response are retained externally. License expressions,
classifiers, and installed upstream license files were inspected. General
BSD labels below retain the publisher's metadata wording; they do not replace
full upstream notices. Dependencies are installed externally, not copied into
our wheel or sdist, and are not relicensed by Apache-2.0.

Some NVIDIA metadata omits a license expression. Installed License.txt files
supply the CUDA SDK/EULA, cuDNN SDK, and NCCL BSD terms. The CUDA toolkit
metapackage itself declares no license and carries no license file; no project
redistribution permission is inferred. Its selected binary components remain
subject to NVIDIA terms for this scoped local installation. See the
[NVIDIA EULA](https://docs.nvidia.com/cuda/eula/index.html). NumPy, SciPy,
PyTorch, and binary runtimes carry bundled-component notices as well as their
project licenses; no blanket permissive-license claim is made for the stack.

| Package | Exact version | Publisher license metadata or inspected notice |
|---|---|---|
| [annotated-doc](https://pypi.org/pypi/annotated-doc/0.0.4/json) | 0.0.4 | MIT |
| [annotated-types](https://pypi.org/pypi/annotated-types/0.7.0/json) | 0.7.0 | MIT License |
| [anyio](https://pypi.org/pypi/anyio/4.14.2/json) | 4.14.2 | MIT |
| [ast-serialize](https://pypi.org/pypi/ast-serialize/0.6.0/json) | 0.6.0 | MIT |
| [certifi](https://pypi.org/pypi/certifi/2026.6.17/json) | 2026.6.17 | Mozilla Public License 2.0 (MPL 2.0) |
| [cfgv](https://pypi.org/pypi/cfgv/3.5.0/json) | 3.5.0 | MIT |
| [click](https://pypi.org/pypi/click/8.4.2/json) | 8.4.2 | BSD-3-Clause |
| [colorama](https://pypi.org/pypi/colorama/0.4.6/json) | 0.4.6 | BSD License |
| [coverage](https://pypi.org/pypi/coverage/7.15.1/json) | 7.15.1 | Apache-2.0 |
| [cuda-bindings](https://pypi.org/pypi/cuda-bindings/13.3.1/json) | 13.3.1 | LicenseRef-NVIDIA-SOFTWARE-LICENSE |
| [cuda-pathfinder](https://pypi.org/pypi/cuda-pathfinder/1.5.6/json) | 1.5.6 | Apache-2.0 |
| [cuda-toolkit](https://pypi.org/pypi/cuda-toolkit/13.0.3.0/json) | 13.0.3.0 | Undeclared metapackage; external only, component NVIDIA terms |
| [distlib](https://pypi.org/pypi/distlib/0.4.3/json) | 0.4.3 | Python Software Foundation License |
| [fastapi](https://pypi.org/pypi/fastapi/0.136.3/json) | 0.136.3 | MIT |
| [filelock](https://pypi.org/pypi/filelock/3.29.7/json) | 3.29.7 | MIT |
| [fsspec](https://pypi.org/pypi/fsspec/2026.6.0/json) | 2026.6.0 | BSD-3-Clause |
| [h11](https://pypi.org/pypi/h11/0.16.0/json) | 0.16.0 | MIT License |
| [hatchling](https://pypi.org/pypi/hatchling/1.29.0/json) | 1.29.0 | MIT (upstream LICENSE.txt at hatchling-v1.29.0) |
| [hf-xet](https://pypi.org/pypi/hf-xet/1.5.1/json) | 1.5.1 | Apache-2.0 |
| [httpcore](https://pypi.org/pypi/httpcore/1.0.9/json) | 1.0.9 | BSD-3-Clause |
| [httpx](https://pypi.org/pypi/httpx/0.28.1/json) | 0.28.1 | BSD License |
| [huggingface-hub](https://pypi.org/pypi/huggingface-hub/1.23.0/json) | 1.23.0 | Apache Software License |
| [identify](https://pypi.org/pypi/identify/2.6.19/json) | 2.6.19 | MIT |
| [idna](https://pypi.org/pypi/idna/3.18/json) | 3.18 | BSD-3-Clause |
| [iniconfig](https://pypi.org/pypi/iniconfig/2.3.0/json) | 2.3.0 | MIT |
| [jinja2](https://pypi.org/pypi/jinja2/3.1.6/json) | 3.1.6 | BSD License |
| [librt](https://pypi.org/pypi/librt/0.13.0/json) | 0.13.0 | MIT |
| [markdown-it-py](https://pypi.org/pypi/markdown-it-py/4.2.0/json) | 4.2.0 | MIT License |
| [markupsafe](https://pypi.org/pypi/markupsafe/3.0.3/json) | 3.0.3 | BSD-3-Clause |
| [mdurl](https://pypi.org/pypi/mdurl/0.1.2/json) | 0.1.2 | MIT License |
| [mpmath](https://pypi.org/pypi/mpmath/1.3.0/json) | 1.3.0 | BSD License |
| [mypy](https://pypi.org/pypi/mypy/2.3.0/json) | 2.3.0 | MIT |
| [mypy-extensions](https://pypi.org/pypi/mypy-extensions/1.1.0/json) | 1.1.0 | MIT (installed LICENSE) |
| [networkx](https://pypi.org/pypi/networkx/3.6.1/json) | 3.6.1 | BSD-3-Clause |
| [nodeenv](https://pypi.org/pypi/nodeenv/1.10.0/json) | 1.10.0 | BSD License |
| [numpy](https://pypi.org/pypi/numpy/2.5.1/json) | 2.5.1 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| [nvidia-cublas](https://pypi.org/pypi/nvidia-cublas/13.1.1.3/json) | 13.1.1.3 | LicenseRef-NVIDIA-Proprietary |
| [nvidia-cuda-cupti](https://pypi.org/pypi/nvidia-cuda-cupti/13.0.85/json) | 13.0.85 | Other/Proprietary License |
| [nvidia-cuda-nvrtc](https://pypi.org/pypi/nvidia-cuda-nvrtc/13.0.88/json) | 13.0.88 | Other/Proprietary License |
| [nvidia-cuda-runtime](https://pypi.org/pypi/nvidia-cuda-runtime/13.0.96/json) | 13.0.96 | NVIDIA CUDA SDK EULA (installed License.txt) |
| [nvidia-cudnn-cu13](https://pypi.org/pypi/nvidia-cudnn-cu13/9.20.0.48/json) | 9.20.0.48 | NVIDIA SDK agreement (installed License.txt) |
| [nvidia-cufft](https://pypi.org/pypi/nvidia-cufft/12.0.0.61/json) | 12.0.0.61 | Other/Proprietary License |
| [nvidia-cufile](https://pypi.org/pypi/nvidia-cufile/1.15.1.6/json) | 1.15.1.6 | Other/Proprietary License |
| [nvidia-curand](https://pypi.org/pypi/nvidia-curand/10.4.0.35/json) | 10.4.0.35 | Other/Proprietary License |
| [nvidia-cusolver](https://pypi.org/pypi/nvidia-cusolver/12.0.4.66/json) | 12.0.4.66 | Other/Proprietary License |
| [nvidia-cusparse](https://pypi.org/pypi/nvidia-cusparse/12.6.3.3/json) | 12.6.3.3 | Other/Proprietary License |
| [nvidia-cusparselt-cu13](https://pypi.org/pypi/nvidia-cusparselt-cu13/0.8.1/json) | 0.8.1 | NVIDIA Proprietary Software |
| [nvidia-nccl-cu13](https://pypi.org/pypi/nvidia-nccl-cu13/2.29.7/json) | 2.29.7 | BSD-3-Clause (installed License.txt) |
| [nvidia-nvjitlink](https://pypi.org/pypi/nvidia-nvjitlink/13.0.88/json) | 13.0.88 | Other/Proprietary License |
| [nvidia-nvshmem-cu13](https://pypi.org/pypi/nvidia-nvshmem-cu13/3.4.5/json) | 3.4.5 | NVIDIA CUDA SDK EULA (installed License.txt) |
| [nvidia-nvtx](https://pypi.org/pypi/nvidia-nvtx/13.0.85/json) | 13.0.85 | Other/Proprietary License |
| [packaging](https://pypi.org/pypi/packaging/26.2/json) | 26.2 | Apache-2.0 OR BSD-2-Clause |
| [pathspec](https://pypi.org/pypi/pathspec/1.1.1/json) | 1.1.1 | Mozilla Public License 2.0 (MPL 2.0) |
| [platformdirs](https://pypi.org/pypi/platformdirs/4.10.0/json) | 4.10.0 | MIT |
| [pluggy](https://pypi.org/pypi/pluggy/1.6.0/json) | 1.6.0 | MIT License |
| [pre-commit](https://pypi.org/pypi/pre-commit/4.6.0/json) | 4.6.0 | MIT |
| [pydantic](https://pypi.org/pypi/pydantic/2.13.4/json) | 2.13.4 | MIT |
| [pydantic-core](https://pypi.org/pypi/pydantic-core/2.46.4/json) | 2.46.4 | MIT |
| [pygments](https://pypi.org/pypi/pygments/2.20.0/json) | 2.20.0 | BSD-2-Clause |
| [pytest](https://pypi.org/pypi/pytest/9.1.1/json) | 9.1.1 | MIT |
| [pytest-cov](https://pypi.org/pypi/pytest-cov/7.1.0/json) | 7.1.0 | MIT |
| [python-discovery](https://pypi.org/pypi/python-discovery/1.4.4/json) | 1.4.4 | MIT License |
| [pyyaml](https://pypi.org/pypi/pyyaml/6.0.3/json) | 6.0.3 | MIT License |
| [regex](https://pypi.org/pypi/regex/2026.7.10/json) | 2026.7.10 | Apache-2.0 AND CNRI-Python |
| [rich](https://pypi.org/pypi/rich/15.0.0/json) | 15.0.0 | MIT License |
| [ruff](https://pypi.org/pypi/ruff/0.15.21/json) | 0.15.21 | MIT |
| [safetensors](https://pypi.org/pypi/safetensors/0.8.0/json) | 0.8.0 | Apache Software License |
| [scipy](https://pypi.org/pypi/scipy/1.18.0/json) | 1.18.0 | BSD License |
| [setuptools](https://pypi.org/pypi/setuptools/83.0.0/json) | 83.0.0 | MIT |
| [shellingham](https://pypi.org/pypi/shellingham/1.5.4/json) | 1.5.4 | ISC License (ISCL) |
| [starlette](https://pypi.org/pypi/starlette/1.3.1/json) | 1.3.1 | BSD-3-Clause |
| [sympy](https://pypi.org/pypi/sympy/1.14.0/json) | 1.14.0 | BSD License |
| [tokenizers](https://pypi.org/pypi/tokenizers/0.22.2/json) | 0.22.2 | Apache Software License |
| [torch](https://pypi.org/pypi/torch/2.13.0/json) | 2.13.0 | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT |
| [tqdm](https://pypi.org/pypi/tqdm/4.68.4/json) | 4.68.4 | MPL-2.0 AND MIT |
| [transformers](https://pypi.org/pypi/transformers/5.13.1/json) | 5.13.1 | Apache 2.0 License |
| [triton](https://pypi.org/pypi/triton/3.7.1/json) | 3.7.1 | MIT License |
| [typer](https://pypi.org/pypi/typer/0.26.8/json) | 0.26.8 | MIT |
| [types-pyyaml](https://pypi.org/pypi/types-pyyaml/6.0.12.20260518/json) | 6.0.12.20260518 | Apache-2.0 |
| [typing-extensions](https://pypi.org/pypi/typing-extensions/4.16.0/json) | 4.16.0 | PSF-2.0 |
| [typing-inspection](https://pypi.org/pypi/typing-inspection/0.4.2/json) | 0.4.2 | MIT |
| [uv](https://pypi.org/pypi/uv/0.11.28/json) | 0.11.28 | MIT OR Apache-2.0 |
| [uvicorn](https://pypi.org/pypi/uvicorn/0.46.0/json) | 0.46.0 | BSD-3-Clause |
| [virtualenv](https://pypi.org/pypi/virtualenv/21.6.1/json) | 21.6.1 | MIT |

Hatchling's [versioned MIT license](https://github.com/pypa/hatch/blob/hatchling-v1.29.0/LICENSE.txt)
was checked separately. Apache's [standard license text](https://www.apache.org/licenses/LICENSE-2.0.txt)
was copied byte for byte into LICENSE; NOTICE and THIRD_PARTY_NOTICES.md define
covered original material and preserve external rights. Wheel and sdist include
all three, with `License-Expression: Apache-2.0` and license-file metadata.

## CI, hooks, and upstream drift

CI has read-only repository permissions, no deployment/publication secret,
Ubuntu 24.04, Python 3.12, and pinned uv 0.11.28. The existing checkout commit
[df4cb1c](https://github.com/actions/checkout/commit/df4cb1c069e1874edd31b4311f1884172cec0e10)
is v6.0.3. setup-uv's previous full object ID
`94527f2e458b27549849d47d273a16bec83a01e9` was an annotated tag object,
not a commit. `git ls-remote` peeled it to the existing v7.6.0 commit
[37802adc](https://github.com/astral-sh/setup-uv/commit/37802adc94f370d6bfd71619e3f0bf239e1f3b78).
M7 uses that commit directly; it does not change the selected action's code.
The pre-commit-hooks v6.0.0 tag was similarly replaced with its existing
commit `3e8a8703264a2f4a69428a0aa4dcb512790b2c8c`.

[Checkout advisories](https://github.com/actions/checkout/security/advisories)
and [setup-uv advisories](https://github.com/astral-sh/setup-uv/security/advisories)
listed no published advisories at access. CI/action and hook source licenses
remain third-party notices, not project-owned code. The local full pre-commit
suite passes; a hosted post-push CI outcome is separate from this local audit.
Hosted runners, action downloader metadata, and separately built hook
transitives are not made fully reproducible by the project Python lock.

Remaining upstream/license/availability ambiguity is explicitly proposed for
REL-SUPPLY-001 acceptance within this code-only public distribution and trusted
local runtime scope. Review on 2026-12-09 or sooner for a material advisory,
license change, missing checkpoint, or hash mismatch. No newly disclosed
unpatched dependency is silently retained to close a release blocker.
