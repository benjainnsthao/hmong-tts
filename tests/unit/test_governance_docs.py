from pathlib import Path


def test_consent_template_contains_required_independent_choices(repository_root: Path) -> None:
    text = (repository_root / "docs/templates/consent_template.md").read_text(encoding="utf-8")
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
    text = (repository_root / "docs/templates/consent_template.md").read_text(encoding="utf-8")
    assert "must remain encrypted outside the repository" in text
