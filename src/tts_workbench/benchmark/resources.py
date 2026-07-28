"""Optional point-in-time resource observations without telemetry."""

from __future__ import annotations

import importlib
import sys
from typing import Protocol

from tts_workbench.benchmark.contracts import ResourceMemoryObservation


class ResourceObserver(Protocol):
    """Provider-neutral seam for one point-in-time memory observation."""

    def observe(self) -> ResourceMemoryObservation:
        """Return available, unavailable, or not-requested memory values."""


class DefaultResourceObserver:
    """Use standard-library CPU data and an already-imported torch runtime when possible."""

    def __init__(self, *, requested: bool) -> None:
        self._requested = requested

    def observe(self) -> ResourceMemoryObservation:
        """Collect one snapshot without importing optional ML packages."""

        if not self._requested:
            return ResourceMemoryObservation(
                cpu_availability="not_requested",
                cuda_availability="not_requested",
            )
        cpu_peak = self._cpu_peak_rss()
        cuda_values = self._cuda_memory()
        return ResourceMemoryObservation(
            cpu_availability="available" if cpu_peak is not None else "unavailable",
            cpu_peak_rss_bytes=cpu_peak,
            cuda_availability="available" if cuda_values is not None else "unavailable",
            cuda_allocated_bytes=None if cuda_values is None else cuda_values[0],
            cuda_reserved_bytes=None if cuda_values is None else cuda_values[1],
        )

    @staticmethod
    def _cpu_peak_rss() -> int | None:
        try:
            resource = importlib.import_module("resource")
            peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        except (AttributeError, ImportError, OSError, TypeError, ValueError):
            return None
        if peak <= 0:
            return None
        return peak if sys.platform == "darwin" else peak * 1024

    @staticmethod
    def _cuda_memory() -> tuple[int, int] | None:
        torch = sys.modules.get("torch")
        if torch is None:
            return None
        try:
            cuda = torch.cuda
            if not bool(cuda.is_available()):
                return None
            return int(cuda.memory_allocated()), int(cuda.memory_reserved())
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return None
