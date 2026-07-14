#!/usr/bin/env bash
set -euo pipefail

UV_VERSION="0.11.28"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required." >&2
  exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
  if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "pip is missing. On Ubuntu run: sudo apt-get install python3-pip" >&2
    exit 2
  fi
  python3 -m pip install --user "uv==${UV_VERSION}"
  export PATH="$(python3 -m site --user-base)/bin:${PATH}"
fi

actual_uv="$(uv --version | awk '{print $2}')"
if [[ "${actual_uv}" != "${UV_VERSION}" ]]; then
  echo "Expected uv ${UV_VERSION}; found ${actual_uv}." >&2
  exit 2
fi

uv sync --frozen
uv run pre-commit install
uv run hmong-tts-config-check
uv run hmong-tts-privacy-scan
uv run pytest
