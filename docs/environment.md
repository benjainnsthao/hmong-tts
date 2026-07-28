# Workbench environment

Registry validation, configuration checks, privacy/artifact scanning, linting,
typing, and synthetic tests require only the locked Python 3.12 core
environment. They do not require PyTorch, Transformers, CUDA, network access,
or model downloads.

The optional MMS dependency group remains restricted to Linux x86-64. Historical
RTX 4070 validation evidence is retained in `reports/validation/` and the
original handoff is archived in
`docs/history/white_hmong_single_speaker/gpu_machine_handoff_phase0.md`.

M3 inference contracts, orchestration, structural WAV handling, registry
selection, and synthetic fake tests use only the core environment. Importing
`tts_workbench`, `tts_workbench.inference.contracts`, or the MMS/VITS adapter
module does not import PyTorch or Transformers. The optional real backend loads
those packages lazily only after an explicit approved-model request.

The adapter preserves `auto`, `cpu`, and `cuda` requests. `auto` resolves to
CUDA only when the optional runtime reports it available and otherwise resolves
to CPU. An explicit unavailable CUDA request fails with a stable
`device_unavailable` category. This minimal runtime decision is not the
generalized environment-readiness work deferred to M4.

The current `tts-workbench-env --require-training` report is a retained Phase 0
diagnostic. General `core_ready`, `cpu_inference_ready`, and
`cuda_inference_ready` capability reporting is deferred to a later workbench
milestone.

Use `--require-artifact-root` when the canonical external artifact boundary is
required. Reports include only artifact-root validity and an identifier-only
failure reason; they never include the resolved absolute root.
