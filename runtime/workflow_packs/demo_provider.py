"""Deterministic local demo provider for the four Workflow Packs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .approvals import action_allowed
from .models import SourceReference, utc_now
from .proof_cards import build_proof_card, render_proof_card_markdown
from .registry import get_workflow_pack
from .store import WorkflowPackStore


_DEFAULT_GOALS = {
    "visual_product_creative_studio": "Create a local campaign pack for a product launch.",
    "founder_personal_automation_audit": "Find the safest highest-ROI workflows to automate first.",
    "research_to_product_intelligence": "Turn source notes into product decisions and an implementation brief.",
    "safe_agent_runtime_governance_kit": "Audit agent permissions and draft safe approval policy recommendations.",
}

_EXTERNAL_ACTION_BY_PACK = {
    "visual_product_creative_studio": "publish_content",
    "founder_personal_automation_audit": "runtime_execution",
    "research_to_product_intelligence": "graph_promotion",
    "safe_agent_runtime_governance_kit": "agent_policy_change",
}


def create_demo_workflow_run(
    vault_root: str | Path,
    *,
    pack_id: str = "founder_personal_automation_audit",
    title: str = "",
    user_goal: str = "",
) -> dict[str, Any]:
    pack = get_workflow_pack(pack_id)
    if pack.id == "visual_product_creative_studio":
        from .creative_studio import create_creative_studio_run

        result = create_creative_studio_run(
            vault_root,
            title=title,
            user_goal=user_goal,
        )
        return {
            **result,
            "surface": "workflow_pack_demo_provider",
            "status": "demo_run_created",
        }

    if pack.id == "founder_personal_automation_audit":
        from .automation_audit import create_automation_audit_run

        result = create_automation_audit_run(
            vault_root,
            title=title,
            user_goal=user_goal,
        )
        return {
            **result,
            "surface": "workflow_pack_demo_provider",
            "status": "demo_run_created",
        }

    if pack.id == "research_to_product_intelligence":
        from .research_intelligence import create_research_intelligence_run

        result = create_research_intelligence_run(
            vault_root,
            title=title,
            user_goal=user_goal,
        )
        return {
            **result,
            "surface": "workflow_pack_demo_provider",
            "status": "demo_run_created",
        }

    if pack.id == "safe_agent_runtime_governance_kit":
        from .agent_governance import create_agent_governance_run

        result = create_agent_governance_run(
            vault_root,
            title=title,
            user_goal=user_goal,
        )
        return {
            **result,
            "surface": "workflow_pack_demo_provider",
            "status": "demo_run_created",
        }

    goal = user_goal.strip() or _DEFAULT_GOALS[pack.id]
    store = WorkflowPackStore(vault_root)
    run = store.create_run(
        pack_id=pack.id,
        title=title or f"{pack.name} demo run",
        user_goal=goal,
        input_data={"provider_mode": "demo_manual", "demo": True},
        source_refs=[
            SourceReference(
                id="manual-demo-intake",
                source_type="manual_note",
                captured_at=utc_now(),
                provenance_status="candidate",
                sensitivity_status="safe",
                title="Manual demo intake",
                summary="Operator-supplied local/demo context only.",
            )
        ],
    )

    artifact_specs = _artifact_specs(pack.id, goal)
    artifacts = [
        store.create_artifact(
            run_id=run.id,
            artifact_type=spec["artifact_type"],
            title=spec["title"],
            content=spec["content"],
            extension=spec.get("extension", "md"),
            mime_type=spec.get("mime_type", "text/markdown"),
            public_share_safe=False,
        )
        for spec in artifact_specs
    ]
    run = store.get_run(run.id)
    gate = store.create_approval_gate(
        run_id=run.id,
        action_type=_EXTERNAL_ACTION_BY_PACK[pack.id],
        reason="Phase 1 blocks all external or sensitive actions until a future approval executor exists.",
        preview_artifact_refs=[artifact.id for artifact in artifacts],
    )
    run = store.get_run(run.id)
    card = build_proof_card(
        pack=pack,
        run=run,
        artifacts=artifacts,
        approval_gates=[gate],
    )
    proof_paths = store.save_proof_card(
        run_id=run.id,
        proof_card=card.to_dict(),
        markdown=render_proof_card_markdown(card, pack),
    )
    final_run = store.get_run(run.id)
    return {
        "surface": "workflow_pack_demo_provider",
        "status": "demo_run_created",
        "run": final_run.to_dict(),
        "pack": pack.to_dict(),
        "artifacts": [artifact.to_dict() for artifact in artifacts],
        "approval_gate": gate.to_dict(),
        "approval_check": action_allowed(gate.action_type, [gate]),
        "proof_card": card.to_dict(),
        "proof_paths": proof_paths,
        "external_actions_performed": False,
        "provider_calls_performed": False,
        "browser_actions_performed": False,
        "canonical_promotion_performed": False,
    }


def _artifact_specs(pack_id: str, goal: str) -> list[dict[str, str]]:
    if pack_id == "founder_personal_automation_audit":
        return [
            {
                "artifact_type": "report",
                "title": "Automation Audit Findings",
                "content": _automation_audit_report(goal),
            },
            {
                "artifact_type": "manifest",
                "title": "Draft Workflow Manifest Recommendations",
                "content": _automation_manifest_drafts(),
                "extension": "yaml",
                "mime_type": "text/yaml",
            },
        ]
    if pack_id == "visual_product_creative_studio":
        return [
            {
                "artifact_type": "brief",
                "title": "Creative Brief",
                "content": _creative_brief(goal),
            },
            {
                "artifact_type": "copy_pack",
                "title": "Campaign Copy Pack",
                "content": _copy_pack(),
            },
            {
                "artifact_type": "html_mockup",
                "title": "Landing Section Mockup",
                "content": _html_mockup(goal),
                "extension": "html",
                "mime_type": "text/html",
            },
        ]
    if pack_id == "research_to_product_intelligence":
        return [
            {
                "artifact_type": "report",
                "title": "Evidence And Claim Packet",
                "content": _research_packet(goal),
            },
            {
                "artifact_type": "brief",
                "title": "Implementation Brief",
                "content": _implementation_brief(),
            },
        ]
    if pack_id == "safe_agent_runtime_governance_kit":
        return [
            {
                "artifact_type": "report",
                "title": "Agent Runtime Risk Audit",
                "content": _governance_report(goal),
            },
            {
                "artifact_type": "policy",
                "title": "Approval Policy Draft",
                "content": _approval_policy_draft(),
            },
        ]
    raise KeyError(pack_id)


def _automation_audit_report(goal: str) -> str:
    return f"""# Automation Audit Findings

