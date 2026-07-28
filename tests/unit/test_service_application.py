from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from tests.fakes.inference import FakeAdapter, synthetic_registry
from tests.fakes.service import ImmediateCoordinator, service_environment
from tts_workbench.artifacts.transaction import AtomicArtifactStore
from tts_workbench.inference.contracts import (
    FailureCategory,
    FailureDetail,
    GenerationSettings,
    InferenceResult,
)
from tts_workbench.inference.execution import InferenceExecutor
from tts_workbench.service import application as application_module
from tts_workbench.service.application import ServiceRuntime, create_app
from tts_workbench.service.contracts import (
    ServiceConfig,
    ServiceFailureCategory,
)
from tts_workbench.service.coordinator import (
    BoundedInferenceCoordinator,
    CoordinatorFailure,
)

RUN_ID = "12345678-1234-4123-8123-123456789abc"
OUTPUT_ID = UUID("87654321-4321-4321-8321-cba987654321")


@pytest.fixture
def service_config() -> ServiceConfig:
    return ServiceConfig(
        schema_version=2,
        host="127.0.0.1",
        port=8000,
        max_input_characters=500,
        queue_capacity=2,
        queue_timeout_seconds=10,
        request_timeout_seconds=30,
        active_inference_operations=1,
        workers=1,
        model_instances=1,
        seeded_generation=True,
        public_deployment_enabled=False,
        normalization_endpoint_public=False,
        access_log=False,
        log_request_text=False,
        log_client_ip=False,
        artifact_output_prefix="service/runs",
    )


def success_result() -> InferenceResult:
    return InferenceResult(
        run_id=RUN_ID,
        status="success",
        wav_path="service/runs/fixture.wav",
        manifest_path="service/runs/fixture.manifest.json",
    )


def runtime_for(
    coordinator: ImmediateCoordinator,
    *,
    adapter: FakeAdapter | None = None,
    artifact_ready: bool = True,
    core_ready: bool = True,
    optional_runtime_ready: bool = False,
) -> tuple[ServiceRuntime, FakeAdapter]:
    owned_adapter = adapter or FakeAdapter()
    return (
        ServiceRuntime(
            registry=synthetic_registry(),
            adapter=owned_adapter,
            coordinator=coordinator,
            environment=service_environment(
                artifact_ready=artifact_ready,
                core_ready=core_ready,
                optional_runtime_ready=optional_runtime_ready,
            ),
            output_id_factory=lambda: OUTPUT_ID,
        ),
        owned_adapter,
    )


def test_application_lifecycle_starts_coordinator_and_unloads_adapter(
    service_config: ServiceConfig,
) -> None:
    coordinator = ImmediateCoordinator(result=success_result())
    runtime, adapter = runtime_for(coordinator)
    app = create_app(service_config, runtime_factory=lambda _: runtime)

    with TestClient(app) as client:
        assert coordinator.start_count == 1
        assert client.get("/health").status_code == 200
    assert coordinator.shutdown_count == 1
    assert adapter.unload_count == 1


