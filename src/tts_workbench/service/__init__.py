"""Bounded, localhost-only inference service."""

from tts_workbench.service.application import create_app
from tts_workbench.service.contracts import ServiceConfig

__all__ = ["ServiceConfig", "create_app"]
