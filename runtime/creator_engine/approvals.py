"""Read-only approval packet previews for Creator Engine draft artifacts.

This pass prepares deterministic review packets for draft-ready jobs without
writing approval requests, consuming approval decisions, executing edits,
publishing, or promoting content into governed memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from .job_store import CreatorJobStore
from .models import SCHEMA_VERSION, utc_now
from .path_policy import artifact_path, ensure_within, relative_to_vault, resolve_vault_root


APPROVAL_PREVIEW_STATUS = "approval_preview_ready"
APPROVAL_PACKET_TYPE = "creator_approval_packet_preview"
APPROVAL_REQUEST_PACKET_TYPE = "creator_approval_request"
APPROVAL_REQUEST_STATUS = "pending_operator_approval"
APPROVAL_CONSUMPTION_DRY_RUN_PACKET_TYPE = "creator_approval_consumption_dry_run"
APPROVAL_SCOPES = ("memory-card", "publish", "timeline")
APPROVAL_SCOPE_CHOICES = (*APPROVAL_SCOPES, "all")
FUTURE_APPROVAL_ROOT = "07_LOGS/Agent-Activity/_creator_engine_approvals"
FUTURE_CONSUMPTION_MARKER_ROOT = f"{FUTURE_APPROVAL_ROOT}/_consumption_markers"

_SCOPE_SPECS: dict[str, dict[str, Any]] = {
    "memory-card": {
        "target_action": "content_memory_card_canonical_promotion",
        "target_artifacts": [
            "memory/content_memory_card.json",
            "memory/content_memory_card.md",
        ],
        "future_write_targets": [
            "operator-approved content memory destination",
            "governed memory promotion marker",
        ],
        "blocked_until_approved": [
            "canonical_memory_promotion",
            "governed_memory_write",
            "content_memory_card_canonical_promotion",
        ],
        "review_checklist": [
            "Confirm summary and claims are supported by source refs.",
            "Choose the exact canonical memory target before any promotion.",
            "Bind the packet digest to an explicit approval decision before writing.",
        ],
    },
    "publish": {
        "target_action": "publish_upload_or_external_delivery",
        "target_artifacts": [
            "metadata/upload_metadata.json",
            "social/social_pack.json",
            "social/social_pack.md",
        ],
        "future_write_targets": [
            "operator-approved upload/publish target",
            "delivery/export evidence record",
        ],
        "blocked_until_approved": [
            "direct_publish",
            "auto_upload",
            "external_delivery",
        ],
        "review_checklist": [
            "Review platform copy, title, description, hashtags, and CTA.",
            "Confirm target platforms and manual upload posture.",
            "Bind the packet digest to an explicit approval decision before upload or delivery.",
        ],
    },
    "timeline": {
        "target_action": "timeline_edit_execution",
        "target_artifacts": [
            "edit/edit_plan.json",
            "captions/captions.srt.json",
            "captions/captions.vtt.json",
            "captions/captions.srt",
            "captions/captions.vtt",
        ],
        "future_write_targets": [
            "operator-approved editor timeline or export target",
            "timeline execution proof record",
        ],
        "blocked_until_approved": [
            "timeline_edit_execution",
            "recordly_or_openscreen_or_obs_automation",
            "render_or_export_execution",
        ],
        "review_checklist": [
            "Review edit plan segments against the recording/transcript.",
            "Confirm captions are timed or manually acceptable before execution.",
            "Bind the packet digest to an explicit approval decision before editor automation.",
        ],
    },
}


class CreatorApprovalPreviewError(ValueError):
    """Raised when a Creator Engine approval packet preview cannot be prepared."""


@dataclass
class CreatorApprovalPacketPreviewResult:
    job_id: str
    source_recording_id: str
    generation_artifact_id: str
    generation_input_digest: str
    job_status: str
    approval_scope: str
    approval_packet_previews: list[dict[str, Any]] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "source_recording_id": self.source_recording_id,
            "generation_artifact_id": self.generation_artifact_id,
            "generation_input_digest": self.generation_input_digest,
            "job_status": self.job_status,
            "approval_scope": self.approval_scope,
            "approval_packet_count": len(self.approval_packet_previews),
            "approval_packet_previews": list(self.approval_packet_previews),
            "files_read": list(self.files_read),
            "files_written": list(self.files_written),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


@dataclass
class _ArtifactSnapshot:
    relative_path: str
    sha256: str
    artifact_type: str
    artifact_id: str | None = None
    status: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)

    def to_ref(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "path": self.relative_path,
            "sha256": self.sha256,
            "artifact_type": self.artifact_type,
        }
        if self.artifact_id:
            payload["artifact_id"] = self.artifact_id
        if self.status:
            payload["status"] = self.status
        if self.summary:
            payload["summary"] = dict(self.summary)
        return payload


def preview_creator_approval_packets(
    vault_root: str | Path,
    *,
    job_id: str,
    approval_scope: str = "all",
    job_store: CreatorJobStore | None = None,
) -> CreatorApprovalPacketPreviewResult:
    """Build deterministic read-only approval packet previews for draft artifacts."""

    if approval_scope not in APPROVAL_SCOPE_CHOICES:
        raise CreatorApprovalPreviewError(
            f"unsupported Creator Engine approval scope: {approval_scope}"
        )

    root = resolve_vault_root(vault_root)
    store = job_store or CreatorJobStore(root, create_root=False)
    job, job_ref = _load_job(root, store, job_id)
    if job.get("status") != "draft_ready":
        raise CreatorApprovalPreviewError("approval packet previews require a draft_ready Creator Engine job")

    manifest_snapshot, generation_manifest = _read_json_artifact(
        root,
        store,
        job_id,
        "generation/generation_manifest.json",
        missing_message="Creator Engine job is missing generation/generation_manifest.json",
    )
    _validate_generation_manifest(job, generation_manifest)

    source_recording_id = str(job.get("source_recording_id") or generation_manifest.get("source_recording_id") or "")
    generation_artifact_id = str(generation_manifest.get("artifact_id") or "")
    generation_input_digest = str(generation_manifest.get("input_digest") or "")
    selected_scopes = APPROVAL_SCOPES if approval_scope == "all" else (approval_scope,)

    files_read = [job_ref, manifest_snapshot.relative_path]
    packet_previews: list[dict[str, Any]] = []
    warnings = [
        "approval_preview_only_no_approval_artifact_written",
        "approval_consumption_not_implemented",
        "execution_publish_and_canonical_promotion_remain_blocked",
    ]

    for scope in selected_scopes:
        packet, scope_files = _build_scope_packet(
            root=root,
            store=store,
            job=job,
            job_id=job_id,
            source_recording_id=source_recording_id,
            generation_artifact_id=generation_artifact_id,
            generation_input_digest=generation_input_digest,
            generation_manifest=generation_manifest,
            manifest_snapshot=manifest_snapshot,
            scope=scope,
        )
        packet_previews.append(packet)
        files_read.extend(scope_files)

    return CreatorApprovalPacketPreviewResult(
        job_id=str(job.get("job_id", job_id)),
        source_recording_id=source_recording_id,
        generation_artifact_id=generation_artifact_id,
        generation_input_digest=generation_input_digest,
        job_status=str(job.get("status", "")),
        approval_scope=approval_scope,
        approval_packet_previews=packet_previews,
        files_read=list(dict.fromkeys(files_read)),
        files_written=[],
        warnings=warnings,
        blockers=[],
    )


def build_creator_approval_request(
    vault_root: str | Path,
    *,
    job_id: str,
    approval_scope: str,
    expected_approval_digest: str | None = None,
    requested_by: str = "operator",
    write_approval_request: bool = False,
    job_store: CreatorJobStore | None = None,
) -> dict[str, Any]:
    """Build or optionally write a pending Creator Engine approval request."""

    if approval_scope not in APPROVAL_SCOPES:
        raise CreatorApprovalPreviewError(
            f"approval request scope must be one of: {', '.join(APPROVAL_SCOPES)}"
        )

    root = resolve_vault_root(vault_root)
    preview = preview_creator_approval_packets(
        root,
        job_id=job_id,
        approval_scope=approval_scope,
        job_store=job_store,
    )
    packet = _single_packet_preview(preview, approval_scope)
    approval_packet_id = str(packet.get("approval_packet_id") or "")
    approval_digest = str(packet.get("approval_digest") or "")
    expected = (expected_approval_digest or "").strip()
    digest_matched = bool(expected and expected == approval_digest)
    blockers = list(preview.blockers)

    if not approval_packet_id:
        blockers.append("approval_packet_id_unavailable")
    if not approval_digest:
        blockers.append("approval_digest_unavailable")
    if expected and expected != approval_digest:
        blockers.append("expected_approval_digest_mismatch")
    if write_approval_request and not expected:
        blockers.append("expected_approval_digest_required_for_write")

    approval_rel_path, approval_abs_path = _approval_request_path(root, approval_packet_id or "unknown-approval-packet")
    artifact_preview = _approval_request_payload(
        vault_root=root,
        requested_by=requested_by,
        approval_artifact_path=approval_rel_path,
        source_preview=preview.to_dict(),
        packet=packet,
    )

    approval_artifact_written = False
    files_written: list[str] = []
    if write_approval_request:
        if approval_abs_path.exists():
            blockers.append("approval_artifact_already_exists_no_overwrite")
        if not blockers:
            approval_abs_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with approval_abs_path.open("x", encoding="utf-8") as handle:
                    handle.write(json.dumps(artifact_preview, indent=2, sort_keys=True) + "\n")
            except FileExistsError:
                blockers.append("approval_artifact_already_exists_no_overwrite")
            else:
                approval_artifact_written = True
                files_written.append(approval_rel_path)

    blockers = sorted(set(blockers))
    ready_to_write = not blockers
    ok = approval_artifact_written if write_approval_request else ready_to_write
    status = (
        "approval_request_written"
        if approval_artifact_written
        else "blocked"
        if blockers
        else "ready_to_write_approval_request"
    )
    authority_flags = _approval_request_authority_flags(artifact_written=approval_artifact_written)

    return {
        "ok": ok,
        "status": status,
        "command": "creator.write-approval-request",
        "schema_version": SCHEMA_VERSION,
        "packet_type": APPROVAL_REQUEST_PACKET_TYPE,
        "preview_only": not approval_artifact_written,
        "writes_performed": approval_artifact_written,
        "vault_root": str(root),
        "requested_by": requested_by,
        "job_id": preview.job_id,
        "source_recording_id": preview.source_recording_id,
        "generation_artifact_id": preview.generation_artifact_id,
        "generation_input_digest": preview.generation_input_digest,
        "approval_scope": approval_scope,
        "approval_packet_id": approval_packet_id,
        "approval_digest": approval_digest,
        "expected_approval_digest": expected,
        "approval_digest_matched": digest_matched,
        "approval_artifact_path": approval_rel_path,
        "write_approval_request_requested": write_approval_request,
        "approval_request_written": approval_artifact_written,
        "approval_artifact_written": approval_artifact_written,
        "approval_request_only": True,
        "ready_for_operator_decision": ready_to_write,
        "operator_confirmation_text": artifact_preview.get("operator_confirmation_text"),
        "approval_artifact_preview": artifact_preview,
        "approval_packet_preview": packet,
        "source_approval_preview": preview.to_dict(),
        "files_read": list(preview.files_read),
        "files_written": files_written,
        "warnings": list(preview.warnings),
        "blockers": blockers,
        "approval_granted": False,
        "approval_consumed": False,
        "approval_decision_written": False,
        "approval_consumption_marker_written": False,
        "timeline_edit_executed": False,
        "direct_publish_performed": False,
        "upload_performed": False,
        "external_delivery_performed": False,
        "canonical_writeback_performed": False,
        "governed_memory_write_performed": False,
        "provider_or_model_call_performed": False,
        "authority_flags": authority_flags,
        "next_recommended_pass": (
            "creator-engine-pass11-approval-consumption-dry-run"
            if approval_artifact_written
            else "creator-engine-pass10-approval-request-writer"
            if ready_to_write
            else "creator-engine-approval-request-repair"
        ),
    }


def build_creator_approval_consumption_dry_run(
    approval_artifact_path: str | Path,
    *,
    expected_approval_digest: str | None = None,
    vault_root: str | Path | None = None,
    job_store: CreatorJobStore | None = None,
) -> dict[str, Any]:
    """Validate a pending Creator Engine approval request without consuming it."""

    root = resolve_vault_root(vault_root or Path.cwd())
    approval_abs_path, approval_path_inside = _resolve_inside_vault(root, approval_artifact_path)
    approval_rel_path = relative_to_vault(root, approval_abs_path) if approval_path_inside else str(approval_artifact_path)
    expected = (expected_approval_digest or "").strip()
    blockers: list[str] = []
    errors: list[str] = []

    approval_payload: dict[str, Any] | None = None
    if not approval_path_inside:
        blockers.append("approval_artifact_path_outside_vault")
    elif not approval_abs_path.is_file():
        blockers.append("approval_artifact_missing")
    else:
        approval_payload, read_error = _read_json_object(
            approval_abs_path,
            artifact_label="approval_artifact",
        )
        if read_error:
            blockers.append(read_error.split(":", 1)[0])
            errors.append(read_error)

    payload = approval_payload or {}
    authority = payload.get("authority_flags") if isinstance(payload.get("authority_flags"), dict) else {}
    approval_packet_id = str(payload.get("approval_packet_id") or "")
    approval_scope = str(payload.get("approval_scope") or "")
    artifact_approval_digest = str(payload.get("approval_digest") or "")
    artifact_status = str(payload.get("status") or "")
    artifact_job_id = str(payload.get("job_id") or "")
    artifact_requested_action = str(payload.get("requested_action") or "")
    source_recording_id = str(payload.get("source_recording_id") or "")
    generation_artifact_id = str(payload.get("generation_artifact_id") or "")
    generation_input_digest = str(payload.get("generation_input_digest") or "")

    if approval_payload is not None:
        if payload.get("schema_version") != SCHEMA_VERSION:
            blockers.append("approval_request_schema_invalid")
        if payload.get("packet_type") != APPROVAL_REQUEST_PACKET_TYPE:
            blockers.append("approval_request_packet_type_invalid")
        if artifact_status == APPROVAL_REQUEST_STATUS:
            blockers.append("operator_approval_decision_required")
        else:
            blockers.append("unsupported_approval_status_until_decision_schema_exists")
        if approval_scope not in APPROVAL_SCOPES:
            blockers.append("approval_scope_invalid")
        if not approval_packet_id:
            blockers.append("approval_packet_id_missing")
        elif not _packet_id_path_safe(approval_packet_id):
            blockers.append("approval_packet_id_path_unsafe")
        if not artifact_job_id:
            blockers.append("job_id_missing")
        if not artifact_approval_digest:
            blockers.append("approval_digest_missing")
        if expected and expected != artifact_approval_digest:
            blockers.append("expected_approval_digest_mismatch")
        if payload.get("approval_request_only") is not True:
            blockers.append("approval_artifact_not_request_only")
        if payload.get("approval_granted") is not False:
            blockers.append("approval_artifact_must_not_grant_approval")
        if payload.get("approval_consumed") is not False:
            blockers.append("approval_artifact_already_consumed_or_ambiguous")
        if payload.get("approval_decision_written") is not False:
            blockers.append("approval_decision_already_written_or_ambiguous")
        if payload.get("approval_consumption_marker_written") is not False:
            blockers.append("approval_consumption_marker_already_written_or_ambiguous")
        if payload.get("timeline_edit_executed") is not False:
            blockers.append("approval_artifact_timeline_execution_state_invalid")
        if payload.get("direct_publish_performed") is not False or payload.get("upload_performed") is not False:
            blockers.append("approval_artifact_publish_state_invalid")
        if payload.get("canonical_writeback_performed") is not False:
            blockers.append("approval_artifact_canonical_state_invalid")
        if payload.get("governed_memory_write_performed") is not False:
            blockers.append("approval_artifact_governed_memory_state_invalid")
        if authority.get("approval_consumption_allowed") is not False:
            blockers.append("approval_authority_does_not_block_consumption")
        if authority.get("approval_marker_write_allowed") is not False:
            blockers.append("approval_authority_does_not_block_marker_write")
        if authority.get("timeline_edit_execution_allowed") is not False:
            blockers.append("approval_authority_does_not_block_timeline_execution")
        if authority.get("direct_publish_allowed") is not False or authority.get("upload_allowed") is not False:
            blockers.append("approval_authority_does_not_block_publish_or_upload")
        if authority.get("canonical_writeback_allowed") is not False:
            blockers.append("approval_authority_does_not_block_canonical_writeback")

    current_preview: CreatorApprovalPacketPreviewResult | None = None
    current_packet: dict[str, Any] | None = None
    current_approval_digest = ""
    current_approval_packet_id = ""
    current_requested_action = ""
    current_files_read: list[str] = []
    if approval_payload is not None and artifact_job_id and approval_scope in APPROVAL_SCOPES:
        try:
            current_preview = preview_creator_approval_packets(
                root,
                job_id=artifact_job_id,
                approval_scope=approval_scope,
                job_store=job_store,
            )
            current_packet = _single_packet_preview(current_preview, approval_scope)
            current_files_read = list(current_preview.files_read)
        except CreatorApprovalPreviewError as exc:
            blockers.append("current_approval_preview_not_ready")
            errors.append(str(exc))
        else:
            current_approval_digest = str(current_packet.get("approval_digest") or "")
            current_approval_packet_id = str(current_packet.get("approval_packet_id") or "")
            current_requested_action = str(current_packet.get("target_action") or "")
            if current_approval_digest != artifact_approval_digest:
                blockers.append("current_approval_digest_mismatch")
            if current_approval_packet_id != approval_packet_id:
                blockers.append("current_approval_packet_id_mismatch")
            if current_requested_action != artifact_requested_action:
                blockers.append("current_requested_action_mismatch")

    marker_rel_path = ""
    marker_abs_path: Path | None = None
    marker_path_inside = False
    marker_exists = False
    if approval_packet_id and _packet_id_path_safe(approval_packet_id):
        marker_rel_path, marker_abs_path = _consumption_marker_path(root, approval_packet_id)
        marker_path_inside = True
        marker_exists = marker_abs_path.exists()
        if marker_exists:
            blockers.append("approval_consumption_marker_already_exists")

    blockers = sorted(set(blockers))
    non_decision_blockers = [
        blocker for blocker in blockers if blocker != "operator_approval_decision_required"
    ]
    dry_run_valid = approval_payload is not None and not non_decision_blockers
    status = (
        "blocked_pending_operator_decision"
        if dry_run_valid and "operator_approval_decision_required" in blockers
        else "blocked"
        if blockers
        else "approval_consumption_dry_run_ready_no_execution"
    )
    checks = {
        "approval_artifact_path_in_vault": approval_path_inside,
        "approval_artifact_present": approval_abs_path.is_file() if approval_path_inside else False,
        "approval_artifact_json_valid": approval_payload is not None,
        "approval_schema_valid": payload.get("schema_version") == SCHEMA_VERSION,
        "approval_packet_type_valid": payload.get("packet_type") == APPROVAL_REQUEST_PACKET_TYPE,
        "approval_status_pending": artifact_status == APPROVAL_REQUEST_STATUS,
        "approval_request_only": payload.get("approval_request_only") is True,
        "approval_not_granted": payload.get("approval_granted") is False,
        "approval_not_consumed": payload.get("approval_consumed") is False,
        "approval_digest_present": bool(artifact_approval_digest),
        "expected_approval_digest_matches": (expected == artifact_approval_digest) if expected else None,
        "current_preview_recomputed": current_preview is not None,
        "current_approval_digest_matches_artifact": bool(
            current_approval_digest and current_approval_digest == artifact_approval_digest
        ),
        "current_approval_packet_id_matches_artifact": bool(
            current_approval_packet_id and current_approval_packet_id == approval_packet_id
        ),
        "current_requested_action_matches_artifact": bool(
            current_requested_action and current_requested_action == artifact_requested_action
        ),
        "future_consumption_marker_path_in_vault": marker_path_inside,
        "future_consumption_marker_absent": bool(marker_abs_path and not marker_exists),
        "no_writes_performed": True,
        "approval_consumption_blocked": True,
        "approval_decision_write_blocked": True,
        "approval_marker_write_blocked": True,
        "timeline_execution_blocked": True,
        "publish_upload_blocked": True,
        "canonical_writeback_blocked": True,
    }
    authority_flags = _approval_consumption_dry_run_authority_flags()
    files_read = [approval_rel_path]
    files_read.extend(current_files_read)

    return {
        "ok": dry_run_valid,
        "status": status,
        "command": "creator.approval-consumption-dry-run",
        "schema_version": SCHEMA_VERSION,
        "packet_type": APPROVAL_CONSUMPTION_DRY_RUN_PACKET_TYPE,
        "read_only": True,
        "preview_only": True,
        "writes_performed": False,
        "vault_root": str(root),
        "approval_artifact_path": approval_rel_path,
        "approval_artifact_loaded": approval_payload is not None,
        "approval_status": artifact_status,
        "approval_packet_id": approval_packet_id,
        "approval_scope": approval_scope,
        "requested_action": artifact_requested_action,
        "job_id": artifact_job_id,
        "source_recording_id": source_recording_id,
        "generation_artifact_id": generation_artifact_id,
        "generation_input_digest": generation_input_digest,
        "approval_digest": artifact_approval_digest,
        "expected_approval_digest": expected,
        "approval_digest_matched": (expected == artifact_approval_digest) if expected else None,
        "current_approval_digest": current_approval_digest,
        "current_approval_packet_id": current_approval_packet_id,
        "current_requested_action": current_requested_action,
        "future_consumption_marker_path": marker_rel_path,
        "future_consumption_marker_exists": marker_exists,
        "approval_request_valid_for_decision_boundary": dry_run_valid,
        "approval_consumption_ready": False,
        "approval_consumption_ready_for_future_executor": False,
        "approval_granted": False,
        "approval_consumed": False,
        "approval_decision_written": False,
        "approval_consumption_marker_written": False,
        "timeline_edit_executed": False,
        "direct_publish_performed": False,
        "upload_performed": False,
        "external_delivery_performed": False,
        "canonical_writeback_performed": False,
        "governed_memory_write_performed": False,
        "provider_or_model_call_performed": False,
        "approval_artifact": approval_payload,
        "current_approval_preview": current_preview.to_dict() if current_preview else None,
        "current_approval_packet": current_packet,
        "files_read": list(dict.fromkeys(files_read)),
        "files_written": [],
        "checks": checks,
        "blockers": blockers,
        "errors": errors,
        "authority_flags": authority_flags,
        "blocked_effects": [
            "approval_grant",
            "approval_decision_write",
            "approval_consumption",
            "approval_consumption_marker_write",
            "timeline_edit_execution",
            "direct_publish_or_upload",
            "external_delivery",
            "canonical_state_change",
            "governed_memory_write",
            "provider_or_model_call",
        ],
        "next_recommended_pass": (
            "creator-engine-pass12-approval-review-decision-contract"
            if dry_run_valid
            else "creator-engine-pass11-approval-consumption-dry-run-repair"
        ),
    }


def _load_job(root: Path, store: CreatorJobStore, job_id: str) -> tuple[dict[str, Any], str]:
    try:
        job = store.load_job(job_id)
    except Exception as exc:
        raise CreatorApprovalPreviewError(f"Creator Engine job not found: {job_id}") from exc
    return job, relative_to_vault(root, artifact_path(root, job_id, "job.json", store.job_root))


def _build_scope_packet(
    *,
    root: Path,
    store: CreatorJobStore,
    job: dict[str, Any],
    job_id: str,
    source_recording_id: str,
    generation_artifact_id: str,
    generation_input_digest: str,
    generation_manifest: dict[str, Any],
    manifest_snapshot: _ArtifactSnapshot,
    scope: str,
) -> tuple[dict[str, Any], list[str]]:
    spec = _SCOPE_SPECS[scope]
    artifact_snapshots = [
        _read_artifact(
            root,
            store,
            job_id,
            relative_path,
            missing_message=f"Creator Engine approval scope {scope} is missing {relative_path}",
        )
        for relative_path in spec["target_artifacts"]
    ]
    digest = _approval_digest(
        job_id=job_id,
        scope=scope,
        target_action=str(spec["target_action"]),
        generation_artifact_id=generation_artifact_id,
        generation_input_digest=generation_input_digest,
        manifest_snapshot=manifest_snapshot,
        artifact_snapshots=artifact_snapshots,
    )
    packet_id = f"creator-approval-{scope}-{digest[:12]}"
    target_artifact_refs = [snapshot.to_ref() for snapshot in artifact_snapshots]
    return (
        {
            "schema_version": SCHEMA_VERSION,
            "packet_type": APPROVAL_PACKET_TYPE,
            "status": "preview_only",
            "approval_scope": scope,
            "approval_packet_id": packet_id,
            "approval_digest": digest,
            "job_id": job.get("job_id", job_id),
            "source_recording_id": source_recording_id,
            "generation_artifact_id": generation_artifact_id,
            "generation_input_digest": generation_input_digest,
            "target_action": spec["target_action"],
            "operator_approval_required": True,
            "approval_artifact_written": False,
            "approval_consumed": False,
            "execution_allowed": False,
            "writes_performed": False,
            "target_artifacts": target_artifact_refs,
            "source_refs": _source_refs(generation_manifest, artifact_snapshots),
            "future_approval_artifact_path": f"{FUTURE_APPROVAL_ROOT}/{packet_id}.json",
            "future_write_targets": list(spec["future_write_targets"]),
            "future_command_hint": (
                "run creator write-approval-request with this approval_digest to persist "
                "a pending request; consumption and execution remain separate future gates"
            ),
            "blocked_until_approved": list(spec["blocked_until_approved"]),
            "review_checklist": list(spec["review_checklist"]),
            "authority_flags": _approval_authority_flags(scope),
            "blockers": [
                "approval_artifact_not_written_by_preview",
                "approval_consumption_not_implemented",
                f"{spec['target_action']}_blocked",
            ],
            "warnings": [
                "preview_only_no_runtime_state_change",
                "review_artifacts_may_be_deterministic_stubs",
            ],
        },
        [snapshot.relative_path for snapshot in artifact_snapshots],
    )


def _read_json_artifact(
    root: Path,
    store: CreatorJobStore,
    job_id: str,
    relative_path: str,
    *,
    missing_message: str,
) -> tuple[_ArtifactSnapshot, dict[str, Any]]:
    snapshot = _read_artifact(root, store, job_id, relative_path, missing_message=missing_message)
    path = artifact_path(root, job_id, relative_path, store.job_root)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CreatorApprovalPreviewError(f"{relative_path} is not valid JSON") from exc
    if not isinstance(loaded, dict):
        raise CreatorApprovalPreviewError(f"{relative_path} is not a JSON object")
    return _artifact_snapshot_for_json(snapshot, loaded), loaded


def _read_artifact(
    root: Path,
    store: CreatorJobStore,
    job_id: str,
    relative_path: str,
    *,
    missing_message: str,
) -> _ArtifactSnapshot:
    path = artifact_path(root, job_id, relative_path, store.job_root)
    if not path.exists():
        raise CreatorApprovalPreviewError(missing_message)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CreatorApprovalPreviewError(f"could not read Creator Engine artifact: {relative_path}") from exc
    snapshot = _ArtifactSnapshot(
        relative_path=relative_to_vault(root, path),
        sha256=hashlib.sha256(raw).hexdigest(),
        artifact_type=_artifact_type_for_path(relative_path),
    )
    if relative_path.endswith(".json"):
        try:
            loaded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CreatorApprovalPreviewError(f"{relative_path} is not valid UTF-8 JSON") from exc
        if not isinstance(loaded, dict):
            raise CreatorApprovalPreviewError(f"{relative_path} is not a JSON object")
        snapshot = _artifact_snapshot_for_json(snapshot, loaded)
    return snapshot


def _artifact_snapshot_for_json(
    snapshot: _ArtifactSnapshot,
    loaded: dict[str, Any],
) -> _ArtifactSnapshot:
    summary: dict[str, Any] = {}
    for key in (
        "target_platforms",
        "approval_required",
        "canonical_promotion_allowed",
        "publish_allowed",
        "upload_allowed",
        "manual_upload_only",
        "generation_mode",
    ):
        if key in loaded:
            summary[key] = loaded[key]
    if isinstance(loaded.get("posts"), list):
        summary["post_count"] = len(loaded["posts"])
    if isinstance(loaded.get("timeline"), list):
        summary["timeline_segment_count"] = len(loaded["timeline"])
    return _ArtifactSnapshot(
        relative_path=snapshot.relative_path,
        sha256=snapshot.sha256,
        artifact_type=str(loaded.get("artifact_type") or snapshot.artifact_type),
        artifact_id=str(loaded["artifact_id"]) if loaded.get("artifact_id") else None,
        status=str(loaded["status"]) if loaded.get("status") else None,
        summary=summary,
    )


def _validate_generation_manifest(job: dict[str, Any], manifest: dict[str, Any]) -> None:
    if manifest.get("job_id") != job.get("job_id"):
        raise CreatorApprovalPreviewError("generation_manifest.json job_id does not match the Creator Engine job")
    if manifest.get("status") != "draft_stub_ready":
        raise CreatorApprovalPreviewError("generation_manifest.json is not draft_stub_ready")
    if not manifest.get("input_digest"):
        raise CreatorApprovalPreviewError("generation_manifest.json is missing input_digest")
    authority_flags = manifest.get("authority_flags")
    if isinstance(authority_flags, dict) and authority_flags.get("provider_call_allowed") is True:
        raise CreatorApprovalPreviewError("generation_manifest.json unexpectedly allows provider calls")


def _approval_digest(
    *,
    job_id: str,
    scope: str,
    target_action: str,
    generation_artifact_id: str,
    generation_input_digest: str,
    manifest_snapshot: _ArtifactSnapshot,
    artifact_snapshots: list[_ArtifactSnapshot],
) -> str:
    payload = {
        "job_id": job_id,
        "scope": scope,
        "target_action": target_action,
        "generation_artifact_id": generation_artifact_id,
        "generation_input_digest": generation_input_digest,
        "generation_manifest_sha256": manifest_snapshot.sha256,
        "artifacts": [
            {
                "path": snapshot.relative_path,
                "sha256": snapshot.sha256,
                "artifact_type": snapshot.artifact_type,
                "artifact_id": snapshot.artifact_id,
            }
            for snapshot in artifact_snapshots
        ],
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _single_packet_preview(
    preview: CreatorApprovalPacketPreviewResult,
    approval_scope: str,
) -> dict[str, Any]:
    packets = list(preview.approval_packet_previews)
    if len(packets) != 1:
        raise CreatorApprovalPreviewError(
            f"approval request requires exactly one approval packet for scope: {approval_scope}"
        )
    packet = packets[0]
    if packet.get("approval_scope") != approval_scope:
        raise CreatorApprovalPreviewError("approval packet scope does not match requested approval scope")
    return packet


def _approval_request_path(root: Path, approval_packet_id: str) -> tuple[str, Path]:
    relative = Path(*FUTURE_APPROVAL_ROOT.split("/")) / f"{approval_packet_id}.json"
    absolute = ensure_within(root, root / relative)
    return relative.as_posix(), absolute


def _consumption_marker_path(root: Path, approval_packet_id: str) -> tuple[str, Path]:
    relative = Path(*FUTURE_CONSUMPTION_MARKER_ROOT.split("/")) / f"{approval_packet_id}.json"
    absolute = ensure_within(root, root / relative)
    return relative.as_posix(), absolute


def _resolve_inside_vault(root: Path, candidate: str | Path) -> tuple[Path, bool]:
    path = Path(candidate)
    absolute = path.resolve() if path.is_absolute() else (root / path).resolve()
    try:
        confined = ensure_within(root, absolute)
    except Exception:
        return absolute, False
    return confined, True


def _read_json_object(path: Path, *, artifact_label: str = "artifact") -> tuple[dict[str, Any] | None, str | None]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"{artifact_label}_read_error:{exc}"
    except json.JSONDecodeError as exc:
        return None, f"{artifact_label}_json_invalid:{exc}"
    if not isinstance(loaded, dict):
        return None, f"{artifact_label}_json_not_object"
    return loaded, None


def _packet_id_path_safe(packet_id: str) -> bool:
    if not packet_id or packet_id in {".", ".."}:
        return False
    return Path(packet_id).name == packet_id and "/" not in packet_id and "\\" not in packet_id


def _approval_request_payload(
    *,
    vault_root: Path,
    requested_by: str,
    approval_artifact_path: str,
    source_preview: dict[str, Any],
    packet: dict[str, Any],
) -> dict[str, Any]:
    approval_scope = str(packet.get("approval_scope") or "")
    approval_digest = str(packet.get("approval_digest") or "")
    return {
        "schema_version": SCHEMA_VERSION,
        "packet_type": APPROVAL_REQUEST_PACKET_TYPE,
        "status": APPROVAL_REQUEST_STATUS,
        "created_at": utc_now(),
        "requested_by": requested_by,
        "vault_root": str(vault_root),
        "approval_artifact_path": approval_artifact_path,
        "approval_packet_id": packet.get("approval_packet_id"),
        "approval_digest": approval_digest,
        "approval_scope": approval_scope,
        "requested_action": packet.get("target_action"),
        "job_id": packet.get("job_id"),
        "source_recording_id": packet.get("source_recording_id"),
        "generation_artifact_id": packet.get("generation_artifact_id"),
        "generation_input_digest": packet.get("generation_input_digest"),
        "target_artifacts": list(packet.get("target_artifacts") or []),
        "source_refs": list(packet.get("source_refs") or []),
        "future_write_targets": list(packet.get("future_write_targets") or []),
        "blocked_until_approved": list(packet.get("blocked_until_approved") or []),
        "review_checklist": list(packet.get("review_checklist") or []),
        "operator_confirmation_text": _operator_confirmation_text(packet),
        "approval_request_only": True,
        "approval_granted": False,
        "approval_consumed": False,
        "approval_decision_written": False,
        "approval_consumption_marker_written": False,
        "timeline_edit_executed": False,
        "direct_publish_performed": False,
        "upload_performed": False,
        "external_delivery_performed": False,
        "canonical_writeback_performed": False,
        "governed_memory_write_performed": False,
        "provider_or_model_call_performed": False,
        "authority_flags": _approval_request_authority_flags(artifact_written=False),
        "approval_packet_preview": packet,
        "source_approval_preview": source_preview,
        "future_decision_requirements": [
            "operator decision artifact must bind this exact approval_digest",
            "operator decision artifact must bind this exact approval_scope and requested_action",
            "denied decisions must block future consumption",
            "approval request must remain unconsumed until a separate exact-once consumption gate runs",
        ],
        "future_executor_requirements": [
            "recompute the approval packet digest immediately before consumption",
            "match approval request, approval decision, job id, approval scope, and digest",
            "reserve an exact-once consumption marker before any future execution",
            "execute only the approved scope and write proof artifacts before external or canonical effects",
        ],
    }


def _operator_confirmation_text(packet: dict[str, Any]) -> str:
    return "\n".join(
        [
            "APPROVE CREATOR ENGINE REQUEST ONLY:",
            f"- approval_packet_id: {packet.get('approval_packet_id') or ''}",
            f"- job_id: {packet.get('job_id') or ''}",
            f"- approval_scope: {packet.get('approval_scope') or ''}",
            f"- target_action: {packet.get('target_action') or ''}",
            f"- approval_digest: {packet.get('approval_digest') or ''}",
            "",
            "This approval request does not grant execution by itself.",
        ]
    )


def _source_refs(
    generation_manifest: dict[str, Any],
    artifact_snapshots: list[_ArtifactSnapshot],
) -> list[str]:
    refs: list[str] = []
    for ref in generation_manifest.get("source_refs") or []:
        if ref:
            refs.append(str(ref))
    for snapshot in artifact_snapshots:
        refs.append(snapshot.relative_path)
    return list(dict.fromkeys(refs))


def _artifact_type_for_path(relative_path: str) -> str:
    name = Path(relative_path).name
    if name.endswith(".md"):
        return "markdown_artifact"
    if name.endswith(".srt") or name.endswith(".vtt"):
        return "caption_file"
    return "creator_artifact"


def _approval_authority_flags(scope: str) -> dict[str, bool]:
    return {
        "runtime_local_read_allowed": True,
        "approval_preview_allowed": True,
        "approval_artifact_write_allowed": False,
        "approval_decision_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_marker_write_allowed": False,
        "execution_allowed": False,
        "content_memory_card_canonical_promotion_allowed": False,
        "timeline_edit_execution_allowed": False,
        "direct_publish_allowed": False,
        "upload_allowed": False,
        "external_delivery_allowed": False,
        "provider_call_allowed": False,
        "governed_memory_write_allowed": False,
        f"{scope.replace('-', '_')}_approval_scope_preview": True,
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
        "execution_allowed": False,
        "content_memory_card_canonical_promotion_allowed": False,
        "timeline_edit_execution_allowed": False,
        "direct_publish_allowed": False,
        "upload_allowed": False,
        "external_delivery_allowed": False,
        "provider_call_allowed": False,
        "governed_memory_write_allowed": False,
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
        "execution_allowed": False,
        "content_memory_card_canonical_promotion_allowed": False,
        "timeline_edit_execution_allowed": False,
        "direct_publish_allowed": False,
        "upload_allowed": False,
        "external_delivery_allowed": False,
        "canonical_writeback_allowed": False,
        "governed_memory_write_allowed": False,
        "provider_call_allowed": False,
    }
