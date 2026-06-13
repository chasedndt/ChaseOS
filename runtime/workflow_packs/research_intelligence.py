"""Local Research-to-Product Intelligence MVP for the research workflow pack."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .approvals import action_allowed
from .models import SourceReference, utc_now
from .proof_cards import build_proof_card, render_proof_card_markdown
from .registry import get_workflow_pack
from .store import WorkflowPackStore


PACK_ID = "research_to_product_intelligence"

QUESTIONNAIRE_FIELDS: tuple[dict[str, str], ...] = (
    {
        "id": "research_mode",
        "label": "Evaluation Lens",
        "kind": "text",
        "placeholder": "product idea, feature integration, technical research",
    },
    {
        "id": "source_material",
        "label": "Pasted Source",
        "kind": "textarea",
        "placeholder": "Paste research notes, thread excerpts, repo notes, docs, or screenshot notes",
    },
    {
        "id": "source_urls",
        "label": "URL / Repo References",
        "kind": "textarea",
        "placeholder": "One URL or repo reference per line. Metadata only; no fetch or clone.",
    },
    {
        "id": "product_context",
        "label": "Product Context",
        "kind": "textarea",
        "placeholder": "Product, module, workflow pack, or roadmap area this should be evaluated against",
    },
    {
        "id": "decision_goal",
        "label": "Decision Goal",
        "kind": "text",
        "placeholder": "Adopt, fork, watchlist, reject, or turn into implementation brief",
    },
    {
        "id": "audience",
        "label": "Audience",
        "kind": "text",
        "placeholder": "Founders, builders, developers, creators, agencies",
    },
    {
        "id": "output_focus",
        "label": "Output Focus",
        "kind": "text",
        "placeholder": "implementation brief, content brief, R&D register export",
    },
)

FORBIDDEN_ACTIONS = (
    "browser_action",
    "external_api_call",
    "runtime_execution",
    "graph_promotion",
    "publish_content",
    "send_email",
)

SCORING_DIMENSIONS = (
    "user_pain_clarity",
    "market_relevance",
    "commercial_potential",
    "technical_feasibility",
    "strategic_fit_with_chaseos",
    "workflow_pack_compatibility",
    "source_evidence_quality",
    "security_risk",
    "license_compliance_risk",
    "implementation_complexity",
    "demo_shareability_potential",
    "long_term_moat_potential",
)


def create_research_intelligence_run(
    vault_root: str | Path,
    *,
    title: str = "",
    user_goal: str = "",
    questionnaire: dict[str, Any] | None = None,
    research_mode: str = "",
    source_material: str = "",
    source_urls: str | list[str] = "",
    product_context: str = "",
    decision_goal: str = "",
    audience: str = "",
    output_focus: str = "",
) -> dict[str, Any]:
    """Create a local, review-gated Research Intelligence run.

    This MVP writes source records, candidate claims, decision artifacts, a
    draft R&D-register-style export, approval-gate records, and proof cards
    under runtime/workflow_packs/state. It does not scrape URLs, call the
    GitHub API, clone repos, promote graph/canonical state, create PRs, publish
    content, or implement any recommendation.
    """

    pack = get_workflow_pack(PACK_ID)
    goal = (user_goal or "").strip() or "Turn source notes into product decisions."
    normalized = normalize_questionnaire(
        questionnaire=questionnaire,
        research_mode=research_mode,
        source_material=source_material,
        source_urls=source_urls,
        product_context=product_context,
        decision_goal=decision_goal,
        audience=audience,
        output_focus=output_focus,
        user_goal=goal,
    )
    source_refs = build_source_references(normalized, user_goal=goal)
    research = build_research_intelligence_result(
        user_goal=goal,
        questionnaire=normalized,
        source_refs=source_refs,
    )
    store = WorkflowPackStore(vault_root)
    run = store.create_run(
        pack_id=PACK_ID,
        title=title or "Research-to-Product Intelligence Run",
        user_goal=goal,
        input_data={
            "provider_mode": "demo_manual",
            "demo": True,
            "workflow_pack_mode": "research_intelligence_mvp",
            "questionnaire": normalized,
            "safe_boundaries": research["safe_boundaries"],
            "status_model": research["status_model"],
        },
        source_refs=source_refs,
    )
    store.append_audit_event(
        run.id,
        "research_intelligence_intake_ingested",
        {
            "source_count": len(source_refs),
            "url_metadata_count": len(normalized["source_urls"]),
            "external_actions_performed": False,
            "web_scraping_performed": False,
        },
    )
    store.append_audit_event(
        run.id,
        "research_intelligence_claims_extracted",
        {
            "claim_count": len(research["claims"]),
            "decision_count": len(research["decisions"]),
            "canonical_promotion_performed": False,
        },
    )

    artifacts = [
        store.create_artifact(
            run_id=run.id,
            artifact_type="report",
            title="Evidence And Claim Packet",
            content=render_evidence_packet(research),
            extension="md",
            mime_type="text/markdown",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="scorecard",
            title="Research Claim Scorecard",
            content=json.dumps(research["scorecard"], indent=2, sort_keys=True) + "\n",
            extension="json",
            mime_type="application/json",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="brief",
            title="Product Decision Matrix",
            content=render_decision_matrix(research),
            extension="md",
            mime_type="text/markdown",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="brief",
            title="Implementation Brief",
            content=render_implementation_brief(research),
            extension="md",
            mime_type="text/markdown",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="brief",
            title="Content Brief",
            content=render_content_brief(research),
            extension="md",
            mime_type="text/markdown",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="json",
            title="R&D Register Style Export",
            content=json.dumps(research["rd_register_export"], indent=2, sort_keys=True) + "\n",
            extension="json",
            mime_type="application/json",
            public_share_safe=False,
        ),
    ]
    store.append_audit_event(
        run.id,
        "research_intelligence_artifacts_created",
        {
            "artifact_ids": [artifact.id for artifact in artifacts],
            "claim_count": len(research["claims"]),
            "rd_register_write_performed": False,
        },
    )

    gates = [
        store.create_approval_gate(
            run_id=run.id,
            action_type="graph_promotion",
            reason="Research Intelligence MVP keeps source records, claims, decisions, and R&D export artifacts in raw/candidate status; graph or canonical promotion requires explicit human approval.",
            preview_artifact_refs=[artifact.id for artifact in artifacts],
            requested_by="research_intelligence_mvp",
        ),
        store.create_approval_gate(
            run_id=run.id,
            action_type="runtime_execution",
            reason="Implementation briefs are recommendations only; no generated decision may trigger autonomous implementation without explicit human approval.",
            preview_artifact_refs=[artifact.id for artifact in artifacts],
            requested_by="research_intelligence_mvp",
        ),
    ]
    store.append_audit_event(
        run.id,
        "research_intelligence_approval_gates_created",
        {"gate_ids": [gate.id for gate in gates], "action_types": [gate.action_type for gate in gates]},
    )

    run = store.get_run(run.id)
    card = build_proof_card(
        pack=pack,
        run=run,
        artifacts=artifacts,
        approval_gates=gates,
    )
    proof_paths = store.save_proof_card(
        run_id=run.id,
        proof_card=card.to_dict(),
        markdown=render_proof_card_markdown(card, pack),
    )
    store.append_audit_event(run.id, "research_intelligence_proof_card_saved", {"proof_card_id": card.id})
    final_run = store.get_run(run.id)

    return {
        "surface": "workflow_pack_research_intelligence_mvp",
        "status": "research_intelligence_created",
        "run": final_run.to_dict(),
        "pack": pack.to_dict(),
        "research_intelligence": research,
        "artifacts": [artifact.to_dict() for artifact in artifacts],
        "approval_gate": gates[0].to_dict(),
        "approval_gates": [gate.to_dict() for gate in gates],
        "approval_check": action_allowed("graph_promotion", gates),
        "proof_card": card.to_dict(),
        "proof_paths": proof_paths,
        "external_actions_performed": False,
        "provider_calls_performed": False,
        "browser_actions_performed": False,
        "canonical_promotion_performed": False,
        "graph_promotion_performed": False,
        "runtime_execution_performed": False,
        "web_scraping_performed": False,
        "github_api_calls_performed": False,
        "repo_cloning_performed": False,
        "rd_register_write_performed": False,
        "autonomous_implementation_performed": False,
    }


def normalize_questionnaire(
    *,
    questionnaire: dict[str, Any] | None = None,
    research_mode: str = "",
    source_material: str = "",
    source_urls: str | list[str] = "",
    product_context: str = "",
    decision_goal: str = "",
    audience: str = "",
    output_focus: str = "",
    user_goal: str = "",
) -> dict[str, Any]:
    data = dict(questionnaire or {})
    for key, value in {
        "research_mode": research_mode,
        "source_material": source_material,
        "source_urls": source_urls,
        "product_context": product_context,
        "decision_goal": decision_goal,
        "audience": audience,
        "output_focus": output_focus,
    }.items():
        if value:
            data[key] = value
    material = normalize_source_material(data.get("source_material") or data.get("pasted_source") or "")
    return {
        "research_mode": clean_text(data.get("research_mode")) or infer_research_mode(user_goal),
        "source_material": material,
        "source_urls": split_items(data.get("source_urls") or data.get("url_refs") or data.get("repo_refs") or ""),
        "product_context": clean_text(data.get("product_context")) or "ChaseOS product and workflow-pack context",
        "decision_goal": clean_text(data.get("decision_goal")) or "Decide whether to adopt, watchlist, reject, or defer the idea.",
        "audience": clean_text(data.get("audience")) or "founders, builders, developers, and operators",
        "output_focus": clean_text(data.get("output_focus")) or "implementation brief and R&D-register-style export",
    }


def build_source_references(questionnaire: dict[str, Any], *, user_goal: str) -> list[SourceReference]:
    now = utc_now()
    refs: list[SourceReference] = []
    material = questionnaire.get("source_material") or ""
    if material:
        refs.append(
            SourceReference(
                id="manual-pasted-source-1",
                source_type="manual_pasted_text",
                captured_at=now,
                provenance_status="raw",
                sensitivity_status="operator_review_required",
                title="Manual pasted source",
                summary=truncate(material, 180),
            )
        )
    else:
        refs.append(
            SourceReference(
                id="manual-research-goal",
                source_type="manual_goal_note",
                captured_at=now,
                provenance_status="raw",
                sensitivity_status="operator_review_required",
                title="Manual research goal",
                summary=truncate(user_goal, 180),
            )
        )
    for index, uri in enumerate(questionnaire.get("source_urls") or [], start=1):
        refs.append(
            SourceReference(
                id=f"metadata-reference-{index}",
                source_type="github_repo_metadata" if "github.com" in uri.lower() else "url_metadata",
                captured_at=now,
                provenance_status="raw",
                sensitivity_status="metadata_only",
                uri=uri,
                title=f"Metadata reference {index}",
                summary="Metadata reference only. ChaseOS did not fetch, scrape, clone, or call an external API.",
            )
        )
    return refs


def build_research_intelligence_result(
    *,
    user_goal: str,
    questionnaire: dict[str, Any],
    source_refs: list[SourceReference],
) -> dict[str, Any]:
    claims = extract_claims(questionnaire, user_goal=user_goal, source_refs=source_refs)
    scorecard_items = [
        score_claim(claim, index=index, questionnaire=questionnaire, source_count=len(source_refs))
        for index, claim in enumerate(claims)
    ]
    decisions = [
        build_decision(item, questionnaire=questionnaire)
        for item in scorecard_items
    ]
    implementation_briefs = build_implementation_briefs(decisions, questionnaire=questionnaire, user_goal=user_goal)
    content_brief = build_content_brief(decisions, questionnaire=questionnaire, user_goal=user_goal)
    source_records = [source_ref.to_dict() for source_ref in source_refs]
    evidence_packet = {
        "schema": "workflow_packs.research_intelligence.evidence_packet.v1",
        "status": "candidate_review_required",
        "generated_at": utc_now(),
        "source_records": source_records,
        "source_count": len(source_records),
        "provenance_status": "raw_to_candidate",
        "canonical_status": "not_promoted",
        "notes": [
            "Pasted source text is treated as raw input.",
            "URL and repo references are metadata only; no external fetch, scrape, API call, or clone occurred.",
            "Claims and decisions are candidate artifacts until reviewed by a human.",
        ],
    }
    rd_register_export = {
        "schema": "workflow_packs.research_intelligence.rd_register_export.v1",
        "status": "draft_review_required",
        "generated_at": utc_now(),
        "writeback_performed": False,
        "canonical_promotion_performed": False,
        "entries": [
            {
                "id": decision["id"],
                "title": truncate(decision["claim"], 80),
                "decision": decision["decision"],
                "candidate_status": "candidate",
                "canonical_status": "not_promoted",
                "product_area": decision["product_area"],
                "next_action": decision["next_action"],
                "linked_claim_id": decision["claim_id"],
                "human_review_required": True,
            }
            for decision in decisions
        ],
    }
    return {
        "schema": "workflow_packs.research_intelligence.result.v1",
        "status": "review_required",
        "user_goal": user_goal,
        "questionnaire": questionnaire,
        "source_records": source_records,
        "evidence_packet": evidence_packet,
        "claims": claims,
        "scorecard": {
            "schema": "workflow_packs.research_intelligence.scorecard.v1",
            "generated_at": utc_now(),
            "method": "deterministic_keyword_claim_score_v1",
            "dimensions": list(SCORING_DIMENSIONS),
            "items": scorecard_items,
        },
        "decisions": decisions,
        "implementation_briefs": implementation_briefs,
        "content_brief": content_brief,
        "rd_register_export": rd_register_export,
        "review_actions_available": [
            "accept_claim_after_human_review",
            "reject_claim_after_human_review",
            "edit_claim_in_artifact_before_promotion",
        ],
        "status_model": {
            "raw_sources": "raw",
            "normalized_sources": "candidate",
            "claims": "candidate",
            "decisions": "candidate",
            "rd_register_export": "draft_review_required",
            "canonical_status": "not_promoted",
        },
        "safe_boundaries": {
            "external_actions_performed": False,
            "provider_calls_performed": False,
            "browser_actions_performed": False,
            "web_scraping_performed": False,
            "github_api_calls_performed": False,
            "repo_cloning_performed": False,
            "runtime_execution_performed": False,
            "graph_promotion_performed": False,
            "canonical_promotion_performed": False,
            "rd_register_write_performed": False,
            "autonomous_implementation_performed": False,
            "source_records_are_raw_or_candidate": True,
            "forbidden_actions": list(FORBIDDEN_ACTIONS),
        },
    }


def extract_claims(
    questionnaire: dict[str, Any],
    *,
    user_goal: str,
    source_refs: list[SourceReference],
) -> list[dict[str, Any]]:
    material = questionnaire.get("source_material") or ""
    seed_text = "\n".join(
        [
            material,
            questionnaire.get("product_context") or "",
            questionnaire.get("decision_goal") or "",
            user_goal,
        ]
    )
    sentences = extract_sentences(seed_text)
    if len(sentences) < 3:
        sentences.extend(default_claim_sentences(questionnaire, user_goal=user_goal))
    unique = []
    for sentence in sentences:
        if sentence not in unique:
            unique.append(sentence)
    source_ids = [source_ref.id for source_ref in source_refs] or ["manual-research-goal"]
    claims: list[dict[str, Any]] = []
    for index, sentence in enumerate(unique[:8], start=1):
        claims.append(
            {
                "id": f"claim-{index}",
                "claim": sentence,
                "source_ids": source_ids[:3],
                "provenance_status": "candidate",
                "canonical_status": "not_promoted",
                "review_status": "pending_review",
                "evidence_summary": evidence_summary(sentence, source_refs),
                "uncertainty": uncertainty_note(sentence),
                "available_review_actions": ["accept", "reject", "edit"],
            }
        )
    return claims


def score_claim(
    claim: dict[str, Any],
    *,
    index: int,
    questionnaire: dict[str, Any],
    source_count: int,
) -> dict[str, Any]:
    text = " ".join(
        [
            claim["claim"],
            questionnaire.get("product_context") or "",
            questionnaire.get("decision_goal") or "",
            questionnaire.get("research_mode") or "",
        ]
    ).lower()
    source_quality = clamp(35 + source_count * 8 + keyword_count(text, EVIDENCE_KEYWORDS) * 5 - uncertainty_penalty(text))
    market_relevance = clamp(35 + keyword_count(text, MARKET_KEYWORDS) * 8 + keyword_count(text, PRODUCT_KEYWORDS) * 4)
    user_pain = clamp(30 + keyword_count(text, PAIN_KEYWORDS) * 10 + keyword_count(text, PRODUCT_KEYWORDS) * 3)
    technical_feasibility = clamp(45 + keyword_count(text, TECHNICAL_KEYWORDS) * 7 - keyword_count(text, COMPLEXITY_KEYWORDS) * 4)
    strategic_fit = clamp(40 + keyword_count(text, CHASEOS_KEYWORDS) * 8 + keyword_count(text, WORKFLOW_KEYWORDS) * 6)
    workflow_compatibility = clamp(35 + keyword_count(text, WORKFLOW_KEYWORDS) * 8 + keyword_count(text, PRODUCT_KEYWORDS) * 5)
    security_risk = clamp(15 + keyword_count(text, SECURITY_RISK_KEYWORDS) * 16)
    license_risk = clamp(10 + keyword_count(text, LICENSE_RISK_KEYWORDS) * 18)
    implementation_complexity = clamp(25 + keyword_count(text, COMPLEXITY_KEYWORDS) * 12 - keyword_count(text, LOCAL_KEYWORDS) * 4)
    commercial_potential = clamp(30 + keyword_count(text, MARKET_KEYWORDS) * 7 + keyword_count(text, COMMERCIAL_KEYWORDS) * 8)
    demo_shareability = clamp(30 + keyword_count(text, DEMO_KEYWORDS) * 8 + workflow_compatibility // 8)
    moat = clamp(25 + keyword_count(text, MOAT_KEYWORDS) * 9 + strategic_fit // 8)
    product_relevance = clamp((market_relevance + strategic_fit + workflow_compatibility) // 3)
    fit_score = clamp((product_relevance + technical_feasibility + user_pain) // 3)
    risk_score = clamp(max(security_risk, license_risk, implementation_complexity // 2))
    return {
        "claim_id": claim["id"],
        "claim": claim["claim"],
        "source_ids": claim["source_ids"],
        "index": index + 1,
        "provenance_status": claim["provenance_status"],
        "canonical_status": "not_promoted",
        "evidence_quality_score": source_quality,
        "product_relevance_score": product_relevance,
        "technical_feasibility_score": technical_feasibility,
        "fit_score": fit_score,
        "risk_score": risk_score,
        "dimensions": {
            "user_pain_clarity": user_pain,
            "market_relevance": market_relevance,
            "commercial_potential": commercial_potential,
            "technical_feasibility": technical_feasibility,
            "strategic_fit_with_chaseos": strategic_fit,
            "workflow_pack_compatibility": workflow_compatibility,
            "source_evidence_quality": source_quality,
            "security_risk": security_risk,
            "license_compliance_risk": license_risk,
            "implementation_complexity": implementation_complexity,
            "demo_shareability_potential": demo_shareability,
            "long_term_moat_potential": moat,
        },
    }


def build_decision(item: dict[str, Any], *, questionnaire: dict[str, Any]) -> dict[str, Any]:
    risk = item["risk_score"]
    evidence = item["evidence_quality_score"]
    relevance = item["product_relevance_score"]
    feasibility = item["technical_feasibility_score"]
    dimensions = item["dimensions"]
    if dimensions["security_risk"] >= 65:
        decision = "needs security review"
        next_action = "Route to a security review before implementation planning."
    elif dimensions["license_compliance_risk"] >= 60:
        decision = "needs license review"
        next_action = "Confirm license and compliance status before using the source idea."
    elif relevance >= 64 and feasibility >= 58 and risk <= 58:
        decision = "adopt"
        next_action = "Draft a small local implementation slice and keep it review-gated."
    elif relevance >= 56 and evidence >= 45:
        decision = "watchlist"
        next_action = "Keep the idea in the candidate register and gather stronger evidence."
    elif dimensions["implementation_complexity"] >= 72:
        decision = "defer"
        next_action = "Defer until foundations, proof, or integration surfaces are ready."
    else:
        decision = "reject"
        next_action = "Do not add to roadmap without stronger evidence or clearer fit."
    product_area = infer_product_area(" ".join([item["claim"], questionnaire.get("product_context") or ""]))
    return {
        "id": f"decision-{item['claim_id']}",
        "claim_id": item["claim_id"],
        "claim": item["claim"],
        "decision": decision,
        "product_area": product_area,
        "fit_score": item["fit_score"],
        "risk_score": risk,
        "evidence_quality_score": evidence,
        "product_relevance_score": relevance,
        "technical_feasibility_score": feasibility,
        "next_action": next_action,
        "candidate_status": "candidate",
        "canonical_status": "not_promoted",
        "human_review_required": True,
    }


def build_implementation_briefs(
    decisions: list[dict[str, Any]],
    *,
    questionnaire: dict[str, Any],
    user_goal: str,
) -> list[dict[str, Any]]:
    selected = [
        decision
        for decision in decisions
        if decision["decision"] in {"adopt", "watchlist", "defer", "needs security review", "needs license review"}
    ][:3]
    if not selected and decisions:
        selected = decisions[:1]
    briefs: list[dict[str, Any]] = []
    for index, decision in enumerate(selected, start=1):
        briefs.append(
            {
                "id": f"implementation-brief-{index}",
                "status": "draft_review_required",
                "decision_id": decision["id"],
                "decision": decision["decision"],
                "title": f"{decision['product_area']} candidate: {truncate(decision['claim'], 72)}",
                "goal": user_goal,
                "target_module": decision["product_area"],
                "recommended_slice": recommended_slice(decision),
                "review_requirements": [
                    "Human review of source provenance and claim wording",
                    "Evidence check before roadmap or graph promotion",
                    "Approval gate before runtime execution or implementation",
                ],
                "not_authorized": [
                    "autonomous implementation",
                    "graph/canonical promotion",
                    "external API calls",
                    "repo cloning",
                    "browser automation",
                ],
                "output_focus": questionnaire.get("output_focus") or "",
            }
        )
    return briefs


def build_content_brief(
    decisions: list[dict[str, Any]],
    *,
    questionnaire: dict[str, Any],
    user_goal: str,
) -> dict[str, Any]:
    lead = decisions[0] if decisions else {
        "claim": user_goal,
        "decision": "watchlist",
        "product_area": "workflow_packs",
        "next_action": "Review source material.",
    }
    return {
        "schema": "workflow_packs.research_intelligence.content_brief.v1",
        "status": "draft_review_required",
        "audience": questionnaire.get("audience") or "builders",
        "angle": f"Turn research into a reviewed {lead['decision']} decision for {lead['product_area']}.",
        "headline": f"Research decision: {truncate(lead['claim'], 72)}",
        "outline": [
            "Show the source context as raw/candidate, not canonical.",
            "Explain the claim and uncertainty.",
            "Show the decision, score, and next action.",
            "End with the proof-card and approval boundary.",
        ],
        "approval_note": "Publish/send actions are not authorized by this MVP.",
    }


def render_evidence_packet(research: dict[str, Any]) -> str:
    sources = "\n".join(
        [
            (
                f"- `{source['id']}` ({source['source_type']}) - "
                f"{source.get('title') or source.get('uri') or 'manual source'} - "
                f"provenance: {source.get('provenance_status', 'raw')}"
            )
            for source in research["source_records"]
        ]
    )
    claims = "\n".join(
        [
            (
                f"- `{claim['id']}` {claim['claim']}\n"
                f"  - Provenance: {claim['provenance_status']}\n"
                f"  - Canonical status: {claim['canonical_status']}\n"
                f"  - Review status: {claim['review_status']}\n"
                f"  - Evidence: {claim['evidence_summary']}\n"
                f"  - Uncertainty: {claim['uncertainty']}"
            )
            for claim in research["claims"]
        ]
    )
    return f"""# Evidence And Claim Packet

