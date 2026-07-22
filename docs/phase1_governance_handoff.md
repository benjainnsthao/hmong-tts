# Phase 1 governance and recording-readiness handoff

Purpose: move from the completed Phase 0 environment gate into consent, native
validation, and recording readiness without beginning recording or training
prematurely.

Phase 0 is complete. Phase 1 is not started until the project owner explicitly
authorizes Step 1 below. That authorization starts governance/readiness work
only; it does not authorize a dry run, production recording, real-data
processing, model training, or public release.

## Responsibility labels

- **Terminal:** repository or private-root work Codex can perform after explicit
  authorization.
- **Outside:** human, legal, physical, or private action that must not be
  delegated to or exposed in the terminal.
- **Both:** an outside decision or activity followed by terminal implementation
  or validation.

## Hard boundaries

- Completed consent records, signatures, legal names, contact details, identity
  mappings, private prompts/ratings, and real audio remain outside Git.
- Do not paste private participant information or completed consent content into
  a prompt, issue, log, commit, or hosted service.
- The terminal may prepare blank templates and pseudonymous engineering records;
  it cannot sign consent, give legal advice, decide White Hmong language rules,
  assess participant comfort, or approve a recording setup.
- No recording begins until Gates A through D in
  `docs/recording_readiness_checklist.md` pass in a dated private record.
- No production recording begins until the 5–10-minute dry run passes Gate E.
- No training begins until separately authorized after consented pilot data and
  its required reviews exist.
- No public release occurs until the relevant consent choices and project/model
  licenses permit it.

## Ordered execution map

| Step | Location | Entry requirement | Work | Exit requirement |
|---|---|---|---|---|
| 1. Governance kickoff | Outside, then Terminal | Phase 0 complete and clean Git checkout | Explicitly authorize governance/readiness preparation; validate the private boundary and create only empty/blank working material | Private scaffold and blank work packet validated; no participant data collected |
| 2. Consent Gate A | Both | Step 1 complete | Adapt/review the consent form privately, discuss every independent choice, assign pseudonymous roles, and sign outside the terminal | Dated private consent record confirms recording and training choices separately |
| 3. Native validation | Both | Both speakers available under pseudonymous roles | Resolve NV-001 through NV-008 from speaker-supplied evidence; terminal records only approved, non-identifying decisions | Native-validation register contains reviewed decisions needed by the applicable readiness gates |
| 4. Privacy/storage Gate B | Both | Approved private storage owner and backup plan | Validate layout and access; arrange encrypted primary/external/off-site storage; rehearse checksums using synthetic files | Dated private Gate B record, successful checksum rehearsal, and privacy scan |
| 5. Prompt Gate C | Both | NV-001 and relevant language decisions approved | Prepare licensed dry-run prompts; native speakers approve naturalness and all uncertain forms | Dated private Gate C record and approved dry-run prompt set outside Git |
| 6. Recording setup Gate D | Outside, with Terminal checks | Gates A through C pass | Configure and physically document the microphone, room, levels, software, naming, fatigue rules, and calibration prompts | Dated private Gate D record; no recording defect is knowingly open |
| 7. Dry run | Both | Gates A through D pass | Record only 5–10 consented minutes outside the terminal; run technical QC and manual review | Every Gate E item passes or has an explicit resolution |
| 8. Pilot | Both | Gate E complete and speaker willing to continue | Record and review 30–45 accepted minutes across at least two sessions | Pilot data, manifests, splits, and reviews pass the project plan’s pilot prerequisites |
| 9. Pilot training/evaluation | Both | Separately authorized consented pilot and frozen evaluation rules | Process data, train identical English/Vietnamese initialization runs, and conduct blind native evaluation | Pilot report supports the next architecture/data decision without overstating quality |

`LICENSE-001` may be resolved in parallel: the owner makes the licensing
decision outside the terminal, and the terminal implements it only after
explicit approval. It must be resolved before public redistribution.

## Step 1 — governance/readiness kickoff

### Step 1 outcome

Step 1 produces only:

- a revalidated clean repository and external private-data boundary;
- the empty directory layout documented in `data/README.md`;
- private blank working copies of the consent template, native-validation
  register, and recording-readiness checklist;
- a redacted gap summary showing which Gates A through D still require outside
  action.

It does not collect participant answers, fill consent choices, store identity
information, author White Hmong prompts, create encryption/recovery keys,
create backups, record audio, process real data, train, or update Phase 1 status.

### Owner checklist before authorizing Step 1 — Outside

- [ ] I intend to begin Phase 1 governance/readiness preparation, but not
  recording or training.
- [ ] I understand that the primary speaker remains `spk01` in engineering
  records and the independent reviewer remains `reviewer02`; real identities
  will be assigned and stored privately without entering the terminal.
- [ ] I have a private way to discuss consent and withdrawal with each
  participant.
