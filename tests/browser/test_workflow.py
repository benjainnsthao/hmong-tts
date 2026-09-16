"""Optional real Chromium checks; install Playwright separately from runtime dependencies."""

from __future__ import annotations

import os
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn

from tests.fakes.browser_server import browser_test_app

playwright = pytest.importorskip("playwright.sync_api")


@pytest.fixture
def dashboard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TTS_WORKBENCH_ARTIFACT_ROOT", str(tmp_path))
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            browser_test_app(tmp_path, port),
            host="127.0.0.1",
            port=port,
            access_log=False,
            log_level="error",
            proxy_headers=False,
        )
    )
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.02)
        assert server.started
        with playwright.sync_playwright() as engine:
            browser = engine.chromium.launch(
                executable_path=os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE"),
                headless=True,
            )
            page = browser.new_page(viewport={"width": 1440, "height": 1080})
            page.goto(f"http://127.0.0.1:{port}/")
            page.get_by_text("Connected · Ready for speech", exact=True).wait_for()
            yield page
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        listener.close()
        assert not thread.is_alive()


def test_generate_play_seek_download_history_and_mobile(dashboard, tmp_path: Path) -> None:
    page = dashboard
    failures = []
    page.on("pageerror", lambda error: failures.append(str(error)))
    assert page.locator("#generate").is_disabled()
    page.get_by_role("button", name="Load example").click()
    page.locator("#generate").click()
    page.get_by_text("Your audio is ready. Press play to listen.", exact=True).wait_for()
    page.wait_for_function("() => document.querySelector('audio').readyState >= 1")
    assert page.locator("audio").evaluate("audio => audio.duration") == 1
    page.locator("audio").evaluate("audio => audio.play()")
    page.wait_for_function("() => document.querySelector('audio').currentTime > 0.1")
    page.locator("audio").evaluate("audio => { audio.pause(); audio.currentTime = 0.6; }")
    assert page.locator("audio").evaluate("audio => audio.currentTime") >= 0.6
    with page.expect_download() as pending:
        page.get_by_role("link", name="Download WAV").click()
    download = pending.value
    destination = tmp_path / "download.wav"
    download.save_as(destination)
    assert destination.read_bytes().startswith(b"RIFF")
    page.locator("#prompt").fill("Synthetic second clip.")
    page.locator("#generate").click()
    page.wait_for_function("() => document.querySelectorAll('#history li').length === 2")
    page.locator("#history button").last.click()
    assert "Clip 1" in page.locator("#result-title").inner_text()
    assert page.evaluate("localStorage.length + sessionStorage.length") == 0
    assert page.evaluate("async () => (await caches.keys()).length") == 0
    screenshot = os.environ.get("TTS_BROWSER_SCREENSHOT")
    if screenshot:
        page.screenshot(path=screenshot, full_page=True)
    page.set_viewport_size({"width": 390, "height": 844})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.locator("#generate").is_visible()
    page.get_by_role("button", name="Clear list").click()
    assert page.locator("#history li").count() == 0
    page.reload()
    assert page.locator("#prompt").input_value() == ""
    assert not failures


def test_validation_safe_text_and_vietnamese_restriction(dashboard) -> None:
    page = dashboard
    page.locator("#prompt").fill(" " * 10)
    assert page.locator("#generate").is_disabled()
    page.locator("#prompt").fill("x" * 501)
    assert page.locator("#generate").is_disabled()
    marker = '<img src=x onerror="window.syntheticInjection=true">'
    page.locator("#prompt").fill(marker)
    page.locator("#generate").click()
    page.get_by_text("Your audio is ready. Press play to listen.", exact=True).wait_for()
    assert page.evaluate("window.syntheticInjection === undefined")
    assert page.locator("img").count() == 0
    page.locator("#model").select_option("fixture-vie")
    assert page.locator("#example").is_disabled()
    assert page.locator("#generate").is_disabled()
    assert "externally reviewed prompt" in page.locator("#model-note").inner_text()


def test_duplicate_submission_failures_and_disconnect(dashboard) -> None:
    page = dashboard
    calls = []

    def queued(route):
        calls.append(route.request.method)
        # The second click dispatched during fetch must not submit again.
        page.locator("#synthesis-form").evaluate(
            "form => form.dispatchEvent(new Event('submit', {cancelable: true}))"
        )
        route.fulfill(status=429, content_type="application/json", body='{"category":"queue_full"}')

    page.route("**/v1/synthesize", queued)
    page.get_by_role("button", name="Load example").click()
    page.locator("#generate").click()
    page.get_by_text("The workbench is busy with other requests.", exact=False).wait_for()
    assert calls == ["POST"]
    page.unroute("**/v1/synthesize", queued)
    page.route(
        "**/v1/synthesize",
        lambda route: route.fulfill(
            status=503, content_type="application/json", body='{"category":"device_unavailable"}'
        ),
    )
    page.locator("#generate").click()
    page.get_by_text("That device is unavailable.", exact=False).wait_for()
    page.unroute("**/v1/synthesize")
    lost = []

    def disconnect(route):
        lost.append(1)
        route.abort("connectionreset")

    page.route("**/v1/synthesize", disconnect)
    page.locator("#generate").click()
    page.get_by_text("The connection ended before a result arrived.", exact=False).wait_for()
    assert lost == [1]


def test_missing_runtime_status_disables_generation(dashboard) -> None:
    page = dashboard

    def missing(route):
        response = route.fetch()
        payload = response.json()
        payload["optional_runtime_ready"] = False
        route.fulfill(response=response, json=payload)

    page.route("**/ready", missing)
    page.get_by_role("button", name="Check connection").click()
    page.get_by_text("Install the mms extra", exact=False).wait_for()
    page.get_by_role("button", name="Load example").click()
    assert page.locator("#generate").is_disabled()
