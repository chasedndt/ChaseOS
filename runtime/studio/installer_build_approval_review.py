"""Operator-review approval artifact for a future Studio installer build.

This pass may write exactly one scoped approval artifact for the installer-build
packet produced by ``installer_build_approval``. It does not consume that
approval, reserve the exact-once marker, build installers, sign artifacts,
mutate startup/autostart, launch Studio, call providers/connectors, enqueue
Agent Bus tasks, mutate Gate, execute workflows, or write canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.installer_build_approval import (
    APPROVAL_RELATIVE_DIR,
    BLOCKED_AUTHORITY,
    DEFAULT_EVIDENCE_ROOT,
    INSTALLER_OUTPUT_ROOT,
    NEXT_APPROVAL_CONSUMPTION_DRY_RUN_PASS,
    build_studio_governed_installer_build_approval,
)


MODEL_VERSION = "studio.installer_build_approval_review.v1"
SURFACE_ID = "studio_installer_build_approval_review"
APPROVAL_RECORD_TYPE = "studio_installer_build_approval_artifact"
READY_STATUS = "ready_to_write_studio_installer_build_approval_artifact"
WRITTEN_STATUS = "studio_installer_build_approval_artifact_written_no_execution"
EXISTING_STATUS = "studio_installer_build_approval_artifact_existing_matching_no_execution"
DENIED_STATUS = "studio_installer_build_approval_denied_no_execution"
BLOCKED_STATUS = "blocked_studio_installer_build_approval_review"
NEXT_OPERATOR_REVIEW_PASS = "operator-review-studio-installer-build-approval-packet"
NEXT_SIGNING_APPROVAL_PASS = "studio-signing-approval-preview"
CONSUMED_STATUS = "studio_installer_build_approval_consumed_by_execution_proof"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _resolve_vault_relative_path(vault: Path, path_value: str) -> Path:
    path = Path(path_value)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"installer-build approval review path escapes vault: {path_value}") from exc
    return resolved


def _approval_artifact_matches(payload: dict[str, Any], packet_id: str, request_digest: str) -> bool:
    return (
        payload.get("record_type") == APPROVAL_RECORD_TYPE
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest_sha256") == request_digest
        and payload.get("operator_decision") == "approved"
        and payload.get("approval_scope") == "one_installer_build_only"
        and payload.get("execution_allowed_in_this_pass") is False
        and payload.get("installer_build_allowed_in_this_pass") is False
    )


def _write_approval_artifact(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = _read_json(path)
        if existing and _approval_artifact_matches(
            existing,
            str(payload.get("approval_packet_id") or ""),
            str(payload.get("request_digest_sha256") or ""),
        ):
            return "existing_matching_approval_reused"
        raise ValueError(f"installer-build approval artifact already exists with different content: {path}")
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return "approval_artifact_written"


def _approved_payload(
    *,
    generated_at: str,
    packet_id: str,
    request_digest: str,
    approval_path: str,
    marker_path: str,
    preview: dict[str, Any],
    future_paths: dict[str, Any],
    reviewer_id: str,
    requested_by: str,
    reason: str | None,
) -> dict[str, Any]:
    material = preview.get("approval_material") or {}
    return {
        "record_type": APPROVAL_RECORD_TYPE,
        "schema_version": MODEL_VERSION,
        "generated_at": generated_at,
        "status": WRITTEN_STATUS,
        "approval_packet_id": packet_id,
        "request_digest_sha256": request_digest,
        "operator_decision": "approved",
        "reviewer_id": reviewer_id,
        "requested_by": requested_by,
        "reason": reason or "Operator approved one future Studio installer-build proof pass.",
        "approval_scope": "one_installer_build_only",
        "approved_installer_format": preview.get("installer_format") or material.get("installer_format") or "zip-portable",
        "approved_output_root": material.get("output_root") or INSTALLER_OUTPUT_ROOT.as_posix(),
        "approved_packaged_executable_sha256": preview.get("packaged_executable_sha256"),
        "approved_packaged_executable": preview.get("packaged_executable") or {},
        "source_release_governance_status": preview.get("source_release_governance_status"),
        "source_release_governance_next": preview.get("source_release_governance_next"),
        "approval_artifact_path": approval_path,
        "exact_once_marker_path": marker_path,
        "exact_once_marker_exists": False,
        "future_output_paths": future_paths,
        "approval_material": material,
        "approval_consumption_required": True,
        "future_single_build_approved": True,
        "execution_allowed_in_this_pass": False,
        "installer_build_allowed_in_this_pass": False,
        "approval_decision_consumed": False,
        "idempotency_marker_reserved": False,
        "builds_executable": False,
        "builds_installer": False,
        "writes_installer": False,
        "writes_packaging_output_root": False,
        "signing_allowed": False,
        "reads_signing_certificate": False,
        "startup_mutation_allowed": False,
        "autostart_registration_allowed": False,
        "registry_write_allowed": False,
        "start_menu_write_allowed": False,
        "desktop_shortcut_write_allowed": False,
        "release_promotion_allowed": False,
        "release_status_write_allowed": False,
        "pywebview_launch_allowed": False,
        "server_start_allowed": False,
        "executable_launch_allowed": False,
        "browser_use_cli_live_run": False,
        "excalidraw_live_proof": False,
        "mutates_gate": False,
        "executes_workflows": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "writes_agent_bus_tasks": False,
        "canonical_mutation_allowed": False,
        "next_recommended_pass": NEXT_APPROVAL_CONSUMPTION_DRY_RUN_PASS,
    }


def build_studio_installer_build_approval_review(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    decision: str = "approve",
    reviewer_id: str = "operator",
    requested_by: str = "Codex",
    reason: str | None = None,
    write_approval: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Review and optionally write the scoped Studio installer-build approval artifact."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    normalized_decision = decision.strip().lower()
    if normalized_decision == "approve":
        normalized_decision = "approved"
    if normalized_decision == "deny":
        normalized_decision = "denied"

    preview_report = build_studio_governed_installer_build_approval(
        vault,
        approval_packet_id=approval_packet_id,
        requested_by=requested_by,
        operator_id=reviewer_id,
        generated_at=timestamp,
    )
    preview = preview_report.get("approval_packet_preview") or {}
    summary = preview_report.get("summary") or {}
    future = preview_report.get("future_approval_artifact") or {}
    marker = preview_report.get("exact_once_marker_contract") or {}
    future_paths = preview_report.get("future_output_paths") or {}
    preview_checks = preview_report.get("checks") or {}
    approved_execution_complete = bool(preview_checks.get("approved_execution_proof_complete"))
    packet_id = str(preview.get("approval_packet_id") or "")
    request_digest = str(preview.get("request_digest_sha256") or "")

    blockers: list[str] = []
    if normalized_decision not in {"approved", "denied"}:
        blockers.append("Operator decision must be approve/approved or deny/denied.")
    if approval_packet_id and approval_packet_id != packet_id:
        blockers.append("Requested approval packet id does not match the current installer-build packet.")
    if not preview_report.get("ok"):
        blockers.extend(str(item) for item in preview_report.get("blockers") or [])
    if not bool(summary.get("release_readiness_governance_ready")):
        blockers.append("Release-readiness governance is not ready.")
    if not bool(summary.get("installer_build_gate_declared")):
        blockers.append("Installer-build approval gate is not declared.")
    if not packet_id or not request_digest:
        blockers.append("Approval packet id or request digest is missing.")
    if not bool(preview_checks.get("future_output_paths_clear")) and not approved_execution_complete:
        blockers.append("Future installer output paths are not clear.")
    if bool(marker.get("exists")) and not approved_execution_complete:
        blockers.append("Future installer-build exact-once marker path already exists.")

    approval_path: Path | None = None
    marker_path: Path | None = None
    existing_payload: dict[str, Any] | None = None
    existing_matches = False
    try:
        approval_path = _resolve_vault_relative_path(vault, str(future.get("path") or ""))
        marker_path = _resolve_vault_relative_path(vault, str(marker.get("path") or ""))
    except ValueError as exc:
        blockers.append(str(exc))

    if approval_path is not None and approval_path.exists():
        existing_payload = _read_json(approval_path)
        existing_matches = bool(existing_payload and _approval_artifact_matches(existing_payload, packet_id, request_digest))
        if not existing_matches:
            blockers.append("Existing installer-build approval artifact does not match the current packet.")

    approved_payload = (
        _approved_payload(
            generated_at=timestamp,
            packet_id=packet_id,
            request_digest=request_digest,
            approval_path=_relative_to_vault(vault, approval_path) if approval_path else str(future.get("path") or ""),
            marker_path=_relative_to_vault(vault, marker_path) if marker_path else str(marker.get("path") or ""),
            preview=preview,
            future_paths=future_paths,
            reviewer_id=reviewer_id,
            requested_by=requested_by,
            reason=reason,
        )
        if packet_id and request_digest
        else {}
    )

    write_status = "not_requested"
    writes_performed = False
    artifact_present = existing_matches
    if not blockers and normalized_decision == "denied":
        status = DENIED_STATUS
        next_pass = NEXT_OPERATOR_REVIEW_PASS
    elif blockers:
        status = BLOCKED_STATUS
        next_pass = "studio-governed-installer-build-approval"
    elif approved_execution_complete:
        status = CONSUMED_STATUS
        write_status = "approval_consumed_by_existing_execution_proof"
        artifact_present = existing_matches
        next_pass = NEXT_SIGNING_APPROVAL_PASS
    elif existing_matches:
        status = EXISTING_STATUS
        write_status = "existing_matching_approval_present"
        next_pass = NEXT_APPROVAL_CONSUMPTION_DRY_RUN_PASS
    elif write_approval and approval_path is not None:
        write_status = _write_approval_artifact(approval_path, approved_payload)
        writes_performed = write_status == "approval_artifact_written"
        artifact_present = True
        status = WRITTEN_STATUS if writes_performed else EXISTING_STATUS
        next_pass = NEXT_APPROVAL_CONSUMPTION_DRY_RUN_PASS
    else:
        status = READY_STATUS
        next_pass = NEXT_OPERATOR_REVIEW_PASS

    ok = status != BLOCKED_STATUS
    approval_artifact_written = artifact_present
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "summary": {
            "approval_packet_id": packet_id,
            "request_digest_sha256": request_digest,
            "operator_decision": normalized_decision,
            "approval_artifact_ready": ok and normalized_decision == "approved",
            "approval_artifact_written": approval_artifact_written,
            "approval_artifact_write_status": write_status,
            "future_single_build_approved": approval_artifact_written,
            "approval_decision_consumed": approved_execution_complete,
            "approved_execution_proof_complete": approved_execution_complete,
            "exact_once_marker_exists": bool(marker.get("exists")),
            "execution_allowed": False,
            "installer_build_allowed": False,
            "writes_performed": writes_performed,
            "next_recommended_pass": next_pass,
        },
        "source_preview": preview_report,
        "approval_artifact_payload": approved_payload,
        "approval_artifact": {
            "path": _relative_to_vault(vault, approval_path) if approval_path else str(future.get("path") or ""),
            "exists_before": bool(existing_payload),
            "exists_after": bool(approval_path and approval_path.exists()),
            "matches_current_packet": approval_artifact_written,
            "write_requested": write_approval,
            "write_status": write_status,
            "written_in_this_pass": writes_performed,
        },
        "exact_once_marker_contract": {
            "path": _relative_to_vault(vault, marker_path) if marker_path else str(marker.get("path") or ""),
            "exists": bool(marker.get("exists")),
            "reserved_in_this_pass": False,
            "future_write_mode": "exclusive_create_before_installer_build",
        },
        "future_output_paths": future_paths,
        "checks": {
            "preview_ready": bool(preview_report.get("ok")),
            "approval_packet_matches_request": (not approval_packet_id) or approval_packet_id == packet_id,
            "operator_decision_supported": normalized_decision in {"approved", "denied"},
            "approval_artifact_absent_or_matching": not bool(existing_payload) or existing_matches,
            "exact_once_marker_absent": not bool(marker.get("exists")),
            "future_output_paths_clear": bool(preview_checks.get("future_output_paths_clear")),
            "approved_execution_proof_complete": approved_execution_complete,
            "no_execution_in_this_pass": True,
        },
        "authority": {
            **dict(BLOCKED_AUTHORITY),
            "approval_packet_preview_only": False,
            "approval_artifact_review_only": True,
            "creates_approval_artifact": bool(writes_performed),
            "writes_approval_artifact": bool(writes_performed),
            "future_single_build_approved": bool(approval_artifact_written),
        },
        "blockers": blockers,
        "unverified": [
            "No new approval decision was consumed in this review pass.",
            "No exact-once marker was reserved in this review pass.",
            "No installer build or dry-run execution was attempted in this review pass.",
            "No signing, startup/autostart, registry, Start Menu, desktop shortcut, release promotion, provider/connector call, Agent Bus write, Gate mutation, workflow execution, or canonical writeback was attempted.",
        ],
        "writes_performed": writes_performed,
        "next_recommended_pass": next_pass,
    }


def write_installer_build_approval_review_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-installer-build-approval-review"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    artifact = report.get("approval_artifact") or {}
    marker = report.get("exact_once_marker_contract") or {}
    lines = [
        "# Studio Installer Build Approval Review Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next: {report.get('next_recommended_pass')}",
        "",
        "## Approval Artifact",
        "",
        f"- approval_packet_id: {summary.get('approval_packet_id')}",
        f"- request_digest_sha256: {summary.get('request_digest_sha256')}",
        f"- operator_decision: {summary.get('operator_decision')}",
        f"- approval_artifact_path: {artifact.get('path')}",
        f"- approval_artifact_written: {summary.get('approval_artifact_written')}",
        f"- write_status: {summary.get('approval_artifact_write_status')}",
        f"- writes_performed: {summary.get('writes_performed')}",
        "",
        "## Exact-Once Boundary",
        "",
        f"- exact_once_marker_path: {marker.get('path')}",
        f"- exact_once_marker_exists: {marker.get('exists')}",
        f"- reserved_in_this_pass: {marker.get('reserved_in_this_pass')}",
        "",
        "## Future Output Paths",
        "",
        *[
            f"- {key}: {value.get('path')} exists={value.get('exists')}"
            for key, value in (report.get("future_output_paths") or {}).items()
        ],
        "",
        "## Authority",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("authority") or {}).items()],
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in (report.get("blockers") or ["None"])],
        "",
        "## Unverified",
        "",
        *[f"- {item}" for item in report.get("unverified") or []],
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
