"""Local-only ChaseOS Pulse Runtime Brain visualization.

This module renders the existing read-only Studio Runtime Brain dashboard
contract as a static Pulse artifact. It does not update runtime brains, apply
repair memory, change runtime navigation maps, grant permissions, dispatch
runtimes, write Agent Bus tasks, or mutate canonical ChaseOS state.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import now_utc
from runtime.studio.runtime_brain_dashboard import build_runtime_brain_dashboard_contract


SURFACE_ID = "chaseos_pulse_runtime_brain_visualization"
VISUALIZATION_ROOT = Path("07_LOGS") / "Pulse-Decks" / "runtime-brains"

AUTHORITY_BOUNDARY = {
    "read_only": True,
    "local_only": True,
    "writes_html_only_when_explicit": True,
    "updates_runtime_brains": False,
    "updates_runtime_navigation_maps": False,
    "updates_agent_identity_ledgers": False,
    "applies_execution_repair_memory": False,
    "applies_feedback_rules": False,
    "applies_personal_map_candidates": False,
    "grants_permissions": False,
    "self_upgrade_active": False,
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
    if "ready" in text or "pass" in text or text == "0":
        return "ok"
    if "partial" in text or "candidate" in text or "review" in text:
        return "warn"
    if "blocked" in text or "missing" in text or "fail" in text:
        return "risk"
    return "muted"


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _blocked_authority(authority: dict[str, Any]) -> list[str]:
    return [
        key.replace("_", " ")
        for key, value in sorted(authority.items())
        if value is False
        and key.endswith(("allowed", "created", "active", "maps", "ledgers", "brains"))
    ]


def _runtime_summary(card: dict[str, Any]) -> dict[str, Any]:
    profile = card.get("profile") or {}
    identity = card.get("identity_ledger") or {}
    navigation = card.get("runtime_navigation") or {}
    repair = card.get("execution_repair_memory") or {}
    scorecard = card.get("scorecard") or {}
    return {
        "runtime_id": card.get("runtime_id"),
        "status": card.get("status"),
        "primary_role": profile.get("primary_role"),
        "strength_count": len(_as_list(profile.get("strengths"))),
        "weakness_count": len(_as_list(profile.get("known_weaknesses"))),
        "missing_family_count": len(_as_list(card.get("missing_families"))),
        "drift_signal_count": int(identity.get("drift_signal_count") or 0),
        "repair_incident_candidate_count": int(repair.get("incident_candidate_count") or 0),
        "preferred_route_count": int(navigation.get("preferred_route_count") or 0),
        "risk_zone_count": int(navigation.get("risk_zone_count") or 0),
        "total_executions": int(scorecard.get("total_executions") or 0),
        "success_count": int(scorecard.get("success_count") or 0),
        "failed_count": int(scorecard.get("failed_count") or 0),
        "compliance_rate": scorecard.get("compliance_rate"),
        "action_hint_count": len(_as_list(card.get("action_hints"))),
    }


def build_runtime_brain_visualization(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a read-only visualization packet over runtime brain evidence."""

    vault = _vault_path(vault_root)
    dashboard = build_runtime_brain_dashboard_contract(vault, runtime_id=runtime_id)
    cards = list(dashboard.get("cards") or [])
    summaries = [_runtime_summary(card) for card in cards]
    runtime_filter = runtime_id or "all"

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "generated_at": generated_at or now_utc(),
        "vault_root": str(vault),
        "runtime_filter": runtime_filter,
        "source_surface": dashboard.get("surface"),
        "source_refs": [
            "runtime/studio/runtime_brain_dashboard.py",
            "runtime/pulse/memory_runtime_readiness.py",
            "runtime/memory/inspector.py",
            "runtime/pulse/runtime_brain_visualization.py",
        ],
        "summary": {
            "dashboard_status": dashboard.get("status"),
            "runtime_card_count": len(cards),
            "missing_family_count": int((dashboard.get("metrics") or {}).get("missing_family_count") or 0),
            "drift_signal_count": int((dashboard.get("metrics") or {}).get("drift_signal_count") or 0),
            "repair_incident_candidate_count": int(
                (dashboard.get("metrics") or {}).get("repair_incident_candidate_count") or 0
            ),
            "action_hint_count": int((dashboard.get("metrics") or {}).get("action_hint_count") or 0),
            "runtime_brain_updates_enabled": False,
            "repair_memory_apply_enabled": False,
            "permission_expansion_enabled": False,
            "self_upgrade_active": False,
        },
        "views": dashboard.get("views") or [],
        "runtime_summaries": summaries,
        "runtime_cards": cards,
        "dashboard_contract": dashboard,
        "authority": dict(AUTHORITY_BOUNDARY),
        "blocked_effects": list(dashboard.get("blocked_effects") or []),
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


