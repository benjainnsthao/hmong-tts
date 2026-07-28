"""M3-only structural waveform validation."""

from __future__ import annotations

import math
from dataclasses import dataclass

from tts_workbench.inference.contracts import WaveformResult


class InvalidWaveformError(ValueError):
    """Raised when a waveform cannot be safely committed as mono PCM."""


@dataclass(frozen=True)
class WaveformMetadata:
    """Structural facts needed for a WAV success manifest."""

    sample_rate: int
    channel_count: int
    sample_count: int
    duration_seconds: float


def validate_waveform(waveform: WaveformResult) -> WaveformMetadata:
    """Validate only the structural invariants required by milestone M3."""
    if not waveform.samples:
        raise InvalidWaveformError("waveform is empty")
    if not all(math.isfinite(sample) for sample in waveform.samples):
        raise InvalidWaveformError("waveform contains nonfinite samples")
    if waveform.sample_rate <= 0:
        raise InvalidWaveformError("sample rate must be positive")
    if waveform.channel_count != 1:
        raise InvalidWaveformError("only mono PCM output is supported")
    sample_count = len(waveform.samples)
    return WaveformMetadata(
        sample_rate=waveform.sample_rate,
        channel_count=waveform.channel_count,
        sample_count=sample_count,
        duration_seconds=sample_count / waveform.sample_rate,
    )
