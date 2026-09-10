from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


def test_review_identity_detects_content_and_mode_changes_but_allows_recording_approval(
    repository_root: Path,
) -> None:
    spec = importlib.util.spec_from_file_location(
        "release_manifest", repository_root / "scripts/release_manifest.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Use the native temporary filesystem: mounted artifact drives may ignore chmod.
    with TemporaryDirectory(prefix="tts-workbench-manifest-") as directory:
        tmp_path = Path(directory)
        (tmp_path / "docs").mkdir()
        source = tmp_path / "source.py"
        source.write_text("value = 1\n")
        approval = tmp_path / module.APPROVAL
        approval.write_text(json.dumps({"owner": "fixture-owner", "release_approval": None}))
        with patch.object(
            module.subprocess,
            "check_output",
            return_value=b"source.py\0docs/m7_owner_approval.json\0",
        ):
            original = module.candidate_manifest(tmp_path)
            approval.write_text(
                json.dumps({"owner": "fixture-owner", "release_approval": {"status": "approved"}})
            )
            assert module.candidate_manifest(tmp_path) == original
            source.write_text("value = 2\n")
            assert module.candidate_manifest(tmp_path) != original
            source.write_text("value = 1\n")
            source.chmod(0o755)
            assert module.candidate_manifest(tmp_path) != original
            source.chmod(0o644)
            approval.write_text(json.dumps({"owner": "different-owner", "release_approval": None}))
            assert module.candidate_manifest(tmp_path) != original
