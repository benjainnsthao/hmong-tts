"""Strict versioned contracts for non-linguistic waveform QC."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from tts_workbench.evaluation.contracts import (
    EvidenceScope,
    M4FailureDetail,
    SanitizedText,
    StrictM4Contract,
)

MetricValue = bool | int | float | str | tuple[int, ...] | None
QcRuleStatus = Literal["pass", "fail", "not_applicable"]
QcOverallStatus = Literal[
    "structurally_invalid",
    "qc_failing",
    "qc_passing",
    "analysis_failure",
]
QcUnit = Literal[
    "boolean",
    "count",
    "ratio",
    "normalized_amplitude",
    "seconds",
    "hertz",
    "bytes_per_sample",
]


def validate_relative_json_path(value: str) -> str:
    """Normalize a root-relative JSON path without resolving a private root."""
    if "\\" in value:
        raise ValueError("artifact paths must use forward slashes")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("artifact path must be normalized and root-relative")
    if not value.lower().endswith(".json"):
        raise ValueError("report path must end in .json")
    return path.as_posix()


def validate_relative_wav_path(value: str) -> str:
    """Normalize a root-relative WAV path without resolving a private root."""
    if "\\" in value:
        raise ValueError("artifact paths must use forward slashes")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("artifact path must be normalized and root-relative")
    if not value.lower().endswith(".wav"):
        raise ValueError("input path must end in .wav")
    return path.as_posix()


class QcThresholds(StrictM4Contract):
    """Conservative engineering thresholds; never language-quality criteria."""

    schema_version: Literal[1] = 1
    expected_channel_count: Literal[1] = 1
    expected_sample_width_bytes: Literal[2] = 2
    allowed_sample_rates_hz: tuple[Annotated[int, Field(gt=0)], ...]
    clipping_amplitude: float = Field(gt=0.0, le=1.0, allow_inf_nan=False)
    maximum_clipping_ratio: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    minimum_rms_amplitude: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    maximum_absolute_dc_offset: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    near_silence_amplitude: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    maximum_leading_silence_ratio: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    maximum_trailing_silence_ratio: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    maximum_total_near_silence_ratio: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    minimum_frame_count: int = Field(gt=0)
    minimum_duration_seconds: float = Field(gt=0.0, allow_inf_nan=False)

    @field_validator("allowed_sample_rates_hz")
    @classmethod
    def require_unique_sorted_rates(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if not value:
            raise ValueError("at least one allowed sample rate is required")
        if tuple(sorted(set(value))) != value:
            raise ValueError("allowed sample rates must be sorted and unique")
        return value

    @model_validator(mode="after")
    def require_silence_below_clipping(self) -> QcThresholds:
        if self.near_silence_amplitude >= self.clipping_amplitude:
            raise ValueError("near-silence amplitude must be below clipping amplitude")
        return self


class QcRuleResult(StrictM4Contract):
    """Stable result for exactly one structural or engineering rule."""

    rule_id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
    status: QcRuleStatus
    observed_value: MetricValue
    threshold_or_expected_value: MetricValue
    unit: QcUnit
    explanation: SanitizedText
    evidence_scope: EvidenceScope = "engineering_sanity_check"


class WaveformFacts(StrictM4Contract):
    """Measured facts retained even when a structural rule fails."""

    wav_readable: bool
    channel_count: int | None = Field(default=None, ge=0)
    sample_width_bytes: int | None = Field(default=None, ge=0)
    sample_rate_hz: int | None = Field(default=None, ge=0)
    frame_count: int | None = Field(default=None, ge=0)
    sample_count: int | None = Field(default=None, ge=0)
    duration_seconds: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    finite_samples: bool | None = None
    absolute_peak_amplitude: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    clipping_sample_count: int | None = Field(default=None, ge=0)
    clipping_ratio: float | None = Field(default=None, ge=0.0, le=1.0, allow_inf_nan=False)
    rms_amplitude: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    dc_offset: float | None = Field(default=None, allow_inf_nan=False)
    leading_near_silence_seconds: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    leading_near_silence_ratio: float | None = Field(
        default=None, ge=0.0, le=1.0, allow_inf_nan=False
    )
    trailing_near_silence_seconds: float | None = Field(default=None, ge=0.0, allow_inf_nan=False)
    trailing_near_silence_ratio: float | None = Field(
        default=None, ge=0.0, le=1.0, allow_inf_nan=False
    )
    total_near_silence_sample_count: int | None = Field(default=None, ge=0)
    total_near_silence_ratio: float | None = Field(
        default=None, ge=0.0, le=1.0, allow_inf_nan=False
    )


class WaveformQcReport(StrictM4Contract):
    """Complete M4 QC result without raw audio or linguistic conclusions."""

    report_schema_version: Literal[1] = 1
    evidence_scope: EvidenceScope = "engineering_sanity_check"
    source_kind: Literal["in_memory_waveform", "artifact_wav"]
    source_artifact_path: str | None = None
    overall_status: QcOverallStatus
    thresholds: QcThresholds
    facts: WaveformFacts
    rules: tuple[QcRuleResult, ...]
    failure: M4FailureDetail | None = None

    @field_validator("source_artifact_path")
    @classmethod
    def validate_source_path(cls, value: str | None) -> str | None:
        return None if value is None else validate_relative_wav_path(value)

    @model_validator(mode="after")
    def require_consistent_report(self) -> WaveformQcReport:
        if self.source_kind == "artifact_wav" and self.source_artifact_path is None:
            raise ValueError("artifact WAV reports require a root-relative source path")
        if self.source_kind == "in_memory_waveform" and self.source_artifact_path is not None:
            raise ValueError("in-memory reports cannot contain an artifact path")
        if len({rule.rule_id for rule in self.rules}) != len(self.rules):
            raise ValueError("QC rule IDs must be unique")
        failed = [rule for rule in self.rules if rule.status == "fail"]
        if self.overall_status == "qc_passing" and (failed or self.failure is not None):
            raise ValueError("QC-passing reports cannot contain failed rules or a failure")
        if self.overall_status == "qc_failing" and (not failed or self.failure is not None):
            raise ValueError("QC-failing reports require failed rules and no analysis failure")
        if self.overall_status in {"structurally_invalid", "analysis_failure"}:
            if self.failure is None:
                raise ValueError("invalid or failed analysis reports require a structured failure")
        elif self.failure is not None:
            raise ValueError("completed QC reports cannot contain a structured failure")
        return self
