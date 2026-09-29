"""Prepare an external, development-only blind listening packet; never synthesize."""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import os
import random
import re
import secrets
import shutil
import sys
import tempfile
import wave
from collections.abc import Sequence
from pathlib import Path

from pydantic import Field, ValidationError

from tts_workbench.evaluation.prompt_set import (
    PromptSet,
    PromptSetError,
    RequiredString,
    _external_input,
    _SanitizedParser,
    load_prompt_set,
    summarize_prompt_set,
)
from tts_workbench.evaluation.source_audit import (
    Digest,
    EvidenceModel,
    SourceEvidence,
    fingerprint,
    load_source_evidence,
    read_external_json,
)


class Clip(EvidenceModel):
    candidate_id: RequiredString
    configuration_sha256: Digest
    case_id: RequiredString
    text_sha256: Digest
    wav_path: RequiredString
    wav_sha256: Digest


class ClipInventory(EvidenceModel):
    pack_sha256: Digest
    clips: list[Clip] = Field(max_length=50)


def _destination(path: Path) -> None:
    if not path.is_absolute():
        raise PromptSetError("output: an absolute external path is required")
    for candidate in (path, path.resolve()):
        for parent in (candidate, *candidate.parents):
            if (parent / ".git").exists() or (
                (parent / "pyproject.toml").is_file()
                and (parent / "configs/models/registry.yaml").is_file()
            ):
                raise PromptSetError("output: must stay outside Git and project trees")
    if path.exists() or path.is_symlink() or not path.parent.is_dir():
        raise PromptSetError("output: require a new path with an existing parent")


def _pcm(clip: Clip) -> tuple[bytes, int]:
    path = Path(clip.wav_path)
    if not path.is_absolute():
        raise PromptSetError("clip: require an absolute external WAV path")
    _external_input(path)
    with path.open("rb") as handle:
        data = handle.read(6_000_001)
    if len(data) > 6_000_000 or hashlib.sha256(data).hexdigest() != clip.wav_sha256:
        raise PromptSetError("clip: size limit or WAV fingerprint mismatch")
    with wave.open(io.BytesIO(data), "rb") as audio:
        rate = audio.getframerate()
        frames = audio.getnframes()
        if (
            audio.getnchannels() != 1
            or audio.getsampwidth() != 2
            or audio.getcomptype() != "NONE"
            or not 8000 <= rate <= 48000
            or not 0 < frames <= 30 * rate
        ):
            raise PromptSetError("clip: require nonempty mono PCM16, 8–48 kHz, at most 30 seconds")
        pcm = audio.readframes(frames)
        if len(pcm) != frames * 2:
            raise PromptSetError("clip: truncated WAV")
    return pcm, rate


