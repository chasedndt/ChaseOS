"""
runtime.chaser.board

Read-only orchestration board contracts for ChaserAgent.

The board is a proposal/evidence surface. It is not a task runner, memory owner,
approval consumer, terminal executor, provider caller, or Agent Bus writer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.policies import (
    CHASER_RUNTIME_ID,
    assert_no_authority_change,
    validate_result_shape,
)


APPROVAL_STATES = ("not_requested", "required", "approved", "blocked")
BOARD_ID = "chaseos_chaser_board"
BOARD_SURFACE = "chaser_orchestration_board"

BOARD_AUTHORITY = {
    "read_only": True,
    "proposal_packets": True,
    "terminal_execution": False,
    "studio_execution": False,
    "provider_calls": False,
    "agent_bus_writes": False,
    "approval_queue_writes": False,
    "approval_consumption": False,
    "canonical_writeback": False,
    "external_upload": False,
    "host_mutation": False,
    "profile_activation": False,
    "toolset_activation": False,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: Any) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BoardCard:
    task_id: str
    origin: str
    operator_intent: str
    target_workspace: str = ""
    target_session: str = ""
    proposed_runtime: str = CHASER_RUNTIME_ID
    proposed_profile: str = "default"
    proposed_toolset: str = "none"
    required_authority: tuple[str, ...] = ()
    approval_state: str = "not_requested"
    result_shape: str = "proposal"
    evidence_links: tuple[str, ...] = ()
    artifact_links: tuple[str, ...] = ()
    session_links: tuple[str, ...] = ()
    audit_links: tuple[str, ...] = ()
    blocked_reasons: tuple[str, ...] = ()
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "origin": self.origin,
            "operator_intent": self.operator_intent,
            "target_workspace": self.target_workspace,
            "target_session": self.target_session,
            "proposed_runtime": self.proposed_runtime,
            "proposed_profile": self.proposed_profile,
            "proposed_toolset": self.proposed_toolset,
            "required_authority": list(self.required_authority),
            "approval_state": self.approval_state,
            "result_shape": self.result_shape,
            "evidence_links": list(self.evidence_links),
            "artifact_links": list(self.artifact_links),
            "session_links": list(self.session_links),
            "audit_links": list(self.audit_links),
            "blocked_reasons": list(self.blocked_reasons),
            "created_at": self.created_at,
        }


def create_board_card(
    *,
    operator_intent: str,
    origin: str = "operator",
    target_workspace: str = "",
    target_session: str = "",
    proposed_runtime: str = CHASER_RUNTIME_ID,
    proposed_profile: str = "default",
    proposed_toolset: str = "none",
    required_authority: tuple[str, ...] | list[str] = (),
    approval_state: str = "not_requested",
    result_shape: str = "proposal",
    evidence_links: tuple[str, ...] | list[str] = (),
    artifact_links: tuple[str, ...] | list[str] = (),
    session_links: tuple[str, ...] | list[str] = (),
    audit_links: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Build a deterministic in-memory board card."""

    intent = str(operator_intent or "").strip()
    if not intent:
        intent = "unspecified operator intent"
    material = {
        "origin": origin,
        "operator_intent": intent,
        "target_workspace": target_workspace,
        "target_session": target_session,
        "proposed_runtime": proposed_runtime,
        "proposed_profile": proposed_profile,
        "proposed_toolset": proposed_toolset,
        "result_shape": result_shape,
    }
    card = BoardCard(
        task_id=f"chaser-{_digest(material)[:16]}",
        origin=str(origin or "operator"),
        operator_intent=intent,
        target_workspace=str(target_workspace or ""),
        target_session=str(target_session or ""),
        proposed_runtime=str(proposed_runtime or CHASER_RUNTIME_ID),
        proposed_profile=str(proposed_profile or "default"),
        proposed_toolset=str(proposed_toolset or "none"),
        required_authority=tuple(str(item) for item in required_authority),
        approval_state=str(approval_state or "not_requested"),
        result_shape=str(result_shape or "proposal").lower(),
        evidence_links=tuple(str(item) for item in evidence_links),
        artifact_links=tuple(str(item) for item in artifact_links),
        session_links=tuple(str(item) for item in session_links),
        audit_links=tuple(str(item) for item in audit_links),
    )
    payload = card.to_dict()
    validation = validate_board_card(payload)
    payload["valid"] = validation["ok"]
    payload["validation"] = validation
    return payload


