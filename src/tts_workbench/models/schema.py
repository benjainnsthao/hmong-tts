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
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
OwnerDecisionReference = Annotated[str, Field(pattern=r"^docs/[a-z0-9_]+\.json$")]
Architecture = Literal["vits", "orpheus_llama_snac"]
ApprovedUse = Literal["local_noncommercial_inference", "local_noncommercial_research_inference"]
# Schema 2 adds restricted research entries; schema 1 files remain valid unchanged.
RegistrySchemaVersion = Literal[1, 2]


class StrictModel(BaseModel):
    """Reject undocumented registry fields and mutation after validation."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class ModelProvenance(StrictModel):
    """Primary-source and repository-audit references for a model."""

    model_card_url: HttpsUrl
    license_url: HttpsUrl
    audit_reference: Literal["docs/license_matrix.md"]
    audited_on: date


_BLOCKED_LICENSES = {"n/a", "none", "unknown", "unverified"}


class UpstreamLicense(StrictModel):
    """A base-model license whose terms still bind a derivative checkpoint."""

    name: NonEmptyText
    license_url: HttpsUrl
    status: Literal["owner_accepted_for_local_research"]


class UseRestrictions(StrictModel):
    """Owner-recorded limits for an entry that is cleared only for local research."""

    scope: Literal["local_noncommercial_research_only"]
    output_policy: Literal["outputs_external_not_shared"]
    public_use: Literal["not_cleared"]
    owner_decision_reference: OwnerDecisionReference
    upstream_licenses: tuple[UpstreamLicense, ...] = Field(min_length=1)
    open_risks: tuple[NonEmptyText, ...] = Field(min_length=1)


class ModelComponent(StrictModel):
    """A separately licensed runtime artifact, loaded only from pinned safetensors."""

    role: Literal["audio_codec"]
    repository: RepositoryId
    revision: ImmutableRevision
    weight_license: NonEmptyText
    license_url: HttpsUrl
    source_file: NonEmptyText
    source_sha256: Sha256
    conversion: Literal["torch_load_weights_only_true_to_safetensors", "none"]
    loaded_format: Literal["safetensors"]
    loaded_sha256: Sha256

    @model_validator(mode="after")
    def require_audited_license(self) -> ModelComponent:
        if self.weight_license.strip().casefold() in _BLOCKED_LICENSES:
            raise ValueError("component weight_license must name an audited license")
        if self.conversion == "none" and self.loaded_sha256 != self.source_sha256:
            raise ValueError("an unconverted component must load its source file")
        return self


class ModelEntry(StrictModel):
    """One checkpoint eligible for the current workbench scope."""

    model_id: ModelId
    provider: NonEmptyText
    repository: RepositoryId
    revision: ImmutableRevision
    documented_language_tag: LanguageTag
    language_tag_standard: Literal["ISO 639-3"]
    architecture: Architecture
    weight_license: NonEmptyText
    approved_use: ApprovedUse
    redistribution_status: Literal["weights_not_redistributed"]
    prompt_set_reference: PromptSetReference
    language_quality_status: Literal["not_evaluated"]
    provenance: ModelProvenance
    use_restrictions: UseRestrictions | None = None
    components: tuple[ModelComponent, ...] = ()

    @model_validator(mode="after")
    def require_audited_license(self) -> ModelEntry:
        if self.weight_license.strip().casefold() in _BLOCKED_LICENSES:
            raise ValueError("weight_license must name an audited license")
        return self

    @model_validator(mode="after")
    def require_research_restrictions(self) -> ModelEntry:
        research = self.approved_use == "local_noncommercial_research_inference"
        if research != (self.use_restrictions is not None):
            raise ValueError("research-only use requires, and only permits, use_restrictions")
        codecs = [item for item in self.components if item.role == "audio_codec"]
        if self.architecture == "orpheus_llama_snac":
            if not research or len(codecs) != 1 or len(self.components) != 1:
                raise ValueError("orpheus_llama_snac requires research use and one audio codec")
        elif self.components:
            raise ValueError("components are only defined for orpheus_llama_snac")
        return self

    @property
    def uses_schema_2_features(self) -> bool:
        return (
            self.architecture != "vits"
            or self.approved_use != "local_noncommercial_inference"
            or self.use_restrictions is not None
            or bool(self.components)
        )


class ModelRegistry(StrictModel):
    """Versioned registry with unique model and immutable artifact identities."""

    schema_version: RegistrySchemaVersion
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

    @model_validator(mode="after")
    def require_declared_schema_features(self) -> ModelRegistry:
        if self.schema_version == 1 and any(m.uses_schema_2_features for m in self.models):
            raise ValueError("restricted research entries require registry schema_version 2")
        return self

    def by_architecture(self, architecture: str) -> tuple[ModelEntry, ...]:
        """Return entries a specific adapter family may load, in registry order."""
        return tuple(model for model in self.models if model.architecture == architecture)

    def by_id(self, model_id: str) -> ModelEntry:
        """Return one registered model without accepting repository aliases."""
        for model in self.models:
            if model.model_id == model_id:
                return model
        raise KeyError(f"Unknown registered model: {model_id}")
