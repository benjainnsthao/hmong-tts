from hmong_tts.environment.detect import training_failures


def test_training_readiness_requires_expected_gpu_and_tools() -> None:
    report = {
        "os": {"system": "Linux", "machine": "x86_64", "wsl": True},
        "python": {"supported": True},
        "git": {"available": True},
        "ffmpeg": {"available": False},
        "gpu": {"expected_rtx_4070_present": False},
        "pytorch": {"installed": False},
        "data_root": {"valid": False},
    }
    failures = training_failures(report)
    assert "FFmpeg is unavailable" in failures
    assert "RTX 4070 is not visible to nvidia-smi" in failures
    assert "PyTorch is not installed" in failures
    assert "HMONG_TTS_DATA_ROOT is not a valid external directory" in failures
