"""Provider-neutral inference contracts and execution boundaries."""

from tts_workbench.inference.adapter import TTSAdapter
from tts_workbench.inference.contracts import (
    AdapterIdentity,
    AdapterRuntime,
    AdapterState,
    FailureCategory,
    GenerationSettings,
    InferenceRequest,
    InferenceResult,
    RunManifest,
    WaveformResult,
)

__all__ = [
    "AdapterIdentity",
    "AdapterRuntime",
    "AdapterState",
    "FailureCategory",
    "GenerationSettings",
    "InferenceRequest",
    "InferenceResult",
    "RunManifest",
    "TTSAdapter",
    "WaveformResult",
]
