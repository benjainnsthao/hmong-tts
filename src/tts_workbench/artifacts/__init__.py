"""External artifact-boundary helpers."""

from tts_workbench.artifacts.paths import (
    ARTIFACT_ROOT_ENV,
    ArtifactBoundaryError,
    get_artifact_root,
    require_under_artifact_root,
)

__all__ = [
    "ARTIFACT_ROOT_ENV",
    "ArtifactBoundaryError",
    "get_artifact_root",
    "require_under_artifact_root",
]
