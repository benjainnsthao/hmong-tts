"""Enforce the workbench's external artifact boundary."""

from __future__ import annotations

import os
import warnings
from collections.abc import Mapping
from pathlib import Path

ARTIFACT_ROOT_ENV = "TTS_WORKBENCH_ARTIFACT_ROOT"
LEGACY_ARTIFACT_ROOT_ENV = "HMONG_TTS_DATA_ROOT"
REPOSITORY_MARKERS = (
    Path("pyproject.toml"),
    Path("configs/models/registry.yaml"),
)


class ArtifactBoundaryError(ValueError):
    """Raised when a path could place workbench artifacts inside Git."""


class LegacyArtifactRootWarning(FutureWarning):
    """Warn that the temporary legacy artifact-root variable must be removed."""


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


def _select_configured_root(env: Mapping[str, str]) -> tuple[Path, str]:
    canonical_raw = env.get(ARTIFACT_ROOT_ENV, "").strip()
    legacy_raw = env.get(LEGACY_ARTIFACT_ROOT_ENV, "").strip()

    if not canonical_raw and not legacy_raw:
        raise ArtifactBoundaryError(f"{ARTIFACT_ROOT_ENV} is not set")

    if canonical_raw and legacy_raw:
        canonical = _absolute_configured_path(canonical_raw, ARTIFACT_ROOT_ENV)
        legacy = _absolute_configured_path(legacy_raw, LEGACY_ARTIFACT_ROOT_ENV)
        if canonical.resolve(strict=False) != legacy.resolve(strict=False):
            raise ArtifactBoundaryError(
                f"{ARTIFACT_ROOT_ENV} and {LEGACY_ARTIFACT_ROOT_ENV} resolve to different paths"
            )
        warnings.warn(
            f"{LEGACY_ARTIFACT_ROOT_ENV} is deprecated and duplicates "
            f"{ARTIFACT_ROOT_ENV}; remove the legacy variable",
            LegacyArtifactRootWarning,
            stacklevel=3,
        )
        return canonical, ARTIFACT_ROOT_ENV

    if canonical_raw:
        return _absolute_configured_path(canonical_raw, ARTIFACT_ROOT_ENV), ARTIFACT_ROOT_ENV

    warnings.warn(
        f"{LEGACY_ARTIFACT_ROOT_ENV} is deprecated; set {ARTIFACT_ROOT_ENV} instead",
        LegacyArtifactRootWarning,
        stacklevel=3,
    )
    return (
        _absolute_configured_path(legacy_raw, LEGACY_ARTIFACT_ROOT_ENV),
        LEGACY_ARTIFACT_ROOT_ENV,
    )


def get_artifact_root(
    *,
    environ: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
    require_exists: bool = True,
) -> Path:
    """Return a validated absolute artifact root located outside the repository."""
    env = os.environ if environ is None else environ
    configured, selected_variable = _select_configured_root(env)
    if configured.is_symlink():
        raise ArtifactBoundaryError(f"{selected_variable} must not be a symlink")

    artifact_root = configured.resolve(strict=False)
    repo_root = (repository_root or find_repository_root()).resolve()
    if artifact_root == repo_root or _is_within(artifact_root, repo_root):
        raise ArtifactBoundaryError(f"{selected_variable} must resolve outside the repository")
    if require_exists and not artifact_root.is_dir():
        raise ArtifactBoundaryError(f"{selected_variable} does not exist or is not a directory")
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
