"""Operator review-state writer for VCMI raw quarantine artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
from typing import Any

from .attachment_disposition import build_attachment_disposition_policy
from .attachments import build_screenshot_attachment_review_policy
from .models import VisualCaptureAttachment, utc_now
from .redaction import scan_secret_like_text


OPERATOR_REVIEW_STATE_POLICY_ID = "vcmi.operator_review_state.v1"
QUARANTINE_PREFIX = "03_INPUTS/00_QUARANTINE/"
JSON_REPLACE_RETRY_DELAYS_SECONDS = (0.01, 0.05, 0.1, 0.2)

PENDING_REVIEW = "pending-review"
REVIEWED = "reviewed"
REJECTED = "rejected"
NEEDS_REDACTION = "needs-redaction"

REVIEW_STATUSES = frozenset(
    {
        PENDING_REVIEW,
        REVIEWED,
        REJECTED,
        NEEDS_REDACTION,
    }
)

REVIEW_DECISION_ALIASES = {
    PENDING_REVIEW: PENDING_REVIEW,
    "pending_review": PENDING_REVIEW,
    "reopen": PENDING_REVIEW,
    "reviewed": REVIEWED,
    "approve": REVIEWED,
    "approved": REVIEWED,
    "operator-reviewed": REVIEWED,
    "trusted": REVIEWED,
    "rejected": REJECTED,
    "reject": REJECTED,
    "needs-redaction": NEEDS_REDACTION,
    "needs_redaction": NEEDS_REDACTION,
    "redaction-required": NEEDS_REDACTION,
    "redact": NEEDS_REDACTION,
}

ALLOWED_REVIEW_TRANSITIONS = {
    PENDING_REVIEW: frozenset({PENDING_REVIEW, REVIEWED, REJECTED, NEEDS_REDACTION}),
    NEEDS_REDACTION: frozenset({NEEDS_REDACTION, PENDING_REVIEW, REJECTED}),
    REVIEWED: frozenset({REVIEWED, PENDING_REVIEW}),
    REJECTED: frozenset({REJECTED, PENDING_REVIEW}),
}

REVIEW_STATE_AUTHORITY = {
    "raw_quarantine_sidecar_write": True,
    "visual_capture_packet_json_write": True,
    "content_write_allowed": False,
    "canonical_mutation_allowed": False,
    "graph_index_mutation_allowed": False,
    "provider_call_allowed": False,
    "external_send_allowed": False,
    "aor_queue_allowed": False,
    "sic_ingestion_allowed": False,
    "source_package_write_allowed": False,
    "attachment_delete_allowed": False,
    "screen_pixel_capture_allowed": False,
    "ocr_allowed": False,
}


class VisualCaptureReviewStateError(ValueError):
    """Raised when VCMI review-state mutation must fail closed."""


def build_operator_review_state_policy() -> dict[str, Any]:
    """Return the governed review-state transition contract."""

    return {
        "policy_id": OPERATOR_REVIEW_STATE_POLICY_ID,
        "status": "implemented",
        "artifact_scope": "vcmi_raw_quarantine_sidecar_and_packet_only",
        "accepted_artifact_paths": [
            "03_INPUTS/00_QUARANTINE/**/*.md",
            "03_INPUTS/00_QUARANTINE/**/*.meta.json",
            "03_INPUTS/00_QUARANTINE/**/*.visual_capture.json",
        ],
        "statuses": sorted(REVIEW_STATUSES),
        "decision_aliases": dict(REVIEW_DECISION_ALIASES),
        "allowed_transitions": {
            status: sorted(targets)
            for status, targets in ALLOWED_REVIEW_TRANSITIONS.items()
        },
        "authority": dict(REVIEW_STATE_AUTHORITY),
        "forbidden_effects": [
            "content_rewrite",
            "canonical_promotion",
            "source_package_write",
            "sic_ingestion",
            "aor_dispatch",
            "graph_index_mutation",
            "provider_call",
            "external_send",
            "attachment_cleanup_or_delete",
        ],
    }


def review_visual_capture_artifact(
    vault_root: str | Path,
    capture_path: str | Path,
    *,
    decision: str,
    reviewed_by: str = "operator",
    review_note: str = "",
    allow_secret_redaction: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update one VCMI quarantine artifact review state.

    This writes only the Phase 8 sidecar and adjacent VCMI packet JSON when the
    packet exists. It never rewrites the Markdown content, promotes canonical
    knowledge, dispatches AOR, or runs SIC.
    """

    vault = Path(vault_root).resolve()
    triplet = _resolve_capture_triplet(vault, capture_path)
    sidecar = _load_json(triplet["sidecar_abs"], "sidecar")
    packet = _load_optional_json(triplet["packet_abs"], "visual capture packet")
    vc_meta = _visual_capture_metadata(sidecar, packet)
    _validate_review_target(triplet, sidecar, vc_meta, packet)

    new_status = _normalize_decision(decision)
    current_status = _current_review_status(sidecar, vc_meta, packet)
    _validate_transition(current_status, new_status)

    safe_reviewed_by, reviewed_by_scan = _sanitize_review_text(
        "reviewed_by",
        reviewed_by or "operator",
        allow_secret_redaction=allow_secret_redaction,
    )
    safe_note, note_scan = _sanitize_review_text(
        "review_note",
        review_note or "",
        allow_secret_redaction=allow_secret_redaction,
    )
    reviewed_at = utc_now()
    decision_record = _decision_record(
        triplet,
        decision=str(decision or "").strip(),
        old_status=current_status,
        new_status=new_status,
        reviewed_by=safe_reviewed_by or "operator",
        reviewed_at=reviewed_at,
        review_note=safe_note,
        redaction_reports=[reviewed_by_scan, note_scan],
    )

    updated_sidecar = _update_sidecar(
        sidecar,
        vc_meta=vc_meta,
        decision_record=decision_record,
        new_status=new_status,
    )
    updated_packet = (
        _update_packet(packet, triplet=triplet, decision_record=decision_record, new_status=new_status)
        if packet is not None
        else None
    )

    if not dry_run:
        _write_json(triplet["sidecar_abs"], updated_sidecar)
        if updated_packet is not None:
            _write_json(triplet["packet_abs"], updated_packet)

    return {
        "ok": True,
        "surface": "capture-to-markdown",
        "action": "review",
        "status": "review_state_updated" if not dry_run else "review_state_dry_run",
        "policy_id": OPERATOR_REVIEW_STATE_POLICY_ID,
        "dry_run": bool(dry_run),
        "write_performed": not dry_run,
        "writes_performed": not dry_run,
        "content_write_performed": False,
        "sidecar_write_performed": not dry_run,
        "visual_capture_packet_json_write_performed": bool(updated_packet is not None and not dry_run),
        "old_status": current_status,
        "new_status": new_status,
        "decision": str(decision or "").strip(),
        "decision_id": decision_record["decision_id"],
        "reviewed_at": reviewed_at,
        "reviewed_by": decision_record["reviewed_by"],
        "review_note_redaction_status": decision_record["review_note_redaction_status"],
        "paths": {
            "content_path": triplet["content_rel"],
            "sidecar_path": triplet["sidecar_rel"],
            "visual_capture_packet_path": triplet["packet_rel"] if triplet["packet_abs"].exists() else "",
        },
        "capture": {
            "capture_id": vc_meta.get("capture_id") or sidecar.get("capture_id"),
            "title": vc_meta.get("title") or sidecar.get("title") or triplet["content_abs"].stem,
            "canonical_status": vc_meta.get("canonical_status", "not_promoted"),
            "source_package_status": sidecar.get("source_package_status"),
            "requires_review": _requires_review(new_status),
        },
        "blockers": [],
        "authority": dict(REVIEW_STATE_AUTHORITY),
        "blocked_downstream_actions": [
            "content_rewrite",
            "source_package_write",
            "aor_dispatch",
            "sic_ingestion",
            "canonical_knowledge_promotion",
            "graph_index_mutation",
            "provider_model_call",
            "external_delivery",
            "attachment_cleanup_or_delete",
        ],
        "policy": build_operator_review_state_policy(),
    }