def test_production_runtime_builds_one_lazy_owner_without_model_access(
    tmp_path: Path,
    service_config: ServiceConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = synthetic_registry()
    monkeypatch.setattr(application_module, "load_model_registry", lambda: registry)
    monkeypatch.setattr(
        application_module,
        "collect_environment",
        service_environment,
    )
    monkeypatch.setattr(
        application_module,
        "AtomicArtifactStore",
        lambda: AtomicArtifactStore(tmp_path),
    )

    runtime = application_module.production_runtime(service_config)

    assert runtime.registry is registry
    assert runtime.adapter.state.lifecycle == "unloaded"
    assert isinstance(runtime.coordinator, BoundedInferenceCoordinator)
    assert runtime.coordinator.state.admission == "closed"


def test_production_runtime_fails_closed_when_artifact_store_is_unavailable(
    service_config: ServiceConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        application_module,
        "load_model_registry",
        synthetic_registry,
    )
    monkeypatch.setattr(
        application_module,
        "collect_environment",
        lambda: service_environment(artifact_ready=False),
    )

    def unavailable_store() -> AtomicArtifactStore:
        raise ValueError("synthetic unavailable artifact boundary")

    monkeypatch.setattr(
        application_module,
        "AtomicArtifactStore",
        unavailable_store,
    )
    runtime = application_module.production_runtime(service_config)

    assert runtime.coordinator is None
    assert runtime.adapter.state.lifecycle == "unloaded"


def test_health_is_independent_of_model_cuda_and_artifact_state(
    service_config: ServiceConfig,
) -> None:
    coordinator = ImmediateCoordinator(result=success_result())
    runtime, _ = runtime_for(
        coordinator,
        artifact_ready=False,
        core_ready=False,
        optional_runtime_ready=False,
    )
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "schema_version": 1,
            "status": "healthy",
            "service_version": "0.4.0",
        }
        assert "hostname" not in response.text
        assert "client" not in response.text


def test_readiness_distinguishes_lazy_model_and_optional_runtime(
    service_config: ServiceConfig,
) -> None:
    coordinator = ImmediateCoordinator(result=success_result())
    runtime, adapter = runtime_for(coordinator)
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.get("/ready")
        payload = response.json()
        assert response.status_code == 200
        assert payload["status"] == "ready"
        assert payload["model_loaded"] is False
        assert payload["optional_runtime_ready"] is False
        assert payload["lazy_model_loading"] is True

        adapter.load("fixture-eng", "cpu")
        loaded = client.get("/ready").json()
        assert loaded["status"] == "ready"
        assert loaded["model_loaded"] is True


@pytest.mark.parametrize(
    ("artifact_ready", "core_ready", "admission"),
    [(False, True, "open"), (True, False, "open"), (True, True, "closed")],
)
def test_nonready_boundaries_return_stable_503(
    service_config: ServiceConfig,
    artifact_ready: bool,
    core_ready: bool,
    admission: str,
) -> None:
    coordinator = ImmediateCoordinator(
        result=success_result(),
        admission=admission,
    )
    runtime, _ = runtime_for(
        coordinator,
        artifact_ready=artifact_ready,
        core_ready=core_ready,
    )
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json()["status"] == "not_ready"
        assert response.json()["failure_categories"] == ["service_not_ready"]


def test_missing_coordinator_keeps_readiness_and_synthesis_closed(
    service_config: ServiceConfig,
) -> None:
    coordinator = ImmediateCoordinator(result=success_result())
    runtime, adapter = runtime_for(coordinator)
    degraded = ServiceRuntime(
        registry=runtime.registry,
        adapter=adapter,
        coordinator=None,
        environment=runtime.environment,
    )
    with TestClient(create_app(service_config, runtime_factory=lambda _: degraded)) as client:
        ready = client.get("/ready")
        synthesis = client.post(
            "/v1/synthesize",
            json={"model_id": "fixture-eng", "text": "synthetic marker"},
        )
    assert ready.status_code == 503
    assert ready.json()["queue"]["admission"] == "closed"
    assert synthesis.status_code == 503
    assert synthesis.json()["category"] == "service_not_ready"
    assert adapter.unload_count == 1


def test_models_are_exact_registry_metadata_without_quality_claims(
    service_config: ServiceConfig,
) -> None:
    coordinator = ImmediateCoordinator(result=success_result())
    runtime, _ = runtime_for(coordinator)
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.get("/v1/models")
    assert response.status_code == 200
    payload = response.json()
    assert payload["registry_schema_version"] == 1
    assert [model["model_id"] for model in payload["models"]] == [
        "fixture-eng",
        "fixture-vie",
    ]
    for model, entry in zip(payload["models"], runtime.registry.models, strict=True):
        assert model["repository"] == entry.repository
        assert model["immutable_revision"] == entry.revision
        assert model["documented_language_tag"] == entry.documented_language_tag
        assert model["approved_use"] == entry.approved_use
        assert model["redistribution_status"] == entry.redistribution_status
        assert model["prompt_set_reference"] == entry.prompt_set_reference
        assert model["language_quality_status"] == "not_evaluated"
    rendered = response.text.casefold()
    assert "supported" not in rendered
    assert "validated" not in rendered


