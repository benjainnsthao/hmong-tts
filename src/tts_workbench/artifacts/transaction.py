"""Atomic WAV and success-manifest artifact transaction."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import tempfile
import wave
from collections.abc import Callable, Iterable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from tts_workbench.artifacts.paths import (
    ARTIFACT_ROOT_ENV,
    get_artifact_root,
    require_under_artifact_root,
)
from tts_workbench.inference.contracts import RunManifest, WaveformResult
from tts_workbench.inference.waveform import (
    InvalidWaveformError,
    WaveformMetadata,
    validate_waveform,
)


class ArtifactCollisionError(FileExistsError):
    """A successful run already owns one of the requested artifact paths."""


class ArtifactWriteError(OSError):
    """A transaction could not publish a valid WAV and success manifest."""


@dataclass(frozen=True)
class ArtifactTargets:
    """Validated absolute and root-relative paths for one run."""

    wav_path: Path
    manifest_path: Path
    relative_wav_path: str
    relative_manifest_path: str


@dataclass(frozen=True)
class CommittedAudio:
    """Validated temporary WAV facts supplied to the manifest builder."""

    metadata: WaveformMetadata
    wav_sha256: str


@dataclass(frozen=True)
class ArtifactCommit:
    """Root-relative result of a completed two-file transaction."""

    wav_path: str
    manifest_path: str
    manifest: RunManifest


ManifestBuilder = Callable[[CommittedAudio], RunManifest]
ReplaceFunction = Callable[[Path, Path], None]
ManifestSerializer = Callable[[RunManifest], str]


def write_pcm16_wave(path: Path, samples: Iterable[float], sample_rate: int) -> None:
    """Write structurally valid mono 16-bit PCM without quality analysis."""
    waveform = WaveformResult(samples=tuple(samples), sample_rate=sample_rate, channel_count=1)
    validate_waveform(waveform)
    pcm = b"".join(
        struct.pack("<h", round(max(-1.0, min(1.0, sample)) * 32767)) for sample in waveform.samples
    )
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm)


def _serialize_manifest(manifest: RunManifest) -> str:
    return (
        json.dumps(
            manifest.model_dump(mode="json", exclude_none=True),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n"
    )


class AtomicArtifactStore:
    """Commit a WAV first and publish its success manifest last."""

    def __init__(
        self,
        artifact_root: Path | None = None,
        *,
        repository_root: Path | None = None,
        replace: ReplaceFunction = os.replace,
        manifest_serializer: ManifestSerializer = _serialize_manifest,
    ) -> None:
        if artifact_root is None:
            self._artifact_root = get_artifact_root(repository_root=repository_root)
        else:
            self._artifact_root = get_artifact_root(
                environ={ARTIFACT_ROOT_ENV: str(artifact_root)},
                repository_root=repository_root,
            )
        self._replace = replace
        self._manifest_serializer = manifest_serializer

    def validate_destination(self, relative_wav_path: str) -> ArtifactTargets:
        """Resolve and collision-check one artifact-root-relative WAV destination."""
        wav_path = require_under_artifact_root(
            Path(relative_wav_path),
            artifact_root=self._artifact_root,
        )
        if wav_path.suffix.lower() != ".wav":
            raise ValueError("inference output must use a .wav suffix")
        relative_wav = wav_path.relative_to(self._artifact_root).as_posix()
        relative_manifest = relative_wav[:-4] + ".manifest.json"
        manifest_path = require_under_artifact_root(
            Path(relative_manifest),
            artifact_root=self._artifact_root,
        )
        if wav_path.exists() or manifest_path.exists():
            raise ArtifactCollisionError("artifact destination already exists")
        return ArtifactTargets(
            wav_path=wav_path,
            manifest_path=manifest_path,
            relative_wav_path=relative_wav,
            relative_manifest_path=relative_manifest,
        )

    def _temporary_path(self, destination: Path) -> Path:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            return Path(handle.name)

    def _safe_unlink(self, path: Path | None) -> None:
        if path is None:
            return
        validated = require_under_artifact_root(path, artifact_root=self._artifact_root)
        with suppress(FileNotFoundError):
            validated.unlink()

    @staticmethod
    def _reopen_wave(path: Path, expected: WaveformMetadata) -> WaveformMetadata:
        try:
            with wave.open(str(path), "rb") as handle:
                channel_count = handle.getnchannels()
                sample_width = handle.getsampwidth()
                sample_rate = handle.getframerate()
                sample_count = handle.getnframes()
                compression = handle.getcomptype()
                handle.readframes(sample_count)
        except (OSError, EOFError, wave.Error) as exc:
            raise InvalidWaveformError("written WAV could not be reopened") from exc
        if sample_width != 2 or compression != "NONE":
            raise InvalidWaveformError("written WAV is not uncompressed 16-bit PCM")
        if channel_count != 1 or channel_count != expected.channel_count:
            raise InvalidWaveformError("written WAV has an unexpected channel count")
        if sample_rate != expected.sample_rate:
            raise InvalidWaveformError("written WAV has an unexpected sample rate")
        if sample_count <= 0 or sample_count != expected.sample_count:
            raise InvalidWaveformError("written WAV has an unexpected frame count")
        return WaveformMetadata(
            sample_rate=sample_rate,
            channel_count=channel_count,
            sample_count=sample_count,
            duration_seconds=sample_count / sample_rate,
        )

    def commit(
        self,
        *,
        relative_wav_path: str,
        waveform: WaveformResult,
        build_manifest: ManifestBuilder,
    ) -> ArtifactCommit:
        """Atomically publish a validated WAV and then its success manifest."""
        targets = self.validate_destination(relative_wav_path)
        expected = validate_waveform(waveform)
        targets.wav_path.parent.mkdir(parents=True, exist_ok=True)
        require_under_artifact_root(
            targets.wav_path.parent,
            artifact_root=self._artifact_root,
        )

        temp_wav: Path | None = None
        temp_manifest: Path | None = None
        attempted_wav_replace = False
        attempted_manifest_replace = False
        try:
            temp_wav = self._temporary_path(targets.wav_path)
            write_pcm16_wave(temp_wav, waveform.samples, waveform.sample_rate)
            reopened = self._reopen_wave(temp_wav, expected)
            wav_sha256 = hashlib.sha256(temp_wav.read_bytes()).hexdigest()
            manifest = build_manifest(CommittedAudio(metadata=reopened, wav_sha256=wav_sha256))
            if manifest.wav_path != targets.relative_wav_path:
                raise ValueError("manifest WAV path does not match the transaction destination")
            serialized_manifest = self._manifest_serializer(manifest)

            temp_manifest = self._temporary_path(targets.manifest_path)
            temp_manifest.write_text(serialized_manifest, encoding="utf-8", newline="\n")

            if targets.wav_path.exists() or targets.manifest_path.exists():
                raise ArtifactCollisionError("artifact destination already exists")
            attempted_wav_replace = True
            self._replace(temp_wav, targets.wav_path)
            temp_wav = None
            attempted_manifest_replace = True
            self._replace(temp_manifest, targets.manifest_path)
            temp_manifest = None
        except (ArtifactCollisionError, InvalidWaveformError):
            self._safe_unlink(temp_wav)
            self._safe_unlink(temp_manifest)
            if attempted_manifest_replace:
                self._safe_unlink(targets.manifest_path)
            if attempted_wav_replace:
                self._safe_unlink(targets.wav_path)
            raise
        except Exception as exc:
            self._safe_unlink(temp_wav)
            self._safe_unlink(temp_manifest)
            if attempted_manifest_replace:
                self._safe_unlink(targets.manifest_path)
            if attempted_wav_replace:
                self._safe_unlink(targets.wav_path)
            raise ArtifactWriteError("atomic artifact transaction failed") from exc

        return ArtifactCommit(
            wav_path=targets.relative_wav_path,
            manifest_path=targets.relative_manifest_path,
            manifest=manifest,
        )
