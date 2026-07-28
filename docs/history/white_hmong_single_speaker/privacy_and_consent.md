# Privacy and consent controls

The project uses privacy-by-location and privacy-by-validation. Git contains
only code, schemas, blank templates, public documentation, and synthetic test
fixtures. Real data is never copied into the working tree.

## Boundary

`HMONG_TTS_DATA_ROOT` must be an absolute existing directory outside the
repository. `hmong_tts.data.paths` rejects repository-relative roots and rejects
any private input/output path that escapes the approved root. Public model
downloads may use a cache, but generated WAV, checkpoints, manifests containing
private text, ratings, and logs remain below the private root.

`HMONG_TTS_PII_DENYLIST` may point to a separate encrypted text file outside the
repository, with one known speaker identifier per line. Local scans compare its
contents case-insensitively without copying identifiers into reports.

## Automated controls

- `.gitignore` blocks audio, model artifacts, completed consent/release names,
  local environment files, and private working directories.
- `hmong-tts-privacy-scan` detects forbidden extensions, audio magic bytes,
  consent records, private keys, common service-token formats, email addresses,
  US phone/SSN patterns, and external-denylist identifiers.
- Explicit file tests prove ignored audio or renamed audio is rejected if
  scanned; staged force-adds are included in the default Git candidate list.
- The same scanner runs in pre-commit, CI, and the ordinary test suite.
- Hosted experiment tracking is prohibited; configs require local/offline mode.

## Private layout and access

See `data/README.md`. Consent records are separate from recordings. Use
full-disk/file encryption, least-privilege accounts, encrypted backups, and
checksums. Never paste secrets or private data into issues, prompts, logs, model
cards, validation reports, or hosted services.

## Incident response

If sensitive material appears in Git or an external system:

1. Stop syncing, deployment, and distribution; disable public access.
2. Revoke exposed credentials and preserve only minimal non-sensitive evidence.
3. Notify the project owner and affected participant through a private channel.
4. Remove controlled copies and rotate/rebuild affected artifacts.
5. Assess history/caches/forks; do not claim deletion from third parties unless verified.
6. Record the incident and prevention change in a private incident record; put
   only a redacted decision summary in this repository.

## Consent gate

Use `docs/templates/consent_template.md`. It is project documentation, not legal
advice. Completed forms and signatures remain outside Git. Reconfirm consent
before public demos, samples, or model distribution and whenever scope changes.
