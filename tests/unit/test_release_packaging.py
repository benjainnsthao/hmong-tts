"""Build real archives with the project's pinned backend and synthetic Git metadata."""

from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

import pytest


@pytest.mark.parametrize("git_layout", ["directory", "worktree-pointer"])
def test_archives_exclude_git_metadata_at_root_and_inside_package(
    repository_root: Path, tmp_path: Path, git_layout: str
) -> None:
    # The normal core sync/build populates uv's pinned build cache. No model
    # runtime or network is needed; all generated content lives in pytest's temp root.
    project = tmp_path / "project"
    project.mkdir()
    for name in ["pyproject.toml", "README.md", "LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"]:
        shutil.copyfile(repository_root / name, project / name)
    package = project / "src/tts_workbench"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text('__version__ = "1.0.0"\n', encoding="utf-8")
    canary = b"SYNTHETIC_GIT_ADMINISTRATIVE_CONTENT_MUST_NOT_SHIP"
    for parent in [project, package]:
        marker = parent / ".git"
        if git_layout == "directory":
            marker.mkdir()
            (marker / "config").write_bytes(canary)
        else:
            marker.write_bytes(b"gitdir: " + str(tmp_path / "synthetic-admin").encode() + b"\n")

    environment = os.environ.copy()
    environment["UV_OFFLINE"] = "1"
    environment["UV_PYTHON_DOWNLOADS"] = "never"
    result = subprocess.run(
        ["uv", "build", "--offline", "--sdist", "--wheel", "--out-dir", str(tmp_path / "dist")],
        cwd=project,
        env=environment,
        capture_output=True,
        check=False,
    )
    # Do not echo build output: it can contain temporary absolute paths.
    assert result.returncode == 0, "offline packaging failed; populate the pinned build cache"
    archives = sorted((tmp_path / "dist").glob("*"))
    archives = [path for path in archives if path.suffix == ".whl" or path.name.endswith(".tar.gz")]
    assert len(archives) == 2
    for archive in archives:
        if archive.suffix == ".whl":
            with zipfile.ZipFile(archive) as wheel:
                members = {name: wheel.read(name) for name in wheel.namelist()}
        else:
            with tarfile.open(archive) as sdist:
                assert all(member.isfile() for member in sdist.getmembers())
                members = {}
                for member in sdist.getmembers():
                    stream = sdist.extractfile(member)
                    assert stream is not None
                    members[member.name] = stream.read()
        assert not any(".git" in PurePosixPath(name).parts for name in members)
        assert not any(canary in content for content in members.values())
        assert not any(str(tmp_path).encode() in content for content in members.values())
        for notice in ["LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"]:
            matches = [content for name, content in members.items() if name.endswith("/" + notice)]
            assert matches == [(repository_root / notice).read_bytes()]
        assert any(name.endswith("tts_workbench/__init__.py") for name in members)
