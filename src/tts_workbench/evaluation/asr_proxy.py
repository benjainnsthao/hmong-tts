"""Automated ASR round-trip proxy: character/word error rates, never a language verdict.

An ASR model has its own language-model prior and can "hear" what it expects, so
a low error rate does not show correct tones, pronunciation or naturalness, and
a high one does not isolate the cause. Reports carry these limits as fixed fields.
"""

from __future__ import annotations

import re
import statistics
import unicodedata
from collections.abc import Sequence
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Label = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}$")]

_NON_WORD = re.compile(r"[^\w\s-]|_")


def _fold(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold()


def normalize_characters(text: str) -> str:
    """Comparison-only form: letters and digits, including RPA tone letters; no spacing.

    Word spacing and hyphenation vary in published RPA, so both are removed here.
    """
    return "".join(ch for ch in _fold(text) if ch.isalnum())


def normalize_words(text: str) -> list[str]:
    """Comparison-only words: punctuation removed, hyphens treated as word breaks."""
    return _NON_WORD.sub(" ", _fold(text)).replace("-", " ").split()


def edit_distance(reference: Sequence[str], hypothesis: Sequence[str]) -> int:
    """Levenshtein distance with unit substitution, insertion and deletion costs."""
    previous = list(range(len(hypothesis) + 1))
    for i, ref_item in enumerate(reference, 1):
        current = [i]
        for j, hyp_item in enumerate(hypothesis, 1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (ref_item != hyp_item),
                )
            )
        previous = current
    return previous[-1]


def error_rate(reference: Sequence[str], hypothesis: Sequence[str]) -> float:
    if not reference:
        raise ValueError("reference must contain at least one comparison unit")
    return edit_distance(reference, hypothesis) / len(reference)


class ProxyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class AsrProxyCase(ProxyModel):
    """One scored clip; raw text stays in the external record, never in Git."""

    group: Label
    case_id: Label
    reference_sha256: Digest
    audio_sha256: Digest
    audio_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    reference: str
    hypothesis: str
    cer: float = Field(ge=0.0, allow_inf_nan=False)
    wer: float = Field(ge=0.0, allow_inf_nan=False)


class AsrProxySummary(ProxyModel):
    group: Label
    case_count: int = Field(ge=1)
    median_cer: float = Field(ge=0.0, allow_inf_nan=False)
    mean_cer: float = Field(ge=0.0, allow_inf_nan=False)
    median_wer: float = Field(ge=0.0, allow_inf_nan=False)
    mean_wer: float = Field(ge=0.0, allow_inf_nan=False)


class AsrProxyReport(ProxyModel):
    schema_version: Literal[1] = 1
    evidence_scope: Literal["automated_intelligibility_proxy"] = "automated_intelligibility_proxy"
    tone_correctness: Literal["not_measured"] = "not_measured"
    replaces_human_listening: Literal[False] = False
    language_acceptance: Literal["pending_fluent_human_review"] = "pending_fluent_human_review"
    normalization: Literal["nfc_casefold_alnum_only_for_cer_hyphen_split_words_for_wer"] = (
        "nfc_casefold_alnum_only_for_cer_hyphen_split_words_for_wer"
    )
    asr_repository: str
    asr_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    asr_subfolder: str
    asr_independence: str
    cases: tuple[AsrProxyCase, ...] = Field(min_length=1)
    summaries: tuple[AsrProxySummary, ...] = Field(min_length=1)


def score_case(reference: str, hypothesis: str) -> tuple[float, float]:
    """Return (CER, WER) over the comparison-only normalizations."""
    return (
        error_rate(list(normalize_characters(reference)), list(normalize_characters(hypothesis))),
        error_rate(normalize_words(reference), normalize_words(hypothesis)),
    )


def summarize(group: str, cases: Sequence[AsrProxyCase]) -> AsrProxySummary:
    chosen = [case for case in cases if case.group == group]
    if not chosen:
        raise ValueError("summary group has no cases")
    cers = [case.cer for case in chosen]
    wers = [case.wer for case in chosen]
    return AsrProxySummary(
        group=group,
        case_count=len(chosen),
        median_cer=statistics.median(cers),
        mean_cer=statistics.fmean(cers),
        median_wer=statistics.median(wers),
        mean_wer=statistics.fmean(wers),
    )