def test_successful_synthesis_derives_path_and_provenance_and_forwards_settings(
    service_config: ServiceConfig,
) -> None:
    coordinator = ImmediateCoordinator(result=success_result())
    runtime, _ = runtime_for(coordinator)
    payload = {
        "schema_version": 1,
        "model_id": "fixture-eng",
        "text": "synthetic service marker",
        "requested_device": "cuda",
        "seed": 77,
        "generation_settings": {
            "noise_scale": 0.5,
            "noise_scale_duration": 0.6,
            "speaking_rate": 1.25,
        },
    }
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.post("/v1/synthesize", json=payload)
    assert response.status_code == 200
    assert response.json()["manifest_path"].endswith(".manifest.json")
    assert len(coordinator.requests) == 1
    internal = coordinator.requests[0]
    assert internal.output_wav_path == f"service/runs/{OUTPUT_ID}.wav"
    assert internal.prompt_set_reference == "builtin:synthetic-fixture-v1"
    assert internal.requested_device == "cuda"
    assert internal.seed == 77
    assert internal.generation_settings == GenerationSettings(
        noise_scale=0.5,
        noise_scale_duration=0.6,
        speaking_rate=1.25,
    )


def test_unknown_model_is_rejected_before_coordinator_submission(
    service_config: ServiceConfig,
) -> None:
    coordinator = ImmediateCoordinator(result=success_result())
    runtime, _ = runtime_for(coordinator)
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.post(
            "/v1/synthesize",
            json={"model_id": "missing-model", "text": "synthetic marker"},
        )
    assert response.status_code == 404
    assert response.json()["category"] == "unknown_or_unapproved_model"
    assert coordinator.requests == []


@pytest.mark.parametrize(
    "payload",
    [
        {"model_id": "fixture-eng", "text": ""},
        {"model_id": "fixture-eng", "text": " "},
        {
            "model_id": "fixture-eng",
            "text": "synthetic marker",
            "output_wav_path": "../escape.wav",
        },
        {
            "model_id": "fixture-eng",
            "text": "synthetic marker",
            "repository": "unapproved/repository",
        },
    ],
)
def test_validation_failure_is_sanitized_and_never_echoes_text(
    service_config: ServiceConfig,
    payload: dict[str, object],
) -> None:
    submitted_text = str(payload.get("text", ""))
    coordinator = ImmediateCoordinator(result=success_result())
    runtime, _ = runtime_for(coordinator)
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.post("/v1/synthesize", json=payload)
    assert response.status_code == 422
    assert response.json()["category"] == "invalid_request"
    if submitted_text.strip():
        assert submitted_text not in response.text
    assert "output_wav_path" not in response.text
    assert coordinator.requests == []


def test_prompt_and_client_identity_are_absent_from_responses_and_logs(
    service_config: ServiceConfig,
    caplog: pytest.LogCaptureFixture,
) -> None:
    marker = "synthetic privacy marker"
    coordinator = ImmediateCoordinator(result=success_result())
    runtime, _ = runtime_for(coordinator)
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.post(
            "/v1/synthesize",
            json={
                "model_id": "fixture-eng",
                "text": marker,
                "unexpected": "rejected",
            },
            headers={"x-synthetic-secret": "synthetic-header-marker"},
        )
    rendered = response.text.casefold()
    assert response.status_code == 422
    assert marker not in response.text
    assert "synthetic-header-marker" not in response.text
    assert "client" not in rendered
    assert "ip_address" not in rendered
    assert marker not in caplog.text
    assert "synthetic-header-marker" not in caplog.text


