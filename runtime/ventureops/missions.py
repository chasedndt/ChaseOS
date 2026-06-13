"""Mission manifest helpers for VentureOps Mission Mode."""

from __future__ import annotations

from datetime import date
from typing import Any

from .sub_agents import MISSION_MODE_FORBIDDEN_ACTIONS, build_sub_agent_plan


MISSION_APPROVAL_REQUIREMENTS = [
    "external_sends",
    "purchases",
    "listings",
    "payments",
    "live_trading",
    "protected_file_edits",
    "credential_access",
    "browser_actions_with_external_effect",
    "browser_skill_activation",
    "provider_config_mutation",
    "workflow_evolution_activation",
    "canonical_promotion",
]


def build_mission_manifest(
    *,
    mission_id: str,
    name: str,
    owner: str,
    objective: str,
    domain: str,
    target_user: str,
    workflow_packs: list[dict[str, Any]],
    sub_agent_roles: list[str] | None = None,
    success_metric: str = "operator-defined success metric required before activation",
    risk_class: str = "standard",
) -> dict[str, Any]:
    today = date.today().isoformat()
    sub_agent_plan = build_sub_agent_plan(mission_id, roles=sub_agent_roles)
    return {
        "schema_version": "0.1",
        "mission_id": mission_id,
        "name": name,
        "version": "0.1",
        "owner": owner,
        "instance_id": "operator-selected",
        "status": "draft",
        "created": today,
        "updated": today,
        "objective": objective,
        "domain": domain,
        "target_user": target_user,
        "success_metric": success_metric,
        "time_horizon": "long_running",
        "capital_or_resource_constraints": ["operator-defined budget/time constraints required before activation"],
        "risk_class": risk_class,
        "mission_mode": {
            "adaptive": True,
            "auto_apply_evolution": False,
            "approval_required_for_evolution": True,
        },
        "workflow_packs": workflow_packs,
        "sub_agents": sub_agent_plan["sub_agents"],
        "runtime_split": {
            "hermes": ["mission_supervisor", "planner", "researcher", "presenter"],
            "codex": ["runtime_operator", "implementation_scaffolding"],
            "browser_runtime": ["tool_operator"],
            "local_runtime": ["deterministic_validation"],
            "human": ["approval", "external_effects", "canonical_promotion"],
        },
        "required_inputs": ["mission objective", "domain goal profile", "approval policy"],
        "required_context": ["VentureOps architecture", "workflow registry", "role cards", "permission matrix"],
        "allowed_tools": ["deterministic_markdown_scan", "schema_validation", "proposal_drafting"],
        "forbidden_tools": list(MISSION_MODE_FORBIDDEN_ACTIONS),
        "approval_required_for": list(MISSION_APPROVAL_REQUIREMENTS),
        "writeback_targets": ["07_LOGS/VentureOps-Missions/", "07_LOGS/Mission-Reviews/"],
        "proof_artifact_targets": ["07_LOGS/Workflow-Proofs/"],
        "audit_targets": ["07_LOGS/Agent-Activity/"],
        "scorecard": {
            "status": "not_scored",
            "required_before_evolution": True,
            "scorecard_artifact_required": True,
        },
        "failure_behavior": "fail_closed_and_request_operator_review",
        "review_cadence": "operator-selected cadence; default weekly for active missions",
        "evolution_policy": {
            "allow_proposals": True,
            "allow_dry_run": True,
            "allow_auto_apply": False,
            "required_approvals": ["human_approval", "gate_review", "mission_owner_acceptance"],
        },
        "unsafe_boundaries": list(MISSION_MODE_FORBIDDEN_ACTIONS),
        "notes": "Draft Mission Mode manifest only; does not authorize execution.",
    }
