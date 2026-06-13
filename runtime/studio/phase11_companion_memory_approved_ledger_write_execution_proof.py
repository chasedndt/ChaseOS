"""Phase 11 companion memory approved ledger-write execution proof.

This executor consumes one digest-bound companion-memory ledger-write approval
exactly once, reserves an execution marker before the ledger append, and writes
one real companion-memory JSONL entry. It stays deliberately narrower than a
general memory system: no provider calls, runtime dispatch, Agent Bus task
writes, canonical promotion, or broad vault mutation are granted here.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_companion_memory_ledger_write_approval_preview import (
    APPROVAL_CLASS,
    LEDGER_MARKER_DIR,
    MEMORY_ROOT,
    build_phase11_companion_memory_ledger_write_approval_preview,
)
from runtime.studio.service import ApprovalRequest, StudioService, StudioServiceError


MODEL_VERSION = "studio.phase11_companion_memory_approved_ledger_write_execution_proof.v1"
SURFACE_ID = "phase11_companion_memory_approved_ledger_write_execution_proof"
PASS_ID = "phase11-companion-memory-approved-ledger-write-execution-proof"
STATUS = "COMPLETE / APPROVAL-CONSUMED / REAL LEDGER WRITTEN / VERIFIED"
BLOCKED_STATUS = "BLOCKED / COMPANION-MEMORY-LEDGER-WRITE / NO LEDGER WRITE"
NEXT_RECOMMENDED_PASS = "phase11-companion-memory-ledger-read-model-preview"
EVIDENCE_ROOT = Path("07_LOGS") / "Studio-Graph-Views" / "cml-ledger-write-proof"
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"
AUDIT_SLUG = "phase11-cml-ledger-write-execution"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c == "-" else "_" for c in str(value or "")) or "unknown"


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_approval(service: StudioService, req: ApprovalRequest) -> None:
    service._write_approval_record(req)  # type: ignore[attr-defined]  # governed executor uses service persistence.


def _resolve_inside_vault(vault: Path, rel_path: str) -> Path:
    if not rel_path or not rel_path.strip():
        raise StudioServiceError("target_path_required")
    candidate = Path(rel_path)
    resolved = candidate.resolve() if candidate.is_absolute() else (vault / candidate).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise StudioServiceError("target_path_resolves_outside_vault") from exc
    return resolved


def _load_ledger_entry(content: str | None) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(str(content or "").strip() or "{}")
    except json.JSONDecodeError as exc:
        return None, f"approval_content_json_malformed:{exc}"
    if not isinstance(payload, dict):
        return None, "approval_content_json_not_object"
    return payload, None


def _read_jsonl_entries(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], []
    entries: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"existing_ledger_read_failed:{exc}"]
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"existing_ledger_line_malformed:{index}:{exc}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"existing_ledger_line_not_object:{index}")
            continue
        entries.append(payload)
    return entries, errors


def _evidence_paths(vault: Path, approval_id: str) -> dict[str, Path]:
    safe = _safe_id(approval_id)
    root = vault / EVIDENCE_ROOT
    return {
        "execution_evidence": root / f"{safe}-execution-evidence.json",
        "rollback_plan": root / f"{safe}-rollback-plan.json",
        "ledger_entry_copy": root / f"{safe}-ledger-entry.json",
    }


def _path_records(vault: Path, paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    return {
        key: {
            "path": _rel(vault, path),
            "exists": path.is_file(),
            "size_bytes": path.stat().st_size if path.is_file() else 0,
        }
        for key, path in paths.items()
    }


def _authority() -> dict[str, bool]:
    return {
        "approval_consumption_allowed": True,
        "approval_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "memory_root_create_allowed": True,
        "memory_ledger_write_allowed": True,
        "single_jsonl_append_allowed": True,
        "ledger_read_for_duplicate_guard_allowed": True,
        "evidence_write_allowed": True,
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


def _memory_snapshot(vault: Path) -> list[str]:
    root = vault / MEMORY_ROOT
    if not root.exists():
        return []
    return sorted(_rel(vault, path) for path in root.rglob("*") if path.is_file())


def _summary(
    *,
    approval_id: str | None,
    approval_status: str | None = None,
    operator_approval_recorded_from_statement: bool = False,
    expected_ledger_write_approval_digest: str | None = None,
    approval_consumed: bool = False,
    approval_status_mutated: bool = False,
    exact_once_marker_written: bool = False,
    marker_reserved_before_ledger_append: bool = False,
    ledger_entry_written: bool = False,
    ledger_line_count_after: int = 0,
    duplicate_blocked_before_ledger_append: bool = False,
    blocker_count: int = 0,
    memory_root_created: bool = False,
) -> dict[str, Any]:
    return {
        "approval_id": approval_id or None,
        "approval_status": approval_status,
        "operator_approval_recorded_from_statement": operator_approval_recorded_from_statement,
        "expected_ledger_write_approval_digest_provided": bool(expected_ledger_write_approval_digest),
        "approval_consumed": approval_consumed,
        "approval_status_mutated": approval_status_mutated,
        "exact_once_marker_written": exact_once_marker_written,
        "marker_reserved_before_ledger_append": marker_reserved_before_ledger_append,
        "memory_root_created": memory_root_created,
        "memory_ledger_written": ledger_entry_written,
        "memory_write_executed": ledger_entry_written,
        "ledger_entry_written": ledger_entry_written,
        "ledger_line_count_after": ledger_line_count_after,
        "duplicate_blocked_before_ledger_append": duplicate_blocked_before_ledger_append,
        "provider_call_performed": False,
        "runtime_dispatch_performed": False,
        "browser_control_performed": False,
        "agent_bus_task_written": False,
        "canonical_mutation_performed": False,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _blocked_payload(
    *,
    vault: Path,
    approval_id: str,
    expected_ledger_write_approval_digest: str,
    ledger_write_approval_digest: str | None,
    target_path: str | None,
    blockers: list[str],
    evidence_paths: dict[str, Path],
) -> dict[str, Any]:
    unique = list(dict.fromkeys(blockers))
    duplicate = any(
        item in unique
        for item in (
            "exact_once_marker_already_present",
            "ledger_entry_already_present",
            "future_evidence_output_collision",
        )
    )
    marker_path = vault / LEDGER_MARKER_DIR / f"{_safe_id(approval_id)}.json"
    ledger_path = vault / str(target_path or "")
    existing_entries, _errors = _read_jsonl_entries(ledger_path) if target_path else ([], [])
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
            expected_ledger_write_approval_digest=expected_ledger_write_approval_digest,
            duplicate_blocked_before_ledger_append=duplicate,
            ledger_line_count_after=len(existing_entries),
            blocker_count=len(unique),
            memory_root_created=(vault / MEMORY_ROOT).exists(),
        ),
        "digest_proof": {
            "expected_ledger_write_approval_digest": expected_ledger_write_approval_digest or None,
            "ledger_write_approval_digest": ledger_write_approval_digest,
            "ledger_write_approval_digest_matched": False,
            "approved_ledger_line_sha256": None,
            "executed_ledger_line_sha256": None,
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": False,
            "duplicate_blocked_before_ledger_append": duplicate,
        },
        "ledger": {
            "target_path": target_path,
            "target_exists": ledger_path.is_file() if target_path else False,
            "line_count_after": len(existing_entries),
            "entry_written": False,
        },
        "evidence_outputs": _path_records(vault, evidence_paths),
        "execution_record": {
            "execution_id": None,
            "execution_status": None,
        },
        "authority": _authority(),
        "blocked_reasons": unique,
    }


def _validate_approval(
    vault: Path,
    req: ApprovalRequest | None,
    *,
    expected_ledger_write_approval_digest: str,
    operator_approval_statement: str,
) -> tuple[dict[str, Any] | None, str | None, str | None, list[str]]:
    blockers: list[str] = []
    ledger_entry, content_error = _load_ledger_entry(req.action_spec.content if req else None)
    if content_error:
        blockers.append(content_error)
    if req is None:
        blockers.append("approval_request_not_found")
        return ledger_entry, None, None, blockers

    metadata = dict(req.action_spec.metadata or {})
    digest = str(metadata.get("phase11_companion_memory_ledger_write_approval_digest") or "")
    source_id = str(metadata.get("source_companion_memory_approval_id") or "")
    companion_id = str(metadata.get("companion_id") or "")
    target_path = str(req.action_spec.target_path or "")

    if req.status == "pending" and not operator_approval_statement:
        blockers.append("operator_decision_not_approved")
    elif req.status not in {"pending", "approved"}:
        blockers.append("approval_status_not_approved_or_pending_with_statement")
    if req.action_spec.action_type != "companion_memory_ledger_append":
        blockers.append("approval_action_type_not_companion_memory_ledger_append")
    if metadata.get("required_approval_class") != APPROVAL_CLASS:
        blockers.append("approval_class_not_companion_memory_ledger_write_future")
    if not digest:
        blockers.append("ledger_write_approval_digest_missing")
    if not expected_ledger_write_approval_digest:
        blockers.append("expected_ledger_write_approval_digest_required")
    elif expected_ledger_write_approval_digest != digest:
        blockers.append("ledger_write_approval_digest_mismatch")
    if not source_id:
        blockers.append("source_companion_memory_approval_id_missing")
    if not companion_id:
        blockers.append("companion_id_missing")
    expected_target = f"{MEMORY_ROOT.as_posix()}/{companion_id}/memory-ledger.jsonl"
    if target_path != expected_target:
        blockers.append("approval_target_path_not_expected_companion_memory_ledger")

    if ledger_entry is not None:
        if ledger_entry.get("source_approval_id") != source_id:
            blockers.append("ledger_entry_source_approval_id_mismatch")
        if ledger_entry.get("companion_id") != companion_id:
            blockers.append("ledger_entry_companion_id_mismatch")
        if ledger_entry.get("source_memory_approval_digest") != metadata.get("source_companion_memory_approval_digest"):
            blockers.append("ledger_entry_source_memory_digest_mismatch")
        if ledger_entry.get("trust_state") != "raw":
            blockers.append("ledger_entry_trust_state_not_raw")
        if ledger_entry.get("canonical") is not False or ledger_entry.get("authoritative") is not False:
            blockers.append("ledger_entry_claims_authoritative_or_canonical")

    if source_id and digest:
        preview = build_phase11_companion_memory_ledger_write_approval_preview(
            vault,
            source_approval_id=source_id,
        )
        recomputed = str((preview.get("digest_proof") or {}).get("ledger_write_approval_digest") or "")
        if preview.get("ok") is not True:
            blockers.append("source_ledger_write_preview_no_longer_valid")
            blockers.extend(str(item) for item in preview.get("blocked_reasons") or [])
        elif recomputed != digest:
            blockers.append("ledger_write_digest_no_longer_matches_source_preview")

    return ledger_entry, digest, target_path, blockers


def _executed_ledger_entry(
    approved_entry: dict[str, Any],
    *,
    approval_id: str,
    execution_id: str,
    ledger_write_approval_digest: str,
    ledger_written_at_utc: str,
) -> dict[str, Any]:
    entry = dict(approved_entry)
    entry.update(
        {
            "ledger_write_performed": True,
            "ledger_write_approval_id": approval_id,
            "ledger_write_approval_digest": ledger_write_approval_digest,
            "ledger_write_execution_id": execution_id,
            "ledger_written_at_utc": ledger_written_at_utc,
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "browser_control_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
            "canonical": False,
            "authoritative": False,
            "trust_state": "raw",
        }
    )
    return entry


def _marker_payload(
    *,
    status: str,
    approval_id: str,
    execution_id: str,
    ledger_write_approval_digest: str,
    target_path: str,
    operator_id: str,
    marker_reserved_before_ledger_append: bool,
    ledger_entry_written: bool,
    ledger_line_sha256: str | None = None,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "phase11_companion_memory_ledger_write_execution_marker.v1",
        "status": status,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "ledger_write_approval_digest": ledger_write_approval_digest,
        "target_path": target_path,
        "operator_id": operator_id,
        "marker_reserved_before_ledger_append": marker_reserved_before_ledger_append,
        "ledger_entry_written": ledger_entry_written,
        "ledger_line_sha256": ledger_line_sha256,
        "provider_call_performed": False,
        "runtime_dispatch_performed": False,
        "browser_control_performed": False,
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
    ledger_write_approval_digest: str,
    target_path: str,
    operator_id: str,
    ledger_line_sha256: str,
) -> str:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{AUDIT_SLUG}-{ledger_write_approval_digest[:20]}.md"
    if path.exists():
        for index in range(2, 100):
            candidate = root / f"{AUDIT_SLUG}-{ledger_write_approval_digest[:20]}-{index}.md"
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
            "# Phase 11 Companion Memory Approved Ledger-Write Execution Proof",
            "",
            f"operator_id: {operator_id}",
            f"approval_id: {approval_id}",
            f"execution_id: {execution_id}",
            f"ledger_write_approval_digest: {ledger_write_approval_digest}",
            f"target_path: {target_path}",
            f"ledger_line_sha256: {ledger_line_sha256}",
            "approval_consumed: true",
            "exact_once_marker_written: true",
            "marker_reserved_before_ledger_append: true",
            "memory_ledger_written: true",
            "provider_call_performed: false",
            "runtime_dispatch_performed: false",
            "browser_control_performed: false",
            "agent_bus_task_written: false",
            "canonical_mutation_performed: false",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return _rel(vault, path)


def execute_phase11_companion_memory_approved_ledger_write_execution_proof(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    expected_ledger_write_approval_digest: str | None = None,
    execute: bool = False,
    operator_id: str = "operator",
    operator_approval_statement: str | None = None,
) -> dict[str, Any]:
    """Consume one approved ledger-write request and append one JSONL memory entry."""

    vault = Path(vault_root).resolve()
    effective_approval_id = str(approval_id or "").strip()
    expected = str(expected_ledger_write_approval_digest or "").strip()
    operator = str(operator_id or "operator").strip() or "operator"
    approval_statement = " ".join(str(operator_approval_statement or "").strip().split())
    evidence_paths = _evidence_paths(vault, effective_approval_id)
    service = StudioService(vault)
    req = service.get_approval(effective_approval_id) if effective_approval_id else None
    approved_entry, ledger_write_digest, target_path, blockers = _validate_approval(
        vault,
        req,
        expected_ledger_write_approval_digest=expected,
        operator_approval_statement=approval_statement,
    )

    if not effective_approval_id:
        blockers.append("approval_id_required")
    if not execute:
        blockers.append("execute_flag_required")

    marker_path = vault / LEDGER_MARKER_DIR / f"{_safe_id(effective_approval_id)}.json"
    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")
    if any(path.exists() for path in evidence_paths.values()):
        blockers.append("future_evidence_output_collision")

    ledger_path: Path | None = None
    existing_entries: list[dict[str, Any]] = []
    if target_path:
        try:
            ledger_path = _resolve_inside_vault(vault, target_path)
        except StudioServiceError as exc:
            blockers.append(str(exc))
        if ledger_path is not None:
            existing_entries, existing_errors = _read_jsonl_entries(ledger_path)
            blockers.extend(existing_errors)
            for item in existing_entries:
                if item.get("ledger_write_approval_digest") == ledger_write_digest:
                    blockers.append("ledger_entry_already_present")
                    break
                if (
                    approved_entry
                    and item.get("source_approval_id") == approved_entry.get("source_approval_id")
                    and item.get("source_memory_approval_digest") == approved_entry.get("source_memory_approval_digest")
                ):
                    blockers.append("ledger_entry_already_present")
                    break

    if blockers:
        return _blocked_payload(
            vault=vault,
            approval_id=effective_approval_id,
            expected_ledger_write_approval_digest=expected,
            ledger_write_approval_digest=ledger_write_digest,
            target_path=target_path,
            blockers=blockers,
            evidence_paths=evidence_paths,
        )

    assert req is not None
    assert approved_entry is not None
    assert ledger_write_digest is not None
    assert target_path is not None
    assert ledger_path is not None

    execution_id = f"companion-memory-ledger-write-{ledger_write_digest[:20]}"
    approval_recorded_from_statement = False
    memory_before = _memory_snapshot(vault)

    try:
        now = _now_utc()
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
                ledger_write_approval_digest=ledger_write_digest,
                target_path=target_path,
                operator_id=operator,
                marker_reserved_before_ledger_append=True,
                ledger_entry_written=False,
            ),
        )
        marker_reserved_before_ledger_append = marker_path.is_file()

        ledger_written_at = _now_utc()
        executed_entry = _executed_ledger_entry(
            approved_entry,
            approval_id=effective_approval_id,
            execution_id=execution_id,
            ledger_write_approval_digest=ledger_write_digest,
            ledger_written_at_utc=ledger_written_at,
        )
        approved_line = str(req.action_spec.content or "")
        executed_line = _canonical_json(executed_entry) + "\n"
        approved_line_sha = _sha256_text(approved_line)
        executed_line_sha = _sha256_text(executed_line)

        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(executed_line)

        after_entries, after_errors = _read_jsonl_entries(ledger_path)
        if after_errors:
            raise StudioServiceError("; ".join(after_errors))

        execution_evidence = {
            "record_type": "phase11_companion_memory_ledger_write_execution_evidence",
            "status": STATUS,
            "approval_id": effective_approval_id,
            "execution_id": execution_id,
            "ledger_write_approval_digest": ledger_write_digest,
            "target_path": target_path,
            "marker_path": _rel(vault, marker_path),
            "marker_reserved_before_ledger_append": marker_reserved_before_ledger_append,
            "ledger_entry_written": True,
            "ledger_line_count_before": len(existing_entries),
            "ledger_line_count_after": len(after_entries),
            "approved_ledger_line_sha256": approved_line_sha,
            "executed_ledger_line_sha256": executed_line_sha,
            "execution_transform_fields": [
                "ledger_write_performed",
                "ledger_write_approval_id",
                "ledger_write_approval_digest",
                "ledger_write_execution_id",
                "ledger_written_at_utc",
            ],
            "provider_call_performed": False,
            "runtime_dispatch_performed": False,
            "browser_control_performed": False,
            "agent_bus_task_written": False,
            "canonical_mutation_performed": False,
            "generated_at_utc": _now_utc(),
        }
        rollback_plan = {
            "record_type": "phase11_companion_memory_ledger_write_rollback_plan",
            "approval_id": effective_approval_id,
            "execution_id": execution_id,
            "rollback_scope": "remove_last_jsonl_line_if_sha256_matches",
            "target_path": target_path,
            "line_to_remove_sha256": executed_line_sha,
            "line_count_after_execution": len(after_entries),
            "manual_review_required": True,
            "automatic_rollback_performed": False,
        }
        _write_json(evidence_paths["ledger_entry_copy"], executed_entry)
        _write_json(evidence_paths["execution_evidence"], execution_evidence)
        _write_json(evidence_paths["rollback_plan"], rollback_plan)

        _write_json(
            marker_path,
            _marker_payload(
                status="executed",
                approval_id=effective_approval_id,
                execution_id=execution_id,
                ledger_write_approval_digest=ledger_write_digest,
                target_path=target_path,
                operator_id=operator,
                marker_reserved_before_ledger_append=marker_reserved_before_ledger_append,
                ledger_entry_written=True,
                ledger_line_sha256=executed_line_sha,
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
                "phase11_companion_memory_approved_ledger_write_execution_proof": True,
                "phase11_companion_memory_ledger_write_execution_id": execution_id,
                "approval_consumed": True,
                "marker_reserved_before_ledger_append": marker_reserved_before_ledger_append,
                "companion_memory_ledger_write_performed": True,
                "companion_memory_root_created": bool((vault / MEMORY_ROOT).exists() and not memory_before),
                "approved_ledger_line_sha256": approved_line_sha,
                "executed_ledger_line_sha256": executed_line_sha,
                "provider_call_performed": False,
                "runtime_dispatch_performed": False,
                "browser_control_performed": False,
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
            ledger_write_approval_digest=ledger_write_digest,
            target_path=target_path,
            operator_id=operator,
            ledger_line_sha256=executed_line_sha,
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
                    ledger_write_approval_digest=ledger_write_digest,
                    target_path=target_path,
                    operator_id=operator,
                    marker_reserved_before_ledger_append=marker_path.exists(),
                    ledger_entry_written=ledger_path.is_file() and ledger_path.stat().st_size > 0,
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
            expected_ledger_write_approval_digest=expected,
            ledger_write_approval_digest=ledger_write_digest,
            target_path=target_path,
            blockers=[f"companion_memory_ledger_write_execution_failed:{error}"],
            evidence_paths=evidence_paths,
        )
        failed["status"] = "FAILED / COMPANION-MEMORY-LEDGER-WRITE / PARTIAL CHECK REQUIRED"
        return failed

    memory_after = _memory_snapshot(vault)
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
            expected_ledger_write_approval_digest=expected,
            approval_consumed=True,
            approval_status_mutated=True,
            exact_once_marker_written=True,
            marker_reserved_before_ledger_append=marker_reserved_before_ledger_append,
            ledger_entry_written=True,
            ledger_line_count_after=len(after_entries),
            blocker_count=0,
            memory_root_created=bool((vault / MEMORY_ROOT).exists() and not memory_before),
        ),
        "digest_proof": {
            "expected_ledger_write_approval_digest": expected,
            "ledger_write_approval_digest": ledger_write_digest,
            "ledger_write_approval_digest_matched": True,
            "approved_ledger_line_sha256": approved_line_sha,
            "executed_ledger_line_sha256": executed_line_sha,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "approval_id": effective_approval_id,
                        "execution_id": execution_id,
                        "ledger_write_approval_digest": ledger_write_digest,
                        "executed_ledger_line_sha256": executed_line_sha,
                        "target_path": target_path,
                    }
                )
            ),
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": marker_path.is_file(),
            "duplicate_blocked_before_ledger_append": False,
        },
        "ledger": {
            "target_path": target_path,
            "target_exists": ledger_path.is_file(),
            "entry_written": True,
            "ledger_line_count_before": len(existing_entries),
            "line_count_after": len(after_entries),
            "ledger_line_sha256": executed_line_sha,
            "entry": executed_entry,
        },
        "evidence_outputs": _path_records(vault, evidence_paths),
        "execution_record": {
            "execution_id": execution_id,
            "execution_status": "completed",
        },
        "audit_record": {
            "audit_written": True,
            "audit_record_path": audit_path,
        },
        "memory_snapshot_proof": {
            "root_path": MEMORY_ROOT.as_posix(),
            "files_before": memory_before,
            "files_after": memory_after,
            "target_path": target_path,
            "target_file_present_after": ledger_path.is_file(),
        },
        "authority": _authority(),
        "blocked_reasons": [],
        "warnings": [],
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }


def format_phase11_companion_memory_approved_ledger_write_execution_proof(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    marker = payload.get("exact_once_marker") or {}
    digest = payload.get("digest_proof") or {}
    ledger = payload.get("ledger") or {}
    lines = [
        "Phase 11 Companion Memory Approved Ledger-Write Execution Proof",
        f"Status: {payload.get('status')}",
        f"Approval id: {summary.get('approval_id') or 'missing'}",
        f"Approval consumed: {summary.get('approval_consumed')}",
        f"Approval status mutated: {summary.get('approval_status_mutated')}",
        f"Exact-once marker written: {summary.get('exact_once_marker_written')}",
        f"Marker reserved before ledger append: {summary.get('marker_reserved_before_ledger_append')}",
        f"Memory ledger written: {summary.get('memory_ledger_written')}",
        f"Ledger path: {ledger.get('target_path') or 'none'}",
        f"Ledger line count after: {summary.get('ledger_line_count_after')}",
        f"Ledger-write approval digest matched: {digest.get('ledger_write_approval_digest_matched')}",
        f"Marker path: {marker.get('marker_path') or 'none'}",
        f"Next recommended pass: {summary.get('next_recommended_pass') or payload.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
