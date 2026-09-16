"""Packaged dashboard and protected, process-local playback routes."""

from importlib.resources import files
from typing import cast

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from tts_workbench.inference.prompts import ENGLISH_EXAMPLE, VIETNAMESE_SHA256
from tts_workbench.service.contracts import ServiceConfig
from tts_workbench.service.results import ResultIndex, ResultUnavailable, audio_slice


def _unavailable() -> JSONResponse:
    return JSONResponse(
        {
            "status": "failure",
            "category": "result_unavailable",
            "message": "Result unavailable. Generate a new result in this server session.",
        },
        status_code=404,
    )


def _index(request: Request) -> ResultIndex:
    index = cast(ResultIndex | None, request.app.state.result_index)
    if index is None:
        raise ResultUnavailable()
    return index


def attach_browser_routes(app: FastAPI, config: ServiceConfig) -> None:
    assets = files("tts_workbench.service").joinpath("static")

    @app.get("/", include_in_schema=False)
    def dashboard() -> Response:
        return Response(assets.joinpath("index.html").read_bytes(), media_type="text/html")

    @app.get("/ui/{asset}", include_in_schema=False)
    def static_asset(asset: str) -> Response:
        types = {"app.js": "text/javascript", "styles.css": "text/css"}
        if asset not in types:
            return _unavailable()
        return Response(assets.joinpath(asset).read_bytes(), media_type=types[asset])

    @app.get("/v1/ui-config")
    def ui_config() -> dict[str, object]:
        return {
            "max_input_characters": config.max_input_characters,
            "english_example": ENGLISH_EXAMPLE,
            "vietnamese_prompt_sha256": VIETNAMESE_SHA256,
            "history_limit": 8,
            "speaking_rate_min": 0.5,
            "speaking_rate_max": 2.0,
        }

    @app.get("/v1/runs/{run_id}")
    def result_metadata(run_id: str, request: Request) -> Response:
        try:
            manifest, _ = _index(request).read(run_id)
        except ResultUnavailable:
            return _unavailable()
        return JSONResponse(
            {
                "run_id": manifest.run_id,
                "model_id": manifest.model.model_id,
                "device": manifest.resolved_device,
                "duration_seconds": manifest.audio.duration_seconds,
                "sample_rate": manifest.audio.sample_rate,
                "seed": manifest.seed,
                "speaking_rate": manifest.generation_settings.speaking_rate,
                "model_load_seconds": manifest.timings.model_load_seconds,
                "synthesis_seconds": manifest.timings.synthesis_seconds,
                "prompt_provenance": manifest.prompt_provenance or "legacy_unverified",
                "language_quality_status": manifest.model.language_quality_status,
            }
        )

    @app.get("/v1/runs/{run_id}/audio")
    def result_audio(run_id: str, request: Request, download: bool = False) -> Response:
        try:
            _, audio = _index(request).read(run_id)
        except ResultUnavailable:
            return _unavailable()
        status, payload, headers = audio_slice(audio, request.headers.get("range"))
        disposition = "attachment" if download else "inline"
        headers["Content-Disposition"] = f'{disposition}; filename="tts-{run_id}.wav"'
        return Response(payload, status_code=status, media_type="audio/wav", headers=headers)