def _list_items(items: list[Any], empty: str) -> str:
    if not items:
        return f"<li>{_escape(empty)}</li>"
    return "".join(f"<li>{_escape(item)}</li>" for item in items[:8])


def _render_runtime_card(card: dict[str, Any]) -> str:
    profile = card.get("profile") or {}
    identity = card.get("identity_ledger") or {}
    navigation = card.get("runtime_navigation") or {}
    repair = card.get("execution_repair_memory") or {}
    scorecard = card.get("scorecard") or {}
    hints = card.get("action_hints") or []
    hint_rows = "".join(
        "<li>"
        f"{_escape(hint.get('label'))}"
        f"{_pill('review' if hint.get('requires_operator_review') else 'inspect')}"
        f"{_pill('non-executing')}"
        "</li>"
        for hint in hints[:8]
    )
    return (
        "<article class='runtime-card'>"
        "<div class='card-top'>"
        f"{_pill(card.get('runtime_id'))}"
        f"{_pill(card.get('status'), status=card.get('status'))}"
        f"{_pill('missing ' + str(len(card.get('missing_families') or [])), status=card.get('status'))}"
        "</div>"
        f"<h2>{_escape(profile.get('primary_role') or 'Runtime brain')}</h2>"
        "<div class='runtime-grid'>"
        f"{_metric('drift signals', identity.get('drift_signal_count'), status=identity.get('drift_signal_count'))}"
        f"{_metric('repair candidates', repair.get('incident_candidate_count'), status=repair.get('incident_candidate_count'))}"
        f"{_metric('safe write paths', navigation.get('safe_write_path_count'), status='ready')}"
        f"{_metric('compliance', scorecard.get('compliance_rate'), status='ready')}"
        "</div>"
        "<div class='columns'>"
        "<section><h3>Strengths</h3><ul>"
        f"{_list_items(_as_list(profile.get('strengths')), 'No strengths recorded yet.')}"
        "</ul></section>"
        "<section><h3>Known Weaknesses</h3><ul>"
        f"{_list_items(_as_list(profile.get('known_weaknesses')), 'No weaknesses recorded yet.')}"
        "</ul></section>"
        "<section><h3>Runtime Navigation</h3><ul>"
        f"<li>Preferred routes: {_escape(navigation.get('preferred_route_count'))}</li>"
        f"<li>Trusted zones: {_escape(navigation.get('trusted_zone_count'))}</li>"
        f"<li>Risk zones: {_escape(navigation.get('risk_zone_count'))}</li>"
        f"<li>Escalation points: {_escape(navigation.get('escalation_point_count'))}</li>"
        "</ul></section>"
        "<section><h3>Non-Executing Hints</h3><ul>"
        f"{hint_rows or '<li>No action hints.</li>'}"
        "</ul></section>"
        "</div>"
        "</article>"
    )


