# Changelog

## 1.0.0 — M7 release candidate, 2026-09-10

Final disposition is recorded in `docs/m7_owner_approval.json`; this version
number alone is not owner approval or package publication.

- Apply the owner-approved Apache-2.0 license to covered original code, with
  explicit third-party/model/output exclusions and package license notices.
- Remove the deprecated `HMONG_TTS_DATA_ROOT` bridge and its warning type.
  Configure `TTS_WORKBENCH_ARTIFACT_ROOT`; see `docs/m7_migration.md`.
  The major version marks this breaking stable-interface transition from
  0.5.0. Existing M3–M6 request/report schemas and QC thresholds remain intact.
- Require safetensors for MMS weights; no pickle fallback. Adapter version
  advances to 1.0.1 to identify this loading behavior.
- Sanitize invalid smoke requests before constructing an adapter so validation
  errors cannot echo raw input through a traceback.
- Remediate audited Starlette, PyTorch, and setuptools advisories; remove unused
  vulnerable Accelerate. Only required CUDA toolkit and Triton transitives
  change. Full version delta and rationale: `docs/m7_dependency_audit.md`.
- Pin existing CI/hook selections to commit objects: peel setup-uv's annotated
  v7 tag and replace the pre-commit-hooks v6.0.0 tag with its existing commit.
- Add candidate identity, current provenance/advisory evidence, reproduction,
  migration, privacy/retention, risk dispositions, and owner decision records.

Historical 0.5.0/M6 behavior remains recorded in its original validation report.
