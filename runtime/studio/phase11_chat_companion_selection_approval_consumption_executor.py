"""Phase 11 companion-selection approval consumption executor.

This governed executor consumes a digest-bound companion-selection approval and
writes the approved selection target exactly once. It is intentionally separate
from the generic StudioService approval executor so ambient approval execution
does not gain companion-selection mutation authority.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_companion_selection_approval_consumption_readiness import (
    MARKER_DIR,
    build_phase11_chat_companion_selection_approval_consumption_readiness,
)
from runtime.studio.phase11_chat_companion_selection_preview import SELECTION_TARGET_PATH
from runtime.studio.service import ApprovalRequest, StudioService


MODEL_VERSION = "studio.phase11_chat_companion_selection_approval_consumption_executor.v1"
SURFACE_ID = "phase11_chat_companion_selection_approval_consumption_executor"
PASS_ID = "phase11-chat-companion-selection-approval-consumption-executor"
STATUS = "COMPLETE / APPROVAL-CONSUMED / VERIFIED / COMPANION SELECTION WRITTEN"
NEXT_RECOMMENDED_PASS = "operator-select-next-governed-executor-lane"
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_id(value: str | None) -> str:
    return "".join(c if c.isalnum() or c == "-" else "_" for c in str(value or ""))


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _authority() -> dict[str, bool]:
    return {
        "approval_consumption_allowed": True,
        "approval_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "target_vault_write_allowed": True,
        "companion_selection_write_allowed": True,
        "runtime_control_allowed": False,
        "runtime_dispatch_allowed": False,
        "identity_ledger_mutation_allowed": False,
        "role_card_mutation_allowed": False,
        "profile_write_allowed": False,
        "provider_calls_allowed": False,
        "agent_bus_task_write_allowed": False,
        "canonical_mutation_allowed": False,
    }


def _summary(
    *,
    readiness: dict[str, Any],
    approval_id: str,
    expected_consumption_digest: str,
    operator_approval_recorded: bool = False,
    approval_status: str | None = None,
    approval_consumed: bool = False,
    approval_status_mutated: bool = False,
    exact_once_marker_written: bool = False,
    companion_selection_written: bool = False,
    target_write_performed: bool = False,
    duplicate_blocked_before_target_write: bool = False,
    blocker_count: int = 0,
) -> dict[str, Any]:
    source = readiness.get("summary") or {}
    return {
        "approval_id": approval_id or source.get("selected_approval_id"),
        "approval_status": approval_status or source.get("approval_status"),
        "operator_approval_recorded_from_statement": operator_approval_recorded,
        "expected_consumption_digest_provided": bool(expected_consumption_digest),
        "approval_consumed": approval_consumed,
        "approval_status_mutated": approval_status_mutated,
        "exact_once_marker_written": exact_once_marker_written,
        "companion_selection_written": companion_selection_written,
        "target_write_performed": target_write_performed,
        "duplicate_blocked_before_target_write": duplicate_blocked_before_target_write,
        "runtime_control_performed": False,
        "runtime_dispatch_performed": False,
        "provider_call_performed": False,
        "agent_bus_task_written": False,
        "identity_ledger_mutated": False,
        "profile_writes_performed": False,
        "role_card_writes_performed": False,
        "canonical_mutation_performed": False,
        "selected_runtime_id": source.get("selected_runtime_id"),
        "previous_runtime_id": source.get("previous_runtime_id"),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _blocked_payload(
    *,
    vault: Path,
    readiness: dict[str, Any],
    approval_id: str,
    expected_consumption_digest: str,
    blockers: list[str],
) -> dict[str, Any]:
    unique_blockers = list(dict.fromkeys(blockers))
    digest = readiness.get("digest_proof") or {}
    marker = readiness.get("exact_once_marker_preview") or {}
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "BLOCKED / APPROVAL-CONSUMPTION / NO COMPANION SELECTION WRITE",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            readiness=readiness,
            approval_id=approval_id,
            expected_consumption_digest=expected_consumption_digest,
            duplicate_blocked_before_target_write="exact_once_marker_already_present" in unique_blockers,
            blocker_count=len(unique_blockers),
        ),
        "readiness_contract": readiness,
        "digest_proof": {
            "expected_consumption_digest": expected_consumption_digest or None,
            "consumption_digest": digest.get("consumption_digest"),
            "consumption_digest_matched": False,
        },
        "exact_once_marker": {
            "marker_path": marker.get("marker_path_preview"),
            "marker_written": False,
            "duplicate_blocked_before_target_write": "exact_once_marker_already_present" in unique_blockers,
        },
        "target_write": {
            "target_path": SELECTION_TARGET_PATH,
            "target_write_performed": False,
        },
        "execution_record": {
            "execution_id": None,
            "execution_status": None,
        },
        "audit_record": {
            "audit_written": False,
            "audit_record_path": None,
        },
        "authority": _authority(),
        "blocked_reasons": unique_blockers,
    }


def _load_content_payload(req: ApprovalRequest) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(str(req.action_spec.content or "{}"))
    except json.JSONDecodeError as exc:
        return None, f"approval_content_json_malformed:{exc}"
    if not isinstance(payload, dict):
        return None, "approval_content_json_not_object"
    return payload, None


def _write_approval(service: StudioService, req: ApprovalRequest) -> None:
    service._write_approval_record(req)  # type: ignore[attr-defined]  # Executor uses Studio's durable queue writer.


def _marker_payload(
    *,
    status: str,
    approval_id: str,
    execution_id: str,
    consumption_digest: str,
    target_path: str,
    operator_id: str,
    target_write_performed: bool,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "phase11_companion_selection_consumption_marker.v1",
        "status": status,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "consumption_digest": consumption_digest,
        "target_path": target_path,
        "operator_id": operator_id,
        "target_write_performed": target_write_performed,
        "runtime_control_performed": False,
        "provider_call_performed": False,
        "agent_bus_task_written": False,
        "canonical_mutation_performed": False,
        "error": error,
        "updated_at_utc": _now_utc(),
    }


def _next_audit_path(vault: Path, consumption_digest: str) -> Path:
    root = vault / AUDIT_DIR
    root.mkdir(parents=True, exist_ok=True)
    base = root / f"{PASS_ID}-{consumption_digest[:20]}.md"
    if not base.exists():
        return base
    for index in range(2, 100):
        candidate = root / f"{PASS_ID}-{consumption_digest[:20]}-{index}.md"
        if not candidate.exists():
            return candidate
    raise RuntimeError("could not allocate companion-selection consumption audit path")


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    consumption_digest: str,
    target_path: str,
    selected_runtime_id: str | None,
    previous_runtime_id: str | None,
    operator_id: str,
) -> str:
    path = _next_audit_path(vault, consumption_digest)
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
            "# Phase 11 Companion Selection Approval Consumption Executor",
            "",
            f"operator_id: {operator_id}",
            f"approval_id: {approval_id}",
            f"execution_id: {execution_id}",
            f"consumption_digest: {consumption_digest}",
            f"target_path: {target_path}",
            f"selected_runtime_id: {selected_runtime_id or 'missing'}",
            f"previous_runtime_id: {previous_runtime_id or 'missing'}",
            "approval_consumed: true",
            "approval_status_mutated: true",
            "exact_once_marker_written: true",
            "companion_selection_written: true",
            "runtime_control_performed: false",
            "provider_call_performed: false",
            "agent_bus_task_written: false",
            "canonical_mutation_performed: false",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return _rel(vault, path)


def execute_phase11_chat_companion_selection_approval_consumption(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    message: str | None = None,
    expected_consumption_digest: str | None = None,
    operator_id: str = "operator",
    operator_approval_statement: str | None = None,
) -> dict[str, Any]:
    """Consume one companion-selection approval and write the selection target."""

    vault = Path(vault_root).resolve()
    requested_approval_id = str(approval_id or "").strip()
    expected = str(expected_consumption_digest or "").strip()
    operator = str(operator_id or "operator").strip() or "operator"
    approval_statement = " ".join(str(operator_approval_statement or "").strip().split())
    readiness = build_phase11_chat_companion_selection_approval_consumption_readiness(
        vault,
        approval_id=requested_approval_id or None,
        message=message,
    )
    digest = readiness.get("digest_proof") or {}
    consumption_digest = str(digest.get("consumption_digest") or "")
    selected_approval_id = str((readiness.get("summary") or {}).get("selected_approval_id") or "")
    effective_approval_id = requested_approval_id or selected_approval_id
    blockers = list(readiness.get("blocked_reasons") or [])

    if not effective_approval_id:
        blockers.append("approval_id_required_for_consumption_executor")
    if not expected:
        blockers.append("expected_consumption_digest_required")
    elif expected != consumption_digest:
        blockers.append("consumption_digest_mismatch")

    if "operator_decision_not_approved" in blockers and approval_statement:
        blockers = [item for item in blockers if item != "operator_decision_not_approved"]

    if "future_exact_once_marker_already_present" in blockers:
        blockers.append("exact_once_marker_already_present")

    service = StudioService(vault)
    req = service.get_approval(effective_approval_id) if effective_approval_id else None
    if req is None:
        blockers.append("approval_request_not_loadable")
    else:
        if req.status == "pending" and not approval_statement:
            blockers.append("operator_decision_not_approved")
        elif req.status not in {"pending", "approved"}:
            blockers.append("approval_status_not_approved_or_pending_with_statement")
        if req.action_spec.action_type != "chat_companion_selection_change":
            blockers.append("approval_action_type_not_companion_selection_change")
        if req.action_spec.target_path != SELECTION_TARGET_PATH:
            blockers.append("approval_target_path_not_companion_selection_target")
        content_payload, content_error = _load_content_payload(req)
        if content_error:
            blockers.append(content_error)
        elif not str((content_payload or {}).get("selected_runtime_id") or ""):
            blockers.append("selected_runtime_id_missing_from_approval_content")

    marker_path = vault / MARKER_DIR / f"{_safe_id(effective_approval_id) or 'unknown'}.json"
    if marker_path.exists() and "exact_once_marker_already_present" not in blockers:
        blockers.append("exact_once_marker_already_present")

    target_path = vault / SELECTION_TARGET_PATH
    if target_path.exists() and "future_companion_selection_target_collision" not in blockers:
        blockers.append("future_companion_selection_target_collision")

    hard_blockers = [
        item
        for item in blockers
        if item != "operator_decision_not_approved" or not approval_statement
    ]
    if hard_blockers:
        return _blocked_payload(
            vault=vault,
            readiness=readiness,
            approval_id=effective_approval_id,
            expected_consumption_digest=expected,
            blockers=hard_blockers,
        )

    assert req is not None
    content_payload, _ = _load_content_payload(req)
    content_payload = content_payload or {}
    execution_id = f"companion-selection-consumption-{consumption_digest[:20]}"
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
        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executing",
                    approval_id=effective_approval_id,
                    execution_id=execution_id,
                    consumption_digest=consumption_digest,
                    target_path=SELECTION_TARGET_PATH,
                    operator_id=operator,
                    target_write_performed=False,
                ),
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(str(req.action_spec.content or ""), encoding="utf-8")

        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executed",
                    approval_id=effective_approval_id,
                    execution_id=execution_id,
                    consumption_digest=consumption_digest,
                    target_path=SELECTION_TARGET_PATH,
                    operator_id=operator,
                    target_write_performed=True,
                ),
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
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
                "phase11_companion_selection_approval_consumption_executor": True,
                "phase11_companion_selection_consumption_digest": consumption_digest,
                "target_selection_write_performed": True,
                "approval_execution_called": True,
            }
        )
        req.action_spec.metadata = metadata
        _write_approval(service, req)

        audit_path = _write_audit(
            vault=vault,
            approval_id=effective_approval_id,
            execution_id=execution_id,
            consumption_digest=consumption_digest,
            target_path=SELECTION_TARGET_PATH,
            selected_runtime_id=content_payload.get("selected_runtime_id"),
            previous_runtime_id=content_payload.get("previous_runtime_id"),
            operator_id=operator,
        )
    except Exception as exc:
        error = str(exc)
        try:
            marker_path.parent.mkdir(parents=True, exist_ok=True)
            marker_path.write_text(
                json.dumps(
                    _marker_payload(
                        status="execution_failed",
                        approval_id=effective_approval_id,
                        execution_id=execution_id,
                        consumption_digest=consumption_digest,
                        target_path=SELECTION_TARGET_PATH,
                        operator_id=operator,
                        target_write_performed=target_path.exists(),
                        error=error,
                    ),
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
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
            readiness=readiness,
            approval_id=effective_approval_id,
            expected_consumption_digest=expected,
            blockers=[f"companion_selection_consumption_execution_failed:{error}"],
        )
        failed["status"] = "FAILED / APPROVAL-CONSUMPTION / PARTIAL EXECUTION CHECK REQUIRED"
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
            readiness=readiness,
            approval_id=effective_approval_id,
            expected_consumption_digest=expected,
            operator_approval_recorded=approval_recorded_from_statement,
            approval_status="executed",
            approval_consumed=True,
            approval_status_mutated=True,
            exact_once_marker_written=True,
            companion_selection_written=True,
            target_write_performed=True,
            blocker_count=0,
        ),
        "readiness_contract": readiness,
        "digest_proof": {
            "expected_consumption_digest": expected,
            "consumption_digest": consumption_digest,
            "consumption_digest_matched": True,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "approval_id": effective_approval_id,
                        "execution_id": execution_id,
                        "consumption_digest": consumption_digest,
                        "target_path": SELECTION_TARGET_PATH,
                    }
                )
            ),
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path),
            "marker_written": True,
            "marker_status": "executed",
            "duplicate_blocked_before_target_write": True,
        },
        "target_write": {
            "target_path": SELECTION_TARGET_PATH,
            "target_write_performed": True,
            "target_content_sha256": _sha256_text(str(req.action_spec.content or "")),
            "selected_runtime_id": content_payload.get("selected_runtime_id"),
            "previous_runtime_id": content_payload.get("previous_runtime_id"),
        },
        "execution_record": {
            "execution_id": execution_id,
            "execution_status": "completed",
            "approval_status": "executed",
        },
        "audit_record": {
            "audit_written": True,
            "audit_record_path": audit_path,
        },
        "authority": _authority(),
        "blocked_reasons": [],
    }


def format_phase11_chat_companion_selection_approval_consumption_executor(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    marker = payload.get("exact_once_marker") or {}
    target = payload.get("target_write") or {}
    lines = [
        "Phase 11 Chat Companion Selection Approval Consumption Executor",
        f"Status: {payload.get('status')}",
        f"Approval id: {summary.get('approval_id') or 'none'}",
        f"Approval consumed: {summary.get('approval_consumed')}",
        f"Consumption digest: {digest.get('consumption_digest') or 'missing'}",
        f"Marker written: {summary.get('exact_once_marker_written')}",
        f"Target path: {target.get('target_path') or SELECTION_TARGET_PATH}",
        f"Companion selection written: {summary.get('companion_selection_written')}",
        f"Selected runtime: {target.get('selected_runtime_id') or summary.get('selected_runtime_id') or 'missing'}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    lines.append(
        "Boundary: companion-selection approval consumption only; no provider call, "
        "runtime dispatch/control, identity/profile/role-card mutation, Agent Bus task "
        "write, or canonical writeback."
    )
    if marker.get("marker_path"):
        lines.append(f"Marker path: {marker.get('marker_path')}")
    return "\n".join(lines)
