"""Mission state ledger helpers for VentureOps Mission Mode."""

from __future__ import annotations

from datetime import date
from typing import Any


def build_initial_mission_state(
    *,
    mission_id: str,
    current_phase: str = "draft",
    next_recommended_pass: str = "draft-mission-manifest",
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "mission_id": mission_id,
        "current_status": "draft",
        "current_phase": current_phase,
        "active_workflow_versions": [],
        "last_run_id": "",
        "last_review_date": date.today().isoformat(),
        "progress_summary": "Mission created as a draft; no execution pass has run.",
        "scorecard_summary": {"status": "not_scored", "latest_score": None, "trend": "none"},
        "active_hypotheses": [],
        "active_blockers": ["mission_manifest_not_approved", "first_pass_not_run"],
        "pending_approvals": [],
        "approved_evolutions": [],
        "rejected_evolutions": [],
        "next_recommended_pass": next_recommended_pass,
        "evidence_links": [],
        "proof_cards": [],
        "audit_links": [],
        "authority_boundary": {
            "mission_local_state_only": True,
            "does_not_replace_project_truth": True,
            "workflow_evolution_auto_apply_allowed": False,
        },
    }
