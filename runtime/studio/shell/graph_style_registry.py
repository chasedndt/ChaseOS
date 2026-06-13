"""ChaseOS Studio — graph design system style registry.

Defines defaults for all 14 node families, 4 edge layers, and 8 trust states.
Schema validation. Read-only module — no I/O, no writes.
"""
from __future__ import annotations

SCHEMA_VERSION = "studio.graph.style.registry.v1"

VALID_SHAPES: frozenset[str] = frozenset({
    "ellipse", "triangle", "round-triangle", "rectangle", "round-rectangle",
    "bottom-round-rectangle", "cut-rectangle", "barrel", "rhomboid",
    "right-rhomboid", "diamond", "round-diamond", "pentagon", "round-pentagon",
    "hexagon", "round-hexagon", "concave-hexagon", "heptagon", "round-heptagon",
    "octagon", "round-octagon", "star", "tag", "round-tag", "vee",
})
VALID_BORDER_STYLES: frozenset[str] = frozenset({"solid", "dashed", "dotted", "double"})
VALID_LINE_STYLES: frozenset[str] = frozenset({"solid", "dashed", "dotted"})
VALID_ARROW_STYLES: frozenset[str] = frozenset({
    "triangle", "triangle-backcurve", "vee", "tee", "circle", "none",
})
VALID_TRUST_STATES: frozenset[str] = frozenset({
    "raw", "quarantined", "suggested", "promoted", "canonical",
    "archived", "disputed", "generated",
})
VALID_EDGE_LAYERS: frozenset[str] = frozenset({"explicit", "structural", "suggested_semantic", "runtime_action"})
EDGE_LAYER_ALIASES: dict[str, str] = {
    "suggested": "suggested_semantic",
    "semantic": "suggested_semantic",
    "runtime": "runtime_action",
    "runtime-action": "runtime_action",
}

# Mapping from actual graph_index_contract node_type → canonical 14-family
NODE_TYPE_TO_FAMILY: dict[str, str] = {
    "system_root_doc":            "knowledge",
    "chaseos_markdown_doc":       "knowledge",
    "markdown_note":              "knowledge",
    "home_doc":                   "knowledge",
    "project_doc":                "project",
    "knowledge_doc":              "knowledge",
    "source_doc":                 "source",
    "intake_doc":                 "intake",
    "generated_artifact_doc":     "generated_artifact",
    "sop_template_doc":           "sop_template",
    "workflow_doc":               "workflow",
    "agent_control_doc":          "agent",
    "runtime_doc":                "runtime",
    "decision_doc":               "decision",
    "log_audit":                  "log_audit",
    "build_log":                  "log_audit",
    "documentation_history_note": "log_audit",
    "daily_note":                 "log_audit",
    "markdown_heading":           "entity_object",
    "markdown_tag":               "entity_object",
    "markdown_task":              "entity_object",
    "obsidian_block_marker":      "entity_object",
    "unresolved_wikilink":        "entity_object",
    "unresolved_markdown_link":   "entity_object",
    "external_resource":          "entity_object",
    # Future / explicitly named families map to themselves
    "project":                    "project",
    "domain":                     "domain",
    "knowledge":                  "knowledge",
    "source":                     "source",
    "synthesis":                  "synthesis",
    "intake":                     "intake",
    "generated_artifact":         "generated_artifact",
    "sop_template":               "sop_template",
    "workflow":                   "workflow",
    "agent":                      "agent",
    "runtime":                    "runtime",
    "decision":                   "decision",
    "log_audit":                  "log_audit",
    "entity_object":              "entity_object",
}

