"""Approval-request gate for future WML-gated live AOR execution."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .aor_dispatch_gate import (
    build_workspace_mode_aor_dispatch_gate,
    format_workspace_mode_aor_dispatch_gate,
)


APPROVAL_ROOT = Path("07_LOGS/Agent-Activity/_workspace_mode_aor_live_execution_approvals")


def _safe_relative(path: Path, vault_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(vault_root.resolve())).replace("\\", "/")
    except (OSError, ValueError):
        return str(path).replace("\\", "/")


def _resolve_inside_vault(path: str | Path, vault_root: Path) -> tuple[Path, bool]:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = vault_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(vault_root.resolve())
        return resolved, True
    except ValueError:
        return resolved, False


def _approval_packet_id(gate: dict[str, Any], requested_by: str) -> str:
    material = {
        "surface": "workspace_mode_aor_live_execution_approval_gate.v1",
        "workspace_path": gate.get("workspace_path"),
        "workflow_id": gate.get("requested_workflow_id"),
        "adapter": gate.get("requested_adapter"),
        "profile_source_path": gate.get("profile_source_path"),
        "dispatch_gate_packet_id": gate.get("dispatch_gate_packet_id"),
        "requested_by": requested_by,
    }
    digest = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return f"wml-aor-live-exec-appr-{digest}"


def _approval_text(*, approval_packet_id: str, gate: dict[str, Any]) -> str:
    profile_source_path = gate.get("profile_source_path") or "(none)"
    return "\n".join(
        [
            "APPROVE WML-GATED LIVE AOR EXECUTION ONLY:",
            f"- approval_packet_id: {approval_packet_id}",
            f"- workspace_path: {gate.get('workspace_path')}",
            f"- workflow_id: {gate.get('requested_workflow_id')}",
            f"- adapter: {gate.get('requested_adapter')}",
            f"- profile_source_path: {profile_source_path}",
            f"- dispatch_gate_packet_id: {gate.get('dispatch_gate_packet_id')}",
            "",
            "This approval would allow a future executor to call AOR live only for this exact scope.",
            "The future executor must re-run the WML dispatch gate immediately before execution.",
            "The future executor must run or bind fresh AOR dry-run evidence before live writeback.",
            "No Agent Bus task, provider/model call, browser action, external send, protected-file write, or canonical promotion is approved by this packet.",
        ]
    )


def _approval_artifact_payload(
    *,
    approval_packet_id: str,
    requested_by: str,
    vault_root: Path,
    gate: dict[str, Any],
) -> dict[str, Any]:
    gate_cleared = bool(gate.get("dispatch_gate_cleared"))
    return {
        "schema_version": "workspace_mode_aor_live_execution_approval_request.v1",
        "approval_packet_id": approval_packet_id,
        "status": "pending_operator_decision",
        "created_at": datetime.now(UTC).isoformat(),
        "requested_by": requested_by,
        "vault_root": str(vault_root),
        "requested_action": "approve_future_wml_gated_live_aor_execution",
        "approval_scope": {
            "workspace_path": gate.get("workspace_path"),
            "workflow_id": gate.get("requested_workflow_id"),
            "adapter": gate.get("requested_adapter"),
            "profile_source_path": gate.get("profile_source_path"),
            "dispatch_gate_packet_id": gate.get("dispatch_gate_packet_id"),
            "live_aor_execution_allowed_after_separate_consumption": gate_cleared,
            "workflow_writeback_allowed_after_separate_consumption": gate_cleared,
            "exact_scope_only": True,
            "requires_gate_rerun": True,
            "requires_fresh_aor_dry_run_evidence": True,
            "agent_bus_task_allowed": False,
            "provider_or_model_call_allowed": False,
            "browser_or_external_action_allowed": False,
            "external_send_allowed": False,
            "protected_file_write_allowed": False,
            "canonical_promotion_allowed": False,
        },
        "operator_confirmation_text": _approval_text(
            approval_packet_id=approval_packet_id,
            gate=gate,
        ),
        "dispatch_gate": {
            "dispatch_gate_packet_id": gate.get("dispatch_gate_packet_id"),
            "dispatch_gate_cleared": gate.get("dispatch_gate_cleared"),
            "workspace_path": gate.get("workspace_path"),
            "requested_workflow_id": gate.get("requested_workflow_id"),
            "requested_adapter": gate.get("requested_adapter"),
            "profile_source": gate.get("profile_source"),
            "profile_source_path": gate.get("profile_source_path"),
            "workflow_manifest": gate.get("workflow_manifest"),
        },
        "future_executor_requirements": [
            "approval packet id must match this request",
            "operator decision must approve this exact packet id and scope",
            "executor must reserve an exact-once consumption marker before live execution",
            "executor must re-run the WML dispatch gate immediately before live execution",
            "executor must run or bind fresh AOR dry-run evidence before live execution",
            "executor must call run_workflow with dry_run=False only after all gates clear",
            "executor must report all AOR outputs, files written, and audit ids",
            "executor must not write Agent Bus tasks unless a separate bus approval exists",
        ],
        "authority_flags": {
            "approval_request_written": False,
            "approval_consumed": False,
            "run_workflow_called": False,
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


def build_workspace_mode_aor_live_execution_approval_gate(
    *,
    workspace_path: str | Path,
    workflow_id: str,
    adapter: str = "codex",
    vault_root: str | Path | None = None,
    profile_path: str | Path | None = None,
    requested_by: str = "operator",
    approval_packet_id: str | None = None,
    write_approval_request: bool = False,
    confirm: bool = False,
) -> dict[str, Any]:
    """Build or optionally write a pending live-execution approval request.

    This surface never calls AOR live and never consumes an approval. It only
    binds a cleared dispatch gate to a future exact-scope approval request.
    """

    gate = build_workspace_mode_aor_dispatch_gate(
        workspace_path=workspace_path,
        workflow_id=workflow_id,
        adapter=adapter,
        vault_root=vault_root,
        profile_path=profile_path,
        requested_by=requested_by,
        confirm=confirm,
    )
    root = Path(gate["vault_root"]).resolve() if gate.get("vault_root") else Path(vault_root or ".").resolve()
    request_id = approval_packet_id or _approval_packet_id(gate, requested_by=requested_by)
    approval_rel_path = APPROVAL_ROOT / f"{request_id}.json"
    approval_abs_path, approval_path_inside = _resolve_inside_vault(approval_rel_path, root)

    blockers = list(gate.get("blockers") or [])
    if not gate.get("dispatch_gate_cleared"):
        blockers.append("dispatch_gate_not_cleared")
    if not approval_path_inside:
        blockers.append("approval_artifact_path_outside_vault")

    ready_for_operator_decision = not blockers
    artifact_payload = _approval_artifact_payload(
        approval_packet_id=request_id,
        requested_by=requested_by,
        vault_root=root,
        gate=gate,
    )

    approval_request_written = False
    if write_approval_request:
        if not ready_for_operator_decision:
            blockers.append("approval_request_not_written_until_blockers_clear")
        elif approval_abs_path.exists():
            blockers.append("approval_artifact_already_exists_no_overwrite")
        else:
            approval_abs_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_payload["authority_flags"]["approval_request_written"] = True
            approval_abs_path.write_text(
                json.dumps(artifact_payload, indent=2) + "\n",
                encoding="utf-8",
            )
            approval_request_written = True

    ok = not blockers
    return {
        "ok": ok,
        "surface": "workspace_mode_aor_live_execution_approval_gate",
        "schema_version": "workspace_mode_aor_live_execution_approval_gate.v1",
        "approval_request_surface_only": True,
        "preview_only": not approval_request_written,
        "write_approval_request_requested": write_approval_request,
        "approval_request_written": approval_request_written,
        "approval_packet_id": request_id,
        "approval_artifact_path": _safe_relative(approval_abs_path, root),
        "approval_artifact_path_in_vault": approval_path_inside,
        "requested_by": requested_by,
        "ready_for_operator_decision": ready_for_operator_decision and not blockers,
        "operator_confirmation_text": _approval_text(
            approval_packet_id=request_id,
            gate=gate,
        ),
        "workspace_path": gate.get("workspace_path"),
        "requested_workflow_id": workflow_id,
        "requested_adapter": adapter,
        "profile_source_path": gate.get("profile_source_path"),
        "dispatch_gate_cleared": bool(gate.get("dispatch_gate_cleared")),
        "dispatch_gate_packet_id": gate.get("dispatch_gate_packet_id"),
        "live_execution_approval_required": True,
        "live_execution_approved": False,
        "aor_dispatch_enabled": False,
        "run_workflow_called": False,
        "run_workflow_live_called": False,
        "run_workflow_dry_run": False,
        "workflow_execution_performed": False,
        "workflow_writeback_performed": False,
        "agent_bus_task_written": False,
        "approval_consumed": False,
        "provider_or_model_call_performed": False,
        "browser_or_external_action_performed": False,
        "external_action_performed": False,
        "canonical_write_performed": False,
        "blockers": blockers,
        "dispatch_gate": gate,
        "approval_artifact_preview": artifact_payload,
        "future_executor_requirements": artifact_payload["future_executor_requirements"],
        "future_executor_command_preview": (
            "python -m runtime.cli.main runtime workspace-mode live-executor "
            f"--workspace-path {gate.get('workspace_path')} --workflow-id {workflow_id} "
            f"--adapter {adapter} --gate-approval-id {request_id} --confirm --json"
        ),
        "next_recommended_pass": (
            "workspace-mode-aor-live-executor-approval-decision-or-consumption-gate"
            if ok
            else "resolve-workspace-mode-aor-live-execution-approval-blockers"
        ),
    }


def format_workspace_mode_aor_live_execution_approval_gate(payload: dict[str, Any]) -> str:
    blockers = payload.get("blockers") or []
    lines = [
        "Workspace Mode AOR live-execution approval gate",
        f"  workspace_path:       {payload.get('workspace_path') or payload.get('dispatch_gate', {}).get('workspace_path')}",
        f"  workflow_id:          {payload.get('requested_workflow_id') or payload.get('dispatch_gate', {}).get('requested_workflow_id')}",
        f"  dispatch_gate_cleared:{payload.get('dispatch_gate_cleared')}",
        f"  approval_packet_id:   {payload.get('approval_packet_id')}",
        f"  ready_for_decision:   {payload.get('ready_for_operator_decision')}",
        f"  request_written:      {payload.get('approval_request_written')}",
        f"  artifact_path:        {payload.get('approval_artifact_path')}",
        f"  blockers:             {', '.join(blockers) if blockers else '(none)'}",
        "  boundary: approval request only; no live run_workflow call, workflow execution, writeback, Agent Bus task, approval consumption, external action, or canonical writeback.",
        "  operator approval text:",
        payload.get("operator_confirmation_text") or "",
    ]
    if payload.get("dispatch_gate") and not payload.get("dispatch_gate_cleared"):
        lines.append("")
        lines.append(format_workspace_mode_aor_dispatch_gate(payload["dispatch_gate"]))
    return "\n".join(lines)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m runtime.workspace_modes.aor_live_execution_approval_gate",
        description="Build or write a pending WML live AOR execution approval request.",
    )
    parser.add_argument("--workspace-path", required=True, metavar="PATH")
    parser.add_argument("--workflow-id", required=True, metavar="WORKFLOW_ID")
    parser.add_argument("--adapter", default="codex", metavar="ADAPTER")
    parser.add_argument("--profile", dest="profile_path", default=None, metavar="PATH")
    parser.add_argument("--vault-root", default=None, metavar="PATH")
    parser.add_argument("--requested-by", default="operator", metavar="NAME")
    parser.add_argument("--approval-packet-id", default=None, metavar="ID")
    parser.add_argument("--write-approval-request", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--json", action="store_true", dest="output_json")
    args = parser.parse_args(argv)

    payload = build_workspace_mode_aor_live_execution_approval_gate(
        workspace_path=args.workspace_path,
        workflow_id=args.workflow_id,
        adapter=args.adapter,
        vault_root=args.vault_root,
        profile_path=args.profile_path,
        requested_by=args.requested_by,
        approval_packet_id=args.approval_packet_id,
        write_approval_request=args.write_approval_request,
        confirm=args.confirm,
    )
    if args.output_json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_workspace_mode_aor_live_execution_approval_gate(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(_main())
