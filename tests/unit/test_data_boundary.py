from pathlib import Path

import pytest

from hmong_tts.data.paths import DataBoundaryError, get_data_root, require_under_data_root


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "WHITE_HMONG_TTS_PROJECT_PLAN.md").write_text("synthetic", encoding="utf-8")
    return repo


def test_accepts_existing_absolute_root_outside_repository(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    private = tmp_path / "private-data"
    private.mkdir()

    result = get_data_root(environ={"HMONG_TTS_DATA_ROOT": str(private)}, repository_root=repo)

    assert result == private.resolve()


@pytest.mark.parametrize("value", ["", "relative/path"])
def test_rejects_missing_or_relative_root(tmp_path: Path, value: str) -> None:
    repo = make_repo(tmp_path)
    with pytest.raises(DataBoundaryError):
        get_data_root(environ={"HMONG_TTS_DATA_ROOT": value}, repository_root=repo)


def test_rejects_root_inside_repository(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    inside = repo / "private"
    inside.mkdir()
    with pytest.raises(DataBoundaryError, match="outside"):
        get_data_root(environ={"HMONG_TTS_DATA_ROOT": str(inside)}, repository_root=repo)


def test_output_must_remain_below_private_root(tmp_path: Path) -> None:
    private = tmp_path / "private"
    private.mkdir()
    assert (
        require_under_data_root(Path("smoke/output.wav"), data_root=private)
        == (private / "smoke/output.wav").resolve()
    )
    with pytest.raises(DataBoundaryError):
        require_under_data_root(tmp_path / "escaped.wav", data_root=private)
