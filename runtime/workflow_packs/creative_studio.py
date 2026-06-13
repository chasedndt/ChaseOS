"""Local Creative Studio MVP for the visual product workflow pack."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from .approvals import action_allowed
from .models import SourceReference, utc_now
from .proof_cards import build_proof_card, render_proof_card_markdown
from .registry import get_workflow_pack
from .store import WorkflowPackStore


PACK_ID = "visual_product_creative_studio"

QUESTIONNAIRE_FIELDS: tuple[dict[str, str], ...] = (
    {
        "id": "campaign_type",
        "label": "Campaign Type",
        "kind": "text",
        "placeholder": "Local business, creator launch, product landing",
    },
    {
        "id": "brand_profile",
        "label": "Brand Profile",
        "kind": "textarea",
        "placeholder": "What the brand is, how it should feel, and what makes it credible",
    },
    {
        "id": "offer",
        "label": "Offer",
        "kind": "text",
        "placeholder": "The product, service, or thing being promoted",
    },
    {
        "id": "audience",
        "label": "Audience",
        "kind": "text",
        "placeholder": "Who this is for",
    },
    {
        "id": "tone",
        "label": "Tone",
        "kind": "text",
        "placeholder": "Clear, premium, playful, technical",
    },
    {
        "id": "channels",
        "label": "Channels",
        "kind": "text",
        "placeholder": "Landing page, social, email",
    },
    {
        "id": "primary_cta",
        "label": "Primary CTA",
        "kind": "text",
        "placeholder": "Book a consult, join waitlist, start demo",
    },
)

FORBIDDEN_ACTIONS = (
    "publish_content",
    "send_email",
    "browser_action",
    "external_api_call",
    "runtime_execution",
)


def create_creative_studio_run(
    vault_root: str | Path,
    *,
    title: str = "",
    user_goal: str = "",
    questionnaire: dict[str, Any] | None = None,
    campaign_type: str = "",
    brand_profile: str = "",
    offer: str = "",
    audience: str = "",
    tone: str = "",
    channels: str | list[str] = "",
    primary_cta: str = "",
) -> dict[str, Any]:
    """Create a local, review-gated Creative Studio run.

    This MVP writes campaign artifacts and approval-gate records under
    runtime/workflow_packs/state. It does not call image/design providers,
    publish content, send email, automate browsers, or promote anything into
    canonical ChaseOS state.
    """

    pack = get_workflow_pack(PACK_ID)
    goal = (user_goal or "").strip() or "Create a reviewed local campaign pack."
    normalized = normalize_questionnaire(
        questionnaire=questionnaire,
        campaign_type=campaign_type,
        brand_profile=brand_profile,
        offer=offer,
        audience=audience,
        tone=tone,
        channels=channels,
        primary_cta=primary_cta,
        user_goal=goal,
    )
    creative = build_creative_studio_result(user_goal=goal, questionnaire=normalized)
    store = WorkflowPackStore(vault_root)
    run = store.create_run(
        pack_id=PACK_ID,
        title=title or "Visual Product & Creative Studio Run",
        user_goal=goal,
        input_data={
            "provider_mode": "demo_manual",
            "demo": True,
            "workflow_pack_mode": "creative_studio_mvp",
            "questionnaire": normalized,
            "safe_boundaries": creative["safe_boundaries"],
        },
        source_refs=[
            SourceReference(
                id="manual-creative-studio-questionnaire",
                source_type="manual_questionnaire",
                captured_at=utc_now(),
                provenance_status="candidate",
                sensitivity_status="operator_review_required",
                title="Manual Creative Studio questionnaire",
                summary="Operator-supplied local campaign context only.",
            )
        ],
    )
    store.append_audit_event(
        run.id,
        "creative_studio_intake_ingested",
        {
            "campaign_type": creative["campaign_type"],
            "channel_count": len(creative["channels"]),
            "external_actions_performed": False,
        },
    )

    artifacts = [
        store.create_artifact(
            run_id=run.id,
            artifact_type="report",
            title="Brand Opportunity Audit",
            content=render_brand_opportunity_audit(creative),
            extension="md",
            mime_type="text/markdown",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="brief",
            title="Creative Brief",
            content=render_creative_brief(creative),
            extension="md",
            mime_type="text/markdown",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="copy_pack",
            title="Campaign Copy Pack",
            content=render_copy_pack(creative),
            extension="md",
            mime_type="text/markdown",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="html_mockup",
            title="Visual Card Mockup",
            content=render_visual_card_html(creative),
            extension="html",
            mime_type="text/html",
            public_share_safe=False,
        ),
        store.create_artifact(
            run_id=run.id,
            artifact_type="html_mockup",
            title="Landing Section Mockup",
            content=render_landing_section_html(creative),
            extension="html",
            mime_type="text/html",
            public_share_safe=False,
        ),
    ]
    store.append_audit_event(
        run.id,
        "creative_studio_artifacts_created",
        {
            "artifact_ids": [artifact.id for artifact in artifacts],
            "artifact_count": len(artifacts),
            "mockup_count": 2,
        },
    )

    gates = [
        store.create_approval_gate(
            run_id=run.id,
            action_type="publish_content",
            reason="Creative Studio MVP generates local draft artifacts only; publishing any copy, mockup, or landing-page content requires explicit human approval.",
            preview_artifact_refs=[artifact.id for artifact in artifacts],
            requested_by="creative_studio_mvp",
        ),
        store.create_approval_gate(
            run_id=run.id,
            action_type="send_email",
            reason="The copy pack includes an email draft; sending remains blocked until a future approved executor exists.",
            preview_artifact_refs=[artifact.id for artifact in artifacts],
            requested_by="creative_studio_mvp",
        ),
    ]
    store.append_audit_event(
        run.id,
        "creative_studio_approval_gates_created",
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
    store.append_audit_event(run.id, "creative_studio_proof_card_saved", {"proof_card_id": card.id})
    final_run = store.get_run(run.id)

    return {
        "surface": "workflow_pack_creative_studio_mvp",
        "status": "creative_studio_created",
        "run": final_run.to_dict(),
        "pack": pack.to_dict(),
        "creative_studio": creative,
        "artifacts": [artifact.to_dict() for artifact in artifacts],
        "approval_gate": gates[0].to_dict(),
        "approval_gates": [gate.to_dict() for gate in gates],
        "approval_check": action_allowed("publish_content", gates),
        "proof_card": card.to_dict(),
        "proof_paths": proof_paths,
        "external_actions_performed": False,
        "provider_calls_performed": False,
        "browser_actions_performed": False,
        "canonical_promotion_performed": False,
        "runtime_execution_performed": False,
        "publishing_performed": False,
        "email_send_performed": False,
        "image_provider_calls_performed": False,
    }


def normalize_questionnaire(
    *,
    questionnaire: dict[str, Any] | None = None,
    campaign_type: str = "",
    brand_profile: str = "",
    offer: str = "",
    audience: str = "",
    tone: str = "",
    channels: str | list[str] = "",
    primary_cta: str = "",
    user_goal: str = "",
) -> dict[str, Any]:
    data = dict(questionnaire or {})
    for key, value in {
        "campaign_type": campaign_type,
        "brand_profile": brand_profile,
        "offer": offer,
        "audience": audience,
        "tone": tone,
        "channels": channels,
        "primary_cta": primary_cta,
    }.items():
        if value:
            data[key] = value
    channels_value = data.get("channels") or data.get("channel_mix") or ""
    return {
        "campaign_type": clean_text(data.get("campaign_type")) or infer_campaign_type(user_goal),
        "brand_profile": clean_text(data.get("brand_profile")) or "A focused product or service brand with useful proof to show.",
        "offer": clean_text(data.get("offer")) or infer_offer(user_goal),
        "audience": clean_text(data.get("audience")) or "founders, creators, operators, and small teams",
        "tone": clean_text(data.get("tone")) or "clear, useful, trustworthy",
        "channels": split_items(channels_value) or ["landing page", "social caption", "email draft"],
        "primary_cta": clean_text(data.get("primary_cta")) or "Start with a local review run",
    }


def build_creative_studio_result(*, user_goal: str, questionnaire: dict[str, Any]) -> dict[str, Any]:
    campaign_type = questionnaire["campaign_type"]
    offer = questionnaire["offer"]
    audience = questionnaire["audience"]
    tone = questionnaire["tone"]
    primary_cta = questionnaire["primary_cta"]
    audit = build_brand_opportunity_audit(questionnaire, user_goal=user_goal)
    creative_brief = {
        "campaign_goal": user_goal,
        "campaign_type": campaign_type,
        "audience": audience,
        "offer": offer,
        "tone": tone,
        "primary_cta": primary_cta,
        "message_pillar": audit["message_pillar"],
        "visual_direction": build_visual_direction(campaign_type, tone),
        "review_notes": [
            "Confirm the offer is accurate before reuse.",
            "Confirm claims have evidence before public use.",
            "Approve publish/send actions separately.",
        ],
    }
    copy_pack = build_copy_pack(creative_brief)
    return {
        "schema": "workflow_packs.creative_studio.result.v1",
        "status": "review_required",
        "user_goal": user_goal,
        "questionnaire": questionnaire,
        "campaign_type": campaign_type,
        "brand_profile": questionnaire["brand_profile"],
        "offer": offer,
        "audience": audience,
        "tone": tone,
        "channels": questionnaire["channels"],
        "primary_cta": primary_cta,
        "brand_opportunity_audit": audit,
        "creative_brief": creative_brief,
        "copy_pack": copy_pack,
        "visual_mockup": {
            "format": "local_html_card",
            "status": "draft_review_required",
            "description": "A static local HTML card mockup saved as an artifact.",
        },
        "landing_section_mockup": {
            "format": "local_html_section",
            "status": "draft_review_required",
            "description": "A static local HTML landing section mockup saved as an artifact.",
        },
        "review_checklist": [
            "Brand profile reviewed",
            "Offer and audience reviewed",
            "Claims checked against available proof",
            "Copy approved before publish or send",
            "Mockup approved before external use",
        ],
        "safe_boundaries": {
            "external_actions_performed": False,
            "provider_calls_performed": False,
            "image_provider_calls_performed": False,
            "browser_actions_performed": False,
            "publishing_performed": False,
            "email_send_performed": False,
            "runtime_execution_performed": False,
            "canonical_promotion_performed": False,
            "mockups_are_local_static_html_only": True,
            "forbidden_actions": list(FORBIDDEN_ACTIONS),
        },
    }


def build_brand_opportunity_audit(questionnaire: dict[str, Any], *, user_goal: str) -> dict[str, Any]:
    offer = questionnaire["offer"]
    audience = questionnaire["audience"]
    brand_profile = questionnaire["brand_profile"]
    tone = questionnaire["tone"]
    channels = questionnaire["channels"]
    return {
        "method": "deterministic_local_positioning_scan_v1",
        "generated_at": utc_now(),
        "confidence": "candidate",
        "summary": f"{offer} can be positioned as a practical, reviewable offer for {audience}.",
        "message_pillar": build_message_pillar(offer, audience, user_goal),
        "strengths": [
            "The offer can be explained through a concrete before/after promise.",
            "The local proof-card workflow gives the campaign a built-in trust surface.",
            f"The requested tone is usable for {', '.join(channels[:3])}.",
        ],
        "risks": [
            "Unverified claims must stay in review before public use.",
            "Outbound sends and publishing require explicit approval.",
            "Static mockups are direction-setting artifacts, not final design-system output.",
        ],
        "opportunities": [
            f"Lead with the clearest problem solved by {offer}.",
            f"Make the first CTA low-friction for {audience}.",
            f"Use the brand profile as proof context: {brand_profile[:120]}",
        ],
        "scores": {
            "message_clarity": score_text_density(offer, user_goal),
            "audience_specificity": score_text_density(audience, brand_profile),
            "approval_risk": 82,
        },
    }


def build_message_pillar(offer: str, audience: str, user_goal: str) -> str:
    goal = user_goal.rstrip(".")
    return f"{offer} helps {audience} move from rough context to reviewed launch assets. {goal}."


def build_visual_direction(campaign_type: str, tone: str) -> dict[str, str]:
    lower = f"{campaign_type} {tone}".lower()
    if "local" in lower:
        palette = "warm white, ink, local-market green"
        layout = "direct offer card with testimonial slot and CTA band"
    elif "creator" in lower:
        palette = "soft black, clean white, signal yellow"
        layout = "creator launch card with proof strip and waitlist CTA"
    elif "premium" in lower or "luxury" in lower:
        palette = "charcoal, off-white, muted gold"
        layout = "editorial landing section with compact proof and quiet CTA"
    else:
        palette = "white, graphite, electric blue, mint accent"
        layout = "product landing section with benefit stack and proof badge"
    return {
        "palette": palette,
        "layout": layout,
        "imagery": "Use inspected product, venue, or operator-provided assets before public use.",
        "type_feel": "clear sans-serif hierarchy with compact proof details",
    }


def build_copy_pack(brief: dict[str, Any]) -> dict[str, Any]:
    offer = brief["offer"]
    audience = brief["audience"]
    cta = brief["primary_cta"]
    pillar = brief["message_pillar"]
    return {
        "headline": f"{offer}: ready for review, not guesswork",
        "subheadline": f"A local campaign pack for {audience}, with brief, copy, mockups, and proof in one pass.",
        "social_caption": f"Turn the rough idea into reviewed launch material. {pillar} {cta}.",
        "email_subject": f"Draft campaign pack: {offer}",
        "email_body": (
            f"Here is the reviewed draft direction for {offer}.\n\n"
            f"Audience: {audience}\n"
            f"Message: {pillar}\n\n"
            f"Next step: {cta}.\n\n"
            "No send or publish action should happen until this copy is approved."
        ),
        "landing_cta": cta,
        "proof_badge": "Local draft generated with approval gates and proof-card trail.",
    }


def render_brand_opportunity_audit(creative: dict[str, Any]) -> str:
    audit = creative["brand_opportunity_audit"]
    strengths = "\n".join(f"- {item}" for item in audit["strengths"])
    risks = "\n".join(f"- {item}" for item in audit["risks"])
    opportunities = "\n".join(f"- {item}" for item in audit["opportunities"])
    return f"""# Brand Opportunity Audit

