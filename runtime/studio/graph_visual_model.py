"""Read-only typed graph visual model helpers for Studio.

This module decorates already-derived graph nodes and edges with ChaseOS Studio
visual metadata. It performs no I/O and no writes; callers pass bounded graph
payloads in memory.
"""

from __future__ import annotations

from typing import Any

from runtime.studio.shell.graph_style_registry import (
    DEFAULT_EDGE_LAYERS,
    DEFAULT_NODE_FAMILIES,
    DEFAULT_TRUST_STATES,
    NODE_TYPE_TO_FAMILY,
    get_default_registry,
    validate_registry,
)


MODEL_VERSION = "studio.graph_visual_model.v1"
REQUIRED_NODE_FAMILY_COUNT = 14
REQUIRED_EDGE_LAYER_COUNT = 4
REQUIRED_TRUST_STATE_COUNT = 8
NEXT_RECOMMENDED_PASS = "phase10aa-controlled-node-create-edit"

CANONICAL_EDGE_LAYERS = ("explicit", "structural", "suggested", "runtime")
EDGE_LAYER_ALIASES = {
    "suggested-semantic": "suggested",
    "suggested_semantic": "suggested",
    "semantic": "suggested",
    "runtime-action": "runtime",
    "runtime_action": "runtime",
    "runtime-action-layer": "runtime",
    "runtime_action_layer": "runtime",
}

EDGE_LAYER_EXPORT_LABELS = {
    "explicit": "Explicit",
    "structural": "Structural",
    "suggested": "Suggested",
    "runtime": "Runtime-Action",
}


def normalize_edge_layer(value: Any) -> str:
    raw = str(value or "explicit").strip().lower().replace(" ", "-")
    normalized = EDGE_LAYER_ALIASES.get(raw, raw)
    return normalized if normalized in CANONICAL_EDGE_LAYERS else "explicit"


