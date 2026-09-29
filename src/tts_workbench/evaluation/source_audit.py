"""Audit external source evidence and split leakage without granting human approval."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from collections.abc import Sequence
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from tts_workbench.evaluation.prompt_set import (
    PromptSet,
    PromptSetError,
    RequiredString,
    _external_input,
    _reject_constant,
    _SanitizedParser,
    _unique_object,
    load_prompt_set,
    summarize_prompt_set,
)

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
WebURL = Annotated[str, Field(pattern=r"^https://[^\s]+$")]


class EvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, hide_input_in_errors=True)


class TranslationCheck(EvidenceModel):
    """Supplementary suggestions stay separate from original text and human review."""

    provider: Literal["google_translate"]
    interface: Literal["web_ui", "cloud_translation"]
    input_origin: Literal["published_source"]
    input_text_sha256: Digest
    source_language: Literal["hmn"]
    target_language: Literal["en"]
    checked_at: RequiredString
    translation: RequiredString
    comparison: Literal["provisional_agreement", "discrepancy", "uncertain"]
    note: RequiredString


class SourceRecord(EvidenceModel):
    case_id: RequiredString
    text_sha256: Digest
    source_reference: RequiredString
    permission_reference: RequiredString
    source_text: RequiredString
    source_url: WebURL
    source_revision: RequiredString
    accessed_at: RequiredString
    snapshot_sha256: Digest
    source_group: RequiredString
    attribution: RequiredString
    meaning: RequiredString
    meaning_source_url: WebURL
    license_name: RequiredString
    license_url: WebURL
    permission_evidence: RequiredString
    local_synthesis: Literal["license_supported", "unresolved", "denied"]
    public_use: Literal["unresolved"] = "unresolved"
    family_ids: Annotated[list[RequiredString], Field(min_length=1)]
    language_check: Literal["source_supported", "flagged"]
    language_flags: list[RequiredString]
    coverage_note: RequiredString
    transcription_note: RequiredString
    translation_checks: list[TranslationCheck] = Field(default_factory=list)


class SourceEvidence(EvidenceModel):
    schema_version: Literal[1]
    pack_sha256: Digest
    records: Annotated[list[SourceRecord], Field(min_length=1, max_length=500)]


def fingerprint(model: BaseModel) -> str:
    return hashlib.sha256(
        json.dumps(
            model.model_dump(mode="json"),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def read_external_json(path: Path) -> object:
    """Bound offline companion inputs and reuse the pack's checkout/JSON guards."""
    try:
        if not path.is_absolute():
            raise PromptSetError("evidence: an absolute external path is required")
        _external_input(path)
        with path.open("rb") as handle:
            data = handle.read(16_000_001)
        if len(data) > 16_000_000:
            raise PromptSetError("evidence: input exceeds 16 MB")
        return json.loads(
            data.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant
        )
    except PromptSetError:
        raise
    except (OSError, ValueError, RuntimeError):
        raise PromptSetError("evidence: cannot read valid external UTF-8 JSON") from None


def load_source_evidence(path: Path, pack: PromptSet) -> SourceEvidence:
    try:
        payload = read_external_json(path)
        # Literal[1] otherwise accepts True and 1.0, even with strict=True.
        if not isinstance(payload, dict) or type(payload.get("schema_version")) is not int:
            raise PromptSetError("evidence: schema_version must be integer 1")
        evidence = SourceEvidence.model_validate(payload)
    except ValidationError:
        raise PromptSetError("evidence: invalid source-record structure") from None
    if evidence.pack_sha256 != summarize_prompt_set(pack)["pack_sha256"]:
        raise PromptSetError("evidence: pack fingerprint mismatch")
    records = {record.case_id: record for record in evidence.records}
    if len(records) != len(evidence.records) or set(records) != {case.id for case in pack.cases}:
        raise PromptSetError("evidence: require exactly one record per case")
    for index, case in enumerate(pack.cases):
        record = records[case.id]
        digest = hashlib.sha256(case.text.encode("utf-8")).hexdigest()
        if (
            record.text_sha256 != digest
            or record.source_text != case.text
            or record.source_reference != case.source_reference
            or record.permission_reference != case.permission_reference
            or any(check.input_text_sha256 != digest for check in record.translation_checks)
        ):
            raise PromptSetError(f"evidence: cases[{index}] text or reference mismatch")
        if record.language_flags and record.language_check != "flagged":
            raise PromptSetError(f"evidence: cases[{index}] has unacknowledged language flags")
    return evidence


def _tokens(text: str) -> list[str]:
    # Comparison ONLY. Never overwrite source/model input or strip RPA tone letters.
    return re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", text).casefold())


def audit_sources(pack: PromptSet, evidence: SourceEvidence) -> dict[str, object]:
    """Heuristic flags and record counts; no semantic, permission or review verdict."""
    if len(pack.cases) > 500 or any(len(case.text) > 4096 for case in pack.cases):
        raise PromptSetError("audit: at most 500 cases of 4096 characters are supported")
    records = {record.case_id: record for record in evidence.records}
    tokens = [_tokens(case.text) for case in pack.cases]
    pairs: list[dict[str, object]] = []
    for left, right in combinations(range(len(pack.cases)), 2):
        a, b = pack.cases[left], pack.cases[right]
        reasons = []
        if set(records[a.id].family_ids) & set(records[b.id].family_ids):
            reasons.append("shared_family")
        if tokens[left] and tokens[left] == tokens[right]:
            reasons.append("normalized_duplicate")
        elif tokens[left] and tokens[right]:
            chars = SequenceMatcher(None, " ".join(tokens[left]), " ".join(tokens[right])).ratio()
            words = SequenceMatcher(None, tokens[left], tokens[right], autojunk=False).ratio()
            if chars >= 0.84 or (min(len(tokens[left]), len(tokens[right])) >= 3 and words >= 0.78):
                reasons.append("near_duplicate_or_template")
        if reasons:
            pairs.append(
                {"indices": [left, right], "cross_split": a.split != b.split, "reasons": reasons}
            )
    concentration = {
        split: dict(
            sorted(
                Counter(
                    records[case.id].source_group
                    for case in pack.cases
                    if split == "all" or case.split == split
                ).items()
            )
        )
        for split in ("all", "development", "held_out")
    }
    return {
        "schema_version": 1,
        "evidence_scope": "source_preparation_only",
        "pack_sha256": summarize_prompt_set(pack)["pack_sha256"],
        "evidence_sha256": fingerprint(evidence),
        "case_count": len(pack.cases),
        "human_review_claims": dict(Counter(case.review_status for case in pack.cases)),
        "local_permission_records": dict(Counter(r.local_synthesis for r in evidence.records)),
        "language_check_records": dict(Counter(r.language_check for r in evidence.records)),
        "flagged_case_indices": [
            i for i, case in enumerate(pack.cases) if records[case.id].language_check == "flagged"
        ],
        "source_concentration": concentration,
        "related_pairs": pairs,
        "cross_split_pair_count": sum(bool(pair["cross_split"]) for pair in pairs),
        "final_freeze": "pending_independent_review_and_permission_reconciliation",
        "pretraining_overlap": "unknown_published_text_may_have_been_seen",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = _SanitizedParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--require-separated", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        pack = load_prompt_set(args.input)
        evidence = load_source_evidence(args.evidence, pack)
        report = audit_sources(pack, evidence)
        if args.require_separated and report["cross_split_pair_count"]:
            raise PromptSetError("audit: related cross-split pairs require resolution")
    except PromptSetError as error:
        print(f"SOURCE AUDIT ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