## Goal
{research["user_goal"]}

## Source Records
{sources}

## Extracted Claims
{claims}

## Status Boundary
- Raw sources: {research["status_model"]["raw_sources"]}
- Claims: {research["status_model"]["claims"]}
- Decisions: {research["status_model"]["decisions"]}
- Canonical status: {research["status_model"]["canonical_status"]}

## Safety Boundary
- Web scraping performed: false
- GitHub API calls performed: false
- Repo cloning performed: false
- Graph promotion performed: false
- Autonomous implementation performed: false
"""


def render_decision_matrix(research: dict[str, Any]) -> str:
    rows = "\n".join(
        [
            (
                f"| {decision['claim_id']} | {decision['evidence_quality_score']} | "
                f"{decision['product_area']} | {decision['fit_score']} | "
                f"{decision['risk_score']} | {decision['decision']} | {decision['next_action']} |"
            )
            for decision in research["decisions"]
        ]
    )
    return f"""# Product Decision Matrix

| Claim | Evidence | Product Area | Fit | Risk | Decision | Next Action |
|---|---:|---|---:|---:|---|---|
{rows}

## Review Boundary

All decisions are candidate recommendations. Accept, reject, or edit claims only after human review. No decision is automatically implemented or promoted.
"""


def render_implementation_brief(research: dict[str, Any]) -> str:
    sections = []
    for brief in research["implementation_briefs"]:
        reviews = "\n".join(f"- {item}" for item in brief["review_requirements"])
        blocked = "\n".join(f"- {item}" for item in brief["not_authorized"])
        sections.append(
            f"""## {brief["title"]}

