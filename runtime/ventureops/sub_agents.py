"""Sub-agent planning helpers for VentureOps Mission Mode."""

from __future__ import annotations

from typing import Any


MISSION_MODE_FORBIDDEN_ACTIONS = [
    "external_sends",
    "purchases",
    "listings",
    "payments",
    "live_trading",
    "protected_file_edits",
    "credential_reads",
    "browser_skill_activation",
    "provider_config_mutation",
    "canonical_promotion",
]


DEFAULT_SUB_AGENT_ROLES: dict[str, dict[str, Any]] = {
    "mission_supervisor": {
        "responsibility": "Maintain mission continuity, pass planning, blocker escalation, and mission review summaries.",
        "runtime_preference": "hermes",
        "authority": "advisory",
        "allowed_outputs": ["mission_review", "pass_plan", "blocker_report"],
    },
    "planner": {
        "responsibility": "Decompose objectives, choose workflow packs, sequence dependencies, and draft pass plans.",
        "runtime_preference": "strong_model",
        "authority": "proposal_only",
        "allowed_outputs": ["pass_plan", "workflow_pack_selection", "dependency_map"],
    },
    "researcher": {
        "responsibility": "Read source packs, retrieve evidence, summarize inputs, and propose knowledge updates.",
        "runtime_preference": "hermes",
        "authority": "advisory",
        "allowed_outputs": ["source_summary", "evidence_digest", "missing_context_report"],
    },
    "tool_operator": {
        "responsibility": "Prepare approved browser, SaaS, file, or workflow action proposals within declared scope.",
        "runtime_preference": "openclaw_or_browser_runtime",
        "authority": "approval_gated_execution",
        "allowed_outputs": ["browser_run_log", "screenshot_artifact", "site_profile_candidate"],
    },
    "critic_validator": {
        "responsibility": "Review assumptions, score outputs, detect missing evidence, and validate safety boundaries.",
        "runtime_preference": "strong_model",
        "authority": "review_only",
        "allowed_outputs": ["scorecard", "failure_analysis", "evolution_risk_review"],
    },
    "security_reviewer": {
        "responsibility": "Evaluate permissions, side effects, secrets risk, prompt injection, and runtime/browser control risk.",
        "runtime_preference": "strong_model",
        "authority": "review_only",
        "allowed_outputs": ["permission_review", "risk_review", "blocked_action_report"],
    },
    "growth_operator": {
        "responsibility": "Review content-to-market workflows, CTA quality, funnel signals, and conversion evidence.",
        "runtime_preference": "hermes",
        "authority": "proposal_only",
        "allowed_outputs": ["growth_review", "cta_review", "funnel_hypothesis"],
    },
    "commerce_operator": {
        "responsibility": "Analyze sourcing, pricing, listing drafts, and profit/risk evidence without purchase authority.",
        "runtime_preference": "hermes",
        "authority": "proposal_only",
        "allowed_outputs": ["pricing_review", "listing_draft", "margin_risk_review"],
    },
    "career_operator": {
        "responsibility": "Draft job/internship application packs, fit reviews, and follow-up plans without submission authority.",
        "runtime_preference": "hermes",
        "authority": "proposal_only",
        "allowed_outputs": ["application_pack", "fit_score", "follow_up_plan"],
    },
    "runtime_operator": {
        "responsibility": "Review runtime readiness, provider posture, workflow dispatch readiness, and failure logs.",
        "runtime_preference": "codex",
        "authority": "review_only",
        "allowed_outputs": ["runtime_readiness_report", "failure_summary", "fallback_recommendation"],
    },
    "presenter": {
        "responsibility": "Package user-facing summaries, proof cards, client-safe reports, and final handoffs.",
        "runtime_preference": "hermes",
        "authority": "advisory",
        "allowed_outputs": ["proof_card", "client_safe_report", "final_handoff"],
    },
}


def build_sub_agent_plan(
    mission_id: str,
    roles: list[str] | None = None,
    *,
    version: str = "0.1",
) -> dict[str, Any]:
    selected_roles = roles or ["mission_supervisor", "planner", "researcher", "critic_validator", "presenter"]
    sub_agents: list[dict[str, Any]] = []
    for role in selected_roles:
        profile = DEFAULT_SUB_AGENT_ROLES.get(role)
        if profile is None:
            sub_agents.append(
                {
                    "role": role,
                    "responsibility": "Unknown role; fail closed until a role card or mission-local assignment is reviewed.",
                    "runtime_preference": "unknown",
                    "authority": "blocked",
                    "allowed_outputs": [],
                    "forbidden_actions": list(MISSION_MODE_FORBIDDEN_ACTIONS),
                    "handoff_requirements": ["operator_review_required"],
                    "review_requirements": ["unknown_role_definition"],
                }
            )
            continue
        sub_agents.append(
            {
                "role": role,
                "responsibility": profile["responsibility"],
                "runtime_preference": profile["runtime_preference"],
                "authority": profile["authority"],
                "allowed_outputs": list(profile["allowed_outputs"]),
                "forbidden_actions": list(MISSION_MODE_FORBIDDEN_ACTIONS),
                "handoff_requirements": ["write structured artifact", "cite evidence", "escalate blockers"],
                "review_requirements": ["mission supervisor review", "critic/validator review for risky outputs"],
            }
        )
    return {
        "schema_version": "0.1",
        "mission_id": mission_id,
        "version": version,
        "sub_agents": sub_agents,
        "permission_rule": "Sub-agent assignment never expands runtime authority; each task still needs AOR/Gate/Agent Bus scope.",
    }
