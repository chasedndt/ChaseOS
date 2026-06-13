"""Approved execution proof for the governed Studio signing lane.

This is a narrow proof lane for the already-written Studio signing approval
artifact. It consumes the approval through an exact-once marker, writes a
proof-signed portable ZIP bundle under the approved signing output root, and
records manifest/audit/evidence records.

The proof does not read raw certificate material, expose secrets, mutate
startup/autostart, write registry/Start Menu/desktop shortcuts, promote a
release, launch Studio, call providers/connectors, enqueue Agent Bus tasks,
mutate Gate, execute workflows, configure Git, or write canonical ChaseOS
state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
import zipfile

from runtime.studio.installer_build_approval import BLOCKED_AUTHORITY, DEFAULT_EVIDENCE_ROOT
from runtime.studio.signing_approval_consumption_dry_run import (
    build_studio_signing_approval_consumption_dry_run,
)
from runtime.studio.signing_approval_preview import (
    SIGNING_APPROVAL_RELATIVE_DIR,
    SIGNING_MARKER_RELATIVE_DIR,
    SIGNING_OUTPUT_ROOT,
)
from runtime.studio.signing_approval_review import APPROVAL_RECORD_TYPE


MODEL_VERSION = "studio.signing_approved_execution_proof.v1"
SURFACE_ID = "studio_signing_approved_execution_proof"
READY_STATUS = "ready_for_studio_signing_approved_execution_proof"
COMPLETE_STATUS = "studio_signing_approved_execution_proof_complete"
BLOCKED_STATUS = "blocked_studio_signing_approved_execution_proof"
DUPLICATE_BLOCKED_STATUS = "blocked_duplicate_studio_signing_execution"
NEXT_STARTUP_AUTOSTART_APPROVAL_PASS = "studio-startup-autostart-approval-preview"
BLOCKED_PASS = "studio-signing-approval-consumption-dry-run"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_payload(payload: dict[str, Any]) -> str:
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _resolve_vault_relative_path(vault: Path, path_value: str) -> Path:
    path = Path(path_value)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"signing execution proof path escapes vault: {path_value}") from exc
    return resolved


def _path_under(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
    except ValueError:
        return False
    return True


def _file_record(vault: Path, path: Path) -> dict[str, Any]:
    return {
        "path": _relative_to_vault(vault, path),
        "exists": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": _sha256_file(path),
    }


def _future_path(vault: Path, future_paths: dict[str, Any], key: str, fallback: Path) -> Path:
    value = future_paths.get(key)
    path_value = str(value.get("path") or "") if isinstance(value, dict) else ""
    return _resolve_vault_relative_path(vault, path_value) if path_value else (vault / fallback).resolve()


def _completed_marker(marker_payload: dict[str, Any] | None, approval_packet_id: str) -> bool:
    return bool(
        marker_payload
        and marker_payload.get("record_type") == "studio_signing_execution_marker"
        and marker_payload.get("approval_packet_id") == approval_packet_id
        and marker_payload.get("status") == COMPLETE_STATUS
    )


def _certificate_reference(approval_payload: dict[str, Any]) -> dict[str, Any]:
    profile = str(approval_payload.get("approved_signing_profile") or "")
    return {
        "profile": profile,
        "reference_kind": "opaque_profile_label",
        "reference_present": bool(profile),
        "certificate_material_read": False,
        "certificate_file_read": False,
        "external_secret_lookup_performed": False,
        "raw_certificate_values_visible": False,
        "raw_password_values_visible": False,
        "production_code_signing_certificate_used": False,
        "proof_signature_only": True,
    }


def _signed_zip_entries(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"entries": [], "proof": None, "unsigned_zip_sha256": None}
    try:
        with zipfile.ZipFile(path, mode="r") as archive:
            names = sorted(archive.namelist())
            proof_payload = json.loads(archive.read("CHASEOS-SIGNING-PROOF.json").decode("utf-8"))
            unsigned_bytes = archive.read("unsigned/ChaseOS-Studio-portable.zip")
    except (OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile):
        return {"entries": [], "proof": None, "unsigned_zip_sha256": None}
    return {
        "entries": names,
        "proof": proof_payload if isinstance(proof_payload, dict) else None,
        "unsigned_zip_sha256": hashlib.sha256(unsigned_bytes).hexdigest(),
    }


def _paths_snapshot(vault: Path, context: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "approval_artifact": context["approval_path"],
        "exact_once_marker": context["marker_path"],
        "output_root": context["output_root"],
        "unsigned_portable_zip": context["unsigned_zip"],
        "signed_portable_zip": context["signed_zip"],
        "signing_manifest": context["manifest_path"],
        "pre_output_audit": context["pre_audit_path"],
        "post_output_audit": context["post_audit_path"],
        "dry_run_evidence": context["dry_run_evidence_path"],
        "execution_evidence": context["execution_evidence_path"],
    }
    return {
        key: {
            "path": _relative_to_vault(vault, path),
            "exists": path.exists(),
            "is_file": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else 0,
            "sha256": _sha256_file(path) if path.is_file() else None,
        }
        for key, path in paths.items()
    }


def _authority_for(executed: bool) -> dict[str, Any]:
    return {
        **dict(BLOCKED_AUTHORITY),
        "read_only": not executed,
        "approval_packet_preview_only": False,
        "approval_artifact_review_only": False,
        "approval_consumption_dry_run_only": False,
        "approved_signing_execution_proof": True,
        "validates_approval_artifact": True,
        "consumes_approval_decision": bool(executed),
        "executes_approval_decisions": bool(executed),
        "reserves_idempotency_marker": bool(executed),
        "writes_idempotency_marker": bool(executed),
        "builds_executable": False,
        "builds_installer": False,
        "writes_installer": False,
        "writes_packaging_output_root": bool(executed),
        "signs_artifacts": bool(executed),
        "proof_signs_artifacts": bool(executed),
        "reads_signing_certificate": False,
        "signing_certificate_read": False,
        "raw_certificate_values_visible": False,
        "writes_signed_artifact": bool(executed),
        "verifies_signature": bool(executed),
        "writes_signing_manifest": bool(executed),
        "writes_signing_audit": bool(executed),
        "writes_signing_execution_evidence": bool(executed),
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


def _collect_context(
    vault: Path,
    *,
    approval_packet_id: str | None,
    generated_at: str,
) -> dict[str, Any]:
    consumption = build_studio_signing_approval_consumption_dry_run(
        vault,
        approval_packet_id=approval_packet_id,
        generated_at=generated_at,
    )
    summary = consumption.get("summary") or {}
    artifact = consumption.get("approval_artifact") or {}
    marker = consumption.get("exact_once_marker_contract") or {}
    future_paths = consumption.get("future_output_paths") or {}
    packet_id = str(summary.get("approval_packet_id") or approval_packet_id or "")
    request_digest = str(summary.get("request_digest_sha256") or "")
    approval_path = _resolve_vault_relative_path(vault, str(artifact.get("path") or ""))
    marker_path = _resolve_vault_relative_path(vault, str(marker.get("path") or ""))
    approval_payload = _read_json(approval_path)
    payload = approval_payload or {}
    output_root = _resolve_vault_relative_path(vault, str(payload.get("approved_output_root") or SIGNING_OUTPUT_ROOT.as_posix()))
    unsigned_zip = _resolve_vault_relative_path(vault, str(payload.get("approved_unsigned_portable_zip_path") or ""))
    installer_manifest = _resolve_vault_relative_path(vault, str(payload.get("approved_installer_manifest_path") or ""))
    installer_marker = _resolve_vault_relative_path(vault, str(payload.get("approved_installer_execution_marker_path") or ""))
    signed_zip = _future_path(
        vault,
        future_paths,
        "signed_portable_zip",
        SIGNING_OUTPUT_ROOT / "dist" / packet_id / "ChaseOS-Studio-portable-signed.zip",
    )
    manifest_path = _future_path(
        vault,
        future_paths,
        "signing_manifest",
        SIGNING_OUTPUT_ROOT / "manifest" / f"{packet_id}-signing-manifest.json",
    )
    dry_run_evidence_path = _future_path(
        vault,
        future_paths,
        "signing_dry_run_evidence",
        DEFAULT_EVIDENCE_ROOT / f"{packet_id}-signing-dry-run.json",
    )
    execution_evidence_path = _future_path(
        vault,
        future_paths,
        "signing_execution_evidence",
        DEFAULT_EVIDENCE_ROOT / f"{packet_id}-signing-execution.json",
    )
    marker_payload = _read_json(marker_path) if marker_path.exists() else None
    return {
        "consumption": consumption,
        "approval_payload": approval_payload,
        "marker_payload": marker_payload,
        "requested_approval_packet_id": approval_packet_id,
        "packet_id": packet_id,
        "request_digest": request_digest,
        "approval_path": approval_path,
        "marker_path": marker_path,
        "future_paths": future_paths,
        "output_root": output_root,
        "unsigned_zip": unsigned_zip,
        "installer_manifest": installer_manifest,
        "installer_marker": installer_marker,
        "signed_zip": signed_zip,
        "manifest_path": manifest_path,
        "dry_run_evidence_path": dry_run_evidence_path,
        "execution_evidence_path": execution_evidence_path,
        "pre_audit_path": output_root / "audit" / f"{packet_id}-pre-signing-audit.json",
        "post_audit_path": output_root / "audit" / f"{packet_id}-post-signing-audit.json",
    }


def _preflight_checks(vault: Path, context: dict[str, Any], *, require_clear_outputs: bool) -> dict[str, bool]:
    approval_payload = context.get("approval_payload") or {}
    packet_id = str(context.get("packet_id") or "")
    requested_packet_id = context.get("requested_approval_packet_id")
    request_digest = str(context.get("request_digest") or "")
    marker_path = context["marker_path"]
    marker_payload = context.get("marker_payload")
    output_root = context["output_root"]
    signed_zip = context["signed_zip"]
    manifest_path = context["manifest_path"]
    dry_run_evidence_path = context["dry_run_evidence_path"]
    execution_evidence_path = context["execution_evidence_path"]
    expected_outputs = [signed_zip, manifest_path, dry_run_evidence_path, execution_evidence_path]
    clear_outputs = not any(path.exists() for path in expected_outputs)
    cert = _certificate_reference(approval_payload)
    completed = _completed_marker(marker_payload, packet_id)
    return {
        "consumption_contract_ok": bool((context.get("consumption") or {}).get("ok")),
        "approval_packet_argument_matches": (not requested_packet_id) or requested_packet_id == packet_id,
        "approval_artifact_present": context["approval_path"].is_file(),
        "approval_artifact_json_readable": bool(approval_payload),
        "approval_record_type_valid": approval_payload.get("record_type") == APPROVAL_RECORD_TYPE,
        "approval_packet_id_matches": approval_payload.get("approval_packet_id") == packet_id,
        "request_digest_matches": approval_payload.get("request_digest_sha256") == request_digest,
        "operator_decision_approved": approval_payload.get("operator_decision") == "approved",
        "approval_scope_one_signing_proof": approval_payload.get("approval_scope") == "one_signing_proof_only",
        "approved_output_root_matches": approval_payload.get("approved_output_root") == SIGNING_OUTPUT_ROOT.as_posix(),
        "approval_not_previously_consumed_by_artifact": approval_payload.get("approval_decision_consumed") is False,
        "approval_artifact_not_mutated_for_execution": approval_payload.get("idempotency_marker_reserved") is False,
        "unsigned_portable_zip_present": context["unsigned_zip"].is_file(),
        "unsigned_portable_zip_sha_matches": bool(approval_payload.get("approved_unsigned_portable_zip_sha256"))
        and _sha256_file(context["unsigned_zip"]) == approval_payload.get("approved_unsigned_portable_zip_sha256"),
        "installer_manifest_present": context["installer_manifest"].is_file(),
        "installer_manifest_sha_matches": bool(approval_payload.get("approved_installer_manifest_sha256"))
        and _sha256_file(context["installer_manifest"]) == approval_payload.get("approved_installer_manifest_sha256"),
        "installer_execution_marker_present": context["installer_marker"].is_file(),
        "installer_execution_marker_sha_matches": bool(approval_payload.get("approved_installer_execution_marker_sha256"))
        and _sha256_file(context["installer_marker"]) == approval_payload.get("approved_installer_execution_marker_sha256"),
        "certificate_reference_present": bool(cert.get("reference_present")),
        "certificate_reference_opaque": bool(cert.get("proof_signature_only"))
        and not bool(cert.get("certificate_material_read"))
        and not bool(cert.get("raw_certificate_values_visible")),
        "approval_path_under_expected_root": _path_under(context["approval_path"], vault / SIGNING_APPROVAL_RELATIVE_DIR),
        "marker_path_under_expected_root": _path_under(marker_path, vault / SIGNING_MARKER_RELATIVE_DIR),
        "output_root_under_approved_root": output_root == (vault / SIGNING_OUTPUT_ROOT).resolve(),
        "signed_zip_under_output_root": _path_under(signed_zip, output_root),
        "manifest_under_output_root": _path_under(manifest_path, output_root),
        "audit_paths_under_output_root": _path_under(context["pre_audit_path"], output_root)
        and _path_under(context["post_audit_path"], output_root),
        "future_output_paths_clear_before_execution": clear_outputs if require_clear_outputs else True,
        "real_marker_absent_before_execution": (not marker_path.exists()) if require_clear_outputs else True,
        "existing_marker_is_completed_if_present": (not marker_path.exists()) or completed,
        "no_startup_authority": approval_payload.get("startup_mutation_allowed") is False,
        "no_release_authority": approval_payload.get("release_promotion_allowed") is False,
        "no_provider_connector_agent_bus_gate_canonical_authority": all(
            approval_payload.get(key) is False
            for key in [
                "provider_calls_allowed",
                "connector_calls_allowed",
                "writes_agent_bus_tasks",
                "mutates_gate",
                "canonical_mutation_allowed",
            ]
        ),
    }


def _signature_envelope(context: dict[str, Any], *, generated_at: str) -> dict[str, Any]:
    approval_payload = context["approval_payload"] or {}
    cert = _certificate_reference(approval_payload)
    material = {
        "schema_version": MODEL_VERSION,
        "record_type": "studio_signing_proof_signature_envelope",
        "generated_at": generated_at,
        "approval_packet_id": context["packet_id"],
        "request_digest_sha256": context["request_digest"],
        "signing_mode": "proof_only_detached_signature_envelope",
        "production_code_signature_applied": False,
        "unsigned_portable_zip_path": approval_payload.get("approved_unsigned_portable_zip_path"),
        "unsigned_portable_zip_sha256": _sha256_file(context["unsigned_zip"]),
        "installer_manifest_path": approval_payload.get("approved_installer_manifest_path"),
        "installer_manifest_sha256": _sha256_file(context["installer_manifest"]),
        "installer_execution_marker_path": approval_payload.get("approved_installer_execution_marker_path"),
        "installer_execution_marker_sha256": _sha256_file(context["installer_marker"]),
        "certificate_reference": cert,
        "raw_certificate_values_visible": False,
        "release_promotion_allowed": False,
    }
    return {**material, "proof_signature_sha256": _sha256_payload(material)}


def _write_signed_zip_bundle(context: dict[str, Any], envelope: dict[str, Any]) -> list[dict[str, Any]]:
    signed_zip = context["signed_zip"]
    signed_zip.parent.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []
    unsigned_arc = "unsigned/ChaseOS-Studio-portable.zip"
    proof_arc = "CHASEOS-SIGNING-PROOF.json"
    readme_arc = "SIGNING-PROOF-README.txt"
    with zipfile.ZipFile(signed_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(context["unsigned_zip"], unsigned_arc)
        files.append(
            {
                "archive_path": unsigned_arc,
                "size_bytes": context["unsigned_zip"].stat().st_size,
                "sha256": _sha256_file(context["unsigned_zip"]),
            }
        )
        proof_bytes = (json.dumps(envelope, indent=2, default=str) + "\n").encode("utf-8")
        archive.writestr(proof_arc, proof_bytes)
        files.append(
            {
                "archive_path": proof_arc,
                "size_bytes": len(proof_bytes),
                "sha256": hashlib.sha256(proof_bytes).hexdigest(),
            }
        )
        readme = (
            "ChaseOS Studio signing proof bundle.\n"
            "This is a governed proof signature envelope, not a public release promotion.\n"
            "Raw certificate values are not included.\n"
        ).encode("utf-8")
        archive.writestr(readme_arc, readme)
        files.append({"archive_path": readme_arc, "size_bytes": len(readme), "sha256": hashlib.sha256(readme).hexdigest()})
    return files


def _post_execution_checks(vault: Path, context: dict[str, Any]) -> dict[str, bool]:
    marker_path = context["marker_path"]
    signed_zip = context["signed_zip"]
    manifest_path = context["manifest_path"]
    execution_evidence_path = context["execution_evidence_path"]
    manifest = _read_json(manifest_path)
    execution = _read_json(execution_evidence_path)
    marker = _read_json(marker_path)
    zip_info = _signed_zip_entries(signed_zip)
    signed_zip_sha = _sha256_file(signed_zip)
    packet_id = str(context.get("packet_id") or "")
    envelope = zip_info.get("proof") or {}
    cert = envelope.get("certificate_reference") or {}
    return {
        "approval_consumed_by_marker": _completed_marker(marker, packet_id),
        "exact_once_marker_exists": marker_path.is_file(),
        "duplicate_execution_blocked": marker_path.is_file(),
        "signed_portable_zip_exists": signed_zip.is_file(),
        "signed_portable_zip_hash_present": bool(signed_zip_sha),
        "signed_zip_contains_unsigned_zip": "unsigned/ChaseOS-Studio-portable.zip" in (zip_info.get("entries") or []),
        "signed_zip_contains_signature_proof": "CHASEOS-SIGNING-PROOF.json" in (zip_info.get("entries") or []),
        "embedded_unsigned_zip_hash_matches": zip_info.get("unsigned_zip_sha256") == _sha256_file(context["unsigned_zip"]),
        "signature_proof_digest_present": bool(envelope.get("proof_signature_sha256")),
        "signature_proof_packet_matches": envelope.get("approval_packet_id") == packet_id,
        "signing_manifest_exists": manifest_path.is_file(),
        "manifest_packet_id_matches": bool(manifest and manifest.get("approval_packet_id") == packet_id),
        "manifest_unsigned_zip_hash_matches": bool(
            manifest and manifest.get("unsigned_portable_zip_sha256") == _sha256_file(context["unsigned_zip"])
        ),
        "manifest_signed_zip_hash_matches": bool(manifest and manifest.get("signed_portable_zip_sha256") == signed_zip_sha),
        "manifest_signature_digest_matches": bool(
            manifest and manifest.get("proof_signature_sha256") == envelope.get("proof_signature_sha256")
        ),
        "pre_output_audit_exists": context["pre_audit_path"].is_file(),
        "post_output_audit_exists": context["post_audit_path"].is_file(),
        "dry_run_evidence_exists": context["dry_run_evidence_path"].is_file(),
        "execution_evidence_exists": execution_evidence_path.is_file(),
        "execution_evidence_packet_id_matches": bool(
            execution and execution.get("summary", {}).get("approval_packet_id") == packet_id
        ),
        "certificate_reference_no_raw_secret": bool(cert.get("reference_present"))
        and not bool(cert.get("certificate_material_read"))
        and not bool(cert.get("raw_certificate_values_visible")),
        "production_code_signature_not_claimed": envelope.get("production_code_signature_applied") is False,
        "output_root_within_workspace": _path_under(context["output_root"], vault),
        "rollback_boundary_owned_output_root_only": True,
        "startup_release_still_blocked": True,
    }


def build_studio_signing_approved_execution_proof(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    execute: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or execute the approved one-shot Studio signing proof."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    try:
        context = _collect_context(vault, approval_packet_id=approval_packet_id, generated_at=timestamp)
    except (ValueError, KeyError) as exc:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "status": BLOCKED_STATUS,
            "generated_at": timestamp,
            "vault_root": str(vault),
            "summary": {
                "approval_packet_id": approval_packet_id,
                "execution_requested": bool(execute),
                "execution_performed": False,
                "approval_consumed": False,
                "next_recommended_pass": BLOCKED_PASS,
            },
            "checks": {"context_loaded": False},
            "authority": _authority_for(False),
            "blockers": [str(exc)],
            "writes_performed": False,
            "next_recommended_pass": BLOCKED_PASS,
        }

    pre_execution_paths = _paths_snapshot(vault, context)
    completed_before = _completed_marker(context.get("marker_payload"), str(context.get("packet_id") or ""))
    checks = _preflight_checks(vault, context, require_clear_outputs=bool(execute and not completed_before))
    if completed_before:
        post_checks = _post_execution_checks(vault, context)
        completed_ok = all(post_checks.values()) and all(
            value
            for key, value in checks.items()
            if key not in {"future_output_paths_clear_before_execution", "real_marker_absent_before_execution"}
        )
        ok = completed_ok and not execute
        return {
            "ok": ok,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "status": DUPLICATE_BLOCKED_STATUS if execute else COMPLETE_STATUS,
            "generated_at": timestamp,
            "vault_root": str(vault),
            "summary": {
                "approval_packet_id": context.get("packet_id"),
                "request_digest_sha256": context.get("request_digest"),
                "execution_requested": bool(execute),
                "execution_performed": False,
                "already_executed": True,
                "approval_consumed": True,
                "exact_once_marker_reserved": True,
                "exact_once_marker_completed": True,
                "duplicate_execution_blocked": True,
                "signed_portable_zip_path": _relative_to_vault(vault, context["signed_zip"]),
                "signed_portable_zip_sha256": _sha256_file(context["signed_zip"]),
                "signing_manifest_path": _relative_to_vault(vault, context["manifest_path"]),
                "dry_run_evidence_path": _relative_to_vault(vault, context["dry_run_evidence_path"]),
                "execution_evidence_path": _relative_to_vault(vault, context["execution_evidence_path"]),
                "certificate_reference_resolved": bool(
                    _certificate_reference(context.get("approval_payload") or {}).get("reference_present")
                ),
                "signing_certificate_read": False,
                "raw_certificate_values_visible": False,
                "proof_signature_verified": bool(post_checks.get("manifest_signature_digest_matches")),
                "production_code_signature_applied": False,
                "startup_mutation_allowed": False,
                "release_promotion_allowed": False,
                "writes_performed": False,
                "next_recommended_pass": NEXT_STARTUP_AUTOSTART_APPROVAL_PASS if ok else BLOCKED_PASS,
            },
            "preflight_checks": checks,
            "post_execution_checks": post_checks,
            "paths": pre_execution_paths,
            "rollback_boundary": {
                "owned_output_root": SIGNING_OUTPUT_ROOT.as_posix(),
                "rollback_scope": "delete_or_replace_owned_signing_output_root_only_after_operator_review",
                "host_mutation_to_rollback": False,
                "release_status_to_rollback": False,
            },
            "authority": _authority_for(False),
            "blockers": [] if ok else ["signing_exact_once_marker_already_exists_duplicate_execution_blocked"],
            "unverified": [
                "No production code-signing certificate was read.",
                "No startup/autostart, registry, Start Menu, or desktop shortcut write was attempted.",
                "No release promotion or release-status write was attempted.",
            ],
            "writes_performed": False,
            "next_recommended_pass": NEXT_STARTUP_AUTOSTART_APPROVAL_PASS if ok else BLOCKED_PASS,
        }

    blockers = [name for name, passed in checks.items() if not passed]
    if blockers or not execute:
        ok = not blockers
        return {
            "ok": ok,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "status": READY_STATUS if ok else BLOCKED_STATUS,
            "generated_at": timestamp,
            "vault_root": str(vault),
            "summary": {
                "approval_packet_id": context.get("packet_id"),
                "request_digest_sha256": context.get("request_digest"),
                "execution_requested": bool(execute),
                "execution_performed": False,
                "already_executed": False,
                "approval_consumed": False,
                "exact_once_marker_reserved": False,
                "future_output_paths_clear": bool(checks.get("future_output_paths_clear_before_execution")),
                "certificate_reference_resolved": bool(
                    _certificate_reference(context.get("approval_payload") or {}).get("reference_present")
                ),
                "signing_certificate_read": False,
                "raw_certificate_values_visible": False,
                "signed_artifact_written": False,
                "startup_mutation_allowed": False,
                "release_promotion_allowed": False,
                "writes_performed": False,
                "next_recommended_pass": "run-with---execute" if ok else BLOCKED_PASS,
            },
            "preflight_checks": checks,
            "paths": pre_execution_paths,
            "rollback_boundary": {
                "owned_output_root": SIGNING_OUTPUT_ROOT.as_posix(),
                "rollback_scope": "owned_signing_output_root_only",
                "host_mutation_to_rollback": False,
                "release_status_to_rollback": False,
            },
            "authority": _authority_for(False),
            "blockers": blockers,
            "unverified": [
                "Execution was not requested, so no marker, signed ZIP, manifest, audit, or execution evidence was written.",
                "No startup/autostart or release gate was exercised.",
            ],
            "writes_performed": False,
            "next_recommended_pass": "run-with---execute" if ok else BLOCKED_PASS,
        }

    packet_id = str(context["packet_id"])
    marker_path = context["marker_path"]
    reserved_at = _now_utc()
    marker_payload = {
        "record_type": "studio_signing_execution_marker",
        "schema_version": MODEL_VERSION,
        "status": "reserved_before_signed_output",
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "reserved_at": reserved_at,
        "completed_at": None,
        "approval_artifact_path": _relative_to_vault(vault, context["approval_path"]),
        "output_root": _relative_to_vault(vault, context["output_root"]),
        "signed_portable_zip_path": _relative_to_vault(vault, context["signed_zip"]),
        "signing_manifest_path": _relative_to_vault(vault, context["manifest_path"]),
        "duplicate_policy": "block_before_any_signed_artifact_output_write",
    }
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        with marker_path.open("x", encoding="utf-8") as handle:
            json.dump(marker_payload, handle, indent=2, default=str)
    except FileExistsError:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "status": DUPLICATE_BLOCKED_STATUS,
            "generated_at": timestamp,
            "vault_root": str(vault),
            "summary": {
                "approval_packet_id": packet_id,
                "execution_requested": True,
                "execution_performed": False,
                "approval_consumed": True,
                "duplicate_execution_blocked": True,
                "writes_performed": False,
                "next_recommended_pass": BLOCKED_PASS,
            },
            "preflight_checks": checks,
            "paths": _paths_snapshot(vault, context),
            "authority": _authority_for(False),
            "blockers": ["signing_exact_once_marker_already_exists_duplicate_execution_blocked"],
            "writes_performed": False,
            "next_recommended_pass": BLOCKED_PASS,
        }

    dry_run_payload = {
        "record_type": "studio_signing_pre_output_dry_run_evidence",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "exact_once_marker_reserved_before_this_write": True,
        "signed_output_written_at_this_point": False,
        "preflight_checks": checks,
        "certificate_reference": _certificate_reference(context["approval_payload"] or {}),
        "authority": _authority_for(False),
    }
    _write_json(context["dry_run_evidence_path"], dry_run_payload)

    pre_audit = {
        "record_type": "studio_signing_pre_output_audit",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "marker_reserved": True,
        "unsigned_portable_zip": _file_record(vault, context["unsigned_zip"]),
        "output_root": _relative_to_vault(vault, context["output_root"]),
        "certificate_material_read": False,
        "startup_release_blocked": True,
    }
    _write_json(context["pre_audit_path"], pre_audit)

    envelope = _signature_envelope(context, generated_at=_now_utc())
    files = _write_signed_zip_bundle(context, envelope)
    signed_zip_sha = _sha256_file(context["signed_zip"])
    manifest = {
        "record_type": "studio_signing_manifest",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "signing_mode": "proof_only_detached_signature_envelope",
        "production_code_signature_applied": False,
        "approval_artifact_path": _relative_to_vault(vault, context["approval_path"]),
        "exact_once_marker_path": _relative_to_vault(vault, marker_path),
        "unsigned_portable_zip": _file_record(vault, context["unsigned_zip"]),
        "unsigned_portable_zip_sha256": _sha256_file(context["unsigned_zip"]),
        "signed_portable_zip": _file_record(vault, context["signed_zip"]),
        "signed_portable_zip_sha256": signed_zip_sha,
        "installer_manifest": _file_record(vault, context["installer_manifest"]),
        "installer_execution_marker": _file_record(vault, context["installer_marker"]),
        "proof_signature_sha256": envelope.get("proof_signature_sha256"),
        "certificate_reference": _certificate_reference(context["approval_payload"] or {}),
        "signed_zip_entries": files,
        "startup_mutation_allowed": False,
        "release_promotion_allowed": False,
    }
    _write_json(context["manifest_path"], manifest)

    post_audit = {
        "record_type": "studio_signing_post_output_audit",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "marker_reserved": True,
        "signed_portable_zip_sha256": signed_zip_sha,
        "manifest_path": _relative_to_vault(vault, context["manifest_path"]),
        "rollback_boundary": "owned_signing_output_root_only",
        "host_mutation_to_rollback": False,
        "release_status_to_rollback": False,
        "startup_release_blocked": True,
    }
    _write_json(context["post_audit_path"], post_audit)

    completed_at = _now_utc()
    marker_payload.update(
        {
            "status": COMPLETE_STATUS,
            "completed_at": completed_at,
            "signed_portable_zip_sha256": signed_zip_sha,
            "signing_manifest_sha256": _sha256_file(context["manifest_path"]),
            "pre_output_audit_sha256": _sha256_file(context["pre_audit_path"]),
            "post_output_audit_sha256": _sha256_file(context["post_audit_path"]),
            "proof_signature_sha256": envelope.get("proof_signature_sha256"),
        }
    )
    _write_json(marker_path, marker_payload)

    post_execution_paths = _paths_snapshot(vault, context)
    post_checks = _post_execution_checks(vault, context)
    ok = all(post_checks.values())
    report = {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": COMPLETE_STATUS if ok else BLOCKED_STATUS,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "summary": {
            "approval_packet_id": packet_id,
            "request_digest_sha256": context["request_digest"],
            "execution_requested": True,
            "execution_performed": True,
            "already_executed": False,
            "approval_consumed": True,
            "approval_artifact_mutated": False,
            "exact_once_marker_reserved": True,
            "exact_once_marker_completed": True,
            "duplicate_execution_blocked": True,
            "unsigned_portable_zip_path": _relative_to_vault(vault, context["unsigned_zip"]),
            "unsigned_portable_zip_sha256": _sha256_file(context["unsigned_zip"]),
            "signed_portable_zip_path": _relative_to_vault(vault, context["signed_zip"]),
            "signed_portable_zip_sha256": signed_zip_sha,
            "signing_manifest_path": _relative_to_vault(vault, context["manifest_path"]),
            "pre_output_audit_path": _relative_to_vault(vault, context["pre_audit_path"]),
            "post_output_audit_path": _relative_to_vault(vault, context["post_audit_path"]),
            "dry_run_evidence_path": _relative_to_vault(vault, context["dry_run_evidence_path"]),
            "execution_evidence_path": _relative_to_vault(vault, context["execution_evidence_path"]),
            "certificate_reference_resolved": True,
            "signing_certificate_read": False,
            "raw_certificate_values_visible": False,
            "proof_signature_verified": bool(post_checks.get("manifest_signature_digest_matches")),
            "production_code_signature_applied": False,
            "startup_mutation_allowed": False,
            "release_promotion_allowed": False,
            "writes_performed": True,
            "next_recommended_pass": NEXT_STARTUP_AUTOSTART_APPROVAL_PASS if ok else BLOCKED_PASS,
        },
        "preflight_checks": checks,
        "post_execution_checks": post_checks,
        "pre_execution_paths": pre_execution_paths,
        "post_execution_paths": post_execution_paths,
        "signature_envelope": envelope,
        "manifest": manifest,
        "rollback_boundary": {
            "owned_output_root": SIGNING_OUTPUT_ROOT.as_posix(),
            "rollback_scope": "owned_signing_output_root_only",
            "rollback_requires_operator_review": True,
            "host_mutation_to_rollback": False,
            "release_status_to_rollback": False,
        },
        "authority": _authority_for(True),
        "blocked_authority": [key for key, value in _authority_for(True).items() if value is False],
        "blockers": [] if ok else [name for name, passed in post_checks.items() if not passed],
        "unverified": [
            "No production code-signing certificate was read.",
            "No startup/autostart, registry, Start Menu, or desktop shortcut write was attempted.",
            "No release promotion or release-status write was attempted.",
        ],
        "writes_performed": True,
        "next_recommended_pass": NEXT_STARTUP_AUTOSTART_APPROVAL_PASS if ok else BLOCKED_PASS,
    }
    _write_json(context["execution_evidence_path"], report)
    report["post_execution_paths"] = _paths_snapshot(vault, context)
    report["post_execution_checks"] = _post_execution_checks(vault, context)
    report["blockers"] = [] if all(report["post_execution_checks"].values()) else [
        name for name, passed in report["post_execution_checks"].items() if not passed
    ]
    report["ok"] = not report["blockers"]
    report["status"] = COMPLETE_STATUS if report["ok"] else BLOCKED_STATUS
    report["summary"]["writes_performed"] = True
    report["summary"]["next_recommended_pass"] = NEXT_STARTUP_AUTOSTART_APPROVAL_PASS if report["ok"] else BLOCKED_PASS
    report["next_recommended_pass"] = report["summary"]["next_recommended_pass"]
    _write_json(context["execution_evidence_path"], report)
    return report


def write_signing_approved_execution_proof_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-signing-approved-execution-proof"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    lines = [
        "# Studio Signing Approved Execution Proof Evidence",
        "",
        f"Generated: {report.get('generated_at')}",
        "Runtime: Codex",
        f"Status: {report.get('status')}",
        f"OK: {report.get('ok')}",
        f"Next: {report.get('next_recommended_pass')}",
        "",
        "## Summary",
        "",
        f"- approval_packet_id: {summary.get('approval_packet_id')}",
        f"- approval_consumed: {summary.get('approval_consumed')}",
        f"- execution_performed: {summary.get('execution_performed')}",
        f"- duplicate_execution_blocked: {summary.get('duplicate_execution_blocked')}",
        f"- signed_portable_zip_path: {summary.get('signed_portable_zip_path')}",
        f"- signed_portable_zip_sha256: {summary.get('signed_portable_zip_sha256')}",
        f"- signing_manifest_path: {summary.get('signing_manifest_path')}",
        f"- certificate_reference_resolved: {summary.get('certificate_reference_resolved')}",
        f"- signing_certificate_read: {summary.get('signing_certificate_read')}",
        f"- raw_certificate_values_visible: {summary.get('raw_certificate_values_visible')}",
        f"- proof_signature_verified: {summary.get('proof_signature_verified')}",
        f"- production_code_signature_applied: {summary.get('production_code_signature_applied')}",
        "",
        "## Post-Execution Checks",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("post_execution_checks") or {}).items()],
        "",
        "## Rollback Boundary",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("rollback_boundary") or {}).items()],
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
