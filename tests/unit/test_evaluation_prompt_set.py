from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from tts_workbench.evaluation.prompt_set import (
    PromptSet,
    PromptSetError,
    load_prompt_set,
    main,
    summarize_prompt_set,
)


def synthetic_pack() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "target_variety": "White Hmong (Hmoob Dawb)",
        "writing_system": "RPA",
        "intended_use": "public_noncommercial",
        "cases": [
            {
                "id": "synthetic-01",
                "text": "abc",
                "split": "development",
                "category": "everyday",
                "source_reference": "private-synthetic-source",
                "permission_reference": "private-synthetic-permission-tracking",
                "review_status": "pending",
            }
        ],
    }


def write_pack(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "private-synthetic-pack.json"
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return path


def assert_failure(
    path: Path, capsys: pytest.CaptureFixture[str], field: str, *options: str
) -> str:
    before = path.read_bytes()
    assert main(["validate", "--input", str(path), *options]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert field in captured.err
    assert "PROMPT SET ERROR:" in captured.err
    assert "private-synthetic" not in captured.err
    assert str(path) not in captured.err
    assert "Traceback" not in captured.err
    assert path.read_bytes() == before
    return captured.err


def test_small_pending_pack_has_stable_sanitized_summary_and_is_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = synthetic_pack()
    path = write_pack(tmp_path, payload)
    before = path.read_bytes()
    modified = path.stat().st_mtime_ns
    outputs = []
    for _ in range(2):
        assert main(["validate", "--input", str(path)]) == 0
        captured = capsys.readouterr()
        assert captured.err == ""
        outputs.append(captured.out)
    assert outputs[0] == outputs[1]
    summary = json.loads(outputs[0])
    assert len(summary.pop("pack_sha256")) == 64
    assert summary == {
        "case_count": 1,
        "counts_by_split": {"development": 1, "held_out": 0},
        "counts_by_review_status": {"pending": 1, "reviewed": 0},
        "counts_by_split_and_category": {
            "development": {"everyday": 1, "tone": 0, "pronunciation": 0, "punctuation": 0},
            "held_out": {"everyday": 0, "tone": 0, "pronunciation": 0, "punctuation": 0},
        },
        "cases": [
            {
                "id": "synthetic-01",
                "text_sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            }
        ],
    }
    assert '"abc"' not in outputs[0]
    assert "private-synthetic" not in outputs[0]
    assert path.read_bytes() == before
    assert path.stat().st_mtime_ns == modified
    assert list(tmp_path.iterdir()) == [path]


def test_reviewed_gate_and_counts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload = synthetic_pack()
    reviewed = deepcopy(payload["cases"][0])
    reviewed.update(
        id="synthetic-02",
        text="Synthetic punctuation?",
        split="held_out",
        category="punctuation",
        review_status="reviewed",
        review_reference="private-synthetic-review",
    )
    payload["cases"].append(reviewed)
    path = write_pack(tmp_path, payload)
    assert main(["validate", "--input", str(path)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["counts_by_split"] == {"development": 1, "held_out": 1}
    assert summary["counts_by_review_status"] == {"pending": 1, "reviewed": 1}
    assert [case["id"] for case in summary["cases"]] == ["synthetic-01", "synthetic-02"]
    assert_failure(path, capsys, "cases[0].review_status", "--require-reviewed")

    payload["cases"] = [reviewed]
    path = write_pack(tmp_path, payload)
    before = path.read_bytes()
    assert main(["validate", "--input", str(path), "--require-reviewed"]) == 0
    assert "private-synthetic" not in capsys.readouterr().out
    assert path.read_bytes() == before


@pytest.mark.parametrize("ensure_ascii", [True, False])
def test_exact_decoded_text_and_utf8_hash_are_preserved(tmp_path: Path, ensure_ascii: bool) -> None:
    text = " \tSYNTHETIC b j v s g m d 0012,!? É é e\u0301 \U0001f642\r\n  "
    payload = synthetic_pack()
    payload["cases"][0]["text"] = text
    path = tmp_path / "synthetic.json"
    path.write_bytes(json.dumps(payload, ensure_ascii=ensure_ascii).encode("utf-8"))
    before = path.read_bytes()

    pack = load_prompt_set(path)

    assert pack.cases[0].text == text
    assert pack.model_dump()["cases"][0]["text"].encode("utf-8") == text.encode("utf-8")
    assert summarize_prompt_set(pack)["cases"] == [
        {"id": "synthetic-01", "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    ]
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", 2),
        ("schema_version", True),
        ("schema_version", 1.0),
        ("schema_version", "1"),
        ("target_variety", "private-synthetic-variety"),
        ("writing_system", "private-synthetic-script"),
        ("intended_use", "private-synthetic-use"),
        ("cases", []),
        ("cases", {}),
        ("cases", None),
        ("cases", ["private-synthetic-case"]),
        ("private-synthetic-unknown-field", "private-synthetic-value"),
    ],
)
def test_invalid_pack_fields_are_sanitized(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], field: str, value: object
) -> None:
    payload = synthetic_pack()
    payload[field] = value
    location = "<unknown_field>" if field.startswith("private-synthetic") else field
    assert_failure(write_pack(tmp_path, payload), capsys, location)


@pytest.mark.parametrize("field", list(synthetic_pack()))
def test_missing_pack_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], field: str
) -> None:
    payload = synthetic_pack()
    del payload[field]
    assert_failure(write_pack(tmp_path, payload), capsys, field)


@pytest.mark.parametrize("field", list(synthetic_pack()["cases"][0]))
def test_missing_case_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], field: str
) -> None:
    payload = synthetic_pack()
    del payload["cases"][0][field]
    assert_failure(write_pack(tmp_path, payload), capsys, f"cases[0].{field}")