## Summary
{audit["summary"]}

## Message Pillar
{audit["message_pillar"]}

## Strengths
{strengths}

## Risks
{risks}

## Opportunities
{opportunities}

## Scores
- Message clarity: {audit["scores"]["message_clarity"]}
- Audience specificity: {audit["scores"]["audience_specificity"]}
- Approval risk: {audit["scores"]["approval_risk"]}

## Safety Boundary
- External actions performed: false
- Provider calls performed: false
- Image provider calls performed: false
- Browser actions performed: false
- Publishing performed: false
- Email sending performed: false
"""


def render_creative_brief(creative: dict[str, Any]) -> str:
    brief = creative["creative_brief"]
    direction = brief["visual_direction"]
    review_notes = "\n".join(f"- {item}" for item in brief["review_notes"])
    channels = ", ".join(creative["channels"])
    return f"""# Creative Brief

## Campaign Goal
{brief["campaign_goal"]}

## Campaign Type
{brief["campaign_type"]}

## Audience
{brief["audience"]}

## Offer
{brief["offer"]}

## Channels
{channels}

## Tone
{brief["tone"]}

## Core Message
{brief["message_pillar"]}

## Visual Direction
- Palette: {direction["palette"]}
- Layout: {direction["layout"]}
- Imagery: {direction["imagery"]}
- Type feel: {direction["type_feel"]}

