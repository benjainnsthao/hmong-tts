# Local browser dashboard

The dashboard shares the FastAPI service at `/`. HTML, CSS, and JavaScript live
in `src/tts_workbench/service/static/` and ship in Python packages. There is no
frontend build step, second server, external CDN, or production fake mode.

## Install and launch

From the repository on Linux/WSL x86-64:

```bash
UV_PROJECT_ENVIRONMENT="$HOME/.local/share/tts-workbench/venv" \
  uv sync --frozen --extra mms --python 3.12
bash scripts/launch-local.sh
```

Open **http://127.0.0.1:8000/**. The launcher acknowledges model access and uses
external defaults for the environment, artifacts, and caches. It respects
existing `UV_PROJECT_ENVIRONMENT`, `TTS_WORKBENCH_ARTIFACT_ROOT`, `HF_HOME`, and
`TORCH_HOME` settings. It does not install packages or change drivers.

After configuring those variables yourself, the equivalent command is
`tts-workbench-serve run --acknowledge-model-access`. Use `--config` with a
local YAML file to change the loopback port. The terminal prints the URL and
actionable startup errors. Without speech dependencies, the dashboard opens
and explains that installing the `mms` extra and restarting is necessary.

## Generate and compare

1. Select English and choose **Load example**, or enter permitted custom text.
2. Choose **Generate speech**. First use may download/load the registered voice.
3. Press play, seek through the clip, or download a local WAV copy.
4. Adjust device, seed, or speaking speed under **Advanced settings** and
   compare clips from the session list.

The UI follows the configured character limit (at most 500), counting Unicode
code points after trimming. Multiline text is preserved. The UI uses speeds
from 0.5 to 2.0 and nonnegative JavaScript-safe integer seeds. The existing API
retains its wider settings range.

The last eight results stay in page memory. Reloading or clearing the list
does not delete files. The server exposes only its latest 64 successful runs
from the current process, with a 32 MiB playback limit per WAV. Restarting or
evicting a result removes browser access but leaves external files intact.
No directory is scanned or listed. Prompts and audio are not placed in
persistent browser storage or caches. An explicit download saves a local file.

Custom English text is recorded as `user_supplied_unreviewed`. Vietnamese
requires the exact externally reviewed prompt and the source/provenance review
in `docs/m7_reproduction.md`; neither prompt nor source is bundled in the UI.
Hash matching verifies content identity, not a fresh rights review. Language
quality is unevaluated. Hmong support and NV-001 through NV-008 remain deferred.

A disconnected request may continue generating. The UI never retries
automatically or claims to cancel active inference. Check service activity
before explicitly starting another request. Global queue counts do not identify
a particular request's status; elapsed time is not a model progress estimate.

## Verification

Ordinary tests use fake backends and synthetic audio. The optional Chromium
suite `tests/browser/test_workflow.py` runs the real HTTP service, queue, and
artifact transaction with a test-only sine-wave adapter. It checks generation,
playback/seek, download, history, mobile overflow, safe rendering, input limits,
missing runtime, duplicate submission, errors, and disconnects.

Install Playwright separately in an external test environment containing the
project's development dependencies, then install its Chromium browser:

```bash
python -m playwright install chromium
python -m pytest tests/browser -q
```

`PLAYWRIGHT_CHROMIUM_EXECUTABLE` may select an existing compatible browser.
Optional `TTS_BROWSER_SCREENSHOT` must point outside Git. Without Playwright,
the browser module is explicitly skipped. API/security/package tests still run.
`tests/unit/test_browser_package.py` verifies the installed wheel from outside
the checkout. Synthetic checks establish no real model or linguistic quality;
real MMS checks require the optional runtime and approved checkpoint.