def prepare_listening(
    pack: PromptSet,
    evidence: SourceEvidence,
    inventory: ClipInventory,
    output: Path,
    key_path: Path,
    *,
    seed: int,
) -> dict[str, object]:
    """A new packet and separate private key; input audio/text are never modified."""
    if len(pack.cases) > 20 or any(case.split != "development" for case in pack.cases):
        raise PromptSetError("listening: require a development-only pack of at most 20 cases")
    pack_hash = str(summarize_prompt_set(pack)["pack_sha256"])
    if inventory.pack_sha256 != pack_hash or evidence.pack_sha256 != pack_hash:
        raise PromptSetError("listening: pack fingerprint mismatch")
    _destination(output)
    _destination(key_path)
    if key_path.resolve() == output.resolve() or output.resolve() in key_path.resolve().parents:
        raise PromptSetError("listening: keep the answer key outside the reviewer directory")
    records = {record.case_id: record for record in evidence.records}
    cases = {case.id: case for case in pack.cases}
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", key) for key in cases):
        raise PromptSetError("listening: require opaque alphanumeric case IDs for score sheets")
    identities = sorted(
        {(clip.candidate_id, clip.configuration_sha256) for clip in inventory.clips}
    )
    if len(identities) > 2:
        raise PromptSetError("listening: at most two fixed candidate configurations")
    counts: dict[tuple[str, str], int] = {}
    for supplied in inventory.clips:
        identity = (supplied.candidate_id, supplied.configuration_sha256)
        counts[identity] = counts.get(identity, 0) + 1
        if counts[identity] > 25:
            raise PromptSetError("listening: at most 25 clips per configuration")
        if (
            supplied.case_id not in cases
            or supplied.text_sha256
            != hashlib.sha256(cases[supplied.case_id].text.encode()).hexdigest()
        ):
            raise PromptSetError("listening: unknown case or text fingerprint mismatch")
        if records[supplied.case_id].local_synthesis != "license_supported":
            raise PromptSetError("listening: source permission unresolved for a supplied clip")
    rng = random.Random(seed)
    rng.shuffle(identities)
    labels = {identity: chr(65 + i) for i, identity in enumerate(identities)}
    clips = list(inventory.clips)
    rng.shuffle(clips)
    summary: dict[str, object] = {
        "status": "exploratory" if clips else "awaiting_eligible_audio",
        "case_count": len(pack.cases),
        "clip_count": len(clips),
        "candidate_count": len(identities),
        "pack_sha256": pack_hash,
        "evidence_sha256": fingerprint(evidence),
        "language_acceptance": "pending_fluent_human_review",
    }
    staging = Path(tempfile.mkdtemp(prefix=".listening-", dir=output.parent))
    key_written = False
    try:
        score_rows = []
        key_rows = []
        cards = []
        # An empty inventory prepares a real text-review packet with no fake audio or ratings.
        entries: list[tuple[str, Clip | None]] = [(clip.case_id, clip) for clip in clips]
        if not entries:
            entries = [(case.id, None) for case in pack.cases]
        for index, (case_id, clip) in enumerate(entries, 1):
            case, record = cases[case_id], records[case_id]
            clip_id = f"clip-{index:03}" if clip else f"text-{index:03}"
            label = labels[(clip.candidate_id, clip.configuration_sha256)] if clip else ""
            player = "<p>Awaiting eligible candidate audio.</p>"
            if clip:
                pcm, rate = _pcm(clip)
                wav_name = f"{clip_id}.wav"
                with wave.open(str(staging / wav_name), "wb") as audio:
                    audio.setparams((1, 2, rate, 0, "NONE", "not compressed"))
                    audio.writeframes(pcm)
                key_rows.append(
                    {
                        "clip_id": clip_id,
                        "candidate_label": label,
                        **clip.model_dump(),
                        "packet_wav_sha256": hashlib.sha256(
                            (staging / wav_name).read_bytes()
                        ).hexdigest(),
                    }
                )
                player = f'<audio controls preload="none" src="{wav_name}"></audio>'
            score_rows.append([clip_id, case_id, label, "", "", "", "", "", "", ""])
            notes = html.escape("; ".join(record.language_flags) or "Independent review pending.")
            cards.append(
                f'<article><h2>{clip_id} {label}</h2><p lang="hmn">{html.escape(case.text)}</p>'
                f"<p>Published meaning: {html.escape(record.meaning)}</p>{player}"
                f"<p>Review notes: {notes}</p>"
                f"<small>{html.escape(record.attribution)} — "
                f'<a href="{html.escape(record.source_url, quote=True)}">Source</a>; '
                f'<a href="{html.escape(record.meaning_source_url, quote=True)}">'
                "Meaning source</a>; "
                f'<a href="{html.escape(record.license_url, quote=True)}">'
                f"{html.escape(record.license_name)}</a>"
                "</small></article>"
            )
        (staging / "index.html").write_text(
            '<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
            "style-src 'unsafe-inline'; media-src 'self'\">"
            "<title>White Hmong development listening</title><style>"
            "body{font:18px system-ui;max-width:850px;margin:2rem auto;padding:1rem}"
            "article{border-top:1px solid #bbb;padding:1rem 0}p{white-space:pre-wrap}"
            "audio{width:100%}small{display:block;margin-top:1rem}</style>"
            "<h1>White Hmong development review</h1>"
            "<p>Exploratory preparation. Independent language acceptance is pending. "
            "Review source ambiguities before scoring. Listen once without reading the meaning, "
            "then compare. Use scores.csv; blank means unscored.</p>"
            "<p>Intelligibility, tone, pronunciation, phrasing and naturalness: "
            "1 = major problems, 2 = repeated problems, 3 = understandable with effort, "
            "4 = minor problems, 5 = no noticed problems. Record meaning-changing errors "
            "and uncertainty separately. These anchors require fluent-human acceptance; "
            "no pass threshold has been approved.</p>" + "".join(cards) + "</html>",
            encoding="utf-8",
        )
        with (staging / "scores.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "clip_id",
                    "case_id",
                    "candidate_label",
                    "intelligibility",
                    "tone",
                    "pronunciation",
                    "phrasing",
                    "naturalness",
                    "critical_error_or_uncertainty",
                    "notes",
                ]
            )
            writer.writerows(score_rows)
        (staging / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        # Create the key private from the first byte; never readable before a chmod.
        descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        key_written = True
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump({"seed": seed, "summary": summary, "clips": key_rows}, handle, indent=2)
            handle.write("\n")
        key_path.chmod(0o600)
        # A collision never replaces another packet, including an empty directory.
        if output.exists() or output.is_symlink():
            raise PromptSetError("output: destination already exists")
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        if key_written:
            key_path.unlink(missing_ok=True)
        raise
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = _SanitizedParser(description=__doc__)
    for name in ("input", "evidence", "output", "key"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--clips", type=Path)
    parser.add_argument("--seed", type=int)
    try:
        args = parser.parse_args(argv)
        pack = load_prompt_set(args.input)
        evidence = load_source_evidence(args.evidence, pack)
        inventory = (
            ClipInventory.model_validate(read_external_json(args.clips))
            if args.clips
            else ClipInventory(pack_sha256=str(summarize_prompt_set(pack)["pack_sha256"]), clips=[])
        )
        summary = prepare_listening(
            pack,
            evidence,
            inventory,
            args.output,
            args.key,
            seed=args.seed if args.seed is not None else secrets.randbits(64),
        )
    except PromptSetError as error:
        print(f"LISTENING ERROR: {error}", file=sys.stderr)
        return 2
    except (ValidationError, OSError, ValueError, RuntimeError, EOFError, wave.Error):
        print("LISTENING ERROR: invalid records, audio, or external output", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