## CTA
{brief["primary_cta"]}

## Review Notes
{review_notes}
"""


def render_copy_pack(creative: dict[str, Any]) -> str:
    copy = creative["copy_pack"]
    return f"""# Campaign Copy Pack

## Headline
{copy["headline"]}

## Subheadline
{copy["subheadline"]}

## Social Caption
{copy["social_caption"]}

## Email Draft
Subject: {copy["email_subject"]}

{copy["email_body"]}

## Landing CTA
{copy["landing_cta"]}

## Proof Badge
{copy["proof_badge"]}
"""


def render_visual_card_html(creative: dict[str, Any]) -> str:
    copy = creative["copy_pack"]
    direction = creative["creative_brief"]["visual_direction"]
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Visual Card Mockup</title>
<style>
  :root {{ color-scheme: light; font-family: Inter, Arial, sans-serif; }}
  body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #f4f6f8; color: #121417; }}
  main {{ width: min(440px, calc(100vw - 32px)); border: 1px solid #cbd5e1; border-radius: 8px; background: #ffffff; padding: 24px; box-shadow: 0 18px 44px rgba(15, 23, 42, 0.12); }}
  p {{ line-height: 1.45; color: #475569; }}
  .kicker {{ color: #047857; font-size: 12px; font-weight: 700; text-transform: uppercase; }}
  .badge {{ display: inline-block; margin-top: 14px; border: 1px solid #94a3b8; border-radius: 4px; padding: 6px 8px; font-size: 12px; color: #334155; }}
  button {{ margin-top: 16px; border: 0; border-radius: 4px; background: #111827; color: #fff; padding: 10px 14px; font-weight: 700; }}
</style>
<body>
  <main>
    <div class="kicker">{esc_html(creative["campaign_type"])}</div>
    <h1>{esc_html(copy["headline"])}</h1>
    <p>{esc_html(copy["subheadline"])}</p>
    <p>{esc_html(direction["layout"])}</p>
    <button disabled>{esc_html(copy["landing_cta"])}</button>
    <div class="badge">Approval required before publish</div>
  </main>
</body>
</html>
"""


