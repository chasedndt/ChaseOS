"""Read-only ChaseOS Pulse Personal Map visualization contract.

This module turns existing Personal Map schema/candidate evidence into a
visualization-ready packet and optional static HTML artifact. It does not apply
Personal Map candidates, approve memory, mutate profile state, or write
canonical files.
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from runtime.memory.candidate_store import (
    PERSONAL_MAP_CANDIDATE_ROOT,
    build_personal_map_candidate_queue,
)
from runtime.pulse.card_schema import now_utc
from runtime.pulse.memory_runtime_readiness import build_pulse_memory_runtime_readiness


SURFACE_ID = "chaseos_pulse_personal_map_visualization_contract"
VISUALIZATION_ROOT = Path("07_LOGS") / "Pulse-Decks" / "personal-map"

DECLARED_PERSONAL_MAP_LANES = (
    ("personal_domain_chaseos", "ChaseOS", "domain"),
    ("personal_domain_business_os", "Business OS", "business_os"),
    ("personal_domain_university", "University", "learning_map"),
    ("personal_domain_learning", "Learning", "learning_map"),
    ("personal_domain_trading", "Trading", "trading_map"),
    ("personal_domain_content_brand", "Content / Brand", "content_map"),
    ("personal_domain_ai_engineering", "AI Engineering", "domain"),
    ("personal_domain_software_engineering", "Software Engineering", "skill"),
    ("personal_domain_cybersecurity", "Cybersecurity", "skill"),
    ("personal_domain_personal_doctrine", "Personal Doctrine", "doctrine"),
    ("personal_domain_runtime_agents", "Runtime Agents", "domain"),
)

AUTHORITY_BOUNDARY = {
    "read_only": True,
    "local_only": True,
    "writes_html_only_when_explicit": True,
    "applies_personal_map_candidates": False,
    "mutates_personal_map": False,
    "approves_memory": False,
    "creates_tasks": False,
    "updates_project_files": False,
    "updates_now": False,
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


def _declared_lane_nodes() -> list[dict[str, Any]]:
    return [
        {
            "node_id": node_id,
            "node_type": node_type,
            "label": label,
            "summary": "Declared Personal Map lane from architecture docs.",
            "status": "declared_lane",
            "source": "06_AGENTS/Personal-Map-Architecture.md",
            "candidate_id": None,
            "tags": [],
            "evidence_count": 1,
        }
        for node_id, label, node_type in DECLARED_PERSONAL_MAP_LANES
    ]


def _candidate_node_to_visual(candidate: Any) -> dict[str, Any] | None:
    node = getattr(candidate, "node", None)
    if node is None:
        return None
    return {
        "node_id": node.node_id,
        "node_type": node.node_type,
        "label": node.label,
        "summary": node.summary,
        "status": "candidate_pending_review",
        "source": getattr(candidate, "source_deck_path", None) or "personal_map_candidate",
        "candidate_id": candidate.candidate_id,
        "tags": list(node.tags),
        "evidence_count": len(node.evidence),
    }


def _candidate_edge_to_visual(candidate: Any) -> dict[str, Any] | None:
    edge = getattr(candidate, "edge", None)
    if edge is None:
        return None
    return {
        "edge_id": edge.edge_id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "relation": edge.relation,
        "confidence": edge.confidence,
        "status": "candidate_pending_review",
        "source": getattr(candidate, "source_deck_path", None) or "personal_map_candidate",
        "candidate_id": candidate.candidate_id,
        "evidence_count": len(edge.evidence),
    }


def _count_by(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_personal_map_visualization_contract(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a read-only visualization packet over Personal Map evidence."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or now_utc()
    queue = build_personal_map_candidate_queue(vault)
    memory_runtime = build_pulse_memory_runtime_readiness(vault)

    candidate_nodes = [
        visual
        for candidate in queue.items
        if (visual := _candidate_node_to_visual(candidate)) is not None
    ]
    candidate_edges = [
        visual
        for candidate in queue.items
        if (visual := _candidate_edge_to_visual(candidate)) is not None
    ]
    declared_nodes = _declared_lane_nodes()
    nodes = declared_nodes + candidate_nodes
    node_ids = {node["node_id"] for node in nodes}
    disconnected_edges = [
        edge
        for edge in candidate_edges
        if edge["source_node_id"] not in node_ids or edge["target_node_id"] not in node_ids
    ]

    return {
        "ok": True,
        "surface": SURFACE_ID,
        "generated_at": timestamp,
        "source_refs": sorted(
            {
                "06_AGENTS/Personal-Map-Architecture.md",
                "runtime/memory/personal_map.py",
                "runtime/memory/candidate_store.py",
                "runtime/pulse/personal_map_visualization.py",
                "runtime/pulse/memory_runtime_readiness.py",
                *queue.source_log_paths,
            }
        ),
        "summary": {
            "declared_lane_count": len(declared_nodes),
            "candidate_node_count": len(candidate_nodes),
            "candidate_edge_count": len(candidate_edges),
            "visual_node_count": len(nodes),
            "visual_edge_count": len(candidate_edges),
            "disconnected_edge_count": len(disconnected_edges),
            "personal_map_candidate_count": queue.item_count,
            "accepted_node_count": 0,
            "accepted_edge_count": 0,
            "applied_graph_present": False,
            "memory_runtime_readiness_status": memory_runtime.readiness_status,
        },
        "groups": {
            "by_node_type": _count_by(nodes, "node_type"),
            "by_status": _count_by(nodes, "status"),
        },
        "nodes": nodes,
        "edges": candidate_edges,
        "disconnected_edges": disconnected_edges,
        "candidate_queue": queue.to_dict(),
        "authority": dict(AUTHORITY_BOUNDARY),
        "writes": [],
    }


def render_personal_map_visualization_html(model: dict[str, Any]) -> str:
    """Render the Personal Map visualization contract as static HTML."""

    summary = model.get("summary") or {}
    nodes = model.get("nodes") or []
    edges = model.get("edges") or []
    disconnected = model.get("disconnected_edges") or []
    authority = model.get("authority") or {}
    blocked = [
        key.replace("_", " ")
        for key, value in sorted(authority.items())
        if value is False and key.endswith(("allowed", "created"))
    ]

    node_cards = "".join(
        "<article class='node'>"
        f"<span>{_escape(node.get('node_type'))}</span>"
        f"<h2>{_escape(node.get('label'))}</h2>"
        f"<p>{_escape(node.get('summary'))}</p>"
        f"<code>{_escape(node.get('status'))}</code>"
        "</article>"
        for node in nodes[:80]
    )
    edge_rows = "".join(
        "<tr>"
        f"<td>{_escape(edge.get('source_node_id'))}</td>"
        f"<td>{_escape(edge.get('relation'))}</td>"
        f"<td>{_escape(edge.get('target_node_id'))}</td>"
        f"<td>{_escape(edge.get('confidence'))}</td>"
        "</tr>"
        for edge in edges[:80]
    )
    blocked_items = "".join(f"<li>{_escape(item)}</li>" for item in blocked)
    disconnected_items = "".join(
        f"<li><code>{_escape(edge.get('edge_id'))}</code> references missing node endpoint(s)</li>"
        for edge in disconnected[:20]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ChaseOS Pulse Personal Map</title>
  <style>
    :root {{
      --bg: #f6f7f2;
      --panel: #ffffff;
      --ink: #182024;
      --muted: #62706f;
      --line: #d7ddd5;
      --accent: #0f766e;
      --warn: #a15c07;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Inter, Segoe UI, Arial, sans-serif; }}
    header {{ padding: 28px clamp(18px, 4vw, 56px) 18px; border-bottom: 1px solid var(--line); }}
    main {{ padding: 24px clamp(18px, 4vw, 56px) 48px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
    h2, h3 {{ letter-spacing: 0; }}
    .sub {{ color: var(--muted); max-width: 920px; line-height: 1.5; }}
    .metrics, .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }}
    .metric, .node, .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; }}
    .metric span, .node span {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .metric strong {{ display: block; margin-top: 6px; font-size: 24px; }}
    .node h2 {{ margin: 8px 0; font-size: 18px; }}
    .node p {{ color: var(--muted); min-height: 44px; }}
    code {{ white-space: normal; overflow-wrap: anywhere; color: var(--accent); }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }}
    td, th {{ padding: 10px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .warn {{ color: var(--warn); }}
  </style>
</head>
<body>
  <header>
    <h1>ChaseOS Pulse Personal Map</h1>
    <p class="sub">Read-only visualization contract for Personal Map lanes and pending candidates. It does not apply candidates, approve memory, mutate profile state, or write canonical files.</p>
  </header>
  <main>
    <section class="metrics" aria-label="Personal Map metrics">
      <div class="metric"><span>Declared lanes</span><strong>{_escape(summary.get('declared_lane_count'))}</strong></div>
      <div class="metric"><span>Candidate nodes</span><strong>{_escape(summary.get('candidate_node_count'))}</strong></div>
      <div class="metric"><span>Candidate edges</span><strong>{_escape(summary.get('candidate_edge_count'))}</strong></div>
      <div class="metric"><span>Accepted graph</span><strong>{_escape('not built')}</strong></div>
    </section>
    <section>
      <h2>Map Nodes</h2>
      <div class="grid">{node_cards}</div>
    </section>
    <section>
      <h2>Candidate Edges</h2>
      <table>
        <thead><tr><th>Source</th><th>Relation</th><th>Target</th><th>Confidence</th></tr></thead>
        <tbody>{edge_rows or '<tr><td colspan="4">No candidate edges.</td></tr>'}</tbody>
      </table>
    </section>
    <section class="panel">
      <h2>Review Warnings</h2>
      <ul>{disconnected_items or '<li>No disconnected candidate edges detected.</li>'}</ul>
    </section>
    <section class="panel">
      <h2>Blocked Authority</h2>
      <ul>{blocked_items}</ul>
    </section>
  </main>
</body>
</html>
"""


def write_personal_map_visualization_html(
    vault_root: str | Path,
    *,
    output_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Write a static Personal Map visualization artifact under Pulse logs."""

    vault = _vault_path(vault_root)
    model = build_personal_map_visualization_contract(vault, generated_at=generated_at)
    root = (vault / VISUALIZATION_ROOT).resolve()
    if output_path is None:
        target = root / f"{_date_slug(model.get('generated_at'))}-personal-map-visualization.html"
    else:
        target = Path(output_path)
        target = target if target.is_absolute() else vault / target
    _assert_inside(target, root, "Personal Map visualization output must stay under Pulse personal-map logs")
    root.mkdir(parents=True, exist_ok=True)
    target.write_text(render_personal_map_visualization_html(model), encoding="utf-8")
    model["writes"] = [_relative_to_vault(vault, target)]
    model["html_output_path"] = _relative_to_vault(vault, target)
    return model
