"""Real HTTP/queue/artifact workflow with synthetic audio, only for tests."""

import math
from pathlib import Path

from fastapi import FastAPI

from tests.fakes.inference import FakeAdapter, synthetic_registry
from tests.fakes.service import service_environment
from tts_workbench.artifacts.transaction import AtomicArtifactStore
from tts_workbench.config.loader import load_config
from tts_workbench.inference.contracts import WaveformResult
from tts_workbench.inference.execution import InferenceExecutor
from tts_workbench.inference.prompts import ENGLISH_REFERENCE, VIETNAMESE_REFERENCE
from tts_workbench.service.application import ServiceRuntime, create_app
from tts_workbench.service.contracts import ServiceConfig
from tts_workbench.service.coordinator import BoundedInferenceCoordinator


def browser_test_app(root: Path, port: int = 8000) -> FastAPI:
    config = ServiceConfig.model_validate(
        load_config("inference", Path("configs/inference/local.yaml")).model_dump()
    ).model_copy(update={"port": port})
    registry = synthetic_registry()
    registry.models[0] = registry.models[0].model_copy(
        update={"prompt_set_reference": ENGLISH_REFERENCE}
    )
    registry.models[1] = registry.models[1].model_copy(
        update={"prompt_set_reference": VIETNAMESE_REFERENCE}
    )
    adapter = FakeAdapter(
        waveform=WaveformResult(
            samples=tuple(0.2 * math.sin(2 * math.pi * 440 * i / 16000) for i in range(16000)),
            sample_rate=16000,
        )
    )
    executor = InferenceExecutor(
        registry=registry, adapter=adapter, artifact_store=AtomicArtifactStore(root)
    )
    coordinator = BoundedInferenceCoordinator(
        worker=executor, pending_capacity=2, queue_timeout_seconds=10
    )
    runtime = ServiceRuntime(
        registry=registry,
        adapter=adapter,
        coordinator=coordinator,
        environment=service_environment(optional_runtime_ready=True),
    )
    return create_app(config, runtime_factory=lambda _: runtime)