## Goal
{goal}

## Repeated Tasks Found
- Weekly reporting and status collation
- Manual client/source intake checks
- Drafting recurring outreach or update packets

## Top Opportunities
1. Weekly operating brief - high confidence - approval mode: review required
2. Intake triage checklist - medium confidence - approval mode: manual
3. Draft follow-up packet - medium confidence - approval mode: approval before send

## Roadmap
- Build a local dry-run first.
- Keep all sends/publishing blocked behind approval.
- Promote only reviewed artifacts.
"""


def _automation_manifest_drafts() -> str:
    return """draft_manifests:
  - id: weekly_operating_brief
    mode: demo_manual
    external_actions: []
    review_status: pending_review
  - id: intake_triage_checklist
    mode: demo_manual
    external_actions: []
    review_status: pending_review
  - id: draft_follow_up_packet
    mode: demo_manual
    external_actions:
      - send_email
    approval_required: true
"""


def _creative_brief(goal: str) -> str:
    return f"""# Creative Brief

## Campaign Goal
{goal}

## Audience
Founders, creators, operators, and small teams who need useful assets quickly.

## Offer Angle
Turn messy context into a reviewed launch pack with proof.

## CTA
Start with a local demo run, review outputs, then approve any external action separately.
"""


def _copy_pack() -> str:
    return """# Campaign Copy Pack

## Social Caption
Turn one rough idea into a reviewed campaign pack: brief, copy, mockup, and proof.

## Email Draft
Subject: Your launch pack is ready for review

Body: The local draft pack is ready. Review the artifacts and approve any external send separately.
"""


def _html_mockup(goal: str) -> str:
    safe_goal = goal.replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!doctype html>
<html lang=\"en\">
<meta charset=\"utf-8\">
<title>Workflow Pack Demo Mockup</title>
<body>
  <main>
    <h1>{safe_goal}</h1>
    <p>Local demo mockup. No external publishing has occurred.</p>
    <button disabled>Approval required before publish</button>
  </main>
</body>
</html>
"""


def _research_packet(goal: str) -> str:
    return f"""# Evidence And Claim Packet

## Goal
{goal}

## Candidate Claims
- Claim: The idea may map to an onboarding workflow. Evidence quality: candidate.
- Claim: Governance proof improves trust. Evidence quality: candidate.

## Decisions
- Adopt: local proof-card generation.
- Watchlist: graph linkage after Phase 1.
- Defer: automatic implementation without approval.
"""


def _implementation_brief() -> str:
    return """# Implementation Brief

## Recommended Slice
Build source intake, claim scoring, decision artifacts, and proof cards before runtime integration.

## Required Reviews
- Source provenance review
- Generated claim review
- Approval gate before graph/canonical promotion
"""


def _governance_report(goal: str) -> str:
    return f"""# Agent Runtime Risk Audit

## Goal
{goal}

## Permission Matrix Draft
- Read local declared inputs: allowed
- Write local artifacts: allowed
- External send/publish: blocked until approval
- Runtime permission change: blocked until approval

## Findings
- External action gates are required.
- Hermes/OpenClaw escalation is not permitted through this workflow.
- Manifest linting should reject external actions without approval requirements.
"""


def _approval_policy_draft() -> str:
    return """# Approval Policy Draft

## Required Gates
- send_email: human approval required
- publish_content: human approval required
- browser_action: human approval required
- runtime_execution: human approval required
- agent_policy_change: human approval required
- graph_promotion: human approval required
- external_api_call: human approval required

## Non-Goals
This draft does not apply policy live and does not mutate runtime permissions.
"""
