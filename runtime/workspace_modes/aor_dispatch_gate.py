"""No-execution AOR dispatch gate for Workspace Mode Layer context."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .aor_routing_preview import (
    build_aor_workspace_route_preview,
    format_aor_workspace_route_preview,
)


def _packet_id(route_preview: dict[str, Any], requested_by: str) -> str:
    digest = hashlib.sha256(
        json.dumps(
            {
                "workspace_path": route_preview.get("workspace_path"),
                "workflow_id": route_preview.get("requested_workflow_id"),
                "adapter": route_preview.get("requested_adapter"),
                "profile_source_path": route_preview.get("profile_source_path"),
                "requested_by": requested_by,
                "surface": "workspace_mode_aor_dispatch_gate.v1",
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:16]
    return f"wml-aor-dispatch-gate-{digest}"


def _future_executor_requirements() -> list[str]:
    return [
        "executor re-runs this dispatch gate immediately before any AOR call",
        "executor must call run_workflow only after dispatch_gate_cleared=true",
        "executor must support dry-run before live writeback",
        "executor must preserve AOR audit/writeback boundaries",
        "executor must not write Agent Bus tasks unless a separate bus boundary is approved",
        "executor must report workflow_execution_performed and files_written from AOR result",
    ]


def build_workspace_mode_aor_dispatch_gate(
    *,
    workspace_path: str | Path,
    workflow_id: str,
    adapter: str = "codex",
    vault_root: str | Path | None = None,
    profile_path: str | Path | None = None,
    requested_by: str = "operator",
    confirm: bool = False,
) -> dict[str, Any]:
    """Build a no-execution WML dispatch gate in front of AOR."""

    route_preview = build_aor_workspace_route_preview(
        workspace_path=workspace_path,
        workflow_id=workflow_id,
        adapter=adapter,
        vault_root=vault_root,
        profile_path=profile_path,
    )
    route_blockers = list(route_preview.get("dispatch_blockers") or [])
    blockers = list(route_blockers)
    if not route_preview.get("ready_for_aor_dispatch"):
        blockers.append("route_preview_not_ready_for_aor_dispatch")
    if not confirm:
        blockers.append("confirm_required_to_clear_dispatch_gate")

    cleared = not blockers
    packet_id = _packet_id(route_preview, requested_by=requested_by)
    future_command = (
        "python -m runtime.cli.main runtime workspace-mode dispatch-gate "
        f"--workspace-path {route_preview.get('workspace_path')} "
        f"--workflow-id {workflow_id} --adapter {adapter} --confirm --json"
    )

    return {
        "ok": True,
        "surface": "workspace_mode_aor_dispatch_gate",
        "schema_version": "workspace_mode_aor_dispatch_gate.v1",
        "preview_only": True,
        "dispatch_gate_only": True,
        "vault_root": route_preview.get("vault_root"),
        "requested_by": requested_by,
        "dispatch_gate_packet_id": packet_id,
        "workspace_path": route_preview.get("workspace_path"),
        "requested_workflow_id": workflow_id,
        "requested_adapter": adapter,
        "profile_source": route_preview.get("profile_source"),
        "profile_source_path": route_preview.get("profile_source_path"),
        "workspace_mode": route_preview.get("workspace_mode"),
        "adapter_ceiling": route_preview.get("adapter_ceiling"),
        "approval_mode": route_preview.get("approval_mode"),
        "workflow_manifest": route_preview.get("workflow_manifest"),
        "route_preview_ready_for_aor_dispatch": bool(route_preview.get("ready_for_aor_dispatch")),
        "route_preview_blockers": route_blockers,
        "operator_confirmed": bool(confirm),
        "dispatch_gate_cleared": cleared,
        "ready_for_guarded_aor_executor": cleared,
        "aor_dispatch_enabled": False,
        "run_workflow_called": False,
        "workflow_execution_performed": False,
        "workflow_writeback_performed": False,
        "agent_bus_task_written": False,
        "approval_consumed": False,
        "provider_or_model_call_performed": False,
        "browser_or_external_action_performed": False,
        "external_action_performed": False,
        "canonical_write_performed": False,
        "blockers": blockers,
        "future_executor_requirements": _future_executor_requirements(),
        "future_executor_command_preview": future_command,
        "next_recommended_pass": (
            "workspace-mode-aor-dispatch-dry-run-executor"
            if cleared
            else "resolve-workspace-mode-dispatch-gate-blockers"
        ),
        "route_preview": route_preview,
    }


def format_workspace_mode_aor_dispatch_gate(payload: dict[str, Any]) -> str:
    blockers = payload.get("blockers") or []
    lines = [
        "Workspace Mode AOR dispatch gate",
        f"  workspace_path:        {payload.get('workspace_path')}",
        f"  workflow_id:           {payload.get('requested_workflow_id')}",
        f"  adapter:               {payload.get('requested_adapter')}",
        f"  profile_source:        {payload.get('profile_source')} ({payload.get('profile_source_path') or 'none'})",
        f"  route_ready:           {payload.get('route_preview_ready_for_aor_dispatch')}",
        f"  operator_confirmed:    {payload.get('operator_confirmed')}",
        f"  dispatch_gate_cleared: {payload.get('dispatch_gate_cleared')}",
        f"  packet_id:             {payload.get('dispatch_gate_packet_id')}",
        f"  blockers:              {', '.join(blockers) if blockers else '(none)'}",
        "  boundary: gate only; no run_workflow call, workflow execution, writeback, Agent Bus task, approval consumption, external action, or canonical writeback.",
    ]
    if payload.get("route_preview") and blockers:
        lines.append("")
        lines.append(format_aor_workspace_route_preview(payload["route_preview"]))
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m runtime.workspace_modes.aor_dispatch_gate",
        description="Gate a WML/AOR dispatch request without running a workflow.",
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

    payload = build_workspace_mode_aor_dispatch_gate(
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
        print(format_workspace_mode_aor_dispatch_gate(payload))
    return 0 if payload.get("ok") and payload.get("dispatch_gate_cleared") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
