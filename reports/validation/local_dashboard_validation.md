# Local dashboard validation

Date: 2026-09-15. Scope: subsequent local browser development, not a new M7
release approval. M7 approval, candidate manifest, and historical evidence were
not changed. Validation was completed before committing or pushing. The owner
subsequently authorized committing and pushing this work to the active branch;
package publication and public deployment remain outside this work.

## Results

- Full Python suite including optional Chromium workflows: **310 passed**.
- Aggregate branch-aware coverage: **84.08%**, above the existing 78% gate.
- Strict typing: **44 source files passed**.
- Ruff lint and formatting, JavaScript syntax, shell syntax, diff whitespace,
  and repository privacy scan: passed.
- Wheel and sdist include dashboard assets. An externally installed wheel
  served HTML/CSS/JavaScript from outside the source checkout.
- Browser automation used Playwright 1.63.0 with locally available Chromium.
  It verified actual audio playback/seek, WAV download, result switching,
  mobile width without overflow, safe text rendering, limits, missing runtime,
  duplicate-submit prevention, queue-full/device errors, and connection loss.
- HTTP tests covered same-origin/Host restrictions, trusted CLI access,
  independent run/file IDs, manifest verification, unavailable results,
  traversal and symlink rejection, no-store headers, and byte ranges.
- The production launcher was exercised against the core-only external
  environment. Health and dashboard requests passed, and Chromium showed the
  missing-runtime setup message with generation disabled. The service was
  stopped after this check.

## Interpretation and gaps

Automated generation used a test-only sine-wave adapter through the real HTTP
application, queue, executor, and artifact transaction. Production has no fake
mode. This verifies the interface and engineering behavior, not synthesized
speech or linguistic quality. Real MMS inference was not exercised: the
configured external environment has no optional MMS runtime, and no approved
English snapshot was found in the checked local caches. Install the locked
`mms` extra and run the English example to complete that check.

Chromium was tested; Firefox, Safari, and assistive-technology interaction were
not manually verified. Synthetic browser testing does not establish real GPU
performance or the duration of initial model downloads. A Starlette warning
about the existing httpx TestClient dependency was emitted; tests passed and
the dependency lock was left unchanged.

Screenshots, generated audio, wheel installs, browser tools, coverage data,
and pytest temporary outputs remained external. See
[`apps/README.md`](../../apps/README.md) for reproduction and launch commands.
