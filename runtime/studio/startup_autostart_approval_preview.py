"""No-execution startup/autostart approval preview for ChaseOS Studio.

This contract is the next governed gate after the Studio signing approved
execution proof. It inspects the completed proof-signed Studio package and
previews a stable operator-review packet for a future startup/autostart proof.

It does not create approval artifacts, consume approvals, reserve markers,
resolve host startup paths, write Windows startup folders, register autostart,
write registry/Start Menu/desktop shortcuts, promote a release, launch Studio,
call providers/connectors, enqueue Agent Bus tasks, mutate Gate, execute
workflows, configure Git, or write canonical ChaseOS state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.installer_build_approval import BLOCKED_AUTHORITY, DEFAULT_EVIDENCE_ROOT
from runtime.studio.signing_approved_execution_proof import (
    COMPLETE_STATUS as SIGNING_EXECUTION_COMPLETE_STATUS,
    build_studio_signing_approved_execution_proof,
)


MODEL_VERSION = "studio.startup_autostart_approval_preview.v1"
SURFACE_ID = "studio_startup_autostart_approval_preview"
READY_STATUS = "ready_for_operator_studio_startup_autostart_approval_review"
PENDING_CONSUMPTION_STATUS = "studio_startup_autostart_approval_artifact_present_pending_consumption"
EXECUTION_COMPLETE_STATUS = "studio_startup_autostart_approved_execution_proof_complete"
BLOCKED_STATUS = "blocked_studio_startup_autostart_approval_preview"
STARTUP_APPROVAL_RELATIVE_DIR = Path("07_LOGS") / "Agent-Activity" / "_studio_startup_autostart_approvals"
STARTUP_MARKER_RELATIVE_DIR = STARTUP_APPROVAL_RELATIVE_DIR / "_execution_markers"
STARTUP_PROOF_ROOT = Path(".pytest_tmp_env") / "studio-startup-autostart-proof"
NEXT_OPERATOR_REVIEW_PASS = "operator-review-studio-startup-autostart-approval-packet"
NEXT_STARTUP_CONSUMPTION_DRY_RUN_PASS = "studio-startup-autostart-approval-consumption-dry-run"
NEXT_RELEASE_PROMOTION_APPROVAL_PASS = "studio-release-promotion-approval-preview"
BLOCKED_PASS = "studio-signing-approved-execution-proof"

HOST_TARGET_PREVIEWS = (
    {
        "id": "windows-startup-folder-shortcut",
        "kind": "startup_folder_shortcut",
        "status": "approval_required_before_host_mutation",
        "host_path_resolved_now": False,
        "write_allowed_in_this_pass": False,
    },
    {
        "id": "windows-task-scheduler",
        "kind": "scheduled_task_registration",
        "status": "deferred_to_future_governed_executor",
        "host_path_resolved_now": False,
        "write_allowed_in_this_pass": False,
    },
    {
        "id": "windows-registry-run-key",
        "kind": "registry_run_key",
        "status": "deferred_to_future_governed_executor",
        "host_path_resolved_now": False,
        "write_allowed_in_this_pass": False,
    },
    {
        "id": "start-menu-shortcut",
        "kind": "start_menu_shortcut",
        "status": "separate_shortcut_write_gate_required",
        "host_path_resolved_now": False,
        "write_allowed_in_this_pass": False,
    },
    {
        "id": "desktop-shortcut",
        "kind": "desktop_shortcut",
        "status": "separate_shortcut_write_gate_required",
        "host_path_resolved_now": False,
        "write_allowed_in_this_pass": False,
    },
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _slug(value: str, fallback: str = "studio-startup-autostart") -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug or fallback


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _completed_startup_marker(marker_path: Path, approval_packet_id: str) -> bool:
    payload = _read_json(marker_path) if marker_path.is_file() else None
    return bool(
        payload
        and payload.get("record_type") == "studio_startup_autostart_execution_marker"
        and payload.get("approval_packet_id") == approval_packet_id
        and payload.get("status") == EXECUTION_COMPLETE_STATUS
    )


def _safe_json_path(vault: Path, base_relative: Path, identifier: str) -> Path:
    base = (vault / base_relative).resolve()
    path = (base / f"{_slug(identifier)}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Studio startup/autostart approval path escapes base directory: {path}") from exc
    return path


def _resolve_vault_relative_path(vault: Path, path_value: str) -> Path:
    path = Path(path_value)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"Studio startup/autostart preview path escapes vault: {path_value}") from exc
    return resolved


def _path_from_record(vault: Path, record: dict[str, Any]) -> Path | None:
    value = str(record.get("path") or "")
    return _resolve_vault_relative_path(vault, value) if value else None


def _file_record(vault: Path, path: Path | None, path_value: str = "") -> dict[str, Any]:
    return {
        "path": _relative_to_vault(vault, path) if path else path_value,
        "exists": bool(path and path.is_file()),
        "size_bytes": path.stat().st_size if path and path.is_file() else 0,
        "sha256": _sha256_file(path) if path and path.is_file() else None,
    }


def _future_paths(vault: Path, packet_id: str) -> dict[str, dict[str, Any]]:
    output_root = vault / STARTUP_PROOF_ROOT
    return {
        "output_root": {
            "path": _relative_to_vault(vault, output_root),
            "exists": output_root.exists(),
        },
        "startup_dry_run_evidence": _file_record(
            vault,
            vault / DEFAULT_EVIDENCE_ROOT / f"{packet_id}-startup-autostart-dry-run.json",
        ),
        "startup_execution_evidence": _file_record(
            vault,
            vault / DEFAULT_EVIDENCE_ROOT / f"{packet_id}-startup-autostart-execution.json",
        ),
        "rollback_plan": _file_record(
            vault,
            output_root / "rollback" / f"{packet_id}-startup-autostart-rollback-plan.json",
        ),
        "host_mutation_audit": _file_record(
            vault,
            output_root / "audit" / f"{packet_id}-startup-autostart-host-mutation-audit.json",
        ),
    }


def _approval_material(
    *,
    signing_approval_packet_id: str,
    signing_execution_marker_path: str,
    signing_execution_marker_sha256: str,
    signed_portable_zip_path: str,
    signed_portable_zip_sha256: str,
    signing_manifest_path: str,
    signing_manifest_sha256: str,
    requested_by: str,
    operator_id: str,
    startup_mode: str,
) -> dict[str, Any]:
    return {
        "schema_version": MODEL_VERSION,
        "operation": "studio_startup_autostart_proof",
        "required_gate": "startup-autostart-approval",
        "signing_approval_packet_id": signing_approval_packet_id,
        "signing_execution_marker_path": signing_execution_marker_path,
        "signing_execution_marker_sha256": signing_execution_marker_sha256,
        "signed_portable_zip_path": signed_portable_zip_path,
        "signed_portable_zip_sha256": signed_portable_zip_sha256,
        "signing_manifest_path": signing_manifest_path,
        "signing_manifest_sha256": signing_manifest_sha256,
        "requested_by": requested_by,
        "operator_id": operator_id,
        "startup_mode": startup_mode,
        "target_platform": "windows",
        "candidate_host_targets": [item["id"] for item in HOST_TARGET_PREVIEWS],
        "approval_effect": "authorizes one future startup/autostart proof only after a separate approval artifact is written and consumed",
        "host_path_resolution_allowed_in_preview": False,
        "startup_mutation_allowed_in_preview": False,
        "registry_write_allowed_in_preview": False,
        "shortcut_write_allowed_in_preview": False,
        "release_promotion_allowed": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "canonical_writeback_allowed": False,
    }


def _approval_packet_id(material: dict[str, Any]) -> str:
    digest = _sha256(material)
    return f"studio-startup-autostart-appr-{digest[:16]}"


def _approval_artifact_matches_preview(path: Path, packet_id: str, request_digest: str) -> bool:
    payload = _read_json(path)
    if not payload:
        return False
    return (
        payload.get("record_type") == "studio_startup_autostart_approval_artifact"
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest_sha256") == request_digest
        and payload.get("operator_decision") == "approved"
        and payload.get("approval_scope") == "one_startup_autostart_proof_only"
        and payload.get("startup_mutation_allowed_in_this_pass") is False
        and payload.get("approval_decision_consumed") is False
    )


def _authority() -> dict[str, Any]:
    return {
        **dict(BLOCKED_AUTHORITY),
        "approval_packet_preview_only": True,
        "startup_autostart_approval_preview_only": True,
        "creates_approval_artifact": False,
        "writes_approval_artifact": False,
        "consumes_approval_decision": False,
        "grants_approvals": False,
        "executes_approval_decisions": False,
        "reserves_idempotency_marker": False,
        "writes_idempotency_marker": False,
        "builds_executable": False,
        "builds_installer": False,
        "writes_installer": False,
        "writes_packaging_output_root": False,
        "signs_artifacts": False,
        "reads_signing_certificate": False,
        "writes_signed_artifact": False,
        "verifies_signature": False,
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


def build_studio_startup_autostart_approval_preview(
    vault_root: str | Path,
    *,
    signing_approval_packet_id: str | None = None,
    requested_by: str = "Codex",
    operator_id: str = "operator",
    startup_mode: str = "windows-startup-folder-shortcut-preview",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build the no-execution Studio startup/autostart approval preview."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    try:
        signing = build_studio_signing_approved_execution_proof(
            vault,
            approval_packet_id=signing_approval_packet_id,
            execute=False,
            generated_at=timestamp,
        )
    except (ValueError, KeyError) as exc:
        signing = {"ok": False, "status": BLOCKED_PASS, "summary": {}, "paths": {}}
        blockers.append(str(exc))

    summary = signing.get("summary") or {}
    paths = signing.get("paths") or {}
    marker_record = paths.get("exact_once_marker") or {}
    signed_zip_record = paths.get("signed_portable_zip") or {}
    manifest_record = paths.get("signing_manifest") or {}
    execution_record = paths.get("execution_evidence") or {}
    packet_id = str(summary.get("approval_packet_id") or signing_approval_packet_id or "")
    marker_path = _path_from_record(vault, marker_record)
    signed_zip_path = _path_from_record(vault, signed_zip_record)
    manifest_path = _path_from_record(vault, manifest_record)
    marker_sha = str(marker_record.get("sha256") or (_sha256_file(marker_path) if marker_path else "") or "")
    signed_zip_sha = str(signed_zip_record.get("sha256") or (_sha256_file(signed_zip_path) if signed_zip_path else "") or "")
    manifest_sha = str(manifest_record.get("sha256") or (_sha256_file(manifest_path) if manifest_path else "") or "")

    material = _approval_material(
        signing_approval_packet_id=packet_id,
        signing_execution_marker_path=_relative_to_vault(vault, marker_path) if marker_path else str(marker_record.get("path") or ""),
        signing_execution_marker_sha256=marker_sha,
        signed_portable_zip_path=_relative_to_vault(vault, signed_zip_path) if signed_zip_path else str(signed_zip_record.get("path") or ""),
        signed_portable_zip_sha256=signed_zip_sha,
        signing_manifest_path=_relative_to_vault(vault, manifest_path) if manifest_path else str(manifest_record.get("path") or ""),
        signing_manifest_sha256=manifest_sha,
        requested_by=requested_by,
        operator_id=operator_id,
        startup_mode=startup_mode,
    )
    approval_packet_id = _approval_packet_id(material)
    request_digest = _sha256(material)
    approval_path = _safe_json_path(vault, STARTUP_APPROVAL_RELATIVE_DIR, approval_packet_id)
    marker_contract_path = _safe_json_path(vault, STARTUP_MARKER_RELATIVE_DIR, approval_packet_id)
    future_paths = _future_paths(vault, approval_packet_id)
    output_paths_clear = not any(
        bool(item.get("exists"))
        for key, item in future_paths.items()
        if key != "output_root"
    )
    approval_exists = approval_path.is_file()
    approval_matches = (
        _approval_artifact_matches_preview(approval_path, approval_packet_id, request_digest)
        if approval_exists
        else False
    )
    startup_execution_complete = _completed_startup_marker(marker_contract_path, approval_packet_id)
    output_paths_clear = output_paths_clear or startup_execution_complete

    checks = {
        "signing_execution_proof_complete": signing.get("status") == SIGNING_EXECUTION_COMPLETE_STATUS and bool(signing.get("ok")),
        "signing_approval_consumed": bool(summary.get("approval_consumed")),
        "signing_duplicate_execution_blocked": bool(summary.get("duplicate_execution_blocked")),
        "signed_portable_zip_present": bool(signed_zip_path and signed_zip_path.is_file()),
        "signed_portable_zip_hash_present": bool(signed_zip_sha),
        "signing_manifest_present": bool(manifest_path and manifest_path.is_file()),
        "signing_manifest_hash_present": bool(manifest_sha),
        "signing_execution_marker_complete": bool(marker_path and marker_path.is_file() and marker_sha),
        "signing_execution_evidence_present": bool(execution_record.get("exists")),
        "startup_approval_artifact_absent_or_matching": (not approval_exists) or approval_matches,
        "startup_exact_once_marker_absent": not marker_contract_path.exists() or startup_execution_complete,
        "future_startup_output_paths_clear": output_paths_clear,
        "startup_autostart_execution_proof_complete": startup_execution_complete,
        "host_paths_not_resolved": True,
        "host_mutation_blocked_in_this_pass": True,
    }

    if not checks["signing_execution_proof_complete"]:
        blockers.append("Studio signing approved execution proof is not complete.")
    if not checks["signing_approval_consumed"]:
        blockers.append("Studio signing approval has not been consumed by the execution proof.")
    if not checks["signed_portable_zip_present"] or not checks["signed_portable_zip_hash_present"]:
        blockers.append("Proof-signed portable ZIP is missing or unhashed.")
    if not checks["signing_manifest_present"] or not checks["signing_manifest_hash_present"]:
        blockers.append("Signing manifest is missing or unhashed.")
    if approval_exists and not approval_matches:
        blockers.append("Future startup/autostart approval artifact path already exists with mismatched content.")
    if marker_contract_path.exists() and not startup_execution_complete:
        blockers.append("Future startup/autostart exact-once marker path already exists.")
    if not output_paths_clear and not startup_execution_complete:
        blockers.append("Future startup/autostart output evidence paths are not clear.")

    ok = not blockers
    status = (
        EXECUTION_COMPLETE_STATUS
        if ok and startup_execution_complete
        else PENDING_CONSUMPTION_STATUS
        if ok and approval_matches
        else READY_STATUS
        if ok
        else BLOCKED_STATUS
    )
    next_pass = (
        NEXT_RELEASE_PROMOTION_APPROVAL_PASS
        if ok and startup_execution_complete
        else NEXT_STARTUP_CONSUMPTION_DRY_RUN_PASS
        if ok and approval_matches
        else NEXT_OPERATOR_REVIEW_PASS
        if ok
        else BLOCKED_PASS
    )
    authority = _authority()
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "summary": {
            "signing_approval_packet_id": packet_id,
            "startup_autostart_approval_packet_id": approval_packet_id,
            "request_digest_sha256": request_digest,
            "startup_autostart_approval_preview_ready": ok,
            "startup_autostart_execution_proof_complete": startup_execution_complete,
            "approval_artifact_written": approval_matches,
            "approval_decision_consumed": startup_execution_complete,
            "host_path_resolution_attempted": False,
            "host_startup_mutation_allowed": False,
            "autostart_registration_allowed": False,
            "registry_write_allowed": False,
            "start_menu_write_allowed": False,
            "desktop_shortcut_write_allowed": False,
            "release_promotion_allowed": False,
            "writes_performed": False,
            "next_recommended_pass": next_pass,
        },
        "source_contracts": {
            "signing_approved_execution_proof": {
                "ok": signing.get("ok"),
                "status": signing.get("status"),
                "next_recommended_pass": signing.get("next_recommended_pass"),
            }
        },
        "startup_autostart_approval_packet_preview": {
            "record_type": "studio_startup_autostart_approval_packet_preview",
            "schema_version": MODEL_VERSION,
            "approval_packet_id": approval_packet_id,
            "request_digest_sha256": request_digest,
            "status": "approved_artifact_present" if approval_matches else "preview_only_not_approved",
            "required_gate": "startup-autostart-approval",
            "requested_by": requested_by,
            "operator_id": operator_id,
            "startup_mode": startup_mode,
            "approval_artifact_path": _relative_to_vault(vault, approval_path),
            "approval_artifact_written": approval_matches,
            "approval_decision_consumed": startup_execution_complete,
            "future_single_startup_autostart_proof_approved": approval_matches,
            "host_mutation_allowed_in_this_pass": False,
            "approval_material": material,
        },
        "source_artifacts": {
            "signing_exact_once_marker": _file_record(vault, marker_path, str(marker_record.get("path") or "")),
            "signed_portable_zip": _file_record(vault, signed_zip_path, str(signed_zip_record.get("path") or "")),
            "signing_manifest": _file_record(vault, manifest_path, str(manifest_record.get("path") or "")),
            "signing_execution_evidence": {
                "path": str(execution_record.get("path") or ""),
                "exists": bool(execution_record.get("exists")),
                "sha256": execution_record.get("sha256"),
            },
        },
        "future_approval_artifact": {
            "path": _relative_to_vault(vault, approval_path),
            "exists": approval_exists,
            "matches_current_packet": approval_matches,
            "write_allowed_in_this_pass": False,
            "future_write_pass": None if approval_matches else NEXT_OPERATOR_REVIEW_PASS,
        },
        "exact_once_marker_contract": {
            "path": _relative_to_vault(vault, marker_contract_path),
            "exists": marker_contract_path.exists(),
            "reserved_in_this_pass": False,
            "completed_by_execution_proof": startup_execution_complete,
            "future_write_mode": "exclusive_create_before_host_startup_mutation",
            "duplicate_policy": "block_before_any_host_startup_or_shortcut_write",
        },
        "future_output_paths": future_paths,
        "host_target_previews": [dict(item) for item in HOST_TARGET_PREVIEWS],
        "dry_run_plan": [
            {"step": "verify_signing_execution_marker", "required": True, "effect_now": "read_only_check"},
            {"step": "verify_signed_portable_zip_hash", "required": True, "effect_now": "read_only_check"},
            {"step": "verify_signing_manifest_hash", "required": True, "effect_now": "read_only_check"},
            {"step": "verify_startup_autostart_approval_artifact", "required": True, "effect_now": "preview_only"},
            {"step": "verify_future_startup_marker_absent", "required": True, "effect_now": "read_only_check"},
            {"step": "preview_host_targets_without_resolving_paths", "required": True, "effect_now": "metadata_only"},
            {"step": "build_rollback_plan", "required": True, "effect_now": "blocked_until_future_governed_pass"},
            {"step": "write_host_startup_or_shortcut", "required": True, "effect_now": "blocked_until_future_governed_pass"},
            {"step": "write_startup_execution_audit", "required": True, "effect_now": "blocked_until_future_governed_pass"},
        ],
        "required_future_approval_fields": [
            "approval_packet_id",
            "request_digest_sha256",
            "operator_decision: approved",
            "approved_signed_portable_zip_sha256",
            "approved_signing_manifest_sha256",
            "approved_startup_mode",
            "approved_host_targets",
            "approval_scope: one_startup_autostart_proof_only",
        ],
        "rollback_audit_requirements": [
            "future startup proof must dry-run exact host write targets before mutation",
            "future startup proof must reserve the exact-once marker before host startup mutation",
            "future startup proof must write rollback/audit evidence before and after host mutation",
            "future startup proof must verify host state after mutation and provide rollback command/evidence",
            "future startup proof must keep release promotion behind a separate gate",
        ],
        "checks": checks,
        "authority": authority,
        "blocked_authority": [key for key, value in authority.items() if value is False],
        "blockers": blockers,
        "unverified": [
            "No startup/autostart approval artifact was written or mutated in this preview pass.",
            "No approval decision was consumed in this preview pass.",
            "No startup/autostart exact-once marker was reserved in this preview pass.",
            "No host startup paths were resolved or probed.",
            "No host startup, registry, Start Menu, desktop shortcut, release, or canonical mutation was attempted.",
        ],
        "writes_performed": False,
        "next_recommended_pass": next_pass,
    }


def write_startup_autostart_approval_preview_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-startup-autostart-approval-preview"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    preview = report.get("startup_autostart_approval_packet_preview") or {}
    future = report.get("future_approval_artifact") or {}
    marker = report.get("exact_once_marker_contract") or {}
    source = report.get("source_artifacts") or {}
    lines = [
        "# Studio Startup/Autostart Approval Preview Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next: {report.get('next_recommended_pass')}",
        "",
        "## Summary",
        "",
        f"- Signing approval packet: {summary.get('signing_approval_packet_id')}",
        f"- Startup/autostart approval packet: {summary.get('startup_autostart_approval_packet_id')}",
        f"- Request digest: {summary.get('request_digest_sha256')}",
        f"- Approval artifact written: {summary.get('approval_artifact_written')}",
        f"- Approval decision consumed: {summary.get('approval_decision_consumed')}",
        f"- Host path resolution attempted: {summary.get('host_path_resolution_attempted')}",
        f"- Host startup mutation allowed: {summary.get('host_startup_mutation_allowed')}",
        f"- Autostart registration allowed: {summary.get('autostart_registration_allowed')}",
        f"- Registry write allowed: {summary.get('registry_write_allowed')}",
        f"- Shortcut writes allowed: start_menu={summary.get('start_menu_write_allowed')}, desktop={summary.get('desktop_shortcut_write_allowed')}",
        f"- Release promotion allowed: {summary.get('release_promotion_allowed')}",
        "",
        "## Approval Preview",
        "",
        f"- Packet id: {preview.get('approval_packet_id')}",
        f"- Approval artifact path: {future.get('path')}",
        f"- Approval artifact exists: {future.get('exists')}",
        f"- Marker path: {marker.get('path')}",
        f"- Marker exists: {marker.get('exists')}",
        f"- Future write mode: {marker.get('future_write_mode')}",
        "",
        "## Source Artifacts",
        "",
        f"- Signed portable ZIP: {(source.get('signed_portable_zip') or {}).get('path')} sha256={(source.get('signed_portable_zip') or {}).get('sha256')}",
        f"- Signing manifest: {(source.get('signing_manifest') or {}).get('path')} sha256={(source.get('signing_manifest') or {}).get('sha256')}",
        f"- Signing marker: {(source.get('signing_exact_once_marker') or {}).get('path')} sha256={(source.get('signing_exact_once_marker') or {}).get('sha256')}",
        "",
        "## Host Target Previews",
        "",
        *[
            f"- {item.get('id')}: {item.get('status')}; write_allowed={item.get('write_allowed_in_this_pass')}; host_path_resolved={item.get('host_path_resolved_now')}"
            for item in report.get("host_target_previews") or []
        ],
        "",
        "## Dry-Run Plan",
        "",
        *[
            f"- {step.get('step')}: required={step.get('required')} effect_now={step.get('effect_now')}"
            for step in report.get("dry_run_plan") or []
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
        "## Unverified / Deferred",
        "",
        *[f"- {item}" for item in report.get("unverified") or []],
        "",
    ]
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
