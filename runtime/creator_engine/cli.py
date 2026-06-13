"""CLI payloads for runtime-local Creator Engine operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .approvals import (
    APPROVAL_SCOPES,
    APPROVAL_SCOPE_CHOICES,
    CreatorApprovalPreviewError,
    build_creator_approval_consumption_dry_run as build_creator_approval_consumption_dry_run_artifact,
    build_creator_approval_request as build_creator_approval_request_artifact,
    preview_creator_approval_packets,
)
from .context_pack import (
    ContextPackError,
    build_context_pack,
    preview_context_pack,
)
from .generator import (
    GenerationArtifactError,
    build_generation_artifact_stubs,
    preview_generation_artifact_stubs,
)
from .media_reference import (
    MediaReferenceError,
    import_manual_media_reference,
    preview_manual_media_reference,
)
from .transcript_intake import (
    TranscriptIntakeError,
    attach_provided_transcript_to_job,
    import_provided_transcript,
    preview_provided_transcript_attachment,
    preview_provided_transcript,
)


SUPPORTED_INGEST_SOURCES = {
    "manual-file": "manual_file",
    "manual_file": "manual_file",
    "provided-transcript": "provided_transcript",
    "provided_transcript": "provided_transcript",
}


def _root(vault_root: str | Path | None = None) -> Path:
    return Path(vault_root) if vault_root is not None else Path.cwd()


def _authority_flags(*, runtime_local_write_allowed: bool = True) -> dict[str, bool]:
    return {
        "runtime_local_write_allowed": runtime_local_write_allowed,
        "media_file_read_allowed": True,
        "media_reference_allowed": True,
        "transcript_file_read_allowed": True,
        "context_reference_read_allowed": True,
        "context_pack_write_allowed": runtime_local_write_allowed,
        "media_copy_allowed": False,
        "ffmpeg_probe_allowed": False,
        "transcription_backend_allowed": False,
        "recordly_or_obs_automation_allowed": False,
        "source_intelligence_query_allowed": False,
        "rag_index_write_allowed": False,
        "generation_allowed": False,
        "provider_call_allowed": False,
        "direct_publish_allowed": False,
        "canonical_writeback_allowed": False,
        "governed_memory_write_allowed": False,
    }


def _boundaries() -> list[str]:
    return [
        "provided transcript import or manual media reference only",
        "provided transcripts may attach to existing manual media jobs with --attach-to-job",
        "writes remain under runtime/creator_engine/jobs/",
        "manual source metadata is operator-supplied metadata only",
        "manual media is referenced only and never copied",
        "no media copy",
        "no FFmpeg or ffprobe media probing",
        "no transcription backend",
        "no Recordly or OBS automation",
        "no provider call",
        "no direct publish or upload",
        "no canonical memory promotion",
    ]


def _context_pack_boundaries() -> list[str]:
    return [
        "existing transcript_ready Creator Engine job only",
        "explicit declared context references only",
        "context excerpts are treated as untrusted operator-declared content",
        "writes remain under runtime/creator_engine/jobs/",
        "no Source Intelligence query or RAG index write",
        "no generation or provider call",
        "no direct publish or upload",
        "no canonical memory promotion",
        "no governed memory write",
    ]


def _generation_stub_boundaries() -> list[str]:
    return [
        "existing context_ready Creator Engine job only",
        "writes remain under runtime/creator_engine/jobs/",
        "deterministic template/stub artifacts only",
        "no Source Intelligence query or RAG index write",
        "no provider/model call",
        "no TTS or voiceover audio generation",
        "no Recordly/OpenScreen/OBS timeline execution",
        "no direct publish or upload",
        "no canonical memory promotion",
        "no governed memory write",
    ]


def _approval_preview_boundaries() -> list[str]:
    return [
        "existing draft_ready Creator Engine job only",
        "reads runtime-local draft artifacts only",
        "approval packet output is preview-only",
        "no approval artifact write",
        "no approval decision write",
        "no approval consumption",
        "no exact-once marker write",
        "no timeline execution",
        "no direct publish or upload",
        "no canonical memory promotion",
        "no governed memory write",
    ]


def _approval_request_boundaries() -> list[str]:
    return [
        "existing draft_ready Creator Engine job only",
        "approval request scope must be memory-card, publish, or timeline",
        "writes only pending request artifacts under 07_LOGS/Agent-Activity/_creator_engine_approvals/",
        "write requires exact --expected-approval-digest",
        "create-only request artifact write; no overwrite",
        "no approval grant",
        "no approval decision write",
        "no approval consumption",
        "no exact-once marker write",
        "no timeline execution",
        "no direct publish or upload",
        "no canonical memory promotion",
        "no governed memory write",
    ]


def _approval_consumption_dry_run_boundaries() -> list[str]:
    return [
        "pending Creator Engine approval request artifact only",
        "approval artifact path must stay inside the vault root",
        "recomputes the current approval preview digest before reporting readiness",
        "optional --expected-approval-digest must match the pending request digest",
        "requires future operator decision before any consumption",
        "checks future marker absence but writes no marker",
        "no approval grant",
        "no approval decision write",
        "no approval consumption",
        "no exact-once marker write",
        "no timeline execution",
        "no direct publish or upload",
        "no canonical memory promotion",
        "no governed memory write",
    ]


def _error_payload(
    *,
    status: str,
    vault_root: Path,
    source: str | None,
    errors: list[str],
    warnings: list[str] | None = None,
    dry_run: bool = False,
    manual_source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "command": "creator.ingest",
        "source": source,
        "vault_root": str(vault_root),
        "dry_run": dry_run,
        "writes_performed": False,
        "files_read": [],
        "files_written": [],
        "manual_source_metadata": dict(manual_source_metadata or {}),
        "errors": errors,
        "warnings": list(warnings or []),
        "authority_flags": _authority_flags(runtime_local_write_allowed=False if dry_run else True),
        "boundaries": _boundaries(),
    }


def _context_pack_error_payload(
    *,
    status: str,
    vault_root: Path,
    job_id: str | None,
    errors: list[str],
    warnings: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "command": "creator.context-pack",
        "job_id": job_id,
        "vault_root": str(vault_root),
        "dry_run": dry_run,
        "writes_performed": False,
        "files_read": [],
        "files_written": [],
        "errors": errors,
        "warnings": list(warnings or []),
        "authority_flags": _authority_flags(runtime_local_write_allowed=False if dry_run else True),
        "boundaries": _context_pack_boundaries(),
    }


def _generation_stub_error_payload(
    *,
    status: str,
    vault_root: Path,
    job_id: str | None,
    errors: list[str],
    warnings: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "command": "creator.generate-stubs",
        "job_id": job_id,
        "vault_root": str(vault_root),
        "dry_run": dry_run,
        "writes_performed": False,
        "files_read": [],
        "files_written": [],
        "errors": errors,
        "warnings": list(warnings or []),
        "authority_flags": _generation_stub_authority_flags(
            runtime_local_write_allowed=False if dry_run else True
        ),
        "boundaries": _generation_stub_boundaries(),
    }


def _approval_preview_error_payload(
    *,
    status: str,
    vault_root: Path,
    job_id: str | None,
    approval_scope: str,
    errors: list[str],
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "command": "creator.approval-preview",
        "job_id": job_id,
        "approval_scope": approval_scope,
        "vault_root": str(vault_root),
        "writes_performed": False,
        "files_read": [],
        "files_written": [],
        "errors": errors,
        "warnings": list(warnings or []),
        "authority_flags": _approval_preview_authority_flags(),
        "boundaries": _approval_preview_boundaries(),
    }


def _approval_request_error_payload(
    *,
    status: str,
    vault_root: Path,
    job_id: str | None,
    approval_scope: str,
    errors: list[str],
    warnings: list[str] | None = None,
    write_approval_request: bool = False,
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "command": "creator.write-approval-request",
        "job_id": job_id,
        "approval_scope": approval_scope,
        "vault_root": str(vault_root),
        "write_approval_request_requested": write_approval_request,
        "approval_request_written": False,
        "approval_artifact_written": False,
        "writes_performed": False,
        "files_read": [],
        "files_written": [],
        "errors": errors,
        "warnings": list(warnings or []),
        "authority_flags": _approval_request_authority_flags(artifact_written=False),
        "boundaries": _approval_request_boundaries(),
    }


def _approval_consumption_dry_run_error_payload(
    *,
    status: str,
    vault_root: Path,
    approval_artifact_path: str | Path | None,
    errors: list[str],
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status,
        "command": "creator.approval-consumption-dry-run",
        "approval_artifact_path": str(approval_artifact_path or ""),
        "vault_root": str(vault_root),
        "writes_performed": False,
        "files_read": [],
        "files_written": [],
        "errors": errors,
        "warnings": list(warnings or []),
        "authority_flags": _approval_consumption_dry_run_authority_flags(),
        "boundaries": _approval_consumption_dry_run_boundaries(),
    }


def _generation_stub_authority_flags(*, runtime_local_write_allowed: bool = True) -> dict[str, bool]:
    return {
        "runtime_local_write_allowed": runtime_local_write_allowed,
        "generation_artifact_stub_write_allowed": runtime_local_write_allowed,
        "deterministic_template_only": True,
        "ai_generation_performed": False,
        "source_intelligence_query_allowed": False,
        "rag_index_write_allowed": False,
        "provider_call_allowed": False,
        "tts_generation_allowed": False,
        "timeline_edit_execution_allowed": False,
        "direct_publish_allowed": False,
        "upload_allowed": False,
        "canonical_writeback_allowed": False,
        "governed_memory_write_allowed": False,
    }


def _approval_preview_authority_flags() -> dict[str, bool]:
    return {
        "runtime_local_read_allowed": True,
        "runtime_local_write_allowed": False,
        "approval_preview_allowed": True,
        "approval_artifact_write_allowed": False,
        "approval_decision_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_marker_write_allowed": False,
        "timeline_edit_execution_allowed": False,
        "direct_publish_allowed": False,
        "upload_allowed": False,
        "external_delivery_allowed": False,
        "canonical_writeback_allowed": False,
        "governed_memory_write_allowed": False,
        "provider_call_allowed": False,
    }


def _approval_request_authority_flags(*, artifact_written: bool) -> dict[str, bool]:
    return {
        "runtime_local_read_allowed": True,
        "runtime_local_write_allowed": artifact_written,
        "approval_preview_allowed": True,
        "approval_artifact_write_allowed": artifact_written,
        "approval_request_written": artifact_written,
        "approval_decision_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_marker_write_allowed": False,
        "timeline_edit_execution_allowed": False,
        "direct_publish_allowed": False,
        "upload_allowed": False,
        "external_delivery_allowed": False,
        "canonical_writeback_allowed": False,
        "governed_memory_write_allowed": False,
        "provider_call_allowed": False,
    }


def _approval_consumption_dry_run_authority_flags() -> dict[str, bool]:
    return {
        "runtime_local_read_allowed": True,
        "runtime_local_write_allowed": False,
        "approval_preview_allowed": True,
        "approval_artifact_write_allowed": False,
        "approval_decision_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_marker_write_allowed": False,
        "timeline_edit_execution_allowed": False,
        "direct_publish_allowed": False,
        "upload_allowed": False,
        "external_delivery_allowed": False,
        "canonical_writeback_allowed": False,
        "governed_memory_write_allowed": False,
        "provider_call_allowed": False,
    }


def build_creator_ingest(
    *,
    vault_root: str | Path | None = None,
    source: str = "provided-transcript",
    transcript_path: str | Path | None = None,
    media_path: str | Path | None = None,
    job_id: str | None = None,
    attach_to_job_id: str | None = None,
    source_recording_id: str | None = None,
    target_platforms: list[str] | None = None,
    context_prompt: str | None = None,
    manual_source_metadata: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Build and execute the narrow Creator Engine provided-transcript ingest."""

    root = _root(vault_root)
    normalized_source = SUPPORTED_INGEST_SOURCES.get(source)
    if normalized_source not in {"provided_transcript", "manual_file"}:
        return _error_payload(
            status="unsupported_source",
            vault_root=root,
            source=source,
            errors=["creator ingest currently supports source=provided-transcript or manual-file only"],
            dry_run=dry_run,
            manual_source_metadata=manual_source_metadata,
        )
    if normalized_source == "manual_file":
        if not media_path:
            return _error_payload(
                status="missing_media",
                vault_root=root,
                source=source,
                errors=["--media is required for manual-file ingest"],
                dry_run=dry_run,
                manual_source_metadata=manual_source_metadata,
            )
        if dry_run:
            try:
                preview = preview_manual_media_reference(
                    root,
                    media_path,
                    source_recording_id=source_recording_id,
                    target_platforms=list(target_platforms or []),
                    context_prompt=context_prompt,
                    manual_source_metadata=manual_source_metadata,
                )
            except MediaReferenceError as exc:
                return _error_payload(
                    status="blocked",
                    vault_root=root,
                    source=source,
                    errors=[str(exc)],
                    dry_run=True,
                    manual_source_metadata=manual_source_metadata,
                )
            return {
                "ok": True,
                "status": "dry_run_ready",
                "command": "creator.ingest",
                "source": normalized_source,
                "vault_root": str(root.resolve()),
                "dry_run": True,
                "writes_performed": False,
                "files_read": list(preview.files_read),
                "files_written": [],
                "manual_source_metadata": dict(preview.manual_source_metadata),
                "warnings": list(preview.warnings),
                "blockers": list(preview.blockers),
                "preview": preview.to_dict(),
                "authority_flags": _authority_flags(runtime_local_write_allowed=False),
                "boundaries": _boundaries(),
            }
        try:
            result = import_manual_media_reference(
                root,
                media_path,
                job_id=job_id,
                source_recording_id=source_recording_id,
                target_platforms=list(target_platforms or []),
                context_prompt=context_prompt,
                manual_source_metadata=manual_source_metadata,
            )
        except MediaReferenceError as exc:
            return _error_payload(
                status="blocked",
                vault_root=root,
                source=source,
                errors=[str(exc)],
                manual_source_metadata=manual_source_metadata,
            )
        return {
            "ok": True,
            "status": "intake_ready",
            "command": "creator.ingest",
            "source": normalized_source,
            "vault_root": str(root.resolve()),
            "dry_run": False,
            "writes_performed": True,
            "job_id": result.job_id,
            "source_recording_id": result.source_recording_id,
            "files_read": list(result.files_read),
            "files_written": list(result.files_written),
            "manual_source_metadata": dict(result.job.get("inputs", {}).get("manual_source_metadata", {})),
            "warnings": list(result.warnings),
            "blockers": list(result.blockers),
            "job": result.job,
            "authority_flags": _authority_flags(),
            "boundaries": _boundaries(),
        }

    if not transcript_path:
        return _error_payload(
            status="missing_transcript",
            vault_root=root,
            source=source,
            errors=["--transcript is required for provided-transcript ingest"],
            dry_run=dry_run,
            manual_source_metadata=manual_source_metadata,
        )

    if attach_to_job_id:
        if job_id:
            return _error_payload(
                status="blocked",
                vault_root=root,
                source=source,
                errors=["--attach-to-job cannot be combined with --job-id"],
                dry_run=dry_run,
                manual_source_metadata=manual_source_metadata,
            )
        if source_recording_id:
            return _error_payload(
                status="blocked",
                vault_root=root,
                source=source,
                errors=["--attach-to-job uses the existing job source recording; omit --source-recording-id"],
                dry_run=dry_run,
                manual_source_metadata=manual_source_metadata,
            )
        if dry_run:
            try:
                preview = preview_provided_transcript_attachment(
                    root,
                    transcript_path,
                    attach_to_job_id=attach_to_job_id,
                    target_platforms=list(target_platforms or []),
                    context_prompt=context_prompt,
                    manual_source_metadata=manual_source_metadata,
                )
            except TranscriptIntakeError as exc:
                return _error_payload(
                    status="blocked",
                    vault_root=root,
                    source=source,
                    errors=[str(exc)],
                    dry_run=True,
                    manual_source_metadata=manual_source_metadata,
                )
            return {
                "ok": True,
                "status": "dry_run_ready",
                "command": "creator.ingest",
                "source": normalized_source,
                "vault_root": str(root.resolve()),
                "dry_run": True,
                "writes_performed": False,
                "attach_to_job_id": attach_to_job_id,
                "source_recording_id": preview.source_recording_id,
                "files_read": list(preview.files_read),
                "files_written": [],
                "files_would_write": list(preview.files_would_write),
                "manual_source_metadata": dict(preview.manual_source_metadata),
                "warnings": list(preview.warnings),
                "blockers": list(preview.blockers),
                "preview": preview.to_dict(),
                "authority_flags": _authority_flags(runtime_local_write_allowed=False),
                "boundaries": _boundaries(),
            }

        try:
            result = attach_provided_transcript_to_job(
                root,
                transcript_path,
                attach_to_job_id=attach_to_job_id,
                target_platforms=list(target_platforms or []),
                context_prompt=context_prompt,
                manual_source_metadata=manual_source_metadata,
            )
        except TranscriptIntakeError as exc:
            return _error_payload(
                status="blocked",
                vault_root=root,
                source=source,
                errors=[str(exc)],
                manual_source_metadata=manual_source_metadata,
            )
        return {
            "ok": True,
            "status": "transcript_ready",
            "command": "creator.ingest",
            "source": normalized_source,
            "vault_root": str(root.resolve()),
            "dry_run": False,
            "writes_performed": True,
            "attach_to_job_id": attach_to_job_id,
            "job_id": result.job_id,
            "source_recording_id": result.source_recording_id,
            "transcript_artifact_id": result.transcript_artifact_id,
            "files_read": list(result.files_read),
            "files_written": list(result.files_written),
            "manual_source_metadata": dict(
                result.job.get("inputs", {}).get("provided_transcript_source_metadata", {})
            ),
            "warnings": list(result.warnings),
            "blockers": list(result.blockers),
            "job": result.job,
            "authority_flags": _authority_flags(),
            "boundaries": _boundaries(),
        }

    if dry_run:
        try:
            preview = preview_provided_transcript(
                root,
                transcript_path,
                source_recording_id=source_recording_id,
                target_platforms=list(target_platforms or []),
                context_prompt=context_prompt,
                manual_source_metadata=manual_source_metadata,
            )
        except TranscriptIntakeError as exc:
            return _error_payload(
                status="blocked",
                vault_root=root,
                source=source,
                errors=[str(exc)],
                dry_run=True,
                manual_source_metadata=manual_source_metadata,
            )
        return {
            "ok": True,
            "status": "dry_run_ready",
            "command": "creator.ingest",
            "source": normalized_source,
            "vault_root": str(root.resolve()),
            "dry_run": True,
            "writes_performed": False,
            "files_read": list(preview.files_read),
            "files_written": [],
            "manual_source_metadata": dict(preview.manual_source_metadata),
            "warnings": list(preview.warnings),
            "blockers": list(preview.blockers),
            "preview": preview.to_dict(),
            "authority_flags": _authority_flags(runtime_local_write_allowed=False),
            "boundaries": _boundaries(),
        }

    try:
        result = import_provided_transcript(
            root,
            transcript_path,
            job_id=job_id,
            source_recording_id=source_recording_id,
            target_platforms=list(target_platforms or []),
            context_prompt=context_prompt,
            manual_source_metadata=manual_source_metadata,
        )
    except TranscriptIntakeError as exc:
        return _error_payload(
            status="blocked",
            vault_root=root,
            source=source,
            errors=[str(exc)],
            manual_source_metadata=manual_source_metadata,
        )

    return {
        "ok": True,
        "status": "transcript_ready",
        "command": "creator.ingest",
        "source": normalized_source,
        "vault_root": str(root.resolve()),
        "dry_run": False,
        "writes_performed": True,
        "job_id": result.job_id,
        "source_recording_id": result.source_recording_id,
        "transcript_artifact_id": result.transcript_artifact_id,
        "files_read": list(result.files_read),
        "files_written": list(result.files_written),
        "manual_source_metadata": dict(result.job.get("inputs", {}).get("manual_source_metadata", {})),
        "warnings": list(result.warnings),
        "blockers": list(result.blockers),
        "job": result.job,
        "authority_flags": _authority_flags(),
        "boundaries": _boundaries(),
    }


