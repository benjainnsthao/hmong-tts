"""Atomic, artifact-root-scoped storage for privacy-safe JSON reports."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol

from pydantic import BaseModel

from tts_workbench.artifacts.paths import (
    ARTIFACT_ROOT_ENV,
    ArtifactBoundaryError,
    get_artifact_root,
    require_under_artifact_root,
)


class JsonReportCollisionError(FileExistsError):
    """Raised when a report destination already exists."""


class JsonReportWriteError(RuntimeError):
    """Raised when a report cannot be committed atomically."""


class JsonSerializable(Protocol):
    """Minimal serialization contract accepted by the report store."""

    def model_dump(self, *, mode: str) -> object:
        """Return a JSON-compatible object."""


JsonSerializer = Callable[[JsonSerializable], str]
AtomicReplace = Callable[[str | Path, str | Path], None]


def serialize_json_report(report: JsonSerializable) -> str:
    """Serialize a report deterministically without embedding runtime paths."""

    return (
        json.dumps(
            report.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


class AtomicJsonReportStore:
    """Write one JSON report using a closed temporary file and atomic replace."""

    def __init__(
        self,
        *,
        artifact_root: Path | None = None,
        repository_root: Path | None = None,
        serializer: JsonSerializer = serialize_json_report,
        replace: AtomicReplace = os.replace,
    ) -> None:
        self._artifact_root = (
            get_artifact_root(repository_root=repository_root)
            if artifact_root is None
            else get_artifact_root(
                environ={ARTIFACT_ROOT_ENV: str(artifact_root)},
                repository_root=repository_root,
            )
        )
        self._serializer = serializer
        self._replace = replace

    def validate_destination(self, relative_output_path: str | Path) -> Path:
        """Resolve and collision-check an artifact-root-relative JSON destination."""

        if Path(relative_output_path).is_absolute():
            raise ArtifactBoundaryError("JSON report path must be artifact-root-relative")
        destination = require_under_artifact_root(
            Path(relative_output_path),
            artifact_root=self._artifact_root,
        )
        if destination.suffix.lower() != ".json":
            raise ArtifactBoundaryError("JSON report path must end in .json")
        if destination.exists():
            raise JsonReportCollisionError(
                f"Report destination already exists: {Path(relative_output_path).as_posix()}"
            )
        return destination

    def write(
        self,
        report: BaseModel,
        relative_output_path: str | Path,
    ) -> Path:
        """Commit a report and return its artifact-root-relative path."""

        destination = self.validate_destination(relative_output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        temporary_path: Path | None = None
        replace_attempted = False
        try:
            payload = self._serializer(report)
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix=f".{destination.name}.",
                suffix=".tmp",
                dir=destination.parent,
                delete=False,
            ) as temporary:
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = Path(temporary.name)

            if destination.exists():
                raise JsonReportCollisionError(
                    "Report destination appeared while the report was being prepared."
                )
            replace_attempted = True
            self._replace(temporary_path, destination)
            return destination.relative_to(self._artifact_root)
        except JsonReportCollisionError:
            raise
        except Exception as exc:
            if replace_attempted and destination.exists():
                with suppress(OSError):
                    destination.unlink()
            raise JsonReportWriteError("Unable to commit the JSON report atomically.") from exc
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
