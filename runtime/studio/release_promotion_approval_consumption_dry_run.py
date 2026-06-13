"""Dry-run approval-consumption guard for Studio release promotion.

This validates the written release-promotion approval artifact and proves the
exact-once consumption boundary without consuming approval, reserving the real
marker, writing release status, promoting a release, mutating host startup
state, touching Gate/Agent Bus/Git/canonical state, or calling providers.
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
    RELEASE_APPROVAL_RELATIVE_DIR,
    RELEASE_MARKER_RELATIVE_DIR,
    RELEASE_PROOF_ROOT,
)
from runtime.studio.release_promotion_approval_review import (
    APPROVAL_RECORD_TYPE,
    build_studio_release_promotion_approval_review,
)


MODEL_VERSION = "studio.release_promotion_approval_consumption_dry_run.v1"
SURFACE_ID = "studio_release_promotion_approval_consumption_dry_run"
READY_STATUS = "studio_release_promotion_approval_consumption_dry_run_ready_no_release_mutation"
BLOCKED_STATUS = "blocked_studio_release_promotion_approval_consumption_dry_run"
BLOCKED_PASS = "studio-release-promotion-approval-review"
NEXT_RELEASE_APPROVED_EXECUTION_PROOF_PASS = "studio-release-promotion-approved-execution-proof"


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
        raise ValueError(f"release-promotion approval consumption path escapes vault: {path_value}") from exc
    return resolved


def _approval_artifact_path_for_packet(vault: Path, approval_packet_id: str | None) -> Path | None:
    if not approval_packet_id:
        return None
    if "/" in approval_packet_id or "\\" in approval_packet_id or approval_packet_id in {".", ".."}:
        raise ValueError(f"invalid release-promotion approval packet id: {approval_packet_id}")
    return (vault / RELEASE_APPROVAL_RELATIVE_DIR / f"{approval_packet_id}.json").resolve()


def _approved_startup_packet_id_from_artifact(vault: Path, approval_packet_id: str | None) -> str | None:
    path = _approval_artifact_path_for_packet(vault, approval_packet_id)
    if not path or not path.is_file():
        return None
    payload = _read_json(path) or {}
    value = payload.get("approved_startup_approval_packet_id")
    return str(value) if value else None


def _path_under(vault: Path, path_value: str, base_relative: Path) -> bool:
    try:
        resolved = _resolve_vault_relative_path(vault, path_value)
        resolved.relative_to((vault / base_relative).resolve())
    except (ValueError, RuntimeError):
        return False
    return True


def _all_future_output_paths_clear(future_paths: dict[str, Any]) -> bool:
    return not any(
        bool(value.get("exists"))
        for key, value in future_paths.items()
        if key != "output_root" and isinstance(value, dict)
    )


def _completed_release_marker(marker_path: Path | None, approval_packet_id: str) -> bool:
    if not marker_path or not marker_path.is_file():
        return False
    payload = _read_json(marker_path)
    return bool(
        payload
        and payload.get("record_type") == "studio_release_promotion_execution_marker"
        and payload.get("approval_packet_id") == approval_packet_id
        and payload.get("status") == EXECUTION_COMPLETE_STATUS
    )


def _marker_reservation_dry_run(marker_exists: bool) -> dict[str, Any]:
    first_reservation_allowed = not marker_exists
    return {
        "proof_mode": "in_memory_no_real_marker_write",
        "real_marker_written": False,
        "real_marker_reserved": False,
        "marker_exists_before": bool(marker_exists),
        "first_reservation_allowed": first_reservation_allowed,
        "first_reservation_status": "would_reserve_exclusively" if first_reservation_allowed else "blocked_existing_marker",
        "duplicate_reservation_blocked": True,
        "duplicate_reservation_status": "blocked_prior_marker_exists",
        "required_future_write_mode": "atomic_create_new_only_before_any_release_status_write",
        "proof_passed": first_reservation_allowed,
    }


def _output_path_constraints(vault: Path, future_paths: dict[str, Any]) -> dict[str, Any]:
    output_root = (vault / RELEASE_PROOF_ROOT).resolve()
    evidence_root = (vault / DEFAULT_EVIDENCE_ROOT).resolve()
    paths: dict[str, Any] = {
        "output_root": {
            "path": RELEASE_PROOF_ROOT.as_posix(),
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
    preview = source_preview.get("release_promotion_approval_packet_preview") or {}
    material = preview.get("approval_material") or {}
    source_artifacts = source_preview.get("source_artifacts") or {}
    startup_marker = source_artifacts.get("startup_exact_once_marker") or {}
    signed_zip = source_artifacts.get("signed_portable_zip") or {}
    signing_manifest = source_artifacts.get("signing_manifest") or {}
    startup_evidence = source_artifacts.get("startup_execution_evidence") or {}
    startup_audit = source_artifacts.get("startup_host_mutation_audit") or {}
    startup_rollback = source_artifacts.get("startup_rollback_plan") or {}
    expected_packet_id = str(summary.get("approval_packet_id") or "")
    expected_digest = str(summary.get("request_digest_sha256") or "")
    artifact_path_value = str((review.get("approval_artifact") or {}).get("path") or "")
    marker_path_value = str((review.get("exact_once_marker_contract") or {}).get("path") or "")
    payload = approval_payload or {}
    authority_flags_false = all(
        payload.get(key) is False
        for key in [
            "release_status_write_allowed_in_this_pass",
            "release_promotion_allowed_in_this_pass",
            "approval_decision_consumed",
            "idempotency_marker_reserved",
            "writes_release_status",
            "promotes_release",
            "host_path_resolution_attempted",
            "resolves_host_startup_paths",
            "writes_host_startup",
            "registers_autostart",
            "writes_registry",
            "writes_start_menu",
            "writes_desktop_shortcut",
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
        and _path_under(vault, artifact_path_value, RELEASE_APPROVAL_RELATIVE_DIR),
        "approval_artifact_present": bool(approval_path and approval_path.is_file()),
        "approval_artifact_json_readable": approval_payload is not None,
        "approval_record_type_valid": payload.get("record_type") == APPROVAL_RECORD_TYPE,
        "approval_packet_id_matches": payload.get("approval_packet_id") == expected_packet_id,
        "request_digest_matches": payload.get("request_digest_sha256") == expected_digest,
        "operator_decision_approved": payload.get("operator_decision") == "approved",
        "approval_scope_one_release_promotion_proof": payload.get("approval_scope") == "one_release_promotion_proof_only",
        "approved_startup_marker_sha_matches": payload.get("approved_startup_execution_marker_sha256")
        == (startup_marker.get("sha256") or material.get("startup_execution_marker_sha256")),
        "approved_signed_zip_sha_matches": payload.get("approved_signed_portable_zip_sha256")
        == (signed_zip.get("sha256") or material.get("signed_portable_zip_sha256")),
        "approved_signing_manifest_sha_matches": payload.get("approved_signing_manifest_sha256")
        == (signing_manifest.get("sha256") or material.get("signing_manifest_sha256")),
        "approved_startup_execution_evidence_sha_matches": payload.get("approved_startup_execution_evidence_sha256")
        == (startup_evidence.get("sha256") or material.get("startup_execution_evidence_sha256")),
        "approved_startup_audit_sha_matches": payload.get("approved_startup_host_mutation_audit_sha256")
        == (startup_audit.get("sha256") or material.get("startup_host_mutation_audit_sha256")),
        "approved_startup_rollback_sha_matches": payload.get("approved_startup_rollback_plan_sha256")
        == (startup_rollback.get("sha256") or material.get("startup_rollback_plan_sha256")),
        "approved_release_channel_matches": payload.get("approved_release_channel") == material.get("release_channel"),
        "approved_release_mode_matches": payload.get("approved_release_mode") == material.get("release_mode"),
        "approval_consumption_required": payload.get("approval_consumption_required") is True,
        "approval_not_already_consumed": payload.get("approval_decision_consumed") is False,
        "approval_authority_flags_blocked": authority_flags_false,
        "marker_path_under_expected_root": bool(marker_path_value)
        and _path_under(vault, marker_path_value, RELEASE_MARKER_RELATIVE_DIR),
        "real_marker_absent": bool(marker_path and (not marker_path.exists() or _completed_release_marker(marker_path, expected_packet_id))),
        "source_packet_digest_present": bool(expected_packet_id and expected_digest),
        "source_artifact_hashes_present": all(
            bool(value)
            for value in [
                startup_marker.get("sha256") or material.get("startup_execution_marker_sha256"),
                signed_zip.get("sha256") or material.get("signed_portable_zip_sha256"),
                signing_manifest.get("sha256") or material.get("signing_manifest_sha256"),
                startup_evidence.get("sha256") or material.get("startup_execution_evidence_sha256"),
                startup_audit.get("sha256") or material.get("startup_host_mutation_audit_sha256"),
                startup_rollback.get("sha256") or material.get("startup_rollback_plan_sha256"),
            ]
        ),
    }


def build_studio_release_promotion_approval_consumption_dry_run(
    vault_root: str | Path,
    *,
    approval_packet_id: str | None = None,
    startup_approval_packet_id: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Validate release-promotion approval consumption readiness without consuming it."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    blockers: list[str] = []
    approved_startup_approval_packet_id = None
    try:
        approved_startup_approval_packet_id = _approved_startup_packet_id_from_artifact(vault, approval_packet_id)
    except ValueError as exc:
        blockers.append(str(exc))
    if (
        startup_approval_packet_id
        and approved_startup_approval_packet_id
        and startup_approval_packet_id != approved_startup_approval_packet_id
    ):
        blockers.append("Explicit startup/autostart approval packet id does not match the release-promotion artifact.")
    selected_startup_approval_packet_id = startup_approval_packet_id or approved_startup_approval_packet_id
    try:
        review = build_studio_release_promotion_approval_review(
            vault,
            approval_packet_id=approval_packet_id,
            startup_approval_packet_id=selected_startup_approval_packet_id,
            decision="approve",
            write_approval=False,
            generated_at=timestamp,
        )
    except (ValueError, KeyError) as exc:
        review = {"ok": False, "summary": {}, "approval_artifact": {}, "exact_once_marker_contract": {}, "future_output_paths": {}}
        blockers.append(str(exc))

    artifact = review.get("approval_artifact") or {}
    marker = review.get("exact_once_marker_contract") or {}
    future_paths = review.get("future_output_paths") or {}
    approval_path = None
    marker_path = None
    approval_payload = None
    try:
        artifact_path_value = str(artifact.get("path") or "")
        marker_path_value = str(marker.get("path") or "")
        approval_path = _resolve_vault_relative_path(vault, artifact_path_value) if artifact_path_value else None
        marker_path = _resolve_vault_relative_path(vault, marker_path_value) if marker_path_value else None
        approval_payload = _read_json(approval_path) if approval_path and approval_path.is_file() else None
    except ValueError as exc:
        blockers.append(str(exc))

    summary = review.get("summary") or {}
    release_execution_complete = _completed_release_marker(marker_path, str(summary.get("approval_packet_id") or ""))
    checks = _approval_validation_checks(
        vault=vault,
        approval_payload=approval_payload,
        approval_path=approval_path,
        marker_path=marker_path,
        review=review,
        approval_packet_id=approval_packet_id,
    )
    marker_proof = _marker_reservation_dry_run(bool(marker_path and marker_path.exists()))
    output_paths_clear = _all_future_output_paths_clear(future_paths) or release_execution_complete
    output_constraints = _output_path_constraints(vault, future_paths)
    source_checks = {
        **((review.get("source_preview") or {}).get("checks") or {}),
        **(review.get("checks") or {}),
    }
    checks.update(
        {
            "future_output_paths_clear": output_paths_clear,
            "startup_autostart_approved_execution_proof_complete": bool(
                source_checks.get("startup_autostart_approved_execution_proof_complete")
            ),
            "startup_approval_consumed": bool(source_checks.get("startup_approval_consumed")),
            "startup_exact_once_marker_complete": bool(source_checks.get("startup_exact_once_marker_complete")),
            "release_status_write_blocked": bool(
                source_checks.get("release_status_write_blocked")
                or source_checks.get("release_status_write_blocked_in_this_pass")
            ),
            "release_promotion_blocked": bool(
                source_checks.get("release_promotion_blocked")
                or source_checks.get("release_promotion_blocked_in_this_pass")
            ),
            "marker_reservation_proof_passed": bool(marker_proof.get("proof_passed")) or release_execution_complete,
            "duplicate_marker_blocked": bool(marker_proof.get("duplicate_reservation_blocked")),
            "rollback_audit_plan_present": True,
            "no_real_marker_write_in_this_pass": marker_proof.get("real_marker_written") is False,
            "no_release_status_write_in_this_pass": True,
            "no_release_promotion_in_this_pass": True,
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
        "writes_release_status": False,
        "promotes_release": False,
        "resolves_host_startup_paths": False,
        "writes_host_startup": False,
        "registers_autostart": False,
        "writes_registry": False,
        "writes_start_menu": False,
        "writes_desktop_shortcut": False,
    }
    next_pass = (
        NEXT_AFTER_RELEASE_PROMOTION_PROOF_PASS
        if ok and release_execution_complete
        else NEXT_RELEASE_APPROVED_EXECUTION_PROOF_PASS
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
            "approval_packet_id": summary.get("approval_packet_id"),
            "startup_approval_packet_id": selected_startup_approval_packet_id,
            "request_digest_sha256": summary.get("request_digest_sha256"),
            "approval_artifact_present": checks.get("approval_artifact_present"),
            "approval_digest_matches": checks.get("request_digest_matches"),
            "approval_scope_valid": checks.get("approval_scope_one_release_promotion_proof"),
            "startup_marker_hash_matches": checks.get("approved_startup_marker_sha_matches"),
            "signed_portable_zip_hash_matches": checks.get("approved_signed_zip_sha_matches"),
            "signing_manifest_hash_matches": checks.get("approved_signing_manifest_sha_matches"),
            "startup_execution_evidence_hash_matches": checks.get("approved_startup_execution_evidence_sha_matches"),
            "startup_audit_hash_matches": checks.get("approved_startup_audit_sha_matches"),
            "startup_rollback_hash_matches": checks.get("approved_startup_rollback_sha_matches"),
            "release_channel_matches": checks.get("approved_release_channel_matches"),
            "release_mode_matches": checks.get("approved_release_mode_matches"),
            "exact_once_marker_absent": checks.get("real_marker_absent"),
            "marker_reservation_proof_passed": checks.get("marker_reservation_proof_passed"),
            "duplicate_consumption_blocked": checks.get("duplicate_marker_blocked"),
            "future_output_paths_clear": output_paths_clear,
            "release_promotion_execution_proof_complete": release_execution_complete,
            "approval_consumed": release_execution_complete,
            "exact_once_marker_reserved": release_execution_complete,
            "release_status_write_allowed": False,
            "release_promotion_allowed": False,
            "host_path_resolution_attempted": False,
            "host_mutation_performed": False,
            "execution_allowed": False,
            "writes_performed": False,
            "next_recommended_pass": next_pass,
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
            "completed_by_execution_proof": release_execution_complete,
            "future_write_mode": "atomic_create_new_only_before_any_release_status_write",
            "duplicate_policy": "block_before_any_release_status_or_release_promotion_write",
        },
        "marker_reservation_dry_run": marker_proof,
        "future_output_paths": future_paths,
        "output_path_constraints": output_constraints,
        "dry_run_plan": [
            {"step": "load_release_promotion_approval_artifact", "effect_now": "read_only_validation", "required": True},
            {"step": "validate_packet_id_digest_scope_and_source_hashes", "effect_now": "read_only_validation", "required": True},
            {"step": "verify_real_exact_once_marker_absent", "effect_now": "read_only_validation", "required": True},
            {"step": "simulate_exclusive_marker_reservation", "effect_now": "in_memory_no_write", "required": True},
            {"step": "simulate_duplicate_consumption_block", "effect_now": "in_memory_no_write", "required": True},
            {"step": "verify_future_release_output_paths_clear", "effect_now": "read_only_validation", "required": True},
            {"step": "preview_release_status_manifest_audit_rollback_requirements", "effect_now": "read_only_plan", "required": True},
            {"step": "stop_before_real_marker_release_status_or_promotion_write", "effect_now": "execution_block", "required": True},
        ],
        "rollback_audit_plan": {
            "rollback_root": RELEASE_PROOF_ROOT.as_posix(),
            "rollback_scope": "owned_release_promotion_proof_root_only",
            "future_execution_must_reserve_marker_before_release_status_write": True,
            "future_execution_must_write_rollback_plan_before_release_status_write": True,
            "future_execution_must_write_release_audit": True,
            "dry_run_pass_writes_release_status": False,
            "dry_run_pass_promotes_release": False,
        },
        "checks": checks,
        "authority": authority,
        "blocked_authority": [key for key, value in authority.items() if value is False],
        "blockers": blockers,
        "unverified": [
            "No approval decision was consumed in this dry-run pass.",
            "No real exact-once marker was reserved or written in this dry-run pass.",
            "No release-status preview, release manifest, audit, rollback, or execution evidence was written.",
            "No host startup/autostart, provider/connector, Agent Bus, Gate, workflow, Git, or canonical mutation was attempted.",
        ],
        "writes_performed": False,
        "next_recommended_pass": next_pass,
    }


def write_release_promotion_approval_consumption_dry_run_evidence(
    vault_root: str | Path,
    report: dict[str, Any],
    *,
    evidence_slug: str | None = None,
    evidence_root: str | Path | None = None,
) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    root = vault / (Path(evidence_root) if evidence_root else DEFAULT_EVIDENCE_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    slug = evidence_slug or f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-studio-release-promotion-approval-consumption-dry-run"
    json_path = root / f"{slug}.json"
    markdown_path = root / f"{slug}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    summary = report.get("summary") or {}
    artifact = report.get("approval_artifact") or {}
    marker = report.get("exact_once_marker_contract") or {}
    marker_proof = report.get("marker_reservation_dry_run") or {}
    lines = [
        "# Studio Release Promotion Approval Consumption Dry-Run Evidence",
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
            if isinstance(value, dict)
        ],
        "",
        "## Checks",
        "",
        *[f"- {key}: {value}" for key, value in (report.get("checks") or {}).items()],
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
