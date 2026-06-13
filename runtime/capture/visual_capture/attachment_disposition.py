"""Attachment disposition controls for Capture to Markdown artifacts.

The default disposition layer is review metadata. A separate guarded cleanup
executor is available only for quarantine-local copied attachments after an
exact operator confirmation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import VisualCaptureAttachment, utc_now


ATTACHMENT_DISPOSITION_POLICY_ID = "vcmi.attachment_disposition.v1"
ATTACHMENT_CLEANUP_POLICY_ID = "vcmi.attachment_cleanup_executor.v1"
ATTACHMENT_DELETE_CONFIRMATION = "DELETE CAPTURE ATTACHMENTS"

ATTACHMENT_DISPOSITION_DECISIONS = (
    "retain",
    "retain-until-downstream-review",
    "needs-redaction",
    "delete-requested",
)

ATTACHMENT_DISPOSITION_AUTHORITY = {
    "metadata_write_allowed": True,
    "runtime_delete_allowed": False,
    "studio_delete_controls_allowed": True,
    "cleanup_executor_available": True,
    "cleanup_requires_exact_operator_confirmation": True,
    "cleanup_scope": "quarantine_local_copied_attachments_only",
    "operator_delete_decision_required": True,
    "content_rewrite_allowed": False,
    "canonical_mutation_allowed": False,
    "provider_call_allowed": False,
    "external_send_allowed": False,
}

_REVIEW_STATUS_TO_DISPOSITION = {
    "reviewed": "retain",
    "pending-review": "retain-until-downstream-review",
    "needs-redaction": "needs-redaction",
    "rejected": "retain-until-downstream-review",
}


def build_attachment_disposition_policy(
    attachments: list[VisualCaptureAttachment] | list[dict[str, Any]] | None,
    *,
    review_status: str = "pending-review",
    requested_disposition: str | None = None,
) -> dict[str, Any]:
    """Return the attachment disposition contract."""

    normalized = [_coerce_attachment(item, index) for index, item in enumerate(attachments or [], start=1)]
    normalized = [item for item in normalized if item is not None]
    disposition = _normalize_disposition(requested_disposition, review_status)

    if not normalized:
        return {
            "policy_id": ATTACHMENT_DISPOSITION_POLICY_ID,
            "status": "metadata_policy_only",
            "applicable": False,
            "attachment_count": 0,
            "review_status": review_status or "pending-review",
            "default_disposition": "not-applicable",
            "supported_dispositions": list(ATTACHMENT_DISPOSITION_DECISIONS),
            "runtime_delete_allowed": False,
            "studio_delete_controls_allowed": True,
            "cleanup_executor_available": True,
            "delete_request_status": "not_applicable",
            "cleanup_requires_exact_operator_confirmation": True,
            "delete_confirmation_phrase": ATTACHMENT_DELETE_CONFIRMATION,
            "authority": dict(ATTACHMENT_DISPOSITION_AUTHORITY),
            "forbidden_effects": _forbidden_effects(),
        }

    rows = []
    for attachment in normalized:
        rows.append(
            {
                "attachment_id": attachment.attachment_id,
                "filename": attachment.filename,
                "relative_path": attachment.relative_path,
                "mime_type": attachment.mime_type,
                "sha256": attachment.sha256,
                "size_bytes": attachment.size_bytes,
                "redaction_status": attachment.redaction_status,
                "review_status": review_status or "pending-review",
                "current_disposition": disposition,
                "runtime_delete_allowed": False,
                "studio_delete_controls_allowed": True,
                "cleanup_executor_available": True,
                "cleanup_requires_exact_operator_confirmation": True,
                "delete_request_status": (
                    "metadata_only_requested"
                    if disposition == "delete-requested"
                    else "not_requested"
                ),
            }
        )

    return {
        "policy_id": ATTACHMENT_DISPOSITION_POLICY_ID,
        "status": "metadata_policy_only",
        "applicable": True,
        "attachment_count": len(rows),
        "review_status": review_status or "pending-review",
        "default_disposition": disposition,
        "supported_dispositions": list(ATTACHMENT_DISPOSITION_DECISIONS),
        "runtime_delete_allowed": False,
        "studio_delete_controls_allowed": True,
        "cleanup_executor_available": True,
        "cleanup_requires_exact_operator_confirmation": True,
        "delete_confirmation_phrase": ATTACHMENT_DELETE_CONFIRMATION,
        "cleanup_scope": "quarantine_local_copied_attachments_only",
        "delete_request_status": (
            "metadata_only_requested"
            if disposition == "delete-requested"
            else "not_requested"
        ),
        "operator_decision_required_for_delete": True,
        "operator_review_required": disposition != "retain",
        "attachments": rows,
        "authority": dict(ATTACHMENT_DISPOSITION_AUTHORITY),
        "forbidden_effects": _forbidden_effects(),
        "governance_note": (
            "Attachment disposition records retain/redaction/delete-request intent. "
            "Studio cleanup can delete only quarantine-local copied attachments after "
            "an exact operator confirmation. It never rewrites captured Markdown, "
            "calls providers, sends externally, or promotes canonical state."
        ),
    }


def update_capture_attachment_disposition(
    vault_root: str | Path,
    capture_path: str | Path,
    *,
    requested_disposition: str,
    reviewed_by: str = "operator",
    review_note: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update disposition metadata for one Capture to Markdown artifact."""

    vault = Path(vault_root).resolve()
    triplet = _resolve_capture_triplet(vault, capture_path)
    sidecar = _load_json(triplet["sidecar_abs"], "sidecar")
    packet = _load_optional_json(triplet["packet_abs"], "visual capture packet")
    vc_meta = _visual_capture_metadata(sidecar, packet)
    attachments = _attachments_from_metadata(vc_meta)
    current_review_status = str(vc_meta.get("review_status") or sidecar.get("review_status") or "pending-review")
    policy = build_attachment_disposition_policy(
        attachments,
        review_status=current_review_status,
        requested_disposition=requested_disposition,
    )
    decision = {
        "policy_id": ATTACHMENT_DISPOSITION_POLICY_ID,
        "updated_at": utc_now(),
        "updated_by": str(reviewed_by or "operator").strip() or "operator",
        "review_note": str(review_note or "").strip(),
        "requested_disposition": policy["default_disposition"],
        "attachment_count": policy["attachment_count"],
        "dry_run": bool(dry_run),
    }
    updated_sidecar = _apply_disposition_metadata(sidecar, vc_meta, policy, decision)
    updated_packet = _apply_disposition_packet_metadata(packet, policy, decision) if packet else None
    if not dry_run:
        _write_json(triplet["sidecar_abs"], updated_sidecar)
        if updated_packet is not None:
            _write_json(triplet["packet_abs"], updated_packet)
    return {
        "ok": True,
        "policy_id": ATTACHMENT_DISPOSITION_POLICY_ID,
        "status": "attachment_disposition_updated",
        "content_path": triplet["content_rel"],
        "sidecar_path": triplet["sidecar_rel"],
        "visual_capture_packet_path": triplet["packet_rel"] if triplet["packet_abs"].exists() else "",
        "requested_disposition": policy["default_disposition"],
        "attachment_count": policy["attachment_count"],
        "write_performed": not dry_run,
        "attachment_disposition_policy": policy,
        "authority": {
            "sidecar_write": True,
            "visual_capture_packet_json_write": bool(packet),
            "attachment_delete_performed": False,
            "content_write_allowed": False,
            "canonical_mutation_allowed": False,
            "provider_call_allowed": False,
            "external_send_allowed": False,
        },
    }


