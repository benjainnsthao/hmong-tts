"""Create or verify M7's review identity without embedding the final commit SHA."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import subprocess
from pathlib import Path
from typing import Any

BASELINE = "32e55eed6c647fbe497e14973c768bf83f0a3a85"
MANIFEST = "reports/validation/m7_candidate_manifest.json"
APPROVAL = "docs/m7_owner_approval.json"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def candidate_manifest(root: Path) -> dict[str, Any]:
    """Bind file names, executable modes, and bytes; normalize only final approval."""
    raw = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root
    )
    entries = []
    for name in sorted(set(raw.decode().strip("\0").split("\0"))):
        if not name or name == MANIFEST:
            continue
        path = root / name
        if path.is_symlink():
            raise ValueError("candidate symlinks require separate review")
        if not path.exists():
            continue  # A tracked deletion is represented by absence from this complete list.
        content = path.read_bytes()
        if name == APPROVAL:
            approval = json.loads(content)
            # The only post-review change allowed: recording the actual human decision.
            approval["release_approval"] = None
            content = canonical(approval)
        mode = "100755" if path.stat().st_mode & stat.S_IXUSR else "100644"
        entries.append({"path": name, "mode": mode, "sha256": hashlib.sha256(content).hexdigest()})
    payload = {"schema_version": 1, "starting_commit": BASELINE, "files": entries}
    return {**payload, "candidate_sha256": hashlib.sha256(canonical(payload)).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write a new review manifest")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    actual = candidate_manifest(root)
    target = root / MANIFEST
    if args.write:
        target.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    elif json.loads(target.read_text(encoding="utf-8")) != actual:
        print("FAIL: candidate contents differ from the reviewed manifest")
        return 1
    print(f"PASS: {len(actual['files'])} files; candidate_sha256={actual['candidate_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