def build_creator_context_pack(
    *,
    vault_root: str | Path | None = None,
    job_id: str | None = None,
    context_refs: list[str | Path] | None = None,
    context_prompt: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Build or preview a runtime-local Creator Engine context pack."""

    root = _root(vault_root)
    if not job_id:
        return _context_pack_error_payload(
            status="missing_job_id",
            vault_root=root,
            job_id=job_id,
            errors=["--job-id is required for creator context-pack"],
            dry_run=dry_run,
        )

    if dry_run:
        try:
            preview = preview_context_pack(
                root,
                job_id=job_id,
                context_refs=list(context_refs or []),
                context_prompt=context_prompt,
            )
        except ContextPackError as exc:
            return _context_pack_error_payload(
                status="blocked",
                vault_root=root,
                job_id=job_id,
                errors=[str(exc)],
                dry_run=True,
            )
        return {
            "ok": True,
            "status": "dry_run_ready",
            "command": "creator.context-pack",
            "vault_root": str(root.resolve()),
            "job_id": preview.job_id,
            "source_recording_id": preview.source_recording_id,
            "context_pack_artifact_id": preview.context_pack_artifact_id,
            "dry_run": True,
            "writes_performed": False,
            "files_read": list(preview.files_read),
            "files_written": [],
            "files_would_write": list(preview.files_would_write),
            "warnings": list(preview.warnings),
            "blockers": list(preview.blockers),
            "preview": preview.to_dict(),
            "authority_flags": _authority_flags(runtime_local_write_allowed=False),
            "boundaries": _context_pack_boundaries(),
        }

    try:
        result = build_context_pack(
            root,
            job_id=job_id,
            context_refs=list(context_refs or []),
            context_prompt=context_prompt,
        )
    except ContextPackError as exc:
        return _context_pack_error_payload(
            status="blocked",
            vault_root=root,
            job_id=job_id,
            errors=[str(exc)],
        )

    return {
        "ok": True,
        "status": "context_ready",
        "command": "creator.context-pack",
        "vault_root": str(root.resolve()),
        "job_id": result.job_id,
        "source_recording_id": result.source_recording_id,
        "context_pack_artifact_id": result.context_pack_artifact_id,
        "dry_run": False,
        "writes_performed": True,
        "files_read": list(result.files_read),
        "files_written": list(result.files_written),
        "warnings": list(result.warnings),
        "blockers": list(result.blockers),
        "job": result.job,
        "context_pack": result.context_pack,
        "authority_flags": _authority_flags(),
        "boundaries": _context_pack_boundaries(),
    }


def build_creator_generation_stubs(
    *,
    vault_root: str | Path | None = None,
    job_id: str | None = None,
    target_platforms: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Build or preview deterministic runtime-local Creator Engine draft stubs."""

    root = _root(vault_root)
    if not job_id:
        return _generation_stub_error_payload(
            status="missing_job_id",
            vault_root=root,
            job_id=job_id,
            errors=["--job-id is required for creator generate-stubs"],
            dry_run=dry_run,
        )

    if dry_run:
        try:
            preview = preview_generation_artifact_stubs(
                root,
                job_id=job_id,
                target_platforms=list(target_platforms or []),
            )
        except GenerationArtifactError as exc:
            return _generation_stub_error_payload(
                status="blocked",
                vault_root=root,
                job_id=job_id,
                errors=[str(exc)],
                dry_run=True,
            )
        return {
            "ok": True,
            "status": "dry_run_ready",
            "command": "creator.generate-stubs",
            "vault_root": str(root.resolve()),
            "job_id": preview.job_id,
            "source_recording_id": preview.source_recording_id,
            "generation_artifact_id": preview.generation_artifact_id,
            "target_platforms": list(preview.target_platforms),
            "dry_run": True,
            "writes_performed": False,
            "files_read": list(preview.files_read),
            "files_written": [],
            "files_would_write": list(preview.files_would_write),
            "artifact_paths": dict(preview.artifact_paths),
            "warnings": list(preview.warnings),
            "blockers": list(preview.blockers),
            "preview": preview.to_dict(),
            "authority_flags": _generation_stub_authority_flags(runtime_local_write_allowed=False),
            "boundaries": _generation_stub_boundaries(),
        }

    try:
        result = build_generation_artifact_stubs(
            root,
            job_id=job_id,
            target_platforms=list(target_platforms or []),
        )
    except GenerationArtifactError as exc:
        return _generation_stub_error_payload(
            status="blocked",
            vault_root=root,
            job_id=job_id,
            errors=[str(exc)],
        )

    return {
        "ok": True,
        "status": "draft_ready",
        "command": "creator.generate-stubs",
        "vault_root": str(root.resolve()),
        "job_id": result.job_id,
        "source_recording_id": result.source_recording_id,
        "generation_artifact_id": result.generation_artifact_id,
        "target_platforms": list(result.manifest.get("target_platforms", [])),
        "dry_run": False,
        "writes_performed": True,
        "files_read": list(result.files_read),
        "files_written": list(result.files_written),
        "warnings": list(result.warnings),
        "blockers": list(result.blockers),
        "job": result.job,
        "manifest": result.manifest,
        "authority_flags": _generation_stub_authority_flags(),
        "boundaries": _generation_stub_boundaries(),
    }


def build_creator_approval_preview(
    *,
    vault_root: str | Path | None = None,
    job_id: str | None = None,
    approval_scope: str = "all",
) -> dict[str, Any]:
    """Preview approval packets for draft-ready Creator Engine artifacts."""

    root = _root(vault_root)
    if approval_scope not in APPROVAL_SCOPE_CHOICES:
        return _approval_preview_error_payload(
            status="unsupported_approval_scope",
            vault_root=root,
            job_id=job_id,
            approval_scope=approval_scope,
            errors=[f"--approval-scope must be one of: {', '.join(APPROVAL_SCOPE_CHOICES)}"],
        )
    if not job_id:
        return _approval_preview_error_payload(
            status="missing_job_id",
            vault_root=root,
            job_id=job_id,
            approval_scope=approval_scope,
            errors=["--job-id is required for creator approval-preview"],
        )

    try:
        result = preview_creator_approval_packets(
            root,
            job_id=job_id,
            approval_scope=approval_scope,
        )
    except CreatorApprovalPreviewError as exc:
        return _approval_preview_error_payload(
            status="blocked",
            vault_root=root,
            job_id=job_id,
            approval_scope=approval_scope,
            errors=[str(exc)],
        )

    return {
        "ok": True,
        "status": "approval_preview_ready",
        "command": "creator.approval-preview",
        "vault_root": str(root.resolve()),
        "job_id": result.job_id,
        "source_recording_id": result.source_recording_id,
        "generation_artifact_id": result.generation_artifact_id,
        "generation_input_digest": result.generation_input_digest,
        "approval_scope": result.approval_scope,
        "approval_packet_count": len(result.approval_packet_previews),
        "approval_packet_previews": list(result.approval_packet_previews),
        "writes_performed": False,
        "files_read": list(result.files_read),
        "files_written": [],
        "warnings": list(result.warnings),
        "blockers": list(result.blockers),
        "preview": result.to_dict(),
        "authority_flags": _approval_preview_authority_flags(),
        "boundaries": _approval_preview_boundaries(),
    }


def build_creator_approval_request(
    *,
    vault_root: str | Path | None = None,
    job_id: str | None = None,
    approval_scope: str = "memory-card",
    expected_approval_digest: str | None = None,
    requested_by: str = "operator",
    write_approval_request: bool = False,
) -> dict[str, Any]:
    """Build or write a guarded pending Creator Engine approval request."""

    root = _root(vault_root)
    if approval_scope not in APPROVAL_SCOPES:
        return _approval_request_error_payload(
            status="unsupported_approval_scope",
            vault_root=root,
            job_id=job_id,
            approval_scope=approval_scope,
            errors=[f"--approval-scope must be one of: {', '.join(APPROVAL_SCOPES)}"],
            write_approval_request=write_approval_request,
        )
    if not job_id:
        return _approval_request_error_payload(
            status="missing_job_id",
            vault_root=root,
            job_id=job_id,
            approval_scope=approval_scope,
            errors=["--job-id is required for creator write-approval-request"],
            write_approval_request=write_approval_request,
        )

    try:
        result = build_creator_approval_request_artifact(
            root,
            job_id=job_id,
            approval_scope=approval_scope,
            expected_approval_digest=expected_approval_digest,
            requested_by=requested_by,
            write_approval_request=write_approval_request,
        )
    except CreatorApprovalPreviewError as exc:
        return _approval_request_error_payload(
            status="blocked",
            vault_root=root,
            job_id=job_id,
            approval_scope=approval_scope,
            errors=[str(exc)],
            write_approval_request=write_approval_request,
        )

    return {
        **result,
        "boundaries": _approval_request_boundaries(),
    }


def build_creator_approval_consumption_dry_run(
    *,
    vault_root: str | Path | None = None,
    approval_artifact_path: str | Path | None = None,
    expected_approval_digest: str | None = None,
) -> dict[str, Any]:
    """Validate a pending Creator Engine approval request without consuming it."""

    root = _root(vault_root)
    if not approval_artifact_path:
        return _approval_consumption_dry_run_error_payload(
            status="missing_approval_artifact_path",
            vault_root=root,
            approval_artifact_path=approval_artifact_path,
            errors=["--approval-artifact-path is required for creator approval-consumption-dry-run"],
        )

    result = build_creator_approval_consumption_dry_run_artifact(
        approval_artifact_path,
        expected_approval_digest=expected_approval_digest,
        vault_root=root,
    )
    return {
        **result,
        "boundaries": _approval_consumption_dry_run_boundaries(),
    }


def format_creator_ingest(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS Creator Engine Ingest",
        f"  status: {payload.get('status')}",
        f"  source: {payload.get('source')}",
    ]
    if payload.get("dry_run"):
        lines.append("  dry_run: true")
    if not payload.get("ok"):
        for error in payload.get("errors") or []:
            lines.append(f"  error: {error}")
        lines.append("  boundary: provided transcript import only; no transcription, publish, or canonical writeback")
        return "\n".join(lines)
    if payload.get("dry_run"):
        preview = payload.get("preview") or {}
        if payload.get("source") == "manual_file":
            lines.extend(
                [
                    f"  media_path: {preview.get('media_path')}",
                    f"  media_kind: {preview.get('media_kind')}",
                    f"  probe_status: {preview.get('probe_status')}",
                    "  files_written: none",
                    "  boundary: dry-run media reference only; no copy, probe, transcription, publish, or canonical writeback",
                ]
            )
            return "\n".join(lines)
        lines.extend(
            [
                f"  transcript_path: {preview.get('transcript_path')}",
                f"  word_count: {preview.get('word_count')}",
                "  files_written: none",
                "  boundary: dry-run validation only; no runtime job, transcription, publish, or canonical writeback",
            ]
        )
        if payload.get("attach_to_job_id"):
            lines.insert(-2, f"  attach_to_job_id: {payload.get('attach_to_job_id')}")
            lines[-1] = (
                "  boundary: dry-run attachment validation only; no runtime write, "
                "transcription, publish, or canonical writeback"
            )
        return "\n".join(lines)

    lines.extend(
        [
            f"  job_id: {payload.get('job_id')}",
            "  files_written:",
        ]
    )
    if payload.get("transcript_artifact_id"):
        lines.insert(-1, f"  transcript_artifact_id: {payload.get('transcript_artifact_id')}")
    for path in payload.get("files_written") or []:
        lines.append(f"    - {path}")
    warnings = payload.get("warnings") or []
    if warnings:
        lines.append("  warnings:")
        for warning in warnings:
            lines.append(f"    - {warning}")
    lines.append("  boundary: runtime-local artifacts only; no transcription, publish, or canonical writeback")
    return "\n".join(lines)


def format_creator_context_pack(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS Creator Engine Context Pack",
        f"  status: {payload.get('status')}",
    ]
    if payload.get("job_id"):
        lines.append(f"  job_id: {payload.get('job_id')}")
    if payload.get("dry_run"):
        lines.append("  dry_run: true")
    if not payload.get("ok"):
        for error in payload.get("errors") or []:
            lines.append(f"  error: {error}")
        lines.append("  boundary: no generation, provider call, publish, or canonical writeback")
        return "\n".join(lines)
    if payload.get("dry_run"):
        preview = payload.get("preview") or {}
        lines.extend(
            [
                f"  context_pack_artifact_id: {preview.get('context_pack_artifact_id')}",
                f"  context_items: {len(preview.get('context_items') or [])}",
                "  files_written: none",
                "  boundary: dry-run context-pack validation only; no runtime write, generation, publish, or canonical writeback",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            f"  context_pack_artifact_id: {payload.get('context_pack_artifact_id')}",
            "  files_written:",
        ]
    )
    for path in payload.get("files_written") or []:
        lines.append(f"    - {path}")
    warnings = payload.get("warnings") or []
    if warnings:
        lines.append("  warnings:")
        for warning in warnings:
            lines.append(f"    - {warning}")
    lines.append("  boundary: runtime-local context pack only; no generation, publish, or canonical writeback")
    return "\n".join(lines)


def format_creator_generation_stubs(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS Creator Engine Generation Stubs",
        f"  status: {payload.get('status')}",
    ]
    if payload.get("job_id"):
        lines.append(f"  job_id: {payload.get('job_id')}")
    if payload.get("dry_run"):
        lines.append("  dry_run: true")
    if not payload.get("ok"):
        for error in payload.get("errors") or []:
            lines.append(f"  error: {error}")
        lines.append("  boundary: no provider call, publish, upload, timeline execution, or canonical writeback")
        return "\n".join(lines)
    if payload.get("dry_run"):
        lines.extend(
            [
                f"  generation_artifact_id: {payload.get('generation_artifact_id')}",
                f"  target_platforms: {', '.join(payload.get('target_platforms') or [])}",
                "  files_written: none",
                "  boundary: dry-run generation-stub validation only; no runtime write, provider call, publish, or canonical writeback",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            f"  generation_artifact_id: {payload.get('generation_artifact_id')}",
            f"  target_platforms: {', '.join(payload.get('target_platforms') or [])}",
            "  files_written:",
        ]
    )
    for path in payload.get("files_written") or []:
        lines.append(f"    - {path}")
    warnings = payload.get("warnings") or []
    if warnings:
        lines.append("  warnings:")
        for warning in warnings:
            lines.append(f"    - {warning}")
    lines.append("  boundary: runtime-local draft stubs only; no provider call, publish, or canonical writeback")
    return "\n".join(lines)


def format_creator_approval_preview(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS Creator Engine Approval Preview",
        f"  status: {payload.get('status')}",
    ]
    if payload.get("job_id"):
        lines.append(f"  job_id: {payload.get('job_id')}")
    lines.append(f"  approval_scope: {payload.get('approval_scope')}")
    if not payload.get("ok"):
        for error in payload.get("errors") or []:
            lines.append(f"  error: {error}")
        lines.append("  boundary: no approval write, consumption, execution, publish, or canonical writeback")
        return "\n".join(lines)

    lines.append(f"  approval_packet_count: {payload.get('approval_packet_count')}")
    for packet in payload.get("approval_packet_previews") or []:
        lines.append(
            f"  - {packet.get('approval_scope')}: {packet.get('approval_packet_id')} "
            f"({packet.get('target_action')})"
        )
    lines.append("  files_written: none")
    lines.append("  boundary: preview-only approval packets; no approval write, consumption, execution, publish, or canonical writeback")
    return "\n".join(lines)


def format_creator_approval_request(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS Creator Engine Approval Request",
        f"  status: {payload.get('status')}",
    ]
    if payload.get("job_id"):
        lines.append(f"  job_id: {payload.get('job_id')}")
    lines.extend(
        [
            f"  approval_scope: {payload.get('approval_scope')}",
            f"  approval_packet_id: {payload.get('approval_packet_id') or '(none)'}",
            f"  approval_digest: {payload.get('approval_digest') or '(none)'}",
            f"  expected_digest_matched: {payload.get('approval_digest_matched')}",
            f"  request_written: {payload.get('approval_request_written')}",
            f"  artifact_path: {payload.get('approval_artifact_path') or '(none)'}",
        ]
    )
    if not payload.get("ok"):
        for error in payload.get("errors") or []:
            lines.append(f"  error: {error}")
    blockers = payload.get("blockers") or []
    if blockers:
        lines.append(f"  blockers: {', '.join(blockers)}")
    lines.append("  boundary: approval request only; no approval grant, consumption, execution, publish, or canonical writeback")
    return "\n".join(lines)


def format_creator_approval_consumption_dry_run(payload: dict[str, Any]) -> str:
    lines = [
        "ChaseOS Creator Engine Approval Consumption Dry Run",
        f"  status: {payload.get('status')}",
        f"  approval_artifact_path: {payload.get('approval_artifact_path') or '(none)'}",
        f"  approval_packet_id: {payload.get('approval_packet_id') or '(none)'}",
        f"  approval_scope: {payload.get('approval_scope') or '(none)'}",
        f"  approval_digest: {payload.get('approval_digest') or '(none)'}",
        f"  expected_digest_matched: {payload.get('approval_digest_matched')}",
        f"  current_digest: {payload.get('current_approval_digest') or '(none)'}",
        f"  future_marker_path: {payload.get('future_consumption_marker_path') or '(none)'}",
        f"  approval_consumption_ready: {payload.get('approval_consumption_ready')}",
    ]
    if not payload.get("ok"):
        for error in payload.get("errors") or []:
            lines.append(f"  error: {error}")
    blockers = payload.get("blockers") or []
    if blockers:
        lines.append(f"  blockers: {', '.join(blockers)}")
    lines.append(
        "  boundary: consumption dry-run only; no approval grant, decision write, consumption, marker write, execution, publish, or canonical writeback"
    )
    return "\n".join(lines)


def _print(args: argparse.Namespace, payload: dict[str, Any], text: str) -> int:
    if getattr(args, "output_json", False):
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(text)
    return 0 if payload.get("ok") else 1


def cmd_creator_ingest(args: argparse.Namespace) -> int:
    source_notes = getattr(args, "source_notes", None) or []
    manual_source_metadata = {
        "source_title": getattr(args, "source_title", None),
        "source_origin": getattr(args, "source_origin", None),
        "source_kind": getattr(args, "source_kind", None),
        "recorded_at": getattr(args, "recorded_at", None),
        "source_notes": source_notes,
    }
    payload = build_creator_ingest(
        vault_root=getattr(args, "vault_root", None),
        source=getattr(args, "source", "provided-transcript"),
        transcript_path=getattr(args, "transcript_path", None),
        media_path=getattr(args, "media_path", None),
        job_id=getattr(args, "job_id", None),
        attach_to_job_id=getattr(args, "attach_to_job_id", None),
        source_recording_id=getattr(args, "source_recording_id", None),
        target_platforms=getattr(args, "target_platforms", None),
        context_prompt=getattr(args, "context_prompt", None),
        manual_source_metadata=manual_source_metadata,
        dry_run=getattr(args, "dry_run", False),
    )
    return _print(args, payload, format_creator_ingest(payload))


def cmd_creator_context_pack(args: argparse.Namespace) -> int:
    payload = build_creator_context_pack(
        vault_root=getattr(args, "vault_root", None),
        job_id=getattr(args, "job_id", None),
        context_refs=getattr(args, "context_refs", None) or [],
        context_prompt=getattr(args, "context_prompt", None),
        dry_run=getattr(args, "dry_run", False),
    )
    return _print(args, payload, format_creator_context_pack(payload))


def cmd_creator_generate_stubs(args: argparse.Namespace) -> int:
    payload = build_creator_generation_stubs(
        vault_root=getattr(args, "vault_root", None),
        job_id=getattr(args, "job_id", None),
        target_platforms=getattr(args, "target_platforms", None) or [],
        dry_run=getattr(args, "dry_run", False),
    )
    return _print(args, payload, format_creator_generation_stubs(payload))


def cmd_creator_approval_preview(args: argparse.Namespace) -> int:
    payload = build_creator_approval_preview(
        vault_root=getattr(args, "vault_root", None),
        job_id=getattr(args, "job_id", None),
        approval_scope=getattr(args, "approval_scope", "all"),
    )
    return _print(args, payload, format_creator_approval_preview(payload))


def cmd_creator_write_approval_request(args: argparse.Namespace) -> int:
    payload = build_creator_approval_request(
        vault_root=getattr(args, "vault_root", None),
        job_id=getattr(args, "job_id", None),
        approval_scope=getattr(args, "approval_scope", "memory-card"),
        expected_approval_digest=getattr(args, "expected_approval_digest", None),
        requested_by=getattr(args, "requested_by", "operator"),
        write_approval_request=getattr(args, "write_approval_request", False),
    )
    return _print(args, payload, format_creator_approval_request(payload))


def cmd_creator_approval_consumption_dry_run(args: argparse.Namespace) -> int:
    payload = build_creator_approval_consumption_dry_run(
        vault_root=getattr(args, "vault_root", None),
        approval_artifact_path=getattr(args, "approval_artifact_path", None),
        expected_approval_digest=getattr(args, "expected_approval_digest", None),
    )
    return _print(args, payload, format_creator_approval_consumption_dry_run(payload))
