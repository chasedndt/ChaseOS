"""WML-gated AOR dry-run executor."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runtime.aor import run_workflow

from .aor_dispatch_gate import (
    build_workspace_mode_aor_dispatch_gate,
    format_workspace_mode_aor_dispatch_gate,
)


def build_workspace_mode_aor_dispatch_dry_run_executor(
    *,
    workspace_path: str | Path,
    workflow_id: str,
    adapter: str = "codex",
    vault_root: str | Path | None = None,
    profile_path: str | Path | None = None,
    requested_by: str = "operator",
    confirm: bool = False,
) -> dict[str, Any]:
    """Run AOR dry-run only after the WML dispatch gate clears."""

    gate = build_workspace_mode_aor_dispatch_gate(
        workspace_path=workspace_path,
        workflow_id=workflow_id,
        adapter=adapter,
        vault_root=vault_root,
        profile_path=profile_path,
        requested_by=requested_by,
        confirm=confirm,
    )
    if not gate.get("dispatch_gate_cleared"):
        return {
            "ok": False,
            "surface": "workspace_mode_aor_dispatch_dry_run_executor",
            "schema_version": "workspace_mode_aor_dispatch_dry_run_executor.v1",
            "dry_run_executor": True,
            "dispatch_gate_cleared": False,
            "aor_dry_run_performed": False,
            "run_workflow_called": False,
            "workflow_execution_performed": False,
            "workflow_writeback_performed": False,
            "agent_bus_task_written": False,
            "approval_consumed": False,
            "provider_or_model_call_performed": False,
            "browser_or_external_action_performed": False,
            "external_action_performed": False,
            "canonical_write_performed": False,
            "blockers": list(gate.get("blockers") or []),
            "dispatch_gate": gate,
            "next_recommended_pass": "resolve-workspace-mode-dispatch-gate-blockers",
        }

    inputs = {
        "workspace_path": gate.get("workspace_path"),
        "requested_by": requested_by,
        "wml_dispatch_gate_packet_id": gate.get("dispatch_gate_packet_id"),
    }
    result = run_workflow(
        workflow_id,
        inputs=inputs,
        vault_root=Path(gate["vault_root"]) if gate.get("vault_root") else vault_root,
        dry_run=True,
    )
    ok = result.status == "dry_run_ok"
    blockers: list[str] = []
    if not ok:
        blockers.append(f"aor_dry_run_status:{result.status}")
        if result.escalation_reason:
            blockers.append(f"aor_escalation:{result.escalation_reason}")
        if result.error:
            blockers.append(f"aor_error:{result.error}")

    return {
        "ok": ok,
        "surface": "workspace_mode_aor_dispatch_dry_run_executor",
        "schema_version": "workspace_mode_aor_dispatch_dry_run_executor.v1",
        "dry_run_executor": True,
        "dispatch_gate_cleared": True,
        "dispatch_gate_packet_id": gate.get("dispatch_gate_packet_id"),
        "workspace_path": gate.get("workspace_path"),
        "requested_workflow_id": workflow_id,
        "requested_adapter": adapter,
        "profile_source_path": gate.get("profile_source_path"),
        "aor_dry_run_performed": True,
        "run_workflow_called": True,
        "run_workflow_dry_run": True,
        "workflow_execution_performed": False,
        "workflow_writeback_performed": False,
        "agent_bus_task_written": False,
        "approval_consumed": False,
        "provider_or_model_call_performed": False,
        "browser_or_external_action_performed": False,
        "external_action_performed": False,
        "canonical_write_performed": False,
        "aor_result": {
            "workflow_id": result.workflow_id,
            "status": result.status,
            "audit_id": result.audit_id,
            "stage_reached": result.stage_reached,
            "outputs": result.outputs,
            "escalation_reason": result.escalation_reason,
            "error": result.error,
        },
        "aor_dry_run_audit_id": result.audit_id,
        "aor_dry_run_audit_written": bool(result.audit_id),
        "blockers": blockers,
        "dispatch_gate": gate,
        "next_recommended_pass": (
            "workspace-mode-aor-live-executor-approval-gate"
            if ok
            else "resolve-aor-dry-run-blockers"
        ),
    }


def format_workspace_mode_aor_dispatch_dry_run_executor(payload: dict[str, Any]) -> str:
    blockers = payload.get("blockers") or []
    lines = [
        "Workspace Mode AOR dry-run executor",
        f"  workspace_path:       {payload.get('workspace_path') or payload.get('dispatch_gate', {}).get('workspace_path')}",
        f"  workflow_id:          {payload.get('requested_workflow_id') or payload.get('dispatch_gate', {}).get('requested_workflow_id')}",
        f"  dispatch_gate_cleared:{payload.get('dispatch_gate_cleared')}",
        f"  run_workflow_called:  {payload.get('run_workflow_called')}",
        f"  aor_dry_run:          {payload.get('aor_dry_run_performed')}",
        f"  aor_status:           {(payload.get('aor_result') or {}).get('status')}",
        f"  audit_id:             {payload.get('aor_dry_run_audit_id') or '(none)'}",
        f"  blockers:             {', '.join(blockers) if blockers else '(none)'}",
        "  boundary: AOR dry-run only; no handler execution, workflow writeback, Agent Bus task, approval consumption, external action, or canonical writeback.",
    ]
    if payload.get("dispatch_gate") and not payload.get("dispatch_gate_cleared"):
        lines.append("")
        lines.append(format_workspace_mode_aor_dispatch_gate(payload["dispatch_gate"]))
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m runtime.workspace_modes.aor_dispatch_dry_run_executor",
        description="Run AOR dry-run after WML dispatch gate clearance.",
    )
    parser.add_argument("--workspace-path", required=True, metavar="PATH")
    parser.add_argument("--workflow-id", required=True, metavar="WORKFLOW_ID")
    parser.add_argument("--adapter", default="codex", metavar="ADAPTER")
    parser.add_argument("--profile", dest="profile_path", default=None, metavar="PATH")
    parser.add_argument("--vault-root", default=None, metavar="PATH")
    parser.add_argument("--requested-by", default="operator", metavar="NAME")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--json", action="store_true", dest="output_json")
    args = parser.parse_args(argv)

    payload = build_workspace_mode_aor_dispatch_dry_run_executor(
        workspace_path=args.workspace_path,
        workflow_id=args.workflow_id,
        adapter=args.adapter,
        vault_root=args.vault_root,
        profile_path=args.profile_path,
        requested_by=args.requested_by,
        confirm=args.confirm,
    )
    if args.output_json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_workspace_mode_aor_dispatch_dry_run_executor(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
