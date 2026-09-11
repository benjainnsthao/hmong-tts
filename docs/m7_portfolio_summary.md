# M7 engineering summary

The long-term purpose is useful speech technology for the Hmong community.
The current work delivers a local reproducible engineering workbench with
English and Vietnamese MMS demonstrations. Recruiters are a secondary
audience for the reproducibility, security, and release-evidence methods.
There is no Hmong capability or linguistic/perceptual-quality claim.

Version 1.0.0 pairs a strict immutable model registry with lazy runtime imports,
one-model adapter ownership, atomic WAV/manifest transactions, structural QC,
bounded benchmarks, and a one-worker loopback service. M7 removes the legacy
artifact-root bridge, applies the owner-approved Apache-2.0 license to original
code, requires safetensors, and fixes the exact dependency advisories found
in the release audit. External model/data/output rights remain separate.

Both registered checkpoints run on the RTX 4070 with requested/resolved
CUDA/float32. Clean CPU-only core operation is established separately; bounded
CPU-model diagnostics also succeed. Paired CUDA runs produce matching hashes
within the same environment; CPU hashes differ, and no cross-device identity
is promised. Eight real WAV/manifest pairs pass structural and identity checks.
Both QC reports are `qc_passing` under unchanged M4 thresholds and retain
`engineering_sanity_check` labels.

| Measured CUDA benchmark | English fixture | Vietnamese legal-document prompt |
|---|---:|---:|
| Cold load, seconds | 4.3307 | 4.3117 |
| Audio duration, seconds | 2.416 | 11.600 |
| Median warm synthesis, seconds | 0.0402 | 0.1451 |
| Nearest-rank p95 warm synthesis, seconds | 0.0411 | 0.1582 |
| Median real-time factor | 0.01662 | 0.01251 |
| Measured successes / failures | 3 / 0 | 3 / 0 |

One warmup is excluded for each model. Different prompts and three samples
cannot support language rankings, broad performance guarantees, or deployment
capacity claims. Observable memory, raw timings, exact revisions, dependency
versions, and commands are recorded in the [M7 validation report](../reports/validation/m7_release_validation.md)
and [reproduction procedure](m7_reproduction.md).

The real service handles both models, safely rejects an unregistered model
without artifact creation or prompt echo, then shuts down with an unloaded
adapter and closed listener. Its finite FIFO is not a complete resource quota:
loopback is not authentication, body parsing and output duration are not
hard-bounded, and native active calls are not safely preemptible. These limits
are explicit residual risks for a trusted local development tool.

The expanded history audit also disclosed an existing personal-provider email
in prior commit metadata. Its raw value is withheld; a public release requires
explicit owner disposition, and the proposed M7 commit uses a verified GitHub
no-reply identity. Existing history is not rewritten.

The release evidence distinguishes prior owner-approved code licensing,
measured technical results, proposed risk dispositions, and final human
approval. The candidate file manifest binds reviewed contents before the
authorized commit sequence. The first M7 commit was approved and pushed, but
clean-worktree packaging found a private-path pointer in its external sdist.
The correction explicitly excludes Git metadata and adds real archive regression
tests; a changed candidate requires new review and exact-commit validation.
The failed archive was not published. The actual current outcome is in
[m7_owner_approval.json](m7_owner_approval.json); only an approved `release`
with all gates passed completes M7 as a public-release gate.

Weights, caches, raw prompts/source scans, audio, environments, and full raw
reports stay external. M1–M6 validation reports and NV-001 through NV-008
remain unchanged. No community-language, recording, training, application,
or public-deployment work is authorized by this milestone.
