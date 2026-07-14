# Voice and data misuse threat model

## Protected assets

Speaker identity, consent choices, raw and processed voice, transcripts,
evaluation responses, checkpoints, credentials, and the ability to synthesize
the participant’s voice.

## Principal threats

- accidental Git, tracker, log, or cloud exposure;
- unauthorized insiders or compromised accounts accessing private storage;
- model or sample distribution beyond consent or upstream licenses;
- voice impersonation, fraud, deceptive media/politics, harassment, or consent bypass;
- prompt abuse, denial of service, or extraction through a public demo;
- inability to recall third-party downloads after withdrawal;
- misleading claims about language accuracy from unvalidated automation.

## Phase 0 controls

External encrypted data root, separate identity/consent storage, pseudonymous
IDs, scanner/pre-commit/CI gates, local/offline tracking, audited pinned model
revisions, no public deployment, no weights, no real test data, and explicit
native-validation blocks.

## Required pre-demo controls

Prominent “synthetic voice, used with consent” notice; model-card prohibited
uses; input/rate limits; one worker and GPU queue; request timeout; no
unnecessary prompt or IP logging; abuse reporting; kill switch; short documented
retention; WAV provenance metadata; and a demo-first/no-download release order.

No blocklist, watermark, or technical control may be represented as eliminating
misuse risk.
