"""Evidence-backed VentureOps workflow recommendation engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .instance_profile import build_instance_profile
from .models import WorkflowRecommendation
from .registry import load_use_case_registry, workflow_by_id


DOMAIN_TO_WORKFLOWS: dict[str, tuple[str, ...]] = {
    "visual_product_creative": ("growth_studio_proof_pack",),
    "creator_content": ("creator_content_to_market_batch",),
    "client_services": ("client_fulfillment_pipeline", "fullstack_build_to_proof_sprint"),
    "jobs_career": ("job_application_pack",),
    "university": ("university_portfolio_os",),
    "research_to_product": ("research_to_product_intelligence",),
    "runtime_governance": ("agent_runtime_governance_audit", "ai_engineering_workflow_lab"),
    "crypto_trading": ("tradesync_strikezone_supply_engine",),
    "ecommerce_reselling": ("ecommerce_reselling_ops",),
    "game_prototype": ("game_prototype_from_brief",),
    "founder_automation": ("founder_automation_audit",),
    "delegation": ("delegation_mesh",),
    "ai_engineering": ("ai_engineering_workflow_lab",),
    "fullstack_build": ("fullstack_build_to_proof_sprint",),
}

CRYPTO_WORKFLOWS = {"tradesync_strikezone_supply_engine"}

DOMAIN_TO_MISSION_ROLES: dict[str, tuple[str, ...]] = {
    "runtime_governance": ("mission_supervisor", "planner", "security_reviewer", "critic_validator", "presenter"),
    "creator_content": ("mission_supervisor", "planner", "growth_operator", "researcher", "critic_validator", "presenter"),
    "client_services": ("mission_supervisor", "planner", "tool_operator", "critic_validator", "presenter"),
    "jobs_career": ("mission_supervisor", "planner", "career_operator", "researcher", "critic_validator", "presenter"),
    "university": ("mission_supervisor", "planner", "researcher", "critic_validator", "presenter"),
    "ecommerce_reselling": ("mission_supervisor", "planner", "commerce_operator", "tool_operator", "critic_validator", "presenter"),
    "crypto_trading": ("mission_supervisor", "planner", "researcher", "critic_validator", "security_reviewer", "presenter"),
    "ai_engineering": ("mission_supervisor", "planner", "researcher", "runtime_operator", "critic_validator", "presenter"),
    "fullstack_build": ("mission_supervisor", "planner", "runtime_operator", "critic_validator", "presenter"),
}


def _record_text(record: dict[str, Any], *keys: str) -> str:
    parts: list[str] = []
    for key in keys:
        value = record.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
    return " ".join(parts)


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _recommendation_from_record(
    record: dict[str, Any],
    *,
    domain: str,
    confidence: float,
    evidence_files: list[str],
) -> WorkflowRecommendation:
    runtime_surfaces = _as_list(record.get("runtime_surfaces")) or _as_list(record.get("required_runtime_surfaces"))
    approval_requirements = _as_list(record.get("approval_requirements"))
    risks = _as_list(record.get("risk_notes")) + _as_list(record.get("safety"))
    status = str(record.get("status") or "DOCS-ONLY")
    readiness = str(record.get("default_readiness_level") or "needs_inputs")
    why = f"Matched local {domain} evidence in {len(evidence_files)} file(s); recommendation remains draft until a manifest/proof run exists."
    return WorkflowRecommendation(
        workflow_id=str(record.get("workflow_id")),
        workflow_name=str(record.get("name") or record.get("workflow_id")),
        target_user_or_customer=str(record.get("target_user_or_customer") or record.get("customer") or "operator-selected user/customer"),
        domain=domain,
        problem_solved=str(record.get("purpose") or record.get("problem") or "convert repeated local work into a governed workflow pack"),
        why_suggested=why,
        evidence_files=evidence_files,
        confidence_score=min(0.95, confidence),
        required_inputs=_as_list(record.get("required_inputs")),
        required_context=_as_list(record.get("required_context")),
        required_runtime_surfaces=runtime_surfaces,
        approval_requirements=approval_requirements,
        expected_outputs=_as_list(record.get("expected_outputs")),
        proof_artifact=str(record.get("proof_artifact") or "07_LOGS/Workflow-Proofs/<run>.md"),
        monetization_path=str(record.get("monetization_path") or record.get("monetization_model") or "draft offer/case-study path"),
        risks=risks,
        first_safe_next_step=str(record.get("first_safe_next_step") or "draft a workflow pack manifest with evidence references"),
        readiness_level=readiness,
        status=status,
    )


def build_recommendations(
    vault_root: str | Path,
    *,
    max_recommendations: int = 10,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build draft workflow recommendations from local instance evidence."""
    root = Path(vault_root).resolve()
    instance_profile = profile or build_instance_profile(root)
    registry = load_use_case_registry(root)
    records = workflow_by_id(registry)
    mode = instance_profile.get("workspace_mode")
    if mode == "unknown_sparse":
        return {
            "ok": True,
            "status": "insufficient_evidence",
            "workspace_mode": mode,
            "recommendations": [],
            "discovery_questions": instance_profile.get("discovery_questions", []),
            "authority_boundary": {
                "read_only": True,
                "draft_recommendations_only": True,
                "external_sends_allowed": False,
                "live_trading_allowed": False,
                "provider_calls_allowed": False,
            },
        }

    recommendations: list[WorkflowRecommendation] = []
    for signal in instance_profile.get("detected_domains", []):
        if not isinstance(signal, dict):
            continue
        domain = str(signal.get("domain") or "")
        evidence_files = [str(item.get("path")) for item in signal.get("evidence", []) if isinstance(item, dict) and item.get("path")]
        for workflow_id in DOMAIN_TO_WORKFLOWS.get(domain, ()):
            if workflow_id in CRYPTO_WORKFLOWS and domain != "crypto_trading":
                continue
            record = records.get(workflow_id)
            if record is None:
                continue
            recommendations.append(
                _recommendation_from_record(
                    record,
                    domain=domain,
                    confidence=float(signal.get("confidence") or 0.0),
                    evidence_files=evidence_files,
                )
            )

    recommendations.sort(
        key=lambda item: (
            -item.confidence_score,
            item.workflow_id,
        )
    )
    deduped: list[WorkflowRecommendation] = []
    seen: set[str] = set()
    for item in recommendations:
        if item.workflow_id in seen:
            continue
        seen.add(item.workflow_id)
        deduped.append(item)
        if len(deduped) >= max_recommendations:
            break

    return {
        "ok": True,
        "status": "draft_recommendations",
        "workspace_mode": mode,
        "recommendations": [item.to_dict() for item in deduped],
        "discovery_questions": instance_profile.get("discovery_questions", []),
        "crypto_trading_policy": {
            "optional_domain_pack": True,
            "recommended_only_with_instance_evidence": True,
            "live_trading_allowed": False,
            "default_mode": "analysis_draft_paper_proof",
        },
        "authority_boundary": {
            "read_only": True,
            "draft_recommendations_only": True,
            "external_sends_allowed": False,
            "live_trading_allowed": False,
            "provider_calls_allowed": False,
            "credential_or_secret_reads_allowed": False,
        },
    }