def render_runtime_brain_visualization_html(model: dict[str, Any]) -> str:
    """Render Runtime Brain visualization as static HTML."""

    summary = model.get("summary") or {}
    authority = model.get("authority") or {}
    cards = model.get("runtime_cards") or []
    blocked = _blocked_authority(authority)
    runtime_cards = "".join(_render_runtime_card(card) for card in cards)
    blocked_items = "".join(f"<li>{_escape(item)}</li>" for item in blocked)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ChaseOS Pulse Runtime Brain</title>
  <style>
    :root {{
      --bg: #f4f6f8;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #637385;
      --line: #d8e0e8;
      --ok: #0f766e;
      --warn: #9a5b06;
      --risk: #a11d33;
      --soft: #eef3f7;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Inter, Segoe UI, Arial, sans-serif; }}
    header {{ padding: 28px clamp(18px, 4vw, 56px) 18px; border-bottom: 1px solid var(--line); }}
    main {{ padding: 24px clamp(18px, 4vw, 56px) 48px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
    h2, h3 {{ letter-spacing: 0; }}
    .sub {{ color: var(--muted); max-width: 980px; line-height: 1.5; }}
    .metrics, .runtime-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }}
    .runtime-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-top: 14px; }}
    .metric, .runtime-card, .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .metric strong {{ display: block; margin-top: 6px; font-size: 24px; }}
    .card-top {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    .pill {{ display: inline-flex; max-width: 100%; padding: 4px 8px; border-radius: 999px; background: var(--soft); color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }}
    .ok {{ color: var(--ok); }}
    .warn {{ color: var(--warn); }}
    .risk {{ color: var(--risk); }}
    .runtime-card h2 {{ margin: 12px 0; font-size: 20px; }}
    .columns {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    ul {{ margin: 8px 0 0; padding-left: 18px; }}
    li {{ margin: 6px 0; overflow-wrap: anywhere; }}
    code {{ white-space: normal; overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <header>
    <h1>ChaseOS Pulse Runtime Brain</h1>
    <p class="sub">Static, local-only Runtime Brain visualization over the read-only Studio contract. It exposes runtime profile, identity, navigation, repair, scorecard, and non-executing review hints without applying changes or granting authority.</p>
  </header>
  <main>
    <section class="metrics" aria-label="Runtime Brain metrics">
      {_metric('dashboard status', summary.get('dashboard_status'), status=summary.get('dashboard_status'))}
      {_metric('runtime cards', summary.get('runtime_card_count'), status='ready')}
      {_metric('missing families', summary.get('missing_family_count'), status=summary.get('missing_family_count'))}
      {_metric('drift signals', summary.get('drift_signal_count'), status=summary.get('drift_signal_count'))}
      {_metric('repair candidates', summary.get('repair_incident_candidate_count'), status=summary.get('repair_incident_candidate_count'))}
      {_metric('action hints', summary.get('action_hint_count'), status='partial')}
    </section>
    <section>
      <h2>Runtime Cards</h2>
      <div class="runtime-cards">{runtime_cards or '<article class="runtime-card"><h2>No runtime brain cards</h2><p>No runtime memory evidence is present for this filter.</p></article>'}</div>
    </section>
    <section class="panel">
      <h2>Blocked Authority</h2>
      <ul>{blocked_items}</ul>
    </section>
  </main>
</body>
</html>
"""


def write_runtime_brain_visualization_html(
    vault_root: str | Path,
    *,
    runtime_id: str | None = None,
    output_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Write a static Runtime Brain visualization under Pulse logs."""

    vault = _vault_path(vault_root)
    model = build_runtime_brain_visualization(
        vault,
        runtime_id=runtime_id,
        generated_at=generated_at,
    )
    root = (vault / VISUALIZATION_ROOT).resolve()
    if output_path is None:
        suffix = "runtime-brain-visualization"
        if runtime_id and runtime_id != "all":
            suffix = f"runtime-brain-{runtime_id}"
        target = root / f"{_date_slug(model.get('generated_at'))}-{suffix}.html"
    else:
        target = Path(output_path)
        target = target if target.is_absolute() else vault / target
    _assert_inside(target, root, "Runtime Brain visualization output must stay under Pulse runtime-brain logs")
    root.mkdir(parents=True, exist_ok=True)
    target.write_text(render_runtime_brain_visualization_html(model), encoding="utf-8")
    model["writes"] = [_relative_to_vault(vault, target)]
    model["html_output_path"] = _relative_to_vault(vault, target)
    return model
