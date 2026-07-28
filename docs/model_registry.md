# Audited model registry

`configs/models/registry.yaml` is the active source of truth for public
checkpoint identity and workbench-use policy. Registry commands validate
metadata only; they do not contact a model host or download weights.

The registry is loaded through `tts_workbench.models` and is unchanged by the
0.2 namespace migration and M3/M4 execution work. Its schema version remains 1.

## Required fields and policy

Every entry records:

- a stable workbench model ID, provider, repository, and immutable 40-character
  revision;
- the provider-documented ISO 639-3 language tag and architecture;
- the audited weight license and primary-source provenance;
- the only currently approved use: `local_noncommercial_inference`;
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
synthetic smoke fixture. The Vietnamese entry still requires an external,
independently audited public prompt; M3 adds no Vietnamese prompt content.

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
smoke prompt. The Vietnamese entry still requires an artifact-root-relative,
independently audited public prompt file. M4 validation uses only the synthetic
test registry and does not execute either real entry.

## M5 service routing

`GET /v1/models` lists only registry entries and copies immutable identity,
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
  external public prompt with independent license/provenance review; the
  workbench invents no Vietnamese prompt.

Both are CC BY-NC 4.0, scoped to local non-commercial inference, and have no
linguistic-quality finding from this project. Their inclusion does not provide
evidence about White Hmong.

## Commands

```text
tts-workbench-models validate
tts-workbench-models list
tts-workbench-models list --json
tts-workbench-serve openapi
```

An alternate local registry may be checked with `--registry PATH`. Validation
is fail-closed and performs no weight download.

Before adding a model, update `docs/license_matrix.md` from primary sources,
pin an immutable revision, record prompt provenance, and add policy tests.
