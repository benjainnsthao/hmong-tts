# Environment target and observed host

## Supported project target

Ubuntu 24.04 on x86-64 WSL2 or native Linux, Python 3.12, Git, FFmpeg, an
NVIDIA-visible RTX 4070, and CUDA-enabled PyTorch. `hmong-tts-env` checks each
item and reports all failures in machine-readable JSON without emitting user or
host names.

## Observed on 2026-07-14

- Host: Windows 11 Home 10.0.26200, ARM64, Python 3.13.7.
- WSL: Ubuntu 24.04.3, kernel 6.6.87.2, `aarch64`, Python 3.12.3.
- Git: available (Windows 2.52.0; WSL 2.43.0).
- Missing: `uv` initially, FFmpeg, `nvidia-smi`, `nvcc`, PyTorch, CUDA.
- No RTX 4070 is visible in either context.

Core governance/config/tests can run with a managed Python 3.12 environment.
Audio processing, CUDA training, and the MMS inference smoke require the target
x86-64/GPU environment.