def test_configured_maximum_length_is_enforced_without_echo(
    service_config: ServiceConfig,
) -> None:
    short_config = service_config.model_copy(update={"max_input_characters": 10})
    coordinator = ImmediateCoordinator(result=success_result())
    runtime, _ = runtime_for(coordinator)
    marker = "synthetic length marker"
    with TestClient(create_app(short_config, runtime_factory=lambda _: runtime)) as client:
        response = client.post(
            "/v1/synthesize",
            json={"model_id": "fixture-eng", "text": marker},
        )
    assert response.status_code == 422
    assert marker not in response.text
    assert coordinator.requests == []


@pytest.mark.parametrize(
    ("category", "expected_status"),
    [
        (ServiceFailureCategory.SERVICE_NOT_READY, 503),
        (ServiceFailureCategory.QUEUE_FULL, 429),
        (ServiceFailureCategory.DEADLINE_TIMEOUT, 504),
        (ServiceFailureCategory.UNEXPECTED_INTERNAL_FAILURE, 500),
    ],
)
def test_coordinator_failures_have_stable_http_mappings(
    service_config: ServiceConfig,
    category: ServiceFailureCategory,
    expected_status: int,
) -> None:
    coordinator = ImmediateCoordinator(
        result=success_result(),
        failure=CoordinatorFailure(category, "backend content must not escape"),
    )
    runtime, _ = runtime_for(coordinator)
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.post(
            "/v1/synthesize",
            json={"model_id": "fixture-eng", "text": "synthetic marker"},
        )
    assert response.status_code == expected_status
    assert response.json()["category"] == category
    assert "backend content" not in response.text


def test_untyped_coordinator_exception_is_sanitized(
    service_config: ServiceConfig,
) -> None:
    class ExplodingCoordinator(ImmediateCoordinator):
        async def submit(self, request):  # type: ignore[no-untyped-def]
            self.requests.append(request)
            raise RuntimeError("private exception marker")

    coordinator = ExplodingCoordinator(result=success_result())
    runtime, _ = runtime_for(coordinator)
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.post(
            "/v1/synthesize",
            json={"model_id": "fixture-eng", "text": "synthetic marker"},
        )
    assert response.status_code == 500
    assert response.json()["category"] == "unexpected_internal_failure"
    assert "private exception marker" not in response.text


@pytest.mark.parametrize(
    ("category", "expected_status"),
    [
        (FailureCategory.INVALID_REQUEST, 422),
        (FailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL, 404),
        (FailureCategory.DEPENDENCY_UNAVAILABLE, 503),
        (FailureCategory.DEVICE_UNAVAILABLE, 503),
        (FailureCategory.MODEL_LOAD_FAILURE, 503),
        (FailureCategory.SYNTHESIS_FAILURE, 500),
        (FailureCategory.INVALID_WAVEFORM, 500),
        (FailureCategory.ARTIFACT_BOUNDARY_FAILURE, 500),
        (FailureCategory.ARTIFACT_COLLISION, 409),
        (FailureCategory.ARTIFACT_WRITE_FAILURE, 500),
    ],
)
def test_inference_failures_have_stable_http_mappings(
    service_config: ServiceConfig,
    category: FailureCategory,
    expected_status: int,
) -> None:
    result = InferenceResult(
        run_id=RUN_ID,
        status="failure",
        failure=FailureDetail(category=category, message="private backend detail"),
    )
    coordinator = ImmediateCoordinator(result=result)
    runtime, _ = runtime_for(coordinator)
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.post(
            "/v1/synthesize",
            json={"model_id": "fixture-eng", "text": "synthetic marker"},
        )
    assert response.status_code == expected_status
    assert response.json()["category"] == category
    assert "private backend detail" not in response.text