def _canonical_edge_layer_defs(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_layers = registry.get("edge_layers") or DEFAULT_EDGE_LAYERS
    layers: dict[str, dict[str, Any]] = {}
    for layer, definition in raw_layers.items():
        canonical = normalize_edge_layer(layer)
        layers[canonical] = dict(definition)
    return {layer: layers.get(layer) or dict((raw_layers.get(layer) or raw_layers.get("explicit") or {})) for layer in CANONICAL_EDGE_LAYERS}


def normalize_trust_state(value: Any) -> str:
    raw = str(value or "raw").strip().lower().replace(" ", "_")
    return raw if raw in DEFAULT_TRUST_STATES else "raw"


def normalize_node_family(node: dict[str, Any], registry: dict[str, Any] | None = None) -> str:
    reg = registry or get_default_registry()
    families = reg.get("node_families") or DEFAULT_NODE_FAMILIES
    node_type_map = reg.get("node_type_to_family") or NODE_TYPE_TO_FAMILY
    node_type = str(node.get("node_type") or "")
    family = str(node.get("node_family") or node_type_map.get(node_type) or "entity_object")
    return family if family in families else "entity_object"


def _properties(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("properties") or {}
    return value if isinstance(value, dict) else {}


def _counted_legend(
    defaults: dict[str, dict[str, Any]],
    counts: dict[str, int],
    *,
    export_layer_labels: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, definition in defaults.items():
        row = dict(definition)
        row["id"] = key
        row["count"] = int(counts.get(key, 0) or 0)
        if export_layer_labels:
            row["layer_label"] = EDGE_LAYER_EXPORT_LABELS.get(key, str(definition.get("label") or key))
            row["canonical_layer"] = "runtime-action" if key == "runtime" else key
        rows.append(row)
    return rows


def _safe_label(value: Any, limit: int = 44) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= limit else f"{text[: max(1, limit - 3)]}..."


def _node_visual(
    node: dict[str, Any],
    *,
    registry: dict[str, Any],
    degree: int,
) -> dict[str, Any]:
    props = _properties(node)
    families = registry.get("node_families") or DEFAULT_NODE_FAMILIES
    trust_states = registry.get("trust_states") or DEFAULT_TRUST_STATES
    family = normalize_node_family(node, registry)
    trust_state = normalize_trust_state(props.get("trust_state"))
    family_def = families.get(family) or families["entity_object"]
    trust_def = trust_states.get(trust_state) or trust_states["raw"]
    generated = bool(
        trust_state == "generated"
        or family == "generated_artifact"
        or props.get("generated") is True
        or props.get("source_kind") == "generated"
    )
    canonical = bool(trust_state == "canonical" or props.get("canonical") is True)
    family_badge = family_def.get("badge")
    trust_badge = trust_def.get("badge")
    badges = [badge for badge in (family_badge, trust_badge, "CAN" if canonical else None) if badge]
    label = _safe_label(node.get("label") or node.get("title") or node.get("id"))
    display_label = label if not badges else f"{label} [{' '.join(badges)}]"
    content_class = " content--canonical" if canonical else ""
    content_class += " content--generated" if generated else ""
    return {
        "id": str(node.get("id")),
        "label": label,
        "display_label": display_label,
        "node_type": str(node.get("node_type") or "unknown"),
        "node_family": family,
        "trust_state": trust_state,
        "classes": f"node node--{family} trust--{trust_state}{content_class}",
        "shape": family_def.get("shape"),
        "fill_color": family_def.get("fill_color"),
        "border_color": family_def.get("border_color"),
        "border_style": family_def.get("border_style"),
        "border_width": family_def.get("border_width"),
        "size": int(family_def.get("size_base") or 18) + min(12, max(0, degree) * 2),
        "family_label": family_def.get("label"),
        "family_badge": family_badge,
        "trust_label": trust_def.get("label"),
        "trust_badge": trust_badge,
        "trust_ring_color": trust_def.get("ring_color"),
        "trust_ring_style": trust_def.get("ring_style"),
        "trust_ring_width": trust_def.get("ring_width"),
        "generated": generated,
        "canonical": canonical,
        "degree": degree,
        "display_badges": badges,
    }


def _edge_visual(edge: dict[str, Any], *, registry: dict[str, Any]) -> dict[str, Any]:
    props = _properties(edge)
    layers = _canonical_edge_layer_defs(registry)
    layer = normalize_edge_layer(edge.get("edge_layer") or props.get("edge_layer"))
    layer_def = layers.get(layer) or layers["explicit"]
    return {
        "id": str(edge.get("id")),
        "source": str(edge.get("source")),
        "target": str(edge.get("target")),
        "relation": str(edge.get("relation") or ""),
        "edge_layer": layer,
        "canonical_layer": "runtime-action" if layer == "runtime" else layer,
        "classes": f"edge edge--{layer}",
        "label": layer_def.get("label"),
        "layer_label": EDGE_LAYER_EXPORT_LABELS.get(layer, str(layer_def.get("label") or layer)),
        "color": layer_def.get("color"),
        "line_style": layer_def.get("line_style"),
        "width": layer_def.get("width"),
        "opacity": layer_def.get("opacity"),
        "arrow": layer_def.get("arrow"),
        "animated": bool(layer_def.get("animated")),
        "visible": bool(layer_def.get("visible", True)),
    }


def _degree_counts(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, int]:
    node_ids = {str(node.get("id")) for node in nodes}
    degrees = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source in degrees:
            degrees[source] += 1
        if target in degrees:
            degrees[target] += 1
    return degrees


def _hex_to_rgb(value: Any) -> tuple[float, float, float] | None:
    text = str(value or "").strip().lstrip("#")
    if len(text) != 6:
        return None
    try:
        return tuple(int(text[index : index + 2], 16) / 255 for index in (0, 2, 4))  # type: ignore[return-value]
    except ValueError:
        return None


def _linear(channel: float) -> float:
    return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4


def contrast_ratio(foreground: Any, background: Any = "#0f172a") -> float | None:
    fg = _hex_to_rgb(foreground)
    bg = _hex_to_rgb(background)
    if fg is None or bg is None:
        return None
    fg_lum = 0.2126 * _linear(fg[0]) + 0.7152 * _linear(fg[1]) + 0.0722 * _linear(fg[2])
    bg_lum = 0.2126 * _linear(bg[0]) + 0.7152 * _linear(bg[1]) + 0.0722 * _linear(bg[2])
    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def build_graph_visual_model(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    graph_summary: dict[str, Any] | None = None,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return typed node, edge layer, and trust overlay metadata."""

    reg = registry or get_default_registry()
    registry_validation = validate_registry(reg)
    degrees = _degree_counts(nodes, edges)
    node_visuals = [_node_visual(node, registry=reg, degree=degrees.get(str(node.get("id")), 0)) for node in nodes]
    edge_visuals = [_edge_visual(edge, registry=reg) for edge in edges]

    node_family_counts = {family: 0 for family in (reg.get("node_families") or DEFAULT_NODE_FAMILIES)}
    trust_state_counts = {state: 0 for state in (reg.get("trust_states") or DEFAULT_TRUST_STATES)}
    edge_layer_defs = _canonical_edge_layer_defs(reg)
    edge_layer_counts = {layer: 0 for layer in edge_layer_defs}
    for visual in node_visuals:
        node_family_counts[visual["node_family"]] = node_family_counts.get(visual["node_family"], 0) + 1
        trust_state_counts[visual["trust_state"]] = trust_state_counts.get(visual["trust_state"], 0) + 1
    for visual in edge_visuals:
        edge_layer_counts[visual["edge_layer"]] = edge_layer_counts.get(visual["edge_layer"], 0) + 1

    generated_count = sum(1 for visual in node_visuals if visual["generated"])
    canonical_count = sum(1 for visual in node_visuals if visual["canonical"])
    accessibility_rows = []
    for family, family_def in (reg.get("node_families") or DEFAULT_NODE_FAMILIES).items():
        ratio = contrast_ratio(family_def.get("fill_color"))
        accessibility_rows.append(
            {
                "node_family": family,
                "fill_color": family_def.get("fill_color"),
                "background": "#0f172a",
                "contrast_ratio": ratio,
                "minimum_large_icon_contrast_ready": bool(ratio is not None and ratio >= 3.0),
            }
        )

    return {
        "model_version": MODEL_VERSION,
        "registry_schema_version": reg.get("schema_version"),
        "registry_valid": bool(registry_validation.get("ok")),
        "registry_errors": registry_validation.get("errors", []),
        "node_visuals": node_visuals,
        "edge_visuals": edge_visuals,
        "node_visual_map": {visual["id"]: visual for visual in node_visuals},
        "edge_visual_map": {visual["id"]: visual for visual in edge_visuals},
        "legend": {
            "node_families": _counted_legend(reg.get("node_families") or DEFAULT_NODE_FAMILIES, node_family_counts),
            "edge_layers": _counted_legend(
                edge_layer_defs,
                edge_layer_counts,
                export_layer_labels=True,
            ),
            "trust_states": _counted_legend(reg.get("trust_states") or DEFAULT_TRUST_STATES, trust_state_counts),
            "generated_vs_canonical": [
                {"id": "generated", "label": "Generated", "count": generated_count},
                {"id": "canonical", "label": "Canonical", "count": canonical_count},
            ],
        },
        "summary": {
            "visible_node_count": len(nodes),
            "visible_edge_count": len(edges),
            "node_family_counts": node_family_counts,
            "trust_state_counts": trust_state_counts,
            "edge_layer_counts": edge_layer_counts,
            "generated_count": generated_count,
            "canonical_count": canonical_count,
            "generated_vs_canonical_ready": True,
        },
        "coverage": {
            "node_family_count": len(reg.get("node_families") or {}),
            "edge_layer_count": len(edge_layer_defs),
            "trust_state_count": len(reg.get("trust_states") or {}),
            "all_14_node_families_available": len(reg.get("node_families") or {}) == REQUIRED_NODE_FAMILY_COUNT,
            "all_4_edge_layers_available": len(edge_layer_defs) == REQUIRED_EDGE_LAYER_COUNT,
            "all_8_trust_states_available": len(reg.get("trust_states") or {}) == REQUIRED_TRUST_STATE_COUNT,
            "runtime_action_layer_available": "runtime" in edge_layer_defs,
            "runtime_action_export_label": EDGE_LAYER_EXPORT_LABELS["runtime"],
        },
        "accessibility": {
            "contrast_background": "#0f172a",
            "family_contrast": accessibility_rows,
            "high_contrast_overlay_metadata_ready": True,
        },
        "source_summary": graph_summary or {},
    }


def visual_model_ready(visual_model: dict[str, Any], *, graph_ready: bool, blockers: list[str]) -> bool:
    coverage = visual_model.get("coverage") or {}
    return bool(
        graph_ready
        and not blockers
        and visual_model.get("registry_valid") is True
        and coverage.get("all_14_node_families_available") is True
        and coverage.get("all_4_edge_layers_available") is True
        and coverage.get("all_8_trust_states_available") is True
    )
