# Audited model registry

`configs/models/registry.yaml` is the active source of truth for public
checkpoint identity and workbench-use policy. Registry commands validate
metadata only; they do not contact a model host or download weights.

The registry is loaded through `tts_workbench.models`. The committed file uses
schema version 2 (2026-09-29); schema 1 files remain valid unchanged.

## Schema 2: restricted research entries

Schema 2 exists only to express owner-restricted local research. A schema 1 file
cannot contain any of these fields, so older registries keep their meaning.

- `architecture: orpheus_llama_snac` alongside `vits`.
- `approved_use: local_noncommercial_research_inference`, which requires
  `use_restrictions`, and only that use may carry them:
  `scope: local_noncommercial_research_only`,
  `output_policy: outputs_external_not_shared`, `public_use: not_cleared`, a
  repository-relative `owner_decision_reference`, at least one upstream license
  marked `owner_accepted_for_local_research`, and at least one open risk.
- `components`: required for Orpheus (exactly one `audio_codec`) and forbidden
  elsewhere. Each component pins its repository/revision, audited license, the
  source file SHA-256, the conversion method and the SHA-256 of the
  `safetensors` file actually loaded. An unconverted component must load its
  source digest.

`language_quality_status` is still only `not_evaluated`. Manifests and benchmark
reports record `registry_schema_version` 1 or 2 and copy the approved use.
The local service filters its registry to unrestricted VITS entries, so
`/v1/models`, the dashboard and `tts-workbench-mms-smoke` never list or route
the research entry.

### `orpheus-hmong-3b`

`Pakorn2112/Orpheus-TTS-hmong-3b@464d34449a778b1a6d9506bc10bd4e00f752c5c8`,
documented as Hmong Daw (`mww`), card label Apache-2.0 research/educational.
Owner decisions D1–D3 ([record](hmong_orpheus_owner_decision.json)) permit local
non-commercial research only; outputs stay outside Git and are not shared.
The SNAC 24 kHz codec (`hubertsiuzdak/snac_24khz@d73ad176…`, MIT) was converted
once from `pytorch_model.bin` (`4b8164cc…bff40`) with `weights_only=True` to
safetensors (`2db6ee7e…d138c`). `OrpheusAdapter` verifies that digest before
importing any ML package and loads it from the content-addressed
`$TTS_WORKBENCH_ARTIFACT_ROOT/converted-weights/sha256/` path. The prompt
reference `external:white-hmong-draft-v2-development` means development cases
only; the held-out reserve is never a runtime input.

## Required fields and policy

Every entry records:

- a stable workbench model ID, provider, repository, and immutable 40-character
  revision;
- the provider-documented ISO 639-3 language tag and architecture;
- the audited weight license and primary-source provenance;
- an approved use: `local_noncommercial_inference`, or (schema 2 only)
  `local_noncommercial_research_inference` with recorded restrictions;
- `weights_not_redistributed`;
- a prompt-set reference; and
- `language_quality_status: not_evaluated`.

Unknown license placeholders, mutable revisions, duplicate model IDs, duplicate
repository/revision pairs, unapproved uses, extra capability fields, and
positive language-quality claims fail validation.

## M3 inference boundary

`InferenceExecutor` looks up a request's model ID in this registry before any
adapter load. `MmsVitsAdapter` performs its own registry lookup and supplies
only the registered repository and immutable revision to the optional backend.
Repository aliases or caller-supplied revisions are not accepted.

A request's `prompt_set_reference` must exactly match its registry entry.
The built-in English reference identifies only the existing project-authored
synthetic smoke fixture. The Vietnamese entry identifies the externally
retained, independently audited 2013 Constitution Article 1 prompt; no prompt
content is stored in the registry or repository.

Successful run manifests copy the eligible entry's model ID, provider,
repository, revision, architecture, documented language tag, license/use/
redistribution fields, prompt reference, and
`language_quality_status: not_evaluated`. This is provenance, not evidence of
pronunciation or linguistic quality.

## M4 benchmark routing

`BenchmarkRunner` accepts one explicit model ID and resolves it through the same
registry before adapter loading. Prompt provenance must exactly match the
entry. Benchmark reports copy the same immutable model/policy identity used by
M3 manifests and retain only a SHA-256 prompt hash.

`tts-workbench-benchmark run` fails closed without
`--acknowledge-model-access`. The English entry may use its existing synthetic
smoke prompt. The Vietnamese entry requires the matching artifact-root-relative
audited prompt file. M4 validation used only the synthetic test registry; M6
separately executed both real entries after the provenance and model-access
gates passed.

## M5 service routing

`GET /v1/models` lists only unrestricted VITS registry entries and copies immutable identity,
provenance, license/use/redistribution policy, prompt-set reference, and
`language_quality_status: not_evaluated`. It performs no checkpoint or model
host access.

`POST /v1/synthesize` resolves the caller's model ID before coordinator
admission or adapter load. The service supplies the registered prompt
reference to the internal M3 request; callers cannot override prompt
provenance, repository, revision, provider settings, or output location. An
unknown model returns a sanitized 404 before inference.

## Registered models

- `mms-eng`: public English MMS/VITS checkpoint. Its built-in input is a
  project-authored synthetic smoke fixture, not a language-quality evaluation.
- `mms-vie`: public Vietnamese MMS/VITS checkpoint. Inference requires an
  external public prompt matching
  `external:vietnam-constitution-2013-article-1`. Its source/license audit and
  SHA-256 are recorded without text in `docs/m6_reproduction.md`; the workbench
  invents no Vietnamese prompt.

Both are CC BY-NC 4.0, scoped to local non-commercial inference, and have no
linguistic-quality finding from this project. Their inclusion does not provide
evidence about White Hmong.
- `orpheus-hmong-3b`: restricted research entry described above. It is not
  served locally, and its inclusion is not evidence of White Hmong quality.

## Commands

```text
tts-workbench-models validate
tts-workbench-models list
tts-workbench-models list --json
tts-workbench-serve openapi
```

An alternate local registry may be checked with `--registry PATH`. Validation
is fail-closed and performs no weight download.

Both model provenance records were re-audited on 2026-09-09 at their exact
Hugging Face revisions. M6 cache snapshot identities matched the registered
40-character revisions; callers still cannot provide alternate repositories or
mutable revisions. Both checkpoint pages listed CC BY-NC 4.0 and safetensors
weights. M6 does not change use, redistribution, or quality policy.

Before adding a model, update `docs/license_matrix.md` from primary sources,
pin an immutable revision, record prompt provenance, and add policy tests.

## M7 source refresh

Both existing revisions were re-audited on 2026-09-10. Exact Hub revision
metadata remains public and ungated; cached safetensors SHA-256 values match
upstream LFS identity. Only `audited_on` changes in the registry. No model is
added or substituted, and local non-commercial use, no weight redistribution,
and `language_quality_status: not_evaluated` remain mandatory. Prompt and
current legal-basis evidence are in `license_matrix.md` and
`m7_reproduction.md`; dependency advisories are in `m7_dependency_audit.md`.