@pytest.mark.parametrize("field", ["id", "text", "source_reference", "permission_reference"])
@pytest.mark.parametrize("value", ["", " \t\r\n\u2003", "\x1c", None, 7, {}, [], "\ud800"])
def test_required_strings_reject_blank_nonstring_and_non_utf8_values(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], field: str, value: object
) -> None:
    payload = synthetic_pack()
    payload["cases"][0][field] = value
    assert_failure(write_pack(tmp_path, payload), capsys, f"cases[0].{field}")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("split", "private-synthetic-split"),
        ("category", "private-synthetic-category"),
        ("review_status", "private-synthetic-status"),
        ("text", {"private-synthetic-key": "private-synthetic-sentence"}),
        ("private-synthetic-field", "private-synthetic-reference"),
    ],
)
def test_invalid_case_fields_do_not_leak_values_or_unknown_keys(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], field: str, value: object
) -> None:
    payload = synthetic_pack()
    payload["cases"][0].update(id="private-synthetic-id", text="private-synthetic-sentence")
    payload["cases"][0][field] = value
    location = "<unknown_field>" if field.startswith("private-synthetic") else field
    assert_failure(write_pack(tmp_path, payload), capsys, f"cases[0].{location}")


@pytest.mark.parametrize("reference", [None, "", " \t\n", 3, {}, "\ud800"])
def test_reviewed_reference_must_be_nonblank_string(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], reference: object
) -> None:
    payload = synthetic_pack()
    payload["cases"][0].update(review_status="reviewed", review_reference=reference)
    assert_failure(write_pack(tmp_path, payload), capsys, "cases[0].review_reference")


def test_review_metadata_consistency(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    payload = synthetic_pack()
    payload["cases"][0]["review_status"] = "reviewed"
    assert_failure(write_pack(tmp_path, payload), capsys, "cases[0].review_reference")
    payload["cases"][0].update(review_status="pending", review_reference="private-synthetic-review")
    assert_failure(write_pack(tmp_path, payload), capsys, "cases[0].review_reference")
    payload["cases"][0]["review_reference"] = None
    assert load_prompt_set(write_pack(tmp_path, payload)).cases[0].review_reference is None


@pytest.mark.parametrize("split", ["development", "held_out"])
def test_duplicate_ids_are_rejected_across_all_splits(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], split: str
) -> None:
    payload = synthetic_pack()
    duplicate = deepcopy(payload["cases"][0])
    duplicate.update(text="private-synthetic-other-text", split=split)
    payload["cases"].append(duplicate)
    error = assert_failure(write_pack(tmp_path, payload), capsys, "cases[1].id")
    assert "cases[0].id" in error


@pytest.mark.parametrize("reverse", [False, True])
def test_identical_text_cannot_cross_splits(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], reverse: bool
) -> None:
    payload = synthetic_pack()
    payload["cases"][0]["text"] = "private-synthetic-sentence"
    duplicate = deepcopy(payload["cases"][0])
    duplicate.update(id="synthetic-02", split="held_out")
    payload["cases"].append(duplicate)
    if reverse:
        payload["cases"].reverse()
    error = assert_failure(write_pack(tmp_path, payload), capsys, "cases[1].text")
    assert "cases[0].text" in error
    payload["cases"][1]["split"] = payload["cases"][0]["split"]
    assert len(load_prompt_set(write_pack(tmp_path, payload)).cases) == 2


