"""ChaseOS Studio graph preset management.

Built-in presets are read-only workspace recipes. User presets are stored under
the Studio user state directory, not inside the opened vault.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

PRESET_VERSION = "studio.graph.preset.v1"
_PRESETS_SUBDIR = "graph-presets"
_PRESET_SUFFIX = ".json"
_SAFE_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}[a-z0-9]$|^[a-z0-9]$")


def _preset(
    preset_id: str,
    label: str,
    description: str,
    *,
    filters: dict | None = None,
    layout: dict | None = None,
    settings_patch: dict | None = None,
    visible_panels: list[str] | None = None,
    focus_mode: dict | None = None,
    legend_state: dict | None = None,
) -> dict:
    return {
        "schema_version": PRESET_VERSION,
        "id": preset_id,
        "label": label,
        "description": description,
        "builtin": True,
        "filters": filters or {},
        "layout": layout or {},
        "node_style_overrides": {},
        "edge_style_overrides": {},
        "visible_panels": visible_panels or ["graph", "inspector", "filters", "legend"],
        "focus_mode": focus_mode or {},
        "legend_state": legend_state or {"expanded": True},
        "settings_patch": settings_patch or {},
    }


BUILTIN_PRESETS: dict[str, dict] = {
    "knowledge-map": _preset(
        "knowledge-map",
        "Knowledge Map",
        "Durable knowledge, sources, synthesis, projects, and domains.",
        filters={
            "node_families": ["knowledge", "source", "synthesis", "project", "domain"],
            "edge_layers": ["explicit", "structural"],
        },
        layout={"cluster_by_domain": True},
        settings_patch={
            "node_families": {
                family: {"visible": False}
                for family in ["intake", "generated_artifact", "log_audit", "runtime", "agent", "workflow", "decision"]
            },
            "node_scope": {"show_entity_objects": False, "show_unresolved_links": False},
            "edge_layers": {"suggested_semantic": {"visible": False}, "runtime_action": {"visible": False}},
        },
    ),
    "project-cockpit": _preset(
        "project-cockpit",
        "Project Cockpit",
        "Selected project neighborhood with project, domain, workflow, decision, and runtime context.",
        filters={
            "node_families": ["project", "domain", "workflow", "decision", "agent", "runtime"],
            "edge_layers": ["explicit", "structural", "runtime_action"],
        },
        layout={"local_graph_depth": 2, "cluster_by_project": True},
        focus_mode={"local_depth": 2},
        settings_patch={
            "node_families": {
                family: {"visible": False}
                for family in ["knowledge", "source", "synthesis", "intake", "generated_artifact", "log_audit", "entity_object"]
            },
            "node_scope": {"show_entity_objects": False, "show_unresolved_links": False},
        },
    ),
    "runtime-map": _preset(
        "runtime-map",
        "Runtime Map",
        "Operational graph for workflows, agents, runtimes, logs, decisions, and approvals.",
        filters={
            "node_families": ["workflow", "agent", "runtime", "log_audit", "decision"],
            "edge_layers": ["runtime_action", "structural"],
        },
        layout={"cluster_by_project": True},
        settings_patch={
            "node_families": {
                family: {"visible": False}
                for family in ["knowledge", "source", "synthesis", "sop_template", "domain", "entity_object"]
            },
            "edge_layers": {"suggested_semantic": {"visible": False}},
        },
    ),
    "intake-review": _preset(
        "intake-review",
        "Intake Review",
        "Raw, quarantined, suggested, and disputed material requiring review.",
        filters={
            "node_families": ["intake", "source", "synthesis"],
            "trust_states": ["raw", "quarantined", "suggested", "disputed"],
            "edge_layers": ["explicit", "structural", "suggested_semantic"],
        },
        layout={"cluster_by_trust_state": True},
        settings_patch={
            "node_families": {
                family: {"visible": False}
                for family in ["knowledge", "project", "domain", "sop_template", "workflow", "agent", "runtime", "decision", "log_audit"]
            },
            "edge_layers": {"runtime_action": {"visible": False}},
        },
    ),
    "generated-ideas": _preset(
        "generated-ideas",
        "Generated Ideas",
        "AI-origin proposals and generated artifacts separated from canonical truth.",
        filters={
            "node_families": ["generated_artifact", "synthesis", "decision"],
            "trust_states": ["generated", "suggested", "promoted"],
        },
        layout={"cluster_by_trust_state": True},
        settings_patch={
            "node_families": {
                family: {"visible": False}
                for family in ["knowledge", "source", "project", "domain", "sop_template", "workflow", "agent", "runtime", "log_audit", "entity_object"]
            },
        },
    ),
    "personal-map": _preset(
        "personal-map",
        "Personal Map",
        "Entity objects, projects, domains, knowledge, tools, people, accounts, and resources.",
        filters={
            "node_families": ["entity_object", "project", "domain", "knowledge"],
            "edge_layers": ["explicit", "structural"],
        },
        layout={"cluster_by_domain": True},
        settings_patch={
            "node_families": {
                family: {"visible": False}
                for family in ["intake", "generated_artifact", "log_audit", "workflow", "agent", "runtime", "decision"]
            },
            "edge_layers": {"suggested_semantic": {"visible": False}, "runtime_action": {"visible": False}},
        },
    ),
    "local-neighborhood": _preset(
        "local-neighborhood",
        "Local Neighborhood",
        "Focused local graph view with depth and radius controls.",
        filters={},
        layout={"local_graph_depth": 2, "focus_radius": 2},
        focus_mode={"local_depth": 2},
        legend_state={"expanded": False},
        settings_patch={"layout": {"local_graph_depth": 2, "focus_radius": 2}},
    ),
    "full-graph": _preset(
        "full-graph",
        "Debug / Full Graph",
        "All node families and edge layers visible with debug inspector available.",
        filters={},
        visible_panels=["graph", "inspector", "filters", "legend", "debug"],
    ),
}


def _valid_slug(slug: str) -> bool:
    return bool(_SAFE_SLUG_RE.match(slug)) and not slug.startswith("builtin-")


def _presets_dir(state_dir: Path) -> Path:
    return state_dir / _PRESETS_SUBDIR


def _preset_path(state_dir: Path, slug: str) -> Path:
    return _presets_dir(state_dir) / f"{slug}{_PRESET_SUFFIX}"


def list_presets(state_dir: Path) -> list[dict]:
    """Return built-ins first, then user presets sorted by filename."""
    result = [dict(p) for p in BUILTIN_PRESETS.values()]
    presets_dir = _presets_dir(state_dir)
    if presets_dir.is_dir():
        for path in sorted(presets_dir.glob(f"*{_PRESET_SUFFIX}")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    raw["builtin"] = False
                    result.append(raw)
            except (json.JSONDecodeError, OSError):
                pass
    return result


def get_preset(state_dir: Path, preset_id: str) -> dict | None:
    if preset_id in BUILTIN_PRESETS:
        return dict(BUILTIN_PRESETS[preset_id])
    path = _preset_path(state_dir, preset_id)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw["builtin"] = False
            return raw
    except (json.JSONDecodeError, OSError):
        pass
    return None


def save_preset(
    state_dir: Path,
    slug: str,
    label: str,
    description: str,
    settings_patch: dict,
    filters: dict | None = None,
) -> dict:
    if not _valid_slug(slug):
        return {"ok": False, "errors": [
            f"invalid preset slug {slug!r}. Must match [a-z0-9][a-z0-9_-]{{0,62}}[a-z0-9] and not start with 'builtin-'."
        ]}
    if slug in BUILTIN_PRESETS:
        return {"ok": False, "errors": [f"cannot overwrite built-in preset: {slug!r}"]}
    if not label or not isinstance(label, str):
        return {"ok": False, "errors": ["label must be a non-empty string"]}
    if not isinstance(settings_patch, dict):
        return {"ok": False, "errors": ["settings_patch must be a dict"]}
    if filters is not None and not isinstance(filters, dict):
        return {"ok": False, "errors": ["filters must be a dict"]}

    preset = {
        "schema_version": PRESET_VERSION,
        "id": slug,
        "label": label[:80],
        "description": (description or "")[:256],
        "builtin": False,
        "filters": filters or {},
        "layout": {},
        "node_style_overrides": {},
        "edge_style_overrides": {},
        "visible_panels": ["graph", "inspector", "filters", "legend"],
        "focus_mode": {},
        "legend_state": {"expanded": True},
        "settings_patch": settings_patch,
    }

    presets_dir = _presets_dir(state_dir)
    presets_dir.mkdir(parents=True, exist_ok=True)
    target = _preset_path(state_dir, slug)
    try:
        fd, tmp = tempfile.mkstemp(dir=presets_dir, suffix=".tmp", prefix=f".{slug}-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(preset, fh, indent=2, ensure_ascii=False)
            os.replace(tmp, target)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except OSError as exc:
        return {"ok": False, "errors": [f"write failed: {exc}"]}
    return {"ok": True, "errors": []}


def delete_preset(state_dir: Path, slug: str) -> dict:
    if slug in BUILTIN_PRESETS:
        return {"ok": False, "errors": [f"cannot delete built-in preset: {slug!r}"]}
    path = _preset_path(state_dir, slug)
    if not path.exists():
        return {"ok": False, "errors": [f"preset not found: {slug!r}"]}
    try:
        path.unlink()
    except OSError as exc:
        return {"ok": False, "errors": [f"delete failed: {exc}"]}
    return {"ok": True, "errors": []}
