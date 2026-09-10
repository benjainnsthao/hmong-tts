"""Enforce the workbench's external artifact boundary."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

ARTIFACT_ROOT_ENV = "TTS_WORKBENCH_ARTIFACT_ROOT"
REPOSITORY_MARKERS = (
    Path("pyproject.toml"),
    Path("configs/models/registry.yaml"),
)


class ArtifactBoundaryError(ValueError):
    """Raised when a path could place workbench artifacts inside Git."""


def find_repository_root(start: Path | None = None) -> Path:
    """Find the project root using neutral committed markers."""
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if all((candidate / marker).is_file() for marker in REPOSITORY_MARKERS):
            return candidate
    marker_list = ", ".join(str(marker) for marker in REPOSITORY_MARKERS)
    raise ArtifactBoundaryError(f"Could not locate repository markers: {marker_list}")


def _is_within(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
    except ValueError:
        return False
    return True


def _absolute_configured_path(raw_value: str, variable: str) -> Path:
    configured = Path(raw_value).expanduser()
    if not configured.is_absolute():
        raise ArtifactBoundaryError(f"{variable} must be an absolute path")
    return configured


def get_artifact_root(
    *,
    environ: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
    require_exists: bool = True,
) -> Path:
    """Return a validated absolute artifact root located outside the repository."""
    env = os.environ if environ is None else environ
    raw_value = env.get(ARTIFACT_ROOT_ENV, "").strip()
    if not raw_value:
        raise ArtifactBoundaryError(f"{ARTIFACT_ROOT_ENV} is not set")
    configured = _absolute_configured_path(raw_value, ARTIFACT_ROOT_ENV)
    if configured.is_symlink():
        raise ArtifactBoundaryError(f"{ARTIFACT_ROOT_ENV} must not be a symlink")

    artifact_root = configured.resolve(strict=False)
    repo_root = (repository_root or find_repository_root()).resolve()
    if artifact_root == repo_root or _is_within(artifact_root, repo_root):
        raise ArtifactBoundaryError(f"{ARTIFACT_ROOT_ENV} must resolve outside the repository")
    if require_exists and not artifact_root.is_dir():
        raise ArtifactBoundaryError(f"{ARTIFACT_ROOT_ENV} does not exist or is not a directory")
    return artifact_root


def require_under_artifact_root(
    path: Path,
    *,
    artifact_root: Path | None = None,
) -> Path:
    """Validate that an input or output path stays below the artifact root."""
    root = (artifact_root or get_artifact_root()).resolve()
    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=False)
    if resolved == root or not _is_within(resolved, root):
        raise ArtifactBoundaryError(f"Path must be below {ARTIFACT_ROOT_ENV}")
    return resolved
