# M7 artifact-root migration

Version 1.0.0 removes the 0.2 migration bridge, including
`LegacyArtifactRootWarning` and the legacy environment selector. The owner
approved removal on 2026-09-10 for the intended stable public release.

Set `TTS_WORKBENCH_ARTIFACT_ROOT` to the same existing external directory used
for retained evidence, then remove the old variable from shell startup files,
launchers, CI configuration, and local wrappers. A one-time Bash migration,
when the legacy value is the intended valid directory, is:

```bash
export TTS_WORKBENCH_ARTIFACT_ROOT="${HMONG_TTS_DATA_ROOT}"
unset HMONG_TTS_DATA_ROOT
```

Do not place literal machine-local values in Git. Set `HF_HOME`, `TORCH_HOME`,
and the uv/pre-commit caches below the external boundary; keep virtual
environments external as well. No retained files need to move or be deleted.

| Configuration | 1.0.0 behavior |
|---|---|
| Valid canonical variable only | Accepted |
| Legacy variable only | Fails: canonical variable is not set |
| Both supplied | Only canonical value is read; legacy has no effect |
| Missing, relative, in-repository, nonexistent, or symlinked canonical root | Fails closed |

Tests exercise all rows, including contradictory legacy values and environment
readiness with legacy-only configuration. No compatibility alias remains in
active production source. Historical M1–M6 reports describe behavior at their
own versions and are deliberately unchanged. The separate deprecated
`--require-training` readiness alias is outside this approved variable removal
and remains as documented; it does not authorize training.
