"""Approved execution proof for the governed Studio startup/autostart lane.

This is the narrow proof lane for the already-written Studio startup/autostart
approval artifact. It consumes the approval through an exact-once marker and
writes workspace-scoped proof, rollback, audit, and evidence records.

The approval currently authorizes a preview/proof mode only. This pass does not
resolve real host startup paths, write Windows Startup folder shortcuts, create
Task Scheduler entries, write registry Run keys, write Start Menu or desktop
shortcuts, promote a release, launch Studio, call providers/connectors, enqueue
Agent Bus tasks, mutate Gate, execute workflows, configure Git, or write
canonical ChaseOS state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.installer_build_approval import BLOCKED_AUTHORITY, DEFAULT_EVIDENCE_ROOT
from runtime.studio.startup_autostart_approval_consumption_dry_run import (
    build_studio_startup_autostart_approval_consumption_dry_run,
)
from runtime.studio.startup_autostart_approval_preview import (
    STARTUP_APPROVAL_RELATIVE_DIR,
    STARTUP_MARKER_RELATIVE_DIR,
    STARTUP_PROOF_ROOT,
)
from runtime.studio.startup_autostart_approval_review import APPROVAL_RECORD_TYPE


MODEL_VERSION = "studio.startup_autostart_approved_execution_proof.v1"
SURFACE_ID = "studio_startup_autostart_approved_execution_proof"
READY_STATUS = "ready_for_studio_startup_autostart_approved_execution_proof"
COMPLETE_STATUS = "studio_startup_autostart_approved_execution_proof_complete"
BLOCKED_STATUS = "blocked_studio_startup_autostart_approved_execution_proof"
DUPLICATE_BLOCKED_STATUS = "blocked_duplicate_studio_startup_autostart_execution"
NEXT_RELEASE_PROMOTION_APPROVAL_PASS = "studio-release-promotion-approval-preview"
BLOCKED_PASS = "studio-startup-autostart-approval-consumption-dry-run"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _slug(value: str, fallback: str = "startup-autostart-target") -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug or fallback


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
        raise ValueError(f"startup/autostart execution proof path escapes vault: {path_value}") from exc
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
        and marker_payload.get("record_type") == "studio_startup_autostart_execution_marker"
        and marker_payload.get("approval_packet_id") == approval_packet_id
        and marker_payload.get("status") == COMPLETE_STATUS
    )


def _collect_context(
    vault: Path,
    *,
    approval_packet_id: str | None,
    generated_at: str,
) -> dict[str, Any]:
    consumption = build_studio_startup_autostart_approval_consumption_dry_run(
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
    output_root = _future_path(vault, future_paths, "output_root", STARTUP_PROOF_ROOT)
    signed_zip = _resolve_vault_relative_path(vault, str(payload.get("approved_signed_portable_zip_path") or ""))
    signing_manifest = _resolve_vault_relative_path(vault, str(payload.get("approved_signing_manifest_path") or ""))
    signing_marker = _resolve_vault_relative_path(vault, str(payload.get("approved_signing_execution_marker_path") or ""))
    dry_run_evidence_path = _future_path(
        vault,
        future_paths,
        "startup_dry_run_evidence",
        DEFAULT_EVIDENCE_ROOT / f"{packet_id}-startup-autostart-dry-run.json",
    )
    execution_evidence_path = _future_path(
        vault,
        future_paths,
        "startup_execution_evidence",
        DEFAULT_EVIDENCE_ROOT / f"{packet_id}-startup-autostart-execution.json",
    )
    rollback_plan_path = _future_path(
        vault,
        future_paths,
        "rollback_plan",
        STARTUP_PROOF_ROOT / "rollback" / f"{packet_id}-startup-autostart-rollback-plan.json",
    )
    host_mutation_audit_path = _future_path(
        vault,
        future_paths,
        "host_mutation_audit",
        STARTUP_PROOF_ROOT / "audit" / f"{packet_id}-startup-autostart-host-mutation-audit.json",
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
        "signed_zip": signed_zip,
        "signing_manifest": signing_manifest,
        "signing_marker": signing_marker,
        "dry_run_evidence_path": dry_run_evidence_path,
        "execution_evidence_path": execution_evidence_path,
        "rollback_plan_path": rollback_plan_path,
        "host_mutation_audit_path": host_mutation_audit_path,
        "pre_host_audit_path": output_root / "audit" / f"{packet_id}-pre-host-target-audit.json",
        "post_host_audit_path": output_root / "audit" / f"{packet_id}-post-host-target-audit.json",
        "host_targets_dir": output_root / "host-targets",
        "shortcut_preview_manifest_path": (
            output_root / "shortcuts" / f"{packet_id}-ChaseOS-Studio-startup-shortcut-preview.json"
        ),
    }


def _target_file_path(context: dict[str, Any], target_id: str) -> Path:
    return context["host_targets_dir"] / f"{context['packet_id']}-{_slug(target_id)}.json"


def _target_file_paths(context: dict[str, Any]) -> list[Path]:
    approval_payload = context.get("approval_payload") or {}
    targets = list(approval_payload.get("approved_host_targets") or [])
    return [_target_file_path(context, str(target)) for target in targets]


def _paths_snapshot(vault: Path, context: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "approval_artifact": context["approval_path"],
        "exact_once_marker": context["marker_path"],
        "output_root": context["output_root"],
        "signed_portable_zip": context["signed_zip"],
        "signing_manifest": context["signing_manifest"],
        "signing_execution_marker": context["signing_marker"],
        "dry_run_evidence": context["dry_run_evidence_path"],
        "execution_evidence": context["execution_evidence_path"],
        "rollback_plan": context["rollback_plan_path"],
        "host_mutation_audit": context["host_mutation_audit_path"],
        "pre_host_audit": context["pre_host_audit_path"],
        "post_host_audit": context["post_host_audit_path"],
        "shortcut_preview_manifest": context["shortcut_preview_manifest_path"],
    }
    for target_path in _target_file_paths(context):
        paths[f"host_target_{target_path.stem}"] = target_path
    snapshot: dict[str, Any] = {}
    for key, path in paths.items():
        snapshot[key] = {
            "path": _relative_to_vault(vault, path),
            "exists": path.exists(),
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "size_bytes": path.stat().st_size if path.is_file() else 0,
            "sha256": _sha256_file(path) if path.is_file() else None,
        }
    return snapshot


def _authority_for(executed: bool) -> dict[str, Any]:
    return {
        **dict(BLOCKED_AUTHORITY),
        "read_only": not executed,
        "approval_packet_preview_only": False,
        "approval_artifact_review_only": False,
        "approval_consumption_dry_run_only": False,
        "approved_startup_autostart_execution_proof": True,
        "validates_approval_artifact": True,
        "consumes_approval_decision": bool(executed),
        "executes_approval_decisions": bool(executed),
        "reserves_idempotency_marker": bool(executed),
        "writes_idempotency_marker": bool(executed),
        "builds_executable": False,
        "builds_installer": False,
        "writes_installer": False,
        "writes_packaging_output_root": False,
        "signs_artifacts": False,
        "reads_signing_certificate": False,
        "signing_certificate_read": False,
        "raw_certificate_values_visible": False,
        "writes_signed_artifact": False,
        "verifies_signature": False,
        "writes_startup_autostart_proof_root": bool(executed),
        "writes_startup_autostart_dry_run_evidence": bool(executed),
        "writes_startup_autostart_execution_evidence": bool(executed),
        "writes_startup_autostart_rollback_plan": bool(executed),
        "writes_startup_autostart_audit": bool(executed),
        "writes_workspace_shortcut_preview_manifest": bool(executed),
        "host_path_resolution_attempted": False,
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


def _future_outputs_clear(context: dict[str, Any]) -> bool:
    expected_paths = [
        context["dry_run_evidence_path"],
        context["execution_evidence_path"],
        context["rollback_plan_path"],
        context["host_mutation_audit_path"],
        context["pre_host_audit_path"],
        context["post_host_audit_path"],
        context["shortcut_preview_manifest_path"],
        *_target_file_paths(context),
    ]
    return not any(path.exists() for path in expected_paths)


def _host_target_previews_safe(approval_payload: dict[str, Any]) -> bool:
    previews = approval_payload.get("host_target_previews") or []
    if not isinstance(previews, list) or not previews:
        return False
    return all(
        isinstance(item, dict)
        and item.get("id") in (approval_payload.get("approved_host_targets") or [])
        and item.get("host_path_resolved_now") is False
        and item.get("write_allowed_in_this_pass") is False
        for item in previews
    )


def _approval_authority_flags_blocked(approval_payload: dict[str, Any]) -> bool:
    return all(
        approval_payload.get(key) is False
        for key in [
            "startup_mutation_allowed_in_this_pass",
            "approval_decision_consumed",
            "idempotency_marker_reserved",
            "host_path_resolution_attempted",
            "resolves_host_startup_paths",
            "writes_host_startup",
            "registers_autostart",
            "writes_registry",
            "writes_start_menu",
            "writes_desktop_shortcut",
            "release_promotion_allowed",
            "writes_release_status",
            "pywebview_launch_allowed",
            "server_start_allowed",
            "executable_launch_allowed",
            "browser_use_cli_live_run",
            "excalidraw_live_proof",
            "mutates_gate",
            "executes_workflows",
            "provider_calls_allowed",
            "connector_calls_allowed",
            "writes_agent_bus_tasks",
            "canonical_mutation_allowed",
        ]
    )


def _preflight_checks(vault: Path, context: dict[str, Any], *, require_clear_outputs: bool) -> dict[str, bool]:
    approval_payload = context.get("approval_payload") or {}
    packet_id = str(context.get("packet_id") or "")
    requested_packet_id = context.get("requested_approval_packet_id")
    request_digest = str(context.get("request_digest") or "")
    marker_path = context["marker_path"]
    marker_payload = context.get("marker_payload")
    output_root = context["output_root"]
    completed = _completed_marker(marker_payload, packet_id)
    approved_targets = list(approval_payload.get("approved_host_targets") or [])
    expected_targets = [
        "windows-startup-folder-shortcut",
        "windows-task-scheduler",
        "windows-registry-run-key",
        "start-menu-shortcut",
        "desktop-shortcut",
    ]
    startup_mode = str(approval_payload.get("approved_startup_mode") or "")
    clear_outputs = _future_outputs_clear(context)
    target_files = _target_file_paths(context)
    return {
        "consumption_contract_ok": bool((context.get("consumption") or {}).get("ok")) or completed,
        "approval_packet_argument_matches": (not requested_packet_id) or requested_packet_id == packet_id,
        "approval_artifact_present": context["approval_path"].is_file(),
        "approval_artifact_json_readable": bool(approval_payload),
        "approval_record_type_valid": approval_payload.get("record_type") == APPROVAL_RECORD_TYPE,
        "approval_packet_id_matches": approval_payload.get("approval_packet_id") == packet_id,
        "request_digest_matches": approval_payload.get("request_digest_sha256") == request_digest,
        "operator_decision_approved": approval_payload.get("operator_decision") == "approved",
        "approval_scope_one_startup_autostart_proof": approval_payload.get("approval_scope")
        == "one_startup_autostart_proof_only",
        "approved_startup_mode_preview_only": startup_mode == "windows-startup-folder-shortcut-preview"
        and startup_mode.endswith("-preview"),
        "approved_target_platform_windows": approval_payload.get("approved_target_platform") == "windows",
        "approved_host_targets_match": approved_targets == expected_targets,
        "host_target_previews_safe": _host_target_previews_safe(approval_payload),
        "approval_consumption_required": approval_payload.get("approval_consumption_required") is True,
        "approval_not_previously_consumed_by_artifact": approval_payload.get("approval_decision_consumed") is False,
        "approval_artifact_not_mutated_for_execution": approval_payload.get("idempotency_marker_reserved") is False,
        "approval_authority_flags_blocked": _approval_authority_flags_blocked(approval_payload),
        "signed_portable_zip_present": context["signed_zip"].is_file(),
        "signed_portable_zip_sha_matches": bool(approval_payload.get("approved_signed_portable_zip_sha256"))
        and _sha256_file(context["signed_zip"]) == approval_payload.get("approved_signed_portable_zip_sha256"),
        "signing_manifest_present": context["signing_manifest"].is_file(),
        "signing_manifest_sha_matches": bool(approval_payload.get("approved_signing_manifest_sha256"))
        and _sha256_file(context["signing_manifest"]) == approval_payload.get("approved_signing_manifest_sha256"),
        "signing_execution_marker_present": context["signing_marker"].is_file(),
        "signing_execution_marker_sha_matches": bool(approval_payload.get("approved_signing_execution_marker_sha256"))
        and _sha256_file(context["signing_marker"]) == approval_payload.get("approved_signing_execution_marker_sha256"),
        "approval_path_under_expected_root": _path_under(context["approval_path"], vault / STARTUP_APPROVAL_RELATIVE_DIR),
        "marker_path_under_expected_root": _path_under(marker_path, vault / STARTUP_MARKER_RELATIVE_DIR),
        "output_root_under_approved_root": output_root == (vault / STARTUP_PROOF_ROOT).resolve(),
        "dry_run_evidence_under_evidence_root": _path_under(context["dry_run_evidence_path"], vault / DEFAULT_EVIDENCE_ROOT),
        "execution_evidence_under_evidence_root": _path_under(
            context["execution_evidence_path"], vault / DEFAULT_EVIDENCE_ROOT
        ),
        "rollback_plan_under_output_root": _path_under(context["rollback_plan_path"], output_root),
        "host_mutation_audit_under_output_root": _path_under(context["host_mutation_audit_path"], output_root),
        "audit_paths_under_output_root": _path_under(context["pre_host_audit_path"], output_root)
        and _path_under(context["post_host_audit_path"], output_root),
        "host_target_paths_under_output_root": bool(target_files)
        and all(_path_under(target_path, output_root) for target_path in target_files),
        "shortcut_preview_manifest_under_output_root": _path_under(context["shortcut_preview_manifest_path"], output_root),
        "future_output_paths_clear_before_execution": clear_outputs if require_clear_outputs else True,
        "real_marker_absent_before_execution": (not marker_path.exists()) if require_clear_outputs else True,
        "existing_marker_is_completed_if_present": (not marker_path.exists()) or completed,
        "host_paths_not_resolved_before_execution": True,
        "host_mutation_not_authorized_by_approval_mode": startup_mode.endswith("-preview"),
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


def _host_target_plan(vault: Path, context: dict[str, Any], *, generated_at: str) -> dict[str, Any]:
    approval_payload = context.get("approval_payload") or {}
    previews_by_id = {
        str(item.get("id")): item
        for item in approval_payload.get("host_target_previews") or []
        if isinstance(item, dict) and item.get("id")
    }
    signed_zip_record = _file_record(vault, context["signed_zip"])
    targets: list[dict[str, Any]] = []
    for target_id in approval_payload.get("approved_host_targets") or []:
        target_id = str(target_id)
        preview = previews_by_id.get(target_id) or {}
        selected = target_id == "windows-startup-folder-shortcut"
        proof_path = _target_file_path(context, target_id)
        targets.append(
            {
                "id": target_id,
                "kind": preview.get("kind") or "host_startup_target",
                "approval_preview_status": preview.get("status"),
                "selected_for_workspace_proof": selected,
                "workspace_proof_path": _relative_to_vault(vault, proof_path),
                "workspace_shortcut_preview_manifest_path": (
                    _relative_to_vault(vault, context["shortcut_preview_manifest_path"]) if selected else None
                ),
                "action": "write_workspace_shortcut_preview_manifest" if selected else "record_deferred_target_only",
                "host_path_resolution_attempted": False,
                "host_path_resolved": False,
                "actual_host_path": None,
                "write_allowed_to_host": False,
                "host_mutation_performed": False,
                "rollback_required_for_host": False,
                "deferred_gate_required_before_real_host_write": True,
            }
        )
    return {
        "record_type": "studio_startup_autostart_host_target_plan",
        "schema_version": MODEL_VERSION,
        "generated_at": generated_at,
        "approval_packet_id": context["packet_id"],
        "request_digest_sha256": context["request_digest"],
        "startup_mode": approval_payload.get("approved_startup_mode"),
        "target_platform": approval_payload.get("approved_target_platform"),
        "source_signed_portable_zip": signed_zip_record,
        "selected_proof_target": "windows-startup-folder-shortcut",
        "proof_mode": "workspace_only_shortcut_preview_manifest",
        "host_path_resolution_attempted": False,
        "host_mutation_performed": False,
        "targets": targets,
    }


def _write_host_target_proof_files(vault: Path, context: dict[str, Any], target_plan: dict[str, Any]) -> list[dict[str, Any]]:
    written: list[dict[str, Any]] = []
    for target in target_plan.get("targets") or []:
        path = _target_file_path(context, str(target.get("id") or "target"))
        payload = {
            "record_type": "studio_startup_autostart_host_target_proof",
            "schema_version": MODEL_VERSION,
            "generated_at": _now_utc(),
            "approval_packet_id": context["packet_id"],
            "target": target,
            "workspace_proof_only": True,
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
            "release_promotion_allowed": False,
        }
        _write_json(path, payload)
        written.append(_file_record(vault, path))

    shortcut_payload = {
        "record_type": "studio_startup_shortcut_preview_manifest",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": context["packet_id"],
        "shortcut_kind": "windows_startup_folder_shortcut_preview",
        "startup_mode": (context.get("approval_payload") or {}).get("approved_startup_mode"),
        "source_signed_portable_zip": _file_record(vault, context["signed_zip"]),
        "source_signing_manifest": _file_record(vault, context["signing_manifest"]),
        "would_launch_command": None,
        "actual_host_startup_path": None,
        "host_path_resolution_attempted": False,
        "host_path_resolved": False,
        "host_shortcut_written": False,
        "task_scheduler_registered": False,
        "registry_run_key_written": False,
        "start_menu_shortcut_written": False,
        "desktop_shortcut_written": False,
        "executable_launched": False,
        "workspace_preview_only": True,
    }
    _write_json(context["shortcut_preview_manifest_path"], shortcut_payload)
    written.append(_file_record(vault, context["shortcut_preview_manifest_path"]))
    return written


def _post_execution_checks(vault: Path, context: dict[str, Any]) -> dict[str, bool]:
    marker_path = context["marker_path"]
    marker = _read_json(marker_path)
    dry_run = _read_json(context["dry_run_evidence_path"])
    execution = _read_json(context["execution_evidence_path"])
    rollback = _read_json(context["rollback_plan_path"])
    host_audit = _read_json(context["host_mutation_audit_path"])
    pre_audit = _read_json(context["pre_host_audit_path"])
    post_audit = _read_json(context["post_host_audit_path"])
    shortcut_preview = _read_json(context["shortcut_preview_manifest_path"])
    target_files = _target_file_paths(context)
    target_payloads = [_read_json(path) for path in target_files]
    packet_id = str(context.get("packet_id") or "")
    return {
        "approval_consumed_by_marker": _completed_marker(marker, packet_id),
        "exact_once_marker_exists": marker_path.is_file(),
        "duplicate_execution_blocked": marker_path.is_file(),
        "signed_portable_zip_exists": context["signed_zip"].is_file(),
        "signed_portable_zip_sha_matches_approval": _sha256_file(context["signed_zip"])
        == (context.get("approval_payload") or {}).get("approved_signed_portable_zip_sha256"),
        "signing_manifest_exists": context["signing_manifest"].is_file(),
        "signing_manifest_sha_matches_approval": _sha256_file(context["signing_manifest"])
        == (context.get("approval_payload") or {}).get("approved_signing_manifest_sha256"),
        "signing_execution_marker_exists": context["signing_marker"].is_file(),
        "signing_execution_marker_sha_matches_approval": _sha256_file(context["signing_marker"])
        == (context.get("approval_payload") or {}).get("approved_signing_execution_marker_sha256"),
        "dry_run_evidence_exists": context["dry_run_evidence_path"].is_file(),
        "dry_run_evidence_packet_id_matches": bool(dry_run and dry_run.get("approval_packet_id") == packet_id),
        "execution_evidence_exists": context["execution_evidence_path"].is_file(),
        "execution_evidence_packet_id_matches": bool(
            execution and execution.get("summary", {}).get("approval_packet_id") == packet_id
        ),
        "rollback_plan_exists": context["rollback_plan_path"].is_file(),
        "rollback_scope_owned_output_root_only": bool(
            rollback and rollback.get("rollback_scope") == "owned_startup_autostart_proof_root_only"
        ),
        "host_mutation_audit_exists": context["host_mutation_audit_path"].is_file(),
        "host_mutation_audit_no_host_mutation": bool(host_audit and host_audit.get("host_mutation_performed") is False),
        "pre_host_audit_exists": context["pre_host_audit_path"].is_file(),
        "post_host_audit_exists": context["post_host_audit_path"].is_file(),
        "pre_post_audits_no_host_mutation": bool(
            pre_audit
            and post_audit
            and pre_audit.get("host_mutation_performed") is False
            and post_audit.get("host_mutation_performed") is False
        ),
        "target_proof_files_exist": bool(target_files) and all(path.is_file() for path in target_files),
        "target_proofs_workspace_only": bool(target_payloads)
        and all(payload and payload.get("workspace_proof_only") is True for payload in target_payloads),
        "shortcut_preview_manifest_exists": context["shortcut_preview_manifest_path"].is_file(),
        "shortcut_preview_no_host_write": bool(
            shortcut_preview
            and shortcut_preview.get("workspace_preview_only") is True
            and shortcut_preview.get("host_shortcut_written") is False
            and shortcut_preview.get("task_scheduler_registered") is False
            and shortcut_preview.get("registry_run_key_written") is False
            and shortcut_preview.get("start_menu_shortcut_written") is False
            and shortcut_preview.get("desktop_shortcut_written") is False
        ),
        "host_path_resolution_not_attempted": bool(
            marker
            and host_audit
            and shortcut_preview
            and marker.get("host_path_resolution_attempted") is False
            and host_audit.get("host_path_resolution_attempted") is False
            and shortcut_preview.get("host_path_resolution_attempted") is False
        ),
        "no_host_mutation_performed": bool(
            marker
            and host_audit
            and marker.get("host_mutation_performed") is False
            and host_audit.get("host_mutation_performed") is False
        ),
        "no_release_promotion": bool(
            marker
            and host_audit
            and marker.get("release_promotion_allowed") is False
            and host_audit.get("release_promotion_allowed") is False
        ),
        "all_proof_paths_scoped_under_output_root": all(
            _path_under(path, context["output_root"])
            for path in [
                context["rollback_plan_path"],
                context["host_mutation_audit_path"],
                context["pre_host_audit_path"],
                context["post_host_audit_path"],
                context["shortcut_preview_manifest_path"],
                *target_files,
            ]
        ),
        "execution_evidence_scoped_under_evidence_root": _path_under(
            context["execution_evidence_path"], vault / DEFAULT_EVIDENCE_ROOT
        ),
        "dry_run_evidence_scoped_under_evidence_root": _path_under(
            context["dry_run_evidence_path"], vault / DEFAULT_EVIDENCE_ROOT
        ),
    }


def _already_completed_report(
    vault: Path,
    context: dict[str, Any],
    *,
    timestamp: str,
    execute: bool,
    checks: dict[str, bool],
) -> dict[str, Any]:
    post_checks = _post_execution_checks(vault, context)
    completed_ok = all(post_checks.values()) and all(
        value
        for key, value in checks.items()
        if key not in {"future_output_paths_clear_before_execution", "real_marker_absent_before_execution"}
    )
    ok = completed_ok and not execute
    summary = {
        "approval_packet_id": context.get("packet_id"),
        "request_digest_sha256": context.get("request_digest"),
        "execution_requested": bool(execute),
        "execution_performed": False,
        "already_executed": True,
        "approval_consumed": True,
        "approval_artifact_mutated": False,
        "exact_once_marker_reserved": True,
        "exact_once_marker_completed": True,
        "duplicate_execution_blocked": True,
        "signed_portable_zip_path": _relative_to_vault(vault, context["signed_zip"]),
        "signed_portable_zip_sha256": _sha256_file(context["signed_zip"]),
        "signing_manifest_path": _relative_to_vault(vault, context["signing_manifest"]),
        "dry_run_evidence_path": _relative_to_vault(vault, context["dry_run_evidence_path"]),
        "execution_evidence_path": _relative_to_vault(vault, context["execution_evidence_path"]),
        "rollback_plan_path": _relative_to_vault(vault, context["rollback_plan_path"]),
        "host_mutation_audit_path": _relative_to_vault(vault, context["host_mutation_audit_path"]),
        "host_path_resolution_attempted": False,
        "host_mutation_performed": False,
        "host_startup_mutation_allowed": False,
        "autostart_registration_allowed": False,
        "registry_write_allowed": False,
        "start_menu_write_allowed": False,
        "desktop_shortcut_write_allowed": False,
        "release_promotion_allowed": False,
        "writes_performed": False,
        "next_recommended_pass": NEXT_RELEASE_PROMOTION_APPROVAL_PASS if ok else BLOCKED_PASS,
    }
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": DUPLICATE_BLOCKED_STATUS if execute else COMPLETE_STATUS,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "summary": summary,
        "preflight_checks": checks,
        "post_execution_checks": post_checks,
        "paths": _paths_snapshot(vault, context),
        "rollback_boundary": {
            "owned_output_root": STARTUP_PROOF_ROOT.as_posix(),
            "rollback_scope": "owned_startup_autostart_proof_root_only",
            "rollback_requires_operator_review": True,
            "host_mutation_to_rollback": False,
            "release_status_to_rollback": False,
        },
        "authority": _authority_for(False),
        "blocked_authority": [key for key, value in _authority_for(False).items() if value is False],
        "blockers": [] if ok else ["startup_autostart_exact_once_marker_already_exists_duplicate_execution_blocked"],
        "unverified": [
            "Existing completed marker was inspected only; no new startup/autostart proof output was written.",
            "No host startup path was resolved or probed.",
            "No Startup folder, Task Scheduler, registry Run key, Start Menu, desktop shortcut, release-status, provider/connector, Agent Bus, Gate, workflow, Git, or canonical write was attempted.",
        ],
        "writes_performed": False,
        "next_recommended_pass": NEXT_RELEASE_PROMOTION_APPROVAL_PASS if ok else BLOCKED_PASS,
    }


def build_studio_startup_autostart_approved_execution_proof(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    execute: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or execute the approved one-shot Studio startup/autostart proof."""

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
        return _already_completed_report(vault, context, timestamp=timestamp, execute=execute, checks=checks)

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
                "signed_portable_zip_path": _relative_to_vault(vault, context["signed_zip"]),
                "signed_portable_zip_sha256": _sha256_file(context["signed_zip"]),
                "signing_manifest_path": _relative_to_vault(vault, context["signing_manifest"]),
                "host_path_resolution_attempted": False,
                "host_mutation_performed": False,
                "host_startup_mutation_allowed": False,
                "autostart_registration_allowed": False,
                "registry_write_allowed": False,
                "start_menu_write_allowed": False,
                "desktop_shortcut_write_allowed": False,
                "release_promotion_allowed": False,
                "writes_performed": False,
                "next_recommended_pass": "run-with---execute" if ok else BLOCKED_PASS,
            },
            "preflight_checks": checks,
            "paths": pre_execution_paths,
            "rollback_boundary": {
                "owned_output_root": STARTUP_PROOF_ROOT.as_posix(),
                "rollback_scope": "owned_startup_autostart_proof_root_only",
                "host_mutation_to_rollback": False,
                "release_status_to_rollback": False,
            },
            "authority": _authority_for(False),
            "blocked_authority": [key for key, value in _authority_for(False).items() if value is False],
            "blockers": blockers,
            "unverified": [
                "Execution was not requested, so no marker, rollback plan, host-target proof, audit, or execution evidence was written.",
                "No host startup path was resolved or probed.",
                "No Startup folder, Task Scheduler, registry Run key, Start Menu, desktop shortcut, or release gate was exercised.",
            ],
            "writes_performed": False,
            "next_recommended_pass": "run-with---execute" if ok else BLOCKED_PASS,
        }

    packet_id = str(context["packet_id"])
    marker_path = context["marker_path"]
    reserved_at = _now_utc()
    marker_payload = {
        "record_type": "studio_startup_autostart_execution_marker",
        "schema_version": MODEL_VERSION,
        "status": "reserved_before_startup_autostart_proof_output",
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "reserved_at": reserved_at,
        "completed_at": None,
        "approval_artifact_path": _relative_to_vault(vault, context["approval_path"]),
        "output_root": _relative_to_vault(vault, context["output_root"]),
        "signed_portable_zip_path": _relative_to_vault(vault, context["signed_zip"]),
        "signing_manifest_path": _relative_to_vault(vault, context["signing_manifest"]),
        "dry_run_evidence_path": _relative_to_vault(vault, context["dry_run_evidence_path"]),
        "execution_evidence_path": _relative_to_vault(vault, context["execution_evidence_path"]),
        "rollback_plan_path": _relative_to_vault(vault, context["rollback_plan_path"]),
        "host_mutation_audit_path": _relative_to_vault(vault, context["host_mutation_audit_path"]),
        "host_path_resolution_attempted": False,
        "host_mutation_performed": False,
        "release_promotion_allowed": False,
        "duplicate_policy": "block_before_any_startup_autostart_proof_or_host_write",
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
            "blockers": ["startup_autostart_exact_once_marker_already_exists_duplicate_execution_blocked"],
            "writes_performed": False,
            "next_recommended_pass": BLOCKED_PASS,
        }

    dry_run_payload = {
        "record_type": "studio_startup_autostart_pre_output_dry_run_evidence",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "exact_once_marker_reserved_before_this_write": True,
        "host_path_resolution_attempted_at_this_point": False,
        "host_mutation_written_at_this_point": False,
        "preflight_checks": checks,
        "authority": _authority_for(False),
    }
    _write_json(context["dry_run_evidence_path"], dry_run_payload)

    target_plan = _host_target_plan(vault, context, generated_at=_now_utc())
    rollback_plan = {
        "record_type": "studio_startup_autostart_rollback_plan",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "rollback_root": STARTUP_PROOF_ROOT.as_posix(),
        "rollback_scope": "owned_startup_autostart_proof_root_only",
        "files_to_remove_if_operator_rolls_back": [
            _relative_to_vault(vault, context["dry_run_evidence_path"]),
            _relative_to_vault(vault, context["execution_evidence_path"]),
            _relative_to_vault(vault, context["rollback_plan_path"]),
            _relative_to_vault(vault, context["host_mutation_audit_path"]),
            _relative_to_vault(vault, context["pre_host_audit_path"]),
            _relative_to_vault(vault, context["post_host_audit_path"]),
            _relative_to_vault(vault, context["shortcut_preview_manifest_path"]),
            *[_relative_to_vault(vault, path) for path in _target_file_paths(context)],
        ],
        "host_mutation_to_rollback": False,
        "startup_folder_shortcut_to_remove": None,
        "task_scheduler_entry_to_delete": None,
        "registry_run_key_to_delete": None,
        "start_menu_shortcut_to_delete": None,
        "desktop_shortcut_to_delete": None,
        "release_status_to_rollback": False,
        "rollback_requires_operator_review": True,
    }
    _write_json(context["rollback_plan_path"], rollback_plan)

    pre_audit = {
        "record_type": "studio_startup_autostart_pre_host_target_audit",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "marker_reserved": True,
        "signed_portable_zip": _file_record(vault, context["signed_zip"]),
        "signing_manifest": _file_record(vault, context["signing_manifest"]),
        "target_plan": target_plan,
        "host_path_resolution_attempted": False,
        "host_mutation_performed": False,
        "release_promotion_allowed": False,
    }
    _write_json(context["pre_host_audit_path"], pre_audit)

    host_target_files = _write_host_target_proof_files(vault, context, target_plan)
    host_mutation_audit = {
        "record_type": "studio_startup_autostart_host_mutation_audit",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "startup_mode": (context.get("approval_payload") or {}).get("approved_startup_mode"),
        "target_platform": (context.get("approval_payload") or {}).get("approved_target_platform"),
        "host_path_resolution_attempted": False,
        "host_path_resolved": False,
        "host_mutation_performed": False,
        "startup_folder_shortcut_written": False,
        "task_scheduler_registered": False,
        "registry_run_key_written": False,
        "start_menu_shortcut_written": False,
        "desktop_shortcut_written": False,
        "executable_launched": False,
        "release_promotion_allowed": False,
        "release_status_written": False,
        "workspace_only_proof_files": host_target_files,
        "shortcut_preview_manifest": _file_record(vault, context["shortcut_preview_manifest_path"]),
        "target_plan": target_plan,
    }
    _write_json(context["host_mutation_audit_path"], host_mutation_audit)

    post_audit = {
        "record_type": "studio_startup_autostart_post_host_target_audit",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "marker_reserved": True,
        "rollback_plan": _file_record(vault, context["rollback_plan_path"]),
        "host_mutation_audit": _file_record(vault, context["host_mutation_audit_path"]),
        "host_target_files": host_target_files,
        "host_path_resolution_attempted": False,
        "host_mutation_performed": False,
        "rollback_boundary": "owned_startup_autostart_proof_root_only",
        "release_status_to_rollback": False,
    }
    _write_json(context["post_host_audit_path"], post_audit)

    completed_at = _now_utc()
    marker_payload.update(
        {
            "status": COMPLETE_STATUS,
            "completed_at": completed_at,
            "dry_run_evidence_sha256": _sha256_file(context["dry_run_evidence_path"]),
            "rollback_plan_sha256": _sha256_file(context["rollback_plan_path"]),
            "host_mutation_audit_sha256": _sha256_file(context["host_mutation_audit_path"]),
            "pre_host_audit_sha256": _sha256_file(context["pre_host_audit_path"]),
            "post_host_audit_sha256": _sha256_file(context["post_host_audit_path"]),
            "shortcut_preview_manifest_sha256": _sha256_file(context["shortcut_preview_manifest_path"]),
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
            "release_promotion_allowed": False,
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
            "signed_portable_zip_path": _relative_to_vault(vault, context["signed_zip"]),
            "signed_portable_zip_sha256": _sha256_file(context["signed_zip"]),
            "signing_manifest_path": _relative_to_vault(vault, context["signing_manifest"]),
            "dry_run_evidence_path": _relative_to_vault(vault, context["dry_run_evidence_path"]),
            "execution_evidence_path": _relative_to_vault(vault, context["execution_evidence_path"]),
            "rollback_plan_path": _relative_to_vault(vault, context["rollback_plan_path"]),
            "host_mutation_audit_path": _relative_to_vault(vault, context["host_mutation_audit_path"]),
            "shortcut_preview_manifest_path": _relative_to_vault(vault, context["shortcut_preview_manifest_path"]),
            "host_target_proof_file_count": len(host_target_files),
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
            "host_startup_mutation_allowed": False,
            "autostart_registration_allowed": False,
            "registry_write_allowed": False,
            "start_menu_write_allowed": False,
            "desktop_shortcut_write_allowed": False,
            "release_promotion_allowed": False,
            "writes_performed": True,
            "next_recommended_pass": NEXT_RELEASE_PROMOTION_APPROVAL_PASS if ok else BLOCKED_PASS,
        },
        "preflight_checks": checks,
        "post_execution_checks": post_checks,
        "pre_execution_paths": pre_execution_paths,
        "post_execution_paths": post_execution_paths,
        "target_plan": target_plan,
        "rollback_plan": rollback_plan,
        "host_mutation_audit": host_mutation_audit,
        "rollback_boundary": {
            "owned_output_root": STARTUP_PROOF_ROOT.as_posix(),
            "rollback_scope": "owned_startup_autostart_proof_root_only",
            "rollback_requires_operator_review": True,
            "host_mutation_to_rollback": False,
            "release_status_to_rollback": False,
        },
        "authority": _authority_for(True),
        "blocked_authority": [key for key, value in _authority_for(True).items() if value is False],
        "blockers": [] if ok else [name for name, passed in post_checks.items() if not passed],
        "unverified": [
            "No real host Startup folder, Task Scheduler, registry Run key, Start Menu, or desktop shortcut write was attempted.",
            "No host startup path was resolved or probed.",
            "No packaged Studio executable was launched.",
            "No release promotion or release-status write was attempted.",
        ],
        "writes_performed": True,
        "next_recommended_pass": NEXT_RELEASE_PROMOTION_APPROVAL_PASS if ok else BLOCKED_PASS,
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
    report["summary"]["next_recommended_pass"] = (
        NEXT_RELEASE_PROMOTION_APPROVAL_PASS if report["ok"] else BLOCKED_PASS
    )
    report["next_recommended_pass"] = report["summary"]["next_recommended_pass"]
    _write_json(context["execution_evidence_path"], report)
    return report


def write_startup_autostart_approved_execution_proof_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-startup-autostart-approved-execution-proof"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    lines = [
        "# Studio Startup/Autostart Approved Execution Proof Evidence",
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
        f"- rollback_plan_path: {summary.get('rollback_plan_path')}",
        f"- host_mutation_audit_path: {summary.get('host_mutation_audit_path')}",
        f"- shortcut_preview_manifest_path: {summary.get('shortcut_preview_manifest_path')}",
        f"- host_path_resolution_attempted: {summary.get('host_path_resolution_attempted')}",
        f"- host_mutation_performed: {summary.get('host_mutation_performed')}",
        f"- release_promotion_allowed: {summary.get('release_promotion_allowed')}",
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