@pytest.mark.parametrize(
    ("first", "second"),
    [("abc", " abc "), ("abc", "ABC"), ("é", "e\u0301"), ("12", "twelve")],
)
def test_split_comparison_does_not_normalize_text(tmp_path: Path, first: str, second: str) -> None:
    payload = synthetic_pack()
    payload["cases"][0]["text"] = first
    second_case = deepcopy(payload["cases"][0])
    second_case.update(id="synthetic-02", text=second, split="held_out")
    payload["cases"].append(second_case)
    pack = load_prompt_set(write_pack(tmp_path, payload))
    assert [case.text for case in pack.cases] == [first, second]
    assert hashlib.sha256(first.encode()).digest() != hashlib.sha256(second.encode()).digest()


@pytest.mark.parametrize("category", ["everyday", "tone", "pronunciation", "punctuation"])
def test_all_categories_are_supported(tmp_path: Path, category: str) -> None:
    payload = synthetic_pack()
    payload["cases"][0]["category"] = category
    assert load_prompt_set(write_pack(tmp_path, payload)).cases[0].category == category


@pytest.mark.parametrize(
    "content",
    [
        b'{"private-synthetic-text": ',
        b'{"private-synthetic-key": 1, "private-synthetic-key": 2}',
        b'{"private-synthetic-key": NaN}',
        b'{"private-synthetic-key": Infinity}',
        b'{"private-synthetic-key": -Infinity}',
        b'{"private-synthetic-key": "\xff"}',
        b'"private-synthetic-text"',
        b"[]",
        b"null",
        b"[" * 1100,
    ],
)
def test_invalid_json_is_sanitized_and_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], content: bytes
) -> None:
    path = tmp_path / "private-synthetic-pack.json"
    path.write_bytes(content)
    assert_failure(path, capsys, "input")
    with pytest.raises(PromptSetError) as error:
        load_prompt_set(path)
    assert "private-synthetic" not in str(error.value)


