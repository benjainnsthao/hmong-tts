# Audited model registry

`configs/models/registry.yaml` is the active source of truth for public
checkpoint identity and workbench-use policy. Registry commands validate
metadata only; they do not contact a model host or download weights.

The registry is loaded through `tts_workbench.models` and is unchanged by the
0.2 namespace migration. Its schema version remains 1.

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
```

An alternate local registry may be checked with `--registry PATH`. Validation
is fail-closed and performs no weight download.

Before adding a model, update `docs/license_matrix.md` from primary sources,
pin an immutable revision, record prompt provenance, and add policy tests.
