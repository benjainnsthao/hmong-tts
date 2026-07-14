import math
import wave
from pathlib import Path

import pytest

from hmong_tts.inference.mms_smoke import write_pcm16_wave


def test_wav_writer_creates_valid_mono_pcm(tmp_path: Path) -> None:
    output = tmp_path / "synthetic.wav"
    write_pcm16_wave(output, [0.0, 0.25, -0.25], 16000)
    with wave.open(str(output), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getsampwidth() == 2
        assert handle.getframerate() == 16000
        assert handle.getnframes() == 3


@pytest.mark.parametrize("samples", [[], [math.nan], [math.inf]])
def test_wav_writer_rejects_empty_or_nonfinite(samples: list[float], tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_pcm16_wave(tmp_path / "bad.wav", samples, 16000)
