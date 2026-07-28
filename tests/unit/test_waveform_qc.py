from __future__ import annotations

import json
import os
import struct
import wave
from pathlib import Path

import pytest
from pydantic import ValidationError

from tts_workbench.artifacts.json_report import (
    AtomicJsonReportStore,
    JsonReportCollisionError,
    JsonReportWriteError,
)
from tts_workbench.evaluation.contracts import M4FailureCategory
from tts_workbench.inference.contracts import WaveformResult
from tts_workbench.qc.analysis import WaveformQcAnalyzer
from tts_workbench.qc.contracts import QcThresholds, WaveformQcReport


@pytest.fixture
def thresholds() -> QcThresholds:
    return QcThresholds(
        allowed_sample_rates_hz=(16000,),
        clipping_amplitude=0.9,
        maximum_clipping_ratio=0.1,
        minimum_rms_amplitude=0.05,
        maximum_absolute_dc_offset=0.1,
        near_silence_amplitude=0.001,
        maximum_leading_silence_ratio=0.2,
        maximum_trailing_silence_ratio=0.2,
        maximum_total_near_silence_ratio=0.4,
        minimum_frame_count=4,
        minimum_duration_seconds=0.00025,
    )


def _write_wave(
    path: Path,
    samples: tuple[int, ...],
    *,
    channels: int = 1,
    sample_width: int = 2,
    sample_rate: int = 16000,
) -> None:
    formats = {1: "B", 2: "h"}
    raw = struct.pack(
        f"<{len(samples)}{formats[sample_width]}",
        *samples,
    )
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(sample_width)
        handle.setframerate(sample_rate)
        handle.writeframes(raw)


def _rules(report: WaveformQcReport) -> dict[str, str]:
    return {rule.rule_id: rule.status for rule in report.rules}


def _healthy_report(thresholds: QcThresholds) -> WaveformQcReport:
    return WaveformQcAnalyzer(thresholds).analyze_waveform(
        WaveformResult(samples=(-0.4, 0.4, -0.4, 0.4), sample_rate=16000)
    )


def test_qc_contracts_are_strict_frozen_and_schema_versioned(
    thresholds: QcThresholds,
) -> None:
    with pytest.raises(ValidationError):
        QcThresholds.model_validate({**thresholds.model_dump(), "unexpected": True})
    with pytest.raises(ValidationError):
        thresholds.maximum_clipping_ratio = 0.2  # type: ignore[misc]
    report = _healthy_report(thresholds)
    assert report.report_schema_version == 1
    assert all(rule.evidence_scope == "engineering_sanity_check" for rule in report.rules)


def test_exact_in_memory_calculations_and_rule_order(thresholds: QcThresholds) -> None:
    report = WaveformQcAnalyzer(thresholds).analyze_waveform(
        WaveformResult(samples=(0.0, 0.5, -0.5, 0.0), sample_rate=16000)
    )

    assert report.facts.duration_seconds == pytest.approx(0.00025)
    assert report.facts.absolute_peak_amplitude == 0.5
    assert report.facts.rms_amplitude == pytest.approx((0.5 / 4) ** 0.5)
    assert report.facts.dc_offset == 0.0
    assert report.facts.leading_near_silence_seconds == pytest.approx(1 / 16000)
    assert report.facts.trailing_near_silence_seconds == pytest.approx(1 / 16000)
    assert report.facts.total_near_silence_sample_count == 2
    assert report.facts.total_near_silence_ratio == 0.5
    assert [rule.rule_id for rule in report.rules] == [
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
    ]


@pytest.mark.parametrize(
    ("samples", "intended_rule"),
    [
        ((1.0, -0.4, -0.3, -0.3), "clipping_ratio"),
        ((0.01, -0.01, 0.01, -0.01), "minimum_rms_amplitude"),
        ((0.4, 0.2, 0.4, 0.2), "absolute_dc_offset"),
        (
            (0.0, 0.0, 0.0, 0.4, -0.4, 0.4, -0.4, 0.4, -0.4, 0.4),
            "leading_near_silence_ratio",
        ),
        (
            (0.4, -0.4, 0.4, -0.4, 0.4, -0.4, 0.4, 0.0, 0.0, 0.0),
            "trailing_near_silence_ratio",
        ),
        (
            (0.0, 0.4, 0.0, -0.4, 0.0, 0.4, 0.0, -0.4, 0.0, 0.4),
            "total_near_silence_ratio",
        ),
    ],
)
def test_each_engineering_defect_independently_fails_its_intended_rule(
    thresholds: QcThresholds,
    samples: tuple[float, ...],
    intended_rule: str,
) -> None:
    report = WaveformQcAnalyzer(thresholds).analyze_waveform(
        WaveformResult(samples=samples, sample_rate=16000)
    )
    failed = {rule.rule_id for rule in report.rules if rule.status == "fail"}
    assert report.overall_status == "qc_failing"
    assert failed == {intended_rule}


