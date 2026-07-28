from pathlib import Path


def test_historical_white_hmong_materials_remain_archived(repository_root: Path) -> None:
    archive = repository_root / "docs/history/white_hmong_single_speaker"
    required = {
        "PROJECT_STATUS-v0.1.md",
        "WHITE_HMONG_TTS_PROJECT_PLAN.md",
        "consent_template.md",
        "dataset_statement.md",
        "model_card_untrained.md",
        "phase1_governance_handoff.md",
        "private_data_layout.md",
        "recording_readiness_checklist.md",
        "configs/data_private_mvp.yaml",
        "configs/eval_mvp.yaml",
        "configs/model_mms_vits.yaml",
        "configs/train_mvp.yaml",
    }

    assert all((archive / relative_path).is_file() for relative_path in required)


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


def test_m3_contract_documentation_preserves_scope_boundary(repository_root: Path) -> None:
    text = (repository_root / "docs/inference_contract.md").read_text(encoding="utf-8")

    assert "manifest the commit marker" in text
    assert "Raw prompt text" in text
    assert "do not establish" in text
    assert "NV-001 through NV-008 remain" in text
