"""Personal Map review/apply surface for ChaseOS Pulse.

This surface previews the existing governed Personal Map candidate apply lane.
It does not apply candidates itself. The only live apply path remains
``chaseos pulse apply-decisions --kind personal_map --live``.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from runtime.memory.candidate_store import build_personal_map_candidate_queue
from runtime.pulse.candidate_apply import apply_reviewed_candidates
from runtime.pulse.card_schema import now_utc
from runtime.pulse.review_decision_log import load_review_decisions


SURFACE_ID = "chaseos_pulse_personal_map_review_apply_surface"
REVIEW_APPLY_ROOT = Path("07_LOGS") / "Pulse-Decks" / "personal-map-review"
PERSONAL_MAP_GRAPH_PATH = Path("runtime") / "memory" / "personal-map" / "graph.json"
APPLY_REGISTRY_PATH = (
    Path("07_LOGS") / "Pulse-Decks" / "apply-registry" / "applied-decisions.json"
)

AUTHORITY_BOUNDARY = {
    "read_only": True,
    "local_only": True,
    "writes_html_only_when_explicit": True,
    "runs_apply_command": False,
    "applies_personal_map_candidates": False,
    "writes_runtime_memory_graph": False,
    "approves_memory": False,
    "creates_tasks": False,
    "updates_now": False,
    "updates_project_files": False,
    "updates_knowledge": False,
    "updates_runtime_brains": False,
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


def _load_applied_decision_ids(vault: Path) -> set[str]:
    path = vault / APPLY_REGISTRY_PATH
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {str(item) for item in data.get("applied_decision_ids") or []}


def _load_personal_map_graph_summary(vault: Path) -> dict[str, Any]:
    path = vault / PERSONAL_MAP_GRAPH_PATH
    if not path.exists():
        return {
            "graph_present": False,
            "graph_path": PERSONAL_MAP_GRAPH_PATH.as_posix(),
            "node_count": 0,
            "edge_count": 0,
            "updated_at": None,
            "read_error": None,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("graph JSON root is not an object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "graph_present": True,
            "graph_path": PERSONAL_MAP_GRAPH_PATH.as_posix(),
            "node_count": 0,
            "edge_count": 0,
            "updated_at": None,
            "read_error": str(exc),
        }
    nodes = data.get("nodes") if isinstance(data.get("nodes"), dict) else {}
    edges = data.get("edges") if isinstance(data.get("edges"), dict) else {}
    return {
        "graph_present": True,
        "graph_path": PERSONAL_MAP_GRAPH_PATH.as_posix(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "updated_at": data.get("updated_at"),
        "read_error": None,
    }


def _latest_decisions_by_candidate(vault: Path) -> dict[str, dict[str, Any]]:
    decisions = load_review_decisions(vault, candidate_kind="personal_map")
    latest: dict[str, dict[str, Any]] = {}
    for decision in sorted(decisions, key=lambda item: item.created_at):
        latest[decision.candidate_id] = decision.to_dict()
    return latest


def _candidate_row(candidate: Any, decisions: dict[str, dict[str, Any]], applied: set[str]) -> dict[str, Any]:
    target_ref = None
    label = candidate.candidate_type
    if candidate.node is not None:
        target_ref = candidate.node.node_id
        label = candidate.node.label
    if candidate.edge is not None:
        target_ref = candidate.edge.edge_id
        label = candidate.edge.relation

    decision = decisions.get(candidate.candidate_id)
    decision_id = decision.get("decision_id") if decision else None
    decision_type = decision.get("decision_type") if decision else None
    return {
        "candidate_id": candidate.candidate_id,
        "candidate_type": candidate.candidate_type,
        "label": label,
        "target_ref": target_ref,
        "status": candidate.status,
        "reason": candidate.reason,
        "decision_id": decision_id,
        "decision_type": decision_type,
        "approved_for_future_apply": decision_type == "approve_for_future_apply",
        "already_applied": bool(decision_id and decision_id in applied),
        "source_card_id": candidate.source_card_id,
        "source_deck_path": candidate.source_deck_path,
        "created_at": candidate.created_at,
    }


def build_personal_map_review_apply_surface(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a read-only surface over Personal Map review/apply readiness."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()
    queue = build_personal_map_candidate_queue(vault)
    decisions = _latest_decisions_by_candidate(vault)
    applied_decision_ids = _load_applied_decision_ids(vault)
    apply_preview = apply_reviewed_candidates(vault, dry_run=True, candidate_kind="personal_map")
    graph_summary = _load_personal_map_graph_summary(vault)
    candidate_rows = [
        _candidate_row(candidate, decisions, applied_decision_ids)
        for candidate in queue.items
    ]
    approved_rows = [row for row in candidate_rows if row["approved_for_future_apply"]]

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "generated_at": timestamp,
        "source_refs": sorted(
            {
                "runtime/memory/candidate_store.py",
                "runtime/memory/personal_map.py",
                "runtime/pulse/candidate_apply.py",
                "runtime/pulse/personal_map_review_apply.py",
                "runtime/pulse/review_decision_log.py",
                "06_AGENTS/Personal-Map-Architecture.md",
                *queue.source_log_paths,
            }
        ),
        "summary": {
            "candidate_count": queue.item_count,
            "pending_candidate_count": queue.pending_count,
            "review_decision_count": len(decisions),
            "approved_candidate_count": len(approved_rows),
            "dry_run_apply_count": apply_preview.applied_count,
            "dry_run_skip_already_applied": apply_preview.skipped_already_applied,
            "dry_run_missing_candidate_count": apply_preview.skipped_no_candidate,
            "applied_graph_present": graph_summary["graph_present"],
            "applied_graph_node_count": graph_summary["node_count"],
            "applied_graph_edge_count": graph_summary["edge_count"],
            "live_apply_command": "chaseos pulse apply-decisions --kind personal_map --live",
            "surface_runs_live_apply": False,
        },
        "candidate_rows": candidate_rows,
        "latest_review_decisions": list(decisions.values()),
        "apply_preview": apply_preview.to_dict(),
        "graph_summary": graph_summary,
        "authority": dict(AUTHORITY_BOUNDARY),
        "writes": [],
    }


def _metric(label: str, value: Any) -> str:
    return (
        "<div class='metric'>"
        f"<span>{_escape(label)}</span>"
        f"<strong>{_escape(value)}</strong>"
        "</div>"
    )


def _row(row: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td><code>{_escape(row.get('candidate_id'))}</code></td>"
        f"<td>{_escape(row.get('candidate_type'))}</td>"
        f"<td><strong>{_escape(row.get('label'))}</strong><p>{_escape(row.get('reason'))}</p></td>"
        f"<td>{_escape(row.get('decision_type') or 'not reviewed')}</td>"
        f"<td>{_escape(row.get('already_applied'))}</td>"
        "</tr>"
    )


def render_personal_map_review_apply_html(model: dict[str, Any]) -> str:
    """Render the Personal Map review/apply surface as static HTML."""

    summary = model.get("summary") or {}
    rows = model.get("candidate_rows") or []
    graph = model.get("graph_summary") or {}
    authority = model.get("authority") or {}
    blocked = [
        key.replace("_", " ")
        for key, value in sorted(authority.items())
        if value is False and key.endswith(("allowed", "created", "apply", "candidates", "graph"))
    ]
    blocked_items = "".join(f"<li>{_escape(item)}</li>" for item in blocked)
    candidate_rows = "".join(_row(row) for row in rows[:120])

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ChaseOS Pulse Personal Map Review</title>
  <style>
    :root {{
      --bg: #f4f6f5;
      --panel: #ffffff;
      --ink: #17201f;
      --muted: #62706f;
      --line: #d7ded9;
      --accent: #0f766e;
      --soft: #edf3f1;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Inter, Segoe UI, Arial, sans-serif; overflow-x: hidden; }}
    header {{ padding: 28px clamp(18px, 4vw, 56px) 18px; border-bottom: 1px solid var(--line); background: var(--panel); }}
    main {{ padding: 24px clamp(18px, 4vw, 56px) 48px; display: grid; gap: 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
    h2 {{ letter-spacing: 0; }}
    .sub {{ color: var(--muted); max-width: 980px; line-height: 1.5; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }}
    .metric, .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; min-width: 0; }}
    .metric span, th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: 760; }}
    .metric strong {{ display: block; margin-top: 6px; font-size: 24px; overflow-wrap: anywhere; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th, td {{ text-align: left; border-bottom: 1px solid var(--line); padding: 10px; vertical-align: top; overflow-wrap: anywhere; }}
    td p {{ margin: 4px 0 0; color: var(--muted); }}
    code {{ white-space: normal; overflow-wrap: anywhere; color: var(--accent); }}
    .command {{ display: block; padding: 10px; background: var(--soft); border-radius: 6px; }}
    li {{ margin: 5px 0; overflow-wrap: anywhere; }}
    @media (max-width: 760px) {{ table {{ display: block; overflow-x: auto; }} }}
  </style>
</head>
<body>
  <header>
    <h1>ChaseOS Pulse Personal Map Review</h1>
    <p class="sub">Static local surface over Personal Map candidates, review decisions, current runtime-memory graph state, and the dry-run apply preview. This page does not apply candidates or mutate Personal Map state.</p>
  </header>
  <main>
    <section class="metrics" aria-label="Personal Map review metrics">
      {_metric('candidates', summary.get('candidate_count'))}
      {_metric('approved for apply', summary.get('approved_candidate_count'))}
      {_metric('dry-run apply', summary.get('dry_run_apply_count'))}
      {_metric('graph nodes', summary.get('applied_graph_node_count'))}
      {_metric('graph edges', summary.get('applied_graph_edge_count'))}
    </section>
    <section class="panel">
      <h2>Governed Apply Command</h2>
      <p class="sub">Live apply remains a separate operator action and writes only to runtime memory, not canonical notes.</p>
      <code class="command">{_escape(summary.get('live_apply_command'))}</code>
    </section>
    <section class="panel">
      <h2>Applied Runtime Graph</h2>
      <p><code>{_escape(graph.get('graph_path'))}</code></p>
      <p class="sub">present={_escape(graph.get('graph_present'))}; updated_at={_escape(graph.get('updated_at') or '(none)')}; read_error={_escape(graph.get('read_error') or '(none)')}</p>
    </section>
    <section class="panel">
      <h2>Personal Map Candidates</h2>
      <table>
        <thead><tr><th>Candidate</th><th>Type</th><th>Target</th><th>Decision</th><th>Applied</th></tr></thead>
        <tbody>{candidate_rows or '<tr><td colspan="5">No Personal Map candidates found.</td></tr>'}</tbody>
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


def write_personal_map_review_apply_html(
    vault_root: str | Path,
    *,
    output_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Write the static Personal Map review/apply surface under Pulse logs."""

    vault = _vault_path(vault_root)
    model = build_personal_map_review_apply_surface(vault, generated_at=generated_at)
    root = (vault / REVIEW_APPLY_ROOT).resolve()
    if output_path is None:
        target = root / f"{_date_slug(model.get('generated_at'))}-personal-map-review-apply.html"
    else:
        target = Path(output_path)
        target = target if target.is_absolute() else vault / target
    _assert_inside(target, root, "Personal Map review/apply output must stay under Pulse personal-map-review logs")
    root.mkdir(parents=True, exist_ok=True)
    target.write_text(render_personal_map_review_apply_html(model), encoding="utf-8")
    model["writes"] = [_relative_to_vault(vault, target)]
    model["html_output_path"] = _relative_to_vault(vault, target)
    return model
