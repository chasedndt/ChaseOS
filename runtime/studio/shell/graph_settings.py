"""ChaseOS Studio — graph settings persistence layer.

Loads/saves/resets graph-settings.json in ~/.chaseos/studio/.
Atomic writes (temp + os.replace). No vault writes.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.studio.shell.graph_style_registry import (
    DEFAULT_EDGE_LAYERS,
    DEFAULT_NODE_FAMILIES,
    DEFAULT_TRUST_STATES,
    VALID_ARROW_STYLES,
    VALID_BORDER_STYLES,
    VALID_EDGE_LAYERS,
    VALID_LINE_STYLES,
    VALID_SHAPES,
    VALID_TRUST_STATES,
    canonical_edge_layer,
    get_default_registry,
)

SETTINGS_VERSION = "studio.graph.settings.v1"

_SETTINGS_FILENAME = "graph-settings.json"


# ── Default settings structure (8 sections) ──────────────────────────────────

def _default_appearance() -> dict:
    return {
        "theme": "system",
        "background_color": "#0f172a",
        "grid": False,
        "show_labels": True,
        "label_fade_threshold": 0.55,
        "label_font_size": 11,
        "label_max_length": 32,
        "node_size_base": 24,
        "node_size_by_degree": True,
        "node_opacity": 0.92,
        "link_thickness": 1.0,
        "arrowheads": True,
        "minimap": False,
        "edge_opacity_multiplier": 1.0,
        "animate_runtime_edges": True,
        "show_badges": True,
        "underlay_opacity": 0.18,
    }


def _default_node_families() -> dict:
    """Per-family overrides — starts as empty (falls back to registry defaults)."""
    return {family: {} for family in DEFAULT_NODE_FAMILIES}


def _default_edge_layers() -> dict:
    return {
        layer: {"visible": data["visible"]}
        for layer, data in DEFAULT_EDGE_LAYERS.items()
    }


def _default_trust_states() -> dict:
    return {
        ts: {
            "ring_color": data["ring_color"],
            "ring_width": data["ring_width"],
            "ring_style": data["ring_style"],
            "badge": data.get("badge"),
            "badge_visible": True,
            "pattern_fallback": data["ring_style"] in {"dashed", "dotted", "double"},
        }
        for ts, data in DEFAULT_TRUST_STATES.items()
    }


def _default_accessibility() -> dict:
    return {
        "high_contrast": False,
        "colorblind_mode": "none",
        "colorblind_safe_palette": False,
        "min_edge_width": 1.0,
        "motion_reduce": False,
        "large_labels": False,
        "shape_first_mode": False,
        "pattern_first_trust_rings": True,
        "keyboard_navigation": True,
    }


def _default_node_scope() -> dict:
    return {
        "files_pages": True,
        "headings": True,
        "blocks": False,
        "tasks": False,
        "external_resources": "contract",
        "show_entity_objects": True,
        "show_unresolved_links": True,
        "show_external_resources": True,
        "max_nodes": 1500,
        "max_edges": 4500,
        "max_labels_visible": 150,
    }


def _default_layout() -> dict:
    return {
        "algorithm": "cose",
        "animate_layout": True,
        "node_repulsion": 400000,
        "ideal_edge_length": 80,
        "gravity": 0.25,
        "cluster_by_domain": False,
        "cluster_by_project": False,
        "cluster_by_trust_state": False,
        "local_graph_depth": 1,
        "focus_radius": 2,
        "pinned_nodes": [],
    }


def _default_inspector() -> dict:
    return {
        "default_tab": "overview",
        "show_raw_metadata": False,
        "show_source_content": True,
        "show_provenance_tab": True,
        "show_source_excerpt": True,
        "source_excerpt_length": 1200,
        "show_warnings": True,
        "show_related_nodes": True,
        "show_relation_counts": True,
        "max_relation_display": 50,
    }


def _default_performance() -> dict:
    return {
        # Quality shorthand: ultra | balanced | performance | minimal
        # Changing quality_preset overwrites the individual fields below.
        "quality_preset": "balanced",
        # Physics warmup — pre-simulate N frames before first draw (0 = instant render)
        # 100 warmup frames means nodes are already spread on first visual frame.
        "warmup_ticks": 100,
        # Physics cooldown — pause simulation after N frames (-1 = run forever)
        "cooldown_ticks": 400,
        # D3 alpha decay (lower = longer, smoother simulation; default 0.0228)
        "d3_alpha_decay": 0.0228,
        # D3 velocity decay / damping (higher = quicker stop; default 0.4)
        "d3_velocity_decay": 0.4,
        # Device pixel ratio (0 = auto from window.devicePixelRatio; 1 = native)
        "device_pixel_ratio": 0,
        # Run D3 physics (false = static / frozen layout)
        "physics_enabled": True,
        # 2 = flat 2-D graph (much faster on low-end); 3 = full 3-D
        "num_dimensions": 3,
    }


def get_default_settings() -> dict:
    return {
        "schema_version": SETTINGS_VERSION,
        "updated_at": None,
        "appearance": _default_appearance(),
        "node_families": _default_node_families(),
        "edge_layers": _default_edge_layers(),
        "trust_states": _default_trust_states(),
        "accessibility": _default_accessibility(),
        "node_scope": _default_node_scope(),
        "layout": _default_layout(),
        "inspector": _default_inspector(),
        "performance": _default_performance(),
        "generated_canonical": {
            "generated_badge_visible": True,
            "canonical_badge_visible": True,
            "generated_origin_badge_persists_after_promotion": True,
        },
    }


# ── Validation ────────────────────────────────────────────────────────────────

_VALID_COLORBLIND_MODES = frozenset({"none", "deuteranopia", "protanopia", "tritanopia"})
_VALID_LAYOUT_ALGORITHMS = frozenset({"cose", "grid", "circle", "concentric", "breadthfirst", "random"})
_VALID_INSPECTOR_TABS = frozenset({"overview", "relations", "provenance", "trust", "runtime", "source", "debug"})
_VALID_THEMES = frozenset({"system", "light", "dark", "custom"})


def _is_hex_color(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if len(value) not in (4, 7):
        return False
    if not value.startswith("#"):
        return False
    try:
        int(value[1:], 16)
    except ValueError:
        return False
    return True


def validate_settings(settings: dict) -> dict:
    """Returns {"ok": bool, "errors": list[str], "warnings": list[str]}."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(settings, dict):
        return {"ok": False, "errors": ["settings must be a dict"], "warnings": []}

    # Appearance
    app = settings.get("appearance", {})
    theme = app.get("theme")
    if theme is not None and theme not in _VALID_THEMES:
        errors.append(f"appearance.theme invalid: {theme!r}. Valid: {sorted(_VALID_THEMES)}")
    bg = app.get("background_color")
    if bg is not None and not _is_hex_color(bg):
        errors.append(f"appearance.background_color invalid hex color: {bg!r}")
    font_size = app.get("label_font_size")
    if font_size is not None and not (6 <= font_size <= 32):
        errors.append(f"appearance.label_font_size out of range [6,32]: {font_size}")
    max_len = app.get("label_max_length")
    if max_len is not None and not (8 <= max_len <= 128):
        errors.append(f"appearance.label_max_length out of range [8,128]: {max_len}")
    node_opacity = app.get("node_opacity")
    if node_opacity is not None and not (0.1 <= node_opacity <= 1.0):
        errors.append(f"appearance.node_opacity out of range [0.1,1.0]: {node_opacity}")
    edge_mult = app.get("edge_opacity_multiplier")
    if edge_mult is not None and not (0.1 <= edge_mult <= 1.5):
        errors.append(f"appearance.edge_opacity_multiplier out of range [0.1,1.5]: {edge_mult}")

    # Node family overrides
    for family, cfg in (settings.get("node_families") or {}).items():
        if family not in DEFAULT_NODE_FAMILIES:
            errors.append(f"node_families.{family} unknown family")
            continue
        shape = cfg.get("shape")
        if shape is not None and shape not in VALID_SHAPES:
            errors.append(f"node_families.{family}.shape invalid: {shape!r}")
        border_style = cfg.get("border_style")
        if border_style is not None and border_style not in VALID_BORDER_STYLES:
            errors.append(f"node_families.{family}.border_style invalid: {border_style!r}")
        for color_key in ("fill_color", "border_color"):
            color = cfg.get(color_key)
            if color is not None and not _is_hex_color(color):
                errors.append(f"node_families.{family}.{color_key} invalid hex color: {color!r}")

    # Edge layer overrides
    for layer, cfg in (settings.get("edge_layers") or {}).items():
        canonical_layer = canonical_edge_layer(layer)
        if canonical_layer not in VALID_EDGE_LAYERS:
            errors.append(f"edge_layers.{layer} unknown layer")
            continue
        line_style = cfg.get("line_style")
        if line_style is not None and line_style not in VALID_LINE_STYLES:
            errors.append(f"edge_layers.{layer}.line_style invalid: {line_style!r}")
        arrow = cfg.get("arrow")
        if arrow is not None and arrow not in VALID_ARROW_STYLES:
            errors.append(f"edge_layers.{layer}.arrow invalid: {arrow!r}")
        color = cfg.get("color")
        if color is not None and not _is_hex_color(color):
            errors.append(f"edge_layers.{layer}.color invalid hex color: {color!r}")
        opacity = cfg.get("opacity")
        if opacity is not None and not (0.05 <= opacity <= 1.0):
            errors.append(f"edge_layers.{layer}.opacity out of range [0.05,1.0]: {opacity}")
        confidence = cfg.get("confidence_threshold")
        if confidence is not None and not (0.0 <= confidence <= 1.0):
            errors.append(f"edge_layers.{layer}.confidence_threshold out of range [0,1]: {confidence}")

    # Trust-state visual indicators are configurable but not hideable.
    non_color_indicator_count = 0
    for trust_state, cfg in (settings.get("trust_states") or {}).items():
        if trust_state not in VALID_TRUST_STATES:
            errors.append(f"trust_states.{trust_state} unknown trust state")
            continue
        if cfg.get("visible") is False:
            errors.append(f"trust_states.{trust_state}.visible cannot be false; trust indicators are mandatory")
        ring_style = cfg.get("ring_style")
        if ring_style is not None and ring_style not in VALID_BORDER_STYLES:
            errors.append(f"trust_states.{trust_state}.ring_style invalid: {ring_style!r}")
        ring_color = cfg.get("ring_color")
        if ring_color is not None and not _is_hex_color(ring_color):
            errors.append(f"trust_states.{trust_state}.ring_color invalid hex color: {ring_color!r}")
        if cfg.get("badge_visible") is not False and cfg.get("badge"):
            non_color_indicator_count += 1
        if ring_style in {"dashed", "dotted", "double"} or cfg.get("pattern_fallback"):
            non_color_indicator_count += 1
    if non_color_indicator_count < 1:
        errors.append("trust_states require at least one non-color indicator")

    # Accessibility
    acc = settings.get("accessibility", {})
    cb_mode = acc.get("colorblind_mode")
    if cb_mode is not None and cb_mode not in _VALID_COLORBLIND_MODES:
        errors.append(f"accessibility.colorblind_mode invalid: {cb_mode!r}. Valid: {sorted(_VALID_COLORBLIND_MODES)}")

    # Node scope
    scope = settings.get("node_scope", {})
    max_nodes = scope.get("max_nodes")
    if max_nodes is not None and not (10 <= max_nodes <= 12000):
        errors.append(f"node_scope.max_nodes out of range [10,12000]: {max_nodes}")
    max_edges = scope.get("max_edges")
    if max_edges is not None and not (10 <= max_edges <= 40000):
        errors.append(f"node_scope.max_edges out of range [10,40000]: {max_edges}")

    # Layout
    layout = settings.get("layout", {})
    algo = layout.get("algorithm")
    if algo is not None and algo not in _VALID_LAYOUT_ALGORITHMS:
        errors.append(f"layout.algorithm invalid: {algo!r}. Valid: {sorted(_VALID_LAYOUT_ALGORITHMS)}")

    # Inspector
    inspector = settings.get("inspector", {})
    tab = inspector.get("default_tab")
    if tab is not None and tab not in _VALID_INSPECTOR_TABS:
        errors.append(f"inspector.default_tab invalid: {tab!r}. Valid: {sorted(_VALID_INSPECTOR_TABS)}")

    generated_canonical = settings.get("generated_canonical", {})
    if generated_canonical.get("generated_badge_visible") is False:
        errors.append("generated_canonical.generated_badge_visible cannot be false")
    if generated_canonical.get("canonical_badge_visible") is False:
        errors.append("generated_canonical.canonical_badge_visible cannot be false")
    if generated_canonical.get("generated_origin_badge_persists_after_promotion") is False:
        errors.append("generated_canonical.generated_origin_badge_persists_after_promotion cannot be false")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