def validate_board_card(card: dict[str, Any]) -> dict[str, Any]:
    """Validate board-card shape and no-authority posture."""

    errors: list[str] = []
    if not isinstance(card, dict):
        return {"ok": False, "errors": ["board_card_not_object"], "authority": assert_no_authority_change()}

    for field_name in ("task_id", "origin", "operator_intent", "proposed_runtime", "approval_state", "result_shape"):
        if not str(card.get(field_name) or "").strip():
            errors.append(f"missing_required_field:{field_name}")

    shape = validate_result_shape(str(card.get("result_shape") or ""))
    if not shape["ok"]:
        errors.extend(shape["blocked_reasons"])

    if str(card.get("approval_state") or "") not in APPROVAL_STATES:
        errors.append("invalid_approval_state")

    authority = assert_no_authority_change(card.get("authority") if isinstance(card.get("authority"), dict) else None)
    errors.extend(authority["blocked_reasons"])

    return {
        "ok": not errors,
        "errors": errors,
        "authority": authority,
        "result_shape": shape,
    }


def board_authority() -> dict[str, bool]:
    """Return the board authority ceiling for API/CLI surfaces."""

    return dict(BOARD_AUTHORITY)


def _rel(root: Path, path: str | Path | None) -> str:
    if path in (None, ""):
        return ""
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def _proposal_cwd(vault_root: Path, cwd: str | Path | None) -> tuple[Path, list[str]]:
    requested = Path(cwd).resolve() if cwd else vault_root.resolve()
    try:
        requested.relative_to(vault_root.resolve())
    except ValueError:
        return requested, [f"cwd_outside_vault:{requested}"]
    return requested, []


def _terminal_proposal_status(classification: dict[str, Any], cwd_errors: list[str]) -> tuple[str, list[str]]:
    if cwd_errors:
        return "blocked", cwd_errors

    action_class = str(classification.get("action_class") or "unknown_command")
    reason = str(classification.get("reason") or "")
    if action_class == "read_only_command":
        return "preview_allowed", []
    if action_class == "write_command":
        return "approval_required_future_n6", ["write_capable_terminal_lane_requires_n6_approval"]
    if action_class in {"destructive_command", "elevated_command", "network_command", "blocked_shell_control_command"}:
        return "blocked", [reason or action_class]
    return "blocked", [reason or action_class]


def _terminal_card_actions(command: str) -> list[dict[str, Any]]:
    return [{
        "label": "Preview classification",
        "action_type": "terminal_command",
        "proposal_only": True,
        "command": command,
        "executes_now": False,
        "writes_now": False,
        "approval_queue_write_now": False,
    }] if command else []


