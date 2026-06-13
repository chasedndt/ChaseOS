"""Operator-review approval artifact for a future Studio release-promotion proof.

This pass may write exactly one scoped approval artifact for the
release-promotion packet produced by ``release_promotion_approval_preview``.
It does not consume approval, reserve the exact-once marker, write release
status, promote a release, mutate host startup/autostart, launch Studio, call
providers or connectors, enqueue Agent Bus tasks, mutate Gate, execute
workflows, use Git, or write canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.installer_build_approval import BLOCKED_AUTHORITY, DEFAULT_EVIDENCE_ROOT
from runtime.studio.release_promotion_approval_preview import (
    EXECUTION_COMPLETE_STATUS,
    NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS,
    NEXT_OPERATOR_REVIEW_PASS as PREVIEW_OPERATOR_REVIEW_PASS,
    NEXT_RELEASE_CONSUMPTION_DRY_RUN_PASS,
    build_studio_release_promotion_approval_preview,
)


MODEL_VERSION = "studio.release_promotion_approval_review.v1"
SURFACE_ID = "studio_release_promotion_approval_review"
APPROVAL_RECORD_TYPE = "studio_release_promotion_approval_artifact"
READY_STATUS = "ready_to_write_studio_release_promotion_approval_artifact"
WRITTEN_STATUS = "studio_release_promotion_approval_artifact_written_no_release_mutation"
EXISTING_STATUS = "studio_release_promotion_approval_artifact_existing_matching_no_release_mutation"
CONSUMED_STATUS = "studio_release_promotion_approval_artifact_consumed_by_execution_proof"
DENIED_STATUS = "studio_release_promotion_approval_denied_no_release_mutation"
BLOCKED_STATUS = "blocked_studio_release_promotion_approval_review"
NEXT_OPERATOR_REVIEW_PASS = "operator-review-studio-release-promotion-approval-packet"


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
        raise ValueError(f"release-promotion approval review path escapes vault: {path_value}") from exc
    return resolved


def _approval_artifact_matches(payload: dict[str, Any], packet_id: str, request_digest: str) -> bool:
    return (
        payload.get("record_type") == APPROVAL_RECORD_TYPE
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest_sha256") == request_digest
        and payload.get("operator_decision") == "approved"
        and payload.get("approval_scope") == "one_release_promotion_proof_only"
        and payload.get("release_status_write_allowed_in_this_pass") is False
        and payload.get("release_promotion_allowed_in_this_pass") is False
        and payload.get("approval_decision_consumed") is False
        and payload.get("idempotency_marker_reserved") is False
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
        raise ValueError(f"release-promotion approval artifact already exists with different content: {path}")
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return "approval_artifact_written"


def _approved_payload(
    *,
    generated_at: str,
    packet_id: str,
    request_digest: str,
    approval_path: str,
    marker_path: str,
    preview_report: dict[str, Any],
    preview: dict[str, Any],
    future_paths: dict[str, Any],
    reviewer_id: str,
    requested_by: str,
    reason: str | None,
) -> dict[str, Any]:
    material = preview.get("approval_material") or {}
    source = preview_report.get("source_artifacts") or {}
    startup_marker = source.get("startup_exact_once_marker") or {}
    signed_zip = source.get("signed_portable_zip") or {}
    signing_manifest = source.get("signing_manifest") or {}
    startup_evidence = source.get("startup_execution_evidence") or {}
    startup_audit = source.get("startup_host_mutation_audit") or {}
    startup_rollback = source.get("startup_rollback_plan") or {}
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
        "reason": reason or "Operator approved one future Studio release-promotion proof pass.",
        "approval_scope": "one_release_promotion_proof_only",
        "approved_startup_approval_packet_id": material.get("startup_approval_packet_id"),
        "approved_startup_execution_marker_path": startup_marker.get("path")
        or material.get("startup_execution_marker_path"),
        "approved_startup_execution_marker_sha256": startup_marker.get("sha256")
        or material.get("startup_execution_marker_sha256"),
        "approved_signed_portable_zip_path": signed_zip.get("path") or material.get("signed_portable_zip_path"),
        "approved_signed_portable_zip_sha256": signed_zip.get("sha256")
        or material.get("signed_portable_zip_sha256"),
        "approved_signing_manifest_path": signing_manifest.get("path") or material.get("signing_manifest_path"),
        "approved_signing_manifest_sha256": signing_manifest.get("sha256")
        or material.get("signing_manifest_sha256"),
        "approved_startup_execution_evidence_path": startup_evidence.get("path")
        or material.get("startup_execution_evidence_path"),
        "approved_startup_execution_evidence_sha256": startup_evidence.get("sha256")
        or material.get("startup_execution_evidence_sha256"),
        "approved_startup_host_mutation_audit_path": startup_audit.get("path")
        or material.get("startup_host_mutation_audit_path"),
        "approved_startup_host_mutation_audit_sha256": startup_audit.get("sha256")
        or material.get("startup_host_mutation_audit_sha256"),
        "approved_startup_rollback_plan_path": startup_rollback.get("path")
        or material.get("startup_rollback_plan_path"),
        "approved_startup_rollback_plan_sha256": startup_rollback.get("sha256")
        or material.get("startup_rollback_plan_sha256"),
        "approved_release_channel": material.get("release_channel"),
        "approved_release_mode": material.get("release_mode"),
        "approved_output_root": material.get("output_root"),
        "approval_artifact_path": approval_path,
        "exact_once_marker_path": marker_path,
        "exact_once_marker_exists": False,
        "future_output_paths": future_paths,
        "approval_material": material,
        "approval_consumption_required": True,
        "future_single_release_promotion_proof_approved": True,
        "release_status_write_allowed_in_this_pass": False,
        "release_promotion_allowed_in_this_pass": False,
        "approval_decision_consumed": False,
        "idempotency_marker_reserved": False,
        "writes_release_status": False,
        "promotes_release": False,
        "host_path_resolution_attempted": False,
        "resolves_host_startup_paths": False,
        "writes_host_startup": False,
        "registers_autostart": False,
        "writes_registry": False,
        "writes_start_menu": False,
        "writes_desktop_shortcut": False,
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
        "next_recommended_pass": NEXT_RELEASE_CONSUMPTION_DRY_RUN_PASS,
    }


def build_studio_release_promotion_approval_review(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    startup_approval_packet_id: str | None = None,
    decision: str = "approve",
    reviewer_id: str = "operator",
    requested_by: str = "Codex",
    release_channel: str = "local-proof",
    release_mode: str = "workspace-release-status-preview",
    reason: str | None = None,
    write_approval: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Review and optionally write the scoped Studio release-promotion approval artifact."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    normalized_decision = decision.strip().lower()
    if normalized_decision == "approve":
        normalized_decision = "approved"
    if normalized_decision == "deny":
        normalized_decision = "denied"

    preview_report = build_studio_release_promotion_approval_preview(
        vault,
        startup_approval_packet_id=startup_approval_packet_id,
        requested_by=requested_by,
        operator_id=reviewer_id,
        release_channel=release_channel,
        release_mode=release_mode,
        generated_at=timestamp,
    )
    preview = preview_report.get("release_promotion_approval_packet_preview") or {}
    summary = preview_report.get("summary") or {}
    future = preview_report.get("future_approval_artifact") or {}
    marker = preview_report.get("exact_once_marker_contract") or {}
    future_paths = preview_report.get("future_output_paths") or {}
    preview_checks = preview_report.get("checks") or {}
    release_execution_complete = preview_report.get("status") == EXECUTION_COMPLETE_STATUS or bool(
        summary.get("release_promotion_execution_proof_complete")
    )
    packet_id = str(preview.get("approval_packet_id") or summary.get("release_promotion_approval_packet_id") or "")
    request_digest = str(preview.get("request_digest_sha256") or summary.get("request_digest_sha256") or "")

    blockers: list[str] = []
    if normalized_decision not in {"approved", "denied"}:
        blockers.append("Operator decision must be approve/approved or deny/denied.")
    if approval_packet_id and approval_packet_id != packet_id:
        blockers.append("Requested approval packet id does not match the current release-promotion packet.")
    if not preview_report.get("ok"):
        blockers.extend(str(item) for item in preview_report.get("blockers") or [])
    if not bool(summary.get("release_promotion_approval_preview_ready")):
        blockers.append("Release-promotion approval preview is not ready.")
    if not packet_id or not request_digest:
        blockers.append("Release-promotion approval packet id or request digest is missing.")
    if not bool(preview_checks.get("startup_autostart_approved_execution_proof_complete")):
        blockers.append("Startup/autostart approved execution proof is not complete.")
    if not bool(preview_checks.get("startup_approval_consumed")):
        blockers.append("Startup/autostart approval has not been consumed by its execution proof.")
    if not bool(preview_checks.get("startup_exact_once_marker_complete")):
        blockers.append("Startup/autostart exact-once marker is missing or unhashed.")
    if not bool(preview_checks.get("signed_portable_zip_present")) or not bool(
        preview_checks.get("signed_portable_zip_hash_present")
    ):
        blockers.append("Proof-signed portable ZIP is missing or unhashed.")
    if not bool(preview_checks.get("signing_manifest_present")) or not bool(
        preview_checks.get("signing_manifest_hash_present")
    ):
        blockers.append("Signing manifest is missing or unhashed.")
    if not bool(preview_checks.get("startup_execution_evidence_present")) or not bool(
        preview_checks.get("startup_execution_evidence_hash_present")
    ):
        blockers.append("Startup/autostart execution evidence is missing or unhashed.")
    if not bool(preview_checks.get("startup_host_mutation_audit_present")) or not bool(
        preview_checks.get("startup_host_mutation_audit_hash_present")
    ):
        blockers.append("Startup/autostart host mutation audit is missing or unhashed.")
    if not bool(preview_checks.get("startup_rollback_plan_present")) or not bool(
        preview_checks.get("startup_rollback_plan_hash_present")
    ):
        blockers.append("Startup/autostart rollback plan is missing or unhashed.")
    if not bool(preview_checks.get("host_path_resolution_not_attempted")):
        blockers.append("Startup/autostart proof resolved host paths unexpectedly.")
    if not bool(preview_checks.get("host_mutation_not_performed")):
        blockers.append("Startup/autostart proof reports host mutation.")
    if not bool(preview_checks.get("startup_release_promotion_blocked")):
        blockers.append("Startup/autostart proof did not keep release promotion blocked.")
    if not bool(preview_checks.get("future_release_output_paths_clear")) and not release_execution_complete:
        blockers.append("Future release-promotion output paths are not clear.")
    if bool(marker.get("exists")) and not release_execution_complete:
        blockers.append("Future release-promotion exact-once marker path already exists.")

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
            blockers.append("Existing release-promotion approval artifact does not match the current packet.")

    approved_payload = (
        _approved_payload(
            generated_at=timestamp,
            packet_id=packet_id,
            request_digest=request_digest,
            approval_path=_relative_to_vault(vault, approval_path) if approval_path else str(future.get("path") or ""),
            marker_path=_relative_to_vault(vault, marker_path) if marker_path else str(marker.get("path") or ""),
            preview_report=preview_report,
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
        next_pass = PREVIEW_OPERATOR_REVIEW_PASS
    elif release_execution_complete:
        status = CONSUMED_STATUS
        write_status = "approval_consumed_by_existing_release_promotion_execution_proof"
        next_pass = NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS
    elif existing_matches:
        status = EXISTING_STATUS
        write_status = "existing_matching_approval_present"
        next_pass = NEXT_RELEASE_CONSUMPTION_DRY_RUN_PASS
    elif write_approval and approval_path is not None:
        write_status = _write_approval_artifact(approval_path, approved_payload)
        writes_performed = write_status == "approval_artifact_written"
        artifact_present = True
        status = WRITTEN_STATUS if writes_performed else EXISTING_STATUS
        next_pass = NEXT_RELEASE_CONSUMPTION_DRY_RUN_PASS
    else:
        status = READY_STATUS
        next_pass = NEXT_OPERATOR_REVIEW_PASS

    ok = status != BLOCKED_STATUS
    approval_artifact_written = artifact_present
    authority = {
        **dict(BLOCKED_AUTHORITY),
        "approval_packet_preview_only": False,
        "approval_artifact_review_only": True,
        "creates_approval_artifact": bool(writes_performed),
        "writes_approval_artifact": bool(writes_performed),
        "future_single_release_promotion_proof_approved": bool(approval_artifact_written),
        "release_promotion_approval_preview_only": False,
        "consumes_approval_decision": False,
        "grants_approvals": False,
        "executes_approval_decisions": False,
        "reserves_idempotency_marker": False,
        "writes_idempotency_marker": False,
        "resolves_host_startup_paths": False,
        "writes_host_startup": False,
        "registers_autostart": False,
        "writes_registry": False,
        "writes_start_menu": False,
        "writes_desktop_shortcut": False,
        "promotes_release": False,
        "writes_release_status": False,
        "launches_pywebview": False,
        "starts_servers": False,
        "launches_executable": False,
        "browser_use_cli_live_run": False,
        "excalidraw_live_proof": False,
        "mutates_gate": False,
        "executes_workflows": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "writes_agent_bus_tasks": False,
        "canonical_mutation_allowed": False,
    }
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
            "future_single_release_promotion_proof_approved": approval_artifact_written,
            "release_promotion_execution_proof_complete": release_execution_complete,
            "approval_decision_consumed": release_execution_complete,
            "exact_once_marker_exists": bool(marker.get("exists")),
            "release_status_write_allowed": False,
            "release_promotion_allowed": False,
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
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
            "completed_by_execution_proof": release_execution_complete,
            "future_write_mode": "exclusive_create_before_release_status_write",
        },
        "future_output_paths": future_paths,
        "checks": {
            "preview_ready": bool(preview_report.get("ok")),
            "approval_packet_matches_request": (not approval_packet_id) or approval_packet_id == packet_id,
            "operator_decision_supported": normalized_decision in {"approved", "denied"},
            "approval_artifact_absent_or_matching": not bool(existing_payload) or existing_matches,
            "exact_once_marker_absent": (not bool(marker.get("exists"))) or release_execution_complete,
            "future_output_paths_clear": bool(preview_checks.get("future_release_output_paths_clear"))
            or release_execution_complete,
            "release_promotion_execution_proof_complete": release_execution_complete,
            "startup_autostart_approved_execution_proof_complete": bool(
                preview_checks.get("startup_autostart_approved_execution_proof_complete")
            ),
            "startup_approval_consumed": bool(preview_checks.get("startup_approval_consumed")),
            "startup_exact_once_marker_complete": bool(preview_checks.get("startup_exact_once_marker_complete")),
            "signed_portable_zip_present": bool(preview_checks.get("signed_portable_zip_present")),
            "signing_manifest_present": bool(preview_checks.get("signing_manifest_present")),
            "startup_execution_evidence_present": bool(preview_checks.get("startup_execution_evidence_present")),
            "startup_host_mutation_audit_present": bool(preview_checks.get("startup_host_mutation_audit_present")),
            "startup_rollback_plan_present": bool(preview_checks.get("startup_rollback_plan_present")),
            "host_path_resolution_not_attempted": bool(preview_checks.get("host_path_resolution_not_attempted")),
            "host_mutation_not_performed": bool(preview_checks.get("host_mutation_not_performed")),
            "release_status_write_blocked": True,
            "release_promotion_blocked": True,
            "no_execution_in_this_pass": True,
        },
        "authority": authority,
        "blockers": blockers,
        "unverified": [
            "No approval decision was consumed in this review pass.",
            "No release-promotion exact-once marker was reserved in this review pass.",
            "No release-status, release manifest, release audit, rollback, or promotion output was written.",
            "No host startup/autostart, registry, Start Menu, desktop shortcut, Studio launch, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback was attempted.",
        ],
        "writes_performed": writes_performed,
        "next_recommended_pass": next_pass,
    }


def write_release_promotion_approval_review_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-release-promotion-approval-review"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    artifact = report.get("approval_artifact") or {}
    marker = report.get("exact_once_marker_contract") or {}
    lines = [
        "# Studio Release Promotion Approval Review Evidence",
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
        "## Release Boundary",
        "",
        f"- release_status_write_allowed: {summary.get('release_status_write_allowed')}",
        f"- release_promotion_allowed: {summary.get('release_promotion_allowed')}",
        f"- host_path_resolution_attempted: {summary.get('host_path_resolution_attempted')}",
        f"- host_mutation_performed: {summary.get('host_mutation_performed')}",
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
