"""Fail closed when public repository candidates contain private artifacts."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from hmong_tts.data.paths import DataBoundaryError, find_repository_root, get_data_root

FORBIDDEN_EXTENSIONS = {
    ".aac",
    ".ckpt",
    ".doc",
    ".docx",
    ".flac",
    ".m4a",
    ".mp3",
    ".ogg",
    ".onnx",
    ".opus",
    ".p12",
    ".pdf",
    ".pem",
    ".pfx",
    ".pt",
    ".pth",
    ".safetensors",
    ".wav",
    ".wma",
}
SKIP_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".uv-cache",
    ".venv",
    "__pycache__",
}
ALLOWED_CONSENT_DOCUMENTATION = {
    "docs/privacy_and_consent.md",
    "docs/templates/consent_template.md",
}
AUDIO_MAGIC = (b"fLaC", b"ID3", b"OggS")


@dataclass(frozen=True)
class Finding:
    path: Path
    rule: str
    detail: str

    def render(self, root: Path) -> str:
        try:
            display = self.path.resolve().relative_to(root.resolve())
        except ValueError:
            display = self.path
        return f"{display}: {self.rule}: {self.detail}"


def _content_patterns() -> tuple[tuple[str, re.Pattern[str]], ...]:
    # Sensitive examples are split so the scanner source does not match itself.
    return (
        ("email-address", re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
        ("us-ssn", re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")),
        (
            "us-phone-number",
            re.compile(r"(?<!\d)(?:\+1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)"),
        ),
        ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
        ("aws-access-key", re.compile(r"A" + r"KIA[0-9A-Z]{16}")),
        ("github-token", re.compile(r"g" + r"h[pousr]_[A-Za-z0-9]{20,}")),
        ("huggingface-token", re.compile(r"h" + r"f_[A-Za-z0-9]{20,}")),
        ("slack-token", re.compile(r"x" + r"ox[baprs]-[A-Za-z0-9-]{10,}")),
        (
            "assigned-secret",
            re.compile(
                r"(?im)^\s*(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)"
                r"\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{12,}"
            ),
        ),
    )


def _git_candidates(root: Path) -> list[Path] | None:
    if not (root / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return [root / os.fsdecode(item) for item in result.stdout.split(b"\0") if item]


def candidate_files(root: Path) -> list[Path]:
    """Return every file that could enter Git without an explicit force-add."""
    candidates = _git_candidates(root)
    if candidates is not None:
        return sorted(path for path in candidates if path.is_file())
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not any(part in SKIP_DIRECTORIES for part in path.parts)
    )


def load_private_identifiers(root: Path) -> list[str]:
    denylist_value = os.environ.get("HMONG_TTS_PII_DENYLIST", "").strip()
    if not denylist_value:
        return []
    denylist_path = Path(denylist_value).expanduser()
    if not denylist_path.is_absolute():
        raise DataBoundaryError("HMONG_TTS_PII_DENYLIST must be an absolute path")
    resolved = denylist_path.resolve(strict=True)
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        pass
    else:
        raise DataBoundaryError("HMONG_TTS_PII_DENYLIST must stay outside the repository")
    return [
        line.strip()
        for line in resolved.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def scan_file(path: Path, *, root: Path, private_identifiers: Sequence[str] = ()) -> list[Finding]:
    findings: list[Finding] = []
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        relative = path.name
    lowered_path = relative.lower()

    if path.suffix.lower() in FORBIDDEN_EXTENSIONS:
        findings.append(Finding(path, "forbidden-file-type", path.suffix.lower()))
    if "consent" in lowered_path and relative not in ALLOWED_CONSENT_DOCUMENTATION:
        findings.append(
            Finding(path, "consent-record", "consent files are private; only templates are allowed")
        )
    if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
        findings.append(
            Finding(path, "environment-file", "local environment files must not enter Git")
        )

    try:
        raw = path.read_bytes()
    except OSError as exc:
        findings.append(Finding(path, "unreadable", str(exc)))
        return findings
    if raw.startswith(AUDIO_MAGIC) or (raw.startswith(b"RIFF") and raw[8:12] == b"WAVE"):
        findings.append(
            Finding(path, "audio-signature", "audio content is forbidden regardless of extension")
        )
    if b"\x00" in raw[:8192]:
        return findings
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return findings

    for rule, pattern in _content_patterns():
        if pattern.search(text):
            findings.append(Finding(path, rule, "possible PII or credential material"))
    casefolded = text.casefold()
    for identifier in private_identifiers:
        if identifier.casefold() in casefolded:
            findings.append(Finding(path, "known-private-identifier", "matches external denylist"))
    return findings


def scan_paths(paths: Iterable[Path], *, root: Path) -> list[Finding]:
    identifiers = load_private_identifiers(root)
    findings: list[Finding] = []
    for path in paths:
        if path.is_file():
            findings.extend(scan_file(path, root=root, private_identifiers=identifiers))
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Specific files to scan")
    parser.add_argument("--repo", type=Path, help="Repository root (auto-detected by default)")
    parser.add_argument(
        "--require-data-root",
        action="store_true",
        help="also fail unless HMONG_TTS_DATA_ROOT is a valid external directory",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = (args.repo or find_repository_root()).resolve()
    if args.require_data_root:
        try:
            get_data_root(repository_root=root)
        except DataBoundaryError as exc:
            print(f"DATA BOUNDARY ERROR: {exc}", file=sys.stderr)
            return 2
    paths = [path.resolve() for path in args.paths] if args.paths else candidate_files(root)
    try:
        findings = scan_paths(paths, root=root)
    except (DataBoundaryError, OSError) as exc:
        print(f"PRIVACY SCAN ERROR: {exc}", file=sys.stderr)
        return 2
    if findings:
        print(f"Privacy scan failed with {len(findings)} finding(s):", file=sys.stderr)
        for finding in findings:
            print(f"- {finding.render(root)}", file=sys.stderr)
        return 1
    print(f"Privacy scan passed: {len(paths)} candidate file(s); no forbidden material found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