DEFAULT_NODE_FAMILIES: dict[str, dict] = {
    "project": {
        "label": "Project",
        "shape": "round-rectangle",
        "fill_color": "#0ea5e9",
        "border_color": "#38bdf8",
        "border_style": "solid",
        "border_width": 2,
        "badge": None,
        "size_base": 28,
        "label_mode": "title",
        "description": "Active project or workspace node",
    },
    "domain": {
        "label": "Domain",
        "shape": "barrel",
        "fill_color": "#0891b2",
        "border_color": "#22d3ee",
        "border_style": "solid",
        "border_width": 2,
        "badge": None,
        "size_base": 32,
        "label_mode": "title",
        "description": "Knowledge or operating domain",
    },
    "knowledge": {
        "label": "Knowledge",
        "shape": "rectangle",
        "fill_color": "#6366f1",
        "border_color": "#818cf8",
        "border_style": "solid",
        "border_width": 2,
        "badge": None,
        "size_base": 22,
        "label_mode": "title",
        "description": "Durable reusable knowledge note",
    },
    "source": {
        "label": "Source",
        "shape": "cut-rectangle",
        "fill_color": "#0e7490",
        "border_color": "#06b6d4",
        "border_style": "solid",
        "border_width": 2,
        "badge": None,
        "size_base": 20,
        "label_mode": "title",
        "description": "Source note or evidence item",
    },
    "synthesis": {
        "label": "Synthesis",
        "shape": "hexagon",
        "fill_color": "#0369a1",
        "border_color": "#0ea5e9",
        "border_style": "solid",
        "border_width": 2,
        "badge": None,
        "size_base": 26,
        "label_mode": "title",
        "description": "Multi-source synthesis or combined reasoning",
    },
    "intake": {
        "label": "Intake",
        "shape": "tag",
        "fill_color": "#c2410c",
        "border_color": "#f97316",
        "border_style": "dashed",
        "border_width": 2,
        "badge": "IN",
        "size_base": 20,
        "label_mode": "title",
        "description": "Raw or quarantine input — not yet promoted",
    },
    "generated_artifact": {
        "label": "Generated",
        "shape": "star",
        "fill_color": "#7e22ce",
        "border_color": "#a855f7",
        "border_style": "dashed",
        "border_width": 2,
        "badge": "AI",
        "size_base": 24,
        "label_mode": "title",
        "description": "AI-generated artifact or proposal — not canonical unless promoted",
    },
    "sop_template": {
        "label": "SOP / Template",
        "shape": "round-tag",
        "fill_color": "#6d28d9",
        "border_color": "#8b5cf6",
        "border_style": "solid",
        "border_width": 2,
        "badge": None,
        "size_base": 22,
        "label_mode": "title",
        "description": "SOP, template, or repeatable operational procedure",
    },
    "workflow": {
        "label": "Workflow",
        "shape": "diamond",
        "fill_color": "#3f6212",
        "border_color": "#84cc16",
        "border_style": "solid",
        "border_width": 2,
        "badge": "WF",
        "size_base": 26,
        "label_mode": "title",
        "description": "AOR/SBP workflow — runnable or planned",
    },
    "agent": {
        "label": "Agent",
        "shape": "octagon",
        "fill_color": "#4c1d95",
        "border_color": "#7c3aed",
        "border_style": "solid",
        "border_width": 2,
        "badge": "A",
        "size_base": 28,
        "label_mode": "title",
        "description": "Agent or runtime actor identity",
    },
    "runtime": {
        "label": "Runtime",
        "shape": "pentagon",
        "fill_color": "#881337",
        "border_color": "#f43f5e",
        "border_style": "solid",
        "border_width": 2,
        "badge": "RT",
        "size_base": 26,
        "label_mode": "title",
        "description": "Runtime lane, process, or system surface",
    },
    "decision": {
        "label": "Decision",
        "shape": "vee",
        "fill_color": "#1e3a8a",
        "border_color": "#3b82f6",
        "border_style": "solid",
        "border_width": 2,
        "badge": "D",
        "size_base": 24,
        "label_mode": "title",
        "description": "Decision ledger entry, approval record, or pivot",
    },
    "log_audit": {
        "label": "Log / Audit",
        "shape": "cut-rectangle",
        "fill_color": "#78350f",
        "border_color": "#f59e0b",
        "border_style": "solid",
        "border_width": 2,
        "badge": "L",
        "size_base": 20,
        "label_mode": "title",
        "description": "Build log, agent activity record, or audit artifact",
    },
    "entity_object": {
        "label": "Entity / Object",
        "shape": "ellipse",
        "fill_color": "#1e293b",
        "border_color": "#64748b",
        "border_style": "solid",
        "border_width": 1,
        "badge": None,
        "size_base": 18,
        "label_mode": "title",
        "description": "Person, bookmark, external resource, tool, account, or entity",
    },
}

DEFAULT_EDGE_LAYERS: dict[str, dict] = {
    "explicit": {
        "label": "Explicit Link",
        "color": "#38bdf8",
        "line_style": "solid",
        "width": 1.4,
        "opacity": 0.62,
        "arrow": "triangle",
        "animated": False,
        "visible": True,
        "description": "Wikilinks, markdown links, authored connections",
    },
    "structural": {
        "label": "Structural",
        "color": "#475569",
        "line_style": "dotted",
        "width": 1.0,
        "opacity": 0.40,
        "arrow": "none",
        "animated": False,
        "visible": True,
        "description": "Folder/domain/project lineage, parent-child, derived-by",
    },
    "suggested_semantic": {
        "label": "Suggested Semantic",
        "color": "#facc15",
        "line_style": "dashed",
        "width": 1.1,
        "opacity": 0.45,
        "arrow": "triangle",
        "animated": False,
        "visible": True,
        "confidence_threshold": 0.55,
        "description": "Advisory AI-suggested relations — never canonical",
    },
    "runtime_action": {
        "label": "Runtime / Action",
        "color": "#a855f7",
        "line_style": "solid",
        "width": 1.5,
        "opacity": 0.66,
        "arrow": "triangle",
        "animated": True,
        "visible": True,
        "confidence_threshold": 0.0,
        "description": "Agent touched-by, workflow output-of, approval/audit links",
    },
}

