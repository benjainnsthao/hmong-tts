"""Library-level orchestration for validated TTS inference transactions."""

from __future__ import annotations

import hashlib
import platform
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import ValidationError

from tts_workbench import __version__
from tts_workbench.artifacts.paths import ArtifactBoundaryError
from tts_workbench.artifacts.transaction import (
    ArtifactCollisionError,
    ArtifactWriteError,
    AtomicArtifactStore,
    CommittedAudio,
)
from tts_workbench.inference.adapter import (
    AdapterLifecycleError,
    DependencyUnavailableError,
    DeviceUnavailableError,
    ModelLoadError,
    SynthesisError,
    TTSAdapter,
    UnknownModelError,
)
from tts_workbench.inference.contracts import (
    FailureCategory,
    FailureDetail,
    InferenceRequest,
    InferenceResult,
    ManifestAudio,
    ManifestModel,
    ManifestRuntime,
    ManifestTimings,
    RunManifest,
)
from tts_workbench.inference.waveform import InvalidWaveformError, validate_waveform
from tts_workbench.models.schema import ModelEntry, ModelRegistry

Clock = Callable[[], float]
Now = Callable[[], datetime]
RunIdFactory = Callable[[], UUID]


def prompt_sha256(text: str) -> str:
    """Hash prompt content without persisting or logging the content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(UTC)


class InferenceExecutor:
    """Coordinate registry lookup, adapter execution, and atomic artifacts."""

    def __init__(
        self,
        *,
        registry: ModelRegistry,
        adapter: TTSAdapter,
        artifact_store: AtomicArtifactStore,
        clock: Clock = time.perf_counter,
        now: Now = _utc_now,
        run_id_factory: RunIdFactory = uuid4,
        workbench_version: str = __version__,
    ) -> None:
        self._registry = registry
        self._adapter = adapter
        self._artifact_store = artifact_store
        self._clock = clock
        self._now = now
        self._run_id_factory = run_id_factory
        self._workbench_version = workbench_version

    @staticmethod
    def _failure(
        run_id: str,
        category: FailureCategory,
        message: str,
    ) -> InferenceResult:
        return InferenceResult(
            run_id=run_id,
            status="failure",
            failure=FailureDetail(category=category, message=message),
        )

    def _validated_request(
        self,
        request: InferenceRequest | Mapping[str, Any],
    ) -> InferenceRequest:
        if isinstance(request, InferenceRequest):
            return request
        return InferenceRequest.model_validate(request)

    @staticmethod
    def _manifest_model(entry: ModelEntry) -> ManifestModel:
        return ManifestModel(
            model_id=entry.model_id,
            provider=entry.provider,
            repository=entry.repository,
            immutable_revision=entry.revision,
            architecture=entry.architecture,
            documented_language_tag=entry.documented_language_tag,
            weight_license=entry.weight_license,
            approved_use=entry.approved_use,
            redistribution_status=entry.redistribution_status,
            prompt_set_reference=entry.prompt_set_reference,
            language_quality_status=entry.language_quality_status,
        )

    def execute(
        self,
        request: InferenceRequest | Mapping[str, Any],
    ) -> InferenceResult:
        """Execute one request without exposing prompt text or absolute paths."""
        run_id = str(self._run_id_factory())
        started_at = self._now()
        try:
            validated = self._validated_request(request)
        except (ValidationError, ValueError, TypeError):
            return self._failure(
                run_id,
                FailureCategory.INVALID_REQUEST,
                "request validation failed",
            )

        try:
            model_entry = self._registry.by_id(validated.model_id)
        except KeyError:
            return self._failure(
                run_id,
                FailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL,
                "model is not approved by the audited registry",
            )
        if validated.prompt_set_reference != model_entry.prompt_set_reference:
            return self._failure(
                run_id,
                FailureCategory.INVALID_REQUEST,
                "prompt provenance does not match the registered model",
            )

        try:
            self._artifact_store.validate_destination(validated.output_wav_path)
        except ArtifactCollisionError:
            return self._failure(
                run_id,
                FailureCategory.ARTIFACT_COLLISION,
                "artifact destination already exists",
            )
        except (ArtifactBoundaryError, OSError, ValueError):
            return self._failure(
                run_id,
                FailureCategory.ARTIFACT_BOUNDARY_FAILURE,
                "artifact destination failed boundary validation",
            )

        load_started = self._clock()
        try:
            runtime = self._adapter.load(
                validated.model_id,
                validated.requested_device,
            )
        except (UnknownModelError, KeyError):
            return self._failure(
                run_id,
                FailureCategory.UNKNOWN_OR_UNAPPROVED_MODEL,
                "model is not approved by the audited registry",
            )
        except DependencyUnavailableError:
            return self._failure(
                run_id,
                FailureCategory.DEPENDENCY_UNAVAILABLE,
                "optional inference dependencies are unavailable",
            )
        except DeviceUnavailableError:
            return self._failure(
                run_id,
                FailureCategory.DEVICE_UNAVAILABLE,
                "requested inference device is unavailable",
            )
        except (ModelLoadError, AdapterLifecycleError):
            return self._failure(
                run_id,
                FailureCategory.MODEL_LOAD_FAILURE,
                "registered model could not be loaded",
            )
        load_seconds = max(0.0, self._clock() - load_started)

        synthesis_started = self._clock()
        try:
            waveform = self._adapter.synthesize(
                model_id=validated.model_id,
                text=validated.text,
                seed=validated.seed,
                generation_settings=validated.generation_settings,
            )
        except (SynthesisError, AdapterLifecycleError):
            return self._failure(
                run_id,
                FailureCategory.SYNTHESIS_FAILURE,
                "waveform synthesis failed",
            )
        synthesis_seconds = max(0.0, self._clock() - synthesis_started)

        try:
            validate_waveform(waveform)
        except InvalidWaveformError:
            return self._failure(
                run_id,
                FailureCategory.INVALID_WAVEFORM,
                "adapter returned an invalid waveform",
            )

        prompt_hash = prompt_sha256(validated.text)
        completed_at = self._now()

        def build_manifest(audio: CommittedAudio) -> RunManifest:
            return RunManifest(
                run_id=run_id,
                status="success",
                started_at=started_at,
                completed_at=completed_at,
                adapter=self._adapter.identity,
                registry_schema_version=self._registry.schema_version,
                model=self._manifest_model(model_entry),
                prompt_sha256=prompt_hash,
                requested_device=validated.requested_device,
                resolved_device=runtime.resolved_device,
                dtype=runtime.dtype,
                seed=validated.seed,
                generation_settings=validated.generation_settings,
                runtime=ManifestRuntime(
                    python_version=platform.python_version(),
                    workbench_version=self._workbench_version,
                    pytorch_version=runtime.pytorch_version,
                    transformers_version=runtime.transformers_version,
                ),
                timings=ManifestTimings(
                    model_load_seconds=load_seconds,
                    synthesis_seconds=synthesis_seconds,
                ),
                audio=ManifestAudio(
                    sample_rate=audio.metadata.sample_rate,
                    channel_count=1,
                    sample_count=audio.metadata.sample_count,
                    duration_seconds=audio.metadata.duration_seconds,
                    wav_sha256=audio.wav_sha256,
                ),
                wav_path=validated.output_wav_path,
            )

        try:
            committed = self._artifact_store.commit(
                relative_wav_path=validated.output_wav_path,
                waveform=waveform,
                build_manifest=build_manifest,
            )
        except ArtifactCollisionError:
            return self._failure(
                run_id,
                FailureCategory.ARTIFACT_COLLISION,
                "artifact destination already exists",
            )
        except InvalidWaveformError:
            return self._failure(
                run_id,
                FailureCategory.INVALID_WAVEFORM,
                "WAV structural validation failed",
            )
        except ArtifactBoundaryError:
            return self._failure(
                run_id,
                FailureCategory.ARTIFACT_BOUNDARY_FAILURE,
                "artifact destination failed boundary validation",
            )
        except (ArtifactWriteError, OSError, ValueError):
            return self._failure(
                run_id,
                FailureCategory.ARTIFACT_WRITE_FAILURE,
                "atomic artifact transaction failed",
            )

        return InferenceResult(
            run_id=run_id,
            status="success",
            wav_path=committed.wav_path,
            manifest_path=committed.manifest_path,
        )