def test_file_and_argument_errors_hide_private_paths(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for arguments in (
        ["validate", "--input", str(tmp_path / "private-synthetic-missing.json")],
        ["validate", "--input", str(tmp_path)],
        ["validate", "--input", "private-synthetic-relative.json"],
        ["validate", "--input", "\x00private-synthetic-path"],
        ["private-synthetic-command"],
        ["validate", "--input", str(tmp_path), "--private-synthetic-option"],
        ["validate"],
    ):
        assert main(arguments) == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "PROMPT SET ERROR:" in captured.err
        assert "private-synthetic" not in captured.err
        assert str(tmp_path) not in captured.err


def test_schema_exposes_strict_structure_and_review_condition() -> None:
    schema = PromptSet.model_json_schema()
    assert schema["additionalProperties"] is False
    assert schema["properties"]["cases"]["minItems"] == 1
    assert schema["properties"]["schema_version"]["const"] == 1
    case_schema = schema["$defs"]["PromptCase"]
    assert case_schema["additionalProperties"] is False
    assert case_schema["allOf"][0]["then"]["required"] == ["review_reference"]


def test_module_command_and_help(tmp_path: Path) -> None:
    path = write_pack(tmp_path, synthetic_pack())
    before = path.read_bytes()
    command = [sys.executable, "-m", "tts_workbench.evaluation.prompt_set"]
    result = subprocess.run(
        [*command, "validate", "--input", str(path)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["case_count"] == 1
    assert path.read_bytes() == before
    result = subprocess.run(
        [*command, "validate", "--input", str(path), "--require-reviewed"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "cases[0].review_status" in result.stderr
    assert "private-synthetic" not in result.stderr
    assert path.read_bytes() == before
    result = subprocess.run(
        [*command, "validate", "--help"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert "--require-reviewed" in result.stdout


def test_validation_never_imports_ml_or_uses_network(tmp_path: Path) -> None:
    path = write_pack(tmp_path, synthetic_pack())
    code = """
import importlib.abc
import runpy
import sys

blocked = {"torch", "transformers", "safetensors", "scipy", "numpy", "huggingface_hub"}

class BlockML(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in blocked or fullname.startswith('tts_workbench.inference'):
            raise AssertionError('unexpected ML import')

def no_network(event, args):
    if event.startswith(('socket.', 'urllib.')) or event == 'subprocess.Popen':
        raise AssertionError('unexpected network or subprocess access')

sys.meta_path.insert(0, BlockML())
sys.addaudithook(no_network)
sys.argv = ['prompt_set', 'validate', '--input', sys.argv[1]]
runpy.run_module('tts_workbench.evaluation.prompt_set', run_name='__main__', alter_sys=True)
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(path)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["case_count"] == 1


def target_pack() -> dict[str, Any]:
    payload = synthetic_pack()
    case = payload["cases"][0]
    payload["cases"] = [
        dict(
            case,
            id=f"synthetic-{index:02}",
            text=f"Synthetic case {index}.",
            split="development" if index < 20 else "held_out",
            category=("everyday", "tone", "pronunciation", "punctuation")[index % 4],
        )
        for index in range(30)
    ]
    return payload


def test_target_shape_and_review_are_independent_gates(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = target_pack()
    path = write_pack(tmp_path, payload)
    assert main(["validate", "--input", str(path), "--require-target-shape"]) == 0
    assert json.loads(capsys.readouterr().out)["counts_by_review_status"]["pending"] == 30
    assert_failure(path, capsys, "review_status", "--require-target-shape", "--require-reviewed")
    for case in payload["cases"]:
        case.update(review_status="reviewed", review_reference="private-synthetic-review")
    path = write_pack(tmp_path, payload)
    assert (
        main(["validate", "--input", str(path), "--require-target-shape", "--require-reviewed"])
        == 0
    )
    assert json.loads(capsys.readouterr().out)["counts_by_review_status"]["reviewed"] == 30


@pytest.mark.parametrize("split", ["development", "held_out"])
@pytest.mark.parametrize("defect", ["missing_case", "extra_case", "missing_category", "duplicate"])
def test_target_shape_rejects_wrong_counts_coverage_and_repetition(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], split: str, defect: str
) -> None:
    payload = target_pack()
    cases = [case for case in payload["cases"] if case["split"] == split]
    if defect == "missing_case":
        payload["cases"].remove(cases[0])
    elif defect == "extra_case":
        payload["cases"].append(dict(cases[0], id="synthetic-extra", text="Synthetic extra."))
    elif defect == "missing_category":
        for case in cases:
            case["category"] = "everyday"
    else:
        cases[1]["text"] = cases[0]["text"]
    path = write_pack(tmp_path, payload)
    # Preparation remains possible before meeting the final-pack target.
    load_prompt_set(path)
    assert_failure(path, capsys, split, "--require-target-shape")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "synthetic-other"),
        ("text", "abc "),
        ("split", "held_out"),
        ("category", "tone"),
        ("source_reference", "private-synthetic-source-2"),
        ("permission_reference", "private-synthetic-permission-2"),
        ("review_status", "reviewed"),
    ],
)
def test_pack_fingerprint_binds_text_split_and_review_metadata(
    tmp_path: Path, field: str, value: str
) -> None:
    payload = synthetic_pack()
    first = summarize_prompt_set(load_prompt_set(write_pack(tmp_path, payload)))
    payload["cases"][0][field] = value
    if field == "review_status":
        payload["cases"][0]["review_reference"] = "private-synthetic-review"
    second = summarize_prompt_set(load_prompt_set(write_pack(tmp_path, payload)))
    assert first["pack_sha256"] != second["pack_sha256"]
    assert "private-synthetic" not in json.dumps(second)


def test_pack_fingerprint_is_independent_of_json_formatting(tmp_path: Path) -> None:
    payload = synthetic_pack()
    payload["cases"][0]["text"] = "Synthetic é e\u0301\r\n "
    path = write_pack(tmp_path, payload)
    first = summarize_prompt_set(load_prompt_set(path))
    path.write_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    assert summarize_prompt_set(load_prompt_set(path)) == first


@pytest.mark.parametrize("marker", ["git_directory", "worktree_file", "exported_project"])
def test_checkout_inputs_rejected_even_from_an_external_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], marker: str
) -> None:
    checkout = tmp_path / "private-synthetic-checkout"
    checkout.mkdir()
    if marker == "git_directory":
        (checkout / ".git").mkdir()
    elif marker == "worktree_file":
        (checkout / ".git").write_text("gitdir: private-synthetic-reference", encoding="utf-8")
    else:
        (checkout / "pyproject.toml").touch()
        (checkout / "configs/models").mkdir(parents=True)
        (checkout / "configs/models/registry.yaml").touch()
    monkeypatch.chdir(tmp_path)
    path = write_pack(checkout, synthetic_pack())
    assert_failure(path, capsys, "outside Git")


@pytest.mark.parametrize("link_inside", [False, True])
def test_links_cannot_hide_checkout_input(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], link_inside: bool
) -> None:
    checkout = tmp_path / "private-synthetic-checkout"
    checkout.mkdir()
    (checkout / ".git").mkdir()
    target = write_pack(tmp_path if link_inside else checkout, synthetic_pack())
    link = (checkout if link_inside else tmp_path) / "private-synthetic-link.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable on this platform")
    assert_failure(link, capsys, "outside Git")


def test_symlink_loop_has_sanitized_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "private-synthetic-loop.json"
    try:
        path.symlink_to(path)
    except OSError:
        pytest.skip("symlinks unavailable on this platform")
    assert main(["validate", "--input", str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "PROMPT SET ERROR: input:" in captured.err
    assert "private-synthetic" not in captured.err