def _resolve_capture_triplet(vault: Path, capture_path: str | Path) -> dict[str, Any]:
    raw = Path(capture_path)
    resolved = raw.resolve() if raw.is_absolute() else (vault / raw).resolve()
    if not _is_relative_to(resolved, vault):
        raise VisualCaptureReviewStateError("capture path must stay inside the selected vault root")
    if not resolved.exists() or not resolved.is_file():
        raise VisualCaptureReviewStateError(f"capture path does not exist or is not a file: {capture_path}")

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
        raise VisualCaptureReviewStateError(
            "capture path must be a VCMI .md, .meta.json, or .visual_capture.json file"
        )

    for label, path in (("content", content_abs), ("sidecar", sidecar_abs)):
        if not path.exists() or not path.is_file():
            raise VisualCaptureReviewStateError(f"{label} file missing for visual capture: {_rel(path, vault)}")

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
        raise VisualCaptureReviewStateError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(loaded, dict):
        raise VisualCaptureReviewStateError(f"{label} JSON must be an object: {path}")
    return loaded


def _load_optional_json(path: Path, label: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _load_json(path, label)


def _visual_capture_metadata(sidecar: dict[str, Any], packet: dict[str, Any] | None) -> dict[str, Any]:
    metadata = dict(((sidecar.get("extra_metadata") or {}).get("visual_capture") or {}))
    if packet:
        routing = packet.get("routing") or {}
        metadata.setdefault("capture_id", packet.get("capture_id"))
        metadata.setdefault("schema_version", packet.get("schema_version"))
        metadata.setdefault("title", packet.get("title"))
        metadata.setdefault("profile", packet.get("capture_profile"))
        metadata.setdefault("method", packet.get("capture_method"))
        metadata.setdefault("captured_at", packet.get("captured_at"))
        metadata.setdefault("canonical_status", routing.get("canonical_status"))
        metadata.setdefault("review_status", routing.get("review_status"))
        metadata.setdefault("source_package_status", routing.get("source_package_status"))
        metadata.setdefault("aor_queue_status", routing.get("aor_queue_status"))
    return metadata


def _validate_review_target(
    triplet: dict[str, Any],
    sidecar: dict[str, Any],
    vc_meta: dict[str, Any],
    packet: dict[str, Any] | None,
) -> None:
    if not triplet["content_rel"].startswith(QUARANTINE_PREFIX):
        raise VisualCaptureReviewStateError(
            "visual capture review state only accepts files under 03_INPUTS/00_QUARANTINE/"
        )
    if sidecar.get("promotion_status") != "quarantine":
        raise VisualCaptureReviewStateError("capture sidecar must remain promotion_status=quarantine")
    if sidecar.get("source_package_status") not in {"not-ingested", "reviewed-preview", None}:
        raise VisualCaptureReviewStateError("capture must not already be marked as SIC-ingested")
    if not vc_meta or vc_meta.get("schema_version") != "vcmi.v0.1":
        raise VisualCaptureReviewStateError("capture sidecar does not contain VCMI metadata")
    if vc_meta.get("canonical_status", "not_promoted") != "not_promoted":
        raise VisualCaptureReviewStateError("visual capture must not already be canonically promoted")
    if packet:
        routing = packet.get("routing") or {}
        if routing.get("canonical_status", "not_promoted") != "not_promoted":
            raise VisualCaptureReviewStateError("visual capture packet must not already be canonically promoted")
        if routing.get("source_package_status") not in {"not-ingested", "reviewed-preview", None}:
            raise VisualCaptureReviewStateError("visual capture packet must not already be marked as SIC-ingested")


def _normalize_decision(value: str) -> str:
    key = str(value or "").strip().lower()
    status = REVIEW_DECISION_ALIASES.get(key)
    if not status:
        raise VisualCaptureReviewStateError(
            f"unknown review decision '{value}'. Valid decisions: {sorted(REVIEW_DECISION_ALIASES)}"
        )
    return status


def _normalize_existing_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    return REVIEW_DECISION_ALIASES.get(text, text)


def _current_review_status(
    sidecar: dict[str, Any],
    vc_meta: dict[str, Any],
    packet: dict[str, Any] | None,
) -> str:
    sidecar_status = _normalize_existing_status(
        sidecar.get("quarantine_status") or sidecar.get("review_status")
    )
    visual_status = _normalize_existing_status(vc_meta.get("review_status"))
    if sidecar_status and visual_status and sidecar_status != visual_status:
        raise VisualCaptureReviewStateError(
            f"sidecar quarantine_status and VCMI review_status disagree: {sidecar_status} != {visual_status}"
        )

    packet_status = ""
    if packet:
        packet_status = _normalize_existing_status(((packet.get("routing") or {}).get("review_status")))

    current = visual_status or sidecar_status or packet_status or PENDING_REVIEW
    if current not in REVIEW_STATUSES:
        raise VisualCaptureReviewStateError(f"unsupported current review status: {current}")
    return current


def _validate_transition(old_status: str, new_status: str) -> None:
    allowed = ALLOWED_REVIEW_TRANSITIONS.get(old_status, frozenset())
    if new_status not in allowed:
        raise VisualCaptureReviewStateError(
            f"illegal VCMI review transition: {old_status} -> {new_status}. "
            f"Allowed targets: {sorted(allowed)}"
        )


def _sanitize_review_text(
    label: str,
    value: str,
    *,
    allow_secret_redaction: bool,
):
    report = scan_secret_like_text(value)
    if report.redaction_count and not allow_secret_redaction:
        raise VisualCaptureReviewStateError(f"{label} contains secret-like material")
    return report.redacted_text, report


def _decision_record(
    triplet: dict[str, Any],
    *,
    decision: str,
    old_status: str,
    new_status: str,
    reviewed_by: str,
    reviewed_at: str,
    review_note: str,
    redaction_reports: list[Any],
) -> dict[str, Any]:
    redaction_count = sum(int(report.redaction_count) for report in redaction_reports)
    categories: list[str] = []
    for report in redaction_reports:
        categories.extend(report.indicator_categories)
    category_list = list(dict.fromkeys(categories))
    decision_id = _decision_id(
        triplet["sidecar_rel"],
        reviewed_at,
        reviewed_by,
        old_status,
        new_status,
        review_note,
    )
    return {
        "policy_id": OPERATOR_REVIEW_STATE_POLICY_ID,
        "decision_id": decision_id,
        "decision": decision or new_status,
        "old_status": old_status,
        "new_status": new_status,
        "reviewed_by": reviewed_by or "operator",
        "reviewed_at": reviewed_at,
        "review_note": review_note,
        "review_note_redaction_status": "redacted" if redaction_count else "not_needed",
        "secret_redaction_count": redaction_count,
        "secret_redaction_categories": category_list,
        "content_path": triplet["content_rel"],
        "sidecar_path": triplet["sidecar_rel"],
        "visual_capture_packet_path": triplet["packet_rel"] if triplet["packet_abs"].exists() else "",
        "content_sha256": _sha256_file(triplet["content_abs"]),
        "requires_review": _requires_review(new_status),
        "write_scope": {
            "sidecar": True,
            "visual_capture_packet_json": triplet["packet_abs"].exists(),
            "content": False,
            "canonical": False,
            "source_package": False,
            "aor": False,
            "sic": False,
        },
        "authority": dict(REVIEW_STATE_AUTHORITY),
    }


def _update_sidecar(
    sidecar: dict[str, Any],
    *,
    vc_meta: dict[str, Any],
    decision_record: dict[str, Any],
    new_status: str,
) -> dict[str, Any]:
    updated = dict(sidecar)
    updated["quarantine_status"] = new_status
    updated["review_status"] = new_status
    updated["reviewed_by"] = decision_record["reviewed_by"]
    updated["reviewed_at"] = decision_record["reviewed_at"]
    updated["operator_review_state"] = dict(decision_record)
    updated["review_history"] = _append_history(updated.get("review_history"), decision_record)
    updated.setdefault("promotion_status", "quarantine")
    updated.setdefault("source_package_status", "not-ingested")

    extra = dict(updated.get("extra_metadata") or {})
    updated_meta = dict(vc_meta)
    updated_meta["review_status"] = new_status
    updated_meta["requires_review"] = _requires_review(new_status)
    updated_meta["reviewed_by"] = decision_record["reviewed_by"]
    updated_meta["reviewed_at"] = decision_record["reviewed_at"]
    updated_meta["operator_review_state"] = dict(decision_record)
    updated_meta["review_history"] = _append_history(updated_meta.get("review_history"), decision_record)
    updated_meta["attachment_review_policy"] = build_screenshot_attachment_review_policy(
        _attachments_from_metadata(updated_meta),
        review_status=new_status,
        ocr_status=(
            (updated_meta.get("local_optical_character_recognition") or {}).get("status")
            if isinstance(updated_meta.get("local_optical_character_recognition"), dict)
            else "not_performed"
        ),
        cloud_ocr_allowed=False,
    )
    updated_meta["attachment_disposition_policy"] = build_attachment_disposition_policy(
        _attachments_from_metadata(updated_meta),
        review_status=new_status,
    )
    extra["visual_capture"] = updated_meta
    updated["extra_metadata"] = extra
    return updated


def _update_packet(
    packet: dict[str, Any] | None,
    *,
    triplet: dict[str, Any],
    decision_record: dict[str, Any],
    new_status: str,
) -> dict[str, Any] | None:
    if packet is None:
        return None
    updated = dict(packet)
    routing = dict(updated.get("routing") or {})
    routing["review_status"] = new_status
    routing["requires_review"] = _requires_review(new_status)
    routing.setdefault("canonical_status", "not_promoted")
    routing.setdefault("source_package_status", "not-ingested")
    routing.setdefault("aor_queue_status", "not_queued")
    routing.setdefault("raw_ingestion_path", triplet["content_rel"])
    routing.setdefault("sidecar_path", triplet["sidecar_rel"])
    routing.setdefault("visual_capture_packet_path", triplet["packet_rel"])
    routing["operator_review_state"] = dict(decision_record)
    updated["routing"] = routing

    provenance = dict(updated.get("provenance") or {})
    chain = list(provenance.get("transformation_chain") or [])
    chain.append(
        {
            "step": "operator_review_state_update",
            "method": OPERATOR_REVIEW_STATE_POLICY_ID,
            "at": decision_record["reviewed_at"],
            "status": new_status,
            "decision_id": decision_record["decision_id"],
            "reviewed_by": decision_record["reviewed_by"],
            "input_ref": triplet["sidecar_rel"],
            "output_ref": triplet["sidecar_rel"],
            "write_scope": dict(decision_record["write_scope"]),
        }
    )
    provenance["transformation_chain"] = chain
    updated["provenance"] = provenance
    return updated


def _attachments_from_metadata(vc_meta: dict[str, Any]) -> list[VisualCaptureAttachment]:
    attachments: list[VisualCaptureAttachment] = []
    for index, raw in enumerate(vc_meta.get("attachments") or [], start=1):
        if not isinstance(raw, dict):
            continue
        attachments.append(
            VisualCaptureAttachment(
                attachment_id=str(raw.get("attachment_id") or f"attachment-{index}"),
                filename=str(raw.get("filename") or raw.get("relative_path") or f"attachment-{index}"),
                relative_path=str(raw.get("relative_path") or raw.get("filename") or f"attachment-{index}"),
                mime_type=str(raw.get("mime_type") or "application/octet-stream"),
                sha256=str(raw.get("sha256") or ""),
                size_bytes=int(raw.get("size_bytes") or 0),
                redaction_status=str(raw.get("redaction_status") or "not-scanned"),
            )
        )
    return attachments


def _append_history(value: Any, decision_record: dict[str, Any]) -> list[dict[str, Any]]:
    history = value if isinstance(value, list) else []
    rows = [dict(row) for row in history if isinstance(row, dict)]
    rows.append(dict(decision_record))
    return rows


def _requires_review(status: str) -> bool:
    return status in {PENDING_REVIEW, NEEDS_REDACTION}


def _decision_id(*parts: str) -> str:
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"vcmi-review-{digest}"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temp = path.with_name(f"{path.name}.tmp")
    temp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    last_error: PermissionError | None = None
    for delay in (0.0, *JSON_REPLACE_RETRY_DELAYS_SECONDS):
        if delay:
            time.sleep(delay)
        try:
            temp.replace(path)
            return
        except PermissionError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _rel(path: Path, vault: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError as exc:
        raise VisualCaptureReviewStateError(f"path escapes vault root: {path}") from exc
