"""Path confinement helpers for Creator Engine artifacts."""

from __future__ import annotations

from pathlib import Path
import re


DEFAULT_JOB_ROOT = Path("runtime") / "creator_engine" / "jobs"


class CreatorEnginePathError(ValueError):
    """Raised when a Creator Engine path would escape its allowed boundary."""


def resolve_vault_root(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def ensure_within(base: str | Path, candidate: str | Path) -> Path:
    base_path = Path(base).resolve()
    candidate_path = Path(candidate).resolve()
    try:
        candidate_path.relative_to(base_path)
    except ValueError as exc:
        raise CreatorEnginePathError(f"path escapes allowed boundary: {candidate_path}") from exc
    return candidate_path


def resolve_job_root(vault_root: str | Path, job_root: str | Path | None = None) -> Path:
    root = resolve_vault_root(vault_root)
    configured = Path(job_root) if job_root is not None else DEFAULT_JOB_ROOT
    candidate = configured.resolve() if configured.is_absolute() else (root / configured).resolve()
    return ensure_within(root, candidate)


def safe_slug(value: str, default: str = "creator-job") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value).strip()).strip("-_").lower()
    if not cleaned:
        cleaned = default
    if cleaned in {".", ".."}:
        raise CreatorEnginePathError(f"invalid slug: {value!r}")
    return cleaned


def safe_relative_path(relative_path: str | Path) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        raise CreatorEnginePathError(f"absolute artifact path is not allowed: {relative_path}")
    if any(part in {"..", ""} for part in path.parts):
        raise CreatorEnginePathError(f"artifact path traversal is not allowed: {relative_path}")
    return path


def job_directory(
    vault_root: str | Path,
    job_id: str,
    job_root: str | Path | None = None,
    *,
    create: bool = False,
) -> Path:
    root = resolve_job_root(vault_root, job_root)
    directory = ensure_within(root, root / safe_slug(job_id))
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def artifact_path(
    vault_root: str | Path,
    job_id: str,
    relative_path: str | Path,
    job_root: str | Path | None = None,
    *,
    create_parent: bool = False,
) -> Path:
    directory = job_directory(vault_root, job_id, job_root)
    candidate = ensure_within(directory, directory / safe_relative_path(relative_path))
    if create_parent:
        candidate.parent.mkdir(parents=True, exist_ok=True)
    return candidate


def relative_to_vault(vault_root: str | Path, path: str | Path) -> str:
    root = resolve_vault_root(vault_root)
    confined = ensure_within(root, path)
    return confined.relative_to(root).as_posix()
