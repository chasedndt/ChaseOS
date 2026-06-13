"""Local static renderer for the Studio graph-view contract.

This module renders the read-only graph-view contract into a static HTML
artifact. It does not start a server, provide an interactive UI, persist graph
state, write node IDs, execute workflows, call providers/connectors, or mutate
canonical state. HTML writes are allowed only through an explicit write call and
only under the Studio graph-view log artifact directory.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.graph_view_browser_qa import (
    STATIC_GRAPH_BROWSER_QA_PASS,
    next_graph_view_pass_after_browser_qa,
    static_graph_browser_qa_evidence_built,
)
from runtime.studio.graph_view_contract import build_graph_view_contract


MODEL_VERSION = "studio.graph_view_static_renderer.v1"
SURFACE_ID = "studio_graph_view_static_renderer"
STATIC_RENDER_ROOT = Path("07_LOGS") / "Studio-Graph-Views"

DEFAULT_SVG_WIDTH = 1040
DEFAULT_SVG_HEIGHT = 620
NODE_RADIUS = 18
MAX_LABEL_CHARS = 34

_NODE_COLORS = {
    "system_root_doc": "#0f766e",
    "home_doc": "#2563eb",
    "agent_control_doc": "#7c3aed",
    "build_log": "#b45309",
    "documentation_history_note": "#be123c",
    "daily_note": "#0e7490",
    "project_doc": "#15803d",
    "knowledge_doc": "#4338ca",
    "intake_doc": "#c2410c",
    "sop_template_doc": "#6d28d9",
    "runtime_doc": "#881337",
    "decision_doc": "#1e3a8a",
    "source_doc": "#0e7490",
    "generated_artifact_doc": "#7e22ce",
    "log_audit": "#b45309",
    "chaseos_markdown_doc": "#475569",
    "markdown_note": "#64748b",
    "markdown_heading": "#0891b2",
    "markdown_tag": "#16a34a",
    "markdown_task": "#ca8a04",
    "obsidian_block_marker": "#9333ea",
    "external_resource": "#9333ea",
    "unresolved_wikilink": "#dc2626",
    "unresolved_markdown_link": "#dc2626",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _assert_inside(path: Path, root: Path, message: str) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(message) from exc


def _escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _date_slug(value: str | None) -> str:
    source = value or _now_utc()
    safe = "".join(character if character.isalnum() else "-" for character in source)
    return "-".join(part for part in safe.split("-") if part)[:80]


def _short(value: Any, limit: int = MAX_LABEL_CHARS) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else f"{text[: max(1, limit - 3)]}..."


def _color_for(node_type: str) -> str:
    return _NODE_COLORS.get(node_type, "#64748b")


def _dasharray(style: Any) -> str:
    if style == "dashed":
        return "6 4"
    if style == "dotted":
        return "2 4"
    return ""


def _polygon_points(x: float, y: float, radius: float, sides: int, rotation: float = -90.0) -> str:
    import math

    points = []
    for index in range(sides):
        angle = math.radians(rotation + index * (360 / sides))
        points.append(f"{x + radius * math.cos(angle):.1f},{y + radius * math.sin(angle):.1f}")
    return " ".join(points)


def _node_shape_svg(
    *,
    x: float,
    y: float,
    radius: float,
    visual: dict[str, Any],
    title: str,
) -> str:
    shape = str(visual.get("shape") or "ellipse")
    fill = _escape(visual.get("fill_color") or "#64748b")
    stroke = _escape(visual.get("border_color") or "#ffffff")
    stroke_width = float(visual.get("border_width") or 2)
    dash = _dasharray(visual.get("border_style"))
    dash_attr = f" stroke-dasharray='{_escape(dash)}'" if dash else ""
    common = f"fill='{fill}' stroke='{stroke}' stroke-width='{stroke_width:.1f}'{dash_attr}"
    title_markup = f"<title>{_escape(title)}</title>"
    if shape in {"rectangle", "round-rectangle", "bottom-round-rectangle", "cut-rectangle", "tag", "round-tag", "barrel"}:
        rx = 8 if "round" in shape else 3
        size = radius * 1.8
        return (
            f"<rect x='{x - size / 2:.1f}' y='{y - size / 2:.1f}' width='{size:.1f}' height='{size:.1f}' "
            f"rx='{rx}' {common}>{title_markup}</rect>"
        )
    if shape in {"triangle", "round-triangle", "vee"}:
        return f"<polygon points='{_polygon_points(x, y, radius, 3)}' {common}>{title_markup}</polygon>"
    if shape in {"diamond", "round-diamond", "rhomboid", "right-rhomboid"}:
        return f"<polygon points='{_polygon_points(x, y, radius, 4, rotation=-45)}' {common}>{title_markup}</polygon>"
    if shape in {"pentagon", "round-pentagon"}:
        return f"<polygon points='{_polygon_points(x, y, radius, 5)}' {common}>{title_markup}</polygon>"
    if shape in {"hexagon", "round-hexagon", "concave-hexagon"}:
        return f"<polygon points='{_polygon_points(x, y, radius, 6)}' {common}>{title_markup}</polygon>"
    if shape in {"heptagon", "round-heptagon"}:
        return f"<polygon points='{_polygon_points(x, y, radius, 7)}' {common}>{title_markup}</polygon>"
    if shape in {"octagon", "round-octagon"}:
        return f"<polygon points='{_polygon_points(x, y, radius, 8)}' {common}>{title_markup}</polygon>"
    if shape == "star":
        return f"<polygon points='{_polygon_points(x, y, radius, 10)}' {common}>{title_markup}</polygon>"
    return f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{radius:.1f}' {common}>{title_markup}</circle>"


def _positions_by_id(layout: dict[str, Any]) -> dict[str, tuple[float, float, int]]:
    positions: dict[str, tuple[float, float, int]] = {}
    for item in layout.get("node_positions") or []:
        node_id = str(item.get("id", ""))
        if not node_id:
            continue
        x = float(item.get("x", 0)) + 80
        y = float(item.get("y", 0)) + 80
        degree = int(item.get("degree", 0) or 0)
        positions[node_id] = (x, y, degree)
    return positions


def _svg_dimensions(positions: dict[str, tuple[float, float, int]]) -> tuple[int, int]:
    if not positions:
        return DEFAULT_SVG_WIDTH, DEFAULT_SVG_HEIGHT
    max_x = max(position[0] for position in positions.values())
    max_y = max(position[1] for position in positions.values())
    return (
        max(DEFAULT_SVG_WIDTH, int(max_x + 180)),
        max(DEFAULT_SVG_HEIGHT, int(max_y + 160)),
    )


def _metric(label: str, value: Any) -> str:
    return (
        "<div class='metric'>"
        f"<span>{_escape(label)}</span>"
        f"<strong>{_escape(value)}</strong>"
        "</div>"
    )


def _pill(label: Any, status: Any = None) -> str:
    status_class = "warn" if status in {False, "PARTIAL", "BLOCKED"} else "ok"
    return f"<span class='pill {status_class}'>{_escape(label)}</span>"


def _render_graph_svg(model: dict[str, Any]) -> str:
    view = model.get("view_model") or {}
    nodes = view.get("nodes") or []
    edges = view.get("edges") or []
    layout = view.get("layout") or {}
    overlays = view.get("visual_overlays") or {}
    node_visual_map = overlays.get("node_visual_map") or {}
    edge_visual_map = overlays.get("edge_visual_map") or {}
    positions = _positions_by_id(layout)
    width, height = _svg_dimensions(positions)
    nodes_by_id = {str(node.get("id")): node for node in nodes}

    edge_rows: list[str] = []
    for edge in edges:
        source_id = str(edge.get("source", ""))
        target_id = str(edge.get("target", ""))
        if source_id not in positions or target_id not in positions:
            continue
        x1, y1, _degree1 = positions[source_id]
        x2, y2, _degree2 = positions[target_id]
        visual = edge_visual_map.get(str(edge.get("id"))) or {}
        relation = _escape(edge.get("relation"))
        color = _escape(visual.get("color") or "#91a4b7")
        width_attr = float(visual.get("width") or 1.4)
        opacity = float(visual.get("opacity") or 0.72)
        dash = _dasharray(visual.get("line_style"))
        dash_attr = f" stroke-dasharray='{_escape(dash)}'" if dash else ""
        layer = str(visual.get("edge_layer") or edge.get("edge_layer") or "explicit")
        canonical_layer = str(visual.get("canonical_layer") or layer)
        edge_rows.append(
            f"<line class='edge edge--{_escape(layer)}' "
            f"x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
            f"style='stroke:{color};stroke-width:{width_attr:.1f};stroke-opacity:{opacity:.2f};' {dash_attr}>"
            f"<title>{relation} | {canonical_layer}</title>"
            "</line>"
        )

    node_rows: list[str] = []
    for node_id, (x, y, degree) in positions.items():
        node = nodes_by_id.get(node_id, {})
        node_type = str(node.get("node_type", "unknown"))
        visual = node_visual_map.get(node_id) or {}
        label = str(node.get("label") or node_id)
        radius = max(NODE_RADIUS, float(visual.get("size") or NODE_RADIUS * 2) / 2) + min(10, degree * 2)
        ring_width = float(visual.get("trust_ring_width") or 3)
        ring_dash = _dasharray(visual.get("trust_ring_style"))
        ring_dash_attr = f" stroke-dasharray='{_escape(ring_dash)}'" if ring_dash else ""
        ring_color = _escape(visual.get("trust_ring_color") or "#94a3b8")
        family = _escape(visual.get("node_family") or node_type)
        trust = _escape(visual.get("trust_state") or "raw")
        title = (
            f"{label} | {node_type} | {family} | {trust} | degree {degree}"
        )
        shape = _node_shape_svg(x=x, y=y, radius=radius, visual=visual or {"fill_color": _color_for(node_type)}, title=title)
        badges = visual.get("display_badges") or []
        badge_text = " ".join(str(item) for item in badges[:2])
        badge_markup = (
            f"<text class='node-badge' x='{x:.1f}' y='{y + 4:.1f}' text-anchor='middle'>{_escape(badge_text)}</text>"
            if badge_text
            else ""
        )
        node_rows.append(
            f"<g class='node node--{family} trust--{trust}'>"
            f"<circle class='trust-ring' cx='{x:.1f}' cy='{y:.1f}' r='{radius + ring_width + 2:.1f}' "
            f"fill='none' stroke='{ring_color}' stroke-width='{ring_width:.1f}' stroke-opacity='0.72'{ring_dash_attr}></circle>"
            f"{shape}"
            f"{badge_markup}"
            f"<text x='{x:.1f}' y='{y + radius + 17:.1f}' text-anchor='middle'>{_escape(_short(label))}</text>"
            "</g>"
        )

    if not node_rows:
        node_rows.append("<text class='empty' x='60' y='90'>No graph nodes available for this static render.</text>")

    return (
        f"<svg class='graph' viewBox='0 0 {width} {height}' role='img' aria-label='Studio graph view static render'>"
        "<rect class='graph-bg' x='0' y='0' width='100%' height='100%' />"
        f"{''.join(edge_rows)}"
        f"{''.join(node_rows)}"
        "</svg>"
    )


def _render_legend(model: dict[str, Any]) -> str:
    view = model.get("view_model") or {}
    legend = view.get("legend") or {}
    node_families = legend.get("node_families") or []
    edge_layers = legend.get("edge_layers") or []
    trust_states = legend.get("trust_states") or []
    relations = legend.get("relations") or []
    node_rows = "".join(
        "<li>"
        f"<span class='swatch' style='background:{_escape(item.get('fill_color'))};border-color:{_escape(item.get('border_color'))}'></span>"
        f"{_escape(item.get('label'))}<b>{_escape(item.get('count'))}</b>"
        "</li>"
        for item in node_families[:16]
    )
    edge_rows = "".join(
        "<li>"
        f"<span class='line-swatch' style='background:{_escape(item.get('color'))}'></span>"
        f"{_escape(item.get('layer_label') or item.get('label'))}<b>{_escape(item.get('count'))}</b>"
        "</li>"
        for item in edge_layers[:8]
    )
    trust_rows = "".join(
        "<li>"
        f"<span class='ring-swatch' style='border-color:{_escape(item.get('ring_color'))}'></span>"
        f"{_escape(item.get('label'))}<b>{_escape(item.get('count'))}</b>"
        "</li>"
        for item in trust_states[:10]
    )
    relation_rows = "".join(
        f"<li>{_escape(item.get('label'))}<b>{_escape(item.get('count'))}</b></li>"
        for item in relations[:16]
    )
    return (
        "<section class='panel legend'>"
        "<h2>Legend</h2>"
        "<h3>Node Families</h3>"
        f"<ul>{node_rows or '<li>None<b>0</b></li>'}</ul>"
        "<h3>Trust States</h3>"
        f"<ul>{trust_rows or '<li>None<b>0</b></li>'}</ul>"
        "<h3>Edge Layers</h3>"
        f"<ul>{edge_rows or '<li>None<b>0</b></li>'}</ul>"
        "<h3>Relations</h3>"
        f"<ul>{relation_rows or '<li>None<b>0</b></li>'}</ul>"
        "</section>"
    )


def _render_focus(model: dict[str, Any]) -> str:
    view = model.get("view_model") or {}
    focus = view.get("focus") or {}
    selected = focus.get("selected_node") or {}
    excerpt = focus.get("source_excerpt") or {}
    edge_context = focus.get("edge_context") or {}
    if not focus.get("requested"):
        return (
            "<section class='panel'>"
            "<h2>Focus</h2>"
            "<p class='muted'>No focus node selected.</p>"
            "</section>"
        )

    return (
        "<section class='panel'>"
        "<h2>Focus</h2>"
        f"<p><b>{_escape(selected.get('label') or 'No node')}</b></p>"
        f"<p class='muted'>{_escape(selected.get('id'))}</p>"
        "<div class='mini-grid'>"
        f"{_metric('incoming', edge_context.get('incoming_edge_count', 0))}"
        f"{_metric('outgoing', edge_context.get('outgoing_edge_count', 0))}"
        f"{_metric('related', edge_context.get('related_node_count', 0))}"
        "</div>"
        f"<pre>{_escape(_short(excerpt.get('text'), 900))}</pre>"
        "</section>"
    )


def _render_explainability(model: dict[str, Any]) -> str:
    explainability = model.get("explainability") or {}
    node_identity = explainability.get("node_identity") or {}
    relationships = explainability.get("relationship_context") or {}
    trust = explainability.get("trust_evidence_overlay") or {}
    provenance = explainability.get("provenance_summary") or {}
    source_contracts = ", ".join(str(item) for item in provenance.get("source_contracts") or [] if item)
    return (
        "<section class='panel'>"
        "<h2>Graph Truth</h2>"
        "<div class='mini-grid'>"
        f"{_metric('identity scope', node_identity.get('identity_scope'))}"
        f"{_metric('unresolved refs', relationships.get('unresolved_reference_count', 0))}"
        f"{_metric('generated', trust.get('generated_count', 0))}"
        f"{_metric('canonical', trust.get('canonical_count', 0))}"
        "</div>"
        "<h3>Provenance</h3>"
        f"<p class='muted'>{_escape(provenance.get('provenance_note'))}</p>"
        f"<p class='muted'>Source contracts: {_escape(source_contracts)}</p>"
        "</section>"
    )


def _blocked_authority(authority: dict[str, Any]) -> list[str]:
    blocked = []
    for key, value in sorted(authority.items()):
        if value is False and key.endswith("_allowed"):
            blocked.append(key)
        elif value is False and key.startswith("writes_"):
            blocked.append(key)
    return blocked


def build_graph_view_static_render_model(
    vault_root: str | Path,
    *,
    focus_node_id: str | None = None,
    focus_path: str | Path | None = None,
    folder_path: str | Path | None = None,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
    layout_node_limit: int | None = None,
    content_excerpt_bytes: int | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Return the static renderer model without writing files."""

    vault = _vault_path(vault_root)
    contract = build_graph_view_contract(
        vault,
        focus_node_id=focus_node_id,
        focus_path=focus_path,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
        layout_node_limit=layout_node_limit,
        content_excerpt_bytes=content_excerpt_bytes,
    )
    readiness = contract.get("readiness") or {}
    view = contract.get("view_model") or {}
    viewport = view.get("viewport") or {}
    source_graph = contract.get("source_graph") or {}
    graph_summary = source_graph.get("graph_summary") or {}
    focus = view.get("focus") or {}
    overlays = view.get("visual_overlays") or {}
    overlay_summary = overlays.get("summary") or {}
    overlay_coverage = overlays.get("coverage") or {}
    warnings = list(readiness.get("warnings") or [])
    blockers = list(readiness.get("blockers") or [])
    render_ready = bool(contract.get("ok"))
    static_graph_browser_qa_built = static_graph_browser_qa_evidence_built(vault)
    return {
        "ok": render_ready,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "generated_at": generated_at or _now_utc(),
        "title": "ChaseOS Studio Graph View Static Render",
        "phase": "Phase 10A/10B - Studio Core Shell / Graph + Node Model",
        "status": (
            (
                "PARTIAL / STATIC GRAPH RENDERER BUILT / BROWSER QA VERIFIED TARGETED / FULL UI NOT BUILT"
                if static_graph_browser_qa_built
                else "PARTIAL / STATIC GRAPH RENDERER BUILT / BROWSER QA NOT VERIFIED / FULL UI NOT BUILT"
            )
            if render_ready
            else "BLOCKED / STATIC GRAPH RENDERER BUILT / SOURCE CONTRACT NOT READY"
        ),
        "vault_root": str(vault),
        "target": contract.get("target"),
        "summary": {
            "graph_view_status": contract.get("status"),
            "source_node_count": graph_summary.get("node_count", 0),
            "source_edge_count": graph_summary.get("edge_count", 0),
            "visible_node_count": viewport.get("visible_node_count", 0),
            "visible_edge_count": viewport.get("visible_edge_count", 0),
            "layout_algorithm": (view.get("layout") or {}).get("algorithm"),
            "focus_requested": bool(focus.get("requested")),
            "focus_ok": bool(focus.get("ok")),
            "warning_count": len(warnings),
            "blocker_count": len(blockers),
            "static_renderer_built": True,
            "static_browser_qa_built": static_graph_browser_qa_built,
            "graph_view_ui_built": False,
            "persisted_graph_index_built": False,
            "node_family_count": overlay_coverage.get("node_family_count", 0),
            "edge_layer_count": overlay_coverage.get("edge_layer_count", 0),
            "trust_state_count": overlay_coverage.get("trust_state_count", 0),
            "generated_count": overlay_summary.get("generated_count", 0),
            "canonical_count": overlay_summary.get("canonical_count", 0),
        },
        "source_contract": {
            "surface": contract.get("surface"),
            "model_version": contract.get("model_version"),
            "ok": contract.get("ok"),
            "readiness": readiness,
        },
        "explainability": contract.get("explainability") or {},
        "view_model": view,
        "readiness": {
            "static_graph_renderer_ready": render_ready,
            "graph_view_contract_ready": bool(readiness.get("graph_view_contract_ready")),
            "deterministic_layout_ready": bool(readiness.get("deterministic_layout_ready")),
            "browser_visual_qa_ready": static_graph_browser_qa_built,
            "graph_view_ui_ready": False,
            "persisted_graph_index_ready": False,
            "blockers": blockers,
            "warnings": warnings,
            "next_recommended_pass": (
                (
                    next_graph_view_pass_after_browser_qa(vault)
                    if static_graph_browser_qa_built
                    else STATIC_GRAPH_BROWSER_QA_PASS
                )
                if render_ready
                else readiness.get("next_recommended_pass")
            ),
        },
        "graph_view_truth": {
            "markdown_scan_contract_built": True,
            "graph_index_contract_built": True,
            "node_inspector_contract_built": True,
            "graph_view_contract_built": True,
            "deterministic_layout_contract_built": True,
            "static_graph_renderer_built": True,
            "static_graph_browser_qa_built": static_graph_browser_qa_built,
            "graph_view_ui_built": False,
            "persistent_graph_snapshot_built": False,
            "node_id_writer_built": False,
            "node_editing_built": False,
            "service_layer_write_path_built": False,
            "canonical_graph_writeback_built": False,
        },
        "authority": {
            "read_only": True,
            "local_only": True,
            "reads_file_contents": True,
            "derives_graph_in_memory": True,
            "renders_static_artifact": True,
            "renders_interactive_ui": False,
            "starts_servers": False,
            "writes_html_only_when_explicit": True,
            "writes_graph_artifact_only_when_explicit": True,
            "writes_allowed_root": STATIC_RENDER_ROOT.as_posix(),
            "writes_opened_folder": False,
            "writes_vault": False,
            "writes_settings": False,
            "writes_node_ids": False,
            "writes_graph_index": False,
            "writes_snapshot": False,
            "node_editing_allowed": False,
            "workflow_execution_allowed": False,
            "provider_calls_allowed": False,
            "connector_calls_allowed": False,
            "browser_automation_allowed": False,
            "scheduler_mutation_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "artifact": {
            "write_executed": False,
            "default_output_root": STATIC_RENDER_ROOT.as_posix(),
            "html_output_path": None,
        },
        "writes": [],
        "allowed_actions": ["render-static-graph-view-html", "write-static-graph-view-html-with-explicit-flag"],
        "docs": [
            "ROADMAP.md",
            "06_AGENTS/ChaseOS-Studio-Architecture.md",
            "07_LOGS/Build-Logs/2026-05-03-ChaseOS-phase10-studio-graph-view-local-static-render.md",
        ],
    }


