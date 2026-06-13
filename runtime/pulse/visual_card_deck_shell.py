"""Local-only visual ChaseOS Pulse card/deck shell.

The shell is a static product-surface artifact over existing Pulse contracts.
It renders current repo-local Pulse evidence; it does not submit feedback,
activate schedules, dispatch runtimes, call providers/connectors, or mutate
canonical state.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from runtime.pulse.approval_center import build_pulse_approval_center_readiness
from runtime.pulse.final_product_readiness_audit import build_pulse_final_product_readiness_audit
from runtime.pulse.local_surface import (
    PulseSurfaceError,
    _assert_inside,
    _relative_to_vault,
    _resolve_user_deck_json,
    _user_deck_root,
    build_pulse_surface_model,
)
from runtime.pulse.memory_runtime_readiness import build_pulse_memory_runtime_readiness
from runtime.studio.runtime_brain_dashboard import build_runtime_brain_dashboard_contract


SURFACE_ID = "chaseos_pulse_visual_card_deck_shell"


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _status_class(value: str | None) -> str:
    text = (value or "").lower()
    if "complete" in text or "pass" in text or "ready" in text:
        return "ok"
    if "partial" in text or "review" in text:
        return "warn"
    if "blocked" in text or "fail" in text or "missing" in text:
        return "risk"
    return "muted"


def _authority_boundary() -> dict[str, bool]:
    return {
        "read_only": True,
        "local_only": True,
        "writes_html_only_when_explicit": True,
        "feedback_submission_enabled": False,
        "candidate_apply_allowed": False,
        "mutates_memory": False,
        "mutates_personal_map": False,
        "updates_runtime_brains": False,
        "grants_permissions": False,
        "agent_bus_task_write_allowed": False,
        "runtime_dispatch_allowed": False,
        "provider_or_connector_call_allowed": False,
        "schedule_activation_allowed": False,
        "approval_execution_allowed": False,
        "canonical_writeback_allowed": False,
        "second_datastore_created": False,
        "rd_workbook_update_allowed": False,
    }


def _deck_card_summary(cards: list[dict[str, Any]]) -> dict[str, Any]:
    by_class: dict[str, int] = {}
    max_urgency = 0
    avg_confidence = 0.0
    for card in cards:
        card_class = str(card.get("card_class") or card.get("type") or "unknown")
        by_class[card_class] = by_class.get(card_class, 0) + 1
        max_urgency = max(max_urgency, int(card.get("urgency") or 0))
        avg_confidence += float(card.get("confidence") or 0.0)
    if cards:
        avg_confidence = round(avg_confidence / len(cards), 3)
    return {
        "card_count": len(cards),
        "classes": by_class,
        "max_urgency": max_urgency,
        "average_confidence": avg_confidence,
    }


def build_pulse_visual_card_deck_shell(
    vault_root: str | Path,
    *,
    deck_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build the visual Pulse shell model without writing artifacts."""

    vault = _vault_path(vault_root)
    surface = build_pulse_surface_model(vault, deck_path=deck_path)
    final_audit = build_pulse_final_product_readiness_audit(vault).to_dict()
    approval = build_pulse_approval_center_readiness(vault).to_dict()
    memory_runtime = build_pulse_memory_runtime_readiness(vault).to_dict()
    runtime_brain = build_runtime_brain_dashboard_contract(vault)
    cards = list(surface.get("cards") or [])

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "title": "ChaseOS Pulse",
        "subtitle": "Local visual card deck shell",
        "vault_root": str(vault),
        "source_deck_path": surface.get("source_deck_path"),
        "deck": surface.get("deck") or {},
        "cards": cards,
        "deck_card_summary": _deck_card_summary(cards),
        "final_product_readiness": {
            "audit_status": final_audit.get("audit_status"),
            "current_v1_local_lane_complete": final_audit.get("current_v1_local_lane_complete"),
            "full_product_grade_complete": final_audit.get("full_product_grade_complete"),
            "remaining_full_product_lanes": final_audit.get("remaining_full_product_lanes") or [],
            "next_recommended_pass": final_audit.get("next_recommended_pass"),
        },
        "approval_center": {
            "status": approval.get("approval_center_status"),
            "lane_count": approval.get("lane_count"),
            "action_count": approval.get("action_count"),
            "deck_count": approval.get("deck_count"),
            "candidate_item_count": approval.get("candidate_item_count"),
            "approval_request_count": approval.get("approval_request_count"),
            "lanes": approval.get("lanes") or [],
        },
        "memory_runtime": {
            "readiness_status": memory_runtime.get("readiness_status"),
            "memory_posture": memory_runtime.get("memory_posture"),
            "lane_count": memory_runtime.get("lane_count"),
            "runtime_count": memory_runtime.get("runtime_count"),
            "feedback_rule_count": memory_runtime.get("feedback_rule_count"),
            "personal_map_candidate_count": memory_runtime.get("personal_map_candidate_count"),
            "execution_repair_candidate_count": memory_runtime.get("execution_repair_candidate_count"),
        },
        "runtime_brain_dashboard": {
            "status": runtime_brain.get("status"),
            "metrics": runtime_brain.get("metrics", {}),
            "cards": runtime_brain.get("cards", []),
        },
        "authority": _authority_boundary(),
        "writes": [],
    }


