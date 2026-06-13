"""No-execution signing approval preview for ChaseOS Studio.

This contract is the next governed gate after the installer-build approved
execution proof. It inspects the completed portable ZIP, manifest, audit, and
exact-once marker evidence, then prepares a stable operator-review packet for a
future signing proof.

It does not create approval artifacts, consume approvals, read signing
certificates, sign artifacts, write signed outputs, mutate startup/autostart,
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
from runtime.studio.installer_build_approved_execution_proof import (
    COMPLETE_STATUS as INSTALLER_EXECUTION_COMPLETE_STATUS,
    build_studio_installer_build_approved_execution_proof,
)


MODEL_VERSION = "studio.signing_approval_preview.v1"
SURFACE_ID = "studio_signing_approval_preview"
READY_STATUS = "ready_for_operator_studio_signing_approval_review"
PENDING_CONSUMPTION_STATUS = "studio_signing_approval_artifact_present_pending_consumption"
BLOCKED_STATUS = "blocked_studio_signing_approval_preview"
SIGNING_APPROVAL_RELATIVE_DIR = Path("07_LOGS") / "Agent-Activity" / "_studio_signing_approvals"
SIGNING_MARKER_RELATIVE_DIR = SIGNING_APPROVAL_RELATIVE_DIR / "_execution_markers"
SIGNING_OUTPUT_ROOT = Path(".pytest_tmp_env") / "studio-signing-proof"
NEXT_OPERATOR_REVIEW_PASS = "operator-review-studio-signing-approval-packet"
NEXT_SIGNING_CONSUMPTION_DRY_RUN_PASS = "studio-signing-approval-consumption-dry-run"
NEXT_STARTUP_AUTOSTART_APPROVAL_PASS = "studio-startup-autostart-approval-preview"
BLOCKED_PASS = "studio-installer-build-approved-execution-proof"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _slug(value: str, fallback: str = "studio-signing") -> str:
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


def _safe_json_path(vault: Path, base_relative: Path, identifier: str) -> Path:
    base = (vault / base_relative).resolve()
    path = (base / f"{_slug(identifier)}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Studio signing approval path escapes base directory: {path}") from exc
    return path


def _resolve_vault_relative_path(vault: Path, path_value: str) -> Path:
    path = Path(path_value)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"Studio signing preview path escapes vault: {path_value}") from exc
    return resolved


def _file_record(vault: Path, path: Path) -> dict[str, Any]:
    return {
        "path": _relative_to_vault(vault, path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": _sha256_file(path),
    }


def _output_paths(vault: Path, packet_id: str) -> dict[str, dict[str, Any]]:
    output_root = vault / SIGNING_OUTPUT_ROOT
    return {
        "output_root": {
            "path": _relative_to_vault(vault, output_root),
            "exists": output_root.exists(),
        },
        "signed_portable_zip": _file_record(
            vault,
            output_root / "dist" / packet_id / "ChaseOS-Studio-portable-signed.zip",
        ),
        "signing_manifest": _file_record(
            vault,
            output_root / "manifest" / f"{packet_id}-signing-manifest.json",
        ),
        "signing_dry_run_evidence": _file_record(
            vault,
            vault / DEFAULT_EVIDENCE_ROOT / f"{packet_id}-signing-dry-run.json",
        ),
        "signing_execution_evidence": _file_record(
            vault,
            vault / DEFAULT_EVIDENCE_ROOT / f"{packet_id}-signing-execution.json",
        ),
    }


def _approval_material(
    *,
    installer_approval_packet_id: str,
    installer_execution_marker_path: str,
    installer_execution_marker_sha256: str,
    portable_zip_path: str,
    portable_zip_sha256: str,
    installer_manifest_path: str,
    installer_manifest_sha256: str,
    requested_by: str,
    operator_id: str,
    signing_profile: str,
    output_root: str,
) -> dict[str, Any]:
    return {
        "schema_version": MODEL_VERSION,
        "operation": "studio_portable_zip_signing_proof",
        "required_gate": "studio-signing-approval",
        "installer_approval_packet_id": installer_approval_packet_id,
        "installer_execution_marker_path": installer_execution_marker_path,
        "installer_execution_marker_sha256": installer_execution_marker_sha256,
        "portable_zip_path": portable_zip_path,
        "portable_zip_sha256": portable_zip_sha256,
        "installer_manifest_path": installer_manifest_path,
        "installer_manifest_sha256": installer_manifest_sha256,
        "requested_by": requested_by,
        "operator_id": operator_id,
        "signing_profile": signing_profile,
        "output_root": output_root,
        "approval_effect": "authorizes one future signing proof only after a separate approval artifact is written and consumed",
        "certificate_reference_required": True,
        "raw_certificate_values_allowed": False,
        "signing_allowed_in_preview": False,
        "startup_mutation_allowed": False,
        "release_promotion_allowed": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "canonical_writeback_allowed": False,
    }


def _approval_packet_id(material: dict[str, Any]) -> str:
    digest = _sha256(material)
    return f"studio-signing-appr-{digest[:16]}"


def _approval_artifact_matches_preview(path: Path, packet_id: str, request_digest: str) -> bool:
    payload = _read_json(path)
    if not payload:
        return False
    return (
        payload.get("record_type") == "studio_signing_approval_artifact"
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest_sha256") == request_digest
        and payload.get("operator_decision") == "approved"
        and payload.get("approval_scope") == "one_signing_proof_only"
        and payload.get("signing_allowed_in_this_pass") is False
        and payload.get("approval_decision_consumed") is False
    )


def _completed_signing_marker(path: Path, packet_id: str) -> bool:
    payload = _read_json(path)
    return bool(
        payload
        and payload.get("record_type") == "studio_signing_execution_marker"
        and payload.get("approval_packet_id") == packet_id
        and payload.get("status") == "studio_signing_approved_execution_proof_complete"
    )


def _authority() -> dict[str, Any]:
    return {
        **dict(BLOCKED_AUTHORITY),
        "approval_packet_preview_only": True,
        "signing_approval_preview_only": True,
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


def build_studio_signing_approval_preview(
    vault_root: str | Path,
    *,
    installer_approval_packet_id: str | None = None,
    requested_by: str = "Codex",
    operator_id: str = "operator",
    signing_profile: str = "operator-provided-code-signing-certificate",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build the no-execution Studio signing approval preview."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    try:
        installer = build_studio_installer_build_approved_execution_proof(
            vault,
            approval_packet_id=installer_approval_packet_id,
            execute=False,
            generated_at=timestamp,
        )
    except (ValueError, KeyError) as exc:
        installer = {"ok": False, "status": BLOCKED_PASS, "summary": {}, "paths": {}}
        blockers.append(str(exc))

    summary = installer.get("summary") or {}
    paths = installer.get("paths") or {}
    marker_record = paths.get("exact_once_marker") or {}
    portable_record = paths.get("portable_zip") or {}
    manifest_record = paths.get("build_manifest") or {}
    execution_record = paths.get("execution_evidence") or {}
    packet_id = str(summary.get("approval_packet_id") or installer_approval_packet_id or "")
    portable_zip_path = _resolve_vault_relative_path(vault, str(portable_record.get("path") or summary.get("portable_zip_path") or ""))
    manifest_path = _resolve_vault_relative_path(vault, str(manifest_record.get("path") or summary.get("manifest_path") or ""))
    marker_path = _resolve_vault_relative_path(vault, str(marker_record.get("path") or ""))
    portable_sha = str(portable_record.get("sha256") or _sha256_file(portable_zip_path) or "")
    manifest_sha = str(manifest_record.get("sha256") or _sha256_file(manifest_path) or "")
    marker_sha = str(marker_record.get("sha256") or _sha256_file(marker_path) or "")
    material = _approval_material(
        installer_approval_packet_id=packet_id,
        installer_execution_marker_path=_relative_to_vault(vault, marker_path),
        installer_execution_marker_sha256=marker_sha,
        portable_zip_path=_relative_to_vault(vault, portable_zip_path),
        portable_zip_sha256=portable_sha,
        installer_manifest_path=_relative_to_vault(vault, manifest_path),
        installer_manifest_sha256=manifest_sha,
        requested_by=requested_by,
        operator_id=operator_id,
        signing_profile=signing_profile,
        output_root=SIGNING_OUTPUT_ROOT.as_posix(),
    )
    signing_packet_id = _approval_packet_id(material)
    request_digest = _sha256(material)
    approval_path = _safe_json_path(vault, SIGNING_APPROVAL_RELATIVE_DIR, signing_packet_id)
    marker_contract_path = _safe_json_path(vault, SIGNING_MARKER_RELATIVE_DIR, signing_packet_id)
    future_paths = _output_paths(vault, signing_packet_id)
    output_paths_clear = not any(
        bool(item.get("exists"))
        for key, item in future_paths.items()
        if key != "output_root"
    )
    approval_exists = approval_path.is_file()
    approval_matches = _approval_artifact_matches_preview(approval_path, signing_packet_id, request_digest) if approval_exists else False
    signing_execution_complete = (
        _completed_signing_marker(marker_contract_path, signing_packet_id)
        and bool((future_paths.get("signed_portable_zip") or {}).get("exists"))
        and bool((future_paths.get("signing_manifest") or {}).get("exists"))
        and bool((future_paths.get("signing_execution_evidence") or {}).get("exists"))
    )

    checks = {
        "installer_execution_proof_complete": installer.get("status") == INSTALLER_EXECUTION_COMPLETE_STATUS and bool(installer.get("ok")),
        "installer_approval_consumed": bool(summary.get("approval_consumed")),
        "installer_duplicate_execution_blocked": bool(summary.get("duplicate_execution_blocked")),
        "installer_marker_complete": bool(marker_record.get("exists")) and bool(marker_sha),
        "portable_zip_present": portable_zip_path.is_file(),
        "portable_zip_hash_present": bool(portable_sha),
        "installer_manifest_present": manifest_path.is_file(),
        "installer_manifest_hash_present": bool(manifest_sha),
        "installer_execution_evidence_present": bool(execution_record.get("exists")),
        "signing_approval_artifact_absent_or_matching": (not approval_exists) or approval_matches,
        "signing_exact_once_marker_absent": not marker_contract_path.exists(),
        "future_signing_output_paths_clear": output_paths_clear,
        "signing_execution_proof_complete": signing_execution_complete,
        "signing_certificate_not_read": True,
        "signing_execution_blocked_in_this_pass": True,
        "startup_release_blocked_in_this_pass": True,
    }
    if not checks["installer_execution_proof_complete"]:
        blockers.append("Installer-build approved execution proof is not complete.")
    if not checks["installer_approval_consumed"]:
        blockers.append("Installer-build approval has not been consumed by the execution proof.")
    if not checks["portable_zip_present"] or not checks["portable_zip_hash_present"]:
        blockers.append("Portable ZIP proof is missing or unhashed.")
    if not checks["installer_manifest_present"] or not checks["installer_manifest_hash_present"]:
        blockers.append("Installer manifest is missing or unhashed.")
    if approval_exists and not approval_matches:
        blockers.append("Future signing approval artifact path already exists with mismatched content.")
    if marker_contract_path.exists() and not signing_execution_complete:
        blockers.append("Future signing exact-once marker path already exists.")
    if not output_paths_clear and not signing_execution_complete:
        blockers.append("Future signing output paths are not clear.")

    ok = not blockers
    status = (
        "studio_signing_execution_proof_complete"
        if ok and signing_execution_complete
        else PENDING_CONSUMPTION_STATUS
        if ok and approval_matches
        else READY_STATUS
        if ok
        else BLOCKED_STATUS
    )
    next_pass = (
        NEXT_STARTUP_AUTOSTART_APPROVAL_PASS
        if ok and signing_execution_complete
        else NEXT_SIGNING_CONSUMPTION_DRY_RUN_PASS
        if ok and approval_matches
        else NEXT_OPERATOR_REVIEW_PASS
        if ok
        else BLOCKED_PASS
    )
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "summary": {
            "installer_approval_packet_id": packet_id,
            "signing_approval_packet_id": signing_packet_id,
            "request_digest_sha256": request_digest,
            "signing_approval_preview_ready": ok,
            "approval_artifact_written": approval_matches,
            "approval_decision_consumed": signing_execution_complete,
            "signing_execution_proof_complete": signing_execution_complete,
            "signing_allowed": False,
            "signing_certificate_read": False,
            "signed_artifact_written": signing_execution_complete,
            "startup_mutation_allowed": False,
            "release_promotion_allowed": False,
            "writes_performed": False,
            "next_recommended_pass": next_pass,
        },
        "source_contracts": {
            "installer_build_approved_execution_proof": {
                "ok": installer.get("ok"),
                "status": installer.get("status"),
                "next_recommended_pass": installer.get("next_recommended_pass"),
            }
        },
        "signing_approval_packet_preview": {
            "record_type": "studio_signing_approval_packet_preview",
            "schema_version": MODEL_VERSION,
            "approval_packet_id": signing_packet_id,
            "request_digest_sha256": request_digest,
            "status": "approved_artifact_present" if approval_matches else "preview_only_not_approved",
            "required_gate": "studio-signing-approval",
            "requested_by": requested_by,
            "operator_id": operator_id,
            "signing_profile": signing_profile,
            "approval_artifact_path": _relative_to_vault(vault, approval_path),
            "approval_artifact_written": approval_matches,
            "approval_decision_consumed": signing_execution_complete,
            "future_single_signing_proof_approved": approval_matches,
            "signing_allowed_in_this_pass": False,
            "approval_material": material,
        },
        "source_artifacts": {
            "exact_once_marker": _file_record(vault, marker_path),
            "portable_zip": _file_record(vault, portable_zip_path),
            "installer_manifest": _file_record(vault, manifest_path),
            "installer_execution_evidence": {
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
            "completed_by_execution_proof": signing_execution_complete,
            "future_write_mode": "exclusive_create_before_signing_execution",
            "duplicate_policy": "block_before_any_signed_artifact_output_write",
        },
        "future_output_paths": future_paths,
        "dry_run_plan": [
            {"step": "verify_installer_execution_marker", "required": True, "effect_now": "read_only_check"},
            {"step": "verify_portable_zip_hash", "required": True, "effect_now": "read_only_check"},
            {"step": "verify_installer_manifest_hash", "required": True, "effect_now": "read_only_check"},
            {"step": "verify_signing_approval_artifact", "required": True, "effect_now": "preview_only"},
            {"step": "verify_future_signing_marker_absent", "required": True, "effect_now": "read_only_check"},
            {"step": "validate_signing_output_root_within_workspace", "required": True, "effect_now": "read_only_path_preview"},
            {"step": "resolve_code_signing_certificate_reference", "required": True, "effect_now": "blocked_until_future_governed_signing_pass"},
            {"step": "sign_portable_zip_or_inner_executable", "required": True, "effect_now": "blocked_until_future_governed_signing_pass"},
            {"step": "write_signature_manifest_and_verification_evidence", "required": True, "effect_now": "blocked_until_future_governed_signing_pass"},
        ],
        "required_future_approval_fields": [
            "approval_packet_id",
            "request_digest_sha256",
            "operator_decision: approved",
            "approved_unsigned_portable_zip_sha256",
            "approved_installer_manifest_sha256",
            "approved_signing_profile",
            "approved_output_root",
            "approval_scope: one_signing_proof_only",
        ],
        "rollback_audit_requirements": [
            "future signing proof must write only under the approved signing output root",
            "future signing proof must write a signing manifest with signed artifact hashes",
            "future signing proof must not expose raw certificate values or secrets",
            "future signing proof must not mutate startup/autostart, registry, shortcuts, or release status",
            "future signing proof must keep release promotion behind a separate gate",
        ],
        "checks": checks,
        "authority": _authority(),
        "blocked_authority": [key for key, value in _authority().items() if value is False],
        "blockers": blockers,
        "unverified": [
            "No signing approval artifact was written or mutated in this preview pass.",
            "No approval decision was consumed in this preview pass.",
            "No signing exact-once marker was reserved in this preview pass.",
            "No signing certificate or raw credential value was read.",
            "No artifact was signed, verified, launched, installed, promoted, or registered for startup.",
        ],
        "writes_performed": False,
        "next_recommended_pass": next_pass,
    }


def write_signing_approval_preview_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-signing-approval-preview"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    preview = report.get("signing_approval_packet_preview") or {}
    future = report.get("future_approval_artifact") or {}
    marker = report.get("exact_once_marker_contract") or {}
    source = report.get("source_artifacts") or {}
    lines = [
        "# Studio Signing Approval Preview Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next: {report.get('next_recommended_pass')}",
        "",
        "## Signing Packet Preview",
        "",
        f"- signing_approval_packet_id: {summary.get('signing_approval_packet_id')}",
        f"- request_digest_sha256: {summary.get('request_digest_sha256')}",
        f"- installer_approval_packet_id: {summary.get('installer_approval_packet_id')}",
        f"- approval_artifact_path: {future.get('path')}",
        f"- approval_artifact_written: {future.get('exists')}",
        f"- signing_marker_path: {marker.get('path')}",
        f"- signing_marker_exists: {marker.get('exists')}",
        f"- signing_allowed: {summary.get('signing_allowed')}",
        f"- signing_certificate_read: {summary.get('signing_certificate_read')}",
        "",
        "## Source Artifacts",
        "",
        *[
            f"- {key}: {value.get('path')} exists={value.get('exists')} sha256={value.get('sha256')}"
            for key, value in source.items()
            if isinstance(value, dict)
        ],
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
        "",
        "## Operator Launch Reference",
        "",
        "- Native Studio shell: `python -m chaseos studio shell`",
        "- Localhost compatibility harness: `python -m chaseos studio desktop-shell-app --host 127.0.0.1 --port <PORT>`",
        "- Bounded harness smoke without a long-lived server: `python -m chaseos studio desktop-shell-app --host 127.0.0.1 --port <PORT> --smoke --use-requested-port --json`",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "written": True,
        "json_path": _relative_to_vault(vault, json_path),
        "markdown_path": _relative_to_vault(vault, markdown_path),
    }
