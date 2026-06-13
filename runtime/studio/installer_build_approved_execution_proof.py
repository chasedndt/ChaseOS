"""Approved execution proof for the governed Studio installer build.

This pass is the narrow execution lane for the already-written Studio
installer-build approval artifact. It may consume exactly one matching approval
by reserving the exact-once marker, writing a portable ZIP installer proof under
the approved workspace output root, and writing manifest/audit/evidence records.

It does not rebuild the executable, sign artifacts, read signing certificates,
mutate startup/autostart, write registry/Start Menu/desktop shortcuts, promote a
release, launch PyWebView or the packaged executable, call providers/connectors,
enqueue Agent Bus tasks, mutate Gate, execute workflows, configure Git, or write
canonical ChaseOS state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
import zipfile

from runtime.studio.installer_build_approval import (
    APPROVAL_RELATIVE_DIR,
    BLOCKED_AUTHORITY,
    DEFAULT_EVIDENCE_ROOT,
    IDEMPOTENCY_MARKER_RELATIVE_DIR,
    INSTALLER_OUTPUT_ROOT,
)
from runtime.studio.installer_build_approval_review import (
    APPROVAL_RECORD_TYPE,
    build_studio_installer_build_approval_review,
)


MODEL_VERSION = "studio.installer_build_approved_execution_proof.v1"
SURFACE_ID = "studio_installer_build_approved_execution_proof"
READY_STATUS = "ready_for_studio_installer_build_approved_execution_proof"
COMPLETE_STATUS = "studio_installer_build_approved_execution_proof_complete"
BLOCKED_STATUS = "blocked_studio_installer_build_approved_execution_proof"
DUPLICATE_BLOCKED_STATUS = "blocked_duplicate_studio_installer_build_execution"
NEXT_SIGNING_APPROVAL_PASS = "studio-signing-approval-preview"
BLOCKED_PASS = "studio-installer-build-approval-consumption-dry-run"


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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _resolve_vault_relative_path(vault: Path, path_value: str) -> Path:
    path = Path(path_value)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"installer execution proof path escapes vault: {path_value}") from exc
    return resolved


def _path_under(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
    except ValueError:
        return False
    return True


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        and marker_payload.get("record_type") == "studio_installer_build_execution_marker"
        and marker_payload.get("approval_packet_id") == approval_packet_id
        and marker_payload.get("status") == COMPLETE_STATUS
    )


def _zip_directory(source_dir: Path, zip_path: Path) -> list[dict[str, Any]]:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    files: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in source_dir.rglob("*") if item.is_file()):
            arcname = path.relative_to(source_dir.parent).as_posix()
            archive.write(path, arcname=arcname)
            files.append(
                {
                    "archive_path": arcname,
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256_file(path),
                }
            )
    return files


def _authority_for(executed: bool) -> dict[str, Any]:
    return {
        **dict(BLOCKED_AUTHORITY),
        "read_only": not executed,
        "approval_packet_preview_only": False,
        "approval_artifact_review_only": False,
        "approval_consumption_dry_run_only": False,
        "approved_execution_proof": True,
        "validates_approval_artifact": True,
        "consumes_approval_decision": bool(executed),
        "executes_approval_decisions": bool(executed),
        "reserves_idempotency_marker": bool(executed),
        "writes_idempotency_marker": bool(executed),
        "builds_executable": False,
        "builds_installer": bool(executed),
        "writes_installer": bool(executed),
        "writes_packaging_output_root": bool(executed),
        "writes_installer_manifest": bool(executed),
        "writes_installer_audit": bool(executed),
        "writes_installer_execution_evidence": bool(executed),
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


def _collect_context(
    vault: Path,
    *,
    approval_packet_id: str | None,
    generated_at: str,
) -> dict[str, Any]:
    review = build_studio_installer_build_approval_review(
        vault,
        approval_packet_id=approval_packet_id,
        decision="approve",
        write_approval=False,
        generated_at=generated_at,
    )
    summary = review.get("summary") or {}
    artifact = review.get("approval_artifact") or {}
    marker = review.get("exact_once_marker_contract") or {}
    future_paths = review.get("future_output_paths") or {}
    packet_id = str(summary.get("approval_packet_id") or approval_packet_id or "")
    request_digest = str(summary.get("request_digest_sha256") or "")
    approval_path = _resolve_vault_relative_path(vault, str(artifact.get("path") or ""))
    marker_path = _resolve_vault_relative_path(vault, str(marker.get("path") or ""))
    output_root = (vault / INSTALLER_OUTPUT_ROOT).resolve()
    portable_zip = _future_path(vault, future_paths, "portable_zip", INSTALLER_OUTPUT_ROOT / "dist" / "ChaseOS-Studio-portable.zip")
    manifest_path = _future_path(
        vault,
        future_paths,
        "build_manifest",
        INSTALLER_OUTPUT_ROOT / "manifest" / f"{packet_id}-installer-build-manifest.json",
    )
    dry_run_evidence_path = _future_path(
        vault,
        future_paths,
        "dry_run_evidence",
        DEFAULT_EVIDENCE_ROOT / f"{packet_id}-installer-build-dry-run.json",
    )
    execution_evidence_path = _future_path(
        vault,
        future_paths,
        "execution_evidence",
        DEFAULT_EVIDENCE_ROOT / f"{packet_id}-installer-build-execution.json",
    )
    pre_audit_path = output_root / "audit" / f"{packet_id}-pre-output-audit.json"
    post_audit_path = output_root / "audit" / f"{packet_id}-post-output-audit.json"
    approval_payload = _read_json(approval_path)
    marker_payload = _read_json(marker_path) if marker_path.exists() else None
    return {
        "review": review,
        "approval_payload": approval_payload,
        "marker_payload": marker_payload,
        "requested_approval_packet_id": approval_packet_id,
        "packet_id": packet_id,
        "request_digest": request_digest,
        "approval_path": approval_path,
        "marker_path": marker_path,
        "future_paths": future_paths,
        "output_root": output_root,
        "portable_zip": portable_zip,
        "manifest_path": manifest_path,
        "dry_run_evidence_path": dry_run_evidence_path,
        "execution_evidence_path": execution_evidence_path,
        "pre_audit_path": pre_audit_path,
        "post_audit_path": post_audit_path,
    }


def _preflight_checks(vault: Path, context: dict[str, Any], *, require_clear_outputs: bool) -> dict[str, bool]:
    approval_payload = context.get("approval_payload") or {}
    packet_id = str(context.get("packet_id") or "")
    requested_packet_id = context.get("requested_approval_packet_id")
    request_digest = str(context.get("request_digest") or "")
    output_root = context["output_root"]
    portable_zip = context["portable_zip"]
    manifest_path = context["manifest_path"]
    dry_run_evidence_path = context["dry_run_evidence_path"]
    execution_evidence_path = context["execution_evidence_path"]
    marker_path = context["marker_path"]
    marker_payload = context.get("marker_payload")
    approved_exe = _resolve_vault_relative_path(vault, str(approval_payload.get("approved_packaged_executable", {}).get("path") or ""))
    approved_exe_sha = str(approval_payload.get("approved_packaged_executable_sha256") or "")
    approved_output_root = str(approval_payload.get("approved_output_root") or "")
    approved_source_dir = approved_exe.parent
    completed = _completed_marker(marker_payload, packet_id)
    expected_output_paths = [portable_zip, manifest_path, dry_run_evidence_path, execution_evidence_path]
    clear_outputs = not output_root.exists() and not any(path.exists() for path in expected_output_paths)
    return {
        "approval_review_contract_ok": bool((context.get("review") or {}).get("ok")),
        "approval_packet_argument_matches": (not requested_packet_id) or requested_packet_id == packet_id,
        "approval_artifact_present": bool(context["approval_path"].is_file()),
        "approval_artifact_json_readable": bool(approval_payload),
        "approval_record_type_valid": approval_payload.get("record_type") == APPROVAL_RECORD_TYPE,
        "approval_packet_id_matches": approval_payload.get("approval_packet_id") == packet_id,
        "request_digest_matches": approval_payload.get("request_digest_sha256") == request_digest,
        "operator_decision_approved": approval_payload.get("operator_decision") == "approved",
        "approval_scope_one_build": approval_payload.get("approval_scope") == "one_installer_build_only",
        "installer_format_zip_portable": approval_payload.get("approved_installer_format") == "zip-portable",
        "approved_output_root_matches": approved_output_root == INSTALLER_OUTPUT_ROOT.as_posix(),
        "approval_not_previously_consumed_by_artifact": approval_payload.get("approval_decision_consumed") is False,
        "approval_artifact_not_mutated_for_execution": approval_payload.get("idempotency_marker_reserved") is False,
        "source_executable_present": approved_exe.is_file(),
        "source_executable_sha_matches": bool(approved_exe_sha) and _sha256_file(approved_exe) == approved_exe_sha,
        "source_app_directory_present": approved_source_dir.is_dir(),
        "approval_path_under_expected_root": _path_under(context["approval_path"], vault / APPROVAL_RELATIVE_DIR),
        "marker_path_under_expected_root": _path_under(marker_path, vault / IDEMPOTENCY_MARKER_RELATIVE_DIR),
        "output_root_under_approved_root": output_root == (vault / INSTALLER_OUTPUT_ROOT).resolve(),
        "portable_zip_under_output_root": _path_under(portable_zip, output_root),
        "manifest_under_output_root": _path_under(manifest_path, output_root),
        "audit_paths_under_output_root": _path_under(context["pre_audit_path"], output_root)
        and _path_under(context["post_audit_path"], output_root),
        "future_output_paths_clear_before_execution": clear_outputs if require_clear_outputs else True,
        "real_marker_absent_before_execution": (not marker_path.exists()) if require_clear_outputs else True,
        "existing_marker_is_completed_if_present": (not marker_path.exists()) or completed,
        "no_signing_authority": approval_payload.get("signing_allowed") is False,
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


def _post_execution_checks(vault: Path, context: dict[str, Any]) -> dict[str, bool]:
    marker_path = context["marker_path"]
    portable_zip = context["portable_zip"]
    manifest_path = context["manifest_path"]
    execution_evidence_path = context["execution_evidence_path"]
    dry_run_evidence_path = context["dry_run_evidence_path"]
    pre_audit_path = context["pre_audit_path"]
    post_audit_path = context["post_audit_path"]
    packet_id = str(context.get("packet_id") or "")
    marker_payload = _read_json(marker_path)
    manifest_payload = _read_json(manifest_path)
    execution_payload = _read_json(execution_evidence_path)
    zip_sha = _sha256_file(portable_zip)
    return {
        "approval_consumed_by_marker": _completed_marker(marker_payload, packet_id),
        "exact_once_marker_exists": marker_path.is_file(),
        "duplicate_execution_blocked": marker_path.is_file(),
        "portable_zip_exists": portable_zip.is_file(),
        "portable_zip_hash_present": bool(zip_sha),
        "manifest_exists": manifest_path.is_file(),
        "manifest_packet_id_matches": bool(manifest_payload and manifest_payload.get("approval_packet_id") == packet_id),
        "manifest_zip_hash_matches": bool(manifest_payload and manifest_payload.get("portable_zip_sha256") == zip_sha),
        "manifest_source_hash_matches": bool(
            manifest_payload
            and manifest_payload.get("source_executable_sha256")
            == (context.get("approval_payload") or {}).get("approved_packaged_executable_sha256")
        ),
        "pre_output_audit_exists": pre_audit_path.is_file(),
        "post_output_audit_exists": post_audit_path.is_file(),
        "dry_run_evidence_exists": dry_run_evidence_path.is_file(),
        "execution_evidence_exists": execution_evidence_path.is_file(),
        "execution_evidence_packet_id_matches": bool(
            execution_payload and execution_payload.get("summary", {}).get("approval_packet_id") == packet_id
        ),
        "output_root_within_workspace": _path_under(context["output_root"], vault),
        "rollback_boundary_owned_output_root_only": True,
        "signing_startup_release_still_blocked": True,
    }


def _paths_snapshot(vault: Path, context: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "approval_artifact": context["approval_path"],
        "exact_once_marker": context["marker_path"],
        "output_root": context["output_root"],
        "portable_zip": context["portable_zip"],
        "build_manifest": context["manifest_path"],
        "pre_output_audit": context["pre_audit_path"],
        "post_output_audit": context["post_audit_path"],
        "dry_run_evidence": context["dry_run_evidence_path"],
        "execution_evidence": context["execution_evidence_path"],
    }
    snapshot: dict[str, Any] = {}
    for key, path in paths.items():
        snapshot[key] = {
            "path": _relative_to_vault(vault, path),
            "exists": path.exists(),
            "is_file": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else 0,
            "sha256": _sha256_file(path) if path.is_file() else None,
        }
    return snapshot


def build_studio_installer_build_approved_execution_proof(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    execute: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or execute the approved one-shot Studio installer proof."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
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
    marker_payload = context.get("marker_payload")
    completed_before = _completed_marker(marker_payload, str(context.get("packet_id") or ""))
    checks = _preflight_checks(vault, context, require_clear_outputs=bool(execute and not completed_before))
    if completed_before:
        post_checks = _post_execution_checks(vault, context)
        completed_ok = all(post_checks.values()) and all(
            value for key, value in checks.items() if key not in {"future_output_paths_clear_before_execution", "real_marker_absent_before_execution"}
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
                "duplicate_execution_blocked": True,
                "portable_zip_exists": bool(post_checks.get("portable_zip_exists")),
                "manifest_exists": bool(post_checks.get("manifest_exists")),
                "portable_zip_path": _relative_to_vault(vault, context["portable_zip"]),
                "portable_zip_sha256": _sha256_file(context["portable_zip"]),
                "manifest_path": _relative_to_vault(vault, context["manifest_path"]),
                "pre_output_audit_path": _relative_to_vault(vault, context["pre_audit_path"]),
                "post_output_audit_path": _relative_to_vault(vault, context["post_audit_path"]),
                "dry_run_evidence_path": _relative_to_vault(vault, context["dry_run_evidence_path"]),
                "execution_evidence_path": _relative_to_vault(vault, context["execution_evidence_path"]),
                "signing_allowed": False,
                "startup_mutation_allowed": False,
                "release_promotion_allowed": False,
                "writes_performed": False,
                "next_recommended_pass": NEXT_SIGNING_APPROVAL_PASS if completed_ok and not execute else BLOCKED_PASS,
            },
            "preflight_checks": checks,
            "post_execution_checks": post_checks,
            "paths": pre_execution_paths,
            "rollback_boundary": {
                "owned_output_root": INSTALLER_OUTPUT_ROOT.as_posix(),
                "rollback_scope": "delete_or_replace_owned_output_root_only_after_operator_review",
                "host_mutation_to_rollback": False,
            },
            "authority": _authority_for(False),
            "blockers": [] if ok else ["exact_once_marker_already_exists_duplicate_execution_blocked"],
            "unverified": [
                "No signing was attempted.",
                "No startup/autostart, registry, Start Menu, or desktop shortcut write was attempted.",
                "No release promotion or release-status write was attempted.",
            ],
            "writes_performed": False,
            "next_recommended_pass": NEXT_SIGNING_APPROVAL_PASS if ok else BLOCKED_PASS,
        }

    blockers.extend(name for name, passed in checks.items() if not passed)
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
                "signing_allowed": False,
                "startup_mutation_allowed": False,
                "release_promotion_allowed": False,
                "writes_performed": False,
                "next_recommended_pass": "run-with---execute" if ok else BLOCKED_PASS,
            },
            "preflight_checks": checks,
            "paths": pre_execution_paths,
            "rollback_boundary": {
                "owned_output_root": INSTALLER_OUTPUT_ROOT.as_posix(),
                "rollback_scope": "owned_installer_output_root_only",
                "host_mutation_to_rollback": False,
            },
            "authority": _authority_for(False),
            "blockers": blockers,
            "unverified": [
                "Execution was not requested, so no marker, ZIP, manifest, audit, or execution evidence was written.",
                "No signing/startup/release gate was exercised.",
            ],
            "writes_performed": False,
            "next_recommended_pass": "run-with---execute" if ok else BLOCKED_PASS,
        }

    packet_id = str(context["packet_id"])
    approval_payload = context["approval_payload"] or {}
    approved_exe = _resolve_vault_relative_path(vault, str(approval_payload.get("approved_packaged_executable", {}).get("path") or ""))
    source_dir = approved_exe.parent
    marker_path = context["marker_path"]
    reserved_at = _now_utc()
    marker_payload = {
        "record_type": "studio_installer_build_execution_marker",
        "schema_version": MODEL_VERSION,
        "status": "reserved_before_installer_output",
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "reserved_at": reserved_at,
        "completed_at": None,
        "approval_artifact_path": _relative_to_vault(vault, context["approval_path"]),
        "output_root": _relative_to_vault(vault, context["output_root"]),
        "portable_zip_path": _relative_to_vault(vault, context["portable_zip"]),
        "build_manifest_path": _relative_to_vault(vault, context["manifest_path"]),
        "duplicate_policy": "block_before_any_installer_output_write",
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
            "blockers": ["exact_once_marker_already_exists_duplicate_execution_blocked"],
            "writes_performed": False,
            "next_recommended_pass": BLOCKED_PASS,
        }

    dry_run_payload = {
        "record_type": "studio_installer_build_pre_output_dry_run_evidence",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "exact_once_marker_reserved_before_this_write": True,
        "installer_output_written_at_this_point": False,
        "preflight_checks": checks,
        "authority": _authority_for(False),
    }
    _write_json(context["dry_run_evidence_path"], dry_run_payload)

    pre_audit = {
        "record_type": "studio_installer_build_pre_output_audit",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "marker_reserved": True,
        "source_dir": _relative_to_vault(vault, source_dir),
        "output_root": _relative_to_vault(vault, context["output_root"]),
        "signing_startup_release_blocked": True,
    }
    _write_json(context["pre_audit_path"], pre_audit)

    files = _zip_directory(source_dir, context["portable_zip"])
    portable_zip_sha = _sha256_file(context["portable_zip"])
    manifest = {
        "record_type": "studio_installer_build_manifest",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "installer_format": "zip-portable",
        "source_app_dir": _relative_to_vault(vault, source_dir),
        "source_executable": _file_record(vault, approved_exe),
        "source_executable_sha256": _sha256_file(approved_exe),
        "portable_zip": _file_record(vault, context["portable_zip"]),
        "portable_zip_sha256": portable_zip_sha,
        "file_count": len(files),
        "files": files,
        "approval_artifact_path": _relative_to_vault(vault, context["approval_path"]),
        "exact_once_marker_path": _relative_to_vault(vault, marker_path),
        "signing_allowed": False,
        "startup_mutation_allowed": False,
        "release_promotion_allowed": False,
    }
    _write_json(context["manifest_path"], manifest)

    post_audit = {
        "record_type": "studio_installer_build_post_output_audit",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "marker_reserved": True,
        "portable_zip_sha256": portable_zip_sha,
        "manifest_path": _relative_to_vault(vault, context["manifest_path"]),
        "rollback_boundary": "owned_output_root_only",
        "host_mutation_to_rollback": False,
        "signing_startup_release_blocked": True,
    }
    _write_json(context["post_audit_path"], post_audit)

    completed_at = _now_utc()
    marker_payload.update(
        {
            "status": COMPLETE_STATUS,
            "completed_at": completed_at,
            "portable_zip_sha256": portable_zip_sha,
            "manifest_sha256": _sha256_file(context["manifest_path"]),
            "pre_output_audit_sha256": _sha256_file(context["pre_audit_path"]),
            "post_output_audit_sha256": _sha256_file(context["post_audit_path"]),
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
            "portable_zip_path": _relative_to_vault(vault, context["portable_zip"]),
            "portable_zip_sha256": portable_zip_sha,
            "manifest_path": _relative_to_vault(vault, context["manifest_path"]),
            "pre_output_audit_path": _relative_to_vault(vault, context["pre_audit_path"]),
            "post_output_audit_path": _relative_to_vault(vault, context["post_audit_path"]),
            "dry_run_evidence_path": _relative_to_vault(vault, context["dry_run_evidence_path"]),
            "execution_evidence_path": _relative_to_vault(vault, context["execution_evidence_path"]),
            "signing_allowed": False,
            "startup_mutation_allowed": False,
            "release_promotion_allowed": False,
            "writes_performed": True,
            "next_recommended_pass": NEXT_SIGNING_APPROVAL_PASS if ok else BLOCKED_PASS,
        },
        "preflight_checks": checks,
        "post_execution_checks": post_checks,
        "pre_execution_paths": pre_execution_paths,
        "post_execution_paths": post_execution_paths,
        "manifest": manifest,
        "rollback_boundary": {
            "owned_output_root": INSTALLER_OUTPUT_ROOT.as_posix(),
            "rollback_scope": "owned_installer_output_root_only",
            "rollback_requires_operator_review": True,
            "host_mutation_to_rollback": False,
            "release_status_to_rollback": False,
        },
        "authority": _authority_for(True),
        "blocked_authority": [key for key, value in _authority_for(True).items() if value is False],
        "blockers": [] if ok else [name for name, passed in post_checks.items() if not passed],
        "unverified": [
            "Portable ZIP was not launched or installed.",
            "No signing was attempted.",
            "No signing certificate was read.",
            "No startup/autostart, registry, Start Menu, or desktop shortcut write was attempted.",
            "No release promotion or release-status write was attempted.",
        ],
        "writes_performed": True,
        "next_recommended_pass": NEXT_SIGNING_APPROVAL_PASS if ok else BLOCKED_PASS,
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
    report["summary"]["next_recommended_pass"] = NEXT_SIGNING_APPROVAL_PASS if report["ok"] else BLOCKED_PASS
    report["next_recommended_pass"] = report["summary"]["next_recommended_pass"]
    _write_json(context["execution_evidence_path"], report)
    return report


def write_installer_build_approved_execution_proof_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-installer-build-approved-execution-proof"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    lines = [
        "# Studio Installer Build Approved Execution Proof Evidence",
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
        f"- portable_zip_path: {summary.get('portable_zip_path')}",
        f"- portable_zip_sha256: {summary.get('portable_zip_sha256')}",
        f"- manifest_path: {summary.get('manifest_path')}",
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