def _metric(label: str, value: Any, *, status: str | None = None) -> str:
    klass = _status_class(status or str(value))
    return (
        f"<div class='metric {klass}'>"
        f"<span>{_escape(label)}</span>"
        f"<strong>{_escape(value)}</strong>"
        "</div>"
    )


def _pill(label: Any, *, status: str | None = None) -> str:
    return f"<span class='pill {_status_class(status or str(label))}'>{_escape(label)}</span>"


def _render_card(card: dict[str, Any]) -> str:
    evidence = "".join(
        "<li>"
        f"<code>{_escape(item.get('source_path'))}</code>"
        f"{_pill(item.get('trust_label'))}"
        f"<p>{_escape(item.get('summary'))}</p>"
        "</li>"
        for item in (card.get("evidence") or [])[:4]
    )
    actions = "".join(
        "<li>"
        f"{_escape(action.get('label'))}"
        f"{_pill('approval' if action.get('requires_operator_approval') else 'no approval')}"
        "</li>"
        for action in (card.get("recommended_actions") or [])[:4]
    )
    return (
        "<article class='card'>"
        "<div class='card-top'>"
        f"{_pill(card.get('card_class') or card.get('type'), status='partial')}"
        f"{_pill('urgency ' + str(card.get('urgency', 0)), status='partial')}"
        "</div>"
        f"<h2>{_escape(card.get('title'))}</h2>"
        f"<p class='summary'>{_escape(card.get('summary'))}</p>"
        "<div class='mini-grid'>"
        f"{_metric('confidence', card.get('confidence'), status='ready')}"
        f"{_metric('writeback', card.get('writeback_status'), status=card.get('writeback_status'))}"
        "</div>"
        "<h3>Evidence</h3>"
        f"<ul>{evidence or '<li>None shown.</li>'}</ul>"
        "<h3>Actions</h3>"
        f"<ul>{actions or '<li>None shown.</li>'}</ul>"
        "</article>"
    )


