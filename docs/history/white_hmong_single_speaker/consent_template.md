# Participant consent choices — blank project template

> Project documentation only; not legal advice. Adaptation or execution may
> require review by a qualified lawyer in the relevant jurisdiction. Completed
> forms, signatures, names, contact details, and identity-to-speaker-ID mappings
> must remain encrypted outside the repository.

Project: White Hmong single-speaker TTS research MVP
Document version: 0.1 (2026-07-14)
Pseudonymous participant ID: ____________________
Private consent-record ID: ____________________

## Purpose and role

The project will record one primary speaker to study whether a small,
single-speaker text-to-speech model can synthesize the documented White Hmong
variety. A separate evaluator may review transcripts and synthetic speech. The
primary speaker is the only training voice for this MVP.

Participation is voluntary. Each choice below is independent unless a later use
technically requires an earlier one. A “no” does not silently become a “yes” for
a related use.

## Independent choices

Initial exactly one answer for each row.

| Use | Yes | No | Notes/scope |
|---|---|---|---|
| Participate in recording sessions | ____ | ____ | |
| Use accepted recordings and transcripts to train this TTS model | ____ | ____ | |
| Use the resulting synthetic voice in a locally run research evaluation | ____ | ____ | |
| Host a non-commercial public demo that generates synthetic audio | ____ | ____ | |
| Publicly share specifically selected real recording samples | ____ | ____ | Each sample requires separate approval before release. |
| Publicly share specifically selected synthetic samples | ____ | ____ | Each sample requires separate approval before release. |
| Distribute downloadable model weights/checkpoints | ____ | ____ | This is higher risk than a hosted demo. |
| Permit commercial use of recordings, models, or outputs | ____ | ____ | A “yes” does not override a non-commercial base-model license. |
| Use the voice/model in future translation applications | ____ | ____ | |
| Use the voice/model in future education applications | ____ | ____ | |
| Retain private recordings and derivatives for the period below | ____ | ____ | |

No public release is authorized unless its corresponding row is “yes.” The
project will launch a controlled demo before considering downloadable weights.

## Credit and anonymity

Choose one:

- [ ] Use only the pseudonymous speaker ID; do not publicly credit me.
- [ ] Credit me using a separate display name recorded only in the private
  consent record.
- [ ] Do not publicly release any artifact associated with my voice.

The public repository must never contain the participant’s legal name, contact
details, signature, or identity mapping.

## Retention and access

Approved retention period or end date: ____________________
Who may access raw recordings: ____________________
Private contact/withdrawal channel (stored only in the completed record): ____________________

Private material will be encrypted and access-limited. Consent records are kept
separately from audio. The project will retain only the minimum data needed for
approved uses and will review consent again before a public release.

## Withdrawal

Before public release, a withdrawal request will cause covered private
recordings, processed derivatives, and unpublished checkpoints to be deleted,
subject to any explicitly documented legal retention obligation.

After public release, the project will remove hosted artifacts it controls,
disable the demo when applicable, and mark releases withdrawn. Copies of audio
or model weights already downloaded by third parties cannot reliably be found,
recalled, or deleted. This asymmetry is why downloadable weights require a
separate choice and why a controlled demo comes first.

Withdrawal request received on: ____________________
Withdrawal scope/outcome (private record): ____________________

## Foreseeable misuse and safeguards

Synthetic voice technology can be misused for impersonation, fraud, deceptive
political or media content, harassment, or bypassing consent. Planned safeguards
include a prominent synthetic/consented notice, input and rate limits, a single
inference worker, short/minimal logs, abuse reporting, a kill switch, and model
documentation prohibiting those uses. These controls reduce risk but cannot
guarantee prevention, especially if weights or audio are downloaded.

## Confirmation

The participant has had an opportunity to ask questions, understands the
choices above, understands the limits of withdrawal after publication, and can
receive a copy of the completed record.

Participant signature (private completed copy only): ____________________
Date: ____________________
Project representative signature (private completed copy only): ____________________
Date: ____________________
