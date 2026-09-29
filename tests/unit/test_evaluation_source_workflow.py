from __future__ import annotations

import csv
import hashlib
import json
import wave
from pathlib import Path
from typing import Any

import pytest

from tts_workbench.evaluation import listening, source_audit
from tts_workbench.evaluation.prompt_set import (
    PromptSet,
    PromptSetError,
    load_prompt_set,
    summarize_prompt_set,
)


def write_json(path: Path, payload: Any) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def fixture_pack(texts: tuple[str, ...] = ("Synthetic example.",)) -> PromptSet:
    return PromptSet.model_validate(
        {
            "schema_version": 1,
            "target_variety": "White Hmong (Hmoob Dawb)",
            "writing_system": "RPA",
            "intended_use": "public_noncommercial",
            "cases": [
                {
                    "id": f"D{i:02}",
                    "text": text,
                    "split": "development",
                    "category": "everyday",
                    "source_reference": f"source-{i}",
                    "permission_reference": f"permission-{i}",
                    "review_status": "pending",
                }
                for i, text in enumerate(texts)
            ],
        }
    )


def evidence_payload(pack: PromptSet) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "pack_sha256": summarize_prompt_set(pack)["pack_sha256"],
        "records": [
            {
                "case_id": case.id,
                "source_text": case.text,
                "text_sha256": hashlib.sha256(case.text.encode()).hexdigest(),
                "source_reference": case.source_reference,
                "permission_reference": case.permission_reference,
                "source_url": "https://example.org/source",
                "source_revision": "synthetic-revision",
                "accessed_at": "2026-09-28",
                "snapshot_sha256": "a" * 64,
                "source_group": "synthetic-publisher",
                "attribution": "Synthetic test source",
                "meaning": "Synthetic published meaning.",
                "meaning_source_url": "https://example.org/meaning",
                "license_name": "Synthetic test license",
                "license_url": "https://example.org/license",
                "permission_evidence": "Synthetic fixture, no real grant.",
                "local_synthesis": "license_supported",
                "family_ids": [f"family-{i}"],
                "language_check": "source_supported",
                "language_flags": [],
                "coverage_note": "Synthetic category only.",
                "transcription_note": "Exact fixture text.",
            }
            for i, case in enumerate(pack.cases)
        ],
    }


def evidence(tmp_path: Path, pack: PromptSet) -> source_audit.SourceEvidence:
    return source_audit.load_source_evidence(
        write_json(tmp_path / "evidence.json", evidence_payload(pack)), pack
    )


def inventory(tmp_path: Path, pack: PromptSet, *, count: int = 2) -> listening.ClipInventory:
    clips = []
    for i in range(count):
        path = tmp_path / f"private-candidate-{i}.wav"
        with wave.open(str(path), "wb") as audio:
            audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            audio.writeframes(b"\x10\x00" * 160)
        clips.append(
            listening.Clip(
                candidate_id=f"private-candidate-{i}",
                configuration_sha256=str(i) * 64,
                case_id=pack.cases[0].id,
                text_sha256=hashlib.sha256(pack.cases[0].text.encode()).hexdigest(),
                wav_path=str(path),
                wav_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    return listening.ClipInventory(
        pack_sha256=str(summarize_prompt_set(pack)["pack_sha256"]), clips=clips
    )


def test_source_checks_cannot_grant_human_review(tmp_path: Path) -> None:
    pack = fixture_pack()
    report = source_audit.audit_sources(pack, evidence(tmp_path, pack))
    assert report["human_review_claims"] == {"pending": 1}
    assert report["local_permission_records"] == {"license_supported": 1}
    assert report["final_freeze"].startswith("pending")
    path = write_json(tmp_path / "pack.json", pack.model_dump())
    with pytest.raises(PromptSetError, match="reviewed status"):
        load_prompt_set(path, require_reviewed=True)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_text", "Changed."),
        ("text_sha256", "0" * 64),
        ("source_reference", "wrong"),
        ("permission_reference", "wrong"),
        ("language_flags", ["unacknowledged"]),
        ("unknown-private-field", "secret"),
    ],
)
def test_evidence_cannot_drift_from_exact_pack(tmp_path: Path, field: str, value: object) -> None:
    pack = fixture_pack()
    payload = evidence_payload(pack)
    payload["records"][0][field] = value
    with pytest.raises(PromptSetError) as error:
        source_audit.load_source_evidence(write_json(tmp_path / "e.json", payload), pack)
    assert "Changed" not in str(error.value)
    assert "secret" not in str(error.value)


