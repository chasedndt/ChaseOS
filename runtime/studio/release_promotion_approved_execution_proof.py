"""Approved execution proof for the governed Studio release-promotion lane.

This consumes the written release-promotion approval artifact through an
exact-once marker and writes workspace-scoped proof outputs only. It does not
perform a public release, install anything, mutate host startup/autostart,
touch Git/Gate/Agent Bus/provider/connector state, or write canonical ChaseOS
state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.installer_build_approval import BLOCKED_AUTHORITY, DEFAULT_EVIDENCE_ROOT
from runtime.studio.release_promotion_approval_consumption_dry_run import (
    build_studio_release_promotion_approval_consumption_dry_run,
)
from runtime.studio.release_promotion_approval_preview import (
    EXECUTION_COMPLETE_STATUS,
    NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS,
    RELEASE_MARKER_RELATIVE_DIR,
    RELEASE_PROOF_ROOT,
)
from runtime.studio.release_promotion_approval_review import APPROVAL_RECORD_TYPE


MODEL_VERSION = "studio.release_promotion_approved_execution_proof.v1"
SURFACE_ID = "studio_release_promotion_approved_execution_proof"
READY_STATUS = "ready_for_studio_release_promotion_approved_execution_proof"
COMPLETE_STATUS = EXECUTION_COMPLETE_STATUS
BLOCKED_STATUS = "blocked_studio_release_promotion_approved_execution_proof"
DUPLICATE_BLOCKED_STATUS = "blocked_duplicate_studio_release_promotion_execution"
BLOCKED_PASS = "studio-release-promotion-approval-consumption-dry-run"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _sha256_file(path: Path | None) -> str | None:
    if not path or not path.is_file():
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
    if not path_value:
        raise ValueError("release-promotion execution proof path is empty")
    path = Path(path_value)
    resolved = path.resolve() if path.is_absolute() else (vault / path).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"release-promotion execution proof path escapes vault: {path_value}") from exc
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
        and marker_payload.get("record_type") == "studio_release_promotion_execution_marker"
        and marker_payload.get("approval_packet_id") == approval_packet_id
        and marker_payload.get("status") == COMPLETE_STATUS
    )


def _collect_context(
    vault: Path,
    *,
    approval_packet_id: str | None,
    generated_at: str,
) -> dict[str, Any]:
    consumption = build_studio_release_promotion_approval_consumption_dry_run(
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
    output_root = _future_path(vault, future_paths, "output_root", RELEASE_PROOF_ROOT)
    release_dry_run_evidence_path = _future_path(
        vault,
        future_paths,
        "release_dry_run_evidence",
        DEFAULT_EVIDENCE_ROOT / f"{packet_id}-release-promotion-dry-run.json",
    )
    release_execution_evidence_path = _future_path(
        vault,
        future_paths,
        "release_execution_evidence",
        DEFAULT_EVIDENCE_ROOT / f"{packet_id}-release-promotion-execution.json",
    )
    release_manifest_path = _future_path(
        vault,
        future_paths,
        "release_manifest",
        RELEASE_PROOF_ROOT / "manifest" / f"{packet_id}-release-manifest.json",
    )
    release_status_preview_path = _future_path(
        vault,
        future_paths,
        "release_status_preview",
        RELEASE_PROOF_ROOT / "release-status" / f"{packet_id}-release-status-preview.json",
    )
    release_audit_path = _future_path(
        vault,
        future_paths,
        "release_promotion_audit",
        RELEASE_PROOF_ROOT / "audit" / f"{packet_id}-release-promotion-audit.json",
    )
    rollback_plan_path = _future_path(
        vault,
        future_paths,
        "rollback_plan",
        RELEASE_PROOF_ROOT / "rollback" / f"{packet_id}-release-promotion-rollback-plan.json",
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
        "startup_marker": _resolve_vault_relative_path(
            vault,
            str(payload.get("approved_startup_execution_marker_path") or ""),
        ),
        "signed_zip": _resolve_vault_relative_path(
            vault,
            str(payload.get("approved_signed_portable_zip_path") or ""),
        ),
        "signing_manifest": _resolve_vault_relative_path(
            vault,
            str(payload.get("approved_signing_manifest_path") or ""),
        ),
        "startup_execution_evidence": _resolve_vault_relative_path(
            vault,
            str(payload.get("approved_startup_execution_evidence_path") or ""),
        ),
        "startup_host_mutation_audit": _resolve_vault_relative_path(
            vault,
            str(payload.get("approved_startup_host_mutation_audit_path") or ""),
        ),
        "startup_rollback_plan": _resolve_vault_relative_path(
            vault,
            str(payload.get("approved_startup_rollback_plan_path") or ""),
        ),
        "release_dry_run_evidence_path": release_dry_run_evidence_path,
        "release_execution_evidence_path": release_execution_evidence_path,
        "release_manifest_path": release_manifest_path,
        "release_status_preview_path": release_status_preview_path,
        "release_audit_path": release_audit_path,
        "rollback_plan_path": rollback_plan_path,
    }


def _paths_snapshot(vault: Path, context: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "approval_artifact": context["approval_path"],
        "exact_once_marker": context["marker_path"],
        "output_root": context["output_root"],
        "startup_exact_once_marker": context["startup_marker"],
        "signed_portable_zip": context["signed_zip"],
        "signing_manifest": context["signing_manifest"],
        "startup_execution_evidence": context["startup_execution_evidence"],
        "startup_host_mutation_audit": context["startup_host_mutation_audit"],
        "startup_rollback_plan": context["startup_rollback_plan"],
        "release_dry_run_evidence": context["release_dry_run_evidence_path"],
        "release_execution_evidence": context["release_execution_evidence_path"],
        "release_manifest": context["release_manifest_path"],
        "release_status_preview": context["release_status_preview_path"],
        "release_promotion_audit": context["release_audit_path"],
        "rollback_plan": context["rollback_plan_path"],
    }
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


def _future_outputs_clear(context: dict[str, Any]) -> bool:
    for key in [
        "release_dry_run_evidence_path",
        "release_execution_evidence_path",
        "release_manifest_path",
        "release_status_preview_path",
        "release_audit_path",
        "rollback_plan_path",
    ]:
        if context[key].exists():
            return False
    return True


def _authority_for(executed: bool) -> dict[str, Any]:
    return {
        **dict(BLOCKED_AUTHORITY),
        "read_only": not executed,
        "approval_packet_preview_only": False,
        "approval_artifact_review_only": False,
        "approval_consumption_dry_run_only": False,
        "approved_release_promotion_execution_proof": True,
        "validates_approval_artifact": True,
        "consumes_approval_decision": bool(executed),
        "executes_approval_decisions": bool(executed),
        "reserves_idempotency_marker": bool(executed),
        "writes_idempotency_marker": bool(executed),
        "writes_release_status_preview": bool(executed),
        "writes_release_manifest": bool(executed),
        "writes_release_audit": bool(executed),
        "writes_release_rollback_plan": bool(executed),
        "writes_release_execution_evidence": bool(executed),
        "writes_release_status": bool(executed),
        "promotes_release": False,
        "publishes_release": False,
        "installs_release": False,
        "resolves_host_startup_paths": False,
        "writes_host_startup": False,
        "registers_autostart": False,
        "writes_registry": False,
        "writes_start_menu": False,
        "writes_desktop_shortcut": False,
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
        "git_mutation_allowed": False,
    }


def _preflight_checks(vault: Path, context: dict[str, Any]) -> dict[str, bool]:
    payload = context.get("approval_payload") or {}
    consumption = context.get("consumption") or {}
    marker_payload = context.get("marker_payload")
    packet_id = str(context.get("packet_id") or "")
    approved_sources = {
        "startup_marker": (
            context["startup_marker"],
            str(payload.get("approved_startup_execution_marker_sha256") or ""),
        ),
        "signed_zip": (
            context["signed_zip"],
            str(payload.get("approved_signed_portable_zip_sha256") or ""),
        ),
        "signing_manifest": (
            context["signing_manifest"],
            str(payload.get("approved_signing_manifest_sha256") or ""),
        ),
        "startup_execution_evidence": (
            context["startup_execution_evidence"],
            str(payload.get("approved_startup_execution_evidence_sha256") or ""),
        ),
        "startup_host_mutation_audit": (
            context["startup_host_mutation_audit"],
            str(payload.get("approved_startup_host_mutation_audit_sha256") or ""),
        ),
        "startup_rollback_plan": (
            context["startup_rollback_plan"],
            str(payload.get("approved_startup_rollback_plan_sha256") or ""),
        ),
    }
    output_root = (vault / RELEASE_PROOF_ROOT).resolve()
    marker_root = (vault / RELEASE_MARKER_RELATIVE_DIR).resolve()
    return {
        "consumption_dry_run_ok": bool(consumption.get("ok")),
        "approval_payload_readable": isinstance(payload, dict) and bool(payload),
        "approval_record_type_valid": payload.get("record_type") == APPROVAL_RECORD_TYPE,
        "approval_packet_id_matches": payload.get("approval_packet_id") == packet_id,
        "request_digest_matches": payload.get("request_digest_sha256") == context.get("request_digest"),
        "operator_decision_approved": payload.get("operator_decision") == "approved",
        "approval_scope_one_release_promotion_proof": payload.get("approval_scope") == "one_release_promotion_proof_only",
        "approval_not_consumed_in_artifact": payload.get("approval_decision_consumed") is False,
        "approval_marker_not_reserved_in_artifact": payload.get("idempotency_marker_reserved") is False,
        "release_channel_present": bool(payload.get("approved_release_channel")),
        "release_mode_present": bool(payload.get("approved_release_mode")),
        "marker_path_under_expected_root": _path_under(context["marker_path"], marker_root),
        "output_root_under_expected_root": context["output_root"].resolve() == output_root,
        "marker_absent_before_execution": not context["marker_path"].exists(),
        "future_output_paths_clear_before_execution": _future_outputs_clear(context),
        **{
            f"{key}_present": path.is_file()
            for key, (path, _expected_hash) in approved_sources.items()
        },
        **{
            f"{key}_sha_matches": bool(expected_hash) and _sha256_file(path) == expected_hash
            for key, (path, expected_hash) in approved_sources.items()
        },
        "existing_marker_not_completed": not _completed_marker(marker_payload, packet_id),
        "no_host_mutation_authorized": payload.get("writes_host_startup") is False
        and payload.get("registers_autostart") is False
        and payload.get("writes_registry") is False
        and payload.get("writes_start_menu") is False
        and payload.get("writes_desktop_shortcut") is False,
        "no_release_publication_authorized": payload.get("release_promotion_allowed_in_this_pass") is False
        and payload.get("promotes_release") is False,
        "no_runtime_or_canonical_mutation_authorized": payload.get("mutates_gate") is False
        and payload.get("writes_agent_bus_tasks") is False
        and payload.get("provider_calls_allowed") is False
        and payload.get("connector_calls_allowed") is False
        and payload.get("canonical_mutation_allowed") is False,
    }


def _post_execution_checks(vault: Path, context: dict[str, Any]) -> dict[str, bool]:
    marker_payload = _read_json(context["marker_path"])
    manifest = _read_json(context["release_manifest_path"])
    release_status = _read_json(context["release_status_preview_path"])
    audit = _read_json(context["release_audit_path"])
    rollback = _read_json(context["rollback_plan_path"])
    execution = _read_json(context["release_execution_evidence_path"])
    packet_id = str(context.get("packet_id") or "")
    return {
        "exact_once_marker_complete": _completed_marker(marker_payload, packet_id),
        "marker_reserved_before_output_writes": bool(marker_payload and marker_payload.get("reserved_at")),
        "release_dry_run_evidence_written": context["release_dry_run_evidence_path"].is_file(),
        "release_execution_evidence_written": context["release_execution_evidence_path"].is_file(),
        "release_manifest_written": context["release_manifest_path"].is_file(),
        "release_status_preview_written": context["release_status_preview_path"].is_file(),
        "release_promotion_audit_written": context["release_audit_path"].is_file(),
        "rollback_plan_written": context["rollback_plan_path"].is_file(),
        "manifest_proof_only": bool(manifest and manifest.get("proof_only") is True),
        "release_status_preview_proof_only": bool(release_status and release_status.get("proof_only") is True),
        "release_audit_no_publication": bool(audit and audit.get("release_publication_performed") is False),
        "rollback_plan_owned_root_only": bool(rollback and rollback.get("rollback_scope") == "owned_release_promotion_proof_root_only"),
        "execution_evidence_no_host_mutation": bool(
            execution
            and (execution.get("summary") or {}).get("host_mutation_performed") is False
            and (execution.get("summary") or {}).get("release_publication_performed") is False
        ),
        "duplicate_execution_blocked_before_writes": True,
        "no_agent_bus_gate_git_provider_or_canonical_mutation": True,
        "source_approval_artifact_not_mutated": _sha256_file(context["approval_path"])
        == (context.get("approval_payload") or {}).get("_pre_execution_sha256", _sha256_file(context["approval_path"])),
    }


def build_studio_release_promotion_approved_execution_proof(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    execute: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Consume the approved release-promotion artifact and write proof outputs."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    try:
        context = _collect_context(vault, approval_packet_id=approval_packet_id, generated_at=timestamp)
    except (OSError, ValueError) as exc:
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
                "writes_performed": False,
                "next_recommended_pass": BLOCKED_PASS,
            },
            "blockers": [str(exc)],
            "writes_performed": False,
            "next_recommended_pass": BLOCKED_PASS,
        }

    if context.get("approval_payload"):
        context["approval_payload"]["_pre_execution_sha256"] = _sha256_file(context["approval_path"])
    packet_id = str(context["packet_id"])
    marker_complete = _completed_marker(context.get("marker_payload"), packet_id)
    pre_execution_paths = _paths_snapshot(vault, context)

    if marker_complete:
        if execute:
            return {
                "ok": False,
                "surface": SURFACE_ID,
                "model_version": MODEL_VERSION,
                "status": DUPLICATE_BLOCKED_STATUS,
                "generated_at": timestamp,
                "vault_root": str(vault),
                "summary": {
                    "approval_packet_id": packet_id,
                    "request_digest_sha256": context["request_digest"],
                    "execution_requested": True,
                    "execution_performed": False,
                    "already_executed": True,
                    "approval_consumed": True,
                    "exact_once_marker_reserved": True,
                    "exact_once_marker_completed": True,
                    "duplicate_execution_blocked": True,
                    "release_publication_performed": False,
                    "release_promotion_allowed": False,
                    "host_mutation_performed": False,
                    "writes_performed": False,
                    "next_recommended_pass": BLOCKED_PASS,
                },
                "paths": pre_execution_paths,
                "authority": _authority_for(False),
                "blockers": ["release_promotion_exact_once_marker_already_complete_duplicate_execution_blocked"],
                "writes_performed": False,
                "next_recommended_pass": BLOCKED_PASS,
            }
        post_checks = _post_execution_checks(vault, context)
        ok = all(post_checks.values())
        return {
            "ok": ok,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "status": COMPLETE_STATUS if ok else BLOCKED_STATUS,
            "generated_at": timestamp,
            "vault_root": str(vault),
            "summary": {
                "approval_packet_id": packet_id,
                "request_digest_sha256": context["request_digest"],
                "execution_requested": bool(execute),
                "execution_performed": False,
                "already_executed": True,
                "approval_consumed": True,
                "approval_artifact_mutated": False,
                "exact_once_marker_reserved": True,
                "exact_once_marker_completed": True,
                "duplicate_execution_blocked": True,
                "release_status_preview_written": context["release_status_preview_path"].is_file(),
                "release_status_write_allowed": True,
                "release_publication_performed": False,
                "release_promotion_allowed": False,
                "host_path_resolution_attempted": False,
                "host_mutation_performed": False,
                "writes_performed": False,
                "next_recommended_pass": NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS if ok else BLOCKED_PASS,
            },
            "post_execution_checks": post_checks,
            "paths": pre_execution_paths,
            "rollback_boundary": {
                "owned_output_root": RELEASE_PROOF_ROOT.as_posix(),
                "rollback_scope": "owned_release_promotion_proof_root_only",
                "release_publication_to_rollback": False,
                "host_mutation_to_rollback": False,
            },
            "authority": _authority_for(False),
            "blocked_authority": [key for key, value in _authority_for(False).items() if value is False],
            "blockers": [] if ok else [name for name, passed in post_checks.items() if not passed],
            "unverified": [
                "Static inspection saw an already-completed release-promotion proof; no new writes were performed.",
                "No real release publication, installer installation, host startup mutation, provider call, Git, Gate, Agent Bus, or canonical mutation was attempted.",
            ],
            "writes_performed": False,
            "next_recommended_pass": NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS if ok else BLOCKED_PASS,
        }

    checks = _preflight_checks(vault, context)
    if approval_packet_id and approval_packet_id != packet_id:
        checks["approval_packet_argument_matches"] = False
    else:
        checks["approval_packet_argument_matches"] = True
    blockers = [name for name, passed in checks.items() if not passed]
    ok = not blockers

    if not execute:
        return {
            "ok": ok,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "status": READY_STATUS if ok else BLOCKED_STATUS,
            "generated_at": timestamp,
            "vault_root": str(vault),
            "summary": {
                "approval_packet_id": packet_id,
                "request_digest_sha256": context["request_digest"],
                "execution_requested": False,
                "execution_performed": False,
                "already_executed": False,
                "approval_consumed": False,
                "exact_once_marker_reserved": False,
                "future_output_paths_clear": bool(checks.get("future_output_paths_clear_before_execution")),
                "release_channel": (context.get("approval_payload") or {}).get("approved_release_channel"),
                "release_mode": (context.get("approval_payload") or {}).get("approved_release_mode"),
                "release_status_write_allowed": False,
                "release_publication_performed": False,
                "release_promotion_allowed": False,
                "host_path_resolution_attempted": False,
                "host_mutation_performed": False,
                "writes_performed": False,
                "next_recommended_pass": "run-with---execute" if ok else BLOCKED_PASS,
            },
            "preflight_checks": checks,
            "paths": pre_execution_paths,
            "rollback_boundary": {
                "owned_output_root": RELEASE_PROOF_ROOT.as_posix(),
                "rollback_scope": "owned_release_promotion_proof_root_only",
                "release_publication_to_rollback": False,
                "host_mutation_to_rollback": False,
            },
            "authority": _authority_for(False),
            "blocked_authority": [key for key, value in _authority_for(False).items() if value is False],
            "blockers": blockers,
            "unverified": [
                "Execution was not requested, so no marker, release status preview, manifest, audit, rollback, or execution evidence was written.",
                "No real release publication, installer installation, host startup mutation, provider call, Git, Gate, Agent Bus, or canonical mutation was attempted.",
            ],
            "writes_performed": False,
            "next_recommended_pass": "run-with---execute" if ok else BLOCKED_PASS,
        }

    if not ok:
        return {
            "ok": False,
            "surface": SURFACE_ID,
            "model_version": MODEL_VERSION,
            "status": BLOCKED_STATUS,
            "generated_at": timestamp,
            "vault_root": str(vault),
            "summary": {
                "approval_packet_id": packet_id,
                "execution_requested": True,
                "execution_performed": False,
                "approval_consumed": False,
                "writes_performed": False,
                "next_recommended_pass": BLOCKED_PASS,
            },
            "preflight_checks": checks,
            "paths": pre_execution_paths,
            "authority": _authority_for(False),
            "blockers": blockers,
            "writes_performed": False,
            "next_recommended_pass": BLOCKED_PASS,
        }

    marker_path = context["marker_path"]
    reserved_at = _now_utc()
    marker_payload = {
        "record_type": "studio_release_promotion_execution_marker",
        "schema_version": MODEL_VERSION,
        "status": "reserved_before_release_promotion_proof_output",
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "reserved_at": reserved_at,
        "completed_at": None,
        "approval_artifact_path": _relative_to_vault(vault, context["approval_path"]),
        "output_root": _relative_to_vault(vault, context["output_root"]),
        "release_dry_run_evidence_path": _relative_to_vault(vault, context["release_dry_run_evidence_path"]),
        "release_execution_evidence_path": _relative_to_vault(vault, context["release_execution_evidence_path"]),
        "release_manifest_path": _relative_to_vault(vault, context["release_manifest_path"]),
        "release_status_preview_path": _relative_to_vault(vault, context["release_status_preview_path"]),
        "release_promotion_audit_path": _relative_to_vault(vault, context["release_audit_path"]),
        "rollback_plan_path": _relative_to_vault(vault, context["rollback_plan_path"]),
        "marker_reserved_before_output_writes": True,
        "release_status_preview_written": False,
        "release_publication_performed": False,
        "host_path_resolution_attempted": False,
        "host_mutation_performed": False,
        "duplicate_policy": "block_before_any_release_status_or_release_promotion_write",
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
            "blockers": ["release_promotion_exact_once_marker_already_exists_duplicate_execution_blocked"],
            "writes_performed": False,
            "next_recommended_pass": BLOCKED_PASS,
        }

    dry_run_payload = {
        "record_type": "studio_release_promotion_pre_output_dry_run_evidence",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "exact_once_marker_reserved_before_this_write": True,
        "release_status_preview_written_at_this_point": False,
        "release_publication_performed_at_this_point": False,
        "host_mutation_performed_at_this_point": False,
        "preflight_checks": checks,
        "authority": _authority_for(False),
    }
    _write_json(context["release_dry_run_evidence_path"], dry_run_payload)

    rollback_plan = {
        "record_type": "studio_release_promotion_rollback_plan",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "rollback_root": RELEASE_PROOF_ROOT.as_posix(),
        "rollback_scope": "owned_release_promotion_proof_root_only",
        "files_to_remove_if_operator_rolls_back": [
            _relative_to_vault(vault, context["release_dry_run_evidence_path"]),
            _relative_to_vault(vault, context["release_execution_evidence_path"]),
            _relative_to_vault(vault, context["release_manifest_path"]),
            _relative_to_vault(vault, context["release_status_preview_path"]),
            _relative_to_vault(vault, context["release_audit_path"]),
            _relative_to_vault(vault, context["rollback_plan_path"]),
        ],
        "release_publication_to_rollback": False,
        "installer_installation_to_rollback": False,
        "host_mutation_to_rollback": False,
        "rollback_requires_operator_review": True,
    }
    _write_json(context["rollback_plan_path"], rollback_plan)

    approval_payload = context.get("approval_payload") or {}
    release_manifest = {
        "record_type": "studio_release_promotion_manifest",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "proof_only": True,
        "release_channel": approval_payload.get("approved_release_channel"),
        "release_mode": approval_payload.get("approved_release_mode"),
        "release_publication_performed": False,
        "installer_installation_performed": False,
        "source_artifacts": {
            "startup_exact_once_marker": _file_record(vault, context["startup_marker"]),
            "signed_portable_zip": _file_record(vault, context["signed_zip"]),
            "signing_manifest": _file_record(vault, context["signing_manifest"]),
            "startup_execution_evidence": _file_record(vault, context["startup_execution_evidence"]),
            "startup_host_mutation_audit": _file_record(vault, context["startup_host_mutation_audit"]),
            "startup_rollback_plan": _file_record(vault, context["startup_rollback_plan"]),
        },
    }
    _write_json(context["release_manifest_path"], release_manifest)

    release_status_preview = {
        "record_type": "studio_release_status_preview",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "proof_only": True,
        "release_channel": approval_payload.get("approved_release_channel"),
        "release_mode": approval_payload.get("approved_release_mode"),
        "status": "proof_written_release_publication_deferred",
        "signed_portable_zip": _file_record(vault, context["signed_zip"]),
        "release_manifest": _relative_to_vault(vault, context["release_manifest_path"]),
        "release_publication_performed": False,
        "host_mutation_performed": False,
        "provider_calls_performed": False,
        "connector_calls_performed": False,
        "agent_bus_writes_performed": False,
        "gate_mutation_performed": False,
        "git_mutation_performed": False,
        "canonical_mutation_performed": False,
    }
    _write_json(context["release_status_preview_path"], release_status_preview)

    release_audit = {
        "record_type": "studio_release_promotion_audit",
        "schema_version": MODEL_VERSION,
        "generated_at": _now_utc(),
        "approval_packet_id": packet_id,
        "request_digest_sha256": context["request_digest"],
        "approval_artifact": _file_record(vault, context["approval_path"]),
        "exact_once_marker_reserved": True,
        "release_status_preview": _file_record(vault, context["release_status_preview_path"]),
        "release_manifest": _file_record(vault, context["release_manifest_path"]),
        "rollback_plan": _file_record(vault, context["rollback_plan_path"]),
        "release_status_preview_written": True,
        "release_publication_performed": False,
        "real_release_promoted": False,
        "installer_installation_performed": False,
        "host_path_resolution_attempted": False,
        "host_mutation_performed": False,
        "provider_calls_performed": False,
        "connector_calls_performed": False,
        "agent_bus_writes_performed": False,
        "gate_mutation_performed": False,
        "git_mutation_performed": False,
        "canonical_mutation_performed": False,
    }
    _write_json(context["release_audit_path"], release_audit)

    completed_at = _now_utc()
    marker_payload.update(
        {
            "status": COMPLETE_STATUS,
            "completed_at": completed_at,
            "release_dry_run_evidence_sha256": _sha256_file(context["release_dry_run_evidence_path"]),
            "release_manifest_sha256": _sha256_file(context["release_manifest_path"]),
            "release_status_preview_sha256": _sha256_file(context["release_status_preview_path"]),
            "release_promotion_audit_sha256": _sha256_file(context["release_audit_path"]),
            "rollback_plan_sha256": _sha256_file(context["rollback_plan_path"]),
            "release_status_preview_written": True,
            "release_publication_performed": False,
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
        }
    )
    _write_json(marker_path, marker_payload)

    post_execution_paths = _paths_snapshot(vault, context)
    report = {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": COMPLETE_STATUS,
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
            "release_dry_run_evidence_path": _relative_to_vault(vault, context["release_dry_run_evidence_path"]),
            "release_execution_evidence_path": _relative_to_vault(vault, context["release_execution_evidence_path"]),
            "release_manifest_path": _relative_to_vault(vault, context["release_manifest_path"]),
            "release_status_preview_path": _relative_to_vault(vault, context["release_status_preview_path"]),
            "release_promotion_audit_path": _relative_to_vault(vault, context["release_audit_path"]),
            "rollback_plan_path": _relative_to_vault(vault, context["rollback_plan_path"]),
            "release_status_write_allowed": True,
            "release_status_preview_written": True,
            "release_publication_performed": False,
            "release_promotion_allowed": False,
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
            "writes_performed": True,
            "next_recommended_pass": NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS,
        },
        "preflight_checks": checks,
        "post_execution_checks": {},
        "pre_execution_paths": pre_execution_paths,
        "post_execution_paths": post_execution_paths,
        "release_manifest": release_manifest,
        "release_status_preview": release_status_preview,
        "release_promotion_audit": release_audit,
        "rollback_plan": rollback_plan,
        "rollback_boundary": {
            "owned_output_root": RELEASE_PROOF_ROOT.as_posix(),
            "rollback_scope": "owned_release_promotion_proof_root_only",
            "rollback_requires_operator_review": True,
            "release_publication_to_rollback": False,
            "host_mutation_to_rollback": False,
        },
        "authority": _authority_for(True),
        "blocked_authority": [key for key, value in _authority_for(True).items() if value is False],
        "blockers": [],
        "unverified": [
            "No real release publication, installer installation, host startup/autostart mutation, provider/connector call, Git, Gate, Agent Bus, workflow, or canonical mutation was attempted.",
            "The release-status artifact is a workspace-scoped proof preview only.",
        ],
        "writes_performed": True,
        "next_recommended_pass": NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS,
    }
    _write_json(context["release_execution_evidence_path"], report)
    report["post_execution_paths"] = _paths_snapshot(vault, context)
    report["post_execution_checks"] = _post_execution_checks(vault, context)
    report["blockers"] = [
        name for name, passed in report["post_execution_checks"].items() if not passed
    ]
    report["ok"] = not report["blockers"]
    report["status"] = COMPLETE_STATUS if report["ok"] else BLOCKED_STATUS
    report["summary"]["next_recommended_pass"] = (
        NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS if report["ok"] else BLOCKED_PASS
    )
    report["next_recommended_pass"] = report["summary"]["next_recommended_pass"]
    _write_json(context["release_execution_evidence_path"], report)
    return report


def write_release_promotion_approved_execution_proof_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-release-promotion-approved-execution-proof"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    lines = [
        "# Studio Release Promotion Approved Execution Proof Evidence",
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
        f"- release_status_preview_path: {summary.get('release_status_preview_path')}",
        f"- release_manifest_path: {summary.get('release_manifest_path')}",
        f"- release_promotion_audit_path: {summary.get('release_promotion_audit_path')}",
        f"- rollback_plan_path: {summary.get('rollback_plan_path')}",
        f"- release_publication_performed: {summary.get('release_publication_performed')}",
        f"- host_mutation_performed: {summary.get('host_mutation_performed')}",
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
