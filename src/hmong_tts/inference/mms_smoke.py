"""Run a pinned, non-Hmong MMS inference smoke test outside the repository."""

from __future__ import annotations

import argparse
import math
import platform
import struct
import sys
import wave
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import cast

from hmong_tts.data.paths import DataBoundaryError, require_under_data_root

APPROVED_MODELS = {
    "facebook/mms-tts-eng": "c71de0fe7204c83f1c10820a7d696d0b450048ba",
    "facebook/mms-tts-vie": "b58928d033932a49aa8e3d6cf11625b25fe928d2",
}
DEFAULT_ENGLISH_TEXT = "hello my dog is cute"


def preflight_failures() -> list[str]:
    failures = []
    if platform.system() != "Linux":
        failures.append("the documented MMS environment is Linux/WSL2")
    if platform.machine().lower() not in {"x86_64", "amd64"}:
        failures.append("the locked MMS/CUDA path targets x86-64")
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except (ImportError, OSError) as exc:
        failures.append(f"MMS dependencies are unavailable ({type(exc).__name__})")
    return failures


def write_pcm16_wave(path: Path, samples: Iterable[float], sample_rate: int) -> None:
    values = list(samples)
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError("waveform must contain finite samples")
    pcm = b"".join(struct.pack("<h", round(max(-1.0, min(1.0, value)) * 32767)) for value in values)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(APPROVED_MODELS), default="facebook/mms-tts-eng")
    parser.add_argument(
        "--text-file", type=Path, help="UTF-8 prompt; required for the Vietnamese model"
    )
    parser.add_argument("--output", type=Path, default=Path("smoke/mms-eng.wav"))
    parser.add_argument("--seed", type=int, default=555)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--preflight-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    failures = preflight_failures()
    if failures:
        print("MMS smoke preflight failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 2
    if args.preflight_only:
        print("MMS smoke preflight passed.")
        return 0

    if args.model.endswith("-vie") and args.text_file is None:
        print(
            "Vietnamese smoke requires --text-file; no pronunciation text is invented.",
            file=sys.stderr,
        )
        return 2
    text = (
        args.text_file.read_text(encoding="utf-8").strip()
        if args.text_file
        else DEFAULT_ENGLISH_TEXT
    )
    if not text:
        print("Smoke-test text is empty.", file=sys.stderr)
        return 2
    try:
        output_path = require_under_data_root(args.output)
    except DataBoundaryError as exc:
        print(f"DATA BOUNDARY ERROR: {exc}", file=sys.stderr)
        return 2

    import torch
    from transformers import VitsModel, VitsTokenizer, set_seed

    revision = APPROVED_MODELS[args.model]
    tokenizer = VitsTokenizer.from_pretrained(args.model, revision=revision)
    model = VitsModel.from_pretrained(args.model, revision=revision)
    device: str = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device == "auto":
        device = "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        print("CUDA was requested but PyTorch cannot access it.", file=sys.stderr)
        return 2
    # Transformers decorates this override with Module.to's overloaded signature,
    # which MyPy exposes as an unbound wrapper even though this is a bound method.
    move_to_device = cast(Callable[[str], VitsModel], model.to)
    model = move_to_device(device)
    inputs = tokenizer(text=text, return_tensors="pt").to(device)
    set_seed(args.seed)
    with torch.no_grad():
        waveform = model(**inputs).waveform[0].detach().float().cpu()
    samples = waveform.tolist()
    write_pcm16_wave(output_path, samples, model.config.sampling_rate)
    with wave.open(str(output_path), "rb") as handle:
        if handle.getnchannels() != 1 or handle.getnframes() <= 0:
            raise RuntimeError("generated WAV failed structural validation")
    print(
        f"PASS model={args.model} revision={revision} rate={model.config.sampling_rate} "
        f"samples={len(samples)} output={output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
