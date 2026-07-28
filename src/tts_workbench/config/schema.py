"""Pydantic schema for active workbench configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from tts_workbench.benchmark.contracts import BenchmarkSettings
from tts_workbench.qc.contracts import QcThresholds


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InferenceConfig(StrictModel):
    schema_version: Literal[1]
    host: str
    port: int = Field(ge=1, le=65535)
    max_input_characters: int = Field(gt=0)
    max_normalized_tokens: int = Field(gt=0)
    workers: Literal[1]
    gpu_queue_concurrency: Literal[1]
    request_timeout_seconds: float = Field(gt=0)
    model_instances: Literal[1]
    seeded_generation: Literal[True]
    public_deployment_enabled: Literal[False]
    normalization_endpoint_public: Literal[False]
    log_request_text: Literal[False]
    log_client_ip: Literal[False]


CONFIG_MODELS: dict[str, type[BaseModel]] = {
    "benchmark": BenchmarkSettings,
    "inference": InferenceConfig,
    "qc": QcThresholds,
}
