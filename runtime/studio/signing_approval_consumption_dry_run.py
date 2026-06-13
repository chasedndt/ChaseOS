"""Dry-run approval-consumption guard for a future Studio signing proof.

This pass validates the written Studio signing approval artifact and proves the
consumption boundary before any real signing pass. It does not consume the
approval, reserve the real exact-once marker, read signing certificates, sign
artifacts, write signed outputs, mutate startup/autostart, launch Studio, call
providers/connectors, enqueue Agent Bus tasks, mutate Gate, execute workflows,
use Git, or write canonical ChaseOS state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.studio.installer_build_approval import BLOCKED_AUTHORITY, DEFAULT_EVIDENCE_ROOT
from runtime.studio.signing_approval_preview import (
    SIGNING_APPROVAL_RELATIVE_DIR,
    SIGNING_MARKER_RELATIVE_DIR,
    SIGNING_OUTPUT_ROOT,
)
from runtime.studio.signing_approval_review import (
    APPROVAL_RECORD_TYPE,
    build_studio_signing_approval_review,
)


MODEL_VERSION = "studio.signing_approval_consumption_dry_run.v1"
SURFACE_ID = "studio_signing_approval_consumption_dry_run"
READY_STATUS = "studio_signing_approval_consumption_dry_run_ready_no_execution"
ALREADY_CONSUMED_STATUS = "studio_signing_approval_consumed_by_execution_proof"
BLOCKED_STATUS = "blocked_studio_signing_approval_consumption_dry_run"
NEXT_SIGNING_APPROVED_EXECUTION_PROOF_PASS = "studio-signing-approved-execution-proof"
NEXT_STARTUP_AUTOSTART_APPROVAL_PASS = "studio-startup-autostart-approval-preview"
BLOCKED_PASS = "operator-review-studio-signing-approval-packet"


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
        raise ValueError(f"signing approval consumption path escapes vault: {path_value}") from exc
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
    base = (vault / SIGNING_APPROVAL_RELATIVE_DIR).resolve()
    path = (base / f"{approval_packet_id}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"signing approval packet path escapes approval root: {approval_packet_id}") from exc
    return path


def _all_future_output_paths_clear(future_paths: dict[str, Any]) -> bool:
    return not any(
        bool(value.get("exists"))
        for key, value in future_paths.items()
        if key != "output_root" and isinstance(value, dict)
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
        "required_future_write_mode": "atomic_create_new_only_before_any_signing_output_write",
        "proof_passed": (not marker_exists) and duplicate_reservation_blocked,
    }


def _output_path_constraints(vault: Path, future_paths: dict[str, Any]) -> dict[str, Any]:
    output_root = (vault / SIGNING_OUTPUT_ROOT).resolve()
    evidence_root = (vault / DEFAULT_EVIDENCE_ROOT).resolve()
    paths: dict[str, Any] = {
        "output_root": {
            "path": SIGNING_OUTPUT_ROOT.as_posix(),
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
    preview = source_preview.get("signing_approval_packet_preview") or {}
    source_artifacts = source_preview.get("source_artifacts") or {}
    portable_zip = source_artifacts.get("portable_zip") or {}
    installer_manifest = source_artifacts.get("installer_manifest") or {}
    installer_marker = source_artifacts.get("exact_once_marker") or {}
    expected_packet_id = str(summary.get("approval_packet_id") or "")
    expected_digest = str(summary.get("request_digest_sha256") or "")
    expected_zip_sha = str(portable_zip.get("sha256") or "")
    expected_manifest_sha = str(installer_manifest.get("sha256") or "")
    expected_installer_marker_sha = str(installer_marker.get("sha256") or "")
    artifact_path_value = str((review.get("approval_artifact") or {}).get("path") or "")
    marker_path_value = str((review.get("exact_once_marker_contract") or {}).get("path") or "")

    payload = approval_payload or {}
    authority_flags_false = all(
        payload.get(key) is False
        for key in [
            "signing_allowed_in_this_pass",
            "approval_decision_consumed",
            "idempotency_marker_reserved",
            "signing_certificate_read",
            "raw_certificate_values_visible",
            "signs_artifacts",
            "writes_signed_artifact",
            "verifies_signature",
            "startup_mutation_allowed",
            "autostart_registration_allowed",
            "registry_write_allowed",
            "start_menu_write_allowed",
            "desktop_shortcut_write_allowed",
            "release_promotion_allowed",
            "release_status_write_allowed",
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
        and _path_under(vault, artifact_path_value, Path("07_LOGS") / "Agent-Activity" / "_studio_signing_approvals"),
        "approval_artifact_present": bool(approval_path and approval_path.is_file()),
        "approval_artifact_json_readable": approval_payload is not None,
        "approval_record_type_valid": payload.get("record_type") == APPROVAL_RECORD_TYPE,
        "approval_packet_id_matches": payload.get("approval_packet_id") == expected_packet_id,
        "request_digest_matches": payload.get("request_digest_sha256") == expected_digest,
        "operator_decision_approved": payload.get("operator_decision") == "approved",
        "approval_scope_one_signing_proof": payload.get("approval_scope") == "one_signing_proof_only",
        "approved_output_root_matches": payload.get("approved_output_root") == SIGNING_OUTPUT_ROOT.as_posix(),
        "unsigned_portable_zip_sha_matches": payload.get("approved_unsigned_portable_zip_sha256") == expected_zip_sha,
        "installer_manifest_sha_matches": payload.get("approved_installer_manifest_sha256") == expected_manifest_sha,
        "installer_execution_marker_sha_matches": payload.get("approved_installer_execution_marker_sha256")
        == expected_installer_marker_sha,
        "approval_consumption_required": payload.get("approval_consumption_required") is True,
        "approval_not_already_consumed": payload.get("approval_decision_consumed") is False,
        "approval_artifact_blocks_signing_in_review_pass": payload.get("signing_allowed_in_this_pass") is False
        and payload.get("signs_artifacts") is False
        and payload.get("writes_signed_artifact") is False,
        "approval_authority_flags_blocked": authority_flags_false,
        "marker_path_under_expected_root": bool(marker_path_value)
        and _path_under(vault, marker_path_value, SIGNING_MARKER_RELATIVE_DIR),
        "real_marker_absent": bool(marker_path and not marker_path.exists()),
        "source_packet_digest_present": bool(expected_packet_id and expected_digest),
        "source_unsigned_zip_hash_present": bool(expected_zip_sha),
        "source_manifest_hash_present": bool(expected_manifest_sha),
    }


def build_studio_signing_approval_consumption_dry_run(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Validate signing approval consumption readiness without executing consumption."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    existing_approval = _read_json(_approval_path_for_packet(vault, approval_packet_id)) if approval_packet_id else None
    installer_approval_packet_id = (
        str(existing_approval.get("approved_installer_approval_packet_id") or "")
        if existing_approval
        else None
    )
    try:
        review = build_studio_signing_approval_review(
            vault,
            approval_packet_id=approval_packet_id,
            installer_approval_packet_id=installer_approval_packet_id,
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
    rollback_audit_plan = {
        "rollback_root": SIGNING_OUTPUT_ROOT.as_posix(),
        "rollback_scope": "owned_signing_output_root_only",
        "future_execution_must_resolve_certificate_reference_without_raw_secret_output": True,
        "future_execution_must_write_manifest_before_release_promotion": True,
        "future_execution_must_write_audit_before_output": True,
        "future_execution_must_write_audit_after_output": True,
        "future_execution_must_verify_signed_artifact_hash": True,
        "release_promotion_blocked_until_separate_gate": True,
        "startup_registry_shortcut_blocked_until_separate_gates": True,
        "dry_run_pass_writes_rollback_artifacts": False,
        "dry_run_pass_deletes_outputs": False,
    }
    checks.update(
        {
            "future_output_paths_clear": output_paths_clear,
            "signing_execution_proof_complete": signing_execution_complete,
            "marker_reservation_proof_passed": bool(marker_proof.get("proof_passed")) or signing_execution_complete,
            "duplicate_marker_blocked": bool(marker_proof.get("duplicate_reservation_blocked")),
            "rollback_audit_plan_present": all(
                bool(rollback_audit_plan.get(key))
                for key in [
                    "future_execution_must_resolve_certificate_reference_without_raw_secret_output",
                    "future_execution_must_write_manifest_before_release_promotion",
                    "future_execution_must_write_audit_before_output",
                    "future_execution_must_write_audit_after_output",
                    "future_execution_must_verify_signed_artifact_hash",
                    "release_promotion_blocked_until_separate_gate",
                ]
            ),
            "no_real_marker_write_in_this_pass": marker_proof.get("real_marker_written") is False,
            "no_signing_output_write_in_this_pass": True,
            "certificate_not_read_in_this_pass": True,
        }
    )

    tolerated_when_completed = {
        "real_marker_absent",
        "future_output_paths_clear",
        "marker_reservation_proof_passed",
    }
    informational_checks = {"signing_execution_proof_complete"}
    blockers.extend(
        name
        for name, passed in checks.items()
        if not passed
        and name not in informational_checks
        and not (signing_execution_complete and name in tolerated_when_completed)
    )
    ok = not blockers
    status = ALREADY_CONSUMED_STATUS if ok and signing_execution_complete else READY_STATUS if ok else BLOCKED_STATUS
    authority = {
        **dict(BLOCKED_AUTHORITY),
        "approval_packet_preview_only": False,
        "approval_artifact_review_only": False,
        "approval_consumption_dry_run_only": True,
        "validates_approval_artifact": True,
        "simulates_marker_reservation": True,
        "simulates_duplicate_consumption_block": True,
        "signing_approval_preview_only": False,
        "creates_approval_artifact": False,
        "writes_approval_artifact": False,
        "consumes_approval_decision": False,
        "reserves_idempotency_marker": False,
        "writes_idempotency_marker": False,
        "signs_artifacts": False,
        "reads_signing_certificate": False,
        "writes_signed_artifact": False,
        "verifies_signature": False,
        "writes_packaging_output_root": False,
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
            "approval_scope_valid": checks.get("approval_scope_one_signing_proof"),
            "unsigned_portable_zip_hash_matches": checks.get("unsigned_portable_zip_sha_matches"),
            "installer_manifest_hash_matches": checks.get("installer_manifest_sha_matches"),
            "exact_once_marker_absent": checks.get("real_marker_absent"),
            "marker_reservation_proof_passed": checks.get("marker_reservation_proof_passed"),
            "duplicate_consumption_blocked": checks.get("duplicate_marker_blocked"),
            "future_output_paths_clear": output_paths_clear,
            "signing_execution_proof_complete": signing_execution_complete,
            "approval_consumed": signing_execution_complete,
            "exact_once_marker_reserved": signing_execution_complete,
            "signing_allowed": False,
            "signing_certificate_read": False,
            "signed_artifact_written": signing_execution_complete,
            "execution_allowed": False,
            "writes_performed": False,
            "next_recommended_pass": NEXT_STARTUP_AUTOSTART_APPROVAL_PASS
            if ok and signing_execution_complete
            else NEXT_SIGNING_APPROVED_EXECUTION_PROOF_PASS
            if ok
            else BLOCKED_PASS,
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
            "completed_by_execution_proof": signing_execution_complete,
            "future_write_mode": "atomic_create_new_only_before_any_signing_output_write",
            "duplicate_policy": "block_before_any_signing_output_write",
        },
        "marker_reservation_dry_run": marker_proof,
        "future_output_paths": future_paths,
        "output_path_constraints": output_constraints,
        "dry_run_plan": [
            {"step": "load_signing_approval_artifact", "effect_now": "read_only_validation", "required": True},
            {"step": "validate_packet_id_and_digest", "effect_now": "read_only_validation", "required": True},
            {"step": "validate_scope_and_blocked_authority", "effect_now": "read_only_validation", "required": True},
            {"step": "verify_unsigned_zip_and_manifest_hashes", "effect_now": "read_only_validation", "required": True},
            {"step": "verify_real_exact_once_marker_absent", "effect_now": "read_only_validation", "required": True},
            {"step": "simulate_exclusive_marker_reservation", "effect_now": "in_memory_no_write", "required": True},
            {"step": "simulate_duplicate_consumption_block", "effect_now": "in_memory_no_write", "required": True},
            {"step": "verify_future_signing_output_paths_clear", "effect_now": "read_only_validation", "required": True},
            {"step": "preview_certificate_and_rollback_audit_requirements", "effect_now": "read_only_plan", "required": True},
            {"step": "stop_before_real_marker_certificate_or_signing_output", "effect_now": "execution_block", "required": True},
        ],
        "rollback_audit_plan": rollback_audit_plan,
        "checks": checks,
        "authority": authority,
        "blocked_authority": [key for key, value in authority.items() if value is False],
        "blockers": blockers,
        "unverified": [
            "No approval decision was consumed in this dry-run pass.",
            "No real exact-once marker was reserved or written in this dry-run pass.",
            "No signing certificate or raw credential value was read in this dry-run pass.",
            "No signed artifact, signing manifest, signing dry-run evidence, or signing execution evidence was written in this dry-run pass.",
            "No startup/autostart, registry, Start Menu, desktop shortcut, release promotion, provider/connector call, Agent Bus write, Gate mutation, workflow execution, Git operation, or canonical writeback was attempted.",
        ],
        "writes_performed": False,
        "next_recommended_pass": NEXT_STARTUP_AUTOSTART_APPROVAL_PASS
        if ok and signing_execution_complete
        else NEXT_SIGNING_APPROVED_EXECUTION_PROOF_PASS
        if ok
        else BLOCKED_PASS,
    }


def write_signing_approval_consumption_dry_run_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-signing-approval-consumption-dry-run"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    artifact = report.get("approval_artifact") or {}
    marker = report.get("exact_once_marker_contract") or {}
    marker_proof = report.get("marker_reservation_dry_run") or {}
    lines = [
        "# Studio Signing Approval Consumption Dry-Run Evidence",
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
        f"- unsigned_portable_zip_hash_matches: {summary.get('unsigned_portable_zip_hash_matches')}",
        f"- installer_manifest_hash_matches: {summary.get('installer_manifest_hash_matches')}",
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