def _slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned or "mission"


def _mission_roles_for_domain(domain: str) -> list[str]:
    return list(DOMAIN_TO_MISSION_ROLES.get(domain, ("mission_supervisor", "planner", "researcher", "critic_validator", "presenter")))


def _mission_recommendation_from_workflow(recommendation: dict[str, Any]) -> dict[str, Any]:
    workflow_id = str(recommendation.get("workflow_id") or "")
    domain = str(recommendation.get("domain") or "general")
    evidence_files = [str(item) for item in recommendation.get("evidence_files") or [] if str(item)]
    risk_class = "standard"
    if domain == "crypto_trading" or workflow_id in CRYPTO_WORKFLOWS:
        risk_class = "financial_high_review"
    elif any(term in " ".join(recommendation.get("risks") or []).lower() for term in ("payment", "external", "credential")):
        risk_class = "external_effects_review"
    return {
        "mission_candidate_id": f"mission-{_slug(workflow_id)}",
        "mission_name": f"{recommendation.get('workflow_name') or workflow_id} Mission",
        "target_domain": domain,
        "target_user": recommendation.get("target_user_or_customer") or "operator-selected user/customer",
        "objective": recommendation.get("problem_solved") or "turn a repeated workflow into a governed long-running mission",
        "why_suggested": recommendation.get("why_suggested") or "local evidence matched this workflow family",
        "evidence_files": evidence_files,
        "confidence_score": recommendation.get("confidence_score", 0.0),
        "recommended_workflow_packs": [workflow_id],
        "recommended_sub_agents": _mission_roles_for_domain(domain),
        "required_inputs": list(recommendation.get("required_inputs") or []),
        "required_context": list(recommendation.get("required_context") or []),
        "required_integrations": list(recommendation.get("required_runtime_surfaces") or []),
        "approval_requirements": sorted(
            {
                "workflow_evolution_activation",
                "external_sends",
                "protected_file_edits",
                *[str(item) for item in recommendation.get("approval_requirements") or []],
            }
        ),
        "risk_class": risk_class,
        "first_safe_next_step": recommendation.get("first_safe_next_step") or "draft a mission manifest with evidence references",
        "readiness_level": recommendation.get("readiness_level") or "needs_inputs",
        "authority_boundary": {
            "recommendation_only": True,
            "creates_mission_state": False,
            "runs_workflows": False,
            "external_sends_allowed": False,
            "payment_mutation_allowed": False,
            "live_trading_allowed": False,
            "browser_skill_activation_allowed": False,
            "workflow_evolution_auto_apply_allowed": False,
        },
    }