def test_near_total_silence_is_reported_by_low_level_and_silence_rules(
    thresholds: QcThresholds,
) -> None:
    report = WaveformQcAnalyzer(thresholds).analyze_waveform(
        WaveformResult(samples=(0.0,) * 10, sample_rate=16000)
    )
    failed = {rule.rule_id for rule in report.rules if rule.status == "fail"}
    assert {
        "minimum_rms_amplitude",
        "leading_near_silence_ratio",
        "trailing_near_silence_ratio",
        "total_near_silence_ratio",
    } <= failed


def test_numeric_overflow_is_a_structured_analysis_failure(
    thresholds: QcThresholds,
) -> None:
    report = WaveformQcAnalyzer(thresholds).analyze_waveform(
        WaveformResult(samples=(1e308, -1e308, 1e308, -1e308), sample_rate=16000)
    )
    assert report.overall_status == "analysis_failure"
    assert report.failure is not None
    assert report.failure.category == M4FailureCategory.ANALYSIS_FAILURE


@pytest.mark.parametrize(
    ("waveform", "category", "rule"),
    [
        (
            WaveformResult(samples=(), sample_rate=16000),
            M4FailureCategory.EMPTY_WAVEFORM,
            None,
        ),
        (
            WaveformResult(samples=(0.1, float("nan")), sample_rate=16000),
            M4FailureCategory.NONFINITE_SAMPLES,
            "finite_samples",
        ),
        (
            WaveformResult(samples=(0.1,) * 4, sample_rate=0),
            M4FailureCategory.INVALID_SAMPLE_RATE,
            "sample_rate_hz",
        ),
        (
            WaveformResult(samples=(0.1,) * 4, sample_rate=16000, channel_count=2),
            M4FailureCategory.CHANNEL_MISMATCH,
            "channel_count",
        ),
    ],
)
def test_in_memory_structural_defects_have_stable_categories(
    thresholds: QcThresholds,
    waveform: WaveformResult,
    category: M4FailureCategory,
    rule: str | None,
) -> None:
    report = WaveformQcAnalyzer(thresholds).analyze_waveform(waveform)
    assert report.overall_status == "structurally_invalid"
    assert report.failure is not None
    assert report.failure.category == category
    if rule is not None:
        assert _rules(report)[rule] == "fail"


def test_threshold_boundaries_are_inclusive() -> None:
    thresholds = QcThresholds(
        allowed_sample_rates_hz=(16000,),
        clipping_amplitude=0.9,
        maximum_clipping_ratio=0.5,
        minimum_rms_amplitude=0.1,
        maximum_absolute_dc_offset=0.25,
        near_silence_amplitude=0.01,
        maximum_leading_silence_ratio=0.25,
        maximum_trailing_silence_ratio=0.25,
        maximum_total_near_silence_ratio=0.5,
        minimum_frame_count=4,
        minimum_duration_seconds=0.00025,
    )
    report = WaveformQcAnalyzer(thresholds).analyze_waveform(
        WaveformResult(samples=(0.0, 0.9, -0.9, 0.0), sample_rate=16000)
    )
    rules = _rules(report)
    assert rules["clipping_ratio"] == "pass"
    assert rules["leading_near_silence_ratio"] == "pass"
    assert rules["trailing_near_silence_ratio"] == "pass"
    assert rules["total_near_silence_ratio"] == "pass"
    assert rules["minimum_frame_count"] == "pass"
    assert rules["minimum_duration_seconds"] == "pass"


def test_wav_reopen_and_pcm16_normalization(
    tmp_path: Path,
    thresholds: QcThresholds,
) -> None:
    path = tmp_path / "fixture.wav"
    _write_wave(path, (-32768, -16384, 0, 16384, 32767))
    report = WaveformQcAnalyzer(thresholds).analyze_artifact_wav(
        "fixture.wav",
        artifact_root=tmp_path,
    )
    assert report.facts.wav_readable
    assert report.facts.sample_width_bytes == 2
    assert report.facts.sample_count == 5
    assert report.facts.absolute_peak_amplitude == 1.0
    assert report.facts.dc_offset == pytest.approx(-1 / (32768 * 5))