def build_action_proposal(
    vault_root: str | Path,
    *,
    action_type: str,
    command: str = "",
    cwd: str | Path | None = None,
    card_id: str = "",
    actor: str = "operator",
) -> dict[str, Any]:
    """Build a read-only board action proposal packet.

    Proposal packets are policy/readiness previews only. This helper does not
    execute terminal commands, write approval requests, consume approvals,
    create Agent Bus tasks, or mutate canonical state.
    """

    root = Path(vault_root).resolve()
    normalized_action = str(action_type or "").strip().lower().replace("_", "-")
    if normalized_action in {"terminal", "terminal-command", "terminal-preview", "preview-command"}:
        normalized_action = "terminal_command"

    if normalized_action != "terminal_command":
        proposal_id = f"board-proposal-{_digest({'action_type': normalized_action, 'card_id': card_id})[:16]}"
        return {
            "ok": False,
            "surface": BOARD_SURFACE,
            "proposal_id": proposal_id,
            "action_type": normalized_action or "unknown",
            "status": "blocked",
            "blocked_reasons": ["unsupported_board_action"],
            "authority_summary": board_authority(),
            "executes_now": False,
            "writes_now": False,
            "approval_queue_write_now": False,
            "approval_consumption_now": False,
            "agent_bus_write_now": False,
            "provider_call_now": False,
            "canonical_writeback_now": False,
        }

    from runtime.operator_surface.adapters.terminal_adapter import TerminalAdapter

    command_text = str(command or "").strip()
    classification = TerminalAdapter.classify_command(command_text)
    resolved_cwd, cwd_errors = _proposal_cwd(root, cwd)
    status, blocked_reasons = _terminal_proposal_status(classification, cwd_errors)
    proposal_material = {
        "action_type": normalized_action,
        "command": command_text,
        "cwd": str(resolved_cwd),
        "card_id": card_id,
        "classification": classification,
    }
    action_class = str(classification.get("action_class") or "")
    approval_required = status == "approval_required_future_n6"
    preview_allowed = status in {"preview_allowed", "approval_required_future_n6"}

    return {
        "ok": status != "blocked",
        "surface": BOARD_SURFACE,
        "proposal_id": f"board-proposal-{_digest(proposal_material)[:16]}",
        "board_id": BOARD_ID,
        "action_type": normalized_action,
        "card_id": str(card_id or ""),
        "actor": str(actor or "operator"),
        "created_at": _now_iso(),
        "status": status,
        "command": command_text,
        "cwd": str(resolved_cwd),
        "classification": classification,
        "policy_decision": {
            "preview_allowed": preview_allowed,
            "terminal_execution_allowed_now": False,
            "board_executes_now": False,
            "approval_required": approval_required,
            "blocked": status == "blocked",
            "blocked_reasons": blocked_reasons,
            "current_terminal_adapter_class": action_class,
            "n6_write_lane_required": approval_required,
        },
        "routing": {
            "preview_route": "TerminalAdapter.classify_command",
            "current_execution_route": None,
            "future_execution_route": "N6 approval-gated terminal executor" if approval_required else (
                "chaseos operate terminal run (CLI/AOR only, not board execution)" if action_class == "read_only_command" else None
            ),
            "executor_owner": "runtime.operator_surface.terminal",
            "board_is_executor": False,
        },
        "blocked_reasons": blocked_reasons,
        "authority_summary": board_authority(),
        "executes_now": False,
        "writes_now": False,
        "approval_queue_write_now": False,
        "approval_consumption_now": False,
        "agent_bus_write_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "proposal_packet_only",
            "terminal_output_and_terminal_intent_are_not_instruction_trusted",
        ],
    }


def _terminal_write_approval_spec(proposal: dict[str, Any]) -> Any:
    from runtime.studio.service import ActionSpec

    proposal_id = str(proposal.get("proposal_id") or "")
    return ActionSpec(
        action_type="execute_process",
        target_path=f"07_LOGS/Terminal-Runs/_approval_requests/{proposal_id}.json",
        content=None,
        submitted_by="chaser-board",
        note="Request operator approval for the N6 terminal write-capable lane. This request does not execute.",
        metadata={
            "terminal_write_lane_approval_request": True,
            "terminal_write_executor_implemented": True,
            "terminal_write_executor_cli_available": True,
            "ambient_studio_execution_blocked": True,
            "proposal_id": proposal_id,
            "board_id": BOARD_ID,
            "surface": BOARD_SURFACE,
            "command": proposal.get("command") or "",
            "cwd": proposal.get("cwd") or "",
            "classification": proposal.get("classification") or {},
            "policy_decision": proposal.get("policy_decision") or {},
            "routing": proposal.get("routing") or {},
            "terminal_output_trusted": False,
            "trust_tier": "Tier 4",
            "authority": {
                "terminal_execution_now": False,
                "studio_execution_now": False,
                "approval_consumption_now": False,
                "agent_bus_write_now": False,
                "provider_call_now": False,
                "canonical_writeback_now": False,
            },
        },
    )


