# Workbench threat model

## Protected assets

Checkpoint provenance, license metadata, generated audio, model caches, prompt
sources, benchmark integrity, credentials, and the accuracy of public
capability claims.

## Principal threats

- mutable or substituted model revisions;
- weights used beyond audited license scope or accidentally redistributed;
- generated audio, weights, caches, or credentials entering Git;
- unlicensed or untraceable prompt material;
- prompt or client metadata leaking through local service logs;
- resource exhaustion from unbounded model loading or inference requests;
- runtime metrics being misrepresented as pronunciation or language quality;
- public claims of White Hmong support without community validation **[NV]**.

## Current controls

Strict registry validation, immutable revisions, primary-source provenance,
non-commercial-use and no-redistribution policy fields, an external artifact
root, privacy/artifact scanning, offline synthetic tests, and
`language_quality_status: not_evaluated`.

M7 re-audits real registry-pinned execution and the existing loopback-only
service. See `service_threat_model.md` for its lifecycle, finite FIFO,
pre-execution deadlines, logging controls, trusted-local-client assumptions,
and exhaustion limits. Current dependency corrections and safetensors-only
loading reduce known supply risks; they do not eliminate native-code or
upstream risk. Public binding, deployment, or additional checkpoints require
separate authorization and review. Final acceptance is in
`m7_owner_approval.json`, with per-risk evidence in `release_risk_register.md`.