@pytest.mark.parametrize(
    ("filename", "writer", "category"),
    [
        (
            "corrupt.wav",
            lambda path: path.write_bytes(b"not a synthetic wav"),
            M4FailureCategory.CORRUPT_WAV,
        ),
        (
            "stereo.wav",
            lambda path: _write_wave(path, (0, 1, 0, -1), channels=2),
            M4FailureCategory.CHANNEL_MISMATCH,
        ),
        (
            "pcm8.wav",
            lambda path: _write_wave(path, (128, 129, 127, 128), sample_width=1),
            M4FailureCategory.UNSUPPORTED_ENCODING,
        ),
        (
            "rate.wav",
            lambda path: _write_wave(path, (0, 1, 0, -1), sample_rate=8000),
            M4FailureCategory.INVALID_SAMPLE_RATE,
        ),
        (
            "empty.wav",
            lambda path: _write_wave(path, ()),
            M4FailureCategory.EMPTY_WAVEFORM,
        ),
    ],
)
def test_wav_structural_defects_are_rejected(
    tmp_path: Path,
    thresholds: QcThresholds,
    filename: str,
    writer: object,
    category: M4FailureCategory,
) -> None:
    path = tmp_path / filename
    writer(path)  # type: ignore[operator]
    report = WaveformQcAnalyzer(thresholds).analyze_artifact_wav(
        filename,
        artifact_root=tmp_path,
    )
    assert report.overall_status == "structurally_invalid"
    assert report.failure is not None
    assert report.failure.category == category


def test_qc_artifact_path_escape_and_absolute_paths_are_rejected(
    tmp_path: Path,
    thresholds: QcThresholds,
) -> None:
    analyzer = WaveformQcAnalyzer(thresholds)
    with pytest.raises(ValueError):
        analyzer.analyze_artifact_wav("../escaped.wav", artifact_root=tmp_path)
    with pytest.raises(ValueError):
        analyzer.analyze_artifact_wav(
            str((tmp_path / "absolute.wav").resolve()),
            artifact_root=tmp_path,
        )


def test_atomic_report_success_is_sorted_and_collision_safe(
    tmp_path: Path,
    thresholds: QcThresholds,
) -> None:
    report = _healthy_report(thresholds)
    store = AtomicJsonReportStore(artifact_root=tmp_path)
    relative = store.write(report, "qc/report.json")
    rendered = (tmp_path / relative).read_text(encoding="utf-8")

    assert relative.as_posix() == "qc/report.json"
    assert (
        rendered
        == json.dumps(
            report.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    assert not list(tmp_path.rglob("*.tmp"))
    with pytest.raises(JsonReportCollisionError):
        store.write(report, "qc/report.json")


def test_atomic_report_serialization_and_replacement_failures_roll_back(
    tmp_path: Path,
    thresholds: QcThresholds,
) -> None:
    report = _healthy_report(thresholds)

    def fail_serialization(_: object) -> str:
        raise TypeError("synthetic serialization failure")

    serialization_store = AtomicJsonReportStore(
        artifact_root=tmp_path,
        serializer=fail_serialization,  # type: ignore[arg-type]
    )
    with pytest.raises(JsonReportWriteError):
        serialization_store.write(report, "serialization/report.json")
    assert not [path for path in tmp_path.rglob("*") if path.is_file()]

    def fail_after_replace(source: str | Path, destination: str | Path) -> None:
        os.replace(source, destination)
        raise OSError("synthetic replacement failure")

    replacement_store = AtomicJsonReportStore(
        artifact_root=tmp_path,
        replace=fail_after_replace,
    )
    with pytest.raises(JsonReportWriteError):
        replacement_store.write(report, "replacement/report.json")
    assert not [path for path in tmp_path.rglob("*") if path.is_file()]


def test_atomic_report_rejects_escape_and_absolute_output(
    tmp_path: Path,
    thresholds: QcThresholds,
) -> None:
    store = AtomicJsonReportStore(artifact_root=tmp_path)
    report = _healthy_report(thresholds)
    with pytest.raises(ValueError):
        store.write(report, "../report.json")
    with pytest.raises(ValueError):
        store.write(report, (tmp_path / "absolute.json").resolve())
