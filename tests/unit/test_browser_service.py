from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from tests.fakes.browser_server import browser_test_app
from tts_workbench.inference.contracts import InferenceResult, RunManifest
from tts_workbench.inference.prompts import ENGLISH_EXAMPLE
from tts_workbench.service.results import ResultIndex, ResultUnavailable, audio_slice

ORIGIN = "http://127.0.0.1:8000"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TTS_WORKBENCH_ARTIFACT_ROOT", str(tmp_path))
    with TestClient(browser_test_app(tmp_path), base_url=ORIGIN) as client:
        yield client


def synthesize(client: TestClient, text: str = ENGLISH_EXAMPLE) -> dict[str, str]:
    response = client.post(
        "/v1/synthesize", json={"model_id": "fixture-eng", "text": text}, headers={"Origin": ORIGIN}
    )
    assert response.status_code == 200
    return response.json()


def test_packaged_dashboard_and_ui_config(client: TestClient) -> None:
    page = client.get("/")
    assert page.status_code == 200
    assert "Local TTS Workbench" in page.text
    for asset in ("styles.css", "app.js"):
        assert client.get(f"/ui/{asset}").status_code == 200
    assert client.get("/ui/unknown.js").status_code == 404
    assert client.get("/v1/ui-config").json()["max_input_characters"] == 500
    assert page.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]


def test_generation_metadata_playback_and_range(client: TestClient, tmp_path: Path) -> None:
    result = synthesize(client)
    run_id = result["run_id"]
    # The executor and service allocate independent identifiers.
    assert run_id not in result["wav_path"]
    metadata = client.get(f"/v1/runs/{run_id}")
    assert metadata.status_code == 200
    assert metadata.json()["prompt_provenance"] == "builtin_fixture"
    assert "wav_path" not in metadata.text
    assert ENGLISH_EXAMPLE not in metadata.text
    audio = client.get(f"/v1/runs/{run_id}/audio")
    assert audio.content == (tmp_path / result["wav_path"]).read_bytes()
    assert audio.headers["content-type"] == "audio/wav"
    assert audio.headers["cache-control"] == "no-store"
    partial = client.get(f"/v1/runs/{run_id}/audio", headers={"Range": "bytes=44-99"})
    assert partial.status_code == 206
    assert partial.content == audio.content[44:100]
    assert partial.headers["content-range"] == f"bytes 44-99/{len(audio.content)}"
    download = client.get(f"/v1/runs/{run_id}/audio?download=true")
    assert download.headers["content-disposition"].startswith("attachment;")


def test_custom_multiline_text_has_truthful_provenance(client: TestClient, tmp_path: Path) -> None:
    text = "Synthetic custom marker.\nAnother synthetic sentence."
    result = synthesize(client, text)
    manifest = RunManifest.model_validate_json((tmp_path / result["manifest_path"]).read_bytes())
    assert manifest.manifest_schema_version == 2
    assert manifest.prompt_provenance == "user_supplied_unreviewed"
    assert text not in (tmp_path / result["manifest_path"]).read_text()


def test_historical_manifest_reading_and_required_new_provenance(
    client: TestClient,
    tmp_path: Path,
) -> None:
    result = synthesize(client)
    payload = json.loads((tmp_path / result["manifest_path"]).read_text())
    payload.pop("prompt_provenance")
    with pytest.raises(ValidationError):
        RunManifest.model_validate(payload)
    payload["manifest_schema_version"] = 1
    assert RunManifest.model_validate(payload).prompt_provenance is None


def test_vietnamese_requires_retained_prompt(client: TestClient) -> None:
    response = client.post(
        "/v1/synthesize", json={"model_id": "fixture-vie", "text": "synthetic unrelated text"}
    )
    assert response.status_code == 422
    assert "unrelated" not in response.text


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "attacker.example:8000"},
        {"Host": "127.0.0.1:9999"},
        {"Origin": "https://attacker.example"},
        {"Origin": "null"},
        {"Origin": "http://localhost:8000"},
        {"Sec-Fetch-Site": "cross-site"},
        {"Sec-Fetch-Site": "same-site"},
    ],
)
def test_host_origin_and_fetch_metadata_reject_foreign_requests(
    client: TestClient, headers: dict[str, str]
) -> None:
    assert client.get("/", headers=headers).status_code == 403
    assert (
        client.post(
            "/v1/synthesize", json={"model_id": "fixture-eng", "text": "marker"}, headers=headers
        ).status_code
        == 403
    )