def render_graph_view_static_html(model: dict[str, Any]) -> str:
    """Render a graph-view static model to standalone HTML."""

    summary = model.get("summary") or {}
    readiness = model.get("readiness") or {}
    target = model.get("target") or {}
    authority = model.get("authority") or {}
    warnings = "".join(f"<li>{_escape(item)}</li>" for item in readiness.get("warnings") or [])
    blockers = "".join(f"<li>{_escape(item)}</li>" for item in readiness.get("blockers") or [])
    blocked_authority = "".join(f"<li>{_escape(item)}</li>" for item in _blocked_authority(authority))
    graph_svg = _render_graph_svg(model)
    legend = _render_legend(model)
    focus = _render_focus(model)
    explainability = _render_explainability(model)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ChaseOS Studio Graph View</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #637083;
      --line: #d9e0e7;
      --soft: #edf2f7;
      --ok: #0f766e;
      --warn: #a15c07;
      --risk: #b42335;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: Inter, Segoe UI, Arial, sans-serif; }}
    header {{ padding: 26px clamp(18px, 4vw, 54px) 18px; border-bottom: 1px solid var(--line); background: #fff; }}
    main {{ padding: 22px clamp(18px, 4vw, 54px) 44px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.15; letter-spacing: 0; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; letter-spacing: 0; }}
    h3 {{ margin: 14px 0 8px; font-size: 13px; letter-spacing: 0; color: var(--muted); }}
    p {{ line-height: 1.5; }}
    pre {{ max-height: 260px; overflow: auto; white-space: pre-wrap; background: #f8fafc; border: 1px solid var(--line); border-radius: 8px; padding: 12px; font-size: 12px; line-height: 1.45; }}
    .muted {{ color: var(--muted); overflow-wrap: anywhere; }}
    .topline, .metrics, .mini-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }}
    .topline {{ margin-top: 14px; }}
    .layout {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(280px, 360px); gap: 16px; align-items: start; }}
    .panel, .metric {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .metric strong {{ display: block; margin-top: 6px; font-size: 24px; overflow-wrap: anywhere; }}
    .graph-wrap {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; overflow: auto; min-height: 520px; }}
    .graph {{ display: block; width: 100%; min-width: 820px; height: auto; }}
    .graph-bg {{ fill: #fbfcfe; }}
    .edge {{ stroke: #91a4b7; stroke-width: 1.4; stroke-opacity: .72; }}
    .node circle:not(.trust-ring), .node rect, .node polygon {{ filter: drop-shadow(0 2px 5px rgba(26, 38, 52, .14)); }}
    .trust-ring {{ filter: none; }}
    .node text {{ font-size: 12px; fill: #25303f; pointer-events: none; }}
    .node-badge {{ font-size: 9px; fill: #fff; font-weight: 700; text-shadow: 0 1px 2px rgba(0,0,0,.34); }}
    .empty {{ fill: var(--muted); font-size: 16px; }}
    .side {{ display: grid; gap: 16px; }}
    .pill {{ display: inline-flex; align-items: center; border-radius: 999px; border: 1px solid var(--line); background: var(--soft); color: var(--ink); padding: 5px 9px; margin: 0 6px 6px 0; font-size: 12px; }}
    .pill.ok {{ border-color: #b7dfd8; color: var(--ok); background: #ecfdf9; }}
    .pill.warn {{ border-color: #f2d8a7; color: var(--warn); background: #fffbeb; }}
    ul {{ margin: 0; padding: 0; list-style: none; }}
    li {{ display: flex; justify-content: space-between; gap: 12px; padding: 7px 0; border-bottom: 1px solid var(--line); }}
    li:last-child {{ border-bottom: 0; }}
    .swatch {{ width: 13px; height: 13px; border-radius: 3px; border: 2px solid #fff; flex: 0 0 13px; margin-top: 2px; }}
    .line-swatch {{ width: 18px; height: 2px; border-radius: 2px; flex: 0 0 18px; margin-top: 7px; }}
    .ring-swatch {{ width: 13px; height: 13px; border-radius: 50%; border: 3px solid #91a4b7; flex: 0 0 13px; margin-top: 2px; }}
    .legend li {{ align-items: center; justify-content: flex-start; }}
    .legend li b {{ margin-left: auto; }}
    @media (max-width: 900px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .graph {{ min-width: 700px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>ChaseOS Studio Graph View</h1>
    <div>
      {_pill(model.get("status"), "PARTIAL")}
      {_pill("read-only")}
      {_pill("static html")}
      {_pill("full ui not built", "PARTIAL")}
    </div>
    <p class="muted">{_escape(target.get("resolved_path"))}</p>
    <div class="topline">
      {_metric("visible nodes", summary.get("visible_node_count", 0))}
      {_metric("visible edges", summary.get("visible_edge_count", 0))}
      {_metric("source nodes", summary.get("source_node_count", 0))}
      {_metric("source edges", summary.get("source_edge_count", 0))}
      {_metric("layout", summary.get("layout_algorithm"))}
    </div>
  </header>
  <main>
    <section class="layout">
      <div class="graph-wrap">{graph_svg}</div>
      <div class="side">
        {legend}
        {focus}
        {explainability}
        <section class="panel">
          <h2>Readiness</h2>
          <div class="mini-grid">
            {_metric("renderer", readiness.get("static_graph_renderer_ready"))}
            {_metric("browser qa", readiness.get("browser_visual_qa_ready"))}
            {_metric("next", readiness.get("next_recommended_pass"))}
          </div>
          <h3>Blockers</h3>
          <ul>{blockers or "<li>None<b>0</b></li>"}</ul>
          <h3>Warnings</h3>
          <ul>{warnings or "<li>None<b>0</b></li>"}</ul>
        </section>
        <section class="panel">
          <h2>Authority</h2>
          <ul>{blocked_authority or "<li>No blocked authority listed<b>0</b></li>"}</ul>
        </section>
      </div>
    </section>
  </main>
</body>
</html>
"""


def write_graph_view_static_html(
    vault_root: str | Path,
    *,
    focus_node_id: str | None = None,
    focus_path: str | Path | None = None,
    folder_path: str | Path | None = None,
    max_files: int | None = None,
    max_bytes_per_file: int | None = None,
    max_nodes: int | None = None,
    max_edges: int | None = None,
    layout_node_limit: int | None = None,
    content_excerpt_bytes: int | None = None,
    output_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Write static graph-view HTML under the Studio graph-view artifact root."""

    vault = _vault_path(vault_root)
    model = build_graph_view_static_render_model(
        vault,
        focus_node_id=focus_node_id,
        focus_path=focus_path,
        folder_path=folder_path,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
        max_nodes=max_nodes,
        max_edges=max_edges,
        layout_node_limit=layout_node_limit,
        content_excerpt_bytes=content_excerpt_bytes,
        generated_at=generated_at,
    )
    root = (vault / STATIC_RENDER_ROOT).resolve()
    if output_path is None:
        target = root / f"{_date_slug(model.get('generated_at'))}-graph-view-static.html"
    else:
        target = Path(output_path)
        target = target if target.is_absolute() else vault / target
    _assert_inside(target, root, "Graph view static render output must stay under 07_LOGS/Studio-Graph-Views")
    root.mkdir(parents=True, exist_ok=True)
    html_text = render_graph_view_static_html(model)
    target.write_text(html_text, encoding="utf-8")
    relative_path = _relative_to_vault(vault, target)
    model["writes"] = [relative_path]
    model["artifact"] = {
        "write_executed": True,
        "default_output_root": STATIC_RENDER_ROOT.as_posix(),
        "html_output_path": relative_path,
        "bytes": len(html_text.encode("utf-8")),
    }
    return model
