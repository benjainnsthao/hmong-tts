"""Validate external evaluation-pack structure and recorded review metadata offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Literal, Never

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
)
from pydantic_core import PydanticCustomError


def _utf8_string(value: str) -> str:
    if value.isspace():
        raise PydanticCustomError(
            "string_pattern_mismatch", "must contain non-whitespace characters"
        )
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise PydanticCustomError("utf8_string", "must be encodable as UTF-8") from None
    return value


RequiredString = Annotated[str, Field(min_length=1, pattern=r"\S"), AfterValidator(_utf8_string)]
Split = Literal["development", "held_out"]
ReviewStatus = Literal["pending", "reviewed"]
Category = Literal["everyday", "tone", "pronunciation", "punctuation"]
SPLIT_TARGETS: dict[Split, int] = {"development": 20, "held_out": 10}
CATEGORIES: tuple[Category, ...] = ("everyday", "tone", "pronunciation", "punctuation")


class _StrictPackModel(BaseModel):
    # Do not inherit StrictM4Contract: it strips whitespace from strings.
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        str_strip_whitespace=False,
        hide_input_in_errors=True,
    )


class PromptCase(_StrictPackModel):
    """One exact sentence with opaque references to externally retained records."""

    model_config = ConfigDict(
        json_schema_extra={
            "allOf": [
                {
                    "if": {"properties": {"review_status": {"const": "reviewed"}}},
                    "then": {
                        "required": ["review_reference"],
                        "properties": {"review_reference": {"type": "string"}},
                    },
                    "else": {"properties": {"review_reference": {"type": "null"}}},
                }
            ]
        }
    )

    id: RequiredString
    text: RequiredString
    split: Split
    category: Category
    source_reference: RequiredString
    permission_reference: RequiredString
    review_status: ReviewStatus
    review_reference: RequiredString | None = Field(default=None, validate_default=True)

    @field_validator("review_reference")
    @classmethod
    def consistent_review(cls, value: str | None, info: ValidationInfo) -> str | None:
        status = info.data.get("review_status")
        if status == "reviewed" and value is None:
            raise PydanticCustomError("review_missing", "required when review_status is reviewed")
        if status == "pending" and value is not None:
            raise PydanticCustomError("review_pending", "must be absent or null when pending")
        return value


class PromptSet(_StrictPackModel):
    """Version-one pack; model_json_schema() exposes its strict structural schema."""

    schema_version: Literal[1]
    target_variety: Literal["White Hmong (Hmoob Dawb)"]
    writing_system: Literal["RPA"]
    intended_use: Literal["public_noncommercial"]
    cases: Annotated[list[PromptCase], Field(min_length=1)]

    @field_validator("schema_version", mode="before")
    @classmethod
    def integer_version(cls, value: object) -> object:
        # Literal[1] alone also accepts True and 1.0 in Pydantic.
        if type(value) is not int:
            raise PydanticCustomError("version_type", "must be the integer 1")
        return value

    @field_validator("cases")
    @classmethod
    def separated_cases(cls, cases: list[PromptCase]) -> list[PromptCase]:
        ids: dict[str, int] = {}
        texts: dict[str, tuple[int, Split]] = {}
        for index, case in enumerate(cases):
            if case.id in ids:
                raise PydanticCustomError(
                    "duplicate_id",
                    "duplicate case ID",
                    {"index": index, "first_index": ids[case.id]},
                )
            if case.text in texts and texts[case.text][1] != case.split:
                raise PydanticCustomError(
                    "split_overlap",
                    "identical text occurs in both splits",
                    {"index": index, "first_index": texts[case.text][0]},
                )
            ids[case.id] = index
            texts.setdefault(case.text, (index, case.split))
        return cases


class PromptSetError(ValueError):
    """A sanitized error suitable for printing without exposing input content."""


def _validation_message(error: ValidationError) -> str:
    messages = []
    reasons = {
        "missing": "required field is missing",
        "extra_forbidden": "unknown field",
        "literal_error": "unsupported value",
        "version_type": "must be the integer 1",
        "string_type": "must be a string",
        "string_too_short": "must be nonempty",
        "string_pattern_mismatch": "must contain non-whitespace characters",
        "utf8_string": "must be encodable as UTF-8",
        "review_missing": "required when review_status is reviewed",
        "review_pending": "must be absent or null when review_status is pending",
        "too_short": "must contain at least one case",
        "list_type": "must be a list",
        "model_type": "must be an object",
    }
    known_fields = PromptSet.model_fields.keys() | PromptCase.model_fields.keys()
    for detail in error.errors(include_input=False, include_url=False):
        kind = detail["type"]
        if kind in {"duplicate_id", "split_overlap"}:
            context = detail["ctx"]
            field = "id" if kind == "duplicate_id" else "text"
            reason = "duplicate ID" if kind == "duplicate_id" else "identical text in both splits"
            messages.append(
                f"cases[{context['index']}].{field}: {reason} "
                f"(also cases[{context['first_index']}].{field})"
            )
            continue
        location = ""
        for part in detail["loc"]:
            if isinstance(part, int):
                location += f"[{part}]"
            else:
                safe_field = part if part in known_fields else "<unknown_field>"
                location += ("." if location else "") + safe_field
        messages.append(f"{location or 'input'}: {reasons.get(kind, 'invalid value')}")
    return "; ".join(messages)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PromptSetError("input: duplicate JSON object field")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise PromptSetError("input: nonstandard JSON numeric constant")


def _external_input(path: Path) -> None:
    # Check both lexical and resolved ancestors: neither a checkout-local link to
    # external data nor an external link into a checkout is an external input.
    for candidate in (path, path.resolve(strict=True)):
        for parent in candidate.parents:
            if (parent / ".git").exists() or (
                (parent / "pyproject.toml").is_file()
                and (parent / "configs/models/registry.yaml").is_file()
            ):
                raise PromptSetError("input: file must be outside Git checkouts and project trees")


def _target_shape(pack: PromptSet) -> None:
    for split, target in SPLIT_TARGETS.items():
        cases = [case for case in pack.cases if case.split == split]
        if len(cases) != target:
            raise PromptSetError(f"cases: {split} requires exactly {target} cases")
        if len({case.text for case in cases}) != target:
            raise PromptSetError(f"cases: {split} requires distinct exact texts")
        for category in CATEGORIES:
            if not any(case.category == category for case in cases):
                raise PromptSetError(f"cases: {split} requires category {category}")


def load_prompt_set(
    path: Path, *, require_reviewed: bool = False, require_target_shape: bool = False
) -> PromptSet:
    """Read UTF-8 JSON without rewriting it; all exposed load errors are sanitized."""
    if not path.is_absolute():
        raise PromptSetError("input: an absolute file path is required")
    try:
        _external_input(path)
        payload = json.loads(
            path.read_bytes().decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as error:
        raise PromptSetError(
            f"input: malformed JSON at line {error.lineno}, column {error.colno}"
        ) from None
    except UnicodeError:
        raise PromptSetError("input: file must be UTF-8") from None
    except OSError:
        raise PromptSetError("input: cannot read file") from None
    except (RuntimeError, ValueError) as error:
        if isinstance(error, PromptSetError):
            raise
        raise PromptSetError("input: invalid JSON") from None
    try:
        pack = PromptSet.model_validate(payload)
    except ValidationError as error:
        raise PromptSetError(_validation_message(error)) from None
    if require_reviewed:
        for index, case in enumerate(pack.cases):
            if case.review_status != "reviewed":
                raise PromptSetError(f"cases[{index}].review_status: reviewed status is required")
    if require_target_shape:
        _target_shape(pack)
    return pack


def summarize_prompt_set(pack: PromptSet) -> dict[str, object]:
    """Return counts and fingerprints, never sentences or external reference values."""
    return {
        "pack_sha256": hashlib.sha256(
            json.dumps(
                pack.model_dump(mode="json"),
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        "case_count": len(pack.cases),
        "counts_by_split": {
            split: sum(case.split == split for case in pack.cases)
            for split in ("development", "held_out")
        },
        "counts_by_review_status": {
            status: sum(case.review_status == status for case in pack.cases)
            for status in ("pending", "reviewed")
        },
        "counts_by_split_and_category": {
            split: {
                category: sum(
                    case.split == split and case.category == category for case in pack.cases
                )
                for category in CATEGORIES
            }
            for split in SPLIT_TARGETS
        },
        "cases": [
            {"id": case.id, "text_sha256": hashlib.sha256(case.text.encode("utf-8")).hexdigest()}
            for case in pack.cases
        ],
    }


class _SanitizedParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise PromptSetError("arguments: invalid command arguments; use --help")


def build_parser() -> argparse.ArgumentParser:
    parser = _SanitizedParser(
        prog="python -m tts_workbench.evaluation.prompt_set", description=__doc__
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate an external UTF-8 JSON pack")
    validate.add_argument("--input", required=True, type=Path, help="absolute external JSON path")
    validate.add_argument("--require-reviewed", action="store_true", help="reject pending cases")
    validate.add_argument(
        "--require-target-shape",
        action="store_true",
        help="require 20 development and 10 held-out distinct texts, all categories in each split",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        pack = load_prompt_set(
            args.input,
            require_reviewed=args.require_reviewed,
            require_target_shape=args.require_target_shape,
        )
    except PromptSetError as error:
        print(f"PROMPT SET ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps(summarize_prompt_set(pack), indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
