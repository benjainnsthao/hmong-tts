#!/usr/bin/env bash
# Launch the installed local dashboard with external defaults on Linux/WSL.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-${HOME}/.local/share/tts-workbench/venv}"
if [[ -z "${TTS_WORKBENCH_ARTIFACT_ROOT:-}" ]]; then
  export TTS_WORKBENCH_ARTIFACT_ROOT="${HOME}/tts-workbench-artifacts"
  mkdir -p -- "${TTS_WORKBENCH_ARTIFACT_ROOT}"
fi
export HF_HOME="${HF_HOME:-${TTS_WORKBENCH_ARTIFACT_ROOT}/cache/huggingface}"
export TORCH_HOME="${TORCH_HOME:-${TTS_WORKBENCH_ARTIFACT_ROOT}/cache/torch}"
export PYTHONDONTWRITEBYTECODE=1
python3 - <<'PY'
import os
from pathlib import Path

repository = Path.cwd().resolve()
for variable in ("UV_PROJECT_ENVIRONMENT", "TTS_WORKBENCH_ARTIFACT_ROOT", "HF_HOME", "TORCH_HOME"):
    path = Path(os.environ[variable]).expanduser()
    if not path.is_absolute() or path.resolve().is_relative_to(repository):
        raise SystemExit(f"{variable} must be an absolute directory outside the repository.")
PY
if [[ ! -x "${UV_PROJECT_ENVIRONMENT}/bin/tts-workbench-serve" ]]; then
  echo 'Install first: UV_PROJECT_ENVIRONMENT="$HOME/.local/share/tts-workbench/venv" uv sync --frozen --extra mms --python 3.12' >&2
  exit 2
fi
exec "${UV_PROJECT_ENVIRONMENT}/bin/tts-workbench-serve" run --acknowledge-model-access "$@"
