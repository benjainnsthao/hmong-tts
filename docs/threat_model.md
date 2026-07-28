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
- prompt or client metadata leaking through logs in a future service;
- resource exhaustion from unbounded model loading or inference requests;
- runtime metrics being misrepresented as pronunciation or language quality;
- public claims of White Hmong support without community validation **[NV]**.

## Current controls

Strict registry validation, immutable revisions, primary-source provenance,
non-commercial-use and no-redistribution policy fields, an external artifact
root, privacy/artifact scanning, offline synthetic tests, and
`language_quality_status: not_evaluated`.

The current milestone downloads no weights and exposes no service. Future
inference and deployment milestones require separate model-lifecycle,
concurrency, timeout, logging, and abuse controls.