def cleanup_capture_attachments(
    vault_root: str | Path,
    capture_path: str | Path,
    *,
    operator_confirmed: bool = False,
    confirmation_phrase: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Delete only copied quarantine attachments after exact confirmation."""

    vault = Path(vault_root).resolve()
    triplet = _resolve_capture_triplet(vault, capture_path)
    sidecar = _load_json(triplet["sidecar_abs"], "sidecar")
    packet = _load_optional_json(triplet["packet_abs"], "visual capture packet")
    vc_meta = _visual_capture_metadata(sidecar, packet)
    policy = vc_meta.get("attachment_disposition_policy") if isinstance(vc_meta.get("attachment_disposition_policy"), dict) else {}
    if not operator_confirmed:
        return _cleanup_denied(triplet, "operator_confirmation_required")
    if str(confirmation_phrase or "").strip() != ATTACHMENT_DELETE_CONFIRMATION:
        return _cleanup_denied(triplet, "exact_delete_confirmation_required")
    if policy.get("default_disposition") != "delete-requested":
        return _cleanup_denied(triplet, "delete_request_disposition_required")

    attachments = _attachments_from_metadata(vc_meta)
    targets = [_cleanup_target(vault, attachment) for attachment in attachments]
    targets = [target for target in targets if target is not None]
    if not targets:
        return _cleanup_denied(triplet, "no_quarantine_local_attachments_to_delete")

    deleted = []
    for attachment, target_path in targets:
        existed = target_path.exists()
        if existed and not dry_run:
            target_path.unlink()
        deleted.append(
            {
                "attachment_id": attachment.get("attachment_id") or "",
                "relative_path": attachment.get("relative_path") or "",
                "deleted": existed and not dry_run,
                "would_delete": existed and dry_run,
            }
        )

    cleanup_record = {
        "policy_id": ATTACHMENT_CLEANUP_POLICY_ID,
        "cleaned_at": utc_now(),
        "dry_run": bool(dry_run),
        "deleted_count": len([item for item in deleted if item["deleted"]]),
        "would_delete_count": len([item for item in deleted if item["would_delete"]]),
        "attachments": deleted,
    }
    updated_sidecar = _apply_cleanup_metadata(sidecar, vc_meta, cleanup_record)
    updated_packet = _apply_cleanup_packet_metadata(packet, cleanup_record) if packet else None
    if not dry_run:
        _write_json(triplet["sidecar_abs"], updated_sidecar)
        if updated_packet is not None:
            _write_json(triplet["packet_abs"], updated_packet)
    return {
        "ok": True,
        "policy_id": ATTACHMENT_CLEANUP_POLICY_ID,
        "status": "attachment_cleanup_completed" if not dry_run else "attachment_cleanup_dry_run",
        "content_path": triplet["content_rel"],
        "sidecar_path": triplet["sidecar_rel"],
        "visual_capture_packet_path": triplet["packet_rel"] if triplet["packet_abs"].exists() else "",
        "deleted_count": cleanup_record["deleted_count"],
        "would_delete_count": cleanup_record["would_delete_count"],
        "write_performed": not dry_run,
        "attachments": deleted,
        "authority": {
            "operator_confirmed": True,
            "exact_confirmation_phrase_matched": True,
            "quarantine_local_attachment_delete_allowed": True,
            "content_write_allowed": False,
            "canonical_mutation_allowed": False,
            "provider_call_allowed": False,
            "external_send_allowed": False,
        },
    }


def _normalize_disposition(value: str | None, review_status: str) -> str:
    requested = str(value or "").strip().lower()
    if requested:
        if requested not in ATTACHMENT_DISPOSITION_DECISIONS:
            raise ValueError(
                f"Unsupported attachment disposition '{value}'. "
                f"Valid dispositions: {list(ATTACHMENT_DISPOSITION_DECISIONS)}"
            )
        return requested
    return _REVIEW_STATUS_TO_DISPOSITION.get(
        str(review_status or "").strip().lower(),
        "retain-until-downstream-review",
    )


def _coerce_attachment(item: VisualCaptureAttachment | dict[str, Any], index: int) -> VisualCaptureAttachment | None:
    if isinstance(item, VisualCaptureAttachment):
        return item
    if not isinstance(item, dict):
        return None
    payload = dict(item)
    payload.setdefault("attachment_id", f"attachment-{index}")
    payload.setdefault("filename", payload.get("relative_path", f"attachment-{index}"))
    payload.setdefault("relative_path", payload["filename"])
    payload.setdefault("mime_type", "application/octet-stream")
    payload.setdefault("sha256", "")
    payload.setdefault("size_bytes", 0)
    payload.setdefault("redaction_status", "not-scanned")
    return VisualCaptureAttachment(**payload)


def _resolve_capture_triplet(vault: Path, capture_path: str | Path) -> dict[str, Any]:
    raw = Path(capture_path)
    resolved = raw.resolve() if raw.is_absolute() else (vault / raw).resolve()
    if not _is_relative_to(resolved, vault):
        raise ValueError("capture path must stay inside the selected vault root")
    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"capture path does not exist or is not a file: {capture_path}")
    name = resolved.name
    if name.endswith(".visual_capture.json"):
        base = name[: -len(".visual_capture.json")]
        content_abs = resolved.with_name(f"{base}.md")
        sidecar_abs = resolved.with_name(f"{base}.meta.json")
        packet_abs = resolved
    elif name.endswith(".meta.json"):
        sidecar_abs = resolved
        sidecar = _load_json(sidecar_abs, "sidecar")
        content_name = str(sidecar.get("content_filename") or f"{name[:-len('.meta.json')]}.md")
        content_abs = sidecar_abs.with_name(content_name)
        base = content_abs.name[: -len(content_abs.suffix)] if content_abs.suffix else content_abs.name
        packet_abs = content_abs.with_name(f"{base}.visual_capture.json")
    elif resolved.suffix.lower() == ".md":
        content_abs = resolved
        sidecar_abs = resolved.with_suffix(".meta.json")
        packet_abs = resolved.with_suffix(".visual_capture.json")
    else:
        raise ValueError("capture path must be a .md, .meta.json, or .visual_capture.json file")
    for label, path in (("content", content_abs), ("sidecar", sidecar_abs)):
        if not path.exists() or not path.is_file():
            raise ValueError(f"{label} file missing for visual capture: {_rel(path, vault)}")
    return {
        "content_abs": content_abs,
        "sidecar_abs": sidecar_abs,
        "packet_abs": packet_abs,
        "content_rel": _rel(content_abs, vault),
        "sidecar_rel": _rel(sidecar_abs, vault),
        "packet_rel": _rel(packet_abs, vault),
    }


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"{label} JSON must be an object: {path}")
    return loaded


def _load_optional_json(path: Path, label: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _load_json(path, label)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _visual_capture_metadata(sidecar: dict[str, Any], packet: dict[str, Any] | None) -> dict[str, Any]:
    metadata = dict(((sidecar.get("extra_metadata") or {}).get("visual_capture") or {}))
    if packet:
        routing = packet.get("routing") or {}
        metadata.setdefault("capture_id", packet.get("capture_id"))
        metadata.setdefault("review_status", routing.get("review_status"))
        metadata.setdefault("visual_capture_packet_path", metadata.get("visual_capture_packet_path"))
        if "attachments" not in metadata and isinstance(packet.get("attachments"), list):
            metadata["attachments"] = list(packet.get("attachments") or [])
    return metadata


def _attachments_from_metadata(vc_meta: dict[str, Any]) -> list[dict[str, Any]]:
    attachments = vc_meta.get("attachments")
    return [dict(item) for item in attachments if isinstance(item, dict)] if isinstance(attachments, list) else []


def _apply_disposition_metadata(
    sidecar: dict[str, Any],
    vc_meta: dict[str, Any],
    policy: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    updated = dict(sidecar)
    extra = dict(updated.get("extra_metadata") or {})
    visual = dict(vc_meta)
    history = list(visual.get("attachment_disposition_history") or [])
    history.append(dict(decision))
    visual["attachment_disposition_policy"] = policy
    visual["attachment_disposition_history"] = history
    extra["visual_capture"] = visual
    updated["extra_metadata"] = extra
    return updated


def _apply_disposition_packet_metadata(
    packet: dict[str, Any],
    policy: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    updated = dict(packet)
    provenance = dict(updated.get("provenance") or {})
    chain = list(provenance.get("transformation_chain") or [])
    chain.append(
        {
            "step": "attachment_disposition_update",
            "method": ATTACHMENT_DISPOSITION_POLICY_ID,
            "at": decision["updated_at"],
            "requested_disposition": decision["requested_disposition"],
            "attachment_count": decision["attachment_count"],
        }
    )
    provenance["transformation_chain"] = chain
    updated["provenance"] = provenance
    updated["attachment_disposition_policy"] = policy
    return updated


def _cleanup_target(vault: Path, attachment: dict[str, Any]) -> tuple[dict[str, Any], Path] | None:
    relative = str(attachment.get("relative_path") or "").replace("\\", "/").strip()
    if not relative:
        return None
    if not relative.startswith("03_INPUTS/00_QUARANTINE/") or "/_attachments/" not in relative:
        return None
    target = (vault / relative).resolve()
    if not _is_relative_to(target, vault):
        return None
    return attachment, target


def _apply_cleanup_metadata(
    sidecar: dict[str, Any],
    vc_meta: dict[str, Any],
    cleanup_record: dict[str, Any],
) -> dict[str, Any]:
    updated = dict(sidecar)
    extra = dict(updated.get("extra_metadata") or {})
    visual = dict(vc_meta)
    history = list(visual.get("attachment_cleanup_history") or [])
    history.append(dict(cleanup_record))
    visual["attachment_cleanup_history"] = history
    visual["attachment_cleanup_status"] = (
        "deleted" if cleanup_record["deleted_count"] else "dry_run" if cleanup_record["dry_run"] else "no_files_deleted"
    )
    extra["visual_capture"] = visual
    updated["extra_metadata"] = extra
    return updated


def _apply_cleanup_packet_metadata(
    packet: dict[str, Any],
    cleanup_record: dict[str, Any],
) -> dict[str, Any]:
    updated = dict(packet)
    provenance = dict(updated.get("provenance") or {})
    chain = list(provenance.get("transformation_chain") or [])
    chain.append(
        {
            "step": "attachment_cleanup_executor",
            "method": ATTACHMENT_CLEANUP_POLICY_ID,
            "at": cleanup_record["cleaned_at"],
            "deleted_count": cleanup_record["deleted_count"],
            "dry_run": cleanup_record["dry_run"],
        }
    )
    provenance["transformation_chain"] = chain
    updated["provenance"] = provenance
    return updated


def _cleanup_denied(triplet: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "policy_id": ATTACHMENT_CLEANUP_POLICY_ID,
        "status": "attachment_cleanup_denied",
        "content_path": triplet["content_rel"],
        "sidecar_path": triplet["sidecar_rel"],
        "visual_capture_packet_path": triplet["packet_rel"] if triplet["packet_abs"].exists() else "",
        "blockers": [reason],
        "write_performed": False,
        "deleted_count": 0,
        "authority": {
            "operator_confirmed": False,
            "quarantine_local_attachment_delete_allowed": False,
            "content_write_allowed": False,
            "canonical_mutation_allowed": False,
            "provider_call_allowed": False,
            "external_send_allowed": False,
        },
    }


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _rel(path: Path, vault: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _forbidden_effects() -> list[str]:
    return [
        "ambient_attachment_delete",
        "external_attachment_cleanup",
        "content_rewrite",
        "canonical_promotion",
        "source_package_write",
        "sic_ingestion",
        "aor_dispatch",
        "graph_index_mutation",
        "provider_call",
        "external_send",
    ]
