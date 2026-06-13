"""WorkflowPack registry for the four product-facing MVP packs."""

from __future__ import annotations

from typing import Any

from .models import WorkflowPack

_STAMP = "2026-05-20T00:00:00Z"


DEFAULT_WORKFLOW_PACKS: tuple[WorkflowPack, ...] = (
    WorkflowPack(
        id="visual_product_creative_studio",
        name="Visual Product & Creative Studio",
        description="Create local campaign briefs, copy packs, lightweight visual mockups, and proof cards from manual product or offer context.",
        version="0.1.0",
        category="creative",
        user_facing=True,
        enabled=True,
        input_schema_ref="runtime/workflow_packs/schemas/creative_studio.input.v1",
        output_schema_ref="runtime/workflow_packs/schemas/creative_studio.output.v1",
        default_approval_policy_id="workflow_packs.external_actions_blocked_until_approved",
        supported_runtimes=["manual_provider", "local_service", "hermes_shadow"],
        required_capabilities=["artifact.write.local", "review.queue", "proof_card.generate"],
        artifact_types=["report", "brief", "copy_pack", "html_mockup", "proof_card"],
        proof_card_template_id="workflow_pack_public_safe_v1",
        created_at=_STAMP,
        updated_at=_STAMP,
        examples=["Local business campaign pack", "Creator launch pack", "Indie product landing pack"],
        safety_notes=["No publishing, email sending, browser automation, or external design-provider calls in MVP."],
    ),
    WorkflowPack(
        id="founder_personal_automation_audit",
        name="Founder / Personal Automation Audit",
        description="Turn a guided local questionnaire into repeated-task findings, ranked automation opportunities, draft manifests, and a roadmap.",
        version="0.1.0",
        category="automation_audit",
        user_facing=True,
        enabled=True,
        input_schema_ref="runtime/workflow_packs/schemas/automation_audit.input.v1",
        output_schema_ref="runtime/workflow_packs/schemas/automation_audit.output.v1",
        default_approval_policy_id="workflow_packs.external_actions_blocked_until_approved",
        supported_runtimes=["manual_provider", "local_service"],
        required_capabilities=["artifact.write.local", "review.queue", "proof_card.generate"],
        artifact_types=["report", "scorecard", "manifest", "proof_card"],
        proof_card_template_id="workflow_pack_public_safe_v1",
        created_at=_STAMP,
        updated_at=_STAMP,
        examples=["Founder weekly ops audit", "Student/admin automation audit", "Solo business task audit"],
        safety_notes=["Recommendations are artifacts only; no workflow execution or tool connection occurs in MVP."],
    ),
    WorkflowPack(
        id="research_to_product_intelligence",
        name="Research-to-Product Intelligence Engine",
        description="Convert pasted/manual source context into evidence packets, claim candidates, product decisions, implementation briefs, and proof cards.",
        version="0.1.0",
        category="research_intelligence",
        user_facing=True,
        enabled=True,
        input_schema_ref="runtime/workflow_packs/schemas/research_intelligence.input.v1",
        output_schema_ref="runtime/workflow_packs/schemas/research_intelligence.output.v1",
        default_approval_policy_id="workflow_packs.external_actions_blocked_until_approved",
        supported_runtimes=["manual_provider", "local_service", "sic"],
        required_capabilities=["source.provenance.local", "artifact.write.local", "proof_card.generate"],
        artifact_types=["report", "scorecard", "brief", "json", "proof_card"],
        proof_card_template_id="workflow_pack_public_safe_v1",
        created_at=_STAMP,
        updated_at=_STAMP,
        examples=["Trend-to-feature brief", "Repo/source watchlist decision", "R&D export draft"],
        safety_notes=["Raw/candidate/canonical status remains visible; no implementation or canonical promotion happens automatically."],
    ),
    WorkflowPack(
        id="safe_agent_runtime_governance_kit",
        name="Safe Agent Runtime Governance Kit",
        description="Manually inventory agents and permission surfaces, classify risk, draft approval policies, lint manifests, and produce safety proof.",
        version="0.1.0",
        category="agent_governance",
        user_facing=True,
        enabled=True,
        input_schema_ref="runtime/workflow_packs/schemas/agent_governance.input.v1",
        output_schema_ref="runtime/workflow_packs/schemas/agent_governance.output.v1",
        default_approval_policy_id="workflow_packs.external_actions_blocked_until_approved",
        supported_runtimes=["manual_provider", "local_service"],
        required_capabilities=["policy.draft.local", "manifest.lint.local", "proof_card.generate"],
        artifact_types=["report", "scorecard", "policy", "json", "proof_card"],
        proof_card_template_id="workflow_pack_public_safe_v1",
        created_at=_STAMP,
        updated_at=_STAMP,
        examples=["Agent permission matrix", "Workflow manifest safety lint", "Prompt-injection test pack"],
        safety_notes=["Policy drafts are not applied live; Hermes/OpenClaw permissions cannot be escalated by this pack."],
    ),
)


def list_workflow_packs(*, include_disabled: bool = False) -> list[WorkflowPack]:
    packs = list(DEFAULT_WORKFLOW_PACKS)
    if include_disabled:
        return packs
    return [pack for pack in packs if pack.enabled]


def workflow_pack_ids() -> list[str]:
    return [pack.id for pack in list_workflow_packs(include_disabled=True)]


def get_workflow_pack(pack_id: str) -> WorkflowPack:
    for pack in DEFAULT_WORKFLOW_PACKS:
        if pack.id == pack_id:
            return pack
    raise KeyError(f"unknown workflow pack: {pack_id}")


def validate_registry() -> dict[str, Any]:
    packs = list_workflow_packs(include_disabled=True)
    ids = [pack.id for pack in packs]
    required = {
        "visual_product_creative_studio",
        "founder_personal_automation_audit",
        "research_to_product_intelligence",
        "safe_agent_runtime_governance_kit",
    }
    missing = sorted(required.difference(ids))
    duplicate_ids = sorted({pack_id for pack_id in ids if ids.count(pack_id) > 1})
    return {
        "valid": not missing and not duplicate_ids and all(pack.user_facing for pack in packs),
        "pack_count": len(packs),
        "required_pack_ids_present": not missing,
        "missing_pack_ids": missing,
        "duplicate_pack_ids": duplicate_ids,
        "all_user_facing": all(pack.user_facing for pack in packs),
        "all_enabled": all(pack.enabled for pack in packs),
    }


def registry_summary() -> dict[str, Any]:
    packs = list_workflow_packs(include_disabled=True)
    validation = validate_registry()
    return {
        "surface": "workflow_pack_registry",
        "status": "ready",
        "provider_mode": "demo_manual",
        "packs": [pack.to_dict() for pack in packs],
        "pack_count": len(packs),
        "validation": validation,
    }
