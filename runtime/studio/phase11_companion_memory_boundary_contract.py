"""Phase 11 companion memory boundary contract.

This Studio surface turns the operator decision into repo-visible truth:
companions have separate governed memory namespaces, but no memory write,
approval queue write, approval consumption, provider call, runtime dispatch, or
canonical mutation is mounted by this pass.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.companion.memory import (
    COMPANION_MEMORY_ROOT,
    MEMORY_POLICY_VERSION,
    build_companion_memory_boundary,
)
from runtime.studio.phase11_companion_roster_ui_preview import build_phase11_companion_roster_ui_preview
from runtime.studio.phase11_operator_companion_direction_answers import (
    build_phase11_operator_companion_direction_answers,
)


MODEL_VERSION = "studio.phase11_companion_memory_boundary_contract.v1"
SURFACE_ID = "phase11_companion_memory_boundary_contract"
PASS_ID = "phase11-companion-memory-boundary-contract"
STATUS = "COMPLETE / READ-ONLY / SEPARATE MEMORY BOUNDARY DEFINED / MEMORY WRITES BLOCKED"
NEXT_RECOMMENDED_PASS = "phase11-companion-memory-approval-preview"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _memory_snapshot(vault: Path) -> list[str]:
    root = vault / COMPANION_MEMORY_ROOT
    if not root.exists():
        return []
    return sorted(_rel(vault, path) for path in root.rglob("*") if path.is_file())


def build_phase11_companion_memory_boundary_contract(vault_root: str | Path) -> dict[str, Any]:
    """Build the Studio contract for separate governed companion memory."""

    vault = Path(vault_root).resolve()
    before_memory_files = _memory_snapshot(vault)
    boundary = build_companion_memory_boundary(vault)
    direction = build_phase11_operator_companion_direction_answers(vault)
    roster = build_phase11_companion_roster_ui_preview(vault)
    after_memory_files = _memory_snapshot(vault)

    authority = boundary.get("authority") or {}
    blockers: list[str] = []
    if boundary.get("ok") is not True:
        blockers.append("companion_memory_boundary_core_not_ready")
    if direction.get("ok") is not True:
        blockers.append("operator_companion_direction_policy_not_ready")
    if roster.get("ok") is not True:
        blockers.append("companion_roster_ui_preview_not_ready")
    if before_memory_files != after_memory_files:
        blockers.append("companion_memory_snapshot_changed")
    if boundary.get("memory_writes_allowed_now") is not False:
        blockers.append("memory_write_authority_unexpectedly_enabled")
    if authority.get("canonical_mutation_allowed") is not False:
        blockers.append("canonical_mutation_unexpectedly_enabled")

    ok = not blockers
    namespaces = boundary.get("companion_namespaces") or {}
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "memory_policy_version": MEMORY_POLICY_VERSION,
        "boundary_digest": ((boundary.get("digest_proof") or {}).get("boundary_digest")),
        "namespace_paths": namespaces,
        "memory_files_before": before_memory_files,
        "memory_files_after": after_memory_files,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if ok else "BLOCKED / COMPANION MEMORY BOUNDARY NOT READY",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": {
            "separate_companion_memory_enabled_by_operator": boundary.get("separate_memory_enabled_by_operator") is True,
            "separate_memory_namespace_declared": boundary.get("separate_memory_namespace_declared") is True,
            "memory_namespace_count": len(namespaces),
            "memory_root": boundary.get("memory_root"),
            "memory_writes_allowed_now": False,
            "memory_write_executor_built": False,
            "approval_required_for_memory_write": True,
            "approval_queue_write_performed": False,
            "approval_consumed_by_this_surface": False,
            "memory_files_written_by_this_surface": False,
            "memory_snapshot_unchanged": before_memory_files == after_memory_files,
            "allowed_memory_class_count": len(boundary.get("allowed_memory_classes") or []),
            "denied_memory_class_count": len(boundary.get("denied_memory_classes") or []),
            "sample_allowed_candidate_valid": (
                boundary.get("sample_allowed_candidate_validation") or {}
            ).get("candidate_valid")
            is True,
            "sample_allowed_candidate_write_allowed": (
                boundary.get("sample_allowed_candidate_validation") or {}
            ).get("write_allowed_now")
            is True,
            "sample_denied_candidates_blocked": all(
                (item or {}).get("candidate_valid") is False
                for item in (boundary.get("sample_denied_candidate_validations") or [])
            ),
            "provider_call_performed": False,
            "runtime_dispatched": False,
            "agent_bus_task_written": False,
            "canonical_state_mutated": False,
            "blocker_count": len(blockers),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS if ok else PASS_ID,
        },
        "boundary": boundary,
        "direction_policy": {
            "ok": direction.get("ok") is True,
            "policy_path": direction.get("policy_vault_relative_path"),
            "separate_companion_memory_allowed": (direction.get("summary") or {}).get(
                "separate_companion_memory_allowed"
            )
            is True,
        },
        "roster_posture": {
            "ok": roster.get("ok") is True,
            "roster_card_count": (roster.get("summary") or {}).get("roster_card_count"),
            "memory_access_granted": (roster.get("authority") or {}).get("memory_access_granted"),
        },
        "memory_snapshot_proof": {
            "root_path": COMPANION_MEMORY_ROOT.as_posix(),
            "files_before": before_memory_files,
            "files_after": after_memory_files,
            "unchanged": before_memory_files == after_memory_files,
            "memory_root_created_by_this_surface": False,
        },
        "future_approval_contract": {
            "next_pass": NEXT_RECOMMENDED_PASS,
            "approval_required_before_memory_write": True,
            "exact_once_marker_required": True,
            "candidate_validation_required": True,
            "memory_write_executor_required": True,
            "approval_request_created_by_this_surface": False,
            "memory_write_executed_by_this_surface": False,
        },
        "authority": {
            "read_only": True,
            "separate_memory_namespace_declared": True,
            "memory_write_authority_granted": False,
            "memory_read_authority_granted_to_companion": False,
            "approval_queue_write_allowed": False,
            "approval_consumption_allowed": False,
            "approval_execution_allowed": False,
            "provider_calls_allowed": False,
            "runtime_dispatch_allowed": False,
            "agent_bus_task_write_allowed": False,
            "tool_access_allowed": False,
            "protected_file_access_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "readiness": {
            "companion_memory_boundary_contract_ready": ok,
            "separate_companion_memory_operator_decision_applied": True,
            "companion_memory_namespaces_previewed": len(namespaces) == 3,
            "companion_memory_writes_blocked": True,
            "companion_memory_write_executor_required": True,
            "companion_memory_approval_required": True,
            "companion_memory_candidate_validation_ready": True,
            "companion_memory_provider_calls_blocked": True,
            "companion_memory_runtime_dispatch_blocked": True,
            "companion_memory_agent_bus_write_blocked": True,
            "companion_memory_canonical_mutation_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS if ok else PASS_ID,
        },
        "digest_proof": {
            "memory_boundary_contract_digest": _sha256_text(_canonical_json(digest_material)),
            "digest_material": digest_material,
        },
        "blocked_reasons": blockers,
    }


def format_phase11_companion_memory_boundary_contract(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "Phase 11 Companion Memory Boundary Contract",
        f"Status: {payload.get('status')}",
        f"Separate memory namespace: {summary.get('separate_memory_namespace_declared')}",
        f"Namespaces: {summary.get('memory_namespace_count')}",
        f"Memory writes allowed now: {summary.get('memory_writes_allowed_now')}",
        f"Approval required: {summary.get('approval_required_for_memory_write')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
        "Boundary: separate governed memory is declared, but memory writes, approval queue writes, approval consumption, provider calls, runtime dispatch, Agent Bus writes, and canonical mutation remain blocked.",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
