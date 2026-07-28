"""Deterministic non-linguistic waveform engineering checks."""

from __future__ import annotations

import math
import struct
import wave
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from tts_workbench.artifacts.paths import (
    ARTIFACT_ROOT_ENV,
    get_artifact_root,
    require_under_artifact_root,
)
from tts_workbench.evaluation.contracts import M4FailureCategory, M4FailureDetail
from tts_workbench.inference.contracts import WaveformResult
from tts_workbench.qc.contracts import (
    MetricValue,
    QcOverallStatus,
    QcRuleResult,
    QcThresholds,
    QcUnit,
    WaveformFacts,
    WaveformQcReport,
    validate_relative_wav_path,
)

_RULE_ORDER = (
    "wav_readable",
    "channel_count",
    "sample_width_bytes",
    "sample_rate_hz",
    "minimum_frame_count",
    "minimum_duration_seconds",
    "finite_samples",
    "absolute_peak_amplitude",
    "clipping_ratio",
    "minimum_rms_amplitude",
    "absolute_dc_offset",
    "leading_near_silence_ratio",
    "trailing_near_silence_ratio",
    "total_near_silence_ratio",
)


def _rule(
    rule_id: str,
    status: str,
    observed: MetricValue,
    expected: MetricValue,
    unit: QcUnit,
    explanation: str,
) -> QcRuleResult:
    return QcRuleResult(
        rule_id=rule_id,
        status=status,  # type: ignore[arg-type]
        observed_value=observed,
        threshold_or_expected_value=expected,
        unit=unit,
        explanation=explanation,
    )


def _not_applicable(rule_id: str, thresholds: QcThresholds) -> QcRuleResult:
    units: dict[str, QcUnit] = {
        "wav_readable": "boolean",
        "channel_count": "count",
        "sample_width_bytes": "bytes_per_sample",
        "sample_rate_hz": "hertz",
        "minimum_frame_count": "count",
        "minimum_duration_seconds": "seconds",
        "finite_samples": "boolean",
        "absolute_peak_amplitude": "normalized_amplitude",
        "clipping_ratio": "ratio",
        "minimum_rms_amplitude": "normalized_amplitude",
        "absolute_dc_offset": "normalized_amplitude",
        "leading_near_silence_ratio": "ratio",
        "trailing_near_silence_ratio": "ratio",
        "total_near_silence_ratio": "ratio",
    }
    expected: dict[str, MetricValue] = {
        "wav_readable": True,
        "channel_count": thresholds.expected_channel_count,
        "sample_width_bytes": thresholds.expected_sample_width_bytes,
        "sample_rate_hz": thresholds.allowed_sample_rates_hz,
        "minimum_frame_count": thresholds.minimum_frame_count,
        "minimum_duration_seconds": thresholds.minimum_duration_seconds,
        "finite_samples": True,
        "absolute_peak_amplitude": 1.0,
        "clipping_ratio": thresholds.maximum_clipping_ratio,
        "minimum_rms_amplitude": thresholds.minimum_rms_amplitude,
        "absolute_dc_offset": thresholds.maximum_absolute_dc_offset,
        "leading_near_silence_ratio": thresholds.maximum_leading_silence_ratio,
        "trailing_near_silence_ratio": thresholds.maximum_trailing_silence_ratio,
        "total_near_silence_ratio": thresholds.maximum_total_near_silence_ratio,
    }
    return _rule(
        rule_id,
        "not_applicable",
        None,
        expected[rule_id],
        units[rule_id],
        "Rule was not applicable because prerequisite structural evidence was unavailable.",
    )


def _failure(category: M4FailureCategory, message: str) -> M4FailureDetail:
    return M4FailureDetail(category=category, message=message)


def _normalized_pcm16(raw_frames: bytes) -> tuple[float, ...]:
    if len(raw_frames) % 2:
        raise ValueError("PCM16 frame data was incomplete.")
    sample_count = len(raw_frames) // 2
    return tuple(sample / 32768.0 for sample in struct.unpack(f"<{sample_count}h", raw_frames))


