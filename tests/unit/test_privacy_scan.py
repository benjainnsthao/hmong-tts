from pathlib import Path

import pytest

from tts_workbench.privacy.scan import scan_file


def write_fixture(tmp_path: Path, name: str, content: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(content)
    return path


@pytest.mark.parametrize(
    "name", ["voice.wav", "voice.flac", "weights.safetensors", "completed_record.pdf"]
)
def test_rejects_forbidden_artifact_extensions(tmp_path: Path, name: str) -> None:
    path = write_fixture(tmp_path, name, b"synthetic fixture")
    assert scan_file(path, root=tmp_path)


def test_rejects_renamed_wave_by_magic_bytes(tmp_path: Path) -> None:
    path = write_fixture(tmp_path, "renamed.dat", b"RIFF\x00\x00\x00\x00WAVEfmt ")
    rules = {finding.rule for finding in scan_file(path, root=tmp_path)}
    assert "audio-signature" in rules


@pytest.mark.parametrize(
    ("name", "value", "expected_rule"),
    [
        ("notes.txt", "speaker" + "@example.test", "email-address"),
        ("notes.txt", "555" + "-123-4567", "us-phone-number"),
        ("notes.txt", "123" + "-45-6789", "us-ssn"),
        ("notes.txt", "AK" + "IA" + "A" * 16, "aws-access-key"),
        ("notes.txt", "hf" + "_" + "a" * 24, "huggingface-token"),
        ("signed_consent.pdf", "blank", "consent-record"),
    ],
)
def test_rejects_pii_credentials_and_consent(
    tmp_path: Path, name: str, value: str, expected_rule: str
) -> None:
    path = write_fixture(tmp_path, name, value.encode())
    rules = {finding.rule for finding in scan_file(path, root=tmp_path)}
    assert expected_rule in rules


def test_rejects_external_known_identifier(tmp_path: Path) -> None:
    path = write_fixture(tmp_path, "notes.txt", b"Synthetic Person Identifier")
    rules = {
        finding.rule
        for finding in scan_file(
            path,
            root=tmp_path,
            private_identifiers=["Synthetic Person Identifier"],
        )
    }
    assert "known-private-identifier" in rules


def test_allows_clean_synthetic_text(tmp_path: Path) -> None:
    path = write_fixture(tmp_path, "fixture.txt", b"synthetic non-language fixture")
    assert scan_file(path, root=tmp_path) == []
