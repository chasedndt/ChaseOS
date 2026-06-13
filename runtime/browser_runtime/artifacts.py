"""Artifact path and screenshot evidence helpers for browser runtime runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.browser_runtime.logging import vault_root
from runtime.browser_runtime.models import BrowserArtifact, slugify


ALLOWED_BROWSER_ARTIFACT_DIRS = (
    "07_LOGS/Browser-Runs",
    "07_LOGS/Operator-Screenshots",
)


@dataclass(frozen=True)
class BrowserArtifactValidation:
    """Validation result for a browser runtime artifact path."""

    ok: bool
    status: str
    path: str
    artifact_type: str
    relative_path: str | None = None
    bytes: int = 0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def browser_run_artifact_path(
    run_id: str,
    filename_suffix: str,
    *,
    root: Path | str | None = None,
) -> Path:
    """Return a confined Browser-Runs artifact path for a run."""
    safe_run = slugify(run_id, "browser-runtime")
    safe_suffix = slugify(filename_suffix.lstrip(".") or "artifact", "artifact")
    return vault_root(root) / "07_LOGS" / "Browser-Runs" / f"{safe_run}-{safe_suffix}"


def _relative_posix(root_path: Path, candidate: Path) -> str | None:
    try:
        return candidate.relative_to(root_path).as_posix()
    except ValueError:
        return None


def validate_browser_artifact_path(
    path: Path | str,
    *,
    root: Path | str | None = None,
    artifact_type: str = "screenshot",
    require_exists: bool = False,
    min_bytes: int = 1,
    allowed_dirs: tuple[str, ...] = ALLOWED_BROWSER_ARTIFACT_DIRS,
) -> BrowserArtifactValidation:
    """Validate that a browser artifact stays inside declared evidence dirs."""
    root_path = vault_root(root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root_path / candidate
    resolved = candidate.resolve(strict=False)
    relative = _relative_posix(root_path, resolved)

    if relative is None:
        return BrowserArtifactValidation(
            ok=False,
            status="blocked_artifact_outside_vault_root",
            path=str(resolved),
            artifact_type=artifact_type,
            error="Artifact path resolves outside the vault root.",
        )

    allowed = any(relative == allowed or relative.startswith(f"{allowed}/") for allowed in allowed_dirs)
    if not allowed:
        return BrowserArtifactValidation(
            ok=False,
            status="blocked_artifact_outside_allowed_dirs",
            path=str(resolved),
            artifact_type=artifact_type,
            relative_path=relative,
            error="Artifact path is not under an allowed browser evidence directory.",
            metadata={"allowed_dirs": list(allowed_dirs)},
        )

    if require_exists and not resolved.exists():
        return BrowserArtifactValidation(
            ok=False,
            status="blocked_artifact_missing",
            path=str(resolved),
            artifact_type=artifact_type,
            relative_path=relative,
            error="Artifact file does not exist.",
        )

    size = resolved.stat().st_size if resolved.exists() else 0
    if require_exists and size < min_bytes:
        return BrowserArtifactValidation(
            ok=False,
            status="blocked_artifact_too_small",
            path=str(resolved),
            artifact_type=artifact_type,
            relative_path=relative,
            bytes=size,
            error=f"Artifact file is smaller than required minimum: {min_bytes} bytes.",
        )

    return BrowserArtifactValidation(
        ok=True,
        status="artifact_present" if require_exists else "artifact_path_allowed",
        path=str(resolved),
        artifact_type=artifact_type,
        relative_path=relative,
        bytes=size,
        metadata={"allowed_dirs": list(allowed_dirs)},
    )


def build_screenshot_artifact(
    path: Path | str,
    *,
    root: Path | str | None = None,
    description: str = "Browser runtime screenshot evidence.",
    redacted: bool = False,
    metadata: dict[str, Any] | None = None,
    min_bytes: int = 1,
) -> BrowserArtifact:
    """Build a BrowserArtifact for an existing, confined screenshot file."""
    validation = validate_browser_artifact_path(
        path,
        root=root,
        artifact_type="screenshot",
        require_exists=True,
        min_bytes=min_bytes,
    )
    if not validation.ok:
        raise ValueError(validation.error or validation.status)

    merged_metadata = {"bytes": validation.bytes, **(metadata or {})}
    return BrowserArtifact(
        artifact_type="screenshot",
        path=validation.relative_path or validation.path,
        description=description,
        redacted=redacted,
        metadata=merged_metadata,
    )