def test_full_m3_execution_commits_only_root_relative_success_references(
    tmp_path: Path,
    service_config: ServiceConfig,
) -> None:
    registry = synthetic_registry()
    adapter = FakeAdapter()
    executor = InferenceExecutor(
        registry=registry,
        adapter=adapter,
        artifact_store=AtomicArtifactStore(tmp_path),
    )

    async def immediate(work):  # type: ignore[no-untyped-def]
        return work()

    coordinator = BoundedInferenceCoordinator(
        worker=executor,
        pending_capacity=2,
        queue_timeout_seconds=10,
        execute_async=immediate,
    )
    runtime = ServiceRuntime(
        registry=registry,
        adapter=adapter,
        coordinator=coordinator,
        environment=service_environment(),
        output_id_factory=lambda: OUTPUT_ID,
    )
    marker = "synthetic transaction marker"
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.post(
            "/v1/synthesize",
            json={"model_id": "fixture-eng", "text": marker},
        )
    assert response.status_code == 200
    payload = response.json()
    wav_path = tmp_path / payload["wav_path"]
    manifest_path = tmp_path / payload["manifest_path"]
    assert wav_path.is_file()
    assert manifest_path.is_file()
    rendered_manifest = manifest_path.read_text(encoding="utf-8")
    assert marker not in rendered_manifest
    assert str(tmp_path.resolve()) not in response.text
    assert str(tmp_path.resolve()) not in rendered_manifest


def test_failed_full_execution_creates_no_artifacts(
    tmp_path: Path,
    service_config: ServiceConfig,
) -> None:
    registry = synthetic_registry()
    adapter = FakeAdapter(fail_synthesis=True)
    executor = InferenceExecutor(
        registry=registry,
        adapter=adapter,
        artifact_store=AtomicArtifactStore(tmp_path),
    )

    async def immediate(work):  # type: ignore[no-untyped-def]
        return work()

    coordinator = BoundedInferenceCoordinator(
        worker=executor,
        pending_capacity=1,
        queue_timeout_seconds=10,
        execute_async=immediate,
    )
    runtime = ServiceRuntime(
        registry=registry,
        adapter=adapter,
        coordinator=coordinator,
        environment=service_environment(),
    )
    with TestClient(create_app(service_config, runtime_factory=lambda _: runtime)) as client:
        response = client.post(
            "/v1/synthesize",
            json={"model_id": "fixture-eng", "text": "synthetic failure marker"},
        )
    assert response.status_code == 500
    assert response.json()["category"] == "synthesis_failure"
    assert not [path for path in tmp_path.rglob("*") if path.is_file()]


def test_openapi_generation_has_no_runtime_or_model_access(
    service_config: ServiceConfig,
) -> None:
    calls = 0

    def forbidden_runtime(_: ServiceConfig) -> ServiceRuntime:
        nonlocal calls
        calls += 1
        raise AssertionError("OpenAPI must not initialize runtime")

    app = create_app(service_config, runtime_factory=forbidden_runtime)
    schema = app.openapi()
    assert calls == 0
    assert set(schema["paths"]) == {
        "/health",
        "/ready",
        "/v1/models",
        "/v1/synthesize",
    }
    rendered = json.dumps(schema)
    assert "output_wav_path" not in rendered
    assert (
        "prompt_set_reference"
        not in schema["components"]["schemas"]["SynthesisRequest"]["properties"]
    )


def test_service_imports_are_lazy_and_no_cors_is_installed(
    repository_root: Path,
    service_config: ServiceConfig,
) -> None:
    code = (
        "import sys\n"
        "import tts_workbench.service.contracts\n"
        "import tts_workbench.service.coordinator\n"
        "import tts_workbench.service.application\n"
        "assert 'torch' not in sys.modules\n"
        "assert 'transformers' not in sys.modules\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    app = create_app(
        service_config,
        runtime_factory=lambda _: pytest.fail("lifespan must not run"),
    )
    assert app.user_middleware == []
    importlib.invalidate_caches()
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("hmong_tts.service")
