"""Integrated local ChaseOS Pulse product shell.

The product shell composes existing Pulse Phase 10 surfaces into one static
entry artifact. It does not start a server, submit feedback, apply candidates,
dispatch runtimes, activate schedules, call providers/connectors, or mutate
canonical ChaseOS state.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from runtime.pulse.approval_queue_ui import build_pulse_approval_queue_ui
from runtime.pulse.card_schema import now_utc
from runtime.pulse.final_product_readiness_audit import build_pulse_final_product_readiness_audit
from runtime.pulse.local_surface import (
    PulseSurfaceError,
    _resolve_user_deck_json,
    build_pulse_surface_model,
)
from runtime.pulse.personal_map_live_apply_proof import build_personal_map_live_apply_proof
from runtime.pulse.personal_map_review_apply import build_personal_map_review_apply_surface
from runtime.pulse.personal_map_visualization import build_personal_map_visualization_contract
from runtime.pulse.runtime_brain_visualization import build_runtime_brain_visualization
from runtime.pulse.visual_card_deck_shell import build_pulse_visual_card_deck_shell


SURFACE_ID = "chaseos_pulse_product_shell"
PRODUCT_SHELL_ROOT = Path("07_LOGS") / "Pulse-Decks" / "product-shell"

AUTHORITY_BOUNDARY = {
    "read_only": True,
    "local_only": True,
    "writes_html_only_when_explicit": True,
    "starts_server": False,
    "opens_browser": False,
    "feedback_submission_enabled": False,
    "approval_execution_allowed": False,
    "candidate_apply_allowed": False,
    "personal_map_apply_allowed": False,
    "runtime_brain_update_allowed": False,
    "agent_bus_task_write_allowed": False,
    "runtime_dispatch_allowed": False,
    "provider_or_connector_call_allowed": False,
    "schedule_activation_allowed": False,
    "canonical_writeback_allowed": False,
    "second_datastore_created": False,
    "rd_workbook_update_allowed": False,
}


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _assert_inside(child: Path, parent: Path, message: str) -> None:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(message) from exc


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _date_slug(value: str | None) -> str:
    candidate = (value or now_utc())[:10]
    if len(candidate) == 10 and candidate[4] == "-" and candidate[7] == "-":
        return candidate
    return now_utc()[:10]


def _status_class(value: Any) -> str:
    text = str(value or "").lower()
    if text in {"true", "0"} or "complete" in text or "pass" in text or "ready" in text:
        return "ok"
    if "partial" in text or "review" in text or "candidate" in text:
        return "warn"
    if "blocked" in text or "fail" in text or "missing" in text or text == "false":
        return "risk"
    return "muted"


def _deck_card_summary(cards: list[dict[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, int] = {}
    by_audience: dict[str, int] = {}
    for card in cards:
        card_class = str(card.get("card_class") or card.get("type") or "unknown")
        audience = str(card.get("audience") or "user")
        by_class[card_class] = by_class.get(card_class, 0) + 1
        by_audience[audience] = by_audience.get(audience, 0) + 1
    return {
        "card_count": len(cards),
        "classes": by_class,
        "audiences": by_audience,
    }


def _surface_statuses(
    *,
    visual_shell: dict[str, Any],
    personal_map: dict[str, Any],
    personal_map_review: dict[str, Any],
    personal_map_live_apply_proof: dict[str, Any],
    runtime_brain: dict[str, Any],
    approval_queue: dict[str, Any],
    final_audit: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "surface": "visual_card_deck_shell",
            "status": "ready",
            "summary": visual_shell.get("deck_card_summary") or {},
            "writes": visual_shell.get("writes") or [],
        },
        {
            "surface": "personal_map_visualization",
            "status": "ready",
            "summary": personal_map.get("summary") or {},
            "writes": personal_map.get("writes") or [],
        },
        {
            "surface": "personal_map_review_apply",
            "status": "ready",
            "summary": personal_map_review.get("summary") or {},
            "writes": personal_map_review.get("writes") or [],
        },
        {
            "surface": "personal_map_live_apply_proof",
            "status": (
                "ready"
                if (personal_map_live_apply_proof.get("summary") or {}).get("live_apply_ready")
                else "waiting"
            ),
            "summary": personal_map_live_apply_proof.get("summary") or {},
            "writes": personal_map_live_apply_proof.get("writes") or [],
        },
        {
            "surface": "runtime_brain_visualization",
            "status": runtime_brain.get("summary", {}).get("dashboard_status") or "unknown",
            "summary": runtime_brain.get("summary") or {},
            "writes": runtime_brain.get("writes") or [],
        },
        {
            "surface": "approval_queue_ui",
            "status": approval_queue.get("summary", {}).get("approval_center_status") or "unknown",
            "summary": approval_queue.get("summary") or {},
            "writes": approval_queue.get("writes") or [],
        },
        {
            "surface": "final_product_readiness_audit",
            "status": final_audit.get("audit_status"),
            "summary": {
                "current_v1_local_lane_complete": final_audit.get("current_v1_local_lane_complete"),
                "full_product_grade_complete": final_audit.get("full_product_grade_complete"),
                "remaining_full_product_lanes": final_audit.get("remaining_full_product_lanes") or [],
            },
            "writes": [],
        },
    ]


def build_pulse_product_shell(
    vault_root: str | Path,
    *,
    deck_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build the integrated static Pulse product-shell model without writes."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()
    resolved_deck = _resolve_user_deck_json(vault, deck_path)
    base_surface = build_pulse_surface_model(vault, deck_path=resolved_deck)
    visual_shell = build_pulse_visual_card_deck_shell(vault, deck_path=resolved_deck)
    personal_map = build_personal_map_visualization_contract(vault, generated_at=timestamp)
    personal_map_review = build_personal_map_review_apply_surface(vault, generated_at=timestamp)
    personal_map_live_apply_proof = build_personal_map_live_apply_proof(
        vault,
        generated_at=timestamp,
    )
    runtime_brain = build_runtime_brain_visualization(vault, generated_at=timestamp)
    approval_queue = build_pulse_approval_queue_ui(vault, generated_at=timestamp)
    final_audit = build_pulse_final_product_readiness_audit(vault, generated_at=timestamp).to_dict()
    cards = list(base_surface.get("cards") or [])
    statuses = _surface_statuses(
        visual_shell=visual_shell,
        personal_map=personal_map,
        personal_map_review=personal_map_review,
        personal_map_live_apply_proof=personal_map_live_apply_proof,
        runtime_brain=runtime_brain,
        approval_queue=approval_queue,
        final_audit=final_audit,
    )

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "source_deck_path": _relative_to_vault(vault, resolved_deck),
        "deck": base_surface.get("deck") or {},
        "cards": cards,
        "card_summary": _deck_card_summary(cards),
        "surface_statuses": statuses,
        "final_product_readiness": {
            "audit_status": final_audit.get("audit_status"),
            "current_v1_local_lane_complete": final_audit.get("current_v1_local_lane_complete"),
            "full_product_grade_complete": final_audit.get("full_product_grade_complete"),
            "remaining_full_product_lanes": final_audit.get("remaining_full_product_lanes") or [],
            "next_recommended_pass": final_audit.get("next_recommended_pass"),
        },
        "panels": {
            "visual_shell": visual_shell,
            "personal_map": personal_map,
            "personal_map_review_apply": personal_map_review,
            "personal_map_live_apply_proof": personal_map_live_apply_proof,
            "runtime_brain": runtime_brain,
            "approval_queue": approval_queue,
        },
        "summary": {
            "panel_count": 6,
            "card_count": len(cards),
            "surface_status_count": len(statuses),
            "approval_lane_count": approval_queue.get("summary", {}).get("lane_count"),
            "runtime_card_count": runtime_brain.get("summary", {}).get("runtime_card_count"),
            "personal_map_candidate_count": personal_map.get("summary", {}).get("personal_map_candidate_count"),
            "personal_map_apply_preview_count": personal_map_review.get("summary", {}).get("dry_run_apply_count"),
            "personal_map_live_apply_ready_count": personal_map_live_apply_proof.get("summary", {}).get("ready_for_live_apply_count"),
            "current_v1_local_lane_complete": final_audit.get("current_v1_local_lane_complete"),
            "full_product_grade_complete": final_audit.get("full_product_grade_complete"),
        },
        "authority": dict(AUTHORITY_BOUNDARY),
        "writes": [],
    }


def _metric(label: str, value: Any, *, status: Any = None) -> str:
    return (
        f"<div class='metric {_status_class(status if status is not None else value)}'>"
        f"<span>{_escape(label)}</span>"
        f"<strong>{_escape(value)}</strong>"
        "</div>"
    )


def _pill(value: Any, *, status: Any = None) -> str:
    return f"<span class='pill {_status_class(status if status is not None else value)}'>{_escape(value)}</span>"


def _surface_card(row: dict[str, Any]) -> str:
    summary = row.get("summary") or {}
    details = "".join(
        f"<li><span>{_escape(key)}</span><strong>{_escape(value)}</strong></li>"
        for key, value in list(summary.items())[:6]
        if not isinstance(value, (dict, list))
    )
    return (
        "<article class='surface-card'>"
        "<div class='card-top'>"
        f"<h2>{_escape(row.get('surface'))}</h2>"
        f"{_pill(row.get('status'), status=row.get('status'))}"
        "</div>"
        f"<ul>{details or '<li><span>status</span><strong>No compact details.</strong></li>'}</ul>"
        "</article>"
    )


def _pulse_card(card: dict[str, Any]) -> str:
    evidence = card.get("evidence") or []
    actions = card.get("recommended_actions") or []
    evidence_items = "".join(
        f"<li><code>{_escape(item.get('source_path') or item.get('path') or item.get('source_type'))}</code></li>"
        for item in evidence[:3]
    )
    action_items = "".join(
        f"<li>{_escape(item.get('label') or item.get('type'))}</li>"
        for item in actions[:3]
    )
    return (
        "<article class='pulse-card'>"
        "<div class='card-top'>"
        f"{_pill(card.get('card_class') or card.get('type'))}"
        f"{_pill(card.get('writeback_status'), status=card.get('writeback_status'))}"
        "</div>"
        f"<h2>{_escape(card.get('title'))}</h2>"
        f"<p>{_escape(card.get('summary'))}</p>"
        "<div class='two-col'>"
        f"<section><h3>Evidence</h3><ul>{evidence_items or '<li>No evidence shown.</li>'}</ul></section>"
        f"<section><h3>Actions</h3><ul>{action_items or '<li>No actions shown.</li>'}</ul></section>"
        "</div>"
        "</article>"
    )


def render_pulse_product_shell_html(model: dict[str, Any]) -> str:
    """Render the integrated Pulse product shell as static HTML."""

    summary = model.get("summary") or {}
    final = model.get("final_product_readiness") or {}
    authority = model.get("authority") or {}
    panels = model.get("panels") or {}
    approval = panels.get("approval_queue") or {}
    runtime_brain = panels.get("runtime_brain") or {}
    personal_map = panels.get("personal_map") or {}
    personal_map_review = panels.get("personal_map_review_apply") or {}
    personal_map_live_apply_proof = panels.get("personal_map_live_apply_proof") or {}
    surface_cards = "".join(_surface_card(row) for row in model.get("surface_statuses") or [])
    pulse_cards = "".join(_pulse_card(card) for card in (model.get("cards") or [])[:12])
    remaining = "".join(
        _pill(item, status="partial")
        for item in final.get("remaining_full_product_lanes", [])
    )
    blocked = [
        key.replace("_", " ")
        for key, value in sorted(authority.items())
        if value is False and key.endswith(("allowed", "enabled", "created", "server", "browser"))
    ]
    blocked_pills = "".join(_pill(item, status="blocked") for item in blocked)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ChaseOS Pulse Product Shell</title>
  <style>
    :root {{
      --bg: #f5f7f8;
      --panel: #ffffff;
      --ink: #141c24;
      --muted: #607180;
      --line: #d8e0e5;
      --soft: #eef3f4;
      --ok: #0f766e;
      --warn: #9a5b06;
      --risk: #a11d33;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Inter, Segoe UI, Arial, sans-serif; overflow-x: hidden; }}
    main {{ max-width: 1320px; margin: 0 auto; padding: 24px; display: grid; gap: 18px; }}
    header {{ display: grid; gap: 12px; padding-bottom: 18px; border-bottom: 1px solid var(--line); }}
    h1 {{ margin: 0; font-size: 36px; letter-spacing: 0; }}
    h2, h3 {{ letter-spacing: 0; }}
    .sub {{ color: var(--muted); max-width: 980px; line-height: 1.5; }}
    .metrics, .surfaces, .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }}
    .metric, .surface-card, .pulse-card, .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; min-width: 0; }}
    .metric span, .surface-card li span {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: 740; }}
    .metric strong {{ display: block; margin-top: 6px; font-size: 24px; overflow-wrap: anywhere; }}
    .pill {{ display: inline-flex; max-width: 100%; padding: 4px 8px; border-radius: 999px; background: var(--soft); color: var(--muted); font-size: 12px; margin: 2px 4px 2px 0; overflow-wrap: anywhere; }}
    .ok {{ color: var(--ok); }}
    .warn {{ color: var(--warn); }}
    .risk {{ color: var(--risk); }}
    .muted {{ color: var(--muted); }}
    .card-top {{ display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; align-items: start; }}
    .surface-card h2, .pulse-card h2 {{ margin: 4px 0 10px; font-size: 18px; }}
    ul {{ margin: 8px 0 0; padding-left: 18px; }}
    li {{ margin: 6px 0; overflow-wrap: anywhere; }}
    .two-col {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }}
    code {{ white-space: normal; overflow-wrap: anywhere; color: #203040; background: var(--soft); border-radius: 4px; padding: 1px 4px; }}
    @media (max-width: 720px) {{ main {{ padding: 14px; }} h1 {{ font-size: 30px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>ChaseOS Pulse</h1>
    <p class="sub">Integrated static local product shell over Pulse deck, Personal Map, Runtime Brain, approval queue, and final readiness contracts. This artifact adds no execution authority.</p>
    <code>{_escape(model.get('source_deck_path'))}</code>
  </header>
  <section class="metrics" aria-label="Pulse product metrics">
    {_metric('v1 local lane', summary.get('current_v1_local_lane_complete'), status=summary.get('current_v1_local_lane_complete'))}
    {_metric('full product grade', summary.get('full_product_grade_complete'), status='partial')}
    {_metric('cards', summary.get('card_count'))}
    {_metric('panels', summary.get('panel_count'))}
    {_metric('approval lanes', summary.get('approval_lane_count'))}
    {_metric('runtime cards', summary.get('runtime_card_count'))}
      {_metric('Personal Map candidates', summary.get('personal_map_candidate_count'))}
      {_metric('PM apply preview', summary.get('personal_map_apply_preview_count'))}
      {_metric('PM live-ready', summary.get('personal_map_live_apply_ready_count'))}
  </section>
  <section class="panel">
    <h2>Remaining Product Lanes</h2>
    <div>{remaining}</div>
  </section>
  <section>
    <h2>Surface Status</h2>
    <div class="surfaces">{surface_cards}</div>
  </section>
  <section class="panel">
    <h2>Personal Map</h2>
    <div class="metrics">
      {_metric('declared lanes', (personal_map.get('summary') or {}).get('declared_lane_count'))}
      {_metric('candidate nodes', (personal_map.get('summary') or {}).get('candidate_node_count'))}
      {_metric('candidate edges', (personal_map.get('summary') or {}).get('candidate_edge_count'))}
      {_metric('dry-run apply', (personal_map_review.get('summary') or {}).get('dry_run_apply_count'))}
      {_metric('live-ready candidates', (personal_map_live_apply_proof.get('summary') or {}).get('ready_for_live_apply_count'))}
      {_metric('applied graph', (personal_map_review.get('summary') or {}).get('applied_graph_present'), status=(personal_map_review.get('summary') or {}).get('applied_graph_present'))}
    </div>
  </section>
  <section class="panel">
    <h2>Runtime And Approval</h2>
    <div class="metrics">
      {_metric('approval status', (approval.get('summary') or {}).get('approval_center_status'), status=(approval.get('summary') or {}).get('approval_center_status'))}
      {_metric('approval actions', (approval.get('summary') or {}).get('action_count'))}
      {_metric('runtime dashboard', (runtime_brain.get('summary') or {}).get('dashboard_status'), status=(runtime_brain.get('summary') or {}).get('dashboard_status'))}
      {_metric('drift signals', (runtime_brain.get('summary') or {}).get('drift_signal_count'))}
      {_metric('repair candidates', (runtime_brain.get('summary') or {}).get('repair_incident_candidate_count'))}
    </div>
  </section>
  <section>
    <h2>Pulse Cards</h2>
    <div class="cards">{pulse_cards or '<article class="pulse-card"><h2>No cards found</h2><p>No user Pulse deck cards are available.</p></article>'}</div>
  </section>
  <section class="panel">
    <h2>Blocked Authority</h2>
    <div>{blocked_pills}</div>
  </section>
</main>
</body>
</html>
"""


def write_pulse_product_shell_html(
    vault_root: str | Path,
    *,
    deck_path: str | Path | None = None,
    output_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Write the integrated Pulse product shell under Pulse product-shell logs."""

    vault = _vault_path(vault_root)
    model = build_pulse_product_shell(vault, deck_path=deck_path, generated_at=generated_at)
    root = (vault / PRODUCT_SHELL_ROOT).resolve()
    if output_path is None:
        target = root / f"{_date_slug(model.get('generated_at'))}-pulse-product-shell.html"
    else:
        target = Path(output_path)
        target = target if target.is_absolute() else vault / target
    _assert_inside(target, root, "Pulse product shell output must stay under Pulse product-shell logs")
    root.mkdir(parents=True, exist_ok=True)
    target.write_text(render_pulse_product_shell_html(model), encoding="utf-8")
    model["writes"] = [_relative_to_vault(vault, target)]
    model["html_output_path"] = _relative_to_vault(vault, target)
    return model
