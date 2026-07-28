"""FastAPI application factory for bounded localhost-only inference."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from tts_workbench import __version__
from tts_workbench.artifacts.paths import ArtifactBoundaryError
from tts_workbench.artifacts.transaction import AtomicArtifactStore
from tts_workbench.environment.contracts import EnvironmentCapabilityReport
from tts_workbench.environment.detect import collect_environment
from tts_workbench.inference.adapter import AdapterLifecycleError, TTSAdapter
from tts_workbench.inference.contracts import (
    FailureCategory,
    InferenceRequest,
    InferenceResult,
)
from tts_workbench.inference.execution import InferenceExecutor
from tts_workbench.inference.mms_vits import MmsVitsAdapter
from tts_workbench.models.registry import load_model_registry
from tts_workbench.models.schema import ModelEntry, ModelRegistry
from tts_workbench.service.contracts import (
    HealthResponse,
    ModelListResponse,
    ModelMetadataResponse,
    ModelProvenanceResponse,
    QueueAdmissionState,
    ReadinessResponse,
    SanitizedServiceFailure,
    ServiceConfig,
    ServiceFailureCategory,
    SynthesisRequest,
    SynthesisSuccessResponse,
)
from tts_workbench.service.coordinator import (
    BoundedInferenceCoordinator,
    CoordinatorFailure,
    InferenceCoordinator,
)

RuntimeFactory = Callable[[ServiceConfig], "ServiceRuntime"]
OutputIdFactory = Callable[[], UUID]


@dataclass(frozen=True)
class ServiceRuntime:
    """One application-owned registry, adapter, coordinator, and readiness view."""

    registry: ModelRegistry
    adapter: TTSAdapter
    coordinator: InferenceCoordinator | None
    environment: EnvironmentCapabilityReport
    output_id_factory: OutputIdFactory = uuid4


def production_runtime(config: ServiceConfig) -> ServiceRuntime:
    """Create metadata and one runtime owner without loading a checkpoint."""

    registry = load_model_registry()
    adapter = MmsVitsAdapter(registry)
    environment = collect_environment()
    coordinator: InferenceCoordinator | None = None
    try:
        store = AtomicArtifactStore()
    except (ArtifactBoundaryError, OSError, ValueError):
        pass
    else:
        executor = InferenceExecutor(
            registry=registry,
            adapter=adapter,
            artifact_store=store,
        )
        coordinator = BoundedInferenceCoordinator(
            worker=executor,
            pending_capacity=config.queue_capacity,
            queue_timeout_seconds=min(
                config.queue_timeout_seconds,
                config.request_timeout_seconds,
            ),
        )
    return ServiceRuntime(
        registry=registry,
        adapter=adapter,
        coordinator=coordinator,
        environment=environment,
    )


def _model_response(entry: ModelEntry) -> ModelMetadataResponse:
    return ModelMetadataResponse(
        model_id=entry.model_id,
        provider=entry.provider,
        repository=entry.repository,
        immutable_revision=entry.revision,
        documented_language_tag=entry.documented_language_tag,
        language_tag_standard=entry.language_tag_standard,
        architecture=entry.architecture,
        weight_license=entry.weight_license,
        approved_use=entry.approved_use,
        redistribution_status=entry.redistribution_status,
        prompt_set_reference=entry.prompt_set_reference,
        language_quality_status=entry.language_quality_status,
        provenance=ModelProvenanceResponse(
            model_card_url=str(entry.provenance.model_card_url),
            license_url=str(entry.provenance.license_url),
            audit_reference=entry.provenance.audit_reference,
            audited_on=entry.provenance.audited_on.isoformat(),
        ),
    )


_FAILURE_MESSAGES: dict[ServiceFailureCategory, str] = {
    ServiceFailureCategory.INVALID_REQUEST: "request validation failed",
    ServiceFailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL: (
        "model is not approved by the audited registry"
    ),
    ServiceFailureCategory.SERVICE_NOT_READY: "service is not ready for inference",
    ServiceFailureCategory.QUEUE_FULL: "inference queue is full",
    ServiceFailureCategory.DEADLINE_TIMEOUT: "request expired before inference began",
    ServiceFailureCategory.DEPENDENCY_UNAVAILABLE: (
        "optional inference dependencies are unavailable"
    ),
    ServiceFailureCategory.DEVICE_UNAVAILABLE: "requested inference device is unavailable",
    ServiceFailureCategory.MODEL_LOAD_FAILURE: "registered model could not be loaded",
    ServiceFailureCategory.SYNTHESIS_FAILURE: "waveform synthesis failed",
    ServiceFailureCategory.INVALID_WAVEFORM: "adapter returned an invalid waveform",
    ServiceFailureCategory.ARTIFACT_BOUNDARY_FAILURE: (
        "artifact destination failed boundary validation"
    ),
    ServiceFailureCategory.ARTIFACT_COLLISION: "artifact destination already exists",
    ServiceFailureCategory.ARTIFACT_WRITE_FAILURE: "atomic artifact transaction failed",
    ServiceFailureCategory.UNEXPECTED_INTERNAL_FAILURE: (
        "service failed unexpectedly within the inference boundary"
    ),
}

_HTTP_STATUS: dict[ServiceFailureCategory, int] = {
    ServiceFailureCategory.INVALID_REQUEST: 422,
    ServiceFailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL: 404,
    ServiceFailureCategory.SERVICE_NOT_READY: 503,
    ServiceFailureCategory.QUEUE_FULL: 429,
    ServiceFailureCategory.DEADLINE_TIMEOUT: 504,
    ServiceFailureCategory.DEPENDENCY_UNAVAILABLE: 503,
    ServiceFailureCategory.DEVICE_UNAVAILABLE: 503,
    ServiceFailureCategory.MODEL_LOAD_FAILURE: 503,
    ServiceFailureCategory.SYNTHESIS_FAILURE: 500,
    ServiceFailureCategory.INVALID_WAVEFORM: 500,
    ServiceFailureCategory.ARTIFACT_BOUNDARY_FAILURE: 500,
    ServiceFailureCategory.ARTIFACT_COLLISION: 409,
    ServiceFailureCategory.ARTIFACT_WRITE_FAILURE: 500,
    ServiceFailureCategory.UNEXPECTED_INTERNAL_FAILURE: 500,
}

_INFERENCE_FAILURES: dict[FailureCategory, ServiceFailureCategory] = {
    FailureCategory.INVALID_REQUEST: ServiceFailureCategory.INVALID_REQUEST,
    FailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL: (
        ServiceFailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL
    ),
    FailureCategory.ARTIFACT_BOUNDARY_FAILURE: (ServiceFailureCategory.ARTIFACT_BOUNDARY_FAILURE),
    FailureCategory.DEPENDENCY_UNAVAILABLE: ServiceFailureCategory.DEPENDENCY_UNAVAILABLE,
    FailureCategory.DEVICE_UNAVAILABLE: ServiceFailureCategory.DEVICE_UNAVAILABLE,
    FailureCategory.MODEL_LOAD_FAILURE: ServiceFailureCategory.MODEL_LOAD_FAILURE,
    FailureCategory.SYNTHESIS_FAILURE: ServiceFailureCategory.SYNTHESIS_FAILURE,
    FailureCategory.INVALID_WAVEFORM: ServiceFailureCategory.INVALID_WAVEFORM,
    FailureCategory.ARTIFACT_COLLISION: ServiceFailureCategory.ARTIFACT_COLLISION,
    FailureCategory.ARTIFACT_WRITE_FAILURE: ServiceFailureCategory.ARTIFACT_WRITE_FAILURE,
}


def _failure_response(category: ServiceFailureCategory) -> JSONResponse:
    payload = SanitizedServiceFailure(
        category=category,
        message=_FAILURE_MESSAGES[category],
    )
    return JSONResponse(
        status_code=_HTTP_STATUS[category],
        content=payload.model_dump(mode="json"),
    )


def _runtime(request: Request) -> ServiceRuntime:
    return request.app.state.runtime  # type: ignore[no-any-return]


def create_app(
    config: ServiceConfig,
    *,
    runtime_factory: RuntimeFactory = production_runtime,
) -> FastAPI:
    """Build an app without initializing provider runtimes at module import."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
        runtime = runtime_factory(config)
        app.state.runtime = runtime
        if runtime.coordinator is not None:
            await runtime.coordinator.start()
        try:
            yield
        finally:
            if runtime.coordinator is not None:
                await runtime.coordinator.shutdown()
            with suppress(AdapterLifecycleError, OSError, RuntimeError):
                runtime.adapter.unload()

    app = FastAPI(
        title="Audited TTS Workbench Local Service",
        version=__version__,
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    @app.exception_handler(RequestValidationError)
    async def sanitized_validation_error(
        _request: Request,
        _error: RequestValidationError,
    ) -> JSONResponse:
        return _failure_response(ServiceFailureCategory.INVALID_REQUEST)

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(service_version=__version__)

    @app.get(
        "/ready",
        response_model=ReadinessResponse,
        responses={503: {"model": ReadinessResponse}},
    )
    async def ready(request: Request, response: Response) -> ReadinessResponse:
        runtime = _runtime(request)
        coordinator_state = (
            runtime.coordinator.state
            if runtime.coordinator is not None
            else _closed_queue_state(config)
        )
        admission_ready = (
            runtime.coordinator is not None and coordinator_state.admission != "closed"
        )
        artifact_ready = runtime.environment.artifact_root.valid
        core_ready = runtime.environment.core_ready
        is_ready = admission_ready and artifact_ready and core_ready
        if not is_ready:
            response.status_code = 503
        failures: list[ServiceFailureCategory] = []
        if not admission_ready or not artifact_ready or not core_ready:
            failures.append(ServiceFailureCategory.SERVICE_NOT_READY)
        return ReadinessResponse(
            status="ready" if is_ready else "not_ready",
            admission_ready=admission_ready,
            artifact_root_ready=artifact_ready,
            core_environment_ready=core_ready,
            optional_runtime_ready=(
                runtime.environment.cpu_inference_ready or runtime.environment.cuda_inference_ready
            ),
            model_loaded=runtime.adapter.state.lifecycle == "loaded",
            queue=coordinator_state,
            failure_categories=tuple(failures),
        )

    @app.get("/v1/models", response_model=ModelListResponse)
    async def models(request: Request) -> ModelListResponse:
        registry = _runtime(request).registry
        return ModelListResponse(
            registry_schema_version=registry.schema_version,
            models=tuple(_model_response(entry) for entry in registry.models),
        )

    @app.post(
        "/v1/synthesize",
        response_model=SynthesisSuccessResponse,
        responses={
            code: {"model": SanitizedServiceFailure} for code in sorted(set(_HTTP_STATUS.values()))
        },
    )
    async def synthesize(
        request: Request,
        synthesis_request: SynthesisRequest,
    ) -> SynthesisSuccessResponse | JSONResponse:
        runtime = _runtime(request)
        try:
            entry = runtime.registry.by_id(synthesis_request.model_id)
        except KeyError:
            return _failure_response(ServiceFailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL)
        if len(synthesis_request.text) > config.max_input_characters:
            return _failure_response(ServiceFailureCategory.INVALID_REQUEST)
        coordinator = runtime.coordinator
        if coordinator is None or coordinator.state.admission == "closed":
            return _failure_response(ServiceFailureCategory.SERVICE_NOT_READY)

        output_id = runtime.output_id_factory()
        internal_request = InferenceRequest(
            model_id=entry.model_id,
            text=synthesis_request.text,
            prompt_set_reference=entry.prompt_set_reference,
            requested_device=synthesis_request.requested_device,
            seed=synthesis_request.seed,
            generation_settings=synthesis_request.generation_settings,
            output_wav_path=(f"{config.artifact_output_prefix}/{output_id}.wav"),
        )
        try:
            result = await coordinator.submit(internal_request)
        except CoordinatorFailure as exc:
            return _failure_response(exc.category)
        except Exception:
            return _failure_response(ServiceFailureCategory.UNEXPECTED_INTERNAL_FAILURE)
        return _result_response(result)

    return app


def _closed_queue_state(config: ServiceConfig) -> QueueAdmissionState:
    return QueueAdmissionState(
        admission="closed",
        pending_capacity=config.queue_capacity,
        pending_requests=0,
        active_requests=0,
    )


def _result_response(
    result: InferenceResult,
) -> SynthesisSuccessResponse | JSONResponse:
    if result.status == "failure":
        assert result.failure is not None
        category = _INFERENCE_FAILURES.get(
            result.failure.category,
            ServiceFailureCategory.UNEXPECTED_INTERNAL_FAILURE,
        )
        return _failure_response(category)
    assert result.wav_path is not None
    assert result.manifest_path is not None
    return SynthesisSuccessResponse(
        run_id=result.run_id,
        wav_path=result.wav_path,
        manifest_path=result.manifest_path,
    )
