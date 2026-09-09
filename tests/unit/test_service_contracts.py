from __future__ import annotations

import pytest
from pydantic import ValidationError

from tts_workbench.service.contracts import (
    HealthResponse,
    QueueAdmissionState,
    SanitizedServiceFailure,
    ServiceConfig,
    ServiceFailureCategory,
    SynthesisRequest,
)


def service_config_payload(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 2,
        "host": "127.0.0.1",
        "port": 8000,
        "max_input_characters": 500,
        "queue_capacity": 2,
        "queue_timeout_seconds": 10.0,
        "request_timeout_seconds": 30.0,
        "active_inference_operations": 1,
        "workers": 1,
        "model_instances": 1,
        "seeded_generation": True,
        "public_deployment_enabled": False,
        "normalization_endpoint_public": False,
        "access_log": False,
        "log_request_text": False,
        "log_client_ip": False,
        "artifact_output_prefix": "service/runs",
    }
    payload.update(changes)
    return payload


def test_service_contracts_are_strict_frozen_and_versioned() -> None:
    health = HealthResponse(service_version="0.5.0")
    with pytest.raises(ValidationError):
        HealthResponse.model_validate({**health.model_dump(), "hostname": "forbidden"})
    with pytest.raises(ValidationError):
        health.status = "other"  # type: ignore[assignment]

    request = SynthesisRequest(
        model_id="fixture-eng",
        text="synthetic service marker",
    )
    assert request.schema_version == 1
    assert "output_wav_path" not in SynthesisRequest.model_fields
    assert "prompt_set_reference" not in SynthesisRequest.model_fields
    assert "repository" not in SynthesisRequest.model_fields


@pytest.mark.parametrize(
    "host",
    ["0.0.0.0", "::", "192.0.2.1", "localhost", "example.test"],
)
def test_service_configuration_rejects_nonliteral_or_nonloopback_hosts(host: str) -> None:
    with pytest.raises(ValidationError):
        ServiceConfig.model_validate(service_config_payload(host=host))


@pytest.mark.parametrize("host", ["127.0.0.1", "::1"])
def test_service_configuration_accepts_only_literal_loopback_hosts(host: str) -> None:
    assert ServiceConfig.model_validate(service_config_payload(host=host)).host == host


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("workers", 2),
        ("model_instances", 2),
        ("active_inference_operations", 2),
        ("seeded_generation", False),
        ("public_deployment_enabled", True),
        ("access_log", True),
        ("log_request_text", True),
        ("log_client_ip", True),
    ],
)
def test_service_configuration_enforces_single_owner_and_privacy(
    field: str,
    value: object,
) -> None:
    with pytest.raises(ValidationError):
        ServiceConfig.model_validate(service_config_payload(**{field: value}))


@pytest.mark.parametrize(
    "prefix",
    ["../escape", "/absolute", r"service\runs", "service/./runs", "runs/file.wav"],
)
def test_service_configuration_rejects_unsafe_artifact_prefixes(prefix: str) -> None:
    with pytest.raises(ValidationError):
        ServiceConfig.model_validate(service_config_payload(artifact_output_prefix=prefix))


def test_queue_and_request_timeout_relationship_is_bounded() -> None:
    with pytest.raises(ValidationError):
        ServiceConfig.model_validate(
            service_config_payload(
                queue_timeout_seconds=31.0,
                request_timeout_seconds=30.0,
            )
        )


def test_queue_state_invariants_and_failure_contract() -> None:
    QueueAdmissionState(
        admission="full",
        pending_capacity=2,
        pending_requests=2,
        active_requests=1,
    )
    with pytest.raises(ValidationError):
        QueueAdmissionState(
            admission="full",
            pending_capacity=2,
            pending_requests=1,
            active_requests=0,
        )
    failure = SanitizedServiceFailure(
        category=ServiceFailureCategory.QUEUE_FULL,
        message="inference queue is full",
    )
    assert "text" not in failure.model_dump()
