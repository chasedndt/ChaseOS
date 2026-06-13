"""Local Automation Audit MVP for the founder/personal workflow pack."""

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


PACK_ID = "founder_personal_automation_audit"

QUESTIONNAIRE_FIELDS: tuple[dict[str, str], ...] = (
    {
        "id": "work_domains",
        "label": "Work domains",
        "kind": "text",
        "placeholder": "Ops, content, sales, admin, research",
    },
    {
        "id": "repeated_tasks",
        "label": "Repeated tasks",
        "kind": "textarea",
        "placeholder": "One repeated task per line",
    },
    {
        "id": "pain_points",
        "label": "Pain points",
        "kind": "textarea",
        "placeholder": "Where work feels slow, risky, or easy to forget",
    },
)

DEFAULT_REPEATED_TASKS = (
    "Prepare a weekly operating status update from scattered notes",
    "Review new intake requests and decide the next action",
    "Draft follow-up messages after meetings or client updates",
)

FORBIDDEN_ACTIONS = (
    "send_email",
    "publish_content",
    "browser_action",
    "runtime_execution",
    "external_api_call",
)


def create_automation_audit_run(
    vault_root: str | Path,
    *,
    title: str = "",
    user_goal: str = "",
    questionnaire: dict[str, Any] | None = None,
    work_domains: str | list[str] = "",
    repeated_tasks: str | list[str] = "",
    pain_points: str | list[str] = "",
) -> dict[str, Any]:
    """Create a local, review-gated automation audit run.

    This function writes only Workflow Pack state, artifacts, approval records,
    and proof-card files under runtime/workflow_packs/state. It does not execute
    generated manifests, call providers, control a browser, send email, or
    promote anything into canonical/runtime state.
    """

    pack = get_workflow_pack(PACK_ID)
    goal = (user_goal or "").strip() or "Find the safest highest-ROI workflows to automate first."
    normalized = normalize_questionnaire(
        questionnaire=questionnaire,
        work_domains=work_domains,
        repeated_tasks=repeated_tasks,
        pain_points=pain_points,
    )
    audit = build_automation_audit_result(user_goal=goal, questionnaire=normalized)
    store = WorkflowPackStore(vault_root)
    run = store.create_run(
        pack_id=PACK_ID,
        title=title or "Founder / Personal Automation Audit",
        user_goal=goal,
        input_data={
            "provider_mode": "demo_manual",
            "demo": True,
            "workflow_pack_mode": "automation_audit_mvp",
            "questionnaire": normalized,
            "safe_boundaries": audit["safe_boundaries"],
        },
        source_refs=[
            SourceReference(
                id="manual-automation-audit-questionnaire",
                source_type="manual_questionnaire",
                captured_at=utc_now(),
                provenance_status="candidate",
                sensitivity_status="operator_review_required",
                title="Manual Automation Audit questionnaire",
                summary="Operator-supplied local questionnaire context only.",
            )
        ],
    )
    store.append_audit_event(
        run.id,
        "automation_audit_questionnaire_ingested",
        {
            "task_count": len(audit["repeated_tasks"]),
            "domain_count": len(audit["work_domains"]),
            "external_actions_performed": False,
        },
    )

    artifacts = [
        store.create_artifact(
            run_id=run.id,
            artifact_type="report",
            title="Automation Audit Findings",
            content=render_findings_report(audit),
            extension="md",
            mime_type="text/markdown",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="scorecard",
            title="Automation Opportunity Scorecard",
            content=json.dumps(audit["scorecard"], indent=2, sort_keys=True) + "\n",
            extension="json",
            mime_type="application/json",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="manifest",
            title="Draft Workflow Manifests",
            content=render_manifest_yaml(audit),
            extension="yaml",
            mime_type="text/yaml",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="brief",
            title="Implementation Roadmap",
            content=render_implementation_roadmap(audit),
            extension="md",
            mime_type="text/markdown",
            public_share_safe=False,
        ),
    ]
    store.append_audit_event(
        run.id,
        "automation_audit_artifacts_created",
        {
            "artifact_ids": [artifact.id for artifact in artifacts],
            "manifest_count": len(audit["draft_manifests"]),
            "scorecard_item_count": len(audit["scorecard"]["items"]),
        },
    )

    gates = [
        store.create_approval_gate(
            run_id=run.id,
            action_type="runtime_execution",
            reason="Automation Audit MVP writes draft artifacts only; running any generated workflow manifest requires explicit human approval.",
            preview_artifact_refs=[artifact.id for artifact in artifacts],
            requested_by="automation_audit_mvp",
        )
    ]
    if any(item["external_action_required"] for item in audit["top_opportunities"]):
        gates.append(
            store.create_approval_gate(
                run_id=run.id,
                action_type="send_email",
                reason="At least one automation candidate involves outbound messaging; sending remains blocked until a future approved executor exists.",
                preview_artifact_refs=[artifact.id for artifact in artifacts],
                requested_by="automation_audit_mvp",
            )
        )
    store.append_audit_event(
        run.id,
        "automation_audit_approval_gates_created",
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
    store.append_audit_event(run.id, "automation_audit_proof_card_saved", {"proof_card_id": card.id})
    final_run = store.get_run(run.id)

    return {
        "surface": "workflow_pack_automation_audit_mvp",
        "status": "automation_audit_created",
        "run": final_run.to_dict(),
        "pack": pack.to_dict(),
        "automation_audit": audit,
        "artifacts": [artifact.to_dict() for artifact in artifacts],
        "approval_gate": gates[0].to_dict(),
        "approval_gates": [gate.to_dict() for gate in gates],
        "approval_check": action_allowed("runtime_execution", gates),
        "proof_card": card.to_dict(),
        "proof_paths": proof_paths,
        "external_actions_performed": False,
        "provider_calls_performed": False,
        "browser_actions_performed": False,
        "canonical_promotion_performed": False,
        "runtime_execution_performed": False,
    }


def normalize_questionnaire(
    *,
    questionnaire: dict[str, Any] | None = None,
    work_domains: str | list[str] = "",
    repeated_tasks: str | list[str] = "",
    pain_points: str | list[str] = "",
) -> dict[str, Any]:
    data = dict(questionnaire or {})
    if work_domains:
        data["work_domains"] = work_domains
    if repeated_tasks:
        data["repeated_tasks"] = repeated_tasks
    if pain_points:
        data["pain_points"] = pain_points
    return {
        "work_domains": split_items(data.get("work_domains") or data.get("domains") or ""),
        "repeated_tasks": split_tasks(data.get("repeated_tasks") or data.get("weekly_work") or ""),
        "pain_points": split_tasks(data.get("pain_points") or data.get("friction") or ""),
    }


def build_automation_audit_result(*, user_goal: str, questionnaire: dict[str, Any]) -> dict[str, Any]:
    domains = questionnaire.get("work_domains") or ["operations"]
    tasks = list(questionnaire.get("repeated_tasks") or [])
    if not tasks:
        seed_text = " ".join([user_goal, " ".join(questionnaire.get("pain_points") or [])]).strip()
        tasks = infer_tasks(seed_text)
    pain_points = list(questionnaire.get("pain_points") or [])
    score_items = [
        score_task(task, index=index, pain_points=pain_points, domains=domains)
        for index, task in enumerate(tasks[:8])
    ]
    top_opportunities = sorted(
        score_items,
        key=lambda item: (item["automation_score"], item["estimated_minutes_saved_weekly"]),
        reverse=True,
    )[:5]
    draft_manifests = [build_manifest(item, index=index) for index, item in enumerate(top_opportunities[:3])]
    scorecard = {
        "schema": "workflow_packs.automation_audit.scorecard.v1",
        "generated_at": utc_now(),
        "method": "deterministic_keyword_score_v1",
        "items": score_items,
        "weights": {
            "frequency": 18,
            "pain": 18,
            "clarity": 16,
            "risk_penalty": -10,
            "local_dry_run_bonus": 6,
        },
    }
    return {
        "schema": "workflow_packs.automation_audit.result.v1",
        "status": "review_required",
        "user_goal": user_goal,
        "questionnaire": questionnaire,
        "work_domains": domains,
        "repeated_tasks": tasks,
        "pain_points": pain_points,
        "scorecard": scorecard,
        "top_opportunities": top_opportunities,
        "draft_manifests": draft_manifests,
        "roadmap": build_roadmap(top_opportunities),
        "approval_modes": sorted({item["approval_mode"] for item in top_opportunities}),
        "safe_boundaries": {
            "external_actions_performed": False,
            "provider_calls_performed": False,
            "browser_actions_performed": False,
            "runtime_execution_performed": False,
            "canonical_promotion_performed": False,
            "generated_manifests_are_drafts_only": True,
            "forbidden_actions": list(FORBIDDEN_ACTIONS),
        },
    }


def split_items(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [
        item.strip()
        for item in re.split(r"[,;\n]+", str(value or ""))
        if item.strip()
    ]


def split_tasks(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        raw_items = [str(item) for item in value]
    else:
        raw_items = re.split(r"[\n;]+", str(value or ""))
    tasks: list[str] = []
    for item in raw_items:
        cleaned = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", item).strip()
        if len(cleaned) >= 4 and cleaned not in tasks:
            tasks.append(cleaned)
    return tasks


def infer_tasks(seed_text: str) -> list[str]:
    text = seed_text.lower()
    tasks = list(DEFAULT_REPEATED_TASKS)
    if "email" in text or "client" in text or "follow" in text:
        tasks[2] = "Draft follow-up messages for clients or collaborators"
    if "content" in text or "social" in text or "publish" in text:
        tasks.append("Turn notes into recurring content draft packets")
    if "research" in text or "source" in text:
        tasks.append("Collect source notes and summarize candidate decisions")
    return tasks[:5]


def score_task(task: str, *, index: int, pain_points: list[str], domains: list[str]) -> dict[str, Any]:
    lower = task.lower()
    pain_text = " ".join(pain_points).lower()
    frequency = 5 if any(word in lower for word in ("daily", "every day")) else 4
    if any(word in lower for word in ("monthly", "quarterly", "annual")):
        frequency = 2
    clarity = 4 if any(word in lower for word in ("report", "status", "checklist", "intake", "draft", "summary", "notes")) else 3
    pain = 4 if any(word in lower + " " + pain_text for word in ("manual", "slow", "messy", "late", "boring", "forget", "handoff")) else 3
    risk = 1
    if any(word in lower for word in ("email", "send", "client", "customer", "publish", "post", "payment", "invoice")):
        risk = 4
    elif any(word in lower for word in ("external", "browser", "api", "account")):
        risk = 3
    local_bonus = 6 if risk <= 2 else 0
    score = max(0, min(100, (frequency * 18) + (pain * 18) + (clarity * 16) - (risk * 10) + local_bonus - index))
    approval_mode = "review_required"
    if risk >= 4:
        approval_mode = "approval_before_send"
    elif risk <= 1 and clarity >= 4:
        approval_mode = "local_dry_run_then_review"
    return {
        "id": slug(task),
        "task": task,
        "domain": select_domain(task, domains),
        "frequency": frequency,
        "pain": pain,
        "clarity": clarity,
        "risk": risk,
        "risk_level": "high" if risk >= 4 else "medium" if risk >= 3 else "low",
        "automation_score": score,
        "estimated_minutes_saved_weekly": max(20, min(180, frequency * clarity * 9 - risk * 5)),
        "approval_mode": approval_mode,
        "external_action_required": risk >= 4,
        "recommended_first_step": first_step_for_task(task, risk),
    }


def select_domain(task: str, domains: list[str]) -> str:
    if not domains:
        return "operations"
    lower = task.lower()
    for domain in domains:
        normalized = str(domain).strip()
        if normalized and normalized.lower() in lower:
            return normalized
    return str(domains[0])


def first_step_for_task(task: str, risk: int) -> str:
    if risk >= 4:
        return "Generate drafts only and require approval before any outbound action."
    if any(word in task.lower() for word in ("report", "status", "summary")):
        return "Create a local dry-run report from reviewed inputs."
    return "Draft a checklist-style local workflow and route outputs to review."


def build_manifest(item: dict[str, Any], *, index: int) -> dict[str, Any]:
    manifest_id = f"automation_audit_{index + 1}_{item['id'][:38]}"
    approval_actions = ["runtime_execution"]
    if item["external_action_required"]:
        approval_actions.append("send_email")
    return {
        "id": manifest_id,
        "name": item["task"],
        "status": "draft_review_required",
        "mode": "local_dry_run_only",
        "source": "workflow_pack_automation_audit_mvp",
        "approval_mode": item["approval_mode"],
        "required_approval_actions": approval_actions,
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "steps": [
            "Read operator-reviewed local inputs.",
            "Generate a local draft artifact.",
            "Write the result to the Workflow Packs review queue.",
            "Stop before any external, browser, email, runtime, or canonical action.",
        ],
    }


def build_roadmap(opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    first = opportunities[0]["task"] if opportunities else "the highest-scoring local workflow"
    return [
        {
            "phase": "0_review",
            "summary": "Review the scorecard, task assumptions, and risk levels before treating any draft as actionable.",
        },
        {
            "phase": "1_local_dry_run",
            "summary": f"Prototype a local dry-run for: {first}.",
        },
        {
            "phase": "2_artifact_quality",
            "summary": "Compare the generated draft against real operator output and tighten inputs before automation.",
        },
        {
            "phase": "3_approval_path",
            "summary": "Only after proof exists, add approval-gated execution wiring for the exact manifest and action type.",
        },
    ]


def render_findings_report(audit: dict[str, Any]) -> str:
    opportunity_lines = "\n".join(
        [
            (
                f"{index}. **{item['task']}** - score {item['automation_score']} - "
                f"{item['risk_level']} risk - {item['approval_mode']} - "
                f"{item['estimated_minutes_saved_weekly']} min/week"
            )
            for index, item in enumerate(audit["top_opportunities"], start=1)
        ]
    )
    task_lines = "\n".join(f"- {task}" for task in audit["repeated_tasks"])
    domain_text = ", ".join(audit["work_domains"]) or "operations"
    return f"""# Automation Audit Findings

## Goal
{audit["user_goal"]}

## Work Domains
{domain_text}

## Repeated Tasks
{task_lines}

## Top Opportunities
{opportunity_lines}

## Safety Boundary
- External actions performed: false
- Provider calls performed: false
- Browser actions performed: false
- Runtime execution performed: false
- Generated workflow manifests are drafts only.
"""


def render_manifest_yaml(audit: dict[str, Any]) -> str:
    lines = [
        "schema: workflow_packs.automation_audit.manifests.v1",
        "status: draft_review_required",
        "generated_by: automation_audit_mvp",
        "draft_manifests:",
    ]
    for manifest in audit["draft_manifests"]:
        lines.extend(
            [
                f"  - id: {manifest['id']}",
                f"    name: {yaml_quote(manifest['name'])}",
                f"    status: {manifest['status']}",
                f"    mode: {manifest['mode']}",
                f"    approval_mode: {manifest['approval_mode']}",
                "    required_approval_actions:",
            ]
        )
        lines.extend(f"      - {action}" for action in manifest["required_approval_actions"])
        lines.append("    forbidden_actions:")
        lines.extend(f"      - {action}" for action in manifest["forbidden_actions"])
        lines.append("    steps:")
        lines.extend(f"      - {yaml_quote(step)}" for step in manifest["steps"])
    return "\n".join(lines) + "\n"


def render_implementation_roadmap(audit: dict[str, Any]) -> str:
    roadmap_lines = "\n".join(f"- **{item['phase']}**: {item['summary']}" for item in audit["roadmap"])
    manifest_lines = "\n".join(
        f"- `{manifest['id']}` - {manifest['approval_mode']}"
        for manifest in audit["draft_manifests"]
    )
    return f"""# Automation Implementation Roadmap

## Recommended Sequence
{roadmap_lines}

## Draft Manifests
{manifest_lines}

## Not Authorized In This MVP
- Email sending
- Publishing
- Browser control
- Live runtime execution
- External API calls
- Canonical graph promotion
"""


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return result or "automation_candidate"
