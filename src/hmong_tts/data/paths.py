"""Enforce the repository's private-data boundary."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

DATA_ROOT_ENV = "HMONG_TTS_DATA_ROOT"


class DataBoundaryError(ValueError):
    """Raised when a path could expose private data to the repository."""


def find_repository_root(start: Path | None = None) -> Path:
    """Find the project root without embedding a machine-specific path."""
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "WHITE_HMONG_TTS_PROJECT_PLAN.md").is_file():
            return candidate
    raise DataBoundaryError("Could not locate WHITE_HMONG_TTS_PROJECT_PLAN.md")


def _is_within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
    except ValueError:
        return False
    return True


def get_data_root(
    *,
    environ: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
    require_exists: bool = True,
) -> Path:
    """Return a validated absolute data root located outside the repository."""
    env = os.environ if environ is None else environ
    raw_value = env.get(DATA_ROOT_ENV, "").strip()
    if not raw_value:
        raise DataBoundaryError(f"{DATA_ROOT_ENV} is not set")

    configured = Path(raw_value).expanduser()
    if not configured.is_absolute():
        raise DataBoundaryError(f"{DATA_ROOT_ENV} must be an absolute path")

    data_root = configured.resolve(strict=False)
    repo_root = (repository_root or find_repository_root()).resolve()
    if data_root == repo_root or _is_within(data_root, repo_root):
        raise DataBoundaryError(f"{DATA_ROOT_ENV} must resolve outside the repository")
    if require_exists and not data_root.is_dir():
        raise DataBoundaryError(f"{DATA_ROOT_ENV} does not exist or is not a directory")
    return data_root


def require_under_data_root(path: Path, *, data_root: Path | None = None) -> Path:
    """Validate that an input/output path stays inside the approved private root."""
    root = (data_root or get_data_root()).resolve()
    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=False)
    if resolved == root or not _is_within(resolved, root):
        raise DataBoundaryError(f"Path must be below {DATA_ROOT_ENV}")
    return resolved
