"""Proof-card generation for local/demo WorkflowPack runs."""

from __future__ import annotations

import uuid
from typing import Any

from .models import ApprovalGate, ProofCard, WorkflowArtifact, WorkflowPack, WorkflowRun, utc_now


def build_proof_card(
    *,
    pack: WorkflowPack,
    run: WorkflowRun,
    artifacts: list[WorkflowArtifact],
    approval_gates: list[ApprovalGate],
) -> ProofCard:
    pending_gates = [gate for gate in approval_gates if gate.status == "pending"]
    blocked_flags = [flag for flag in run.risk_flags if flag.blocked]
    user_goal = str(run.input.get("user_goal") or run.title)
    return ProofCard(
        id=f"proof-{uuid.uuid4().hex[:12]}",
        run_id=run.id,
        pack_id=pack.id,
        title=f"Proof Card: {run.title}",
        created_at=utc_now(),
        status="review_required",
        user_goal=user_goal,
        input_summary=_summarize_input(run.input),
        workflow_summary=(
            f"{pack.name} ran in local demo/manual provider mode. "
            "No external provider, browser, email, publishing, or live runtime execution was used."
        ),
        outputs_summary=f"{len(artifacts)} local artifact(s) generated for operator review.",
        artifact_refs=run.artifact_refs,
        source_refs=run.source_refs,
        runtime_trace={
            "reasoning": "manual_provider",
            "execution": "local_service_demo",
            "ui": "studio_workflow_packs_panel",
            "external_action_taken": False,
        },
        approval_summary={
            "approval_required": bool(pending_gates),
            "pending_gate_count": len(pending_gates),
            "approved_gate_count": len([gate for gate in approval_gates if gate.status == "approved"]),
            "pending_action_types": [gate.action_type for gate in pending_gates],
        },
        risk_summary={
            "risk_flags": [flag.to_dict() for flag in run.risk_flags],
            "blocked_risk_count": len(blocked_flags),
            "public_share_safe": False,
        },
        metrics={
            "artifact_count": len(artifacts),
            "source_count": len(run.source_refs),
            "approval_gate_count": len(approval_gates),
            "demo_manual_provider": True,
        },
        public_share_mode="redacted",
        before_state={"status": "manual_goal_entered"},
        after_state={"status": "artifacts_ready_for_review"},
    )


def render_proof_card_markdown(card: ProofCard, pack: WorkflowPack) -> str:
    approval = card.approval_summary
    risk = card.risk_summary
    artifacts = "\n".join(
        f"- {ref.title} ({ref.artifact_type}) - {ref.local_path}" for ref in card.artifact_refs
    ) or "- None"
    pending_actions = ", ".join(approval.get("pending_action_types") or []) or "none"
    return "\n".join(
        [
            f"# {card.title}",
            "",
            "## Goal",
            card.user_goal,
            "",
            "## Workflow Pack",
            f"{pack.name} v{pack.version}",
            "",
            "## Input Summary",
            card.input_summary,
            "",
            "## Workflow Summary",
            card.workflow_summary,
            "",
            "## Outputs",
            artifacts,
            "",
            "## Human Approval",
            f"- Approval required: {str(bool(approval.get('approval_required'))).lower()}",
            f"- Pending gates: {approval.get('pending_gate_count', 0)}",
            f"- Pending action types: {pending_actions}",
            "",
            "## Safety / Risk",
            "- External action taken: false",
            f"- Public share safe: {str(bool(risk.get('public_share_safe'))).lower()}",
            f"- Blocked risk count: {risk.get('blocked_risk_count', 0)}",
            "",
            "## Metrics",
            f"- Artifacts generated: {card.metrics.get('artifact_count', 0)}",
            f"- Approval gates recorded: {card.metrics.get('approval_gate_count', 0)}",
            "",
            "## Review Status",
            card.status,
            "",
        ]
    )


def _summarize_input(data: dict[str, Any]) -> str:
    goal = str(data.get("user_goal") or "").strip()
    if goal:
        return f"Manual user goal supplied: {goal}"
    return "Manual/demo input supplied; no external sources were read."
