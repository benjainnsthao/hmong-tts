"""Pydantic schema for active workbench configuration."""

from __future__ import annotations

from pydantic import BaseModel

from tts_workbench.benchmark.contracts import BenchmarkSettings
from tts_workbench.qc.contracts import QcThresholds
from tts_workbench.service.contracts import ServiceConfig

CONFIG_MODELS: dict[str, type[BaseModel]] = {
    "benchmark": BenchmarkSettings,
    "inference": ServiceConfig,
    "qc": QcThresholds,
}
