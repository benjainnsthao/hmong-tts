#!/usr/bin/env bash
set -euo pipefail

UV_VERSION="0.11.28"
UV_INSTALL_DIR="${HOME}/.local/bin"
UV_INSTALLER_URL="https://astral.sh/uv/${UV_VERSION}/install.sh"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required." >&2
  exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
  if [[ -x "${UV_INSTALL_DIR}/uv" ]]; then
    export PATH="${UV_INSTALL_DIR}:${PATH}"
  elif ! command -v curl >/dev/null 2>&1; then
    echo "curl is missing. On Ubuntu run: sudo apt-get install curl" >&2
    exit 2
  else
    # The versioned standalone installer does not modify the PEP 668-managed
    # system Python. Unmanaged mode also avoids shell-profile edits and
    # disables self-updates; the exact binary version is verified below.
    curl --proto '=https' --tlsv1.2 -LsSf "${UV_INSTALLER_URL}" \
      | env UV_UNMANAGED_INSTALL="${UV_INSTALL_DIR}" sh
    export PATH="${UV_INSTALL_DIR}:${PATH}"
  fi
fi

actual_uv="$(uv --version | awk '{print $2}')"
if [[ "${actual_uv}" != "${UV_VERSION}" ]]; then
  echo "Expected uv ${UV_VERSION}; found ${actual_uv}." >&2
  exit 2
fi

uv sync --frozen
uv run pre-commit install
uv run hmong-tts-config-check
uv run tts-workbench-models validate
uv run hmong-tts-privacy-scan
uv run pytest