def _find_existing_terminal_write_approval(root: Path, proposal_id: str) -> dict[str, Any] | None:
    approval_dir = root / "runtime" / "studio" / "approvals"
    if not approval_dir.exists():
        return None
    for path in sorted(approval_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        spec = data.get("action_spec") if isinstance(data.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if (
            data.get("status") == "pending"
            and metadata.get("terminal_write_lane_approval_request") is True
            and metadata.get("proposal_id") == proposal_id
        ):
            return {
                "approval_id": data.get("approval_id") or path.stem,
                "approval_path": path.relative_to(root).as_posix(),
                "status": data.get("status") or "pending",
                "duplicate_of_existing_pending": True,
            }
    return None


def build_terminal_write_approval_request(
    vault_root: str | Path,
    *,
    command: str,
    cwd: str | Path | None = None,
    card_id: str = "",
    actor: str = "operator",
    expected_proposal_id: str = "",
    write_request: bool = False,
) -> dict[str, Any]:
    """Preview or write a pending approval request for an N6 terminal write.

    This helper never executes terminal commands and never consumes approvals.
    It can write one pending approval request only when ``write_request`` is
    true and the proposal is a write command classified as
    ``approval_required_future_n6``.
    """

    root = Path(vault_root).resolve()
    proposal = build_action_proposal(
        root,
        action_type="terminal_command",
        command=command,
        cwd=cwd,
        card_id=card_id,
        actor=actor,
    )
    proposal_id = str(proposal.get("proposal_id") or "")
    blocked_reasons: list[str] = []
    if expected_proposal_id and expected_proposal_id != proposal_id:
        blocked_reasons.append("proposal_id_mismatch")
    if proposal.get("status") != "approval_required_future_n6":
        blocked_reasons.append(f"proposal_not_eligible:{proposal.get('status') or 'unknown'}")

    eligible = not blocked_reasons
    result: dict[str, Any] = {
        "ok": eligible,
        "surface": BOARD_SURFACE,
        "request_type": "terminal_write_approval_request",
        "proposal": proposal,
        "proposal_id": proposal_id,
        "eligible": eligible,
        "status": "ready_for_approval_request" if eligible else "blocked",
        "blocked_reasons": blocked_reasons,
        "write_request_requested": bool(write_request),
        "approval_request_written": False,
        "approval_id": None,
        "approval_path": None,
        "duplicate_of_existing_pending": False,
        "executes_now": False,
        "writes_terminal_now": False,
        "approval_consumption_now": False,
        "agent_bus_write_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "approval_request_only",
            "n6_terminal_write_executor_requires_separate_approved_cli_execution",
            "ambient_studio_approval_execution_blocked",
        ],
    }
    if not eligible or not write_request:
        return result

    existing = _find_existing_terminal_write_approval(root, proposal_id)
    if existing:
        result.update(existing)
        result["approval_request_written"] = False
        result["status"] = "existing_pending_approval_request"
        return result

    from runtime.studio.service import StudioService

    req = StudioService(root).queue_for_approval(_terminal_write_approval_spec(proposal))
    result["approval_request_written"] = True
    result["approval_id"] = req.approval_id
    result["approval_path"] = f"runtime/studio/approvals/{req.approval_id}.json"
    result["status"] = "pending_approval_request_written"
    return result


def _source_status(source_id: str, status: str, *, count: int = 0, warning: str = "") -> dict[str, Any]:
    payload = {
        "source_id": source_id,
        "status": status,
        "count": count,
        "read_only": True,
        "writes_performed": False,
    }
    if warning:
        payload["warning"] = warning
    return payload


def _board_card(
    *,
    card_id: str,
    card_type: str,
    title: str,
    status: str,
    summary: str,
    source: str,
    evidence_paths: list[str] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "card_id": card_id,
        "type": card_type,
        "title": title,
        "status": status,
        "summary": summary,
        "source": source,
        "actions": _terminal_card_actions(str(data.get("command") or "")) if card_type == "terminal_run" and data else [],
        "actions_are_proposals_only": True,
        "executes_now": False,
        "writes_now": False,
        "evidence_paths": evidence_paths or [],
        "data": data or {},
        "trust_tier": "Tier 4" if card_type in {"terminal_run", "agent_task", "approval"} else "system_operational",
    }


def _append_terminal_cards(root: Path, cards: list[dict[str, Any]], sources: list[dict[str, Any]], warnings: list[str], limit: int) -> None:
    try:
        from runtime.operator_surface.terminal_runs import list_terminal_runs

        runs = list_terminal_runs(root, limit=limit)
        for run in runs:
            run_id = str(run.get("run_id") or "terminal-run")
            classification = run.get("classification") if isinstance(run.get("classification"), dict) else {}
            action_class = str(classification.get("action_class") or run.get("policy_decision") or "terminal_run")
            status = "executed" if run.get("allowed") else "blocked"
            if run.get("exit_code") not in (None, 0):
                status = "nonzero_exit"
            cards.append(_board_card(
                card_id=f"terminal-{run_id}",
                card_type="terminal_run",
                title=run_id,
                status=status,
                summary=f"{run.get('command') or '(no command)'} [{action_class}]",
                source="terminal_runs",
                evidence_paths=[_rel(root, p) for p in (run.get("audit_paths") or {}).values() if p],
                data={
                    "run_id": run_id,
                    "command": run.get("command") or "",
                    "cwd": run.get("cwd") or "",
                    "policy_decision": run.get("policy_decision") or "",
                    "exit_code": run.get("exit_code"),
                    "terminal_output_trusted": False,
                    "trust_state": run.get("trust_state") or "Tier 4",
                },
            ))
        sources.append(_source_status("terminal_runs", "ok", count=len(runs)))
    except Exception as exc:
        warnings.append(f"terminal_runs_unavailable:{exc}")
        sources.append(_source_status("terminal_runs", "unavailable", warning=str(exc)))


def _append_approval_cards(root: Path, cards: list[dict[str, Any]], sources: list[dict[str, Any]], warnings: list[str], limit: int) -> None:
    try:
        from runtime.studio.service import StudioService

        pending = StudioService(root).list_pending()[:limit]
        for req in pending:
            data = req.to_dict()
            spec = data.get("action_spec") if isinstance(data.get("action_spec"), dict) else {}
            target = spec.get("target_path") or spec.get("target_ref") or "(target hidden)"
            cards.append(_board_card(
                card_id=f"approval-{req.approval_id}",
                card_type="approval",
                title=req.approval_id,
                status=req.status,
                summary=f"{spec.get('action_type') or 'action'} -> {target}",
                source="studio_approvals",
                evidence_paths=[f"runtime/studio/approvals/{req.approval_id}.json"],
                data={
                    "approval_id": req.approval_id,
                    "status": req.status,
                    "action_type": spec.get("action_type") or "",
                    "target": target,
                    "submitted_at": req.submitted_at,
                    "updated_at": req.updated_at,
                },
            ))
        sources.append(_source_status("studio_approvals", "ok", count=len(pending)))
    except Exception as exc:
        warnings.append(f"studio_approvals_unavailable:{exc}")
        sources.append(_source_status("studio_approvals", "unavailable", warning=str(exc)))


def _bus_initialized(root: Path) -> bool:
    bus_dir = root / "runtime" / "agent_bus"
    return bus_dir.exists() and any(bus_dir.glob("*.sqlite"))


def _append_agent_bus_cards(root: Path, cards: list[dict[str, Any]], sources: list[dict[str, Any]], warnings: list[str], limit: int) -> None:
    if not _bus_initialized(root):
        sources.append(_source_status("agent_bus", "not_initialized", warning="no sqlite bus storage present; board did not initialize it"))
        return
    try:
        from runtime.agent_bus.bus import db_path, list_heartbeats, list_tasks

        tasks = list_tasks(root)
        active = [task for task in tasks if str(task.get("status") or "") in {"open", "claimed", "in_progress", "blocked", "review"}]
        for task in active[-limit:]:
            task_id = str(task.get("task_id") or "agent-task")
            cards.append(_board_card(
                card_id=f"task-{task_id}",
                card_type="agent_task",
                title=task_id,
                status=str(task.get("status") or "unknown"),
                summary=f"{task.get('sender') or '?'} -> {task.get('recipient') or '?'}: {task.get('intent') or 'TASK'}",
                source="agent_bus",
                evidence_paths=[_rel(root, db_path(root))],
                data={
                    "task_id": task_id,
                    "run_id": task.get("run_id") or "",
                    "sender": task.get("sender") or "",
                    "recipient": task.get("recipient") or "",
                    "status": task.get("status") or "",
                    "priority": task.get("priority") or "",
                    "owner": task.get("owner") or "",
                    "updated_at": task.get("updated_at") or task.get("created_at") or "",
                },
            ))
        heartbeats = list_heartbeats(root)
        for heartbeat in heartbeats[-limit:]:
            runtime = str(heartbeat.get("runtime") or heartbeat.get("bus_name") or "runtime")
            cards.append(_board_card(
                card_id=f"runtime-{runtime}-{_digest(heartbeat)[:10]}",
                card_type="runtime_health",
                title=runtime,
                status=str(heartbeat.get("status") or heartbeat.get("health") or "unknown"),
                summary=str(heartbeat.get("summary") or heartbeat.get("current_task_id") or "heartbeat recorded"),
                source="agent_bus_heartbeats",
                evidence_paths=[_rel(root, db_path(root))],
                data={
                    "runtime": runtime,
                    "runtime_instance_id": heartbeat.get("runtime_instance_id") or "",
                    "current_task_id": heartbeat.get("current_task_id") or "",
                    "last_seen": heartbeat.get("last_seen") or heartbeat.get("updated_at") or "",
                    "health": heartbeat.get("health") or "",
                },
            ))
        sources.append(_source_status("agent_bus", "ok", count=len(active) + len(heartbeats)))
    except Exception as exc:
        warnings.append(f"agent_bus_unavailable:{exc}")
        sources.append(_source_status("agent_bus", "unavailable", warning=str(exc)))


def _append_schedule_cards(root: Path, cards: list[dict[str, Any]], sources: list[dict[str, Any]], warnings: list[str], limit: int) -> None:
    try:
        from runtime.schedules.loader import list_schedules, validate_all_schedules

        validation_errors = validate_all_schedules(root)
        schedules = list_schedules(root, check_registry=False)
        for schedule in schedules[:limit]:
            cards.append(_board_card(
                card_id=f"schedule-{schedule.schedule_id}",
                card_type="schedule",
                title=schedule.schedule_id,
                status="enabled" if schedule.enabled else "disabled",
                summary=f"{schedule.schedule_kind}:{schedule.workflow_id or schedule.command_id or 'unknown'} -> {schedule.runtime_adapter_target}",
                source="schedules",
                evidence_paths=[_rel(root, schedule._source_path)],
                data={
                    "schedule_id": schedule.schedule_id,
                    "schedule_kind": schedule.schedule_kind,
                    "workflow_id": schedule.workflow_id,
                    "command_id": schedule.command_id,
                    "runtime_adapter_target": schedule.runtime_adapter_target,
                    "runtime_adapter_fallback": schedule.runtime_adapter_fallback,
                    "enabled": schedule.enabled,
                    "approval_policy": schedule.approval_policy,
                    "shadow_mode": schedule.shadow_mode,
                },
            ))
        for schedule_id, message in validation_errors[:limit]:
            warnings.append(f"schedule_invalid:{schedule_id}:{message}")
            cards.append(_board_card(
                card_id=f"schedule-invalid-{schedule_id}",
                card_type="schedule",
                title=schedule_id,
                status="invalid",
                summary=message,
                source="schedules",
                data={"schedule_id": schedule_id, "error": message},
            ))
        sources.append(_source_status("schedules", "degraded" if validation_errors else "ok", count=len(schedules)))
    except Exception as exc:
        warnings.append(f"schedules_unavailable:{exc}")
        sources.append(_source_status("schedules", "unavailable", warning=str(exc)))


def _append_gateway_card(root: Path, cards: list[dict[str, Any]], sources: list[dict[str, Any]], warnings: list[str]) -> None:
    try:
        from runtime.chaser.gateway_diagnostic import run_gateway_diagnostic

        diagnostic = run_gateway_diagnostic(root)
        cards.append(_board_card(
            card_id="gateway-diagnostic",
            card_type="gateway_diag",
            title="Chaser Gateway Diagnostic",
            status=str(diagnostic.get("overall_state") or "unknown"),
            summary=f"{len(diagnostic.get('next_actions') or [])} next actions",
            source="gateway_diagnostic",
            data={
                "ok": diagnostic.get("ok"),
                "ready": diagnostic.get("ready"),
                "overall_state": diagnostic.get("overall_state"),
                "runtime_id": diagnostic.get("runtime_id"),
                "next_action_count": len(diagnostic.get("next_actions") or []),
                "authority": diagnostic.get("authority") or {},
            },
        ))
        sources.append(_source_status("gateway_diagnostic", "ok", count=1))
    except Exception as exc:
        warnings.append(f"gateway_diagnostic_unavailable:{exc}")
        sources.append(_source_status("gateway_diagnostic", "unavailable", warning=str(exc)))


def build_board_state(
    vault_root: str | Path,
    *,
    limit: int = 8,
    include_gateway: bool = True,
) -> dict[str, Any]:
    """Build a read-only Chaser orchestration board state.

    The board aggregates existing ChaseOS state only. It does not initialize the
    Agent Bus, write approvals, execute terminal commands, dispatch runtimes, or
    mutate canonical state.
    """

    root = Path(vault_root).resolve()
    bounded_limit = max(0, min(int(limit or 8), 50))
    cards: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    warnings: list[str] = []

    _append_terminal_cards(root, cards, sources, warnings, bounded_limit)
    _append_approval_cards(root, cards, sources, warnings, bounded_limit)
    _append_agent_bus_cards(root, cards, sources, warnings, bounded_limit)
    _append_schedule_cards(root, cards, sources, warnings, bounded_limit)
    if include_gateway:
        _append_gateway_card(root, cards, sources, warnings)

    counts_by_type: dict[str, int] = {}
    counts_by_status: dict[str, int] = {}
    for card in cards:
        counts_by_type[str(card.get("type") or "unknown")] = counts_by_type.get(str(card.get("type") or "unknown"), 0) + 1
        counts_by_status[str(card.get("status") or "unknown")] = counts_by_status.get(str(card.get("status") or "unknown"), 0) + 1

    return {
        "ok": True,
        "surface": BOARD_SURFACE,
        "board_id": BOARD_ID,
        "mode": "operator_read_only",
        "updated_at": _now_iso(),
        "vault_root": str(root),
        "authority_summary": board_authority(),
        "card_count": len(cards),
        "counts_by_type": counts_by_type,
        "counts_by_status": counts_by_status,
        "cards": cards,
        "sources": sources,
        "warnings": warnings,
        "proposal_contract": {
            "available": True,
            "reason": "Pre-N6 proposal packets are available for read-only classification/readiness only.",
            "supported_actions": ["terminal_command"],
            "write_capable_terminal_lane": "gated_future_n6",
            "terminal_write_approval_request_available": True,
            "terminal_write_executor_readiness_available": True,
            "terminal_write_executor_implemented": True,
            "terminal_write_executor_cli_available": True,
            "executes_now": False,
            "writes_now": False,
            "approval_queue_writes_now": False,
            "approval_consumption_now": False,
        },
    }
