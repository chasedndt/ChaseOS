"""Manual media reference intake for Creator Engine jobs.

This module records declared local media as metadata only. It reads the file to
compute size/hash evidence, but it does not copy media, run FFmpeg/ffprobe,
transcribe, publish, or promote anything into canonical ChaseOS memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

from .job_store import CreatorJobStore
from .models import SourceRecording
from .path_policy import ensure_within, relative_to_vault, resolve_vault_root
from .source_metadata import normalize_manual_source_metadata


VIDEO_SUFFIXES = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"}
AUDIO_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"}
SUPPORTED_MEDIA_SUFFIXES = VIDEO_SUFFIXES | AUDIO_SUFFIXES
FORBIDDEN_MEDIA_PATH_PARTS = {"secrets", "credentials"}


class MediaReferenceError(ValueError):
    """Raised when a manual media reference cannot be safely recorded."""


@dataclass
class ManualMediaReferencePreviewResult:
    source_recording_id: str
    media_path: str
    media_kind: str
    file_size_bytes: int
    file_sha256: str
    target_platforms: list[str] = field(default_factory=list)
    context_prompt_present: bool = False
    manual_source_metadata: dict[str, Any] = field(default_factory=dict)
    probe_status: str = "not_probed"
    copied_media: bool = False
    files_read: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_recording_id": self.source_recording_id,
            "media_path": self.media_path,
            "media_kind": self.media_kind,
            "file_size_bytes": self.file_size_bytes,
            "file_sha256": self.file_sha256,
            "target_platforms": list(self.target_platforms),
            "context_prompt_present": self.context_prompt_present,
            "manual_source_metadata": dict(self.manual_source_metadata),
            "probe_status": self.probe_status,
            "copied_media": self.copied_media,
            "files_read": list(self.files_read),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


@dataclass
class ManualMediaReferenceIntakeResult:
    job_id: str
    source_recording_id: str
    job: dict[str, Any]
    files_read: list[str] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source_recording_id": self.source_recording_id,
            "job": self.job,
            "files_read": list(self.files_read),
            "files_written": list(self.files_written),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


@dataclass
class _DeclaredMediaReference:
    media_file: Path
    source_ref: str
    media_kind: str
    file_size_bytes: int
    file_digest: str
    created_at: str
    modified_at: str
    warnings: list[str]


def preview_manual_media_reference(
    vault_root: str | Path,
    media_path: str | Path,
    *,
    source_recording_id: str | None = None,
    target_platforms: list[str] | None = None,
    context_prompt: str | None = None,
    manual_source_metadata: dict[str, Any] | None = None,
) -> ManualMediaReferencePreviewResult:
    """Validate a declared media file and return write-free reference metadata."""

    root = resolve_vault_root(vault_root)
    media = read_declared_media_reference(root, media_path)
    metadata = normalize_manual_source_metadata(manual_source_metadata)
    resolved_source_id = source_recording_id or f"manual-file-{media.file_digest[:12]}"
    return ManualMediaReferencePreviewResult(
        source_recording_id=resolved_source_id,
        media_path=media.source_ref,
        media_kind=media.media_kind,
        file_size_bytes=media.file_size_bytes,
        file_sha256=media.file_digest,
        target_platforms=list(target_platforms or []),
        context_prompt_present=bool(context_prompt),
        manual_source_metadata=metadata,
        files_read=[media.source_ref],
        warnings=media.warnings,
    )


def import_manual_media_reference(
    vault_root: str | Path,
    media_path: str | Path,
    *,
    job_store: CreatorJobStore | None = None,
    job_id: str | None = None,
    source_recording_id: str | None = None,
    target_platforms: list[str] | None = None,
    context_prompt: str | None = None,
    manual_source_metadata: dict[str, Any] | None = None,
) -> ManualMediaReferenceIntakeResult:
    """Record a declared media file as a runtime-local reference-only Creator job."""

    root = resolve_vault_root(vault_root)
    store = job_store or CreatorJobStore(root)
    media = read_declared_media_reference(root, media_path)
    metadata = normalize_manual_source_metadata(manual_source_metadata)
    resolved_source_id = source_recording_id or f"manual-file-{media.file_digest[:12]}"
    inputs: dict[str, Any] = {
        "manual_media_path": media.source_ref,
        "media_sha256": media.file_digest,
        "media_reference_only": True,
        "copied_media": False,
        "ffmpeg_probe_performed": False,
        "transcription_backend": "not_used_media_reference_only",
    }
    if context_prompt:
        inputs["context_prompt"] = context_prompt
    if metadata:
        inputs["manual_source_metadata"] = metadata

    job = store.create_job(
        source_adapter="manual_file",
        source_recording_id=resolved_source_id,
        target_platforms=list(target_platforms or []),
        inputs=inputs,
        warnings=media.warnings,
        job_id=job_id,
    )

    adapter_metadata: dict[str, Any] = {
        "source_kind": "manual_media_reference",
        "media_reference_only": True,
        "copied_media": False,
        "ffmpeg_probe_performed": False,
        "transcription_backend": "not_used_media_reference_only",
        "duration_source": "not_probed",
        "canonical_promotion": False,
    }
    if metadata:
        adapter_metadata["manual_source_metadata"] = metadata

    source_recording = SourceRecording(
        recording_id=resolved_source_id,
        adapter="manual_file",
        path=media.source_ref,
        media_kind=media.media_kind,
        file_size_bytes=media.file_size_bytes,
        sha256=media.file_digest,
        created_at=media.created_at,
        modified_at=media.modified_at,
        duration_seconds=None,
        probe_status="not_probed",
        trust_tier="tier-4",
        adapter_metadata=adapter_metadata,
    )
    source_path = store.write_artifact(
        job.job_id,
        "source_recording.json",
        source_recording.to_dict(),
        artifact_type="source_recording",
    )

    updated_job = store.load_job(job.job_id)
    updated_job["status"] = "intake_ready"
    updated_job["inputs"] = {**updated_job.get("inputs", {}), **inputs}
    updated_job["warnings"] = list(dict.fromkeys([*updated_job.get("warnings", []), *media.warnings]))
    job_path = store.save_job(updated_job)
    final_job = store.load_job(job.job_id)

    return ManualMediaReferenceIntakeResult(
        job_id=job.job_id,
        source_recording_id=resolved_source_id,
        job=final_job,
        files_read=[media.source_ref],
        files_written=[relative_to_vault(root, source_path), relative_to_vault(root, job_path)],
        warnings=media.warnings,
    )


def read_declared_media_reference(vault_root: str | Path, media_path: str | Path) -> _DeclaredMediaReference:
    root = resolve_vault_root(vault_root)
    media_file = _resolve_declared_media(root, media_path)
    _validate_media_file(root, media_file)

    file_digest = _sha256_file(media_file)
    stat = media_file.stat()
    return _DeclaredMediaReference(
        media_file=media_file,
        source_ref=relative_to_vault(root, media_file),
        media_kind=_media_kind(media_file.suffix),
        file_size_bytes=stat.st_size,
        file_digest=file_digest,
        created_at=_iso_from_timestamp(stat.st_ctime),
        modified_at=_iso_from_timestamp(stat.st_mtime),
        warnings=[],
    )


def _resolve_declared_media(vault_root: Path, media_path: str | Path) -> Path:
    declared = Path(media_path)
    candidate = declared.resolve() if declared.is_absolute() else (vault_root / declared).resolve()
    try:
        return ensure_within(vault_root, candidate)
    except ValueError as exc:
        raise MediaReferenceError(f"manual media file is outside the vault: {media_path}") from exc


def _validate_media_file(vault_root: Path, media_file: Path) -> None:
    if not media_file.exists():
        raise MediaReferenceError(f"manual media file does not exist: {media_file}")
    if not media_file.is_file():
        raise MediaReferenceError(f"manual media path is not a file: {media_file}")
    if media_file.suffix.lower() not in SUPPORTED_MEDIA_SUFFIXES:
        raise MediaReferenceError(
            "manual media extension must be one of: "
            + ", ".join(sorted(SUPPORTED_MEDIA_SUFFIXES))
        )
    if media_file.stat().st_size <= 0:
        raise MediaReferenceError("manual media file is empty")

    relative_parts = [part.lower() for part in Path(relative_to_vault(vault_root, media_file)).parts]
    if any(part in FORBIDDEN_MEDIA_PATH_PARTS for part in relative_parts):
        raise MediaReferenceError("manual media path crosses a forbidden secrets boundary")
    if any(part == ".env" or part.startswith(".env.") for part in relative_parts):
        raise MediaReferenceError("manual media path crosses a forbidden environment boundary")


def _media_kind(suffix: str) -> str:
    lowered = suffix.lower()
    if lowered in VIDEO_SUFFIXES:
        return "video"
    if lowered in AUDIO_SUFFIXES:
        return "audio"
    return "media"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iso_from_timestamp(timestamp: float) -> str:
    return (
        datetime.fromtimestamp(timestamp, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
