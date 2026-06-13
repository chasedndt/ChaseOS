"""Workflow evolution proposal helpers for VentureOps Mission Mode."""

from __future__ import annotations

from typing import Any


def build_workflow_evolution_proposal(
    *,
    proposal_id: str,
    mission_id: str,
    workflow_id: str,
    current_version: str,
    proposed_version: str,
    proposal_type: str,
    reason: str,
    dry_run_plan: str,
    evidence: dict[str, Any] | None = None,
    expected_benefit: str = "",
    risk_review: str = "",
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "proposal_id": proposal_id,
        "mission_id": mission_id,
        "workflow_id": workflow_id,
        "current_workflow_version": current_version,
        "proposed_workflow_version": proposed_version,
        "proposal_type": proposal_type,
        "reason": reason,
        "evidence": evidence or {"proof_cards": [], "run_logs": [], "scorecards": [], "source_files": []},
        "risk_review": risk_review or "Risk review required before approval.",
        "expected_benefit": expected_benefit or "Expected benefit not yet proven.",
        "failure_mode": "Proposal could reduce quality or expand authority if applied without review.",
        "dry_run_plan": dry_run_plan,
        "approval_required": True,
        "auto_apply_allowed": False,
        "status": "draft",
        "evidence_backed": False,
        "review_runtime": "strong_model",
        "authority_boundary": {
            "proposal_only": True,
            "applies_workflow_change": False,
            "requires_human_approval": True,
        },
    }
