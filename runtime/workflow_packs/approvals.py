"""Approval helpers for Workflow Packs.

Workflow Packs record local gates for high-risk/external actions. The approved
local resume executor may consume a scoped gate decision, but provider, browser,
email, publish, runtime, Agent Bus, graph/canonical, and policy executors remain
separate authority surfaces.
"""

from __future__ import annotations

from typing import Any

from .models import ApprovalActionType, ApprovalGate


HIGH_RISK_ACTIONS: frozenset[str] = frozenset(
    {
        "send_email",
        "publish_content",
        "browser_action",
        "runtime_execution",
        "agent_policy_change",
        "graph_promotion",
        "external_api_call",
    }
)


def requires_approval(action_type: str) -> bool:
    return action_type in HIGH_RISK_ACTIONS or action_type == "write_file"


def action_allowed(action_type: ApprovalActionType, gates: list[ApprovalGate]) -> dict[str, Any]:
    if not requires_approval(action_type):
        return {
            "allowed": True,
            "blocked": False,
            "action_type": action_type,
            "reason": "approval_not_required_for_local_demo_action",
        }
    approved = [gate for gate in gates if gate.action_type == action_type and gate.status == "approved"]
    if approved:
        return {
            "allowed": True,
            "blocked": False,
            "action_type": action_type,
            "approval_gate_ids": [gate.id for gate in approved],
            "reason": "approved_gate_present",
        }
    pending = [gate for gate in gates if gate.action_type == action_type and gate.status == "pending"]
    return {
        "allowed": False,
        "blocked": True,
        "action_type": action_type,
        "approval_gate_ids": [gate.id for gate in pending],
        "reason": "human_approval_required_before_external_or_sensitive_action",
    }
