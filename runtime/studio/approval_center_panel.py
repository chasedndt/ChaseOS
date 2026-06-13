"""Read-only native Studio Approval Center panel contract.

This surface aggregates approval posture from existing ChaseOS lanes for Studio
display only. It does not record decisions, consume approvals, resume runtimes,
dispatch workflows, call providers/connectors, or mutate canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Any, Callable, TypeVar


MODEL_VERSION = "studio.approval_center_panel.v1"
SURFACE_ID = "studio_approval_center_panel"
FORGE_DECISION_SURFACE_ID = "chaser_forge_approval_center_decision_handoff"
FORGE_DECISION_API_METHOD = "review_chaser_forge_approval_decision"
FORGE_DECISION_FORM_SURFACE_ID = "chaser_forge_operator_decision_form"
FORGE_DECISION_FORM_API_METHOD = "get_chaser_forge_approval_decision_form"
T = TypeVar("T")


def _run_bounded(label: str, timeout_seconds: float, fn: Callable[[], T], fallback: T, warnings: list[str]) -> T:
    """Run source collectors with a small fail-open budget for Studio panels."""

    if timeout_seconds <= 0:
        warnings.append(f"source_timeout:{label}")
        return fallback

    queue: Queue[tuple[bool, T | BaseException]] = Queue(maxsize=1)

    def _target() -> None:
        try:
            queue.put((True, fn()))
        except BaseException as exc:  # noqa: BLE001
            queue.put((False, exc))

    thread = Thread(target=_target, name=f"approval-center-{label}", daemon=True)
    thread.start()
    try:
        ok, value = queue.get(timeout=max(0.001, timeout_seconds))
    except Empty:
        warnings.append(f"source_timeout:{label}")
        return fallback
    if ok:
        return value  # type: ignore[return-value]
    warnings.append(f"{label}_unavailable:{value}")
    return fallback


def _timeout_group(group_id: str, label: str) -> dict[str, Any]:
    return {
        "id": group_id,
        "label": label,
        "status": "source_timeout",
        "item_count": 0,
        "pending_count": 0,
        "ready_count": 0,
        "blocked_count": 0,
        "artifact_count": 0,
        "source_refs": [],
        "latest_items": [],
        "truncated": True,
    }

FORBIDDEN_AUTHORITY = {
    "writes_vault": False,
    "writes_approval_artifacts": False,
    "writes_review_decisions": False,
    "grants_approvals": False,
    "executes_approvals": False,
    "consumes_approval_decisions": False,
    "applies_candidates": False,
    "resumes_runtimes": False,
    "writes_agent_bus_tasks": False,
    "dispatches_runtimes": False,
    "executes_workflows": False,
    "activates_schedules": False,
    "provider_calls_allowed": False,
    "connector_calls_allowed": False,
    "memory_approval_allowed": False,
    "canonical_mutation_allowed": False,
    "shows_secrets": False,
    "shows_raw_credentials": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.relative_to(vault).as_posix()
    except ValueError:
        try:
            return path.resolve().relative_to(vault).as_posix()
        except ValueError:
            return str(path)


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _sample_files(vault: Path, root: Path, pattern: str, limit: int = 5, scan_limit: int = 200) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    files: list[Path] = []
    try:
        for index, path in enumerate(root.glob(pattern)):
            if index >= scan_limit:
                break
            if path.is_file():
                files.append(path)
    except OSError:
        return []
    files = sorted(files, key=lambda item: item.stat().st_mtime, reverse=True)
    return [
        {
            "path": _rel(vault, path),
            "name": path.name,
            "modified_at_epoch": path.stat().st_mtime,
        }
        for path in files[:limit]
    ]


def _pulse_group(vault: Path) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    try:
        from runtime.pulse.approval_center import build_pulse_approval_center_readiness

        surface = build_pulse_approval_center_readiness(vault).to_dict()
    except Exception as exc:  # noqa: BLE001
        surface = {}
        warnings.append(f"pulse_approval_center_unavailable:{exc}")

    queue_root = vault / "07_LOGS" / "Pulse-Decks" / "approval-queue"
    queue_files = _sample_files(vault, queue_root, "*.json")
    lanes = surface.get("lanes") or []
    pending_count = sum(int(item.get("pending_count") or 0) for item in lanes)
    ready_count = sum(int(item.get("ready_count") or 0) for item in lanes)
    blocked_count = sum(int(item.get("blocked_count") or 0) for item in lanes)
    return (
        {
            "id": "pulse",
            "label": "Pulse Candidates + Approval Queue",
            "status": surface.get("approval_center_status") or "not_configured",
            "item_count": int(surface.get("candidate_item_count") or 0)
            + int(surface.get("approval_request_count") or 0)
            + len(queue_files),
            "pending_count": pending_count,
            "ready_count": ready_count,
            "blocked_count": blocked_count,
            "artifact_count": len(queue_files),
            "source_refs": list(surface.get("source_refs") or [])[:8],
            "latest_items": [
                {
                    "title": item.get("label") or item.get("lane_id"),
                    "status": item.get("status") or "read_only",
                    "detail": f"items={item.get('item_count', 0)} pending={item.get('pending_count', 0)} blocked={item.get('blocked_count', 0)}",
                }
                for item in lanes[:8]
            ],
        },
        warnings,
    )


def _studio_service_group(vault: Path, scan_limit: int = 24) -> dict[str, Any]:
    root = vault / "runtime" / "studio" / "approvals"
    items: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    duplicate_count = 0
    seen_approval_ids: set[str] = set()
    duplicated_approval_ids: set[str] = set()
    truncated = False
    if root.exists():
        for index, path in enumerate(root.glob("*.json")):
            if index >= scan_limit:
                truncated = True
                break
            payload = _safe_read_json(path)
            if payload is None:
                payload = {}
                status = "invalid_packet"
            else:
                spec_present = isinstance(payload.get("action_spec"), dict)
                required_present = bool(payload.get("approval_id")) and bool(payload.get("status")) and spec_present
                status = str(payload.get("status") or "unknown") if required_present else "partial_packet"
            approval_id = str(payload.get("approval_id") or path.stem)
            if approval_id in seen_approval_ids:
                duplicate_count += 1
                duplicated_approval_ids.add(approval_id)
            seen_approval_ids.add(approval_id)
            counts[status] = counts.get(status, 0) + 1
            spec = payload.get("action_spec") if isinstance(payload.get("action_spec"), dict) else {}
            metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
            origin = metadata.get("source_contract") or metadata.get("source_surface") or spec.get("submitted_by") or "studio-service"
            requested_action = spec.get("action_type") or "action"
            requested_touch = spec.get("target_path") or spec.get("target_ref") or "(target hidden)"
            affected_files_systems = []
            if requested_touch and requested_touch != "(target hidden)":
                affected_files_systems.append(
                    {
                        "kind": "target_path" if spec.get("target_path") else "target_ref",
                        "path_preview": requested_touch,
                    }
                )
            for affected in spec.get("affected_files_systems") or metadata.get("affected_files_systems") or []:
                if isinstance(affected, dict):
                    affected_files_systems.append(
                        {
                            "kind": affected.get("kind") or affected.get("system") or "affected",
                            "path_preview": affected.get("path_preview") or affected.get("path") or affected.get("system") or affected.get("name"),
                        }
                    )
            request_reason = metadata.get("request_reason") or metadata.get("why") or metadata.get("reason") or "not_provided"
            safety_summary = metadata.get("safety_summary") or metadata.get("boundary_summary") or "not_provided"
            if len(items) < 8:
                items.append(
                    {
                        "title": approval_id,
                        "status": status,
                        "detail": f"{origin}: {requested_action} -> {requested_touch}",
                        "source_ref": _rel(vault, path),
                        "request_digest_sha256": payload.get("request_digest_sha256"),
                        "source_digest": payload.get("request_digest_sha256") or payload.get("source_digest") or "missing",
                        "requested_action": requested_action,
                        "requested_touch": requested_touch,
                        "affected_files_systems": [item for item in affected_files_systems if item.get("path_preview")],
                        "request_reason": request_reason,
                        "safety_summary": safety_summary,
                        "duplicate": approval_id in duplicated_approval_ids,
                        "duplicate_protection_hint": "duplicate approval id detected; operator must inspect source digest before any governed consumption" if approval_id in duplicated_approval_ids else "source digest displayed for duplicate protection",
                    }
                )
    for item in items:
        if item["title"] in duplicated_approval_ids:
            item["duplicate"] = True
            item["duplicate_protection_hint"] = "duplicate approval id detected; operator must inspect source digest before any governed consumption"
    total = sum(counts.values())
    blocked_count = int(counts.get("rejected") or 0) + int(counts.get("invalid_packet") or 0) + int(counts.get("partial_packet") or 0) + duplicate_count
    return {
        "id": "studio-service",
        "label": "Studio Service Approval Queue",
        "status": "pending_operator_review" if counts.get("pending") else "no_pending_items",
        "item_count": total,
        "pending_count": int(counts.get("pending") or 0),
        "ready_count": int(counts.get("approved") or 0),
        "blocked_count": blocked_count,
        "artifact_count": total,
        "status_counts": counts,
        "duplicate_count": duplicate_count,
        "source_refs": [_rel(vault, root)] if root.exists() else [],
        "latest_items": items,
        "scan_limit": scan_limit,
        "truncated": truncated,
    }


def _osril_group(vault: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    warnings: list[str] = []
    try:
        from runtime.osril.approvals import get_approval_state

        state = get_approval_state(vault, limit=12)
    except Exception as exc:  # noqa: BLE001
        state = {"pending_count": 0, "responses_count": 0, "pending": [], "responses": []}
        warnings.append(f"osril_approval_state_unavailable:{exc}")

    responses = state.get("responses") or []
    resume_count = sum(1 for item in responses if item.get("resume_executed"))
    pending = state.get("pending") or []
    osril_group = {
        "id": "osril",
        "label": "OSRIL Approval Gates",
        "status": "pending_operator_review" if state.get("pending_count") else "no_pending_items",
        "item_count": int(state.get("pending_count") or 0) + int(state.get("responses_count") or 0),
        "pending_count": int(state.get("pending_count") or 0),
        "ready_count": int(state.get("responses_count") or 0),
        "blocked_count": 0,
        "artifact_count": int(state.get("responses_count") or 0),
        "source_refs": ["runtime/osril/run", "runtime/osril/approvals"],
        "latest_items": [
            {
                "title": item.get("approval_id") or item.get("event_id") or "approval",
                "status": "pending",
                "detail": f"{item.get('runtime_id') or 'runtime'} / {item.get('workflow_id') or 'workflow'}",
            }
            for item in pending[:8]
        ],
    }
    resume_group = {
        "id": "runtime-resumes",
        "label": "Runtime Resume Evidence",
        "status": "resume_evidence_present" if resume_count else "no_resume_evidence",
        "item_count": int(state.get("responses_count") or 0),
        "pending_count": max(0, int(state.get("responses_count") or 0) - resume_count),
        "ready_count": resume_count,
        "blocked_count": 0,
        "artifact_count": resume_count,
        "source_refs": ["runtime/osril/approvals/*.resume.json"],
        "latest_items": [
            {
                "title": item.get("approval_id") or "approval",
                "status": "resumed" if item.get("resume_executed") else "response_recorded",
                "detail": f"{item.get('decision') or 'decision'} / {item.get('workflow_id') or 'workflow'}",
            }
            for item in responses[:8]
        ],
    }
    return osril_group, resume_group, warnings


def _siteops_group(vault: Path) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    try:
        from runtime.siteops.approvals import list_approval_requests

        approvals = list_approval_requests(vault, tenant_id="local")
    except Exception as exc:  # noqa: BLE001
        approvals = []
        warnings.append(f"siteops_approval_state_unavailable:{exc}")

    pending = [item for item in approvals if item.get("status") == "pending"]
    approved = [item for item in approvals if item.get("status") == "approved"]
    rejected = [item for item in approvals if item.get("status") == "rejected"]
    return (
        {
            "id": "siteops",
            "label": "SiteOps Approvals",
            "status": "pending_operator_review" if pending else "no_pending_items",
            "item_count": len(approvals),
            "pending_count": len(pending),
            "ready_count": len(approved),
            "blocked_count": len(rejected),
            "artifact_count": len(approvals),
            "source_refs": ["07_LOGS/SiteOps-Approvals"],
            "latest_items": [
                {
                    "title": item.get("approval_id") or "siteops approval",
                    "status": item.get("status") or "unknown",
                    "detail": f"{item.get('workflow_id') or 'workflow'} / {item.get('action') or 'action'}",
                    "source_ref": _rel(vault, Path(item["approval_ref"])) if item.get("approval_ref") else None,
                }
                for item in approvals[:8]
            ],
        },
        warnings,
    )


def _startup_controls_group(vault: Path) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    try:
        from runtime.studio.runtime_startup_controls import build_runtime_startup_controls_model

        startup = build_runtime_startup_controls_model(vault)
    except Exception as exc:  # noqa: BLE001
        startup = {}
        warnings.append(f"startup_controls_state_unavailable:{exc}")

    cards = startup.get("surface_cards") or []
    approval_boundary = startup.get("approval_boundary") or {}
    return (
        {
            "id": "startup-controls",
            "label": "Runtime Startup Controls",
            "status": "confirmation_gated" if approval_boundary else "read_only_status",
            "item_count": len(cards),
            "pending_count": 0,
            "ready_count": len(cards),
            "blocked_count": 1 if approval_boundary.get("approval_required_before_confirmed_mutation") else 0,
            "artifact_count": 0,
            "source_refs": ["runtime.studio.runtime_startup_controls"],
            "latest_items": [
                {
                    "title": card.get("label") or card.get("runtime_id") or "runtime",
                    "status": card.get("current_state") or "unknown",
                    "detail": f"confirm_required={card.get('requires_confirm_action')} gate={approval_boundary.get('approval_required_before_confirmed_mutation')}",
                }
                for card in cards[:8]
            ],
        },
        warnings,
    )


def _workspace_upgrade_group(vault: Path) -> dict[str, Any]:
    root = vault / "07_LOGS" / "Agent-Activity" / "_workspace_upgrade_approvals"
    items: list[dict[str, Any]] = []
    pending = 0
    consumed = 0
    blocked = 0
    if root.exists():
        for path in sorted(root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            payload = _safe_read_json(path) or {}
            if payload.get("record_type") != "workspace_upgrade_approval_artifact":
                blocked += 1
                status = "invalid"
            elif payload.get("approval_decision_consumed") is True:
                consumed += 1
                status = "consumed"
            else:
                pending += 1
                status = "approved_pending_execution_proof"
            if len(items) < 8:
                material = payload.get("approved_material") if isinstance(payload.get("approved_material"), dict) else {}
                items.append(
                    {
                        "title": payload.get("approval_packet_id") or path.stem,
                        "status": status,
                        "detail": f"{material.get('workspace_name') or 'workspace'} / proof-temp-only",
                        "source_ref": _rel(vault, path),
                    }
                )
    total = pending + consumed + blocked
    return {
        "id": "workspace-upgrade",
        "label": "Workspace Upgrade Approvals",
        "status": "pending_execution_proof" if pending else "no_pending_items",
        "item_count": total,
        "pending_count": pending,
        "ready_count": consumed,
        "blocked_count": blocked,
        "artifact_count": total,
        "source_refs": [_rel(vault, root)] if root.exists() else [],
        "latest_items": items,
    }


def _forge_lifecycle_status(payload: dict[str, Any]) -> str:
    if payload.get("approval_consumed") is True or payload.get("status") == "consumed":
        return "consumed"
    if payload.get("operator_decision") == "approved" and payload.get("status") == "approved":
        return "approved_pending_execution"
    if payload.get("operator_decision") == "rejected" or payload.get("status") == "rejected":
        return "rejected"
    if payload.get("operator_decision") == "pending" and payload.get("status") == "pending_operator_decision":
        return "pending_operator_review"
    return str(payload.get("status") or "unknown")


def _forge_approval_item(
    *,
    vault: Path,
    path: Path,
    payload: dict[str, Any],
    family_id: str,
    label: str,
    expected_record_type: str,
    expected_scope: str,
) -> tuple[dict[str, Any], str]:
    status = "invalid_packet"
    if payload.get("record_type") == expected_record_type and payload.get("approval_scope") == expected_scope:
        status = _forge_lifecycle_status(payload)

    material = payload.get("approved_material") if isinstance(payload.get("approved_material"), dict) else {}
    target_paths = list(payload.get("future_extension_target_paths") or material.get("target_paths") or [])
    affected = [{"kind": "extension_target", "path_preview": item} for item in target_paths if item]
    if payload.get("future_registry_path"):
        affected.append({"kind": "forge_registry", "path_preview": payload.get("future_registry_path")})
    marker_path = (
        payload.get("future_exact_once_marker_path")
        or payload.get("future_live_exact_once_marker_path")
        or payload.get("future_rollback_exact_once_marker_path")
    )
    if marker_path:
        affected.append({"kind": "exact_once_marker", "path_preview": marker_path})

    action = material.get("requested_action") or expected_record_type
    extension_id = payload.get("extension_id") or material.get("extension_id") or "unknown-extension"
    safety = material.get("approval_effect") or "Forge approval artifact is visibility only until its source-specific executor validates an approved artifact."
    if status == "invalid_packet":
        safety = "Forge artifact failed record type or scope validation; do not consume."

    source_ref = _rel(vault, path)
    decision_handoff_available = status == "pending_operator_review"
    decision_handoff = {
        "available": decision_handoff_available,
        "surface": FORGE_DECISION_SURFACE_ID,
        "api_method": FORGE_DECISION_API_METHOD,
        "source_specific": True,
        "generic_approval_center_control": False,
        "approval_family": family_id,
        "approval_artifact_path": source_ref,
        "expected_request_digest_sha256": payload.get("request_digest_sha256") or "",
        "supported_decisions": ["approved", "rejected"],
        "operator_confirmation_text": payload.get("operator_confirmation_text") if decision_handoff_available else "",
        "approval_consumption_allowed": False,
        "forge_execution_allowed": False,
        "registry_write_allowed": False,
        "extension_file_write_allowed": False,
        "exact_once_marker_reservation_allowed": False,
        "write_requires": [
            "source-specific Studio API call",
            "matching request digest",
            "exact operator statement",
            "pending Forge approval artifact",
        ],
    }
    operator_decision_form = {
        "available": decision_handoff_available,
        "surface": FORGE_DECISION_FORM_SURFACE_ID,
        "api_method": FORGE_DECISION_FORM_API_METHOD,
        "submit_api_method": FORGE_DECISION_API_METHOD,
        "source_specific": True,
        "generic_approval_center_control": False,
        "approval_family": family_id,
        "approval_artifact_path": source_ref,
        "expected_request_digest_sha256": payload.get("request_digest_sha256") or "",
        "supported_decisions": ["approved", "rejected"],
        "copyable_statement_required": True,
        "prepares_submit_payload": True,
        "approval_consumption_allowed": False,
        "forge_execution_allowed": False,
        "registry_write_allowed": False,
        "extension_file_write_allowed": False,
        "exact_once_marker_reservation_allowed": False,
    }

    return (
        {
            "title": payload.get("approval_packet_id") or path.stem,
            "status": status,
            "detail": f"{label}: {action} -> {extension_id}",
            "source_ref": source_ref,
            "request_digest_sha256": payload.get("request_digest_sha256"),
            "source_digest": payload.get("request_digest_sha256") or "missing",
            "requested_action": action,
            "requested_touch": ", ".join(target_paths) or str(extension_id),
            "affected_files_systems": affected,
            "request_reason": payload.get("operator_confirmation_text") or "Forge operator approval request",
            "safety_summary": safety,
            "duplicate": False,
            "duplicate_protection_hint": "Forge request digest plus approval_packet_id must match before any source-specific executor can consume it",
            "decision_handoff": decision_handoff,
            "operator_decision_form": operator_decision_form,
        },
        status,
    )


def _forge_approvals_group(vault: Path, scan_limit: int = 64) -> dict[str, Any]:
    try:
        from runtime.forge.registry import (
            LIVE_INSTALL_APPROVAL_RECORD_TYPE,
            LIVE_INSTALL_APPROVAL_SCOPE,
            LIVE_INSTALL_APPROVAL_RELATIVE_DIR,
            ROLLBACK_APPROVAL_RECORD_TYPE,
            ROLLBACK_APPROVAL_RELATIVE_DIR,
            ROLLBACK_APPROVAL_SCOPE,
            SANDBOX_APPROVAL_RECORD_TYPE,
            SANDBOX_APPROVAL_RELATIVE_DIR,
            SANDBOX_APPROVAL_SCOPE,
        )
        from runtime.forge.marketplace import (
            FORGE_MARKETPLACE_IMPORT_APPROVAL_RECORD_TYPE,
            FORGE_MARKETPLACE_IMPORT_APPROVAL_RELATIVE_DIR,
            FORGE_MARKETPLACE_IMPORT_APPROVAL_SCOPE,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "id": "chaser-forge",
            "label": "Chaser Forge Approval Requests",
            "status": "source_unavailable",
            "item_count": 0,
            "pending_count": 0,
            "ready_count": 0,
            "blocked_count": 1,
            "artifact_count": 0,
            "status_counts": {"source_unavailable": 1},
            "source_refs": [],
            "latest_items": [
                {
                    "title": "forge-source-unavailable",
                    "status": "source_unavailable",
                    "detail": str(exc),
                }
            ],
        }

    families = [
        (
            "sandbox",
            "Forge Sandbox Approval",
            SANDBOX_APPROVAL_RELATIVE_DIR,
            SANDBOX_APPROVAL_RECORD_TYPE,
            SANDBOX_APPROVAL_SCOPE,
        ),
        (
            "live-install",
            "Forge Live Install Approval",
            LIVE_INSTALL_APPROVAL_RELATIVE_DIR,
            LIVE_INSTALL_APPROVAL_RECORD_TYPE,
            LIVE_INSTALL_APPROVAL_SCOPE,
        ),
        (
            "rollback",
            "Forge Rollback Approval",
            ROLLBACK_APPROVAL_RELATIVE_DIR,
            ROLLBACK_APPROVAL_RECORD_TYPE,
            ROLLBACK_APPROVAL_SCOPE,
        ),
        (
            "marketplace-import",
            "Forge Marketplace Import Sandbox Review",
            FORGE_MARKETPLACE_IMPORT_APPROVAL_RELATIVE_DIR,
            FORGE_MARKETPLACE_IMPORT_APPROVAL_RECORD_TYPE,
            FORGE_MARKETPLACE_IMPORT_APPROVAL_SCOPE,
        ),
    ]
    scanned: list[tuple[Path, str, str, str, str]] = []
    source_refs: list[str] = []
    for _family_id, label, relative_root, expected_record_type, expected_scope in families:
        root = vault / relative_root
        if root.exists():
            source_refs.append(_rel(vault, root))
        try:
            for path in root.glob("*.json"):
                if len(scanned) >= scan_limit:
                    break
                if path.is_file():
                    scanned.append((path, _family_id, label, expected_record_type, expected_scope))
        except OSError:
            continue

    scanned = sorted(scanned, key=lambda item: item[0].stat().st_mtime, reverse=True)
    status_counts: dict[str, int] = {}
    items: list[dict[str, Any]] = []
    for path, family_id, label, expected_record_type, expected_scope in scanned:
        payload = _safe_read_json(path)
        if payload is None:
            item = {
                "title": path.stem,
                "status": "invalid_packet",
                "detail": f"{label}: unreadable JSON",
                "source_ref": _rel(vault, path),
                "source_digest": "missing",
                "requested_action": "unknown",
                "requested_touch": "unknown",
                "affected_files_systems": [],
                "safety_summary": "Forge artifact is unreadable; do not consume.",
                "duplicate": False,
                "duplicate_protection_hint": "invalid packet; no digest available",
            }
            status = "invalid_packet"
        else:
            item, status = _forge_approval_item(
                vault=vault,
                path=path,
                payload=payload,
                family_id=family_id,
                label=label,
                expected_record_type=expected_record_type,
                expected_scope=expected_scope,
            )
        status_counts[status] = status_counts.get(status, 0) + 1
        if len(items) < 8:
            items.append(item)

    pending = int(status_counts.get("pending_operator_review") or 0)
    approved = int(status_counts.get("approved_pending_execution") or 0)
    consumed = int(status_counts.get("consumed") or 0)
    blocked = sum(
        count
        for status, count in status_counts.items()
        if status not in {"pending_operator_review", "approved_pending_execution", "consumed"}
    )
    total = sum(status_counts.values())
    return {
        "id": "chaser-forge",
        "label": "Chaser Forge Approval Requests",
        "status": "pending_operator_review" if pending else "approval_artifacts_visible" if total else "no_pending_items",
        "item_count": total,
        "pending_count": pending,
        "ready_count": approved + consumed,
        "blocked_count": blocked,
        "artifact_count": total,
        "status_counts": status_counts,
        "source_specific_decision_handoff_available": pending > 0,
        "decision_handoff_count": pending,
        "decision_handoff_api_method": FORGE_DECISION_API_METHOD,
        "operator_decision_form_available": pending > 0,
        "operator_decision_form_count": pending,
        "operator_decision_form_api_method": FORGE_DECISION_FORM_API_METHOD,
        "source_refs": source_refs,
        "latest_items": items,
        "scan_limit": scan_limit,
        "truncated": len(scanned) >= scan_limit,
    }


def _gate_requests_group(vault: Path) -> dict[str, Any]:
    operator_briefs = vault / "07_LOGS" / "Operator-Briefs"
    request_files = _sample_files(vault, operator_briefs, "*approval-request*.md")
    return {
        "id": "gate-requests",
        "label": "Gate / Runtime MCP Requests",
        "status": "review_artifacts_present" if request_files else "no_review_artifacts",
        "item_count": len(request_files),
        "pending_count": len(request_files),
        "ready_count": 0,
        "blocked_count": 0,
        "artifact_count": len(request_files),
        "source_refs": ["07_LOGS/Operator-Briefs"],
        "latest_items": [
            {
                "title": item["name"],
                "status": "pending_human_review",
                "detail": item["path"],
            }
            for item in request_files
        ],
    }


def build_approval_center_panel(vault_root: str | Path, *, source_timeout_seconds: float = 0.15) -> dict[str, Any]:
    """Build the read-only native Approval Center panel model."""

    vault = _vault_path(vault_root)
    warnings: list[str] = []
    pulse_group, pulse_warnings = _run_bounded(
        "pulse",
        source_timeout_seconds,
        lambda: _pulse_group(vault),
        (_timeout_group("pulse", "Pulse Candidates + Approval Queue"), []),
        warnings,
    )
    osril_group, resume_group, osril_warnings = _run_bounded(
        "osril",
        source_timeout_seconds,
        lambda: _osril_group(vault),
        (
            _timeout_group("osril", "OSRIL Approval Gates"),
            _timeout_group("runtime-resumes", "Runtime Resume Evidence"),
            [],
        ),
        warnings,
    )
    siteops_group, siteops_warnings = _run_bounded(
        "siteops",
        source_timeout_seconds,
        lambda: _siteops_group(vault),
        (_timeout_group("siteops", "SiteOps Approvals"), []),
        warnings,
    )
    startup_group, startup_warnings = _run_bounded(
        "startup-controls",
        source_timeout_seconds,
        lambda: _startup_controls_group(vault),
        (_timeout_group("startup-controls", "Runtime Startup Controls"), []),
        warnings,
    )
    groups = [
        pulse_group,
        _studio_service_group(vault),
        _forge_approvals_group(vault),
        _workspace_upgrade_group(vault),
        osril_group,
        _gate_requests_group(vault),
        resume_group,
        siteops_group,
        startup_group,
    ]
    warnings.extend(pulse_warnings)
    warnings.extend(osril_warnings)
    warnings.extend(siteops_warnings)
    warnings.extend(startup_warnings)

    total_items = sum(int(group.get("item_count") or 0) for group in groups)
    pending_items = sum(int(group.get("pending_count") or 0) for group in groups)
    blocked_items = sum(int(group.get("blocked_count") or 0) for group in groups)
    artifact_count = sum(int(group.get("artifact_count") or 0) for group in groups)
    source_specific_handoffs = sum(int(group.get("decision_handoff_count") or 0) for group in groups)
    operator_decision_forms = sum(int(group.get("operator_decision_form_count") or 0) for group in groups)
    status = "pending_operator_review" if pending_items else "read_only_no_pending_items"
    if warnings:
        status = "partial_with_source_warnings"

    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "native_panel": {
            "mounted": True,
            "panel_id": "approval-center",
            "frontend_target": "panel-approval-center",
            "route_hint": "#/approval-center",
            "read_only": True,
            "status": "mounted-read-only",
        },
        "summary": {
            "overall_status": status,
            "source_group_count": len(groups),
            "total_item_count": total_items,
            "pending_item_count": pending_items,
            "blocked_item_count": blocked_items,
            "artifact_count": artifact_count,
            "operator_decision_controls_present": False,
            "source_specific_decision_handoff_count": source_specific_handoffs,
            "operator_decision_form_count": operator_decision_forms,
            "approval_execution_available": False,
        },
        "source_groups": groups,
        "authority": {
            "read_only": True,
            "allowed_actions": ["inspect-approval-center-panel"],
            "possible_writes": [],
            **FORBIDDEN_AUTHORITY,
        },
        "queue_handoff": {
            "viewing_approvals": True,
            "consuming_or_executing_approvals": False,
            "queue_sources_visible": True,
            "operator_decision_controls_present": False,
            "source_specific_handoffs_present": source_specific_handoffs > 0,
            "chaser_forge_decision_handoff_api_method": FORGE_DECISION_API_METHOD,
            "chaser_forge_operator_decision_form_api_method": FORGE_DECISION_FORM_API_METHOD,
            "source_specific_operator_forms_present": operator_decision_forms > 0,
            "backend_approval_consumption_present": False,
            "handoff_status": "phase9_dependency_blocked",
            "blocked_reason": "Approval Center remains a read-only Studio page. Source-specific Forge decision handoffs and operator form contracts can be inspected here, but approval consumption/execution requires a separate source executor and is intentionally not mounted here.",
            "required_backend_dependency": "phase9_approval_consumption_executor_contract",
        },
        "blocked_authority": dict(FORBIDDEN_AUTHORITY),
        "readiness": {
            "approval_center_panel_mounted": True,
            "approval_center_independent_route": "#/approval-center",
            "unified_sources_visible": True,
            "pulse_candidates_visible": True,
            "osril_approvals_visible": True,
            "chaser_forge_approvals_visible": True,
            "chaser_forge_source_specific_decision_handoff_visible": True,
            "chaser_forge_operator_decision_form_visible": True,
            "generic_approval_center_decision_controls_present": False,
            "gate_requests_visible": True,
            "runtime_resumes_visible": True,
            "siteops_approvals_visible": True,
            "startup_controls_visible": True,
            "approval_queue_artifacts_visible": True,
            "pending_approved_rejected_blocked_states_visible": True,
            "source_digest_visible": True,
            "duplicate_protection_hints_visible": True,
            "affected_files_systems_visible": True,
            "safety_explanation_visible": True,
            "viewing_distinguished_from_consuming": True,
            "phase9_dependency_blocker_visible": True,
            "decision_execution_deferred": True,
            "no_authority_expansion": True,
            "next_recommended_pass": "studio-runtime-cockpit-expansion",
        },
        "allowed_actions": ["inspect-approval-center-panel"],
        "possible_writes": [],
        "warnings": warnings,
    }


def get_approval_center_panel(vault_root: str | Path) -> dict[str, Any]:
    return build_approval_center_panel(vault_root)