@pytest.mark.parametrize("defect", ["pack_hash", "duplicate", "missing", "extra", "bool_version"])
def test_evidence_requires_exact_membership_and_version(tmp_path: Path, defect: str) -> None:
    pack = fixture_pack()
    payload = evidence_payload(pack)
    if defect == "pack_hash":
        payload["pack_sha256"] = "0" * 64
    elif defect == "duplicate":
        payload["records"] *= 2
    elif defect == "missing":
        payload["records"] = []
    elif defect == "extra":
        payload["records"].append(dict(payload["records"][0], case_id="extra"))
    else:
        payload["schema_version"] = True
    with pytest.raises(PromptSetError):
        source_audit.load_source_evidence(write_json(tmp_path / "e.json", payload), pack)


@pytest.mark.parametrize(
    ("texts", "reason"),
    [
        (("Synthetic café!", "SYNTHETIC cafe\u0301?"), "normalized_duplicate"),
        (
            ("Synthetic red vehicle here.", "Synthetic blue vehicle here."),
            "near_duplicate_or_template",
        ),
    ],
)
def test_comparison_flags_do_not_normalize_input(
    tmp_path: Path, texts: tuple[str, ...], reason: str
) -> None:
    pack = fixture_pack(texts)
    pack.cases[1] = pack.cases[1].model_copy(update={"split": "held_out"})
    before = pack.model_dump_json()
    report = source_audit.audit_sources(pack, evidence(tmp_path, pack))
    assert report["cross_split_pair_count"] == 1
    assert reason in report["related_pairs"][0]["reasons"]
    assert pack.model_dump_json() == before


def test_shared_family_checks_nonlexical_relations_and_reports_concentration(
    tmp_path: Path,
) -> None:
    pack = fixture_pack(("First specimen.", "Unrelated words."))
    pack.cases[1] = pack.cases[1].model_copy(update={"split": "held_out"})
    payload = evidence_payload(pack)
    payload["records"][1]["family_ids"] = payload["records"][0]["family_ids"]
    path = write_json(tmp_path / "e.json", payload)
    report = source_audit.audit_sources(pack, source_audit.load_source_evidence(path, pack))
    assert report["related_pairs"] == [
        {"indices": [0, 1], "cross_split": True, "reasons": ["shared_family"]}
    ]
    assert report["source_concentration"]["all"] == {"synthetic-publisher": 2}
    pack_path = write_json(tmp_path / "pack.json", pack.model_dump())
    assert (
        source_audit.main(
            ["--input", str(pack_path), "--evidence", str(path), "--require-separated"]
        )
        == 2
    )


def test_translation_records_bind_original_source_and_do_not_approve(tmp_path: Path) -> None:
    pack = fixture_pack()
    payload = evidence_payload(pack)
    check = {
        "provider": "google_translate",
        "interface": "web_ui",
        "input_origin": "published_source",
        "input_text_sha256": payload["records"][0]["text_sha256"],
        "source_language": "hmn",
        "target_language": "en",
        "checked_at": "2026-09-28",
        "translation": "Synthetic suggestion",
        "comparison": "provisional_agreement",
        "note": "Not independent confirmation.",
    }
    payload["records"][0]["translation_checks"] = [check]
    path = write_json(tmp_path / "e.json", payload)
    source_audit.load_source_evidence(path, pack)
    assert pack.cases[0].review_status == "pending"
    check["input_text_sha256"] = "0" * 64
    with pytest.raises(PromptSetError, match="mismatch"):
        source_audit.load_source_evidence(write_json(path, payload), pack)
    check["input_origin"] = "google_generated"
    with pytest.raises(PromptSetError, match="structure"):
        source_audit.load_source_evidence(write_json(path, payload), pack)


def test_external_json_rejects_checkout_links_and_invalid_json(tmp_path: Path) -> None:
    repo = tmp_path / "checkout"
    repo.mkdir()
    (repo / ".git").write_text("gitdir: synthetic", encoding="utf-8")
    source = write_json(repo / "private.json", {})
    link = tmp_path / "link.json"
    link.symlink_to(source)
    for path in (source, link):
        with pytest.raises(PromptSetError, match="outside Git"):
            source_audit.read_external_json(path)
    invalid = tmp_path / "invalid.json"
    for data in ('{"x":1,"x":2}', '{"x":NaN}', '{"private":'):
        invalid.write_text(data)
        with pytest.raises(PromptSetError):
            source_audit.read_external_json(invalid)


