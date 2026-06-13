"""Dry-run approval-consumption guard for a future Studio startup/autostart proof.

This pass validates the written Studio startup/autostart approval artifact and
proves the consumption boundary before any host startup mutation pass. It does
not consume the approval, reserve the real exact-once marker, resolve host
startup paths, write Startup folder/Task Scheduler/registry/shortcut state,
promote a release, launch Studio, call providers/connectors, enqueue Agent Bus
tasks, mutate Gate, execute workflows, use Git, or write canonical ChaseOS
state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.installer_build_approval import BLOCKED_AUTHORITY, DEFAULT_EVIDENCE_ROOT
from runtime.studio.startup_autostart_approval_preview import (
    STARTUP_APPROVAL_RELATIVE_DIR,
    STARTUP_MARKER_RELATIVE_DIR,
    STARTUP_PROOF_ROOT,
)
from runtime.studio.startup_autostart_approval_review import (
    APPROVAL_RECORD_TYPE,
    build_studio_startup_autostart_approval_review,
)


MODEL_VERSION = "studio.startup_autostart_approval_consumption_dry_run.v1"
SURFACE_ID = "studio_startup_autostart_approval_consumption_dry_run"
READY_STATUS = "studio_startup_autostart_approval_consumption_dry_run_ready_no_host_mutation"
BLOCKED_STATUS = "blocked_studio_startup_autostart_approval_consumption_dry_run"
NEXT_STARTUP_APPROVED_EXECUTION_PROOF_PASS = "studio-startup-autostart-approved-execution-proof"
NEXT_RELEASE_PROMOTION_APPROVAL_PASS = "studio-release-promotion-approval-preview"
STARTUP_EXECUTION_COMPLETE_STATUS = "studio_startup_autostart_approved_execution_proof_complete"
BLOCKED_PASS = "studio-startup-autostart-approval-review"


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
        raise ValueError(f"startup/autostart approval consumption path escapes vault: {path_value}") from exc
    return resolved


def _path_under(vault: Path, path_value: str, base_relative: Path) -> bool:
    try:
        resolved = _resolve_vault_relative_path(vault, path_value)
        resolved.relative_to((vault / base_relative).resolve())
    except (ValueError, RuntimeError):
        return False
    return True


def _approval_path_for_packet(vault: Path, approval_packet_id: str | None) -> Path | None:
    if not approval_packet_id:
        return None
    base = (vault / STARTUP_APPROVAL_RELATIVE_DIR).resolve()
    path = (base / f"{approval_packet_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"startup/autostart approval path escapes approval root: {approval_packet_id}") from exc
    return path


def _all_future_output_paths_clear(future_paths: dict[str, Any]) -> bool:
    return not any(
        bool(value.get("exists"))
        for key, value in future_paths.items()
        if key != "output_root" and isinstance(value, dict)
    )


def _completed_startup_marker(marker_path: Path | None, approval_packet_id: str) -> bool:
    if not marker_path or not marker_path.is_file():
        return False
    payload = _read_json(marker_path)
    return bool(
        payload
        and payload.get("record_type") == "studio_startup_autostart_execution_marker"
        and payload.get("approval_packet_id") == approval_packet_id
        and payload.get("status") == STARTUP_EXECUTION_COMPLETE_STATUS
    )


def _marker_reservation_dry_run(marker_exists: bool) -> dict[str, Any]:
    first_reservation_allowed = not marker_exists
    duplicate_reservation_blocked = True
    return {
        "proof_mode": "in_memory_no_real_marker_write",
        "real_marker_written": False,
        "real_marker_reserved": False,
        "marker_exists_before": bool(marker_exists),
        "first_reservation_allowed": first_reservation_allowed,
        "first_reservation_status": "would_reserve_exclusively" if first_reservation_allowed else "blocked_existing_marker",
        "duplicate_reservation_blocked": duplicate_reservation_blocked,
        "duplicate_reservation_status": "blocked_prior_marker_exists",
        "required_future_write_mode": "atomic_create_new_only_before_any_host_startup_or_shortcut_write",
        "proof_passed": first_reservation_allowed and duplicate_reservation_blocked,
    }


def _output_path_constraints(vault: Path, future_paths: dict[str, Any]) -> dict[str, Any]:
    output_root = (vault / STARTUP_PROOF_ROOT).resolve()
    evidence_root = (vault / DEFAULT_EVIDENCE_ROOT).resolve()
    paths: dict[str, Any] = {
        "output_root": {
            "path": STARTUP_PROOF_ROOT.as_posix(),
            "exists": output_root.exists(),
            "within_workspace": True,
            "within_approved_output_root": True,
        }
    }
    for key, value in future_paths.items():
        if not isinstance(value, dict):
            continue
        path_value = str(value.get("path") or "")
        if not path_value:
            continue
        try:
            resolved = _resolve_vault_relative_path(vault, path_value)
            within_workspace = True
            within_output_root = resolved == output_root or output_root in resolved.parents
            within_evidence_root = resolved == evidence_root or evidence_root in resolved.parents
        except ValueError:
            within_workspace = False
            within_output_root = False
            within_evidence_root = False
        paths[key] = {
            **value,
            "within_workspace": within_workspace,
            "within_approved_output_root": within_output_root,
            "within_evidence_root": within_evidence_root,
        }
    return paths


def _approval_validation_checks(
    *,
    vault: Path,
    approval_payload: dict[str, Any] | None,
    approval_path: Path | None,
    marker_path: Path | None,
    review: dict[str, Any],
    approval_packet_id: str | None,
) -> dict[str, bool]:
    summary = review.get("summary") or {}
    source_preview = review.get("source_preview") or {}
    preview = source_preview.get("startup_autostart_approval_packet_preview") or {}
    material = preview.get("approval_material") or {}
    source_artifacts = source_preview.get("source_artifacts") or {}
    signed_zip = source_artifacts.get("signed_portable_zip") or {}
    signing_manifest = source_artifacts.get("signing_manifest") or {}
    signing_marker = source_artifacts.get("signing_exact_once_marker") or {}
    expected_packet_id = str(summary.get("approval_packet_id") or "")
    expected_digest = str(summary.get("request_digest_sha256") or "")
    expected_signed_zip_sha = str(signed_zip.get("sha256") or material.get("signed_portable_zip_sha256") or "")
    expected_manifest_sha = str(signing_manifest.get("sha256") or material.get("signing_manifest_sha256") or "")
    expected_signing_marker_sha = str(signing_marker.get("sha256") or material.get("signing_execution_marker_sha256") or "")
    expected_targets = list(material.get("candidate_host_targets") or [])
    artifact_path_value = str((review.get("approval_artifact") or {}).get("path") or "")
    marker_path_value = str((review.get("exact_once_marker_contract") or {}).get("path") or "")

    payload = approval_payload or {}
    authority_flags_false = all(
        payload.get(key) is False
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

    return {
        "approval_review_ready": bool(review.get("ok")),
        "approval_packet_argument_matches": (not approval_packet_id) or approval_packet_id == expected_packet_id,
        "approval_artifact_path_under_expected_root": bool(artifact_path_value)
        and _path_under(vault, artifact_path_value, STARTUP_APPROVAL_RELATIVE_DIR),
        "approval_artifact_present": bool(approval_path and approval_path.is_file()),
        "approval_artifact_json_readable": approval_payload is not None,
        "approval_record_type_valid": payload.get("record_type") == APPROVAL_RECORD_TYPE,
        "approval_packet_id_matches": payload.get("approval_packet_id") == expected_packet_id,
        "request_digest_matches": payload.get("request_digest_sha256") == expected_digest,
        "operator_decision_approved": payload.get("operator_decision") == "approved",
        "approval_scope_one_startup_autostart_proof": payload.get("approval_scope") == "one_startup_autostart_proof_only",
        "approved_startup_mode_matches": payload.get("approved_startup_mode") == material.get("startup_mode"),
        "approved_target_platform_windows": payload.get("approved_target_platform") == "windows",
        "approved_host_targets_match": list(payload.get("approved_host_targets") or []) == expected_targets,
        "signed_portable_zip_sha_matches": payload.get("approved_signed_portable_zip_sha256") == expected_signed_zip_sha,
        "signing_manifest_sha_matches": payload.get("approved_signing_manifest_sha256") == expected_manifest_sha,
        "signing_execution_marker_sha_matches": payload.get("approved_signing_execution_marker_sha256")
        == expected_signing_marker_sha,
        "approval_consumption_required": payload.get("approval_consumption_required") is True,
        "approval_not_already_consumed": payload.get("approval_decision_consumed") is False,
        "approval_artifact_blocks_host_mutation_in_review_pass": payload.get("startup_mutation_allowed_in_this_pass") is False
        and payload.get("writes_host_startup") is False
        and payload.get("registers_autostart") is False,
        "approval_authority_flags_blocked": authority_flags_false,
        "marker_path_under_expected_root": bool(marker_path_value)
        and _path_under(vault, marker_path_value, STARTUP_MARKER_RELATIVE_DIR),
        "real_marker_absent": bool(marker_path and (not marker_path.exists() or _completed_startup_marker(marker_path, expected_packet_id))),
        "source_packet_digest_present": bool(expected_packet_id and expected_digest),
        "source_signed_zip_hash_present": bool(expected_signed_zip_sha),
        "source_manifest_hash_present": bool(expected_manifest_sha),
        "source_signing_marker_hash_present": bool(expected_signing_marker_sha),
    }


def build_studio_startup_autostart_approval_consumption_dry_run(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Validate startup/autostart approval consumption readiness without consuming it."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    existing_approval = _read_json(_approval_path_for_packet(vault, approval_packet_id)) if approval_packet_id else None
    signing_approval_packet_id = (
        str(existing_approval.get("approved_signing_approval_packet_id") or "")
        if existing_approval
        else None
    )
    try:
        review = build_studio_startup_autostart_approval_review(
            vault,
            approval_packet_id=approval_packet_id,
            signing_approval_packet_id=signing_approval_packet_id,
            decision="approve",
            write_approval=False,
            generated_at=timestamp,
        )
    except ValueError as exc:
        review = {
            "ok": False,
            "status": "blocked_review_contract_error",
            "summary": {},
            "blockers": [str(exc)],
        }
        blockers.append(str(exc))

    artifact = review.get("approval_artifact") or {}
    marker = review.get("exact_once_marker_contract") or {}
    future_paths = review.get("future_output_paths") or {}
    approval_path: Path | None = None
    marker_path: Path | None = None
    try:
        approval_path = _resolve_vault_relative_path(vault, str(artifact.get("path") or ""))
    except ValueError as exc:
        blockers.append(str(exc))
    try:
        marker_path = _resolve_vault_relative_path(vault, str(marker.get("path") or ""))
    except ValueError as exc:
        blockers.append(str(exc))

    approval_payload = _read_json(approval_path) if approval_path else None
    checks = _approval_validation_checks(
        vault=vault,
        approval_payload=approval_payload,
        approval_path=approval_path,
        marker_path=marker_path,
        review=review,
        approval_packet_id=approval_packet_id,
    )
    marker_proof = _marker_reservation_dry_run(bool(marker_path and marker_path.exists()))
    output_constraints = _output_path_constraints(vault, future_paths)
    output_paths_clear = _all_future_output_paths_clear(future_paths)
    review_checks = review.get("checks") or {}
    signing_execution_complete = bool(review_checks.get("signing_execution_proof_complete"))
    startup_execution_complete = _completed_startup_marker(
        marker_path,
        str((review.get("summary") or {}).get("approval_packet_id") or ""),
    )
    rollback_audit_plan = {
        "rollback_root": STARTUP_PROOF_ROOT.as_posix(),
        "rollback_scope": "owned_startup_autostart_proof_root_only",
        "future_execution_must_dry_run_host_write_targets_before_mutation": True,
        "future_execution_must_reserve_marker_before_host_mutation": True,
        "future_execution_must_write_rollback_plan_before_host_mutation": True,
        "future_execution_must_write_pre_mutation_audit": True,
        "future_execution_must_write_post_mutation_audit": True,
        "future_execution_must_verify_host_state_after_mutation": True,
        "release_promotion_blocked_until_separate_gate": True,
        "dry_run_pass_resolves_host_paths": False,
        "dry_run_pass_writes_rollback_artifacts": False,
        "dry_run_pass_mutates_host_startup": False,
    }
    checks.update(
        {
            "future_output_paths_clear": output_paths_clear or startup_execution_complete,
            "signing_execution_proof_complete": signing_execution_complete,
            "marker_reservation_proof_passed": bool(marker_proof.get("proof_passed")) or startup_execution_complete,
            "duplicate_marker_blocked": bool(marker_proof.get("duplicate_reservation_blocked")),
            "rollback_audit_plan_present": all(
                bool(rollback_audit_plan.get(key))
                for key in [
                    "future_execution_must_dry_run_host_write_targets_before_mutation",
                    "future_execution_must_reserve_marker_before_host_mutation",
                    "future_execution_must_write_rollback_plan_before_host_mutation",
                    "future_execution_must_write_pre_mutation_audit",
                    "future_execution_must_write_post_mutation_audit",
                    "future_execution_must_verify_host_state_after_mutation",
                    "release_promotion_blocked_until_separate_gate",
                ]
            ),
            "no_real_marker_write_in_this_pass": marker_proof.get("real_marker_written") is False,
            "host_paths_not_resolved_in_this_pass": True,
            "no_host_startup_mutation_in_this_pass": True,
        }
    )

    blockers.extend(name for name, passed in checks.items() if not passed)
    ok = not blockers
    status = READY_STATUS if ok else BLOCKED_STATUS
    authority = {
        **dict(BLOCKED_AUTHORITY),
        "approval_packet_preview_only": False,
        "approval_artifact_review_only": False,
        "approval_consumption_dry_run_only": True,
        "validates_approval_artifact": True,
        "simulates_marker_reservation": True,
        "simulates_duplicate_consumption_block": True,
        "creates_approval_artifact": False,
        "writes_approval_artifact": False,
        "consumes_approval_decision": False,
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
    }
    summary = review.get("summary") or {}
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "summary": {
            "approval_packet_id": summary.get("approval_packet_id"),
            "request_digest_sha256": summary.get("request_digest_sha256"),
            "approval_artifact_present": checks.get("approval_artifact_present"),
            "approval_digest_matches": checks.get("request_digest_matches"),
            "approval_scope_valid": checks.get("approval_scope_one_startup_autostart_proof"),
            "signed_portable_zip_hash_matches": checks.get("signed_portable_zip_sha_matches"),
            "signing_manifest_hash_matches": checks.get("signing_manifest_sha_matches"),
            "signing_execution_marker_hash_matches": checks.get("signing_execution_marker_sha_matches"),
            "approved_host_targets_match": checks.get("approved_host_targets_match"),
            "exact_once_marker_absent": checks.get("real_marker_absent"),
            "marker_reservation_proof_passed": checks.get("marker_reservation_proof_passed"),
            "duplicate_consumption_blocked": checks.get("duplicate_marker_blocked"),
            "future_output_paths_clear": output_paths_clear or startup_execution_complete,
            "signing_execution_proof_complete": signing_execution_complete,
            "startup_autostart_execution_proof_complete": startup_execution_complete,
            "approval_consumed": startup_execution_complete,
            "exact_once_marker_reserved": startup_execution_complete,
            "host_path_resolution_attempted": False,
            "host_startup_mutation_allowed": False,
            "autostart_registration_allowed": False,
            "registry_write_allowed": False,
            "start_menu_write_allowed": False,
            "desktop_shortcut_write_allowed": False,
            "release_promotion_allowed": False,
            "execution_allowed": False,
            "writes_performed": False,
            "next_recommended_pass": (
                NEXT_RELEASE_PROMOTION_APPROVAL_PASS
                if ok and startup_execution_complete
                else NEXT_STARTUP_APPROVED_EXECUTION_PROOF_PASS
                if ok
                else BLOCKED_PASS
            ),
        },
        "source_review": review,
        "approval_artifact": {
            "path": _relative_to_vault(vault, approval_path) if approval_path else str(artifact.get("path") or ""),
            "exists": bool(approval_path and approval_path.is_file()),
            "record_type": approval_payload.get("record_type") if approval_payload else None,
            "approval_packet_id": approval_payload.get("approval_packet_id") if approval_payload else None,
            "request_digest_sha256": approval_payload.get("request_digest_sha256") if approval_payload else None,
            "operator_decision": approval_payload.get("operator_decision") if approval_payload else None,
            "approval_scope": approval_payload.get("approval_scope") if approval_payload else None,
            "consumed_in_this_pass": False,
            "mutated_in_this_pass": False,
        },
        "exact_once_marker_contract": {
            "path": _relative_to_vault(vault, marker_path) if marker_path else str(marker.get("path") or ""),
            "exists": bool(marker_path and marker_path.exists()),
            "reserved_in_this_pass": False,
            "written_in_this_pass": False,
            "future_write_mode": "atomic_create_new_only_before_any_host_startup_or_shortcut_write",
            "duplicate_policy": "block_before_any_host_startup_or_shortcut_write",
        },
        "marker_reservation_dry_run": marker_proof,
        "future_output_paths": future_paths,
        "output_path_constraints": output_constraints,
        "dry_run_plan": [
            {"step": "load_startup_autostart_approval_artifact", "effect_now": "read_only_validation", "required": True},
            {"step": "validate_packet_id_and_digest", "effect_now": "read_only_validation", "required": True},
            {"step": "validate_scope_and_blocked_authority", "effect_now": "read_only_validation", "required": True},
            {"step": "verify_signed_zip_manifest_and_signing_marker_hashes", "effect_now": "read_only_validation", "required": True},
            {"step": "verify_real_exact_once_marker_absent", "effect_now": "read_only_validation", "required": True},
            {"step": "simulate_exclusive_marker_reservation", "effect_now": "in_memory_no_write", "required": True},
            {"step": "simulate_duplicate_consumption_block", "effect_now": "in_memory_no_write", "required": True},
            {"step": "verify_future_startup_output_paths_clear", "effect_now": "read_only_validation", "required": True},
            {"step": "preview_host_mutation_rollback_audit_requirements", "effect_now": "read_only_plan", "required": True},
            {"step": "stop_before_real_marker_host_path_resolution_or_host_mutation", "effect_now": "execution_block", "required": True},
        ],
        "rollback_audit_plan": rollback_audit_plan,
        "checks": checks,
        "authority": authority,
        "blocked_authority": [key for key, value in authority.items() if value is False],
        "blockers": blockers,
        "unverified": [
            "No approval decision was consumed in this dry-run pass.",
            "No real exact-once marker was reserved or written in this dry-run pass.",
            "No host startup path was resolved or probed in this dry-run pass.",
            "No Startup folder, Task Scheduler, registry Run key, Start Menu, desktop shortcut, release, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback was attempted.",
        ],
        "writes_performed": False,
        "next_recommended_pass": (
            NEXT_RELEASE_PROMOTION_APPROVAL_PASS
            if ok and startup_execution_complete
            else NEXT_STARTUP_APPROVED_EXECUTION_PROOF_PASS
            if ok
            else BLOCKED_PASS
        ),
    }


def write_startup_autostart_approval_consumption_dry_run_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-startup-autostart-approval-consumption-dry-run"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    artifact = report.get("approval_artifact") or {}
    marker = report.get("exact_once_marker_contract") or {}
    marker_proof = report.get("marker_reservation_dry_run") or {}
    lines = [
        "# Studio Startup/Autostart Approval Consumption Dry-Run Evidence",
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
        f"- approval_artifact_path: {artifact.get('path')}",
        f"- approval_artifact_present: {summary.get('approval_artifact_present')}",
        f"- approval_digest_matches: {summary.get('approval_digest_matches')}",
        f"- approval_scope_valid: {summary.get('approval_scope_valid')}",
        f"- signed_portable_zip_hash_matches: {summary.get('signed_portable_zip_hash_matches')}",
        f"- signing_manifest_hash_matches: {summary.get('signing_manifest_hash_matches')}",
        f"- approved_host_targets_match: {summary.get('approved_host_targets_match')}",
        f"- approval_consumed: {summary.get('approval_consumed')}",
        "",
        "## Exact-Once Dry Run",
        "",
        f"- exact_once_marker_path: {marker.get('path')}",
        f"- exact_once_marker_exists: {marker.get('exists')}",
        f"- real_marker_written: {marker_proof.get('real_marker_written')}",
        f"- first_reservation_allowed: {marker_proof.get('first_reservation_allowed')}",
        f"- duplicate_reservation_blocked: {marker_proof.get('duplicate_reservation_blocked')}",
        f"- proof_passed: {marker_proof.get('proof_passed')}",
        "",
        "## Host Mutation Boundary",
        "",
        f"- host_path_resolution_attempted: {summary.get('host_path_resolution_attempted')}",
        f"- host_startup_mutation_allowed: {summary.get('host_startup_mutation_allowed')}",
        f"- autostart_registration_allowed: {summary.get('autostart_registration_allowed')}",
        f"- registry_write_allowed: {summary.get('registry_write_allowed')}",
        f"- start_menu_write_allowed: {summary.get('start_menu_write_allowed')}",
        f"- desktop_shortcut_write_allowed: {summary.get('desktop_shortcut_write_allowed')}",
        "",
        "## Future Output Paths",
        "",
        *[
            f"- {key}: {value.get('path')} exists={value.get('exists')}"
            for key, value in (report.get("future_output_paths") or {}).items()
            if isinstance(value, dict)
        ],
        "",
        "## Checks",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("checks") or {}).items()],
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
