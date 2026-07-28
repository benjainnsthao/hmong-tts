from pathlib import Path

import pytest

from tts_workbench.artifacts.paths import (
    ARTIFACT_ROOT_ENV,
    LEGACY_ARTIFACT_ROOT_ENV,
    ArtifactBoundaryError,
    LegacyArtifactRootWarning,
    find_repository_root,
    get_artifact_root,
    require_under_artifact_root,
)


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "configs/models").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
    (repo / "configs/models/registry.yaml").write_text(
        "schema_version: 1\nmodels: []\n",
        encoding="utf-8",
    )
    return repo


def test_accepts_canonical_artifact_root_without_warning(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()

    result = get_artifact_root(
        environ={ARTIFACT_ROOT_ENV: str(artifact_root)},
        repository_root=repo,
    )

    assert result == artifact_root.resolve()


def test_accepts_legacy_only_root_with_deprecation_warning(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    artifact_root = tmp_path / "legacy-artifacts"
    artifact_root.mkdir()

    with pytest.warns(LegacyArtifactRootWarning, match="deprecated"):
        result = get_artifact_root(
            environ={LEGACY_ARTIFACT_ROOT_ENV: str(artifact_root)},
            repository_root=repo,
        )

    assert result == artifact_root.resolve()


def test_accepts_matching_canonical_and_legacy_roots_with_warning(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    artifact_root = tmp_path / "shared-artifacts"
    artifact_root.mkdir()

    with pytest.warns(LegacyArtifactRootWarning, match="remove the legacy variable"):
        result = get_artifact_root(
            environ={
                ARTIFACT_ROOT_ENV: str(artifact_root),
                LEGACY_ARTIFACT_ROOT_ENV: str(artifact_root),
            },
            repository_root=repo,
        )

    assert result == artifact_root.resolve()


def test_rejects_conflicting_canonical_and_legacy_roots(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    canonical = tmp_path / "canonical"
    legacy = tmp_path / "legacy"
    canonical.mkdir()
    legacy.mkdir()

    with pytest.raises(ArtifactBoundaryError, match="resolve to different paths"):
        get_artifact_root(
            environ={
                ARTIFACT_ROOT_ENV: str(canonical),
                LEGACY_ARTIFACT_ROOT_ENV: str(legacy),
            },
            repository_root=repo,
        )


def test_rejects_missing_root(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    with pytest.raises(ArtifactBoundaryError, match=f"{ARTIFACT_ROOT_ENV} is not set"):
        get_artifact_root(environ={}, repository_root=repo)


@pytest.mark.parametrize("variable", [ARTIFACT_ROOT_ENV, LEGACY_ARTIFACT_ROOT_ENV])
def test_rejects_relative_root(tmp_path: Path, variable: str) -> None:
    repo = make_repo(tmp_path)
    if variable == LEGACY_ARTIFACT_ROOT_ENV:
        with (
            pytest.warns(LegacyArtifactRootWarning),
            pytest.raises(ArtifactBoundaryError, match="absolute path"),
        ):
            get_artifact_root(environ={variable: "relative/path"}, repository_root=repo)
    else:
        with pytest.raises(ArtifactBoundaryError, match="absolute path"):
            get_artifact_root(environ={variable: "relative/path"}, repository_root=repo)


def test_rejects_nonexistent_root(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)

    with pytest.raises(ArtifactBoundaryError, match="does not exist"):
        get_artifact_root(
            environ={ARTIFACT_ROOT_ENV: str(tmp_path / "missing")},
            repository_root=repo,
        )


def test_rejects_root_inside_repository(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    inside = repo / "artifacts"
    inside.mkdir()

    with pytest.raises(ArtifactBoundaryError, match="outside"):
        get_artifact_root(
            environ={ARTIFACT_ROOT_ENV: str(inside)},
            repository_root=repo,
        )


def test_output_must_remain_below_artifact_root(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()

    assert (
        require_under_artifact_root(
            Path("smoke/output.wav"),
            artifact_root=artifact_root,
        )
        == (artifact_root / "smoke/output.wav").resolve()
    )

    with pytest.raises(ArtifactBoundaryError):
        require_under_artifact_root(
            tmp_path / "escaped.wav",
            artifact_root=artifact_root,
        )


def test_repository_root_detection_uses_neutral_markers(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    nested = repo / "src/package"
    nested.mkdir(parents=True)

    assert not (repo / "WHITE_HMONG_TTS_PROJECT_PLAN.md").exists()
    assert find_repository_root(nested) == repo.resolve()


def test_repository_root_requires_both_markers(tmp_path: Path) -> None:
    incomplete = tmp_path / "incomplete"
    incomplete.mkdir()
    (incomplete / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")

    with pytest.raises(ArtifactBoundaryError, match="configs.models.registry.yaml"):
        find_repository_root(incomplete)