def test_blind_packet_preserves_pcm_hides_candidates_and_escapes_text(tmp_path: Path) -> None:
    pack = fixture_pack(("<script>synthetic</script>",))
    info, clips = evidence(tmp_path, pack), inventory(tmp_path, pack)
    out, key = tmp_path / "packet", tmp_path / "key.json"
    summary = listening.prepare_listening(pack, info, clips, out, key, seed=19)
    assert summary["status"] == "exploratory"
    assert summary["clip_count"] == 2
    page = (out / "index.html").read_text()
    assert '<p lang="hmn">&lt;script&gt;synthetic&lt;/script&gt;</p>' in page
    assert "private-candidate" not in page
    assert "private-candidate" not in (out / "scores.csv").read_text()
    saved = json.loads(key.read_text())
    assert {r["candidate_label"] for r in saved["clips"]} == {"A", "B"}
    assert key.stat().st_mode & 0o777 == 0o600
    with (out / "scores.csv").open() as handle:
        for row in csv.DictReader(handle):
            assert row["tone"] == row["naturalness"] == ""
    for clip in saved["clips"]:
        with wave.open(str(out / (clip["clip_id"] + ".wav")), "rb") as audio:
            assert audio.readframes(audio.getnframes()) == b"\x10\x00" * 160


def test_answer_key_is_private_from_creation(tmp_path: Path, monkeypatch: Any) -> None:
    pack = fixture_pack()
    info, clips = evidence(tmp_path, pack), inventory(tmp_path, pack)
    key = tmp_path / "key.json"
    modes: list[int] = []
    real_fdopen = listening.os.fdopen

    def observe(descriptor: int, *args: Any, **kwargs: Any) -> Any:
        modes.append(key.stat().st_mode & 0o777)
        return real_fdopen(descriptor, *args, **kwargs)

    monkeypatch.setattr(listening.os, "fdopen", observe)
    old_umask = listening.os.umask(0)
    try:
        listening.prepare_listening(pack, info, clips, tmp_path / "packet", key, seed=3)
    finally:
        listening.os.umask(old_umask)
    assert modes == [0o600]


def test_empty_packet_has_no_invented_audio_scores_or_candidates(tmp_path: Path) -> None:
    pack = fixture_pack()
    info = evidence(tmp_path, pack)
    clips = inventory(tmp_path, pack, count=0)
    out = tmp_path / "packet"
    report = listening.prepare_listening(pack, info, clips, out, tmp_path / "key", seed=1)
    assert report["status"] == "awaiting_eligible_audio"
    assert report["candidate_count"] == report["clip_count"] == 0
    assert not list(out.glob("*.wav"))
    assert "<audio" not in (out / "index.html").read_text()


@pytest.mark.parametrize(
    "defect",
    ["held_out", "wrong_text", "unknown_case", "permission", "wav_hash", "three_candidates"],
)
def test_ineligible_listening_inputs_leave_no_packet(tmp_path: Path, defect: str) -> None:
    pack = fixture_pack()
    if defect == "held_out":
        pack.cases[0] = pack.cases[0].model_copy(update={"split": "held_out"})
    info = evidence(tmp_path, pack)
    clips = inventory(tmp_path, pack, count=3 if defect == "three_candidates" else 1)
    if defect == "wrong_text":
        clips.clips[0] = clips.clips[0].model_copy(update={"text_sha256": "0" * 64})
    elif defect == "unknown_case":
        clips.clips[0] = clips.clips[0].model_copy(update={"case_id": "H01"})
    elif defect == "permission":
        info.records[0] = info.records[0].model_copy(update={"local_synthesis": "unresolved"})
    elif defect == "wav_hash":
        clips.clips[0] = clips.clips[0].model_copy(update={"wav_sha256": "0" * 64})
    out, key = tmp_path / "packet", tmp_path / "key.json"
    with pytest.raises(PromptSetError):
        listening.prepare_listening(pack, info, clips, out, key, seed=1)
    assert not out.exists() and not key.exists()
    assert not list(tmp_path.glob(".listening-*"))


def test_listening_rejects_collisions_checkout_outputs_and_disclosed_key(tmp_path: Path) -> None:
    pack = fixture_pack()
    info, clips = evidence(tmp_path, pack), inventory(tmp_path, pack, count=0)
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    repo = tmp_path / "checkout"
    repo.mkdir()
    (repo / ".git").mkdir()
    for output, key in (
        (occupied, tmp_path / "key"),
        (tmp_path / "out", occupied),
        (repo / "out", tmp_path / "key"),
        (tmp_path / "out", tmp_path / "out"),
    ):
        with pytest.raises(PromptSetError):
            listening.prepare_listening(pack, info, clips, output, key, seed=1)


def test_cli_errors_do_not_disclose_private_paths(tmp_path: Path, capsys: Any) -> None:
    assert listening.main(["--input", str(tmp_path / "private-missing")]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "private-missing" not in captured.err
    assert str(tmp_path) not in captured.err
