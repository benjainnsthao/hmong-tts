# Architecture boundary — Phase 0

One shared package will own normalization for training, evaluation, CLI, API,
and demo use. Language behavior is currently blocked pending native validation;
no alternative implementation is allowed in an app or service.

```text
external private root                 public repository
raw masters -> QC -> processed WAV    typed configs + schemas
      |             |                 boundary/privacy checks
      +-> checksums + manifests <---- reproducible scripts
                    |
                    +-> MMS/VITS training -> private checkpoints
                                                   |
public input -> shared validated normalizer -> tokenizer -> inference -> private WAV
```

The MVP is one speaker and 16 kHz MMS/VITS output. `spk01` alone provides
training audio. `reviewer02` remains outside training and leads evaluation. The
sealed test set is isolated from all selection/tuning decisions.