DEFAULT_TRUST_STATES: dict[str, dict] = {
    "raw": {
        "label": "Raw",
        "ring_color": "#94a3b8",
        "ring_style": "solid",
        "ring_width": 3,
        "badge": None,
        "description": "Unprocessed external input",
    },
    "quarantined": {
        "label": "Quarantined",
        "ring_color": "#f97316",
        "ring_style": "dashed",
        "ring_width": 4,
        "badge": "Q",
        "description": "Held for review — not yet trusted",
    },
    "suggested": {
        "label": "Suggested",
        "ring_color": "#facc15",
        "ring_style": "dashed",
        "ring_width": 3,
        "badge": None,
        "description": "Proposal or candidate — advisory only",
    },
    "promoted": {
        "label": "Promoted",
        "ring_color": "#22c55e",
        "ring_style": "solid",
        "ring_width": 3,
        "badge": None,
        "description": "Passed promotion flow — trusted",
    },
    "canonical": {
        "label": "Canonical",
        "ring_color": "#3b82f6",
        "ring_style": "double",
        "ring_width": 4,
        "badge": None,
        "description": "Active authoritative system truth",
    },
    "archived": {
        "label": "Archived",
        "ring_color": "#6b7280",
        "ring_style": "dotted",
        "ring_width": 2,
        "badge": None,
        "description": "Historical or inactive",
    },
    "disputed": {
        "label": "Disputed",
        "ring_color": "#ef4444",
        "ring_style": "dashed",
        "ring_width": 4,
        "badge": "!",
        "description": "Conflict, contradiction, or needs review",
    },
    "generated": {
        "label": "Generated",
        "ring_color": "#a855f7",
        "ring_style": "dashed",
        "ring_width": 3,
        "badge": "AI",
        "description": "AI-generated artifact — not canonical unless promoted",
    },
}


def get_default_registry() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "node_families": {k: dict(v) for k, v in DEFAULT_NODE_FAMILIES.items()},
        "edge_layers": {k: dict(v) for k, v in DEFAULT_EDGE_LAYERS.items()},
        "trust_states": {k: dict(v) for k, v in DEFAULT_TRUST_STATES.items()},
        "node_type_to_family": dict(NODE_TYPE_TO_FAMILY),
        "edge_layer_aliases": dict(EDGE_LAYER_ALIASES),
    }


def canonical_edge_layer(layer: str | None) -> str:
    raw = str(layer or "explicit").strip().lower().replace("-", "_")
    return EDGE_LAYER_ALIASES.get(raw, raw if raw in VALID_EDGE_LAYERS else "explicit")


def validate_node_family(family: dict) -> list[str]:
    errors = []
    shape = family.get("shape")
    if shape not in VALID_SHAPES:
        errors.append(f"invalid shape: {shape!r}. Valid: {sorted(VALID_SHAPES)}")
    border_style = family.get("border_style")
    if border_style not in VALID_BORDER_STYLES:
        errors.append(f"invalid border_style: {border_style!r}")
    return errors


def validate_edge_layer(layer: dict) -> list[str]:
    errors = []
    line_style = layer.get("line_style")
    if line_style not in VALID_LINE_STYLES:
        errors.append(f"invalid line_style: {line_style!r}")
    arrow = layer.get("arrow")
    if arrow not in VALID_ARROW_STYLES:
        errors.append(f"invalid arrow: {arrow!r}")
    opacity = layer.get("opacity")
    try:
        if opacity is not None and not (0.05 <= float(opacity) <= 1.0):
            errors.append(f"invalid opacity: {opacity!r}")
    except (TypeError, ValueError):
        errors.append(f"invalid opacity: {opacity!r}")
    width = layer.get("width")
    try:
        if width is not None and not (0.25 <= float(width) <= 12.0):
            errors.append(f"invalid width: {width!r}")
    except (TypeError, ValueError):
        errors.append(f"invalid width: {width!r}")
    return errors


def validate_trust_state(ts: dict) -> list[str]:
    errors = []
    ring_style = ts.get("ring_style")
    if ring_style not in VALID_BORDER_STYLES:
        errors.append(f"invalid ring_style: {ring_style!r}")
    return errors


def validate_registry(registry: dict) -> dict:
    """Returns {"ok": bool, "errors": list[str]}."""
    errors: list[str] = []
    for name, family in (registry.get("node_families") or {}).items():
        for err in validate_node_family(family):
            errors.append(f"node_family.{name}: {err}")
    for name, layer in (registry.get("edge_layers") or {}).items():
        for err in validate_edge_layer(layer):
            errors.append(f"edge_layer.{name}: {err}")
    for name, ts in (registry.get("trust_states") or {}).items():
        for err in validate_trust_state(ts):
            errors.append(f"trust_state.{name}: {err}")
    return {"ok": not errors, "errors": errors}
