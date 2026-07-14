# Speaker roles and evaluation separation

## MVP roles

- `spk01` is the primary speaker and the only voice whose audio may enter MVP
  training, development, or model-adaptation data.
- `reviewer02` is the second speaker. This person reviews transcripts and leads
  the independent blind listening/transcription evaluation.
- The primary speaker may diagnose errors, but cannot be the sole evaluator of
  their model.
- Final prompts should remain hidden from `reviewer02` until the applicable
  transcription/listening task when feasible.
- The sealed test set is never used for checkpoint selection, configuration
  tuning, normalization-rule tuning, or prompt repair.

Manifests and configs must use pseudonymous IDs only. The identity mapping and
completed evaluator/participant records stay outside the repository.

## No silent role expansion

Adding `reviewer02` or anyone else as a training speaker is outside MVP scope.
It requires all five gates from the authoritative plan: the single-speaker MVP
already passes, a product need exists, separate consent covers training and
distribution, 1–2 clean hours are available, and other independent evaluators
can replace the lost speaker-independent evaluator.