def render_landing_section_html(creative: dict[str, Any]) -> str:
    copy = creative["copy_pack"]
    audit = creative["brand_opportunity_audit"]
    direction = creative["creative_brief"]["visual_direction"]
    opportunities = "".join(f"<li>{esc_html(item)}</li>" for item in audit["opportunities"][:3])
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Landing Section Mockup</title>
<style>
  :root {{ color-scheme: light; font-family: Inter, Arial, sans-serif; }}
  body {{ margin: 0; background: #eef2f7; color: #111827; }}
  section {{ min-height: 72vh; display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(260px, 0.9fr); gap: 28px; align-items: center; padding: 48px; }}
  h1 {{ font-size: clamp(32px, 6vw, 64px); line-height: 1.02; margin: 0; }}
  p {{ color: #475569; line-height: 1.55; max-width: 64ch; }}
  aside {{ border: 1px solid #cbd5e1; background: #ffffff; border-radius: 8px; padding: 20px; }}
  .proof {{ font-size: 12px; color: #047857; font-weight: 700; text-transform: uppercase; }}
  .cta {{ display: inline-block; margin-top: 16px; border-radius: 4px; background: #111827; color: white; padding: 11px 14px; font-weight: 700; }}
  @media (max-width: 760px) {{ section {{ grid-template-columns: 1fr; padding: 28px; }} }}
</style>
<body>
  <section>
    <main>
      <div class="proof">{esc_html(copy["proof_badge"])}</div>
      <h1>{esc_html(copy["headline"])}</h1>
      <p>{esc_html(copy["subheadline"])}</p>
      <span class="cta">{esc_html(copy["landing_cta"])}</span>
    </main>
    <aside>
      <strong>Direction</strong>
      <p>{esc_html(direction["palette"])}. {esc_html(direction["type_feel"])}.</p>
      <strong>Opportunities</strong>
      <ul>{opportunities}</ul>
      <p>Static local mockup. No external publishing has occurred.</p>
    </aside>
  </section>
</body>
</html>
"""


def split_items(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [clean_text(item) for item in value if clean_text(item)]
    return [
        item.strip()
        for item in re.split(r"[,;\n]+", str(value or ""))
        if item.strip()
    ]


def infer_campaign_type(user_goal: str) -> str:
    lower = user_goal.lower()
    if "local" in lower or "restaurant" in lower or "salon" in lower or "shop" in lower:
        return "local_business_campaign"
    if "creator" in lower or "course" in lower or "newsletter" in lower:
        return "creator_launch"
    if "event" in lower or "poster" in lower:
        return "community_event_poster"
    return "indie_product_landing"


def infer_offer(user_goal: str) -> str:
    cleaned = clean_text(user_goal).rstrip(".")
    if len(cleaned) > 12:
        return cleaned[:96]
    return "reviewed product launch pack"


def score_text_density(*values: str) -> int:
    words = [word for value in values for word in re.findall(r"[A-Za-z0-9]+", value)]
    return max(40, min(95, 40 + len(set(word.lower() for word in words)) * 3))


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def esc_html(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)