def test_trusted_cli_and_matching_browser_origins(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
    assert (
        client.get(
            "/health", headers={"Origin": ORIGIN, "Sec-Fetch-Site": "same-origin"}
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/health", headers={"Host": "localhost:8000", "Origin": "http://localhost:8000"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/v1/synthesize", content="marker", headers={"Content-Type": "text/plain"}
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/health", headers=[("Host", "127.0.0.1:8000"), ("Host", "attacker.example")]
        ).status_code
        == 403
    )
    assert (
        client.get("/health", headers=[("Origin", ORIGIN), ("Origin", ORIGIN)]).status_code == 403
    )


@pytest.mark.parametrize(
    "damage",
    [
        "missing_manifest",
        "missing_audio",
        "corrupt_audio",
        "wrong_id",
        "wrong_path",
        "symlink_audio",
        "symlink_manifest",
        "symlink_parent",
        "invalid_manifest",
        "oversized_manifest",
    ],
)
def test_playback_fails_closed_for_damaged_artifacts(
    client: TestClient, tmp_path: Path, damage: str
) -> None:
    result = synthesize(client)
    wav = tmp_path / result["wav_path"]
    manifest = tmp_path / result["manifest_path"]
    if damage == "missing_manifest":
        manifest.unlink()
    elif damage == "missing_audio":
        wav.unlink()
    elif damage == "corrupt_audio":
        wav.write_bytes(b"invalid")
    elif damage == "invalid_manifest":
        manifest.write_text("{}")
    elif damage == "oversized_manifest":
        manifest.write_bytes(b"x" * 65537)
    elif damage in {"wrong_id", "wrong_path"}:
        payload = json.loads(manifest.read_text())
        payload["run_id" if damage == "wrong_id" else "wav_path"] = (
            "12345678-1234-4123-8123-123456789abc" if damage == "wrong_id" else "../escape.wav"
        )
        manifest.write_text(json.dumps(payload))
    elif damage == "symlink_parent":
        original = wav.parent
        target = original.with_name("relocated")
        original.rename(target)
        original.symlink_to(target, target_is_directory=True)
    else:
        original = wav if damage == "symlink_audio" else manifest
        target = original.with_name("relocated-file")
        original.rename(target)
        original.symlink_to(target)
    response = client.get(f"/v1/runs/{result['run_id']}/audio")
    assert response.status_code == 404
    assert str(tmp_path) not in response.text


def test_unknown_and_traversal_paths_are_not_served(client: TestClient) -> None:
    for path in (
        "/v1/runs/unknown/audio",
        "/v1/runs/%2E%2E%2Fsecret/audio",
        "/ui/%2E%2E%2Fsecret",
        "/service/runs/secret.wav",
    ):
        assert client.get(path).status_code == 404


def test_result_index_bounds_history_and_rejects_escaped_paths(tmp_path: Path) -> None:
    index = ResultIndex(tmp_path, "service/runs", capacity=1)
    first = InferenceResult(
        status="success",
        run_id="12345678-1234-4123-8123-123456789abc",
        wav_path="service/runs/a.wav",
        manifest_path="service/runs/a.manifest.json",
    )
    second = first.model_copy(update={"run_id": "22345678-1234-4123-8123-123456789abc"})
    index.remember(first)
    index.remember(second)
    with pytest.raises(ResultUnavailable):
        index.read(first.run_id)
    escaped = second.model_copy(
        update={
            "wav_path": "service/runs/../escape.wav",
            "manifest_path": "service/runs/../escape.manifest.json",
        }
    )
    index.remember(escaped)
    with pytest.raises(ResultUnavailable):
        index.read(escaped.run_id)


@pytest.mark.parametrize(
    ("header", "status", "expected"),
    [
        (None, 200, b"abcdef"),
        ("bytes=1-3", 206, b"bcd"),
        ("bytes=4-", 206, b"ef"),
        ("bytes=-2", 206, b"ef"),
        ("bytes=0-99", 206, b"abcdef"),
        ("bytes=7-", 416, b""),
        ("bytes=-0", 416, b""),
        ("bytes=0-1,4-5", 416, b""),
        ("bytes=-", 416, b""),
    ],
)
def test_audio_ranges(header: str | None, status: int, expected: bytes) -> None:
    actual_status, payload, _ = audio_slice(b"abcdef", header)
    assert (actual_status, payload) == (status, expected)
