"""Provided-transcript intake for Creator Engine jobs.

This pass treats declared transcript files as untrusted source content. It stores
runtime-local artifacts only and never promotes content into canonical memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .job_store import CreatorJobStore
from .models import SourceRecording, TranscriptArtifact
from .path_policy import artifact_path, ensure_within, relative_to_vault, resolve_vault_root
from .source_metadata import normalize_manual_source_metadata


SUPPORTED_TRANSCRIPT_SUFFIXES = {".md", ".txt", ".srt", ".vtt"}
FORBIDDEN_TRANSCRIPT_PATH_PARTS = {"secrets", "credentials"}
INSTRUCTION_LIKE_PATTERNS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "system prompt",
    "developer message",
    "delete files",
    "run this command",
    "execute this command",
)


class TranscriptIntakeError(ValueError):
    """Raised when a provided transcript cannot be safely imported."""


@dataclass
class ProvidedTranscriptIntakeResult:
    job_id: str
    source_recording_id: str
    transcript_artifact_id: str
    job: dict[str, Any]
    files_read: list[str] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source_recording_id": self.source_recording_id,
            "transcript_artifact_id": self.transcript_artifact_id,
            "job": self.job,
            "files_read": list(self.files_read),
            "files_written": list(self.files_written),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


@dataclass
class ProvidedTranscriptPreviewResult:
    source_recording_id: str
    transcript_path: str
    file_size_bytes: int
    file_sha256: str
    content_sha256: str
    word_count: int
    target_platforms: list[str] = field(default_factory=list)
    context_prompt_present: bool = False
    manual_source_metadata: dict[str, Any] = field(default_factory=dict)
    files_read: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_recording_id": self.source_recording_id,
            "transcript_path": self.transcript_path,
            "file_size_bytes": self.file_size_bytes,
            "file_sha256": self.file_sha256,
            "content_sha256": self.content_sha256,
            "word_count": self.word_count,
            "target_platforms": list(self.target_platforms),
            "context_prompt_present": self.context_prompt_present,
            "manual_source_metadata": dict(self.manual_source_metadata),
            "files_read": list(self.files_read),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


@dataclass
class ProvidedTranscriptAttachmentPreviewResult:
    attach_to_job_id: str
    source_recording_id: str
    transcript_path: str
    file_size_bytes: int
    file_sha256: str
    content_sha256: str
    word_count: int
    existing_job_status: str
    existing_source_adapter: str
    target_platforms: list[str] = field(default_factory=list)
    context_prompt_present: bool = False
    manual_source_metadata: dict[str, Any] = field(default_factory=dict)
    files_read: list[str] = field(default_factory=list)
    files_would_write: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attach_to_job_id": self.attach_to_job_id,
            "source_recording_id": self.source_recording_id,
            "transcript_path": self.transcript_path,
            "file_size_bytes": self.file_size_bytes,
            "file_sha256": self.file_sha256,
            "content_sha256": self.content_sha256,
            "word_count": self.word_count,
            "existing_job_status": self.existing_job_status,
            "existing_source_adapter": self.existing_source_adapter,
            "target_platforms": list(self.target_platforms),
            "context_prompt_present": self.context_prompt_present,
            "manual_source_metadata": dict(self.manual_source_metadata),
            "files_read": list(self.files_read),
            "files_would_write": list(self.files_would_write),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


@dataclass
class ProvidedTranscriptAttachmentResult:
    job_id: str
    source_recording_id: str
    transcript_artifact_id: str
    job: dict[str, Any]
    files_read: list[str] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source_recording_id": self.source_recording_id,
            "transcript_artifact_id": self.transcript_artifact_id,
            "job": self.job,
            "files_read": list(self.files_read),
            "files_written": list(self.files_written),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


@dataclass
class _DeclaredTranscriptContent:
    transcript_file: Path
    source_ref: str
    raw_bytes: bytes
    normalized_text: str
    file_digest: str
    content_digest: str
    created_at: str
    modified_at: str
    warnings: list[str]


def import_provided_transcript(
    vault_root: str | Path,
    transcript_path: str | Path,
    *,
    job_store: CreatorJobStore | None = None,
    job_id: str | None = None,
    source_recording_id: str | None = None,
    target_platforms: list[str] | None = None,
    context_prompt: str | None = None,
    manual_source_metadata: dict[str, Any] | None = None,
) -> ProvidedTranscriptIntakeResult:
    """Import a declared transcript file into a runtime-local Creator Engine job."""

    root = resolve_vault_root(vault_root)
    store = job_store or CreatorJobStore(root)
    content = _read_declared_transcript(root, transcript_path)
    metadata = normalize_manual_source_metadata(manual_source_metadata)
    resolved_source_id = source_recording_id or f"provided-transcript-{content.content_digest[:12]}"
    inputs: dict[str, Any] = {
        "provided_transcript_path": content.source_ref,
        "content_sha256": content.content_digest,
        "copied_media": False,
        "transcription_backend": "not_used_provided_transcript",
    }
    if context_prompt:
        inputs["context_prompt"] = context_prompt
    if metadata:
        inputs["manual_source_metadata"] = metadata

    job = store.create_job(
        source_adapter="provided_transcript",
        source_recording_id=resolved_source_id,
        target_platforms=list(target_platforms or []),
        inputs=inputs,
        warnings=content.warnings,
        job_id=job_id,
    )

    adapter_metadata: dict[str, Any] = {
        "source_kind": "provided_transcript",
        "content_sha256": content.content_digest,
        "normalized_line_endings": True,
        "copied_media": False,
        "transcript_trust_tier": "tier-4",
    }
    if metadata:
        adapter_metadata["manual_source_metadata"] = metadata

    source_recording = SourceRecording(
        recording_id=resolved_source_id,
        adapter="provided_transcript",
        path=content.source_ref,
        media_kind="transcript",
        file_size_bytes=len(content.raw_bytes),
        sha256=content.file_digest,
        created_at=content.created_at,
        modified_at=content.modified_at,
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
    raw_transcript_path = store.write_artifact(
        job.job_id,
        "transcripts/transcript.raw.md",
        content.normalized_text,
        artifact_type="transcript_raw",
    )

    transcript_artifact = TranscriptArtifact(
        artifact_id=f"transcript-{content.content_digest[:12]}",
        job_id=job.job_id,
        source_recording_id=resolved_source_id,
        transcript_path=relative_to_vault(root, raw_transcript_path),
        status="provided",
        word_count=_word_count(content.normalized_text),
        transformation_chain=[
            {
                "step": "provided_transcript_read",
                "source_path": content.source_ref,
                "file_sha256": content.file_digest,
                "content_sha256": content.content_digest,
                "external_call": False,
            },
            {
                "step": "runtime_local_transcript_artifact_write",
                "artifact_path": relative_to_vault(root, raw_transcript_path),
                "canonical_promotion": False,
            },
        ],
        warnings=content.warnings,
    )
    transcript_artifact_path = store.write_artifact(
        job.job_id,
        "transcripts/transcript_artifact.json",
        transcript_artifact.to_dict(),
        artifact_type="transcript_artifact",
    )

    updated_job = store.load_job(job.job_id)
    updated_job["status"] = "transcript_ready"
    updated_job["inputs"] = {**updated_job.get("inputs", {}), **inputs}
    updated_job["warnings"] = list(dict.fromkeys([*updated_job.get("warnings", []), *content.warnings]))
    job_path = store.save_job(updated_job)
    final_job = store.load_job(job.job_id)

    files_written = [
        relative_to_vault(root, source_path),
        relative_to_vault(root, raw_transcript_path),
        relative_to_vault(root, transcript_artifact_path),
        relative_to_vault(root, job_path),
    ]
    return ProvidedTranscriptIntakeResult(
        job_id=job.job_id,
        source_recording_id=resolved_source_id,
        transcript_artifact_id=transcript_artifact.artifact_id,
        job=final_job,
        files_read=[content.source_ref],
        files_written=files_written,
        warnings=content.warnings,
    )


def preview_provided_transcript(
    vault_root: str | Path,
    transcript_path: str | Path,
    *,
    source_recording_id: str | None = None,
    target_platforms: list[str] | None = None,
    context_prompt: str | None = None,
    manual_source_metadata: dict[str, Any] | None = None,
) -> ProvidedTranscriptPreviewResult:
    """Validate a declared transcript and return write-free ingest metadata."""

    root = resolve_vault_root(vault_root)
    content = _read_declared_transcript(root, transcript_path)
    metadata = normalize_manual_source_metadata(manual_source_metadata)
    resolved_source_id = source_recording_id or f"provided-transcript-{content.content_digest[:12]}"
    return ProvidedTranscriptPreviewResult(
        source_recording_id=resolved_source_id,
        transcript_path=content.source_ref,
        file_size_bytes=len(content.raw_bytes),
        file_sha256=content.file_digest,
        content_sha256=content.content_digest,
        word_count=_word_count(content.normalized_text),
        target_platforms=list(target_platforms or []),
        context_prompt_present=bool(context_prompt),
        manual_source_metadata=metadata,
        files_read=[content.source_ref],
        warnings=content.warnings,
    )


def preview_provided_transcript_attachment(
    vault_root: str | Path,
    transcript_path: str | Path,
    *,
    attach_to_job_id: str,
    job_store: CreatorJobStore | None = None,
    target_platforms: list[str] | None = None,
    context_prompt: str | None = None,
    manual_source_metadata: dict[str, Any] | None = None,
) -> ProvidedTranscriptAttachmentPreviewResult:
    """Validate attaching a provided transcript to an existing media job without writes."""

    root = resolve_vault_root(vault_root)
    store = job_store or CreatorJobStore(root, create_root=False)
    content = _read_declared_transcript(root, transcript_path)
    job, source_recording_ref = _load_attachable_manual_media_job(root, store, attach_to_job_id)
    _ensure_no_existing_transcript(root, store, attach_to_job_id, job)
    _ensure_attachable_status(job)
    metadata = normalize_manual_source_metadata(manual_source_metadata)
    source_recording_id = str(job.get("source_recording_id") or "")
    job_ref = relative_to_vault(root, artifact_path(root, attach_to_job_id, "job.json", store.job_root))
    return ProvidedTranscriptAttachmentPreviewResult(
        attach_to_job_id=str(job.get("job_id", attach_to_job_id)),
        source_recording_id=source_recording_id,
        transcript_path=content.source_ref,
        file_size_bytes=len(content.raw_bytes),
        file_sha256=content.file_digest,
        content_sha256=content.content_digest,
        word_count=_word_count(content.normalized_text),
        existing_job_status=str(job.get("status", "")),
        existing_source_adapter=str(job.get("source_adapter", "")),
        target_platforms=_merged_target_platforms(job, target_platforms),
        context_prompt_present=bool(context_prompt),
        manual_source_metadata=metadata,
        files_read=[job_ref, source_recording_ref, content.source_ref],
        files_would_write=[
            relative_to_vault(root, artifact_path(root, attach_to_job_id, "transcripts/transcript.raw.md", store.job_root)),
            relative_to_vault(
                root,
                artifact_path(root, attach_to_job_id, "transcripts/transcript_artifact.json", store.job_root),
            ),
            job_ref,
        ],
        warnings=content.warnings,
    )


def attach_provided_transcript_to_job(
    vault_root: str | Path,
    transcript_path: str | Path,
    *,
    attach_to_job_id: str,
    job_store: CreatorJobStore | None = None,
    target_platforms: list[str] | None = None,
    context_prompt: str | None = None,
    manual_source_metadata: dict[str, Any] | None = None,
) -> ProvidedTranscriptAttachmentResult:
    """Attach a provided transcript to an existing manual-media Creator Engine job."""

    root = resolve_vault_root(vault_root)
    store = job_store or CreatorJobStore(root)
    content = _read_declared_transcript(root, transcript_path)
    job, source_recording_ref = _load_attachable_manual_media_job(root, store, attach_to_job_id)
    _ensure_no_existing_transcript(root, store, attach_to_job_id, job)
    _ensure_attachable_status(job)
    metadata = normalize_manual_source_metadata(manual_source_metadata)
    source_recording_id = str(job.get("source_recording_id") or "")

    raw_transcript_path = store.write_artifact(
        attach_to_job_id,
        "transcripts/transcript.raw.md",
        content.normalized_text,
        artifact_type="transcript_raw",
    )
    transcript_artifact = TranscriptArtifact(
        artifact_id=f"transcript-{content.content_digest[:12]}",
        job_id=str(job.get("job_id", attach_to_job_id)),
        source_recording_id=source_recording_id,
        transcript_path=relative_to_vault(root, raw_transcript_path),
        status="provided",
        word_count=_word_count(content.normalized_text),
        transformation_chain=[
            {
                "step": "provided_transcript_attached_to_existing_media_job",
                "job_id": str(job.get("job_id", attach_to_job_id)),
                "source_recording_id": source_recording_id,
                "source_path": content.source_ref,
                "file_sha256": content.file_digest,
                "content_sha256": content.content_digest,
                "external_call": False,
            },
            {
                "step": "runtime_local_transcript_artifact_write",
                "artifact_path": relative_to_vault(root, raw_transcript_path),
                "canonical_promotion": False,
            },
        ],
        warnings=content.warnings,
    )
    transcript_artifact_path = store.write_artifact(
        attach_to_job_id,
        "transcripts/transcript_artifact.json",
        transcript_artifact.to_dict(),
        artifact_type="transcript_artifact",
    )

    updated_job = store.load_job(attach_to_job_id)
    updated_inputs = dict(updated_job.get("inputs", {}))
    updated_inputs.update(
        {
            "provided_transcript_path": content.source_ref,
            "transcript_file_sha256": content.file_digest,
            "transcript_content_sha256": content.content_digest,
            "transcript_word_count": _word_count(content.normalized_text),
            "transcript_attached_to_media_job": True,
            "transcription_backend": "not_used_provided_transcript",
            "copied_media": False,
            "ffmpeg_probe_performed": False,
        }
    )
    if context_prompt:
        updated_inputs["context_prompt"] = context_prompt
    if metadata:
        updated_inputs["provided_transcript_source_metadata"] = metadata

    updated_job["status"] = "transcript_ready"
    updated_job["target_platforms"] = _merged_target_platforms(updated_job, target_platforms)
    updated_job["inputs"] = updated_inputs
    updated_job["warnings"] = list(dict.fromkeys([*updated_job.get("warnings", []), *content.warnings]))
    job_path = store.save_job(updated_job)
    final_job = store.load_job(attach_to_job_id)

    job_ref = relative_to_vault(root, artifact_path(root, attach_to_job_id, "job.json", store.job_root))
    return ProvidedTranscriptAttachmentResult(
        job_id=str(final_job.get("job_id", attach_to_job_id)),
        source_recording_id=source_recording_id,
        transcript_artifact_id=transcript_artifact.artifact_id,
        job=final_job,
        files_read=[job_ref, source_recording_ref, content.source_ref],
        files_written=[
            relative_to_vault(root, raw_transcript_path),
            relative_to_vault(root, transcript_artifact_path),
            relative_to_vault(root, job_path),
        ],
        warnings=content.warnings,
    )


def _load_attachable_manual_media_job(
    vault_root: Path,
    store: CreatorJobStore,
    job_id: str,
) -> tuple[dict[str, Any], str]:
    try:
        job = store.load_job(job_id)
    except Exception as exc:
        raise TranscriptIntakeError(f"attach-to job not found: {job_id}") from exc

    if job.get("source_adapter") != "manual_file":
        raise TranscriptIntakeError("provided transcript can only attach to a manual-file media job")
    if not job.get("source_recording_id"):
        raise TranscriptIntakeError("attach-to job is missing source_recording_id")

    source_path = artifact_path(vault_root, job_id, "source_recording.json", store.job_root)
    if not source_path.exists():
        raise TranscriptIntakeError("attach-to job is missing source_recording.json")
    try:
        source_recording = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TranscriptIntakeError("attach-to source_recording.json is not valid JSON") from exc
    if not isinstance(source_recording, dict):
        raise TranscriptIntakeError("attach-to source_recording.json is not a JSON object")
    if source_recording.get("adapter") != "manual_file":
        raise TranscriptIntakeError("attach-to source recording is not a manual-file media source")
    if source_recording.get("recording_id") != job.get("source_recording_id"):
        raise TranscriptIntakeError("attach-to source recording id does not match the job")
    return job, relative_to_vault(vault_root, source_path)


def _ensure_attachable_status(job: dict[str, Any]) -> None:
    if job.get("status") not in {"intake_ready"}:
        raise TranscriptIntakeError("provided transcript can only attach to a manual-file job at intake_ready")


def _ensure_no_existing_transcript(
    vault_root: Path,
    store: CreatorJobStore,
    job_id: str,
    job: dict[str, Any],
) -> None:
    artifacts = job.get("artifacts", {}) if isinstance(job.get("artifacts"), dict) else {}
    if artifacts.get("transcript_artifact") or artifacts.get("transcript_raw"):
        raise TranscriptIntakeError("attach-to job already has transcript artifacts")
    transcript_paths = [
        artifact_path(vault_root, job_id, "transcripts/transcript.raw.md", store.job_root),
        artifact_path(vault_root, job_id, "transcripts/transcript_artifact.json", store.job_root),
    ]
    if any(path.exists() for path in transcript_paths):
        raise TranscriptIntakeError("attach-to job already has transcript files")


def _merged_target_platforms(job: dict[str, Any], target_platforms: list[str] | None) -> list[str]:
    merged: list[str] = []
    for platform in [*job.get("target_platforms", []), *(target_platforms or [])]:
        normalized = str(platform).strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged


def _read_declared_transcript(vault_root: Path, transcript_path: str | Path) -> _DeclaredTranscriptContent:
    transcript_file = _resolve_declared_transcript(vault_root, transcript_path)
    _validate_transcript_file(vault_root, transcript_file)

    raw_bytes = transcript_file.read_bytes()
    try:
        raw_text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise TranscriptIntakeError("provided transcript must be UTF-8 text") from exc

    normalized_text = _normalize_transcript_text(raw_text)
    if not normalized_text:
        raise TranscriptIntakeError("provided transcript is empty")

    stat = transcript_file.stat()
    return _DeclaredTranscriptContent(
        transcript_file=transcript_file,
        source_ref=relative_to_vault(vault_root, transcript_file),
        raw_bytes=raw_bytes,
        normalized_text=normalized_text,
        file_digest=hashlib.sha256(raw_bytes).hexdigest(),
        content_digest=hashlib.sha256(normalized_text.encode("utf-8")).hexdigest(),
        created_at=_iso_from_timestamp(stat.st_ctime),
        modified_at=_iso_from_timestamp(stat.st_mtime),
        warnings=_content_warnings(normalized_text),
    )


def _resolve_declared_transcript(vault_root: Path, transcript_path: str | Path) -> Path:
    declared = Path(transcript_path)
    candidate = declared.resolve() if declared.is_absolute() else (vault_root / declared).resolve()
    try:
        return ensure_within(vault_root, candidate)
    except ValueError as exc:
        raise TranscriptIntakeError(f"provided transcript is outside the vault: {transcript_path}") from exc


def _validate_transcript_file(vault_root: Path, transcript_file: Path) -> None:
    if not transcript_file.exists():
        raise TranscriptIntakeError(f"provided transcript does not exist: {transcript_file}")
    if not transcript_file.is_file():
        raise TranscriptIntakeError(f"provided transcript is not a file: {transcript_file}")
    if transcript_file.suffix.lower() not in SUPPORTED_TRANSCRIPT_SUFFIXES:
        raise TranscriptIntakeError(
            "provided transcript extension must be one of: "
            + ", ".join(sorted(SUPPORTED_TRANSCRIPT_SUFFIXES))
        )

    relative_parts = [part.lower() for part in Path(relative_to_vault(vault_root, transcript_file)).parts]
    if any(part in FORBIDDEN_TRANSCRIPT_PATH_PARTS for part in relative_parts):
        raise TranscriptIntakeError("provided transcript path crosses a forbidden secrets boundary")
    if any(part == ".env" or part.startswith(".env.") for part in relative_parts):
        raise TranscriptIntakeError("provided transcript path crosses a forbidden environment boundary")


def _normalize_transcript_text(text: str) -> str:
    body = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return f"{body}\n" if body else ""


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _content_warnings(text: str) -> list[str]:
    lowered = text.lower()
    if any(pattern in lowered for pattern in INSTRUCTION_LIKE_PATTERNS):
        return ["instruction_like_transcript_text_treated_as_untrusted_content"]
    return []


def _iso_from_timestamp(timestamp: float) -> str:
    return (
        datetime.fromtimestamp(timestamp, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
