# Workbench environment

Registry validation, configuration checks, privacy/artifact scanning, linting,
typing, and synthetic tests require only the locked Python 3.12 core
environment. They do not require PyTorch, Transformers, CUDA, network access,
or model downloads.

The optional MMS dependency group remains restricted to Linux x86-64. Historical
RTX 4070 validation evidence is retained in `reports/validation/` and the
original handoff is archived in
`docs/history/white_hmong_single_speaker/gpu_machine_handoff_phase0.md`.

The current `hmong-tts-env --require-training` report is a retained Phase 0
diagnostic. General `core_ready`, `cpu_inference_ready`, and
`cuda_inference_ready` capability reporting is deferred to a later workbench
milestone.
