"""Phase 11 companion memory real-ledger activation closeout.

This surface verifies the end-to-end companion-memory ledger activation after
an approved ledger-write execution. It does not append memory, consume
approvals, dispatch runtimes, call providers, or promote canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_companion_memory_approved_ledger_write_execution_proof import (
    EVIDENCE_ROOT,
)
from runtime.studio.phase11_companion_memory_ledger_read_model_preview import (
    LEDGER_FILENAME,
    build_phase11_companion_memory_ledger_read_model_preview,
)
from runtime.studio.phase11_companion_memory_ledger_write_approval_preview import (
    LEDGER_MARKER_DIR,
    MEMORY_ROOT,
)
from runtime.studio.service import StudioService


MODEL_VERSION = "studio.phase11_companion_memory_real_ledger_activation_closeout.v1"
SURFACE_ID = "phase11_companion_memory_real_ledger_activation_closeout"
PASS_ID = "phase11-companion-memory-real-ledger-activation-closeout"
STATUS = "COMPLETE / APPROVAL-CONSUMED / REAL LEDGER ACTIVE / VERIFIED"
BLOCKED_STATUS = "BLOCKED / REAL LEDGER ACTIVATION / INCOMPLETE"
NEXT_RECOMMENDED_PASS = "phase11-companion-memory-context-readiness-preview"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c == "-" else "_" for c in str(value or "")) or "unknown"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _memory_snapshot(vault: Path) -> list[str]:
    root = vault / MEMORY_ROOT
    if not root.exists():
        return []
    return sorted(_rel(vault, path) for path in root.rglob("*") if path.is_file())


def _safe_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"json_read_failed:{_rel(path.parent, path)}:{exc}"
    except json.JSONDecodeError as exc:
        return None, f"json_malformed:{path.name}:{exc}"
    if not isinstance(payload, dict):
        return None, f"json_not_object:{path.name}"
    return payload, None


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _evidence_paths(vault: Path, approval_id: str) -> dict[str, Path]:
    safe = _safe_id(approval_id)
    root = vault / EVIDENCE_ROOT
    return {
        "execution_evidence": root / f"{safe}-execution-evidence.json",
        "rollback_plan": root / f"{safe}-rollback-plan.json",
        "ledger_entry_copy": root / f"{safe}-ledger-entry.json",
    }


def _path_record(vault: Path, path: Path) -> dict[str, Any]:
    return {
        "path": _rel(vault, path),
        "exists": path.is_file(),
        "sha256": _file_sha256(path) if path.is_file() else None,
        "size_bytes": path.stat().st_size if path.is_file() else 0,
    }


def _read_jsonl_entries(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.is_file():
        return [], []
    entries: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"ledger_read_failed:{exc}"]
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"ledger_line_malformed:{line_number}:{exc}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"ledger_line_not_object:{line_number}")
            continue
        entries.append(payload)
    return entries, errors


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "real_companion_memory_read_allowed": True,
        "activation_closeout_allowed": True,
        "approval_artifact_read_allowed": True,
        "exact_once_marker_read_allowed": True,
        "execution_evidence_read_allowed": True,
        "memory_ledger_read_allowed": True,
        "approval_queue_write_allowed": False,
        "approval_consumption_allowed": False,
        "approval_execution_allowed": False,
        "memory_ledger_write_allowed": False,
        "memory_root_create_allowed": False,
        "provider_calls_allowed": False,
        "runtime_dispatch_allowed": False,
        "browser_control_allowed": False,
        "agent_bus_task_write_allowed": False,
        "gate_mutation_allowed": False,
        "git_mutation_allowed": False,
        "workflow_execution_allowed": False,
        "host_mutation_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _select_record(
    records: list[dict[str, Any]],
    *,
    approval_id: str,
) -> dict[str, Any] | None:
    if approval_id:
        for item in records:
            if str(item.get("ledger_write_approval_id") or "") == approval_id:
                return item
        return None
    return records[0] if records else None


def _approval_summary(vault: Path, approval_id: str) -> dict[str, Any]:
    service = StudioService(vault)
    req = service.get_approval(approval_id) if approval_id else None
    metadata = dict(req.action_spec.metadata or {}) if req else {}
    path = vault / StudioService.APPROVAL_DIR / f"{_safe_id(approval_id)}.json"
    return {
        "approval_id": approval_id or None,
        "approval_path": _rel(vault, path),
        "approval_exists": req is not None and path.is_file(),
        "status": req.status if req else None,
        "execution_status": req.execution_status if req else None,
        "result_action_id": req.result_action_id if req else None,
        "ledger_write_approval_digest": metadata.get("phase11_companion_memory_ledger_write_approval_digest"),
        "approved_ledger_write_execution_proof": metadata.get(
            "phase11_companion_memory_approved_ledger_write_execution_proof"
        )
        is True,
        "approval_consumed": metadata.get("approval_consumed") is True,
        "marker_reserved_before_ledger_append": metadata.get("marker_reserved_before_ledger_append") is True,
        "companion_memory_ledger_write_performed": metadata.get("companion_memory_ledger_write_performed") is True,
    }


def build_phase11_companion_memory_real_ledger_activation_closeout(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    companion_id: str | None = None,
    memory_class: str | None = None,
    query: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Verify that a governed companion-memory ledger write is active."""

    vault = Path(vault_root).resolve()
    before_memory = _memory_snapshot(vault)
    requested_approval_id = str(approval_id or "").strip()
    effective_query = requested_approval_id or query
    read_model = build_phase11_companion_memory_ledger_read_model_preview(
        vault,
        companion_id=companion_id,
        memory_class=memory_class,
        query=effective_query,
        limit=max(1, min(int(limit or 50), 500)),
        include_proof_backfill=False,
    )
    ledger_records = [
        item for item in read_model.get("results", []) if item.get("source_type") == "ledger_entry"
    ]
    selected = _select_record(ledger_records, approval_id=requested_approval_id)
    selected_approval_id = requested_approval_id or str((selected or {}).get("ledger_write_approval_id") or "")
    marker_path = vault / LEDGER_MARKER_DIR / f"{_safe_id(selected_approval_id)}.json"
    evidence_paths = _evidence_paths(vault, selected_approval_id)
    marker_payload, marker_error = _safe_json(marker_path) if marker_path.is_file() else ({}, None)
    evidence_payloads: dict[str, dict[str, Any]] = {}
    evidence_errors: list[str] = []
    for key, path in evidence_paths.items():
        if not path.is_file():
            continue
        payload, error = _safe_json(path)
        if error:
            evidence_errors.append(error)
        elif payload is not None:
            evidence_payloads[key] = payload

    approval = _approval_summary(vault, selected_approval_id)
    ledger_path = vault / str((selected or {}).get("ledger_path") or "")
    ledger_entries, ledger_errors = _read_jsonl_entries(ledger_path) if selected else ([], [])
    ledger_write_digest = str((selected or {}).get("ledger_write_approval_digest") or "")
    execution_id = str((selected or {}).get("ledger_write_execution_id") or "")
    execution_evidence = evidence_payloads.get("execution_evidence") or {}
    rollback_plan = evidence_payloads.get("rollback_plan") or {}
    ledger_entry_copy = evidence_payloads.get("ledger_entry_copy") or {}

    blockers: list[str] = []
    if not selected:
        blockers.append("real_ledger_record_not_found")
    if selected_approval_id and not approval.get("approval_exists"):
        blockers.append("approval_artifact_not_found")
    if approval.get("approval_exists") and approval.get("status") != "executed":
        blockers.append("approval_not_executed")
    if approval.get("approval_exists") and approval.get("execution_status") != "completed":
        blockers.append("approval_execution_not_completed")
    if not marker_path.is_file():
        blockers.append("exact_once_marker_not_found")
    if marker_path.is_file() and (marker_payload or {}).get("status") != "executed":
        blockers.append("exact_once_marker_not_executed")
    if marker_path.is_file() and (marker_payload or {}).get("marker_reserved_before_ledger_append") is not True:
        blockers.append("marker_not_reserved_before_ledger_append")
    if marker_path.is_file() and (marker_payload or {}).get("ledger_entry_written") is not True:
        blockers.append("marker_does_not_confirm_ledger_entry_written")
    for key, path in evidence_paths.items():
        if not path.is_file():
            blockers.append(f"{key}_missing")
    blockers.extend(evidence_errors)
    blockers.extend(ledger_errors)
    if selected:
        if selected.get("proof_status") != "ledger_written":
            blockers.append("read_model_record_not_ledger_written")
        if selected.get("ledger_write_performed") is not True:
            blockers.append("ledger_record_not_marked_written")
        if selected.get("trust_state") != "raw":
            blockers.append("ledger_record_trust_state_not_raw")
        if selected.get("canonical") is not False or selected.get("authoritative") is not False:
            blockers.append("ledger_record_canonical_or_authoritative")
        for key in (
            "provider_call_performed",
            "runtime_dispatch_performed",
            "browser_control_performed",
            "agent_bus_task_written",
            "canonical_mutation_performed",
        ):
            if selected.get(key):
                blockers.append(f"ledger_record_forbidden_{key}")
        if ledger_write_digest and approval.get("ledger_write_approval_digest") not in {ledger_write_digest, None}:
            blockers.append("approval_digest_mismatch")
        if marker_payload and marker_payload.get("ledger_write_approval_digest") != ledger_write_digest:
            blockers.append("marker_digest_mismatch")
        if execution_evidence and execution_evidence.get("ledger_write_approval_digest") != ledger_write_digest:
            blockers.append("execution_evidence_digest_mismatch")
        if execution_id and approval.get("result_action_id") not in {execution_id, None}:
            blockers.append("approval_execution_id_mismatch")
        if execution_evidence and execution_evidence.get("execution_id") != execution_id:
            blockers.append("execution_evidence_execution_id_mismatch")
        if rollback_plan and rollback_plan.get("execution_id") != execution_id:
            blockers.append("rollback_plan_execution_id_mismatch")
        if ledger_entry_copy and ledger_entry_copy.get("ledger_write_approval_id") != selected_approval_id:
            blockers.append("ledger_entry_copy_approval_id_mismatch")

    after_memory = _memory_snapshot(vault)
    evidence_present = all(path.is_file() for path in evidence_paths.values())
    ledger_active = not blockers
    duplicate_guard_ready = marker_path.is_file() and bool(selected) and evidence_present
    digest_material = {
        "approval_id": selected_approval_id,
        "ledger_write_digest": ledger_write_digest,
        "execution_id": execution_id,
        "marker_path": _rel(vault, marker_path),
        "ledger_path": (selected or {}).get("ledger_path"),
        "evidence_paths": {key: _rel(vault, path) for key, path in evidence_paths.items()},
        "ledger_active": ledger_active,
        "duplicate_guard_ready": duplicate_guard_ready,
        "memory_snapshot_unchanged": before_memory == after_memory,
    }

    return {
        "ok": ledger_active,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if ledger_active else BLOCKED_STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": {
            "real_ledger_activation_closeout_ready": True,
            "real_ledger_active": ledger_active,
            "approval_id": selected_approval_id or None,
            "approval_consumed": approval.get("approval_consumed") is True or approval.get("status") == "executed",
            "approval_status": approval.get("status"),
            "approval_execution_status": approval.get("execution_status"),
            "exact_once_marker_exists": marker_path.is_file(),
            "exact_once_marker_executed": (marker_payload or {}).get("status") == "executed",
            "marker_reserved_before_ledger_append": (marker_payload or {}).get(
                "marker_reserved_before_ledger_append"
            )
            is True,
            "evidence_outputs_present": evidence_present,
            "real_ledger_record_found": selected is not None,
            "memory_root_exists": (vault / MEMORY_ROOT).is_dir(),
            "ledger_file_exists": ledger_path.is_file() if selected else False,
            "ledger_line_count": len(ledger_entries),
            "read_model_results_count": (read_model.get("summary") or {}).get("results_count"),
            "duplicate_execution_would_block_before_append": duplicate_guard_ready,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "browser_control_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
            "memory_snapshot_unchanged": before_memory == after_memory,
            "blocker_count": len(list(dict.fromkeys(blockers))),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "selected_record": selected or {},
        "approval_record": approval,
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "exists": marker_path.is_file(),
            "status": (marker_payload or {}).get("status"),
            "marker_reserved_before_ledger_append": (marker_payload or {}).get(
                "marker_reserved_before_ledger_append"
            ),
            "ledger_entry_written": (marker_payload or {}).get("ledger_entry_written"),
            "ledger_line_sha256": (marker_payload or {}).get("ledger_line_sha256"),
        },
        "ledger": {
            "root_path": MEMORY_ROOT.as_posix(),
            "target_path": (selected or {}).get("ledger_path"),
            "filename": LEDGER_FILENAME,
            "exists": ledger_path.is_file() if selected else False,
            "line_count": len(ledger_entries),
            "ledger_write_digest": ledger_write_digest or None,
            "ledger_write_execution_id": execution_id or None,
        },
        "evidence_outputs": {key: _path_record(vault, path) for key, path in evidence_paths.items()},
        "evidence_payloads": {
            "execution_evidence": execution_evidence,
            "rollback_plan": rollback_plan,
            "ledger_entry_copy": ledger_entry_copy,
        },
        "duplicate_guard": {
            "exact_once_marker_present": marker_path.is_file(),
            "ledger_entry_present": selected is not None,
            "evidence_output_collision_present": evidence_present,
            "duplicate_execution_would_block_before_append": duplicate_guard_ready,
        },
        "read_model": {
            "surface": read_model.get("surface"),
            "status": read_model.get("status"),
            "summary": read_model.get("summary") or {},
            "filters": read_model.get("filters") or {},
        },
        "memory_snapshot_proof": {
            "root_path": MEMORY_ROOT.as_posix(),
            "files_before": before_memory,
            "files_after": after_memory,
            "unchanged": before_memory == after_memory,
            "memory_root_created_by_this_surface": False,
            "memory_ledger_written_by_this_surface": False,
        },
        "authority": _authority(),
        "readiness": {
            "companion_memory_real_ledger_activation_closeout_ready": True,
            "companion_memory_real_ledger_active": ledger_active,
            "companion_memory_real_ledger_write_completed": selected is not None,
            "companion_memory_exact_once_marker_verified": marker_path.is_file()
            and (marker_payload or {}).get("status") == "executed",
            "companion_memory_execution_evidence_verified": evidence_present,
            "companion_memory_duplicate_guard_verified": duplicate_guard_ready,
            "companion_memory_provider_calls_blocked": True,
            "companion_memory_runtime_dispatch_blocked": True,
            "companion_memory_agent_bus_write_blocked": True,
            "companion_memory_canonical_mutation_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "digest_proof": {
            "activation_closeout_digest": _sha256_text(_canonical_json(digest_material)),
            "digest_material": digest_material,
        },
        "denied_by_this_surface": [
            "approval_queue_write",
            "approval_consumption",
            "approval_execution",
            "companion_memory_ledger_append",
            "companion_memory_directory_create",
            "provider_api_call",
            "runtime_dispatch",
            "browser_control",
            "agent_bus_task_write",
            "gate_mutation",
            "git_mutation",
            "workflow_execution",
            "host_mutation",
            "canonical_writeback",
        ],
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "warnings": [],
    }


def format_phase11_companion_memory_real_ledger_activation_closeout(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    ledger = payload.get("ledger") or {}
    marker = payload.get("exact_once_marker") or {}
    lines = [
        "Phase 11 Companion Memory Real Ledger Activation Closeout",
        f"Status: {payload.get('status')}",
        f"Real ledger active: {summary.get('real_ledger_active')}",
        f"Approval id: {summary.get('approval_id') or 'missing'}",
        f"Approval consumed: {summary.get('approval_consumed')}",
        f"Approval status: {summary.get('approval_status') or 'missing'}",
        f"Marker exists: {summary.get('exact_once_marker_exists')}",
        f"Marker status: {marker.get('status') or 'missing'}",
        f"Marker reserved before append: {summary.get('marker_reserved_before_ledger_append')}",
        f"Evidence outputs present: {summary.get('evidence_outputs_present')}",
        f"Ledger path: {ledger.get('target_path') or 'none'}",
        f"Ledger line count: {summary.get('ledger_line_count')}",
        f"Duplicate guard ready: {summary.get('duplicate_execution_would_block_before_append')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