def build_mission_recommendations(
    vault_root: str | Path,
    *,
    max_recommendations: int = 10,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build evidence-backed draft Mission Mode candidates from local workspace signals.

    This is recommendation-only. It does not create mission state, enqueue Agent Bus
    tasks, invoke AOR, call providers, or authorize external side effects.
    """
    workflow_result = build_recommendations(vault_root, max_recommendations=max_recommendations, profile=profile)
    if workflow_result.get("status") == "insufficient_evidence":
        return {
            "ok": True,
            "status": "insufficient_evidence",
            "workspace_mode": workflow_result.get("workspace_mode"),
            "mission_recommendations": [],
            "discovery_questions": workflow_result.get("discovery_questions", []),
            "authority_boundary": {
                "read_only": True,
                "draft_recommendations_only": True,
                "creates_mission_state": False,
                "runs_workflows": False,
                "external_sends_allowed": False,
                "live_trading_allowed": False,
                "provider_calls_allowed": False,
            },
        }

    mission_recommendations = [
        _mission_recommendation_from_workflow(item)
        for item in workflow_result.get("recommendations", [])
        if isinstance(item, dict) and item.get("evidence_files")
    ]
    return {
        "ok": True,
        "status": "draft_mission_recommendations",
        "workspace_mode": workflow_result.get("workspace_mode"),
        "mission_recommendations": mission_recommendations[:max_recommendations],
        "discovery_questions": workflow_result.get("discovery_questions", []),
        "crypto_trading_policy": {
            "optional_domain_pack": True,
            "recommended_only_with_instance_evidence": True,
            "default_mode": "analysis_journal_paper_risk_review",
            "live_trading_allowed": False,
            "financial_action_requires_human_approval": True,
        },
        "authority_boundary": {
            "read_only": True,
            "draft_recommendations_only": True,
            "creates_mission_state": False,
            "runs_workflows": False,
            "external_sends_allowed": False,
            "payment_mutation_allowed": False,
            "live_trading_allowed": False,
            "provider_calls_allowed": False,
            "credential_or_secret_reads_allowed": False,
            "browser_skill_activation_allowed": False,
        },
    }