# ── Merge helpers ─────────────────────────────────────────────────────────────

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base (base takes precedence for missing keys)."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


# ── I/O ───────────────────────────────────────────────────────────────────────

def _settings_path(state_dir: Path) -> Path:
    return state_dir / _SETTINGS_FILENAME


def load_graph_settings(state_dir: Path) -> dict:
    """Load settings from disk, merging over defaults. Always returns a valid dict."""
    path = _settings_path(state_dir)
    defaults = get_default_settings()
    if not path.exists():
        return defaults
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return defaults
        raw = _migrate_legacy_settings(raw)
        merged = _deep_merge(defaults, raw)
        merged["schema_version"] = SETTINGS_VERSION
        return merged
    except (json.JSONDecodeError, OSError):
        return defaults


def save_graph_settings(state_dir: Path, settings: dict) -> dict:
    """Atomic write of settings to disk. Returns {"ok": bool, "errors": list}."""
    validation = validate_settings(settings)
    if not validation["ok"]:
        return {"ok": False, "errors": validation["errors"]}

    settings = dict(settings)
    settings["schema_version"] = SETTINGS_VERSION
    settings["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    state_dir.mkdir(parents=True, exist_ok=True)
    target = _settings_path(state_dir)
    try:
        fd, tmp_path = tempfile.mkstemp(dir=state_dir, suffix=".tmp", prefix=".graph-settings-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(settings, fh, indent=2, ensure_ascii=False)
            os.replace(tmp_path, target)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except OSError as exc:
        return {"ok": False, "errors": [f"write failed: {exc}"]}
    return {"ok": True, "errors": []}


def reset_graph_settings(state_dir: Path) -> dict:
    """Delete settings file so next load returns defaults. Returns {"ok": bool}."""
    path = _settings_path(state_dir)
    try:
        if path.exists():
            path.unlink()
    except OSError as exc:
        return {"ok": False, "errors": [f"delete failed: {exc}"]}
    return {"ok": True, "errors": []}


def patch_graph_settings(state_dir: Path, patch: dict) -> dict:
    """Load current settings, deep-merge patch, and save. Returns {"ok": bool, "errors": list}."""
    current = load_graph_settings(state_dir)
    merged = _deep_merge(current, patch)
    return save_graph_settings(state_dir, merged)


def _migrate_legacy_settings(settings: dict) -> dict:
    migrated = dict(settings)
    edge_layers = migrated.get("edge_layers")
    if isinstance(edge_layers, dict):
        remapped: dict[str, dict] = {}
        for key, value in edge_layers.items():
            remapped[canonical_edge_layer(key)] = value
        migrated["edge_layers"] = remapped
    return migrated
