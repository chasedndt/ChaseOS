"""Studio-facing read model for Workflow Packs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .approvals import HIGH_RISK_ACTIONS
from .approval_resume_contract import (
    build_approval_resume_contract,
    build_approval_resume_contract_summary,
)
from .approval_consumption_dry_run import build_approval_consumption_dry_run
from .approval_marker_reservation import build_approval_marker_reservation
from .approval_review_artifact import build_approval_review_artifact
from .approved_local_resume_executor import build_approved_local_resume_executor
from .agent_governance import (
    QUESTIONNAIRE_FIELDS as AGENT_GOVERNANCE_QUESTIONNAIRE_FIELDS,
)
from .agent_governance import create_agent_governance_run as create_agent_governance_run_service
from .automation_audit import (
    QUESTIONNAIRE_FIELDS as AUTOMATION_AUDIT_QUESTIONNAIRE_FIELDS,
)
from .automation_audit import create_automation_audit_run as create_automation_audit_run_service
from .creative_studio import (
    QUESTIONNAIRE_FIELDS as CREATIVE_STUDIO_QUESTIONNAIRE_FIELDS,
)
from .creative_studio import create_creative_studio_run as create_creative_studio_run_service
from .demo_provider import create_demo_workflow_run
from .research_intelligence import (
    QUESTIONNAIRE_FIELDS as RESEARCH_INTELLIGENCE_QUESTIONNAIRE_FIELDS,
)
from .research_intelligence import create_research_intelligence_run as create_research_intelligence_run_service
from .registry import registry_summary
from .store import WorkflowPackStore


_AUTHORITY = {
    "read_only": False,
    "local_artifact_write_allowed": True,
    "local_demo_run_write_allowed": True,
    "approval_review_artifact_write_allowed": True,
    "exact_once_marker_write_allowed": True,
    "approved_local_resume_write_allowed": True,
    "external_actions_allowed": False,
    "provider_calls_allowed": False,
    "model_calls_allowed": False,
    "browser_actions_allowed": False,
    "agent_bus_task_write_allowed": False,
    "runtime_dispatch_allowed": False,
    "workflow_execution_allowed": False,
    "approval_consumption_direct_allowed": False,
    "graph_mutation_allowed": False,
    "canonical_mutation_allowed": False,
    "external_delivery_allowed": False,
}


def _mission_operating_context(
    *,
    pack_count: int,
    run_count: int,
    review_count: int,
    proof_count: int,
    state_root: Path,
) -> dict[str, Any]:
    return {
        "title": "Mission Operating Context",
        "description": (
            "Local mission packs for turning operator intent into reviewable "
            "outputs, result cards, and governed local resume records."
        ),
        "source": "Local mission library, saved missions, review queue, and result cards",
        "safe_action": (
            "Create local mission records and inspect review gates. Starting agents, "
            "sending externally, changing memory, or promoting graph records "
            "stays behind separate governed approvals."
        ),
        "state_root": str(state_root),
        "cards": [
            {
                "label": "Mission packs",
                "value": pack_count,
                "note": "Automation, creative, research, and agent governance",
                "status": "local-ready",
            },
            {
                "label": "Local runs",
                "value": run_count,
                "note": "saved mission outputs in the local store",
                "status": "local-artifacts",
            },
            {
                "label": "Review queue",
                "value": review_count,
                "note": "artifacts and approval gates waiting for operator review",
                "status": "review-gated",
            },
            {
                "label": "Result cards",
                "value": proof_count,
                "note": "shareable local evidence summaries",
                "status": "evidence",
            },
        ],
    }


def _mission_readiness(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": (
            "Mission packs can create local artifacts and complete the existing "
            "review/resume chain. Live external work remains blocked."
        ),
        "rows": [
            {
                "label": "Pack registry",
                "status": "ready" if summary.get("pack_count") else "blocked",
                "note": "Four user-facing mission packs are registered.",
            },
            {
                "label": "Local run and artifact store",
                "status": "ready" if summary.get("demo_manual_provider_ready") else "blocked",
                "note": "Creates saved local mission outputs and result cards only.",
            },
            {
                "label": "Operator decision protection",
                "status": "ready"
                if summary.get("approval_review_artifact_writer_ready")
                and summary.get("approval_marker_reservation_ready")
                else "blocked",
                "note": "Local decisions are scoped to one mission gate and protected from repeat use.",
            },
            {
                "label": "Approved local resume",
                "status": "ready" if summary.get("approved_local_resume_executor_ready") else "blocked",
                "note": "An approved local mission can resume and write result evidence.",
            },
            {
                "label": "External work",
                "status": "blocked",
                "note": "No provider call, browser action, runtime dispatch, Agent Bus write, CRM/payment, publication, or delivery is mounted.",
            },
        ],
    }


def _mission_feature_family_coverage() -> list[dict[str, str]]:
    return [
        {
            "family": "VentureOps / Missions",
            "capability": "Mission pack foundation",
            "product_surface": "Main / Missions",
            "status": "Available locally",
            "evidence": "Local catalog, saved mission records, review queue, and result cards.",
            "boundary": "Local output/result lane only; no external/client execution.",
        },
        {
            "family": "Missions",
            "capability": "Automation Audit, Creative Studio, Research Intelligence, Agent Governance Kit",
            "product_surface": "Main / Missions",
            "status": "Available locally",
            "evidence": "Four mission packs are available in the local mission catalog.",
            "boundary": "Pack outputs stay local; no provider, browser, or publication authority.",
        },
        {
            "family": "Governance",
            "capability": "Approval review, duplicate protection, and approved local resume",
            "product_surface": "Missions / Review Queue",
            "status": "Ready",
            "evidence": "Operator review, duplicate protection, and local resume records are wired.",
            "boundary": "Only one scoped local mission gate can be consumed; no generic approval consumption.",
        },
        {
            "family": "Autonomous Operator Runtime",
            "capability": "Mission outputs and result evidence",
            "product_surface": "Missions, Tasks & Runs, Logs / Audit",
            "status": "Available locally",
            "evidence": "Mission outputs and result cards are saved for review.",
            "boundary": "No workflow execution or runtime dispatch from Missions.",
        },
        {
            "family": "Workspace Mode Layer",
            "capability": "Mission-mode product framing",
            "product_surface": "Missions and Workspaces",
            "status": "Available locally",
            "evidence": "Missions appears as a primary product surface in Studio.",
            "boundary": "Mode framing does not grant new runtime or write authority.",
        },
    ]


def build_workflow_packs_panel(vault_root: str | Path) -> dict[str, Any]:
    store = WorkflowPackStore(vault_root)
    registry = registry_summary()
    runs = [run.to_dict() for run in store.list_runs()]
    approval_resume = build_approval_resume_contract_summary(vault_root)
    review_items: list[dict[str, Any]] = []
    proof_cards: list[dict[str, Any]] = []

    for run in store.list_runs():
        for artifact in run.artifact_refs:
            if artifact.review_status == "pending_review":
                review_items.append(
                    {
                        "kind": "artifact",
                        "run_id": run.id,
                        "pack_id": run.pack_id,
                        "item_id": artifact.id,
                        "title": artifact.title,
                        "status": artifact.review_status,
                        "path": artifact.local_path,
                    }
                )
        for gate in store.list_approval_gates(run.id):
            if gate.status == "pending":
                review_items.append(
                    {
                        "kind": "approval_gate",
                        "run_id": run.id,
                        "pack_id": run.pack_id,
                        "item_id": gate.id,
                        "title": gate.action_type,
                        "status": gate.status,
                        "path": f"runtime/workflow_packs/state/runs/{run.id}/approvals/{gate.id}.json",
                    }
                )
        proof_path = store.run_dir(run.id) / "proof" / "proof_card.json"
        if proof_path.exists():
            proof_cards.append(_safe_json(proof_path))

    return {
        "surface": "workflow_packs_panel",
        "status": "approval_resume_contract_ready",
        "summary": {
            "pack_count": registry["pack_count"],
            "run_count": len(runs),
            "review_queue_count": len(review_items),
            "proof_card_count": len(proof_cards),
            "demo_manual_provider_ready": True,
            "automation_audit_mvp_ready": True,
            "creative_studio_mvp_ready": True,
            "research_intelligence_mvp_ready": True,
            "agent_governance_mvp_ready": True,
            "approval_resume_contract_ready": True,
            "approval_review_artifact_writer_ready": True,
            "approval_consumption_dry_run_ready": True,
            "approval_consumption_exact_once_marker_dry_run_ready": True,
            "approval_marker_reservation_ready": True,
            "approved_local_resume_executor_ready": True,
            "approval_review_artifact_consumption_built": True,
            "approval_review_artifact_exact_once_marker_built": True,
            "approval_consumption_marker_writer_built": True,
            "approval_consumption_built": True,
            "resume_executor_built": True,
            "external_actions_blocked": True,
        },
        "authority": dict(_AUTHORITY),
        "operating_context": _mission_operating_context(
            pack_count=registry["pack_count"],
            run_count=len(runs),
            review_count=len(review_items),
            proof_count=len(proof_cards),
            state_root=store.state_root,
        ),
        "readiness": _mission_readiness(
            {
                "pack_count": registry["pack_count"],
                "demo_manual_provider_ready": True,
                "approval_review_artifact_writer_ready": True,
                "approval_marker_reservation_ready": True,
                "approved_local_resume_executor_ready": True,
            }
        ),
        "feature_family_coverage": _mission_feature_family_coverage(),
        "registry": registry,
        "runs": runs,
        "review_queue": review_items,
        "proof_cards": proof_cards,
        "new_run": {
            "default_pack_id": "founder_personal_automation_audit",
            "provider_mode": "demo_manual",
            "api_method": "create_workflow_pack_demo_run",
            "automation_audit_api_method": "create_automation_audit_run",
            "automation_audit_questionnaire_fields": [
                dict(field) for field in AUTOMATION_AUDIT_QUESTIONNAIRE_FIELDS
            ],
            "creative_studio_api_method": "create_creative_studio_run",
            "creative_studio_questionnaire_fields": [
                dict(field) for field in CREATIVE_STUDIO_QUESTIONNAIRE_FIELDS
            ],
            "research_intelligence_api_method": "create_research_intelligence_run",
            "research_intelligence_questionnaire_fields": [
                dict(field) for field in RESEARCH_INTELLIGENCE_QUESTIONNAIRE_FIELDS
            ],
            "agent_governance_api_method": "create_agent_governance_run",
            "agent_governance_questionnaire_fields": [
                dict(field) for field in AGENT_GOVERNANCE_QUESTIONNAIRE_FIELDS
            ],
            "approval_resume_contract_api_method": "get_workflow_pack_approval_resume_contract",
            "approval_review_artifact_api_method": "review_workflow_pack_approval_artifact",
            "approval_consumption_dry_run_api_method": "get_workflow_pack_approval_consumption_dry_run",
            "approval_marker_reservation_api_method": "reserve_workflow_pack_exact_once_marker",
            "approved_local_resume_executor_api_method": "execute_workflow_pack_approved_local_resume",
            "wizard_steps": [
                "choose_pack",
                "enter_goal",
                "answer_creative_studio_questionnaire_when_selected",
                "answer_automation_audit_questionnaire_when_selected",
                "answer_research_intelligence_questionnaire_when_selected",
                "answer_agent_governance_questionnaire_when_selected",
                "attach_sources_later",
                "configure_outputs",
                "review_permissions",
                "create_demo_run",
            ],
        },
        "approval_resume": approval_resume,
        "safety": {
            "approval_integration": "safe_local_stub_with_studio_approval_center_visibility_future",
            "high_risk_actions_blocked": sorted(HIGH_RISK_ACTIONS),
            "approval_resume_contract_preview_only": True,
            "approval_review_artifact_writer_available": True,
            "approval_consumption_dry_run_available": True,
            "approval_marker_reservation_available": True,
            "approved_local_resume_executor_available": True,
            "exact_once_marker_writer_available": True,
            "approval_review_artifact_consumption_performed": False,
            "approval_review_artifact_exact_once_marker_reserved": False,
            "approval_decision_consumption_performed": False,
            "exact_once_marker_reserved": False,
            "approval_consumption_performed": False,
            "resume_execution_performed": False,
            "external_actions_blocked": True,
            "external_actions_performed": False,
            "provider_calls_performed": False,
            "browser_actions_performed": False,
            "canonical_promotion_performed": False,
            "public_share_default": "redacted",
        },
        "state_root": str(store.state_root),
    }


def create_workflow_pack_demo_run(
    vault_root: str | Path,
    *,
    pack_id: str,
    title: str = "",
    user_goal: str = "",
) -> dict[str, Any]:
    return create_demo_workflow_run(vault_root, pack_id=pack_id, title=title, user_goal=user_goal)


def create_automation_audit_run(
    vault_root: str | Path,
    *,
    title: str = "",
    user_goal: str = "",
    work_domains: str = "",
    repeated_tasks: str = "",
    pain_points: str = "",
) -> dict[str, Any]:
    return create_automation_audit_run_service(
        vault_root,
        title=title,
        user_goal=user_goal,
        work_domains=work_domains,
        repeated_tasks=repeated_tasks,
        pain_points=pain_points,
    )


def create_creative_studio_run(
    vault_root: str | Path,
    *,
    title: str = "",
    user_goal: str = "",
    campaign_type: str = "",
    brand_profile: str = "",
    offer: str = "",
    audience: str = "",
    tone: str = "",
    channels: str = "",
    primary_cta: str = "",
) -> dict[str, Any]:
    return create_creative_studio_run_service(
        vault_root,
        title=title,
        user_goal=user_goal,
        campaign_type=campaign_type,
        brand_profile=brand_profile,
        offer=offer,
        audience=audience,
        tone=tone,
        channels=channels,
        primary_cta=primary_cta,
    )


def create_research_intelligence_run(
    vault_root: str | Path,
    *,
    title: str = "",
    user_goal: str = "",
    research_mode: str = "",
    source_material: str = "",
    source_urls: str = "",
    product_context: str = "",
    decision_goal: str = "",
    audience: str = "",
    output_focus: str = "",
) -> dict[str, Any]:
    return create_research_intelligence_run_service(
        vault_root,
        title=title,
        user_goal=user_goal,
        research_mode=research_mode,
        source_material=source_material,
        source_urls=source_urls,
        product_context=product_context,
        decision_goal=decision_goal,
        audience=audience,
        output_focus=output_focus,
    )


def create_agent_governance_run(
    vault_root: str | Path,
    *,
    title: str = "",
    user_goal: str = "",
    agent_name: str = "",
    runtime: str = "",
    runtime_status: str = "",
    tools: str = "",
    reads_from: str = "",
    writes_to: str = "",
    external_actions: str = "",
    permission_surfaces: str = "",
    workflow_manifest: str = "",
    approval_expectations: str = "",
) -> dict[str, Any]:
    return create_agent_governance_run_service(
        vault_root,
        title=title,
        user_goal=user_goal,
        agent_name=agent_name,
        runtime=runtime,
        runtime_status=runtime_status,
        tools=tools,
        reads_from=reads_from,
        writes_to=writes_to,
        external_actions=external_actions,
        permission_surfaces=permission_surfaces,
        workflow_manifest=workflow_manifest,
        approval_expectations=approval_expectations,
    )


def get_workflow_pack_approval_resume_contract(
    vault_root: str | Path,
    *,
    run_id: str = "",
    gate_id: str = "",
) -> dict[str, Any]:
    return build_approval_resume_contract(
        vault_root,
        run_id=run_id,
        gate_id=gate_id,
    )


def review_workflow_pack_approval_artifact(
    vault_root: str | Path,
    *,
    run_id: str = "",
    gate_id: str = "",
    request_digest: str = "",
    reviewer_id: str = "operator",
    operator_statement: str = "",
    decision: str = "approved",
    write_approval: bool = False,
) -> dict[str, Any]:
    return build_approval_review_artifact(
        vault_root,
        run_id=run_id,
        gate_id=gate_id,
        request_digest=request_digest,
        reviewer_id=reviewer_id,
        operator_statement=operator_statement,
        decision=decision,
        write_approval=write_approval,
    )


def get_workflow_pack_approval_consumption_dry_run(
    vault_root: str | Path,
    *,
    run_id: str = "",
    gate_id: str = "",
    request_digest: str = "",
    approval_artifact_path: str = "",
    expected_decision: str = "",
) -> dict[str, Any]:
    return build_approval_consumption_dry_run(
        vault_root,
        run_id=run_id,
        gate_id=gate_id,
        request_digest=request_digest,
        approval_artifact_path=approval_artifact_path,
        expected_decision=expected_decision,
    )


def reserve_workflow_pack_exact_once_marker(
    vault_root: str | Path,
    *,
    run_id: str = "",
    gate_id: str = "",
    request_digest: str = "",
    approval_artifact_path: str = "",
    expected_decision: str = "",
    reserve_marker: bool = False,
    operator_statement: str = "",
    reserved_by: str = "operator",
) -> dict[str, Any]:
    return build_approval_marker_reservation(
        vault_root,
        run_id=run_id,
        gate_id=gate_id,
        request_digest=request_digest,
        approval_artifact_path=approval_artifact_path,
        expected_decision=expected_decision,
        reserve_marker=reserve_marker,
        operator_statement=operator_statement,
        reserved_by=reserved_by,
    )


def execute_workflow_pack_approved_local_resume(
    vault_root: str | Path,
    *,
    run_id: str = "",
    gate_id: str = "",
    request_digest: str = "",
    approval_artifact_path: str = "",
    exact_once_marker_path: str = "",
    expected_decision: str = "",
    execute_resume: bool = False,
    operator_statement: str = "",
    executed_by: str = "operator",
) -> dict[str, Any]:
    return build_approved_local_resume_executor(
        vault_root,
        run_id=run_id,
        gate_id=gate_id,
        request_digest=request_digest,
        approval_artifact_path=approval_artifact_path,
        exact_once_marker_path=exact_once_marker_path,
        expected_decision=expected_decision,
        execute_resume=execute_resume,
        operator_statement=operator_statement,
        executed_by=executed_by,
    )


def _safe_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"error": "not_object", "path": str(path)}
    except Exception as exc:
        return {"error": str(exc), "path": str(path)}
