"""Personal Map live-apply proof surface for ChaseOS Pulse.

This module proves whether approved Personal Map decisions are ready for the
existing governed runtime-memory apply lane. It does not execute live apply.
The write path only emits a static local HTML proof artifact.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from runtime.memory.candidate_store import build_personal_map_candidate_queue
from runtime.pulse.candidate_apply import apply_reviewed_candidates
from runtime.pulse.card_schema import now_utc
from runtime.pulse.personal_map_review_apply import (
    APPLY_REGISTRY_PATH,
    PERSONAL_MAP_GRAPH_PATH,
    _load_applied_decision_ids,
    _load_personal_map_graph_summary,
    _latest_decisions_by_candidate,
)


SURFACE_ID = "chaseos_pulse_personal_map_live_apply_proof"
LIVE_APPLY_PROOF_ROOT = (
    Path("07_LOGS") / "Pulse-Decks" / "personal-map-live-apply-proof"
)

LIVE_APPLY_COMMAND = "chaseos pulse apply-decisions --kind personal_map --live"
DRY_RUN_COMMAND = "chaseos pulse apply-decisions --kind personal_map --json"

AUTHORITY_BOUNDARY = {
    "read_only": True,
    "local_only": True,
    "writes_html_only_when_explicit": True,
    "runs_live_apply": False,
    "candidate_apply_allowed": False,
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


def _candidate_target(candidate: Any) -> dict[str, Any]:
    if candidate.node is not None:
        return {
            "target_type": "node",
            "target_id": candidate.node.node_id,
            "target_label": candidate.node.label,
        }
    if candidate.edge is not None:
        return {
            "target_type": "edge",
            "target_id": candidate.edge.edge_id,
            "target_label": candidate.edge.relation,
        }
    return {
        "target_type": candidate.candidate_type,
        "target_id": None,
        "target_label": candidate.candidate_type,
    }


def _proof_rows(
    candidates: list[Any],
    decisions_by_candidate: dict[str, dict[str, Any]],
    applied_decision_ids: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        target = _candidate_target(candidate)
        decision = decisions_by_candidate.get(candidate.candidate_id) or {}
        decision_id = decision.get("decision_id")
        decision_type = decision.get("decision_type")
        approved = decision_type == "approve_for_future_apply"
        already_applied = bool(decision_id and decision_id in applied_decision_ids)
        ready = approved and not already_applied
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "candidate_type": candidate.candidate_type,
                "target_type": target["target_type"],
                "target_id": target["target_id"],
                "target_label": target["target_label"],
                "reason": candidate.reason,
                "source_card_id": candidate.source_card_id,
                "source_deck_path": candidate.source_deck_path,
                "created_at": candidate.created_at,
                "decision_id": decision_id,
                "decision_type": decision_type,
                "approved_for_future_apply": approved,
                "already_applied": already_applied,
                "ready_for_live_apply": ready,
            }
        )
    return rows


def build_personal_map_live_apply_proof(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a read-only live-apply readiness proof for Personal Map decisions."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()
    queue = build_personal_map_candidate_queue(vault)
    decisions = _latest_decisions_by_candidate(vault)
    applied_decision_ids = _load_applied_decision_ids(vault)
    apply_preview = apply_reviewed_candidates(vault, dry_run=True, candidate_kind="personal_map")
    graph_summary = _load_personal_map_graph_summary(vault)
    rows = _proof_rows(list(queue.items), decisions, applied_decision_ids)
    ready_rows = [row for row in rows if row["ready_for_live_apply"]]
    approved_rows = [row for row in rows if row["approved_for_future_apply"]]
    already_applied_rows = [row for row in rows if row["already_applied"]]
    blocked_rows = [
        row
        for row in rows
        if not row["ready_for_live_apply"] and not row["already_applied"]
    ]
    dry_run_error_count = int(apply_preview.error_count)
    live_apply_ready = bool(ready_rows) and dry_run_error_count == 0

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "generated_at": timestamp,
        "source_refs": sorted(
            {
                "runtime/memory/candidate_store.py",
                "runtime/memory/personal_map.py",
                "runtime/pulse/candidate_apply.py",
                "runtime/pulse/personal_map_live_apply_proof.py",
                "runtime/pulse/personal_map_review_apply.py",
                "runtime/pulse/review_decision_log.py",
                "06_AGENTS/Personal-Map-Architecture.md",
                *queue.source_log_paths,
            }
        ),
        "summary": {
            "candidate_count": queue.item_count,
            "review_decision_count": len(decisions),
            "approved_candidate_count": len(approved_rows),
            "ready_for_live_apply_count": len(ready_rows),
            "already_applied_count": len(already_applied_rows),
            "blocked_or_unreviewed_count": len(blocked_rows),
            "dry_run_apply_count": apply_preview.applied_count,
            "dry_run_error_count": dry_run_error_count,
            "dry_run_skip_already_applied": apply_preview.skipped_already_applied,
            "graph_present": graph_summary["graph_present"],
            "graph_node_count": graph_summary["node_count"],
            "graph_edge_count": graph_summary["edge_count"],
            "live_apply_ready": live_apply_ready,
            "live_apply_command": LIVE_APPLY_COMMAND,
            "dry_run_command": DRY_RUN_COMMAND,
            "surface_runs_live_apply": False,
            "writes_runtime_memory_graph": False,
        },
        "candidate_rows": rows,
        "ready_candidate_rows": ready_rows,
        "apply_preview": apply_preview.to_dict(),
        "graph_summary": graph_summary,
        "apply_registry_path": APPLY_REGISTRY_PATH.as_posix(),
        "personal_map_graph_path": PERSONAL_MAP_GRAPH_PATH.as_posix(),
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
    status = (
        "ready"
        if row.get("ready_for_live_apply")
        else "applied"
        if row.get("already_applied")
        else "blocked"
    )
    return (
        "<tr>"
        f"<td><code>{_escape(row.get('candidate_id'))}</code></td>"
        f"<td>{_escape(row.get('candidate_type'))}</td>"
        f"<td><strong>{_escape(row.get('target_label'))}</strong><p><code>{_escape(row.get('target_id'))}</code></p></td>"
        f"<td>{_escape(row.get('decision_type') or 'not reviewed')}</td>"
        f"<td>{_escape(status)}</td>"
        "</tr>"
    )


def render_personal_map_live_apply_proof_html(model: dict[str, Any]) -> str:
    """Render the Personal Map live-apply proof as static HTML."""

    summary = model.get("summary") or {}
    rows = model.get("candidate_rows") or []
    graph = model.get("graph_summary") or {}
    authority = model.get("authority") or {}
    blocked = [
        key.replace("_", " ")
        for key, value in sorted(authority.items())
        if value is False
        and key.endswith(("allowed", "created", "apply", "candidates", "graph"))
    ]
    blocked_items = "".join(f"<li>{_escape(item)}</li>" for item in blocked)
    candidate_rows = "".join(_row(row) for row in rows[:120])

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ChaseOS Pulse Personal Map Live Apply Proof</title>
  <style>
    :root {{
      --bg: #f5f7f8;
      --panel: #ffffff;
      --ink: #152025;
      --muted: #607078;
      --line: #d8e0e3;
      --accent: #0f766e;
      --soft: #edf3f1;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Inter, Segoe UI, Arial, sans-serif; overflow-x: hidden; }}
    header {{ padding: 28px clamp(18px, 4vw, 56px) 18px; background: var(--panel); border-bottom: 1px solid var(--line); }}
    main {{ padding: 24px clamp(18px, 4vw, 56px) 48px; display: grid; gap: 18px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
    h2 {{ letter-spacing: 0; }}
    .sub {{ color: var(--muted); line-height: 1.5; max-width: 980px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }}
    .metric, .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; min-width: 0; }}
    .metric span, th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: 760; }}
    .metric strong {{ display: block; margin-top: 6px; font-size: 24px; overflow-wrap: anywhere; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    th, td {{ text-align: left; border-bottom: 1px solid var(--line); padding: 10px; vertical-align: top; overflow-wrap: anywhere; }}
    td p {{ margin: 4px 0 0; color: var(--muted); }}
    code {{ white-space: normal; overflow-wrap: anywhere; color: var(--accent); }}
    .command {{ display: block; padding: 10px; background: var(--soft); border-radius: 6px; margin: 8px 0; }}
    li {{ margin: 5px 0; overflow-wrap: anywhere; }}
    @media (max-width: 760px) {{ table {{ display: block; overflow-x: auto; }} }}
  </style>
</head>
<body>
  <header>
    <h1>ChaseOS Pulse Personal Map Live Apply Proof</h1>
    <p class="sub">Read-only proof surface for approved Personal Map candidates. It shows dry-run readiness for the governed runtime-memory apply lane, but this artifact does not run the live command.</p>
  </header>
  <main>
    <section class="metrics" aria-label="Personal Map live apply metrics">
      {_metric('ready for live apply', summary.get('ready_for_live_apply_count'))}
      {_metric('dry-run apply', summary.get('dry_run_apply_count'))}
      {_metric('dry-run errors', summary.get('dry_run_error_count'))}
      {_metric('already applied', summary.get('already_applied_count'))}
      {_metric('graph nodes', summary.get('graph_node_count'))}
      {_metric('graph edges', summary.get('graph_edge_count'))}
    </section>
    <section class="panel">
      <h2>Readiness</h2>
      <p class="sub">live_apply_ready={_escape(summary.get('live_apply_ready'))}; graph_present={_escape(summary.get('graph_present'))}; graph_path=<code>{_escape(model.get('personal_map_graph_path'))}</code></p>
    </section>
    <section class="panel">
      <h2>Operator Commands</h2>
      <p class="sub">Dry-run first, then run live only as a separate operator-approved action.</p>
      <code class="command">{_escape(summary.get('dry_run_command'))}</code>
      <code class="command">{_escape(summary.get('live_apply_command'))}</code>
    </section>
    <section class="panel">
      <h2>Applied Runtime Graph</h2>
      <p><code>{_escape(graph.get('graph_path'))}</code></p>
      <p class="sub">present={_escape(graph.get('graph_present'))}; updated_at={_escape(graph.get('updated_at') or '(none)')}; read_error={_escape(graph.get('read_error') or '(none)')}</p>
    </section>
    <section class="panel">
      <h2>Candidate Proof Rows</h2>
      <table>
        <thead><tr><th>Candidate</th><th>Type</th><th>Target</th><th>Decision</th><th>Status</th></tr></thead>
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


def write_personal_map_live_apply_proof_html(
    vault_root: str | Path,
    *,
    output_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Write the static Personal Map live-apply proof under Pulse logs."""

    vault = _vault_path(vault_root)
    model = build_personal_map_live_apply_proof(vault, generated_at=generated_at)
    root = (vault / LIVE_APPLY_PROOF_ROOT).resolve()
    if output_path is None:
        target = root / f"{_date_slug(model.get('generated_at'))}-personal-map-live-apply-proof.html"
    else:
        target = Path(output_path)
        target = target if target.is_absolute() else vault / target
    _assert_inside(
        target,
        root,
        "Personal Map live-apply proof output must stay under Pulse personal-map-live-apply-proof logs",
    )
    root.mkdir(parents=True, exist_ok=True)
    target.write_text(render_personal_map_live_apply_proof_html(model), encoding="utf-8")
    model["writes"] = [_relative_to_vault(vault, target)]
    model["html_output_path"] = _relative_to_vault(vault, target)
    return model
