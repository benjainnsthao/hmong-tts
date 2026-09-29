from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from tts_workbench.evaluation import asr_proxy
from tts_workbench.evaluation.asr_proxy import (
    AsrProxyCase,
    AsrProxyReport,
    edit_distance,
    error_rate,
    normalize_characters,
    normalize_words,
    score_case,
    summarize,
)


def test_normalization_keeps_tone_letters_and_ignores_spacing_and_hyphens() -> None:
    assert normalize_characters("Kuv to-taub zoo kawg!") == "kuvtotaubzookawg"
    assert normalize_characters("KUV  totaub zoo kawg.") == "kuvtotaubzookawg"
    assert normalize_characters("café") == "café"
    assert normalize_words("Aub! qhov no, qab kawg!") == ["aub", "qhov", "no", "qab", "kawg"]
    assert normalize_words("to-taub_x") == ["to", "taub", "x"]
    # A changed tone letter remains a character error; comparison never strips it.
    assert score_case("Kuv mus.", "Kuv muj.")[0] == pytest.approx(1 / 6)


def test_edit_distance_and_rates() -> None:
    assert edit_distance("kitten", "sitting") == 3
    assert edit_distance([], ["a"]) == 1
    assert error_rate(["a", "b"], ["a", "b", "c", "d"]) == 1.0
    assert score_case("Nyob zoo", "nyob zoo") == (0.0, 0.0)
    with pytest.raises(ValueError):
        error_rate([], ["a"])


def case(group: str, cer: float, wer: float) -> AsrProxyCase:
    return AsrProxyCase(
        group=group,
        case_id="D01",
        reference_sha256="a" * 64,
        audio_sha256="b" * 64,
        audio_seconds=1.5,
        reference="synthetic",
        hypothesis="synthetic",
        cer=cer,
        wer=wer,
    )


def test_summaries_and_report_carry_fixed_limits() -> None:
    cases = (case("tts", 0.1, 0.5), case("tts", 0.3, 1.0), case("human", 0.2, 0.4))
    summary = summarize("tts", cases)
    assert (summary.case_count, summary.median_cer, summary.mean_wer) == (2, 0.2, 0.75)
    with pytest.raises(ValueError):
        summarize("missing", cases)
    report = AsrProxyReport(
        asr_repository="synthetic/asr",
        asr_revision="1" * 40,
        asr_subfolder="MultiSpeech",
        asr_independence="synthetic",
        cases=cases,
        summaries=(summary,),
    )
    assert report.tone_correctness == "not_measured"
    assert report.replaces_human_listening is False
    assert report.evidence_scope == "automated_intelligibility_proxy"
    for field, value in (
        ("tone_correctness", "measured"),
        ("replaces_human_listening", True),
        ("language_acceptance", "accepted"),
    ):
        with pytest.raises(ValidationError):
            AsrProxyReport.model_validate({**report.model_dump(), field: value})


def test_module_has_no_heavy_dependencies() -> None:
    text = Path(asr_proxy.__file__).read_text(encoding="utf-8")
    for name in ("torch", "transformers", "numpy", "jiwer"):
        assert f"import {name}" not in text
