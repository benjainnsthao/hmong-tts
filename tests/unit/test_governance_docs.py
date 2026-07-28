from pathlib import Path


def test_consent_template_contains_required_independent_choices(repository_root: Path) -> None:
    text = (
        repository_root / "docs/history/white_hmong_single_speaker/consent_template.md"
    ).read_text(encoding="utf-8")
    required = [
        "not legal advice",
        "recording sessions",
        "train this tts model",
        "public demo",
        "real recording samples",
        "synthetic samples",
        "model weights",
        "commercial use",
        "translation applications",
        "education applications",
        "retention period",
        "withdrawal",
        "credit and anonymity",
        "impersonation",
    ]
    lowered = text.lower()
    assert all(item in lowered for item in required)


def test_completed_records_are_explicitly_external(repository_root: Path) -> None:
    text = (
        repository_root / "docs/history/white_hmong_single_speaker/consent_template.md"
    ).read_text(encoding="utf-8")
    assert "must remain encrypted outside the repository" in text


def test_white_hmong_native_decisions_remain_deferred(repository_root: Path) -> None:
    text = (repository_root / "docs/deferred/white_hmong_native_validation.md").read_text(
        encoding="utf-8"
    )
    for decision_number in range(1, 9):
        assert f"NV-{decision_number:03}" in text
    assert "No row is approved" in text
