from __future__ import annotations

import json
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


def test_committed_registry_restricts_its_only_hmong_entry_to_local_research(
    repository_root: Path,
) -> None:
    registry = load_model_registry(repository_root=repository_root)

    assert registry.schema_version == 2
    assert {model.model_id for model in registry.models} == {
        "mms-eng",
        "mms-vie",
        "orpheus-hmong-3b",
    }
    assert {model.documented_language_tag for model in registry.models} == {"eng", "vie", "mww"}
    assert {model.language_quality_status for model in registry.models} == {"not_evaluated"}
    assert all(model.revision not in {"main", "master"} for model in registry.models)
    for model_id in ("mms-eng", "mms-vie"):
        entry = registry.by_id(model_id)
        assert entry.architecture == "vits"
        assert entry.approved_use == "local_noncommercial_inference"
        assert entry.use_restrictions is None and entry.components == ()

    hmong = registry.by_id("orpheus-hmong-3b")
    assert hmong.approved_use == "local_noncommercial_research_inference"
    assert hmong.revision == "464d34449a778b1a6d9506bc10bd4e00f752c5c8"
    restrictions = hmong.use_restrictions
    assert restrictions is not None
    assert restrictions.output_policy == "outputs_external_not_shared"
    assert restrictions.public_use == "not_cleared"
    decision = json.loads(
        (repository_root / restrictions.owner_decision_reference).read_text(encoding="utf-8")
    )
    assert decision["owner"] == "benjainnsthao"
    assert decision["scope"] == "local_noncommercial_research_only"
    assert decision["public_use_cleared"] is False
    assert decision["decisions"]["D2"]["revision"] == hmong.revision
    (codec,) = hmong.components
    assert codec.revision == decision["decisions"]["D3"]["revision"]
    assert codec.loaded_format == "safetensors"
    assert codec.conversion == "torch_load_weights_only_true_to_safetensors"
    assert codec.loaded_sha256 != codec.source_sha256


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


def schema_2_registry(**overrides: Any) -> dict[str, Any]:
    from tests.fakes.inference import orpheus_model

    return {"schema_version": 2, "models": [valid_model(), orpheus_model(**overrides)]}


def test_schema_2_accepts_restricted_research_entry_and_existing_entries() -> None:
    registry = ModelRegistry.model_validate(schema_2_registry())
    entry = registry.by_id("fixture-orpheus")
    assert entry.uses_schema_2_features
    assert not registry.by_id("fixture-eng").uses_schema_2_features
    assert [item.model_id for item in registry.by_architecture("vits")] == ["fixture-eng"]
    assert ModelRegistry.model_validate({"schema_version": 2, "models": [valid_model()]})


def test_schema_1_cannot_hide_restricted_research_entries() -> None:
    payload = schema_2_registry()
    payload["schema_version"] = 1
    with pytest.raises(ValidationError, match="schema_version 2"):
        ModelRegistry.model_validate(payload)


@pytest.mark.parametrize(
    "overrides",
    [
        {"use_restrictions": None},
        {"approved_use": "local_noncommercial_inference"},
        {"components": []},
        {"architecture": "vits"},
        {"language_quality_status": "evaluated"},
        {"approved_use": "public_inference"},
    ],
)
def test_research_restrictions_codec_and_quality_are_mandatory(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(schema_2_registry(**overrides))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("output_policy", "outputs_shareable"),
        ("public_use", "cleared"),
        ("owner_decision_reference", "/absolute/private/decision.json"),
        ("upstream_licenses", []),
        ("open_risks", []),
    ],
)
def test_use_restrictions_cannot_be_relaxed(field: str, value: object) -> None:
    from tests.fakes.inference import orpheus_model

    restrictions = deepcopy(orpheus_model()["use_restrictions"])
    restrictions[field] = value
    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(schema_2_registry(use_restrictions=restrictions))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("loaded_format", "pickle"),
        ("weight_license", "unknown"),
        ("revision", "main"),
        ("source_sha256", "not-a-digest"),
        ("conversion", "torch_load_full_unpickle"),
    ],
)
def test_codec_component_requires_pinned_audited_safetensors(field: str, value: object) -> None:
    from tests.fakes.inference import orpheus_model

    (component,) = deepcopy(orpheus_model()["components"])
    component[field] = value
    with pytest.raises(ValidationError):
        ModelRegistry.model_validate(schema_2_registry(components=[component]))


def test_unconverted_component_must_load_its_source_digest() -> None:
    from tests.fakes.inference import orpheus_model

    (component,) = deepcopy(orpheus_model()["components"])
    component["conversion"] = "none"
    with pytest.raises(ValidationError, match="source file"):
        ModelRegistry.model_validate(schema_2_registry(components=[component]))
    component["loaded_sha256"] = component["source_sha256"]
    assert ModelRegistry.model_validate(schema_2_registry(components=[component]))


def test_vits_entries_cannot_carry_components_or_restrictions() -> None:
    from tests.fakes.inference import orpheus_model

    model = valid_model()
    model["components"] = orpheus_model()["components"]
    with pytest.raises(ValidationError, match="components"):
        ModelRegistry.model_validate({"schema_version": 2, "models": [model]})
    model = valid_model()
    model["use_restrictions"] = orpheus_model()["use_restrictions"]
    with pytest.raises(ValidationError, match="use_restrictions"):
        ModelRegistry.model_validate({"schema_version": 2, "models": [model]})


def test_mms_parser_never_offers_restricted_research_entries(repository_root: Path) -> None:
    registry = load_model_registry(repository_root=repository_root)
    with pytest.raises(SystemExit):
        build_parser(registry).parse_args(["--model", "orpheus-hmong-3b"])