class WaveformQcAnalyzer:
    """Analyze in-memory or committed mono PCM16 audio without affecting commitment."""

    def __init__(self, thresholds: QcThresholds) -> None:
        self.thresholds = thresholds

    def analyze_waveform(self, waveform: WaveformResult) -> WaveformQcReport:
        """Analyze an uncommitted M3 waveform on its in-memory numeric scale."""

        base_rules = [
            _rule(
                "wav_readable",
                "not_applicable",
                None,
                None,
                "boolean",
                "WAV readability does not apply to an in-memory waveform.",
            ),
            _rule(
                "channel_count",
                "pass"
                if waveform.channel_count == self.thresholds.expected_channel_count
                else "fail",
                waveform.channel_count,
                self.thresholds.expected_channel_count,
                "count",
                "Channel count must match the configured mono engineering boundary.",
            ),
            _rule(
                "sample_width_bytes",
                "not_applicable",
                None,
                self.thresholds.expected_sample_width_bytes,
                "bytes_per_sample",
                "Sample width does not apply to floating-point in-memory samples.",
            ),
            _rule(
                "sample_rate_hz",
                "pass"
                if waveform.sample_rate in self.thresholds.allowed_sample_rates_hz
                else "fail",
                waveform.sample_rate,
                self.thresholds.allowed_sample_rates_hz,
                "hertz",
                "Sample rate must be one of the configured engineering rates.",
            ),
        ]
        if waveform.channel_count != self.thresholds.expected_channel_count:
            return self._structural_report(
                source_kind="in_memory_waveform",
                source_path=None,
                facts=WaveformFacts(
                    wav_readable=True,
                    channel_count=waveform.channel_count,
                    sample_rate_hz=max(waveform.sample_rate, 0),
                    frame_count=len(waveform.samples),
                    sample_count=len(waveform.samples),
                ),
                rules=base_rules,
                category=M4FailureCategory.CHANNEL_MISMATCH,
                message="Waveform channel count did not match the configured boundary.",
            )
        if waveform.sample_rate not in self.thresholds.allowed_sample_rates_hz:
            return self._structural_report(
                source_kind="in_memory_waveform",
                source_path=None,
                facts=WaveformFacts(
                    wav_readable=True,
                    channel_count=waveform.channel_count,
                    sample_rate_hz=max(waveform.sample_rate, 0),
                    frame_count=len(waveform.samples),
                    sample_count=len(waveform.samples),
                ),
                rules=base_rules,
                category=M4FailureCategory.INVALID_SAMPLE_RATE,
                message="Waveform sample rate was invalid or not configured for QC.",
            )
        if not waveform.samples:
            return self._structural_report(
                source_kind="in_memory_waveform",
                source_path=None,
                facts=WaveformFacts(
                    wav_readable=True,
                    channel_count=waveform.channel_count,
                    sample_rate_hz=waveform.sample_rate,
                    frame_count=0,
                    sample_count=0,
                    duration_seconds=0.0,
                    finite_samples=True,
                ),
                rules=base_rules,
                category=M4FailureCategory.EMPTY_WAVEFORM,
                message="Waveform contained no samples.",
            )
        if not all(math.isfinite(sample) for sample in waveform.samples):
            finite_rule = _rule(
                "finite_samples",
                "fail",
                False,
                True,
                "boolean",
                "Every analyzed sample must be finite.",
            )
            return self._structural_report(
                source_kind="in_memory_waveform",
                source_path=None,
                facts=WaveformFacts(
                    wav_readable=True,
                    channel_count=waveform.channel_count,
                    sample_rate_hz=waveform.sample_rate,
                    frame_count=len(waveform.samples),
                    sample_count=len(waveform.samples),
                    duration_seconds=len(waveform.samples) / waveform.sample_rate,
                    finite_samples=False,
                ),
                rules=[*base_rules, finite_rule],
                category=M4FailureCategory.NONFINITE_SAMPLES,
                message="Waveform contained one or more nonfinite samples.",
            )
        try:
            return self._analyze_samples(
                samples=waveform.samples,
                sample_rate=waveform.sample_rate,
                sample_width=None,
                source_kind="in_memory_waveform",
                source_path=None,
                prefix_rules=base_rules,
            )
        except (ArithmeticError, ValidationError, ValueError):
            return self._analysis_failure_report(
                source_kind="in_memory_waveform",
                source_path=None,
                facts=WaveformFacts(
                    wav_readable=True,
                    channel_count=waveform.channel_count,
                    sample_rate_hz=waveform.sample_rate,
                    frame_count=len(waveform.samples),
                    sample_count=len(waveform.samples),
                    duration_seconds=len(waveform.samples) / waveform.sample_rate,
                    finite_samples=True,
                ),
                rules=base_rules,
            )

    def analyze_artifact_wav(
        self,
        relative_wav_path: str,
        *,
        artifact_root: Path | None = None,
        repository_root: Path | None = None,
    ) -> WaveformQcReport:
        """Reopen and analyze one artifact-root-relative WAV."""

        normalized_path = validate_relative_wav_path(relative_wav_path)
        root = (
            get_artifact_root(repository_root=repository_root)
            if artifact_root is None
            else get_artifact_root(
                environ={ARTIFACT_ROOT_ENV: str(artifact_root)},
                repository_root=repository_root,
            )
        )
        wav_path = require_under_artifact_root(Path(normalized_path), artifact_root=root)
        try:
            with wave.open(str(wav_path), "rb") as handle:
                channel_count = handle.getnchannels()
                sample_width = handle.getsampwidth()
                sample_rate = handle.getframerate()
                frame_count = handle.getnframes()
                compression = handle.getcomptype()
                raw_frames = handle.readframes(frame_count)
        except (EOFError, OSError, wave.Error):
            return self._structural_report(
                source_kind="artifact_wav",
                source_path=normalized_path,
                facts=WaveformFacts(wav_readable=False),
                rules=[
                    _rule(
                        "wav_readable",
                        "fail",
                        False,
                        True,
                        "boolean",
                        "Artifact was not a readable WAV file.",
                    )
                ],
                category=M4FailureCategory.CORRUPT_WAV,
                message="Artifact could not be read as a WAV file.",
            )

        base_rules = [
            _rule(
                "wav_readable",
                "pass",
                True,
                True,
                "boolean",
                "Artifact was reopened as a WAV file.",
            ),
            _rule(
                "channel_count",
                "pass" if channel_count == self.thresholds.expected_channel_count else "fail",
                channel_count,
                self.thresholds.expected_channel_count,
                "count",
                "Channel count must match the configured mono engineering boundary.",
            ),
            _rule(
                "sample_width_bytes",
                "pass"
                if sample_width == self.thresholds.expected_sample_width_bytes
                and compression == "NONE"
                else "fail",
                sample_width,
                self.thresholds.expected_sample_width_bytes,
                "bytes_per_sample",
                "Only uncompressed PCM16 WAV input is supported by M4 QC.",
            ),
            _rule(
                "sample_rate_hz",
                "pass" if sample_rate in self.thresholds.allowed_sample_rates_hz else "fail",
                sample_rate,
                self.thresholds.allowed_sample_rates_hz,
                "hertz",
                "Sample rate must be one of the configured engineering rates.",
            ),
        ]
        facts = WaveformFacts(
            wav_readable=True,
            channel_count=channel_count,
            sample_width_bytes=sample_width,
            sample_rate_hz=sample_rate,
            frame_count=frame_count,
            sample_count=frame_count * channel_count,
            duration_seconds=frame_count / sample_rate if sample_rate > 0 else 0.0,
        )
        if channel_count != self.thresholds.expected_channel_count:
            return self._structural_report(
                source_kind="artifact_wav",
                source_path=normalized_path,
                facts=facts,
                rules=base_rules,
                category=M4FailureCategory.CHANNEL_MISMATCH,
                message="WAV channel count did not match the configured boundary.",
            )
        if sample_width != self.thresholds.expected_sample_width_bytes or compression != "NONE":
            return self._structural_report(
                source_kind="artifact_wav",
                source_path=normalized_path,
                facts=facts,
                rules=base_rules,
                category=M4FailureCategory.UNSUPPORTED_ENCODING,
                message="WAV encoding was not supported uncompressed PCM16.",
            )
        if sample_rate not in self.thresholds.allowed_sample_rates_hz:
            return self._structural_report(
                source_kind="artifact_wav",
                source_path=normalized_path,
                facts=facts,
                rules=base_rules,
                category=M4FailureCategory.INVALID_SAMPLE_RATE,
                message="WAV sample rate was invalid or not configured for QC.",
            )
        if frame_count == 0:
            return self._structural_report(
                source_kind="artifact_wav",
                source_path=normalized_path,
                facts=facts.model_copy(update={"finite_samples": True}),
                rules=base_rules,
                category=M4FailureCategory.EMPTY_WAVEFORM,
                message="WAV contained no audio frames.",
            )
        if len(raw_frames) != frame_count * channel_count * sample_width:
            return self._structural_report(
                source_kind="artifact_wav",
                source_path=normalized_path,
                facts=facts,
                rules=base_rules,
                category=M4FailureCategory.CORRUPT_WAV,
                message="WAV frame data was incomplete.",
            )
        try:
            samples = _normalized_pcm16(raw_frames)
        except (struct.error, ValueError):
            return self._structural_report(
                source_kind="artifact_wav",
                source_path=normalized_path,
                facts=facts,
                rules=base_rules,
                category=M4FailureCategory.CORRUPT_WAV,
                message="WAV frame data could not be decoded as PCM16.",
            )
        try:
            return self._analyze_samples(
                samples=samples,
                sample_rate=sample_rate,
                sample_width=sample_width,
                source_kind="artifact_wav",
                source_path=normalized_path,
                prefix_rules=base_rules,
            )
        except (ArithmeticError, ValidationError, ValueError):
            return self._analysis_failure_report(
                source_kind="artifact_wav",
                source_path=normalized_path,
                facts=facts.model_copy(update={"finite_samples": True}),
                rules=base_rules,
            )

    def _analyze_samples(
        self,
        *,
        samples: Sequence[float],
        sample_rate: int,
        sample_width: int | None,
        source_kind: str,
        source_path: str | None,
        prefix_rules: list[QcRuleResult],
    ) -> WaveformQcReport:
        count = len(samples)
        duration = count / sample_rate
        absolute_values = tuple(abs(sample) for sample in samples)
        peak = max(absolute_values)
        clipping_count = sum(
            value >= self.thresholds.clipping_amplitude for value in absolute_values
        )
        clipping_ratio = clipping_count / count
        rms = math.sqrt(sum(sample * sample for sample in samples) / count)
        dc_offset = sum(samples) / count
        near_silence = tuple(
            value <= self.thresholds.near_silence_amplitude for value in absolute_values
        )
        leading_count = next(
            (index for index, quiet in enumerate(near_silence) if not quiet),
            count,
        )
        trailing_count = next(
            (index for index, quiet in enumerate(reversed(near_silence)) if not quiet),
            count,
        )
        total_quiet = sum(near_silence)
        leading_ratio = leading_count / count
        trailing_ratio = trailing_count / count
        total_ratio = total_quiet / count

        facts = WaveformFacts(
            wav_readable=True,
            channel_count=1,
            sample_width_bytes=sample_width,
            sample_rate_hz=sample_rate,
            frame_count=count,
            sample_count=count,
            duration_seconds=duration,
            finite_samples=True,
            absolute_peak_amplitude=peak,
            clipping_sample_count=clipping_count,
            clipping_ratio=clipping_ratio,
            rms_amplitude=rms,
            dc_offset=dc_offset,
            leading_near_silence_seconds=leading_count / sample_rate,
            leading_near_silence_ratio=leading_ratio,
            trailing_near_silence_seconds=trailing_count / sample_rate,
            trailing_near_silence_ratio=trailing_ratio,
            total_near_silence_sample_count=total_quiet,
            total_near_silence_ratio=total_ratio,
        )
        rules = [
            *prefix_rules,
            _rule(
                "minimum_frame_count",
                "pass" if count >= self.thresholds.minimum_frame_count else "fail",
                count,
                self.thresholds.minimum_frame_count,
                "count",
                "Frame count must meet the configured analysis minimum.",
            ),
            _rule(
                "minimum_duration_seconds",
                "pass" if duration >= self.thresholds.minimum_duration_seconds else "fail",
                duration,
                self.thresholds.minimum_duration_seconds,
                "seconds",
                "Duration must meet the configured analysis minimum.",
            ),
            _rule(
                "finite_samples",
                "pass",
                True,
                True,
                "boolean",
                "Every analyzed sample was finite.",
            ),
            _rule(
                "absolute_peak_amplitude",
                "pass" if peak <= 1.0 else "fail",
                peak,
                1.0,
                "normalized_amplitude",
                "Absolute peak is reported on the normalized amplitude scale.",
            ),
            _rule(
                "clipping_ratio",
                "pass" if clipping_ratio <= self.thresholds.maximum_clipping_ratio else "fail",
                clipping_ratio,
                self.thresholds.maximum_clipping_ratio,
                "ratio",
                "Samples at or above the clipping amplitude contribute to this ratio.",
            ),
            _rule(
                "minimum_rms_amplitude",
                "pass" if rms >= self.thresholds.minimum_rms_amplitude else "fail",
                rms,
                self.thresholds.minimum_rms_amplitude,
                "normalized_amplitude",
                "RMS must meet the configured low-level engineering minimum.",
            ),
            _rule(
                "absolute_dc_offset",
                "pass" if abs(dc_offset) <= self.thresholds.maximum_absolute_dc_offset else "fail",
                abs(dc_offset),
                self.thresholds.maximum_absolute_dc_offset,
                "normalized_amplitude",
                "Absolute mean amplitude must not exceed the configured DC limit.",
            ),
            _rule(
                "leading_near_silence_ratio",
                "pass"
                if leading_ratio <= self.thresholds.maximum_leading_silence_ratio
                else "fail",
                leading_ratio,
                self.thresholds.maximum_leading_silence_ratio,
                "ratio",
                "Leading consecutive samples at or below near-silence are measured.",
            ),
            _rule(
                "trailing_near_silence_ratio",
                "pass"
                if trailing_ratio <= self.thresholds.maximum_trailing_silence_ratio
                else "fail",
                trailing_ratio,
                self.thresholds.maximum_trailing_silence_ratio,
                "ratio",
                "Trailing consecutive samples at or below near-silence are measured.",
            ),
            _rule(
                "total_near_silence_ratio",
                "pass"
                if total_ratio <= self.thresholds.maximum_total_near_silence_ratio
                else "fail",
                total_ratio,
                self.thresholds.maximum_total_near_silence_ratio,
                "ratio",
                "All samples at or below near-silence contribute to this ratio.",
            ),
        ]
        ordered = self._complete_rule_order(rules)
        overall_status: QcOverallStatus = (
            "qc_failing" if any(rule.status == "fail" for rule in ordered) else "qc_passing"
        )
        return WaveformQcReport(
            source_kind=source_kind,  # type: ignore[arg-type]
            source_artifact_path=source_path,
            overall_status=overall_status,
            thresholds=self.thresholds,
            facts=facts,
            rules=ordered,
        )

    def _structural_report(
        self,
        *,
        source_kind: str,
        source_path: str | None,
        facts: WaveformFacts,
        rules: list[QcRuleResult],
        category: M4FailureCategory,
        message: str,
    ) -> WaveformQcReport:
        return WaveformQcReport(
            source_kind=source_kind,  # type: ignore[arg-type]
            source_artifact_path=source_path,
            overall_status="structurally_invalid",
            thresholds=self.thresholds,
            facts=facts,
            rules=self._complete_rule_order(rules),
            failure=_failure(category, message),
        )

    def _analysis_failure_report(
        self,
        *,
        source_kind: str,
        source_path: str | None,
        facts: WaveformFacts,
        rules: list[QcRuleResult],
    ) -> WaveformQcReport:
        return WaveformQcReport(
            source_kind=source_kind,  # type: ignore[arg-type]
            source_artifact_path=source_path,
            overall_status="analysis_failure",
            thresholds=self.thresholds,
            facts=facts,
            rules=self._complete_rule_order(rules),
            failure=_failure(
                M4FailureCategory.ANALYSIS_FAILURE,
                "Waveform metrics could not be calculated safely.",
            ),
        )

    def _complete_rule_order(
        self,
        rules: list[QcRuleResult],
    ) -> tuple[QcRuleResult, ...]:
        by_id = {rule.rule_id: rule for rule in rules}
        return tuple(
            by_id.get(rule_id, _not_applicable(rule_id, self.thresholds)) for rule_id in _RULE_ORDER
        )
