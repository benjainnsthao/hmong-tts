from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from tts_workbench.inference.mms_smoke import build_parser
from tts_workbench.models.registry import load_model_registry, main
from tts_workbench.models.schema import ModelRegistry

REVISION = "1" * 40


def valid_model() -> dict[str, Any]:
    return {
        "model_id": "fixture-eng",
        "provider": "Synthetic Provider",
        "repository": "synthetic/fixture-eng",
        "revision": REVISION,
        "documented_language_tag": "eng",
        "language_tag_standard": "ISO 639-3",
        "architecture": "vits",
        "weight_license": "Apache-2.0",
        "approved_use": "local_noncommercial_inference",
        "redistribution_status": "weights_not_redistributed",
        "prompt_set_reference": "builtin:synthetic-fixture-v1",
        "language_quality_status": "not_evaluated",
        "provenance": {
            "model_card_url": "https://example.test/model-card",
            "license_url": "https://example.test/license",
            "audit_reference": "docs/license_matrix.md",
            "audited_on": "2026-07-14",
        },
    }


def valid_registry() -> dict[str, Any]:
    return {"schema_version": 1, "models": [valid_model()]}


def write_registry(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "registry.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_committed_registry_contains_only_audited_non_hmong_models(
    repository_root: Path,
) -> None:
    registry = load_model_registry(repository_root=repository_root)

    assert {model.model_id for model in registry.models} == {"mms-eng", "mms-vie"}
    assert {model.documented_language_tag for model in registry.models} == {"eng", "vie"}
    assert {model.language_quality_status for model in registry.models} == {"not_evaluated"}
    assert all(model.revision not in {"main", "master"} for model in registry.models)


def test_mms_parser_exposes_registry_ids(repository_root: Path) -> None:
    registry = load_model_registry(repository_root=repository_root)

    assert build_parser(registry).parse_args([]).model == "mms-eng"
    assert build_parser(registry).parse_args(["--model", "mms-vie"]).model == "mms-vie"


def test_registry_lookup_rejects_unknown_id() -> None:
    registry = ModelRegistry.model_validate(valid_registry())

    with pytest.raises(KeyError, match="Unknown registered model"):
        registry.by_id("missing-model")


@pytest.mark.parametrize("revision", ["main", "master", "v1.0.0", "abc123", "A" * 40])
def test_rejects_mutable_or_noncanonical_revision(revision: str) -> None:
    payload = valid_registry()
    payload["models"][0]["revision"] = revision

    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(payload)


@pytest.mark.parametrize("field", ["provenance", "weight_license", "prompt_set_reference"])
def test_rejects_missing_provenance_or_policy_field(field: str) -> None:
    payload = valid_registry()
    del payload["models"][0][field]

    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(payload)


@pytest.mark.parametrize("license_name", ["", "unknown", "unverified", "n/a", "none"])
def test_rejects_missing_or_unaudited_weight_license(license_name: str) -> None:
    payload = valid_registry()
    payload["models"][0]["weight_license"] = license_name

    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(payload)


def test_rejects_duplicate_model_ids() -> None:
    payload = valid_registry()
    duplicate = deepcopy(payload["models"][0])
    duplicate["repository"] = "synthetic/different-artifact"
    duplicate["revision"] = "2" * 40
    payload["models"].append(duplicate)

    with pytest.raises(ValidationError, match="model_id values must be unique"):
        ModelRegistry.model_validate(payload)


def test_rejects_duplicate_repository_revisions() -> None:
    payload = valid_registry()
    duplicate = deepcopy(payload["models"][0])
    duplicate["model_id"] = "different-id"
    payload["models"].append(duplicate)

    with pytest.raises(ValidationError, match="repository and revision pairs must be unique"):
        ModelRegistry.model_validate(payload)


def test_rejects_unapproved_use() -> None:
    payload = valid_registry()
    payload["models"][0]["approved_use"] = "training"

    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(payload)


@pytest.mark.parametrize("claim", ["supported", "native_validated", "production_ready"])
def test_rejects_language_quality_claims(claim: str) -> None:
    payload = valid_registry()
    payload["models"][0]["language_quality_status"] = claim

    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(payload)


def test_rejects_undeclared_language_capability_field() -> None:
    payload = valid_registry()
    payload["models"][0]["white_hmong_support"] = True

    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(payload)


def test_validate_command_reads_only_metadata(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_registry(tmp_path, valid_registry())

    assert main(["--registry", str(path), "validate"]) == 0
    assert "PASS model_registry: schema_version=1 models=1" in capsys.readouterr().out


def test_list_command_reports_policy_status(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_registry(tmp_path, valid_registry())

    assert main(["--registry", str(path), "list"]) == 0
    output = capsys.readouterr().out
    assert "fixture-eng" in output
    assert "local_noncommercial_inference" in output
    assert "not_evaluated" in output


def test_command_rejects_invalid_registry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = valid_registry()
    payload["models"][0]["revision"] = "main"
    path = write_registry(tmp_path, payload)

    assert main(["--registry", str(path), "validate"]) == 2
    assert "MODEL REGISTRY ERROR" in capsys.readouterr().err
