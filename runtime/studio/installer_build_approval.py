"""No-execution installer-build approval preview for ChaseOS Studio.

This contract prepares the operator-review packet for a future Studio installer
build. It computes stable approval identity, exact future output paths, dry-run
steps, exact-once marker path, rollback/audit expectations, and authority
boundaries. It does not create approval artifacts, consume approvals, build
installers, sign artifacts, mutate startup/autostart, launch apps, call
providers/connectors, enqueue Agent Bus tasks, mutate Gate, or write canonical
ChaseOS state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.release_readiness_governance import build_studio_release_readiness_governance


MODEL_VERSION = "studio.installer_build_approval.v1"
SURFACE_ID = "studio_installer_build_approval"
DEFAULT_EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views"
APPROVAL_RELATIVE_DIR = Path("07_LOGS") / "Agent-Activity" / "_studio_installer_build_approvals"
IDEMPOTENCY_MARKER_RELATIVE_DIR = APPROVAL_RELATIVE_DIR / "_execution_markers"
INSTALLER_OUTPUT_ROOT = Path(".pytest_tmp_env") / "studio-installer-proof"
NEXT_OPERATOR_REVIEW_PASS = "operator-review-studio-installer-build-approval-packet"
NEXT_APPROVAL_ARTIFACT_PASS = "studio-installer-build-approval-artifact-write"
NEXT_APPROVAL_CONSUMPTION_DRY_RUN_PASS = "studio-installer-build-approval-consumption-dry-run"
NEXT_SIGNING_APPROVAL_PASS = "studio-signing-approval-preview"
BLOCKED_PASS = "studio-governed-installer-build-approval"

BLOCKED_AUTHORITY = {
    "read_only": True,
    "local_only": True,
    "approval_packet_preview_only": True,
    "creates_approval_artifact": False,
    "writes_approval_artifact": False,
    "consumes_approval_decision": False,
    "grants_approvals": False,
    "executes_approval_decisions": False,
    "reserves_idempotency_marker": False,
    "builds_executable": False,
    "builds_installer": False,
    "writes_installer": False,
    "writes_packaging_output_root": False,
    "signs_artifacts": False,
    "reads_signing_certificate": False,
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


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _slug(value: str, fallback: str = "studio-installer-build") -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug or fallback


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _safe_json_path(vault: Path, base_relative: Path, identifier: str) -> Path:
    base = (vault / base_relative).resolve()
    path = (base / f"{_slug(identifier)}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"installer-build approval path escapes base directory: {path}") from exc
    return path


def _file_record(vault: Path, path: Path) -> dict[str, Any]:
    return {
        "path": _relative_to_vault(vault, path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
    }


def _approval_material(
    *,
    packaged_executable_path: str,
    packaged_executable_sha256: str,
    release_governance_status: str,
    requested_by: str,
    operator_id: str,
    installer_format: str,
    output_root: str,
) -> dict[str, Any]:
    return {
        "schema_version": MODEL_VERSION,
        "operation": "studio_installer_build_zip_portable_proof",
        "required_gate": "installer-build-approval",
        "packaged_executable_path": packaged_executable_path,
        "packaged_executable_sha256": packaged_executable_sha256,
        "release_governance_status": release_governance_status,
        "requested_by": requested_by,
        "operator_id": operator_id,
        "installer_format": installer_format,
        "output_root": output_root,
        "approval_effect": "authorizes one future installer-build dry-run/execution pass only after a separate approval artifact is written and consumed",
        "signing_allowed": False,
        "startup_mutation_allowed": False,
        "release_promotion_allowed": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "canonical_writeback_allowed": False,
    }


def _approval_packet_id(material: dict[str, Any]) -> str:
    digest = _sha256(material)
    return f"studio-installer-build-appr-{digest[:16]}"


def _approval_artifact_matches_preview(path: Path, packet_id: str, request_digest: str) -> bool:
    payload = _read_json(path)
    if not payload:
        return False
    return (
        payload.get("record_type") == "studio_installer_build_approval_artifact"
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest_sha256") == request_digest
        and payload.get("operator_decision") == "approved"
        and payload.get("approval_scope") == "one_installer_build_only"
        and payload.get("execution_allowed_in_this_pass") is False
        and payload.get("installer_build_allowed_in_this_pass") is False
    )


def _future_paths(vault: Path, approval_packet_id: str) -> dict[str, dict[str, Any]]:
    output_root = vault / INSTALLER_OUTPUT_ROOT
    return {
        "output_root": {
            "path": _relative_to_vault(vault, output_root),
            "exists": output_root.exists(),
        },
        "portable_zip": _file_record(
            vault,
            output_root / "dist" / "ChaseOS-Studio-portable.zip",
        ),
        "build_manifest": _file_record(
            vault,
            output_root / "manifest" / f"{approval_packet_id}-installer-build-manifest.json",
        ),
        "dry_run_evidence": _file_record(
            vault,
            vault / DEFAULT_EVIDENCE_ROOT / f"{approval_packet_id}-installer-build-dry-run.json",
        ),
        "execution_evidence": _file_record(
            vault,
            vault / DEFAULT_EVIDENCE_ROOT / f"{approval_packet_id}-installer-build-execution.json",
        ),
    }


def _approved_execution_proof_complete(
    vault: Path,
    approval_packet_id: str,
    future_paths: dict[str, dict[str, Any]],
    marker_path: Path,
) -> bool:
    marker_payload = _read_json(marker_path) if marker_path.is_file() else None
    if not (
        marker_payload
        and marker_payload.get("record_type") == "studio_installer_build_execution_marker"
        and marker_payload.get("approval_packet_id") == approval_packet_id
        and marker_payload.get("status") == "studio_installer_build_approved_execution_proof_complete"
    ):
        return False
    for key in ["portable_zip", "build_manifest", "dry_run_evidence", "execution_evidence"]:
        value = future_paths.get(key) or {}
        path_value = str(value.get("path") or "")
        if not path_value or not (vault / path_value).is_file():
            return False
    return True


def build_studio_governed_installer_build_approval(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    requested_by: str = "Codex",
    operator_id: str = "operator",
    installer_format: str = "zip-portable",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a no-execution installer-build approval packet preview."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    release = build_studio_release_readiness_governance(vault, generated_at=timestamp)
    release_ok = bool(release.get("ok"))
    packaged = release.get("evidence_inputs", {}).get("packaged_app") or {}
    executable = packaged.get("executable") or {}
    executable_path = str(executable.get("path") or "")
    executable_exists = bool(executable.get("exists"))
    executable_sha256 = str(packaged.get("sha256") or "")

    explicit_approval_path = _safe_json_path(vault, APPROVAL_RELATIVE_DIR, approval_packet_id) if approval_packet_id else None
    explicit_payload = _read_json(explicit_approval_path) if explicit_approval_path and explicit_approval_path.is_file() else None
    if explicit_payload and explicit_payload.get("record_type") == "studio_installer_build_approval_artifact":
        material = dict(explicit_payload.get("approval_material") or {})
        packet_id = str(approval_packet_id)
        request_digest = str(explicit_payload.get("request_digest_sha256") or _sha256(material))
        approval_path = explicit_approval_path
        executable = dict(explicit_payload.get("approved_packaged_executable") or {})
        executable_path = str(executable.get("path") or material.get("packaged_executable_path") or "")
        executable_sha256 = str(
            explicit_payload.get("approved_packaged_executable_sha256")
            or material.get("packaged_executable_sha256")
            or ""
        )
        executable_exists = bool(executable.get("exists")) or bool(executable_path and executable_sha256)
        installer_format = str(explicit_payload.get("approved_installer_format") or installer_format)
        release_ok = True
        packaged = {"executable": executable, "sha256": executable_sha256}
    else:
        material = _approval_material(
            packaged_executable_path=executable_path,
            packaged_executable_sha256=executable_sha256,
            release_governance_status=str(release.get("status") or ""),
            requested_by=requested_by,
            operator_id=operator_id,
            installer_format=installer_format,
            output_root=INSTALLER_OUTPUT_ROOT.as_posix(),
        )
        packet_id = _approval_packet_id(material)
        request_digest = _sha256(material)
        approval_path = _safe_json_path(vault, APPROVAL_RELATIVE_DIR, packet_id)
    marker_path = _safe_json_path(vault, IDEMPOTENCY_MARKER_RELATIVE_DIR, packet_id)
    future_paths = _future_paths(vault, packet_id)
    output_paths_clear = not any(
        bool(item.get("exists"))
        for key, item in future_paths.items()
        if key != "output_root"
    )
    approval_exists = approval_path.is_file()
    approval_matches = (
        _approval_artifact_matches_preview(approval_path, packet_id, request_digest)
        if approval_exists
        else False
    )
    marker_exists = marker_path.is_file()
    approved_execution_complete = _approved_execution_proof_complete(vault, packet_id, future_paths, marker_path)
    gate_declared = any(
        item.get("id") == "installer-build-approval"
        for item in release.get("approval_requirements") or []
    ) or bool(explicit_payload)

    checks = {
        "release_readiness_governance_ready": release_ok,
        "installer_build_gate_declared": gate_declared,
        "packaged_executable_present": approved_execution_complete or (executable_exists and bool(executable_sha256)),
        "approval_artifact_absent_or_matching": (not approval_exists) or approval_matches,
        "exact_once_marker_absent": not marker_exists,
        "future_output_paths_clear": output_paths_clear,
        "approved_execution_proof_complete": approved_execution_complete,
        "operator_review_required": True,
        "execution_blocked_in_this_pass": True,
    }
    blockers: list[str] = []
    if not checks["release_readiness_governance_ready"]:
        blockers.append("Release-readiness governance is not ready.")
    if not checks["installer_build_gate_declared"]:
        blockers.append("Installer-build governance gate is not declared.")
    if not checks["packaged_executable_present"]:
        blockers.append("Packaged executable path or SHA-256 is missing.")
    if approval_exists and not approval_matches:
        blockers.append("Future installer-build approval artifact path already exists with mismatched content.")
    if marker_exists and not approved_execution_complete:
        blockers.append("Future installer-build exact-once marker path already exists.")
    if not output_paths_clear and not approved_execution_complete:
        blockers.append("Future installer-build output paths are not clear.")

    ok = not blockers
    status = (
        "studio_installer_build_approved_execution_proof_complete"
        if ok and approved_execution_complete
        else
        "installer_build_approval_artifact_present_pending_consumption"
        if ok and approval_matches
        else "ready_for_operator_installer_build_approval_review"
        if ok
        else "blocked_installer_build_approval_preview"
    )
    approval_packet_preview = {
        "record_type": "studio_installer_build_approval_packet_preview",
        "schema_version": MODEL_VERSION,
        "approval_packet_id": packet_id,
        "request_digest_sha256": request_digest,
        "status": "approved_artifact_present" if approval_matches else "preview_only_not_approved",
        "required_gate": "installer-build-approval",
        "requested_by": requested_by,
        "operator_id": operator_id,
        "installer_format": installer_format,
        "source_release_governance_status": release.get("status"),
        "source_release_governance_next": release.get("next_recommended_pass"),
        "packaged_executable": executable,
        "packaged_executable_sha256": executable_sha256,
        "approval_artifact_path": _relative_to_vault(vault, approval_path),
        "approval_artifact_written": approval_matches,
        "approval_decision_consumed": approved_execution_complete,
        "future_single_build_approved": approval_matches,
        "execution_allowed_in_this_pass": False,
        "approval_material": material,
    }
    next_pass = (
        NEXT_SIGNING_APPROVAL_PASS
        if ok and approved_execution_complete
        else NEXT_APPROVAL_CONSUMPTION_DRY_RUN_PASS
        if ok and approval_matches
        else NEXT_OPERATOR_REVIEW_PASS
    )
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "summary": {
            "release_readiness_governance_ready": release_ok,
            "installer_build_gate_declared": checks["installer_build_gate_declared"],
            "approval_packet_id": packet_id,
            "approval_packet_preview_ready": ok,
            "approval_artifact_written": approval_matches,
            "approval_artifact_matching": approval_matches,
            "approval_decision_consumed": approved_execution_complete,
            "approved_execution_proof_complete": approved_execution_complete,
            "execution_allowed": False,
            "installer_build_allowed": False,
            "next_recommended_pass": next_pass if ok else BLOCKED_PASS,
        },
        "source_contracts": {
            "release_readiness_governance": {
                "ok": release_ok,
                "status": release.get("status"),
                "next_recommended_pass": release.get("next_recommended_pass"),
            },
            "packaged_app": packaged,
        },
        "approval_packet_preview": approval_packet_preview,
        "future_approval_artifact": {
            "path": _relative_to_vault(vault, approval_path),
            "exists": approval_exists,
            "matches_current_packet": approval_matches,
            "write_allowed_in_this_pass": False,
            "future_write_pass": None if approval_matches else NEXT_APPROVAL_ARTIFACT_PASS,
        },
        "exact_once_marker_contract": {
            "path": _relative_to_vault(vault, marker_path),
            "exists": marker_exists,
            "reserved_in_this_pass": False,
            "future_write_mode": "exclusive_create_before_installer_build",
            "duplicate_policy": "block_before_any_installer_output_write",
        },
        "future_output_paths": future_paths,
        "dry_run_plan": [
            {
                "step": "verify_approval_artifact",
                "required": True,
                "effect_now": "preview_only",
            },
            {
                "step": "verify_approval_decision_matches_request_digest",
                "required": True,
                "effect_now": "preview_only",
            },
            {
                "step": "verify_exact_once_marker_absent",
                "required": True,
                "effect_now": "read_only_check",
            },
            {
                "step": "validate_output_root_within_workspace",
                "required": True,
                "effect_now": "read_only_path_preview",
            },
            {
                "step": "build_zip_portable_installer",
                "required": True,
                "effect_now": "blocked_until_future_approval_consumption",
            },
            {
                "step": "write_installer_manifest_and_hash_evidence",
                "required": True,
                "effect_now": "blocked_until_future_approval_consumption",
            },
            {
                "step": "cleanup_owned_temp_processes",
                "required": True,
                "effect_now": "no_process_started",
            },
        ],
        "rollback_audit_requirements": [
            "installer output root must be deletable as a single owned directory if the future build fails",
            "future build must write a manifest with output file hashes before any release promotion",
            "future build must write an audit record before and after installer output creation",
            "future build must not touch signing, startup/autostart, registry, Start Menu, desktop shortcut, or release status",
        ],
        "required_future_approval_fields": [
            "approval_packet_id",
            "request_digest_sha256",
            "operator_decision: approved",
            "approved_installer_format",
            "approved_output_root",
            "approved_packaged_executable_sha256",
            "approval_scope: one_installer_build_only",
        ],
        "checks": checks,
        "authority": dict(BLOCKED_AUTHORITY),
        "blocked_authority": [key for key, value in BLOCKED_AUTHORITY.items() if value is False],
        "blockers": blockers,
        "unverified": [
            "No approval artifact was written or mutated in this preview pass.",
            "No new approval decision was consumed in this preview pass.",
            "No exact-once marker was reserved in this preview pass.",
            "No installer build or dry-run execution was attempted in this preview pass.",
            "No signing, startup/autostart, registry, Start Menu, desktop shortcut, release promotion, provider/connector call, Agent Bus write, Gate mutation, workflow execution, or canonical writeback was attempted.",
        ],
        "next_recommended_pass": next_pass if ok else BLOCKED_PASS,
    }


def write_installer_build_approval_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-governed-installer-build-approval"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    preview = report.get("approval_packet_preview") or {}
    marker = report.get("exact_once_marker_contract") or {}
    future = report.get("future_approval_artifact") or {}
    lines = [
        "# Studio Governed Installer Build Approval Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next: {report.get('next_recommended_pass')}",
        "",
        "## Approval Packet Preview",
        "",
        f"- approval_packet_id: {preview.get('approval_packet_id')}",
        f"- request_digest_sha256: {preview.get('request_digest_sha256')}",
        f"- approval_artifact_path: {future.get('path')}",
        f"- approval_artifact_written: {future.get('exists')}",
        f"- exact_once_marker_path: {marker.get('path')}",
        f"- exact_once_marker_exists: {marker.get('exists')}",
        "",
        "## Future Output Paths",
        "",
        *[
            f"- {key}: {value.get('path')} exists={value.get('exists')}"
            for key, value in (report.get("future_output_paths") or {}).items()
        ],
        "",
        "## Dry-Run Plan",
        "",
        *[
            f"- {item.get('step')}: required={item.get('required')} effect_now={item.get('effect_now')}"
            for item in report.get("dry_run_plan") or []
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
