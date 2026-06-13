"""Phase 11 companion memory approved execution proof.

This governed executor consumes one digest-bound companion-memory approval
exactly once, reserves an execution marker before proof outputs, and writes
proof-only evidence. It intentionally does not create the companion-memory root
or append to a real memory ledger.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_companion_memory_approval_preview import APPROVAL_CLASS
from runtime.studio.service import ApprovalRequest, StudioService


MODEL_VERSION = "studio.phase11_companion_memory_approved_execution_proof.v1"
SURFACE_ID = "phase11_companion_memory_approved_execution_proof"
PASS_ID = "phase11-companion-memory-approved-execution-proof"
STATUS = "COMPLETE / APPROVAL-CONSUMED / PROOF WRITTEN / MEMORY LEDGER WRITE BLOCKED"
BLOCKED_STATUS = "BLOCKED / COMPANION-MEMORY-EXECUTION / NO PROOF WRITE"
NEXT_RECOMMENDED_PASS = "phase11-companion-memory-ledger-write-approval-preview"
MARKER_DIR = Path("runtime/studio/approvals/_companion_memory_execution_markers")
PROOF_ROOT = Path(".pytest_tmp_env/phase11-companion-memory-proof")
EVIDENCE_ROOT = Path("07_LOGS/Studio-Graph-Views/phase11-companion-memory-approved-execution-proof")
AUDIT_DIR = Path("07_LOGS/Agent-Activity")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c == "-" else "_" for c in str(value or "")) or "unknown"


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_approval(service: StudioService, req: ApprovalRequest) -> None:
    service._write_approval_record(req)  # type: ignore[attr-defined]  # governed executor reuses service persistence.


def _load_action_content(req: ApprovalRequest | None) -> tuple[dict[str, Any] | None, str | None]:
    if req is None:
        return None, "approval_request_not_loadable"
    try:
        payload = json.loads(str(req.action_spec.content or "{}"))
    except json.JSONDecodeError as exc:
        return None, f"approval_content_json_malformed:{exc}"
    if not isinstance(payload, dict):
        return None, "approval_content_json_not_object"
    return payload, None


def _proof_paths(vault: Path, approval_id: str) -> dict[str, Path]:
    safe = _safe_id(approval_id)
    root = vault / PROOF_ROOT / safe
    evidence_root = vault / EVIDENCE_ROOT
    return {
        "proof_memory_record": root / "proof-memory-record.json",
        "dry_run_evidence": root / "dry-run-evidence.json",
        "rollback_plan": root / "rollback-plan.json",
        "execution_audit": root / "execution-audit.json",
        "execution_evidence": evidence_root / f"{safe}-execution-evidence.json",
    }


def _proof_path_records(vault: Path, paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    return {
        key: {
            "path": _rel(vault, path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.is_file() else 0,
        }
        for key, path in paths.items()
    }


def _memory_root_exists(vault: Path) -> bool:
    return (vault / "07_LOGS" / "Companion-Memory").exists()


def _authority() -> dict[str, bool]:
    return {
        "approval_consumption_allowed": True,
        "approval_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "proof_output_write_allowed": True,
        "memory_ledger_write_allowed": False,
        "memory_root_create_allowed": False,
        "provider_calls_allowed": False,
        "runtime_dispatch_allowed": False,
        "agent_bus_task_write_allowed": False,
        "gate_mutation_allowed": False,
        "git_mutation_allowed": False,
        "workflow_execution_allowed": False,
        "host_mutation_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _summary(
    *,
    approval_id: str | None,
    approval_status: str | None = None,
    operator_approval_recorded_from_statement: bool = False,
    expected_memory_approval_digest: str | None = None,
    approval_consumed: bool = False,
    approval_status_mutated: bool = False,
    exact_once_marker_written: bool = False,
    marker_reserved_before_outputs: bool = False,
    proof_outputs_written: bool = False,
    duplicate_blocked_before_outputs: bool = False,
    blocker_count: int = 0,
    memory_root_created: bool = False,
) -> dict[str, Any]:
    return {
        "approval_id": approval_id or None,
        "approval_status": approval_status,
        "operator_approval_recorded_from_statement": operator_approval_recorded_from_statement,
        "expected_memory_approval_digest_provided": bool(expected_memory_approval_digest),
        "approval_consumed": approval_consumed,
        "approval_status_mutated": approval_status_mutated,
        "exact_once_marker_written": exact_once_marker_written,
        "marker_reserved_before_outputs": marker_reserved_before_outputs,
        "proof_outputs_written": proof_outputs_written,
        "duplicate_blocked_before_outputs": duplicate_blocked_before_outputs,
        "memory_ledger_written": False,
        "memory_write_executed": False,
        "memory_root_created": memory_root_created,
        "provider_call_performed": False,
        "runtime_dispatch_performed": False,
        "agent_bus_task_written": False,
        "canonical_mutation_performed": False,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _blocked_payload(
    *,
    vault: Path,
    approval_id: str,
    expected_memory_approval_digest: str,
    memory_approval_digest: str | None,
    blockers: list[str],
    proof_paths: dict[str, Path],
) -> dict[str, Any]:
    unique = list(dict.fromkeys(blockers))
    duplicate = "exact_once_marker_already_present" in unique
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": BLOCKED_STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            approval_id=approval_id,
            expected_memory_approval_digest=expected_memory_approval_digest,
            duplicate_blocked_before_outputs=duplicate,
            blocker_count=len(unique),
            memory_root_created=_memory_root_exists(vault),
        ),
        "digest_proof": {
            "expected_memory_approval_digest": expected_memory_approval_digest or None,
            "memory_approval_digest": memory_approval_digest,
            "memory_approval_digest_matched": False,
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, vault / MARKER_DIR / f"{_safe_id(approval_id)}.json"),
            "marker_written": False,
            "duplicate_blocked_before_outputs": duplicate,
        },
        "proof_outputs": _proof_path_records(vault, proof_paths),
        "execution_record": {
            "execution_id": None,
            "execution_status": None,
        },
        "audit_record": {
            "audit_written": False,
            "audit_record_path": None,
        },
        "authority": _authority(),
        "blocked_reasons": unique,
    }


def _validate_approval(
    req: ApprovalRequest | None,
    *,
    expected_memory_approval_digest: str,
    operator_approval_statement: str,
) -> tuple[dict[str, Any] | None, str | None, list[str]]:
    blockers: list[str] = []
    content_payload, content_error = _load_action_content(req)
    if content_error:
        blockers.append(content_error)
    if req is None:
        return content_payload, None, blockers

    metadata = dict(req.action_spec.metadata or {})
    memory_approval_digest = str(metadata.get("phase11_companion_memory_approval_digest") or "")
    companion_id = str(metadata.get("companion_id") or "")

    if req.status == "pending" and not operator_approval_statement:
        blockers.append("operator_decision_not_approved")
    elif req.status not in {"pending", "approved"}:
        blockers.append("approval_status_not_approved_or_pending_with_statement")
    if req.action_spec.action_type != "companion_memory_write":
        blockers.append("approval_action_type_not_companion_memory_write")
    if metadata.get("required_approval_class") != APPROVAL_CLASS:
        blockers.append("approval_class_not_companion_memory_future")
    if not memory_approval_digest:
        blockers.append("memory_approval_digest_missing")
    if not expected_memory_approval_digest:
        blockers.append("expected_memory_approval_digest_required")
    elif expected_memory_approval_digest != memory_approval_digest:
        blockers.append("memory_approval_digest_mismatch")
    target_path = str(req.action_spec.target_path or "")
    expected_prefix = f"07_LOGS/Companion-Memory/{companion_id}/"
    if not target_path.startswith(expected_prefix) or not target_path.endswith("/memory-ledger.jsonl"):
        blockers.append("approval_target_path_not_companion_memory_ledger")
    if content_payload is not None:
        if content_payload.get("target_path") != target_path:
            blockers.append("approval_content_target_path_mismatch")
        if content_payload.get("companion_id") != companion_id:
            blockers.append("approval_content_companion_id_mismatch")
        if content_payload.get("content_sha256") is None:
            blockers.append("approval_content_sha256_missing")
        if content_payload.get("memory_file_written") is not False:
            blockers.append("approval_content_not_preview_only")
    return content_payload, memory_approval_digest, blockers


def _marker_payload(
    *,
    status: str,
    approval_id: str,
    execution_id: str,
    memory_approval_digest: str,
    target_path: str,
    operator_id: str,
    marker_reserved_before_outputs: bool,
    proof_outputs_written: bool,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "phase11_companion_memory_execution_marker.v1",
        "status": status,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "memory_approval_digest": memory_approval_digest,
        "target_path": target_path,
        "operator_id": operator_id,
        "marker_reserved_before_outputs": marker_reserved_before_outputs,
        "proof_outputs_written": proof_outputs_written,
        "memory_ledger_written": False,
        "memory_root_created": False,
        "provider_call_performed": False,
        "runtime_dispatch_performed": False,
        "agent_bus_task_written": False,
        "canonical_mutation_performed": False,
        "error": error,
        "updated_at_utc": _now_utc(),
    }


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    memory_approval_digest: str,
    target_path: str,
    operator_id: str,
) -> str:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{PASS_ID}-{memory_approval_digest[:20]}.md"
    if path.exists():
        for index in range(2, 100):
            candidate = root / f"{PASS_ID}-{memory_approval_digest[:20]}-{index}.md"
            if not candidate.exists():
                path = candidate
                break
    text = "\n".join(
        [
            "---",
            "type: agent-activity",
            "runtime: Codex",
            f"pass_id: {PASS_ID}",
            f"approval_id: {approval_id}",
            f"execution_id: {execution_id}",
            f"status: {STATUS}",
            "---",
            "",
            "# Phase 11 Companion Memory Approved Execution Proof",
            "",
            f"operator_id: {operator_id}",
            f"approval_id: {approval_id}",
            f"execution_id: {execution_id}",
            f"memory_approval_digest: {memory_approval_digest}",
            f"target_path: {target_path}",
            "approval_consumed: true",
            "exact_once_marker_written: true",
            "proof_outputs_written: true",
            "memory_ledger_written: false",
            "memory_root_created: false",
            "provider_call_performed: false",
            "runtime_dispatch_performed: false",
            "agent_bus_task_written: false",
            "canonical_mutation_performed: false",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return _rel(vault, path)


def execute_phase11_companion_memory_approved_execution_proof(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    expected_memory_approval_digest: str | None = None,
    execute: bool = False,
    operator_id: str = "operator",
    operator_approval_statement: str | None = None,
) -> dict[str, Any]:
    """Consume one approved companion-memory request and write proof-only outputs."""

    vault = Path(vault_root).resolve()
    effective_approval_id = str(approval_id or "").strip()
    expected = str(expected_memory_approval_digest or "").strip()
    operator = str(operator_id or "operator").strip() or "operator"
    approval_statement = " ".join(str(operator_approval_statement or "").strip().split())
    proof_paths = _proof_paths(vault, effective_approval_id)
    service = StudioService(vault)
    req = service.get_approval(effective_approval_id) if effective_approval_id else None
    content_payload, memory_approval_digest, blockers = _validate_approval(
        req,
        expected_memory_approval_digest=expected,
        operator_approval_statement=approval_statement,
    )

    if not effective_approval_id:
        blockers.append("approval_id_required")
    if not execute:
        blockers.append("execute_flag_required")
    marker_path = vault / MARKER_DIR / f"{_safe_id(effective_approval_id)}.json"
    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")
    if any(path.exists() for path in proof_paths.values()):
        blockers.append("future_proof_output_collision")

    if blockers:
        return _blocked_payload(
            vault=vault,
            approval_id=effective_approval_id,
            expected_memory_approval_digest=expected,
            memory_approval_digest=memory_approval_digest,
            blockers=blockers,
            proof_paths=proof_paths,
        )

    assert req is not None
    assert memory_approval_digest is not None
    content_payload = content_payload or {}
    execution_id = f"companion-memory-execution-{memory_approval_digest[:20]}"
    target_path = req.action_spec.target_path
    now = _now_utc()
    approval_recorded_from_statement = False

    try:
        if req.status == "pending" and approval_statement:
            req.status = "approved"
            req.reviewed_by = operator
            req.reason = approval_statement
            req.updated_at = now
            _write_approval(service, req)
            approval_recorded_from_statement = True

        req.status = "executing"
        req.execution_id = execution_id
        req.execution_started_at = _now_utc()
        req.execution_finished_at = None
        req.execution_status = None
        req.result_action_id = None
        req.execution_error = ""
        req.updated_at = req.execution_started_at
        _write_approval(service, req)

        marker_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            marker_path,
            _marker_payload(
                status="executing",
                approval_id=effective_approval_id,
                execution_id=execution_id,
                memory_approval_digest=memory_approval_digest,
                target_path=target_path,
                operator_id=operator,
                marker_reserved_before_outputs=True,
                proof_outputs_written=False,
            ),
        )
        marker_reserved_before_outputs = marker_path.is_file()

        proof_record = dict(content_payload)
        proof_record.update(
            {
                "proof_only": True,
                "proof_execution_id": execution_id,
                "approval_id": effective_approval_id,
                "memory_approval_digest": memory_approval_digest,
                "memory_file_written": False,
                "memory_ledger_written": False,
                "memory_root_created": False,
                "created_by_executor": False,
            }
        )
        dry_run = {
            "record_type": "phase11_companion_memory_dry_run_evidence",
            "approval_id": effective_approval_id,
            "execution_id": execution_id,
            "memory_approval_digest": memory_approval_digest,
            "target_path": target_path,
            "generated_at_utc": _now_utc(),
            "memory_ledger_written": False,
            "proof_only": True,
        }
        rollback = {
            "record_type": "phase11_companion_memory_rollback_plan",
            "approval_id": effective_approval_id,
            "execution_id": execution_id,
            "rollback_scope": "proof_outputs_and_marker_only",
            "real_memory_ledger_rollback_required": False,
            "paths_to_remove_if_rolled_back": [_rel(vault, path) for path in proof_paths.values()] + [_rel(vault, marker_path)],
        }
        audit = {
            "record_type": "phase11_companion_memory_execution_audit",
            "approval_id": effective_approval_id,
            "execution_id": execution_id,
            "marker_reserved_before_outputs": marker_reserved_before_outputs,
            "memory_ledger_written": False,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
        }
        execution_evidence = {
            "record_type": "phase11_companion_memory_execution_evidence",
            "status": STATUS,
            "approval_id": effective_approval_id,
            "execution_id": execution_id,
            "memory_approval_digest": memory_approval_digest,
            "target_path": target_path,
            "marker_reserved_before_outputs": marker_reserved_before_outputs,
            "proof_outputs_written": True,
            "memory_ledger_written": False,
            "memory_root_created": False,
            "proof_record_sha256": _sha256_text(_canonical_json(proof_record)),
        }
        _write_json(proof_paths["proof_memory_record"], proof_record)
        _write_json(proof_paths["dry_run_evidence"], dry_run)
        _write_json(proof_paths["rollback_plan"], rollback)
        _write_json(proof_paths["execution_audit"], audit)
        _write_json(proof_paths["execution_evidence"], execution_evidence)

        _write_json(
            marker_path,
            _marker_payload(
                status="executed",
                approval_id=effective_approval_id,
                execution_id=execution_id,
                memory_approval_digest=memory_approval_digest,
                target_path=target_path,
                operator_id=operator,
                marker_reserved_before_outputs=marker_reserved_before_outputs,
                proof_outputs_written=True,
            ),
        )

        req.status = "executed"
        req.execution_finished_at = _now_utc()
        req.execution_status = "completed"
        req.result_action_id = execution_id
        req.execution_error = ""
        req.updated_at = req.execution_finished_at
        metadata = dict(req.action_spec.metadata or {})
        metadata.update(
            {
                "phase11_companion_memory_execution_proof": True,
                "phase11_companion_memory_execution_id": execution_id,
                "approval_consumed": True,
                "proof_outputs_written": True,
                "marker_reserved_before_outputs": marker_reserved_before_outputs,
                "companion_memory_file_written": False,
                "memory_write_executed": False,
                "memory_ledger_written": False,
                "memory_root_created": False,
                "provider_call_performed": False,
                "runtime_dispatch_performed": False,
                "agent_bus_task_write_performed": False,
                "canonical_mutation_allowed": False,
            }
        )
        req.action_spec.metadata = metadata
        _write_approval(service, req)

        audit_path = _write_audit(
            vault=vault,
            approval_id=effective_approval_id,
            execution_id=execution_id,
            memory_approval_digest=memory_approval_digest,
            target_path=target_path,
            operator_id=operator,
        )
    except Exception as exc:
        error = str(exc)
        try:
            _write_json(
                marker_path,
                _marker_payload(
                    status="execution_failed",
                    approval_id=effective_approval_id,
                    execution_id=execution_id,
                    memory_approval_digest=memory_approval_digest,
                    target_path=target_path,
                    operator_id=operator,
                    marker_reserved_before_outputs=marker_path.exists(),
                    proof_outputs_written=any(path.exists() for path in proof_paths.values()),
                    error=error,
                ),
            )
            req.status = "execution_failed"
            req.execution_finished_at = _now_utc()
            req.execution_status = "error"
            req.result_action_id = execution_id
            req.execution_error = error
            req.updated_at = req.execution_finished_at
            _write_approval(service, req)
        except Exception:
            pass
        failed = _blocked_payload(
            vault=vault,
            approval_id=effective_approval_id,
            expected_memory_approval_digest=expected,
            memory_approval_digest=memory_approval_digest,
            blockers=[f"companion_memory_execution_failed:{error}"],
            proof_paths=proof_paths,
        )
        failed["status"] = "FAILED / COMPANION-MEMORY-EXECUTION / PARTIAL PROOF CHECK REQUIRED"
        return failed

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            approval_id=effective_approval_id,
            approval_status="executed",
            operator_approval_recorded_from_statement=approval_recorded_from_statement,
            expected_memory_approval_digest=expected,
            approval_consumed=True,
            approval_status_mutated=True,
            exact_once_marker_written=True,
            marker_reserved_before_outputs=marker_reserved_before_outputs,
            proof_outputs_written=True,
            blocker_count=0,
            memory_root_created=_memory_root_exists(vault),
        ),
        "digest_proof": {
            "expected_memory_approval_digest": expected,
            "memory_approval_digest": memory_approval_digest,
            "memory_approval_digest_matched": True,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "approval_id": effective_approval_id,
                        "execution_id": execution_id,
                        "memory_approval_digest": memory_approval_digest,
                        "proof_only": True,
                        "memory_ledger_written": False,
                    }
                )
            ),
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": marker_path.is_file(),
            "duplicate_blocked_before_outputs": False,
        },
        "proof_outputs": _proof_path_records(vault, proof_paths),
        "execution_record": {
            "execution_id": execution_id,
            "execution_status": "completed",
        },
        "audit_record": {
            "audit_written": True,
            "audit_record_path": audit_path,
        },
        "authority": _authority(),
        "blocked_reasons": [],
        "warnings": [],
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def format_phase11_companion_memory_approved_execution_proof(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    marker = payload.get("exact_once_marker") or {}
    digest = payload.get("digest_proof") or {}
    lines = [
        "Phase 11 Companion Memory Approved Execution Proof",
        f"Status: {payload.get('status')}",
        f"Approval id: {summary.get('approval_id') or 'missing'}",
        f"Approval consumed: {summary.get('approval_consumed')}",
        f"Approval status mutated: {summary.get('approval_status_mutated')}",
        f"Exact-once marker written: {summary.get('exact_once_marker_written')}",
        f"Marker reserved before outputs: {summary.get('marker_reserved_before_outputs')}",
        f"Proof outputs written: {summary.get('proof_outputs_written')}",
        f"Memory ledger written: {summary.get('memory_ledger_written')}",
        f"Memory root created: {summary.get('memory_root_created')}",
        f"Memory approval digest matched: {digest.get('memory_approval_digest_matched')}",
        f"Marker path: {marker.get('marker_path') or 'none'}",
        f"Next recommended pass: {summary.get('next_recommended_pass') or payload.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
