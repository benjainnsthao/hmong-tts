"""Bounded, process-local index of committed results, with descriptor-safe reads."""

from __future__ import annotations

import hashlib
import io
import os
import re
import stat
import wave
from collections import OrderedDict
from pathlib import Path, PurePosixPath
from threading import Lock

from tts_workbench.inference.contracts import InferenceResult, RunManifest

MAX_AUDIO_BYTES = 32 * 1024 * 1024
MAX_MANIFEST_BYTES = 64 * 1024
RUN_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


class ResultUnavailable(ValueError):
    """A result cannot be safely offered for browser playback."""


def _read_regular(root: Path, relative: str, limit: int) -> bytes:
    parts = relative.split("/")
    if (
        PurePosixPath(relative).is_absolute()
        or "\\" in relative
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ResultUnavailable()
    # Walk from / with directory descriptors: neither parent nor final symlinks
    # can redirect the read, including between validation and opening the file.
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in (*root.parts[1:], *parts[:-1]):
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        file_descriptor = os.open(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
        )
        with os.fdopen(file_descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
                raise ResultUnavailable()
            payload = stream.read(limit + 1)
            if len(payload) > limit:
                raise ResultUnavailable()
            return payload
    finally:
        os.close(descriptor)


class ResultIndex:
    def __init__(self, root: Path, prefix: str, capacity: int = 64) -> None:
        self.root = root
        self.prefix = prefix + "/"
        self.capacity = capacity
        self._results: OrderedDict[str, InferenceResult] = OrderedDict()
        self._lock = Lock()

    def remember(self, result: InferenceResult) -> None:
        if result.status != "success":
            return
        with self._lock:
            self._results[result.run_id] = result
            while len(self._results) > self.capacity:
                self._results.popitem(last=False)

    def read(self, run_id: str) -> tuple[RunManifest, bytes]:
        with self._lock:
            result = self._results.get(run_id)
        if result is None or not RUN_PATTERN.fullmatch(run_id):
            raise ResultUnavailable()
        wav_path, manifest_path = result.wav_path, result.manifest_path
        if (
            wav_path is None
            or manifest_path is None
            or not wav_path.startswith(self.prefix)
            or not wav_path.endswith(".wav")
            or manifest_path != wav_path.removesuffix(".wav") + ".manifest.json"
        ):
            raise ResultUnavailable()
        try:
            manifest = RunManifest.model_validate_json(
                _read_regular(self.root, manifest_path, MAX_MANIFEST_BYTES)
            )
            if manifest.run_id != run_id or manifest.wav_path != wav_path:
                raise ResultUnavailable()
            audio = _read_regular(self.root, wav_path, MAX_AUDIO_BYTES)
            if hashlib.sha256(audio).hexdigest() != manifest.audio.wav_sha256:
                raise ResultUnavailable()
            with wave.open(io.BytesIO(audio), "rb") as wav:
                if (
                    wav.getnchannels() != 1
                    or wav.getsampwidth() != 2
                    or wav.getframerate() != manifest.audio.sample_rate
                    or wav.getnframes() != manifest.audio.sample_count
                ):
                    raise ResultUnavailable()
            return manifest, audio
        except (OSError, ValueError, EOFError, wave.Error) as exc:
            raise ResultUnavailable() from exc


def audio_slice(audio: bytes, range_header: str | None) -> tuple[int, bytes, dict[str, str]]:
    headers = {"Accept-Ranges": "bytes"}
    if range_header is None:
        return 200, audio, headers
    match = re.fullmatch(r"bytes=(\d{0,12})-(\d{0,12})", range_header)
    size = len(audio)
    if match and (match[1] or match[2]):
        start = int(match[1]) if match[1] else max(0, size - int(match[2]))
        end = min(int(match[2]), size - 1) if match[1] and match[2] else size - 1
        if start <= end and start < size:
            headers["Content-Range"] = f"bytes {start}-{end}/{size}"
            return 206, audio[start : end + 1], headers
    headers["Content-Range"] = f"bytes */{size}"
    return 416, b"", headers