- [ ] I will decide whether the consent template needs review by a qualified
  lawyer; the repository template is not legal advice.
- [ ] I approve continued use of the existing access-controlled external root
  for blank Phase 1 working material.
- [ ] I understand that encrypted backup media, off-site storage, recovery-key
  custody, physical recording setup, and signatures are outside actions and are
  not authorized by the Step 1 terminal prompt.

If any box is not true, resolve it outside the terminal before continuing.

### What the terminal is allowed to do in Step 1

After the owner sends the authorization prompt below, the terminal may:

1. Verify clean `main`, expected origin, and the Phase 0 closure commit.
2. Validate the existing `HMONG_TTS_DATA_ROOT` without printing its resolved
   path or inspecting existing private-file content.
3. Create only missing empty directories from this approved list, using mode
   `0700`:

   ```text
   consent/
   identity/
   raw/spk01/
   processed/spk01/
   metadata/private/
   manifests/
   evaluation/private/
   checkpoints/
   cache/models/
   runs/phase1/
   backups/manifests/
   ```

4. Create only these blank private working copies, using mode `0600`, and only
   when the destination does not already exist:

   ```text
   consent/blank-consent-template.md
   runs/phase1/native-validation-working-copy.md
   runs/phase1/recording-readiness-working-copy.md
   ```

5. Run the data-root environment check and repository privacy scan.
6. Return a redacted PASS/gap summary without exposing any private path or
   participant information.

The terminal must stop rather than overwrite, read, rename, delete, change
ownership, or change permissions on a pre-existing private file or directory.

### Copyable Step 1 authorization prompt

Review the owner checklist above, then send the following as a new task:

```text
Execute only Step 1 of docs/phase1_governance_handoff.md: Phase 1
governance/readiness preparation.

This authorization starts Phase 1 governance/readiness preparation only. It
does not authorize consent completion, recording, processing real speaker data,
training, inference, public release, backup creation, encryption changes, or
Phase 2 work.

Read first:

- docs/phase1_governance_handoff.md
- docs/privacy_and_consent.md
- docs/templates/consent_template.md
- docs/native_validation_register.md
- docs/recording_readiness_checklist.md
- data/README.md
- PROJECT_STATUS.md

Repository gate:

- Run git status --porcelain before doing anything and stop unless it is empty.
- Require main, the expected origin, and Phase 0 closure commit
  117d11a6aeec13edf1105e7f4f474f705bc750e7 as an ancestor of HEAD.
- Do not pull, switch branches, stage, commit, push, or modify tracked files.

Private-root authorization:

- Use the existing approved administrator-owned private root. If the variable
  is unset, use $HOME/hmong-tts-private.
- Validate that it exists, is mode 0700, is owned by the effective account, is
  not a symlink, and resolves outside Git.
- Preserve the Phase 0 WAV, environment report, and model cache as read-only.
- Do not print the resolved private path or inspect existing private-file
  content.

Create only missing directories from the exact Step 1 approved list in
docs/phase1_governance_handoff.md, with mode 0700. Create the three exact blank
working copies listed there with mode 0600, copying only the repository’s blank
templates/register/checklist. Stop if any destination already exists; do not
overwrite or repair it automatically.

Do not fill any participant choice, identity, signature, language decision,
prompt, rating, or recording field. Do not create credentials, encryption keys,
recovery keys, backups, audio, manifests derived from real data, or checkpoints.

Set PATH for the pinned unmanaged uv installation, run:

  uv run hmong-tts-env --require-data-root
  uv run hmong-tts-privacy-scan --require-data-root
  git status --porcelain

Require both checks to pass and Git to remain clean. Return only a stage-by-stage
PASS summary, the names of blank working copies created without their absolute
paths, and a Gates A–D gap list labeled Terminal, Outside, or Both.

Stop and wait for my review. Do not begin Step 2.
```

### Step 1 review and outside follow-up

After Step 1 passes:

1. Confirm that the terminal reported no tracked changes and no private-content
   inspection.
2. Open the blank consent working copy through the private storage interface,
   adapt it if needed, and obtain legal review if appropriate. Do not paste the
   completed copy into this chat.
3. Privately assign the `spk01` and `reviewer02` identity mappings.
4. Schedule a consent discussion and native-validation sessions with both
   speakers.
5. Select encrypted backup media/off-site storage and decide who retains the
   recovery information. Do not ask the terminal to invent or expose secrets.
6. Proceed to Step 2 only through a new, explicit authorization.

## Reference documents

- `docs/templates/consent_template.md` — blank consent choices; not legal advice.
- `docs/native_validation_register.md` — NV-001 through NV-008.
- `docs/recording_readiness_checklist.md` — Gates A through E.
- `docs/privacy_and_consent.md` — repository/private-data boundary.
- `data/README.md` — approved private layout.
- `WHITE_HMONG_TTS_PROJECT_PLAN.md` — pilot, recording, training, and evaluation
  requirements.
