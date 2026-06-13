"""Exact-once WML-gated live AOR executor."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.aor import run_workflow

from .aor_dispatch_dry_run_executor import (
    build_workspace_mode_aor_dispatch_dry_run_executor,
)
from .aor_dispatch_gate import (
    build_workspace_mode_aor_dispatch_gate,
    format_workspace_mode_aor_dispatch_gate,
)
from .aor_live_execution_approval_gate import (
    APPROVAL_ROOT,
    _resolve_inside_vault,
    _safe_relative,
)


DECISION_ROOT = Path("07_LOGS/Agent-Activity/_workspace_mode_aor_live_execution_decisions")
CONSUMPTION_ROOT = Path("07_LOGS/Agent-Activity/_workspace_mode_aor_live_execution_consumptions")
MARKER_ROOT = CONSUMPTION_ROOT / "_markers"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_create_only(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2) + "\n")


def _path_for(root: Path, rel_root: Path, artifact_id: str) -> tuple[Path, bool, str]:
    rel_path = rel_root / f"{artifact_id}.json"
    abs_path, inside = _resolve_inside_vault(rel_path, root)
    return abs_path, inside, _safe_relative(abs_path, root)


def _approval_matches_scope(
    approval: dict[str, Any],
    *,
    approval_packet_id: str,
    workspace_path: str | Path,
    workflow_id: str,
    adapter: str,
) -> list[str]:
    blockers: list[str] = []
    scope = approval.get("approval_scope") or {}
    expected = {
        "approval_packet_id": approval_packet_id,
        "status": "pending_operator_decision",
        "workspace_path": str(workspace_path).replace("\\", "/"),
        "workflow_id": workflow_id,
        "adapter": adapter,
    }
    if approval.get("approval_packet_id") != expected["approval_packet_id"]:
        blockers.append("approval_packet_id_mismatch")
    if approval.get("status") != expected["status"]:
        blockers.append(f"approval_status_not_pending:{approval.get('status')}")
    if str(scope.get("workspace_path") or "").replace("\\", "/") != expected["workspace_path"]:
        blockers.append("approval_workspace_path_mismatch")
    if scope.get("workflow_id") != expected["workflow_id"]:
        blockers.append("approval_workflow_id_mismatch")
    if scope.get("adapter") != expected["adapter"]:
        blockers.append("approval_adapter_mismatch")
    if scope.get("exact_scope_only") is not True:
        blockers.append("approval_scope_not_exact")
    if scope.get("requires_gate_rerun") is not True:
        blockers.append("approval_missing_gate_rerun_requirement")
    if scope.get("requires_fresh_aor_dry_run_evidence") is not True:
        blockers.append("approval_missing_fresh_dry_run_requirement")
    if scope.get("live_aor_execution_allowed_after_separate_consumption") is not True:
        blockers.append("approval_does_not_allow_live_execution_after_consumption")
    if scope.get("workflow_writeback_allowed_after_separate_consumption") is not True:
        blockers.append("approval_does_not_allow_workflow_writeback_after_consumption")
    if scope.get("agent_bus_task_allowed") is not False:
        blockers.append("approval_bus_scope_not_denied")
    if scope.get("provider_or_model_call_allowed") is not False:
        blockers.append("approval_provider_scope_not_denied")
    if scope.get("browser_or_external_action_allowed") is not False:
        blockers.append("approval_browser_scope_not_denied")
    if scope.get("external_send_allowed") is not False:
        blockers.append("approval_external_send_scope_not_denied")
    if scope.get("canonical_promotion_allowed") is not False:
        blockers.append("approval_canonical_scope_not_denied")
    return blockers


def _decision_payload(
    *,
    approval_packet_id: str,
    decision: str,
    requested_by: str,
    reason: str | None,
    approval_artifact_path: str,
    gate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "workspace_mode_aor_live_execution_decision.v1",
        "approval_packet_id": approval_packet_id,
        "decision": decision,
        "decided_at": _now(),
        "decided_by": requested_by,
        "reason": reason or "",
        "approval_artifact_path": approval_artifact_path,
        "approval_scope": {
            "workspace_path": gate.get("workspace_path"),
            "workflow_id": gate.get("requested_workflow_id"),
            "adapter": gate.get("requested_adapter"),
            "profile_source_path": gate.get("profile_source_path"),
            "dispatch_gate_packet_id": gate.get("dispatch_gate_packet_id"),
            "exact_scope_only": True,
        },
        "authority_flags": {
            "decision_recorded": True,
            "approval_consumed": False,
            "run_workflow_live_called": False,
            "workflow_execution_performed": False,
            "workflow_writeback_performed": False,
            "agent_bus_task_written": False,
            "provider_or_model_call_performed": False,
            "browser_or_external_action_performed": False,
            "external_action_performed": False,
            "canonical_write_performed": False,
        },
    }


def _marker_payload(
    *,
    approval_packet_id: str,
    requested_by: str,
    decision_artifact_path: str,
    dry_run_audit_id: str,
    gate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "workspace_mode_aor_live_execution_exact_once_marker.v1",
        "approval_packet_id": approval_packet_id,
        "reserved_at": _now(),
        "reserved_by": requested_by,
        "decision_artifact_path": decision_artifact_path,
        "fresh_aor_dry_run_audit_id": dry_run_audit_id,
        "workspace_path": gate.get("workspace_path"),
        "workflow_id": gate.get("requested_workflow_id"),
        "adapter": gate.get("requested_adapter"),
        "profile_source_path": gate.get("profile_source_path"),
        "dispatch_gate_packet_id": gate.get("dispatch_gate_packet_id"),
        "reservation_boundary": "reserved_after_fresh_dry_run_and_before_live_run_workflow",
    }


def _consumption_payload(
    *,
    approval_packet_id: str,
    requested_by: str,
    approval_artifact_path: str,
    decision_artifact_path: str,
    marker_path: str,
    dry_run: dict[str, Any],
    live_result: Any | None,
    gate: dict[str, Any],
    blockers: list[str],
) -> dict[str, Any]:
    live_payload: dict[str, Any] | None = None
    if live_result is not None:
        live_payload = {
            "workflow_id": live_result.workflow_id,
            "status": live_result.status,
            "audit_id": live_result.audit_id,
            "stage_reached": live_result.stage_reached,
            "outputs": live_result.outputs,
            "escalation_reason": live_result.escalation_reason,
            "error": live_result.error,
        }
    return {
        "schema_version": "workspace_mode_aor_live_execution_consumption.v1",
        "approval_packet_id": approval_packet_id,
        "consumed_at": _now(),
        "consumed_by": requested_by,
        "status": "consumed" if live_result is not None and live_result.status == "success" else "blocked_or_failed",
        "approval_artifact_path": approval_artifact_path,
        "decision_artifact_path": decision_artifact_path,
        "exact_once_marker_path": marker_path,
        "workspace_path": gate.get("workspace_path"),
        "workflow_id": gate.get("requested_workflow_id"),
        "adapter": gate.get("requested_adapter"),
        "profile_source_path": gate.get("profile_source_path"),
        "dispatch_gate_packet_id": gate.get("dispatch_gate_packet_id"),
        "fresh_dry_run": {
            "performed": bool(dry_run.get("aor_dry_run_performed")),
            "ok": bool(dry_run.get("ok")),
            "audit_id": dry_run.get("aor_dry_run_audit_id"),
            "status": (dry_run.get("aor_result") or {}).get("status"),
        },
        "live_aor_result": live_payload,
        "blockers": blockers,
        "authority_flags": {
            "approval_consumed": live_result is not None and live_result.status == "success",
            "run_workflow_called": live_result is not None,
            "run_workflow_live_called": live_result is not None,
            "workflow_execution_performed": live_result is not None,
            "workflow_writeback_performed": live_result is not None and live_result.status == "success",
            "agent_bus_task_written": False,
            "provider_or_model_call_performed": False,
            "browser_or_external_action_performed": False,
            "external_action_performed": False,
            "canonical_write_performed": False,
        },
    }


def build_workspace_mode_aor_live_executor(
    *,
    workspace_path: str | Path,
    workflow_id: str,
    adapter: str = "codex",
    gate_approval_id: str,
    vault_root: str | Path | None = None,
    profile_path: str | Path | None = None,
    requested_by: str = "operator",
    decision: str = "approved",
    reason: str | None = None,
    write_approval_decision: bool = False,
    write_approval_consumption: bool = False,
    write_consumption_marker: bool = False,
    confirm: bool = False,
) -> dict[str, Any]:
    """Consume an approved WML live-execution packet and run AOR once."""

    root = Path(vault_root or ".").resolve()
    approval_abs, approval_inside, approval_rel = _path_for(root, APPROVAL_ROOT, gate_approval_id)
    decision_abs, decision_inside, decision_rel = _path_for(root, DECISION_ROOT, gate_approval_id)
    consumption_abs, consumption_inside, consumption_rel = _path_for(root, CONSUMPTION_ROOT, gate_approval_id)
    marker_abs, marker_inside, marker_rel = _path_for(root, MARKER_ROOT, gate_approval_id)

    blockers: list[str] = []
    if not confirm:
        blockers.append("confirm_required_for_live_execution")
    if decision not in {"approved", "denied"}:
        blockers.append("decision_must_be_approved_or_denied")
    if not gate_approval_id:
        blockers.append("gate_approval_id_required")
    if not approval_inside:
        blockers.append("approval_artifact_path_outside_vault")
    if not decision_inside:
        blockers.append("decision_artifact_path_outside_vault")
    if not consumption_inside:
        blockers.append("consumption_artifact_path_outside_vault")
    if not marker_inside:
        blockers.append("consumption_marker_path_outside_vault")
    if not approval_abs.exists():
        blockers.append("approval_artifact_missing")

    approval: dict[str, Any] = {}
    if approval_abs.exists() and approval_inside:
        try:
            approval = _read_json(approval_abs)
        except (OSError, json.JSONDecodeError) as exc:
            blockers.append(f"approval_artifact_unreadable:{exc}")
        else:
            blockers.extend(
                _approval_matches_scope(
                    approval,
                    approval_packet_id=gate_approval_id,
                    workspace_path=workspace_path,
                    workflow_id=workflow_id,
                    adapter=adapter,
                )
            )

    gate = build_workspace_mode_aor_dispatch_gate(
        workspace_path=workspace_path,
        workflow_id=workflow_id,
        adapter=adapter,
        vault_root=root,
        profile_path=profile_path,
        requested_by=requested_by,
        confirm=True,
    )
    if not gate.get("dispatch_gate_cleared"):
        blockers.append("fresh_dispatch_gate_not_cleared")
        blockers.extend(list(gate.get("blockers") or []))
    scope = approval.get("approval_scope") or {}
    if scope.get("dispatch_gate_packet_id") and scope.get("dispatch_gate_packet_id") != gate.get("dispatch_gate_packet_id"):
        blockers.append("fresh_dispatch_gate_packet_mismatch")
    if scope.get("profile_source_path") and scope.get("profile_source_path") != gate.get("profile_source_path"):
        blockers.append("fresh_profile_source_path_mismatch")
    if marker_abs.exists():
        blockers.append("exact_once_marker_already_present")
    if write_approval_decision and decision_abs.exists():
        blockers.append("decision_artifact_already_exists_no_overwrite")
    if write_approval_consumption and consumption_abs.exists():
        blockers.append("consumption_artifact_already_exists_no_overwrite")
    if decision == "approved":
        if not write_approval_decision:
            blockers.append("write_approval_decision_required")
        if not write_approval_consumption:
            blockers.append("write_approval_consumption_required")
        if not write_consumption_marker:
            blockers.append("write_consumption_marker_required")

    decision_written = False
    marker_written = False
    consumption_written = False
    dry_run: dict[str, Any] = {}
    live_result: Any | None = None

    if blockers:
        return {
            "ok": False,
            "surface": "workspace_mode_aor_live_executor",
            "schema_version": "workspace_mode_aor_live_executor.v1",
            "approval_packet_id": gate_approval_id,
            "decision": decision,
            "approval_artifact_path": approval_rel,
            "decision_artifact_path": decision_rel,
            "consumption_artifact_path": consumption_rel,
            "exact_once_marker_path": marker_rel,
            "dispatch_gate_cleared": bool(gate.get("dispatch_gate_cleared")),
            "approval_consumed": False,
            "decision_artifact_written": False,
            "consumption_marker_written": False,
            "consumption_artifact_written": False,
            "fresh_aor_dry_run_performed": False,
            "run_workflow_called": False,
            "run_workflow_live_called": False,
            "workflow_execution_performed": False,
            "workflow_writeback_performed": False,
            "agent_bus_task_written": False,
            "provider_or_model_call_performed": False,
            "browser_or_external_action_performed": False,
            "external_action_performed": False,
            "canonical_write_performed": False,
            "blockers": blockers,
            "dispatch_gate": gate,
            "next_recommended_pass": "resolve-workspace-mode-aor-live-executor-blockers",
        }

    decision_payload = _decision_payload(
        approval_packet_id=gate_approval_id,
        decision=decision,
        requested_by=requested_by,
        reason=reason,
        approval_artifact_path=approval_rel,
        gate=gate,
    )
    if write_approval_decision:
        _write_json_create_only(decision_abs, decision_payload)
        decision_written = True

    if decision == "denied":
        return {
            "ok": True,
            "surface": "workspace_mode_aor_live_executor",
            "schema_version": "workspace_mode_aor_live_executor.v1",
            "approval_packet_id": gate_approval_id,
            "decision": decision,
            "approval_artifact_path": approval_rel,
            "decision_artifact_path": decision_rel,
            "decision_artifact_written": decision_written,
            "approval_consumed": False,
            "run_workflow_called": False,
            "run_workflow_live_called": False,
            "workflow_execution_performed": False,
            "workflow_writeback_performed": False,
            "blockers": [],
            "next_recommended_pass": "operator-reopen-or-close-wml-aor-live-execution-request",
        }

    dry_run = build_workspace_mode_aor_dispatch_dry_run_executor(
        workspace_path=workspace_path,
        workflow_id=workflow_id,
        adapter=adapter,
        vault_root=root,
        profile_path=profile_path,
        requested_by=requested_by,
        confirm=True,
    )
    if not dry_run.get("ok"):
        blockers.append("fresh_aor_dry_run_failed")
        blockers.extend(list(dry_run.get("blockers") or []))
    else:
        marker_payload = _marker_payload(
            approval_packet_id=gate_approval_id,
            requested_by=requested_by,
            decision_artifact_path=decision_rel,
            dry_run_audit_id=str(dry_run.get("aor_dry_run_audit_id") or ""),
            gate=gate,
        )
        if write_consumption_marker:
            _write_json_create_only(marker_abs, marker_payload)
            marker_written = True
        live_inputs = {
            "workspace_path": gate.get("workspace_path"),
            "requested_by": requested_by,
            "wml_live_execution_approval_packet_id": gate_approval_id,
            "wml_dispatch_gate_packet_id": gate.get("dispatch_gate_packet_id"),
            "wml_fresh_dry_run_audit_id": dry_run.get("aor_dry_run_audit_id"),
        }
        live_result = run_workflow(
            workflow_id,
            inputs=live_inputs,
            vault_root=root,
            dry_run=False,
        )
        if live_result.status != "success":
            blockers.append(f"aor_live_status:{live_result.status}")
            if live_result.escalation_reason:
                blockers.append(f"aor_escalation:{live_result.escalation_reason}")
            if live_result.error:
                blockers.append(f"aor_error:{live_result.error}")

    consumption_payload = _consumption_payload(
        approval_packet_id=gate_approval_id,
        requested_by=requested_by,
        approval_artifact_path=approval_rel,
        decision_artifact_path=decision_rel,
        marker_path=marker_rel,
        dry_run=dry_run,
        live_result=live_result,
        gate=gate,
        blockers=blockers,
    )
    if write_approval_consumption:
        _write_json_create_only(consumption_abs, consumption_payload)
        consumption_written = True

    ok = live_result is not None and live_result.status == "success" and not blockers
    return {
        "ok": ok,
        "surface": "workspace_mode_aor_live_executor",
        "schema_version": "workspace_mode_aor_live_executor.v1",
        "approval_packet_id": gate_approval_id,
        "decision": decision,
        "workspace_path": gate.get("workspace_path"),
        "requested_workflow_id": workflow_id,
        "requested_adapter": adapter,
        "profile_source_path": gate.get("profile_source_path"),
        "dispatch_gate_packet_id": gate.get("dispatch_gate_packet_id"),
        "approval_artifact_path": approval_rel,
        "decision_artifact_path": decision_rel,
        "consumption_artifact_path": consumption_rel,
        "exact_once_marker_path": marker_rel,
        "decision_artifact_written": decision_written,
        "consumption_marker_written": marker_written,
        "consumption_artifact_written": consumption_written,
        "dispatch_gate_cleared": bool(gate.get("dispatch_gate_cleared")),
        "fresh_aor_dry_run_performed": bool(dry_run.get("aor_dry_run_performed")),
        "fresh_aor_dry_run_ok": bool(dry_run.get("ok")),
        "fresh_aor_dry_run_audit_id": dry_run.get("aor_dry_run_audit_id"),
        "run_workflow_called": live_result is not None,
        "run_workflow_live_called": live_result is not None,
        "workflow_execution_performed": live_result is not None,
        "workflow_writeback_performed": live_result is not None and live_result.status == "success",
        "approval_consumed": ok,
        "agent_bus_task_written": False,
        "provider_or_model_call_performed": False,
        "browser_or_external_action_performed": False,
        "external_action_performed": False,
        "canonical_write_performed": False,
        "aor_live_result": None
        if live_result is None
        else {
            "workflow_id": live_result.workflow_id,
            "status": live_result.status,
            "audit_id": live_result.audit_id,
            "stage_reached": live_result.stage_reached,
            "outputs": live_result.outputs,
            "escalation_reason": live_result.escalation_reason,
            "error": live_result.error,
        },
        "aor_live_audit_id": None if live_result is None else live_result.audit_id,
        "blockers": blockers,
        "dispatch_gate": gate,
        "dry_run_executor": dry_run,
        "next_recommended_pass": (
            "workspace-mode-aor-live-executor-closeout"
            if ok
            else "resolve-aor-live-executor-result"
        ),
    }


def format_workspace_mode_aor_live_executor(payload: dict[str, Any]) -> str:
    blockers = payload.get("blockers") or []
    lines = [
        "Workspace Mode AOR live executor",
        f"  approval_packet_id:   {payload.get('approval_packet_id')}",
        f"  workspace_path:       {payload.get('workspace_path')}",
        f"  workflow_id:          {payload.get('requested_workflow_id')}",
        f"  dispatch_gate_cleared:{payload.get('dispatch_gate_cleared')}",
        f"  dry_run_ok:           {payload.get('fresh_aor_dry_run_ok')}",
        f"  live_run_called:      {payload.get('run_workflow_live_called')}",
        f"  live_status:          {(payload.get('aor_live_result') or {}).get('status')}",
        f"  live_audit_id:        {payload.get('aor_live_audit_id') or '(none)'}",
        f"  marker_path:          {payload.get('exact_once_marker_path')}",
        f"  consumption_path:     {payload.get('consumption_artifact_path')}",
        f"  blockers:             {', '.join(blockers) if blockers else '(none)'}",
        "  boundary: exact-scope live AOR workflow only; no Agent Bus task, provider/model call, browser/external action, or canonical promotion.",
    ]
    if payload.get("dispatch_gate") and not payload.get("dispatch_gate_cleared"):
        lines.append("")
        lines.append(format_workspace_mode_aor_dispatch_gate(payload["dispatch_gate"]))
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m runtime.workspace_modes.aor_live_executor",
        description="Consume an approved WML live AOR execution packet and run AOR once.",
    )
    parser.add_argument("--workspace-path", required=True, metavar="PATH")
    parser.add_argument("--workflow-id", required=True, metavar="WORKFLOW_ID")
    parser.add_argument("--adapter", default="codex", metavar="ADAPTER")
    parser.add_argument("--gate-approval-id", required=True, metavar="ID")
    parser.add_argument("--profile", dest="profile_path", default=None, metavar="PATH")
    parser.add_argument("--vault-root", default=None, metavar="PATH")
    parser.add_argument("--requested-by", default="operator", metavar="NAME")
    parser.add_argument("--decision", default="approved", choices=["approved", "denied"])
    parser.add_argument("--reason", default=None)
    parser.add_argument("--write-approval-decision", action="store_true")
    parser.add_argument("--write-approval-consumption", action="store_true")
    parser.add_argument("--write-consumption-marker", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--json", action="store_true", dest="output_json")
    args = parser.parse_args(argv)

    payload = build_workspace_mode_aor_live_executor(
        workspace_path=args.workspace_path,
        workflow_id=args.workflow_id,
        adapter=args.adapter,
        gate_approval_id=args.gate_approval_id,
        vault_root=args.vault_root,
        profile_path=args.profile_path,
        requested_by=args.requested_by,
        decision=args.decision,
        reason=args.reason,
        write_approval_decision=args.write_approval_decision,
        write_approval_consumption=args.write_approval_consumption,
        write_consumption_marker=args.write_consumption_marker,
        confirm=args.confirm,
    )
    if args.output_json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_workspace_mode_aor_live_executor(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