def render_pulse_visual_card_deck_shell_html(model: dict[str, Any]) -> str:
    """Render a complete static HTML Pulse visual shell."""

    deck = model.get("deck") or {}
    final = model.get("final_product_readiness") or {}
    approval = model.get("approval_center") or {}
    memory = model.get("memory_runtime") or {}
    runtime = model.get("runtime_brain_dashboard") or {}
    authority = model.get("authority") or {}
    summary = model.get("deck_card_summary") or {}

    lane_pills = "".join(
        _pill(lane, status="partial") for lane in final.get("remaining_full_product_lanes", [])
    )
    approval_lanes = "".join(
        "<li>"
        f"{_escape(lane.get('label') or lane.get('lane_id'))}"
        f"{_pill(lane.get('status'))}"
        f"{_pill('items ' + str(lane.get('item_count', 0)), status='ready')}"
        "</li>"
        for lane in approval.get("lanes", [])
    )
    runtime_cards = "".join(
        "<article class='runtime-card'>"
        f"<h3>{_escape(card.get('runtime_id'))}</h3>"
        f"{_pill(card.get('status'), status=card.get('status'))}"
        f"<p>{_escape((card.get('profile') or {}).get('primary_role'))}</p>"
        f"{_pill('missing ' + str(len(card.get('missing_families') or [])), status=card.get('status'))}"
        "</article>"
        for card in runtime.get("cards", [])
    )
    cards_html = "".join(_render_card(card) for card in model.get("cards", []))
    blocked = [
        key.replace("_", " ")
        for key, value in sorted(authority.items())
        if value is False and key.endswith(("allowed", "enabled", "created"))
    ]

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(model.get('title'))}</title>
  <style>
    :root {{
      --bg: #f5f7fa;
      --panel: #ffffff;
      --ink: #121826;
      --muted: #607086;
      --line: #d9e0ea;
      --soft: #eef3f7;
      --ok: #0f766e;
      --warn: #a15c07;
      --risk: #a11d33;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    main {{ max-width: 1280px; margin: 0 auto; padding: 22px; }}
    header {{ display: grid; gap: 12px; padding-bottom: 16px; border-bottom: 1px solid var(--line); }}
    h1 {{ margin: 0; font-size: 2rem; letter-spacing: 0; }}
    h2 {{ margin: 10px 0 8px; font-size: 1.05rem; letter-spacing: 0; }}
    h3 {{ margin: 12px 0 6px; font-size: .82rem; letter-spacing: 0; color: var(--muted); }}
    code {{ background: var(--soft); border: 1px solid var(--line); border-radius: 4px; padding: 1px 5px; overflow-wrap: anywhere; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; }}
    .section {{ margin-top: 16px; }}
    .metric, .card, .runtime-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      min-width: 0;
    }}
    .metric span {{ display: block; color: var(--muted); font-size: .76rem; }}
    .metric strong {{ display: block; overflow-wrap: anywhere; }}
    .ok {{ border-color: #9ed9cf; }}
    .warn {{ border-color: #fed59a; }}
    .risk {{ border-color: #f6a0ad; }}
    .muted {{ border-color: var(--line); }}
    .pill {{
      display: inline-block;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 8px;
      margin: 2px 4px 2px 0;
      color: var(--muted);
      background: #fff;
      max-width: 100%;
      overflow-wrap: anywhere;
      font-size: .76rem;
    }}
    .pill.ok {{ color: var(--ok); border-color: #9ed9cf; }}
    .pill.warn {{ color: var(--warn); border-color: #fed59a; }}
    .pill.risk {{ color: var(--risk); border-color: #f6a0ad; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 12px; align-items: start; }}
    .card-top {{ display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; }}
    .summary {{ color: #263244; }}
    .mini-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }}
    ul {{ margin: 0; padding-left: 18px; }}
    li {{ margin: 5px 0; overflow-wrap: anywhere; }}
    .runtime-list {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px; }}
    .blocked {{ display: flex; flex-wrap: wrap; gap: 4px; }}
    @media (max-width: 720px) {{
      main {{ padding: 14px; }}
      .mini-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>{_escape(model.get('title'))}</h1>
    <div class="grid">
      {_metric('source deck', model.get('source_deck_path'))}
      {_metric('deck id', deck.get('deck_id'))}
      {_metric('cards', summary.get('card_count'))}
      {_metric('max urgency', summary.get('max_urgency'))}
      {_metric('average confidence', summary.get('average_confidence'))}
      {_metric('canonical writeback', 'blocked', status='blocked')}
    </div>
  </header>
  <section class="section">
    <div class="grid">
      {_metric('v1 local lane', final.get('current_v1_local_lane_complete'), status='complete' if final.get('current_v1_local_lane_complete') else 'partial')}
      {_metric('full product grade', final.get('full_product_grade_complete'), status='partial')}
      {_metric('approval center', approval.get('status'), status=approval.get('status'))}
      {_metric('memory runtime', memory.get('readiness_status'), status=memory.get('readiness_status'))}
      {_metric('runtime brain', runtime.get('status'), status=runtime.get('status'))}
      {_metric('next lane', final.get('next_recommended_pass'), status='partial')}
    </div>
  </section>
  <section class="section">
    <h2>Remaining Product Lanes</h2>
    <div>{lane_pills}</div>
  </section>
  <section class="section">
    <h2>Approval Center</h2>
    <div class="grid">
      {_metric('lanes', approval.get('lane_count'))}
      {_metric('actions', approval.get('action_count'))}
      {_metric('candidates', approval.get('candidate_item_count'))}
      {_metric('approval requests', approval.get('approval_request_count'))}
    </div>
    <ul>{approval_lanes}</ul>
  </section>
  <section class="section">
    <h2>Memory And Runtime</h2>
    <div class="grid">
      {_metric('memory posture', memory.get('memory_posture'), status=memory.get('memory_posture'))}
      {_metric('runtimes', memory.get('runtime_count'))}
      {_metric('feedback rules', memory.get('feedback_rule_count'))}
      {_metric('repair candidates', memory.get('execution_repair_candidate_count'))}
    </div>
  </section>
  <section class="section">
    <h2>Runtime Brain</h2>
    <div class="grid">
      {_metric('ready runtimes', (runtime.get('metrics') or {}).get('ready_runtime_count'))}
      {_metric('partial runtimes', (runtime.get('metrics') or {}).get('partial_runtime_count'), status='partial')}
      {_metric('missing families', (runtime.get('metrics') or {}).get('missing_family_count'), status='partial')}
      {_metric('action hints', (runtime.get('metrics') or {}).get('action_hint_count'))}
    </div>
    <div class="runtime-list">{runtime_cards}</div>
  </section>
  <section class="section">
    <h2>Pulse Cards</h2>
    <div class="cards">{cards_html}</div>
  </section>
  <section class="section">
    <h2>Blocked Authority</h2>
    <div class="blocked">{''.join(_pill(item, status='blocked') for item in blocked)}</div>
  </section>
</main>
</body>
</html>
"""


def _default_output_path(deck_path: Path) -> Path:
    return deck_path.with_name(f"{deck_path.stem}.visual-shell.html")


def write_pulse_visual_card_deck_shell_html(
    vault_root: str | Path,
    *,
    deck_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Write the static visual shell beside user Pulse deck artifacts."""

    vault = _vault_path(vault_root)
    resolved_deck = _resolve_user_deck_json(vault, deck_path)
    model = build_pulse_visual_card_deck_shell(vault, deck_path=resolved_deck)
    target = Path(output_path) if output_path is not None else _default_output_path(resolved_deck)
    target = target if target.is_absolute() else vault / target
    target = target.resolve()
    _assert_inside(
        target,
        _user_deck_root(vault),
        "Pulse visual shell output must stay inside 07_LOGS/Pulse-Decks/users/",
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_pulse_visual_card_deck_shell_html(model), encoding="utf-8")
    model = dict(model)
    model["html_output_path"] = _relative_to_vault(vault, target)
    model["writes"] = [_relative_to_vault(vault, target)]
    return model
