"""Stable failure and evidence labels shared by milestone M4 subsystems."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

EvidenceScope = Literal["engineering_sanity_check"]
SanitizedText = Annotated[str, Field(min_length=1, max_length=200, pattern=r"^[^\r\n]+$")]


class StrictM4Contract(BaseModel):
    """Reject extra fields and mutation in M4 reports and requests."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class M4FailureCategory(StrEnum):
    """Structured, non-sensitive QC and benchmark failure categories."""

    INVALID_REQUEST = "invalid_request"
    ARTIFACT_BOUNDARY_FAILURE = "artifact_boundary_failure"
    ARTIFACT_COLLISION = "artifact_collision"
    REPORT_WRITE_FAILURE = "report_write_failure"
    CORRUPT_WAV = "corrupt_wav"
    UNSUPPORTED_ENCODING = "unsupported_encoding"
    EMPTY_WAVEFORM = "empty_waveform"
    CHANNEL_MISMATCH = "channel_mismatch"
    INVALID_SAMPLE_RATE = "invalid_sample_rate"
    NONFINITE_SAMPLES = "nonfinite_samples"
    ANALYSIS_FAILURE = "analysis_failure"
    UNKNOWN_OR_UNAPPROVED_MODEL = "unknown_or_unapproved_model"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    DEVICE_UNAVAILABLE = "device_unavailable"
    MODEL_LOAD_FAILURE = "model_load_failure"
    SYNTHESIS_FAILURE = "synthesis_failure"
    INVALID_WAVEFORM = "invalid_waveform"
    RESOURCE_OBSERVATION_UNAVAILABLE = "resource_observation_unavailable"


class M4FailureDetail(StrictM4Contract):
    """A sanitized failure safe for metadata-only reports and CLI output."""

    category: M4FailureCategory
    message: SanitizedText
