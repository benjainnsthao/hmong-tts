from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from tts_workbench.benchmark.resources import DefaultResourceObserver


def test_not_requested_memory_is_distinct_from_zero() -> None:
    observation = DefaultResourceObserver(requested=False).observe()
    assert observation.cpu_availability == "not_requested"
    assert observation.cuda_availability == "not_requested"
    assert observation.cpu_peak_rss_bytes is None
    assert observation.cuda_allocated_bytes is None


def test_requested_unavailable_memory_is_not_encoded_as_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        DefaultResourceObserver,
        "_cpu_peak_rss",
        staticmethod(lambda: None),
    )
    monkeypatch.setattr(
        DefaultResourceObserver,
        "_cuda_memory",
        staticmethod(lambda: None),
    )
    observation = DefaultResourceObserver(requested=True).observe()
    assert observation.cpu_availability == "unavailable"
    assert observation.cuda_availability == "unavailable"
    assert observation.cpu_peak_rss_bytes is None


def test_cuda_observation_uses_only_an_already_imported_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_cuda = SimpleNamespace(
        is_available=lambda: True,
        memory_allocated=lambda: 0,
        memory_reserved=lambda: 256,
    )
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=fake_cuda))
    assert DefaultResourceObserver._cuda_memory() == (0, 256)


def test_cuda_observation_does_not_import_optional_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(sys.modules, "torch", raising=False)
    assert DefaultResourceObserver._cuda_memory() is None
    assert "torch" not in sys.modules