- Status: {brief["status"]}
- Decision: {brief["decision"]}
- Target module: {brief["target_module"]}
- Recommended slice: {brief["recommended_slice"]}

### Review Requirements
{reviews}

### Not Authorized
{blocked}
"""
        )
    body = "\n".join(sections) or "No implementation briefs were generated."
    return f"""# Implementation Brief

## Goal
{research["user_goal"]}

{body}
"""


def render_content_brief(research: dict[str, Any]) -> str:
    brief = research["content_brief"]
    outline = "\n".join(f"- {item}" for item in brief["outline"])
    return f"""# Content Brief

## Audience
{brief["audience"]}

## Angle
{brief["angle"]}

## Headline
{brief["headline"]}

## Outline
{outline}

## Approval Note
{brief["approval_note"]}
"""


def extract_sentences(text: str) -> list[str]:
    raw_items = re.split(r"(?:[\n\r]+|(?<=[.!?])\s+)", text)
    sentences: list[str] = []
    for item in raw_items:
        cleaned = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", item).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        if 18 <= len(cleaned) <= 260:
            sentences.append(cleaned.rstrip("."))
    return sentences


def default_claim_sentences(questionnaire: dict[str, Any], *, user_goal: str) -> list[str]:
    context = questionnaire.get("product_context") or "the product workflow"
    return [
        f"{context} needs a reviewed product decision before implementation",
        "Candidate source claims should remain raw or candidate until a human accepts them",
        f"{user_goal.rstrip('.')} can be evaluated through evidence quality, product fit, feasibility, and risk",
    ]


def evidence_summary(sentence: str, source_refs: list[SourceReference]) -> str:
    source_count = len(source_refs)
    if any(word in sentence.lower() for word in EVIDENCE_KEYWORDS):
        return f"Candidate claim drawn from {source_count} local source record(s) with evidence-like wording."
    return f"Candidate claim inferred from {source_count} local source record(s); stronger evidence may be needed."


def uncertainty_note(sentence: str) -> str:
    lower = sentence.lower()
    if any(word in lower for word in ("may", "might", "could", "possible", "claim", "appears")):
        return "The wording is uncertain and should be verified before adoption."
    if any(word in lower for word in SECURITY_RISK_KEYWORDS):
        return "Security-sensitive wording requires additional review."
    if any(word in lower for word in LICENSE_RISK_KEYWORDS):
        return "License or compliance-sensitive wording requires additional review."
    return "Human review required before treating this as product truth."


def recommended_slice(decision: dict[str, Any]) -> str:
    if decision["decision"] == "adopt":
        return "Build a narrow local prototype and verify with a proof card before promotion."
    if decision["decision"] == "watchlist":
        return "Keep a candidate note and gather stronger source evidence before roadmap work."
    if decision["decision"] == "defer":
        return "Wait for the required foundation or integration surface before implementation."
    if "security" in decision["decision"]:
        return "Run a security review before any prototype or integration work."
    if "license" in decision["decision"]:
        return "Resolve license/compliance status before reuse."
    return "Archive as rejected unless stronger evidence appears."


def infer_product_area(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ("creative", "campaign", "content", "launch", "landing")):
        return "visual_product_creative_studio"
    if any(word in lower for word in ("automation", "task", "workflow", "manifest")):
        return "founder_personal_automation_audit"
    if any(word in lower for word in ("agent", "permission", "policy", "governance", "security")):
        return "safe_agent_runtime_governance_kit"
    if any(word in lower for word in ("research", "source", "claim", "evidence", "repo", "paper")):
        return "research_to_product_intelligence"
    return "workflow_packs"


def infer_research_mode(user_goal: str) -> str:
    lower = user_goal.lower()
    if "competitor" in lower:
        return "competitor research"
    if "technical" in lower or "repo" in lower or "github" in lower:
        return "technical research"
    if "content" in lower:
        return "content research"
    if "feature" in lower or "integrat" in lower:
        return "feature integration"
    return "product idea"


def normalize_source_material(value: Any) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_items(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        raw_items = [str(item) for item in value]
    else:
        raw_items = re.split(r"[,;\n]+", str(value or ""))
    items = []
    for item in raw_items:
        cleaned = item.strip()
        if cleaned and cleaned not in items:
            items.append(cleaned)
    return items[:12]


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def truncate(value: Any, limit: int) -> str:
    text = clean_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def clamp(value: int) -> int:
    return max(0, min(100, int(value)))


def keyword_count(text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def uncertainty_penalty(text: str) -> int:
    return keyword_count(text, ("may", "might", "could", "possible", "unverified", "rumor")) * 5


EVIDENCE_KEYWORDS = (
    "benchmark",
    "measured",
    "data",
    "docs",
    "paper",
    "repo",
    "github",
    "case study",
    "customer",
    "user",
    "tested",
    "evidence",
)
MARKET_KEYWORDS = (
    "founder",
    "builder",
    "developer",
    "agency",
    "creator",
    "customer",
    "market",
    "commercial",
    "user",
    "team",
)
PRODUCT_KEYWORDS = (
    "product",
    "feature",
    "workflow",
    "pack",
    "roadmap",
    "integration",
    "decision",
    "brief",
)
PAIN_KEYWORDS = (
    "pain",
    "slow",
    "messy",
    "manual",
    "overloaded",
    "risk",
    "problem",
    "need",
    "friction",
)
TECHNICAL_KEYWORDS = (
    "api",
    "local",
    "json",
    "markdown",
    "schema",
    "repo",
    "github",
    "runtime",
    "service",
    "test",
)
CHASEOS_KEYWORDS = (
    "chaseos",
    "local-first",
    "governance",
    "proof",
    "memory",
    "runtime",
    "operator",
    "agent",
)
WORKFLOW_KEYWORDS = (
    "workflow",
    "automation",
    "creative",
    "research",
    "agent",
    "governance",
    "source",
    "claim",
)
SECURITY_RISK_KEYWORDS = (
    "security",
    "credential",
    "secret",
    "token",
    "permission",
    "browser",
    "execute",
    "shell",
    "network",
)
LICENSE_RISK_KEYWORDS = (
    "license",
    "copyright",
    "patent",
    "terms",
    "compliance",
    "proprietary",
)
COMPLEXITY_KEYWORDS = (
    "crawler",
    "scrape",
    "clone",
    "multi-agent",
    "distributed",
    "realtime",
    "production",
    "deploy",
)
LOCAL_KEYWORDS = (
    "local",
    "manual",
    "markdown",
    "json",
    "draft",
)
COMMERCIAL_KEYWORDS = (
    "sales",
    "revenue",
    "pricing",
    "agency",
    "client",
    "customer",
    "business",
)
DEMO_KEYWORDS = (
    "demo",
    "proof",
    "show",
    "share",
    "content",
    "launch",
    "brief",
)
MOAT_KEYWORDS = (
    "defensible",
    "moat",
    "governance",
    "lineage",
    "proof",
    "source",
    "memory",
)
