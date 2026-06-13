"""Local-only ChaseOS Pulse Approval Queue UI.

This module renders the existing Pulse approval-center readiness contract and
candidate inspector snapshot as a static approval queue artifact. It is a
display surface only: it does not grant approvals, execute approvals, persist
review decisions, apply candidates, write Agent Bus tasks, dispatch runtimes,
activate schedules, call providers/connectors, approve memory, or mutate
canonical state.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from runtime.pulse.approval_center import build_pulse_approval_center_readiness
from runtime.pulse.candidate_inspector import build_candidate_inspector_snapshot
from runtime.pulse.card_schema import now_utc


SURFACE_ID = "chaseos_pulse_approval_queue_ui"
APPROVAL_QUEUE_ROOT = Path("07_LOGS") / "Pulse-Decks" / "approval-queue"

AUTHORITY_BOUNDARY = {
    "read_only": True,
    "local_only": True,
    "writes_html_only_when_explicit": True,
    "writes_status_artifact": False,
    "writes_review_decisions": False,
    "writes_feedback_candidates": False,
    "applies_candidates": False,
    "grants_approvals": False,
    "executes_approval": False,
    "agent_bus_task_write_allowed": False,
    "runtime_dispatch_allowed": False,
    "provider_or_connector_call_allowed": False,
    "schedule_activation_allowed": False,
    "memory_approval_allowed": False,
    "canonical_writeback_allowed": False,
    "mutates_canonical_state": False,
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
    if "ready" in text or "available" in text or text == "0":
        return "ok"
    if "blocked" in text or "missing" in text or "fail" in text:
        return "risk"
    if "pending" in text or "review" in text or "candidate" in text:
        return "warn"
    return "muted"


def _compact_candidate(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_id": item.get("item_id"),
        "item_kind": item.get("item_kind"),
        "candidate_kind": item.get("candidate_kind"),
        "status": item.get("status"),
        "title": item.get("title"),
        "summary": item.get("summary"),
        "runtime_id": item.get("runtime_id"),
        "target_ref": item.get("target_ref"),
        "source_log_path": item.get("source_log_path"),
        "source_deck_path": item.get("source_deck_path"),
        "created_at": item.get("created_at"),
        "decision_type": item.get("decision_type"),
        "execution_allowed": False,
        "apply_allowed": False,
    }


def build_pulse_approval_queue_ui(
    vault_root: str | Path,
    *,
    request_id: str | None = None,
    evidence_id: str | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a static approval queue UI packet without writing artifacts."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()
    readiness = build_pulse_approval_center_readiness(
        vault,
        request_id=request_id,
        evidence_id=evidence_id,
        generated_at=timestamp,
        bus_tasks=[],
    ).to_dict()
    candidates = build_candidate_inspector_snapshot(vault).to_dict()
    candidate_rows = [_compact_candidate(item) for item in candidates.get("items", [])]

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "request_id": request_id,
        "evidence_id": evidence_id,
        "source_refs": sorted(
            {
                "runtime/pulse/approval_center.py",
                "runtime/pulse/candidate_inspector.py",
                "runtime/pulse/approval_queue_ui.py",
                *readiness.get("source_refs", []),
                *candidates.get("source_log_paths", []),
            }
        ),
        "summary": {
            "approval_center_status": readiness.get("approval_center_status"),
            "lane_count": readiness.get("lane_count"),
            "action_count": readiness.get("action_count"),
            "deck_count": readiness.get("deck_count"),
            "candidate_item_count": readiness.get("candidate_item_count"),
            "pending_feedback_count": readiness.get("pending_feedback_count"),
            "review_decision_count": readiness.get("review_decision_count"),
            "approval_request_count": readiness.get("approval_request_count"),
            "missing_approval_key_count": len(readiness.get("missing_approval_keys") or []),
            "candidate_row_count": len(candidate_rows),
            "approval_execution_enabled": False,
            "candidate_apply_enabled": False,
        },
        "lanes": readiness.get("lanes", []),
        "action_previews": readiness.get("action_previews", []),
        "candidate_rows": candidate_rows,
        "readiness": readiness,
        "candidate_inspector": candidates,
        "authority": dict(AUTHORITY_BOUNDARY),
        "blocked_effects": readiness.get("blocked_effects", []),
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


def _lane_card(lane: dict[str, Any]) -> str:
    refs = "".join(f"<li><code>{_escape(ref)}</code></li>" for ref in (lane.get("source_refs") or [])[:4])
    refs_html = refs or '<li class="muted">No source refs in this lane.</li>'
    return (
        "<article class='lane-card'>"
        "<div class='lane-top'>"
        f"<h2>{_escape(lane.get('label'))}</h2>"
        f"{_pill(lane.get('status'))}"
        "</div>"
        "<dl>"
        f"<dt>Items</dt><dd>{_escape(lane.get('item_count'))}</dd>"
        f"<dt>Pending</dt><dd>{_escape(lane.get('pending_count'))}</dd>"
        f"<dt>Ready</dt><dd>{_escape(lane.get('ready_count'))}</dd>"
        f"<dt>Blocked</dt><dd>{_escape(lane.get('blocked_count'))}</dd>"
        "</dl>"
        f"<ul>{refs_html}</ul>"
        "</article>"
    )


def _candidate_row(row: dict[str, Any]) -> str:
    source = row.get("source_log_path") or row.get("source_deck_path") or ""
    return (
        "<tr>"
        f"<td>{_pill(row.get('item_kind'))}</td>"
        f"<td><strong>{_escape(row.get('title'))}</strong><p>{_escape(row.get('summary'))}</p></td>"
        f"<td>{_escape(row.get('status'))}</td>"
        f"<td>{_escape(row.get('runtime_id') or row.get('target_ref') or '')}</td>"
        f"<td><code>{_escape(source)}</code></td>"
        "</tr>"
    )


def _action_row(action: dict[str, Any]) -> str:
    command = " ".join(str(part) for part in action.get("command_preview") or [])
    return (
        "<tr>"
        f"<td>{_escape(action.get('label'))}</td>"
        f"<td>{_escape(action.get('lane_id'))}</td>"
        f"<td>{_escape(action.get('action_type'))}</td>"
        f"<td>{_escape(action.get('execution_allowed'))}</td>"
        f"<td><code>{_escape(command)}</code></td>"
        "</tr>"
    )


def render_pulse_approval_queue_ui_html(model: dict[str, Any]) -> str:
    """Render the Pulse approval queue as static HTML."""

    summary = model.get("summary") or {}
    lanes = model.get("lanes") or []
    candidates = model.get("candidate_rows") or []
    actions = model.get("action_previews") or []
    authority = model.get("authority") or {}
    lane_cards = "".join(_lane_card(lane) for lane in lanes)
    candidate_rows = "".join(_candidate_row(row) for row in candidates[:120])
    action_rows = "".join(_action_row(action) for action in actions)
    blocked = [
        key.replace("_", " ")
        for key, value in sorted(authority.items())
        if value is False and key.endswith(("allowed", "created", "approvals"))
    ]
    blocked_items = "".join(f"<li>{_escape(item)}</li>" for item in blocked)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ChaseOS Pulse Approval Queue</title>
  <style>
    :root {{
      --bg: #f5f7fa;
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
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Inter, Segoe UI, Arial, sans-serif; overflow-x: hidden; }}
    header {{ padding: 28px clamp(18px, 4vw, 56px) 18px; border-bottom: 1px solid var(--line); background: var(--panel); }}
    main {{ padding: 24px clamp(18px, 4vw, 56px) 48px; display: grid; gap: 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
    h2, h3 {{ letter-spacing: 0; }}
    .sub {{ color: var(--muted); max-width: 980px; line-height: 1.5; }}
    .metrics, .lane-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .metric, .lane-card, .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; min-width: 0; }}
    .metric span, dt, th {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: 760; }}
    .metric strong {{ display: block; margin-top: 6px; font-size: 24px; overflow-wrap: anywhere; }}
    .pill {{ display: inline-flex; max-width: 100%; padding: 4px 8px; border-radius: 999px; background: var(--soft); color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }}
    .ok {{ color: var(--ok); }}
    .warn {{ color: var(--warn); }}
    .risk {{ color: var(--risk); }}
    .muted {{ color: var(--muted); }}
    .lane-top {{ display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; margin-bottom: 12px; }}
    .lane-top h2 {{ margin: 0; font-size: 18px; }}
    dl {{ display: grid; grid-template-columns: 86px minmax(0, 1fr); gap: 7px 10px; margin: 0 0 12px; }}
    dd {{ margin: 0; min-width: 0; }}
    ul {{ margin: 8px 0 0; padding-left: 18px; }}
    li {{ margin: 5px 0; overflow-wrap: anywhere; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th, td {{ text-align: left; border-bottom: 1px solid var(--line); padding: 10px; vertical-align: top; overflow-wrap: anywhere; }}
    td p {{ margin: 4px 0 0; color: var(--muted); }}
    code {{ white-space: normal; overflow-wrap: anywhere; color: #26313d; }}
    @media (max-width: 760px) {{
      table {{ display: block; overflow-x: auto; }}
      .lane-top {{ display: grid; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>ChaseOS Pulse Approval Queue</h1>
    <p class="sub">Static, local-only approval queue over Pulse readiness and candidate lanes. It shows what needs review without granting approvals, applying candidates, writing Agent Bus tasks, or mutating canonical state.</p>
  </header>
  <main>
    <section class="metrics" aria-label="Approval queue metrics">
      {_metric('status', summary.get('approval_center_status'), status=summary.get('approval_center_status'))}
      {_metric('lanes', summary.get('lane_count'), status='ready')}
      {_metric('actions', summary.get('action_count'), status='review')}
      {_metric('candidate rows', summary.get('candidate_row_count'), status='review')}
      {_metric('approval requests', summary.get('approval_request_count'), status='review')}
      {_metric('missing keys', summary.get('missing_approval_key_count'), status=summary.get('missing_approval_key_count'))}
    </section>
    <section>
      <h2>Review Lanes</h2>
      <div class="lane-grid">{lane_cards}</div>
    </section>
    <section class="panel">
      <h2>Candidate Queue</h2>
      <table>
        <thead><tr><th>Kind</th><th>Candidate</th><th>Status</th><th>Target</th><th>Source</th></tr></thead>
        <tbody>{candidate_rows or '<tr><td colspan="5">No candidate rows.</td></tr>'}</tbody>
      </table>
    </section>
    <section class="panel">
      <h2>Display Actions</h2>
      <table>
        <thead><tr><th>Action</th><th>Lane</th><th>Type</th><th>Execution</th><th>Preview</th></tr></thead>
        <tbody>{action_rows or '<tr><td colspan="5">No action previews.</td></tr>'}</tbody>
      </table>
    </section>
    <section class="panel">
      <h2>Blocked Authority</h2>
      <ul>{blocked_items}</ul>
    </section>
  </main>
</body>
</html>
"""


def write_pulse_approval_queue_ui_html(
    vault_root: str | Path,
    *,
    request_id: str | None = None,
    evidence_id: str | None = None,
    output_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Write a static approval queue UI artifact under Pulse logs."""

    vault = _vault_path(vault_root)
    model = build_pulse_approval_queue_ui(
        vault,
        request_id=request_id,
        evidence_id=evidence_id,
        generated_at=generated_at,
    )
    root = (vault / APPROVAL_QUEUE_ROOT).resolve()
    if output_path is None:
        target = root / f"{_date_slug(model.get('generated_at'))}-approval-queue.html"
    else:
        target = Path(output_path)
        target = target if target.is_absolute() else vault / target
    _assert_inside(target, root, "Approval Queue UI output must stay under Pulse approval-queue logs")
    root.mkdir(parents=True, exist_ok=True)
    target.write_text(render_pulse_approval_queue_ui_html(model), encoding="utf-8")
    model["writes"] = [_relative_to_vault(vault, target)]
    model["html_output_path"] = _relative_to_vault(vault, target)
    return model
