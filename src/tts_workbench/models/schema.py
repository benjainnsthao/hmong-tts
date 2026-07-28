"""Strict schema for audited public TTS model references."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonEmptyText = Annotated[str, Field(min_length=1, pattern=r"^.*\S.*$")]
ModelId = Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
RepositoryId = Annotated[
    str,
    Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$"),
]
ImmutableRevision = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
LanguageTag = Annotated[str, Field(pattern=r"^[a-z]{3}$")]
HttpsUrl = Annotated[str, Field(pattern=r"^https://\S+$")]
PromptSetReference = Annotated[
    str,
    Field(pattern=r"^(?:builtin|external):[a-z0-9]+(?:[._-][a-z0-9]+)*$"),
]


class StrictModel(BaseModel):
    """Reject undocumented registry fields and mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class ModelProvenance(StrictModel):
    """Primary-source and repository-audit references for a model."""

    model_card_url: HttpsUrl
    license_url: HttpsUrl
    audit_reference: Literal["docs/license_matrix.md"]
    audited_on: date


class ModelEntry(StrictModel):
    """One checkpoint eligible for the current workbench scope."""

    model_id: ModelId
    provider: NonEmptyText
    repository: RepositoryId
    revision: ImmutableRevision
    documented_language_tag: LanguageTag
    language_tag_standard: Literal["ISO 639-3"]
    architecture: Literal["vits"]
    weight_license: NonEmptyText
    approved_use: Literal["local_noncommercial_inference"]
    redistribution_status: Literal["weights_not_redistributed"]
    prompt_set_reference: PromptSetReference
    language_quality_status: Literal["not_evaluated"]
    provenance: ModelProvenance

    @model_validator(mode="after")
    def require_audited_license(self) -> ModelEntry:
        blocked_values = {"n/a", "none", "unknown", "unverified"}
        if self.weight_license.strip().casefold() in blocked_values:
            raise ValueError("weight_license must name an audited license")
        return self


class ModelRegistry(StrictModel):
    """Versioned registry with unique model and immutable artifact identities."""

    schema_version: Literal[1]
    models: list[ModelEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_entries(self) -> ModelRegistry:
        model_ids = [model.model_id for model in self.models]
        if len(model_ids) != len(set(model_ids)):
            raise ValueError("model_id values must be unique")

        artifacts = [(model.repository, model.revision) for model in self.models]
        if len(artifacts) != len(set(artifacts)):
            raise ValueError("repository and revision pairs must be unique")
        return self

    def by_id(self, model_id: str) -> ModelEntry:
        """Return one registered model without accepting repository aliases."""
        for model in self.models:
            if model.model_id == model_id:
                return model
        raise KeyError(f"Unknown registered model: {model_id}")
