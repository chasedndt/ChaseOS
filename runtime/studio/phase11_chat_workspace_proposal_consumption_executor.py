"""Phase 11 Chat workspace proposal consumption executor.

This governed executor consumes one digest-bound Studio Chat workspace proposal
approval and writes the native workspace-proposal JSON record exactly once. It
does not create Chat workspaces, folders, threads, Discord threads, messages,
Agent Bus tasks, runtime board items, schedules, provider calls, or canonical
state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.studio.phase11_chat_workspace_proposal_writer import (
    METADATA_BLOCK_KEY,
    PROPOSAL_KINDS,
    PROPOSAL_ROOT,
    SURFACE_ID as WRITER_SURFACE_ID,
)
from runtime.studio.service import ApprovalRequest, StudioService


MODEL_VERSION = "studio.phase11_chat_workspace_proposal_consumption_executor.v1"
SURFACE_ID = "phase11_chat_workspace_proposal_consumption_executor"
PASS_ID = "studio-runtime-chat-workspace-proposal-consumption-executor"
STATUS = "COMPLETE / APPROVAL-CONSUMED / VERIFIED / WORKSPACE PROPOSAL WRITTEN"
NEXT_RECOMMENDED_PASS = "studio-runtime-chat-workspace-target-state-executor"
MARKER_DIR = Path("runtime/studio/approvals/_chat_workspace_proposal_consumption_markers")
AUDIT_DIR = Path("07_LOGS") / "Agent-Activity"


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


def _authority() -> dict[str, bool]:
    return {
        "approval_consumption_allowed": True,
        "approval_status_mutation_allowed": True,
        "exact_once_marker_write_allowed": True,
        "target_workspace_proposal_write_allowed": True,
        "chat_workspace_create_allowed": False,
        "chat_folder_create_allowed": False,
        "chat_thread_create_allowed": False,
        "chat_message_send_allowed": False,
        "discord_api_calls_allowed": False,
        "discord_thread_create_allowed": False,
        "agent_bus_task_write_allowed": False,
        "runtime_board_write_allowed": False,
        "schedule_mutation_allowed": False,
        "provider_calls_allowed": False,
        "credential_values_visible": False,
        "canonical_mutation_allowed": False,
    }


def _effect_flags() -> dict[str, bool]:
    return {
        "chat_workspace_created": False,
        "chat_folder_created": False,
        "chat_thread_created": False,
        "chat_message_sent": False,
        "discord_api_called": False,
        "discord_thread_created": False,
        "agent_bus_task_written": False,
        "runtime_board_written": False,
        "schedule_mutated": False,
        "provider_call_performed": False,
        "credential_value_read": False,
        "canonical_mutation_performed": False,
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
    service._write_approval_record(req)  # type: ignore[attr-defined]  # Reuse Studio's durable queue writer.


def _workspace_proposal_target(vault: Path, target_path: str) -> tuple[Path | None, list[str]]:
    blockers: list[str] = []
    normalized = str(target_path or "").replace("\\", "/").strip()
    if not normalized:
        blockers.append("approval_target_path_required")
        return None, blockers
    if not normalized.startswith(f"{PROPOSAL_ROOT}/"):
        blockers.append("approval_target_path_not_workspace_proposal_root")
    if not normalized.endswith(".json"):
        blockers.append("approval_target_path_not_json")
    target_abs = (vault / normalized).resolve()
    proposal_root_abs = (vault / PROPOSAL_ROOT).resolve()
    try:
        target_abs.relative_to(vault.resolve())
    except ValueError:
        blockers.append("approval_target_path_escapes_vault")
    try:
        target_abs.relative_to(proposal_root_abs)
    except ValueError:
        blockers.append("approval_target_path_escapes_workspace_proposal_root")
    return target_abs, blockers


def _content_blockers(
    *,
    req: ApprovalRequest,
    payload: dict[str, Any] | None,
    expected_proposal_digest: str,
) -> list[str]:
    blockers: list[str] = []
    metadata = req.action_spec.metadata or {}
    content = payload or {}
    proposal_digest = str(content.get("proposal_digest") or "")
    metadata_digest = str(metadata.get("phase11_chat_workspace_proposal_digest") or "")
    target_path = str(req.action_spec.target_path or "").replace("\\", "/")
    content_target = str(content.get("target_path") or "").replace("\\", "/")
    proposal_kind = str(content.get("proposal_kind") or "")

    if req.action_spec.action_type != "create_file":
        blockers.append("approval_action_type_not_workspace_proposal_create_file")
    if metadata.get("phase11_chat_workspace_proposal_writer") is not True:
        blockers.append("approval_not_workspace_proposal_writer_artifact")
    if metadata.get(METADATA_BLOCK_KEY) is not True:
        blockers.append("approval_missing_workspace_proposal_execution_block")
    if metadata.get("source_surface") != WRITER_SURFACE_ID:
        blockers.append("approval_source_surface_not_workspace_proposal_writer")
    if proposal_kind not in PROPOSAL_KINDS:
        blockers.append("approval_content_proposal_kind_unsupported")
    if not proposal_digest:
        blockers.append("approval_content_proposal_digest_missing")
    if metadata_digest and proposal_digest and metadata_digest != proposal_digest:
        blockers.append("approval_metadata_content_digest_mismatch")
    if expected_proposal_digest and proposal_digest and expected_proposal_digest != proposal_digest:
        blockers.append("proposal_digest_mismatch")
    if target_path != content_target:
        blockers.append("approval_target_path_content_mismatch")
    for key, expected in _effect_flags().items():
        if key in content and bool(content.get(key)) is not expected:
            blockers.append(f"approval_content_effect_flag_not_false:{key}")
    if content.get("approval_required_before_effect") is not True:
        blockers.append("approval_content_missing_required_before_effect")
    return blockers


def _consumption_digest_material(
    *,
    approval_id: str,
    proposal_digest: str,
    target_path: str,
    approved_content_sha256: str,
) -> dict[str, Any]:
    return {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "approval_id": approval_id,
        "proposal_digest": proposal_digest,
        "target_path": target_path,
        "approved_content_sha256": approved_content_sha256,
    }


def _summary(
    *,
    approval_id: str,
    proposal_payload: dict[str, Any] | None = None,
    expected_proposal_digest: str = "",
    proposal_digest: str = "",
    approval_status: str | None = None,
    operator_approval_recorded: bool = False,
    approval_consumed: bool = False,
    approval_status_mutated: bool = False,
    exact_once_marker_written: bool = False,
    target_workspace_proposal_written: bool = False,
    duplicate_blocked_before_target_write: bool = False,
    blocker_count: int = 0,
) -> dict[str, Any]:
    proposal = proposal_payload or {}
    return {
        "approval_id": approval_id or None,
        "approval_status": approval_status,
        "operator_approval_recorded_from_statement": operator_approval_recorded,
        "expected_proposal_digest_provided": bool(expected_proposal_digest),
        "proposal_digest": proposal_digest or proposal.get("proposal_digest"),
        "proposal_kind": proposal.get("proposal_kind"),
        "proposal_id": proposal.get("proposal_id"),
        "workspace_id": proposal.get("workspace_id"),
        "folder_id": proposal.get("folder_id"),
        "thread_id": proposal.get("thread_id"),
        "runtime_id": proposal.get("runtime_id"),
        "target_path": proposal.get("target_path"),
        "approval_consumed": approval_consumed,
        "approval_status_mutated": approval_status_mutated,
        "exact_once_marker_written": exact_once_marker_written,
        "target_workspace_proposal_written": target_workspace_proposal_written,
        "duplicate_blocked_before_target_write": duplicate_blocked_before_target_write,
        "chat_workspace_created": False,
        "chat_folder_created": False,
        "chat_thread_created": False,
        "chat_message_sent": False,
        "discord_api_called": False,
        "discord_thread_created": False,
        "agent_bus_task_written": False,
        "runtime_board_written": False,
        "schedule_mutated": False,
        "provider_call_performed": False,
        "credential_value_read": False,
        "canonical_mutation_performed": False,
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        "blocker_count": blocker_count,
    }


def _blocked_payload(
    *,
    vault: Path,
    approval_id: str,
    expected_proposal_digest: str,
    proposal_payload: dict[str, Any] | None,
    proposal_digest: str,
    target_path: str,
    marker_path: Path | None,
    blockers: list[str],
) -> dict[str, Any]:
    unique_blockers = list(dict.fromkeys(blockers))
    return {
        "ok": False,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": "BLOCKED / APPROVAL-CONSUMPTION / NO WORKSPACE PROPOSAL WRITE",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": False,
        "approval_gated": True,
        "summary": _summary(
            approval_id=approval_id,
            proposal_payload=proposal_payload,
            expected_proposal_digest=expected_proposal_digest,
            proposal_digest=proposal_digest,
            target_workspace_proposal_written=False,
            duplicate_blocked_before_target_write="exact_once_marker_already_present" in unique_blockers,
            blocker_count=len(unique_blockers),
        ),
        "digest_proof": {
            "expected_proposal_digest": expected_proposal_digest or None,
            "proposal_digest": proposal_digest or None,
            "proposal_digest_matched": False,
            "consumption_digest": None,
        },
        "exact_once_marker": {
            "marker_path": _rel(vault, marker_path) if marker_path else None,
            "marker_written": False,
            "duplicate_blocked_before_target_write": "exact_once_marker_already_present" in unique_blockers,
        },
        "target_write": {
            "target_path": target_path or None,
            "target_workspace_proposal_written": False,
            "target_file_written": False,
            **_effect_flags(),
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


def _marker_payload(
    *,
    status: str,
    approval_id: str,
    execution_id: str,
    proposal_digest: str,
    consumption_digest: str,
    target_path: str,
    operator_id: str,
    target_workspace_proposal_written: bool,
    error: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "phase11_chat_workspace_proposal_consumption_marker.v1",
        "status": status,
        "approval_id": approval_id,
        "execution_id": execution_id,
        "pass": PASS_ID,
        "surface": SURFACE_ID,
        "proposal_digest": proposal_digest,
        "consumption_digest": consumption_digest,
        "target_path": target_path,
        "operator_id": operator_id,
        "target_workspace_proposal_written": target_workspace_proposal_written,
        **_effect_flags(),
        "error": error,
        "updated_at_utc": _now_utc(),
    }


def _target_payload(
    *,
    proposal_payload: dict[str, Any],
    approval_id: str,
    execution_id: str,
    consumption_digest: str,
    operator_id: str,
) -> dict[str, Any]:
    payload = dict(proposal_payload)
    payload.update(
        {
            "status": "approved_proposal_recorded",
            "approval_id": approval_id,
            "approval_consumed": True,
            "approval_consumed_by": SURFACE_ID,
            "approval_consumption_execution_id": execution_id,
            "approval_consumption_digest": consumption_digest,
            "approved_by": operator_id,
            "approved_at_utc": _now_utc(),
            "target_state_executor_required": True,
            "next_required_pass": NEXT_RECOMMENDED_PASS,
            **_effect_flags(),
        }
    )
    payload["approval_required_before_effect"] = True
    return payload


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
    raise RuntimeError("could not allocate workspace proposal consumption audit path")


def _write_audit(
    *,
    vault: Path,
    approval_id: str,
    execution_id: str,
    proposal_digest: str,
    consumption_digest: str,
    target_path: str,
    proposal_payload: dict[str, Any],
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
            "# Phase 11 Chat Workspace Proposal Consumption Executor",
            "",
            f"operator_id: {operator_id}",
            f"approval_id: {approval_id}",
            f"execution_id: {execution_id}",
            f"proposal_digest: {proposal_digest}",
            f"consumption_digest: {consumption_digest}",
            f"target_path: {target_path}",
            f"proposal_id: {proposal_payload.get('proposal_id') or 'missing'}",
            f"proposal_kind: {proposal_payload.get('proposal_kind') or 'missing'}",
            f"workspace_id: {proposal_payload.get('workspace_id') or 'missing'}",
            f"folder_id: {proposal_payload.get('folder_id') or 'missing'}",
            f"thread_id: {proposal_payload.get('thread_id') or 'missing'}",
            f"runtime_id: {proposal_payload.get('runtime_id') or 'missing'}",
            "approval_consumed: true",
            "approval_status_mutated: true",
            "exact_once_marker_written: true",
            "target_workspace_proposal_written: true",
            "chat_workspace_created: false",
            "chat_folder_created: false",
            "chat_thread_created: false",
            "chat_message_sent: false",
            "discord_api_called: false",
            "discord_thread_created: false",
            "agent_bus_task_written: false",
            "runtime_board_written: false",
            "schedule_mutated: false",
            "provider_call_performed: false",
            "credential_value_read: false",
            "canonical_mutation_performed: false",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")
    return _rel(vault, path)


def execute_phase11_chat_workspace_proposal_consumption(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    expected_proposal_digest: str | None = None,
    operator_id: str = "operator",
    operator_approval_statement: str | None = None,
) -> dict[str, Any]:
    """Consume one approved workspace proposal artifact and write its JSON record."""

    vault = Path(vault_root).resolve()
    requested_approval_id = str(approval_id or "").strip()
    expected = str(expected_proposal_digest or "").strip()
    operator = str(operator_id or "operator").strip() or "operator"
    approval_statement = " ".join(str(operator_approval_statement or "").strip().split())
    service = StudioService(vault)
    blockers: list[str] = []
    proposal_payload: dict[str, Any] | None = None
    proposal_digest = ""
    target_path = ""

    if not requested_approval_id:
        blockers.append("approval_id_required_for_workspace_proposal_consumption")
    if not expected:
        blockers.append("expected_proposal_digest_required")

    req = service.get_approval(requested_approval_id) if requested_approval_id else None
    if req is None:
        blockers.append("approval_request_not_loadable")
    else:
        target_path = str(req.action_spec.target_path or "").replace("\\", "/")
        if req.status == "pending" and not approval_statement:
            blockers.append("operator_decision_not_approved")
        elif req.status not in {"pending", "approved"}:
            blockers.append("approval_status_not_approved_or_pending_with_statement")
        proposal_payload, content_error = _load_content_payload(req)
        if content_error:
            blockers.append(content_error)
        else:
            proposal_digest = str((proposal_payload or {}).get("proposal_digest") or "")
            blockers.extend(
                _content_blockers(
                    req=req,
                    payload=proposal_payload,
                    expected_proposal_digest=expected,
                )
            )

    target_abs, target_blockers = _workspace_proposal_target(vault, target_path)
    blockers.extend(target_blockers)
    marker_path = vault / MARKER_DIR / f"{_safe_id(requested_approval_id)}.json"

    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")
    if target_abs is not None and target_abs.exists():
        blockers.append("workspace_proposal_target_collision")

    hard_blockers = [
        item
        for item in blockers
        if item != "operator_decision_not_approved" or not approval_statement
    ]
    if hard_blockers:
        return _blocked_payload(
            vault=vault,
            approval_id=requested_approval_id,
            expected_proposal_digest=expected,
            proposal_payload=proposal_payload,
            proposal_digest=proposal_digest,
            target_path=target_path,
            marker_path=marker_path,
            blockers=hard_blockers,
        )

    assert req is not None
    assert proposal_payload is not None
    assert target_abs is not None

    approved_content = str(req.action_spec.content or "")
    approved_content_sha256 = _sha256_text(approved_content)
    consumption_material = _consumption_digest_material(
        approval_id=requested_approval_id,
        proposal_digest=proposal_digest,
        target_path=target_path,
        approved_content_sha256=approved_content_sha256,
    )
    consumption_digest = _sha256_text(_canonical_json(consumption_material))
    execution_id = f"chat-workspace-proposal-consumption-{consumption_digest[:20]}"
    approval_recorded_from_statement = False

    try:
        if req.status == "pending" and approval_statement:
            req.status = "approved"
            req.reviewed_by = operator
            req.reason = approval_statement
            req.updated_at = _now_utc()
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
                    approval_id=requested_approval_id,
                    execution_id=execution_id,
                    proposal_digest=proposal_digest,
                    consumption_digest=consumption_digest,
                    target_path=target_path,
                    operator_id=operator,
                    target_workspace_proposal_written=False,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        written_payload = _target_payload(
            proposal_payload=proposal_payload,
            approval_id=requested_approval_id,
            execution_id=execution_id,
            consumption_digest=consumption_digest,
            operator_id=operator,
        )
        target_content = json.dumps(written_payload, indent=2, sort_keys=True) + "\n"
        target_abs.parent.mkdir(parents=True, exist_ok=True)
        target_abs.write_text(target_content, encoding="utf-8")

        marker_path.write_text(
            json.dumps(
                _marker_payload(
                    status="executed",
                    approval_id=requested_approval_id,
                    execution_id=execution_id,
                    proposal_digest=proposal_digest,
                    consumption_digest=consumption_digest,
                    target_path=target_path,
                    operator_id=operator,
                    target_workspace_proposal_written=True,
                ),
                indent=2,
                sort_keys=True,
            )
            + "\n",
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
                "phase11_chat_workspace_proposal_consumption_executor": True,
                "phase11_chat_workspace_proposal_consumption_digest": consumption_digest,
                "target_workspace_proposal_write_performed": True,
                "approval_consumed": True,
                **_effect_flags(),
            }
        )
        req.action_spec.metadata = metadata
        _write_approval(service, req)

        audit_path = _write_audit(
            vault=vault,
            approval_id=requested_approval_id,
            execution_id=execution_id,
            proposal_digest=proposal_digest,
            consumption_digest=consumption_digest,
            target_path=target_path,
            proposal_payload=proposal_payload,
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
                        approval_id=requested_approval_id,
                        execution_id=execution_id,
                        proposal_digest=proposal_digest,
                        consumption_digest=consumption_digest,
                        target_path=target_path,
                        operator_id=operator,
                        target_workspace_proposal_written=target_abs.exists(),
                        error=error,
                    ),
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
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
            approval_id=requested_approval_id,
            expected_proposal_digest=expected,
            proposal_payload=proposal_payload,
            proposal_digest=proposal_digest,
            target_path=target_path,
            marker_path=marker_path,
            blockers=[f"workspace_proposal_consumption_execution_failed:{error}"],
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
            approval_id=requested_approval_id,
            proposal_payload=written_payload,
            expected_proposal_digest=expected,
            proposal_digest=proposal_digest,
            approval_status="executed",
            operator_approval_recorded=approval_recorded_from_statement,
            approval_consumed=True,
            approval_status_mutated=True,
            exact_once_marker_written=True,
            target_workspace_proposal_written=True,
            blocker_count=0,
        ),
        "digest_proof": {
            "expected_proposal_digest": expected,
            "proposal_digest": proposal_digest,
            "proposal_digest_matched": expected == proposal_digest,
            "approved_content_sha256": approved_content_sha256,
            "consumption_digest": consumption_digest,
            "consumption_digest_material": consumption_material,
            "result_digest": _sha256_text(
                _canonical_json(
                    {
                        "approval_id": requested_approval_id,
                        "execution_id": execution_id,
                        "proposal_digest": proposal_digest,
                        "target_path": target_path,
                        "target_content_sha256": _sha256_text(target_content),
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
            "target_path": target_path,
            "target_file_written": True,
            "target_workspace_proposal_written": True,
            "target_content_sha256": _sha256_text(target_content),
            "proposal_id": written_payload.get("proposal_id"),
            "proposal_kind": written_payload.get("proposal_kind"),
            "workspace_id": written_payload.get("workspace_id"),
            "folder_id": written_payload.get("folder_id"),
            "thread_id": written_payload.get("thread_id"),
            "runtime_id": written_payload.get("runtime_id"),
            **_effect_flags(),
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


def format_phase11_chat_workspace_proposal_consumption_executor(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    digest = payload.get("digest_proof") or {}
    marker = payload.get("exact_once_marker") or {}
    target = payload.get("target_write") or {}
    lines = [
        "Phase 11 Chat Workspace Proposal Consumption Executor",
        f"Status: {payload.get('status')}",
        f"Approval id: {summary.get('approval_id') or 'none'}",
        f"Approval consumed: {summary.get('approval_consumed')}",
        f"Proposal digest: {digest.get('proposal_digest') or 'missing'}",
        f"Consumption digest: {digest.get('consumption_digest') or 'missing'}",
        f"Marker written: {summary.get('exact_once_marker_written')}",
        f"Target path: {target.get('target_path') or summary.get('target_path') or 'missing'}",
        f"Workspace proposal written: {summary.get('target_workspace_proposal_written')}",
        f"Proposal kind: {target.get('proposal_kind') or summary.get('proposal_kind') or 'missing'}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    lines.append(
        "Boundary: workspace-proposal approval consumption only; no Chat state "
        "creation, message send, Discord API call/thread creation, Agent Bus task "
        "write, runtime board/schedule mutation, provider call, credential read, "
        "or canonical writeback."
    )
    if marker.get("marker_path"):
        lines.append(f"Marker path: {marker.get('marker_path')}")
    return "\n".join(lines)
