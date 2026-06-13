"""Read-only native Studio runtime intelligence panels.

These panels expose provenance, memory, identity, and runtime navigation state
inside Studio without granting mutation authority. Layer C/D memory remains
advisory and cannot override Gate, trust tiers, role cards, or source truth.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.memory.inspector import build_memory_summary, get_runtime_memory, list_runtime_memory
from runtime.studio.provenance import list_quarantine_provenance


MODEL_VERSION = "studio.runtime_intelligence_panels.v1"
NEXT_RECOMMENDED_PASS = "studio-real-desktop-packaging-readiness"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _common_authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "writes_vault": False,
        "writes_memory": False,
        "writes_provenance": False,
        "writes_identity_ledger": False,
        "writes_runtime_navigation_map": False,
        "writes_agent_bus_tasks": False,
        "updates_trust_tiers": False,
        "updates_permission_matrix": False,
        "approves_memory": False,
        "applies_memory_candidates": False,
        "updates_runtime_brain": False,
        "executes_workflows": False,
        "provider_calls_allowed": False,
        "connector_calls_allowed": False,
        "canonical_mutation_allowed": False,
        "shows_secrets": False,
        "shows_raw_credentials": False,
    }


def _native_panel(panel_id: str) -> dict[str, Any]:
    return {
        "mounted": True,
        "panel_id": panel_id,
        "frontend_target": f"panel-{panel_id}",
        "route_hint": f"#{panel_id}",
        "read_only": True,
        "status": "mounted-read-only",
    }


def _path_status(vault: Path, rel_path: str) -> dict[str, Any]:
    path = vault / rel_path
    result: dict[str, Any] = {
        "path": rel_path,
        "exists": path.exists(),
        "kind": "missing",
        "size_bytes": None,
        "modified_at_utc": None,
    }
    if not path.exists():
        return result
    try:
        stat = path.stat()
    except OSError as exc:
        result["kind"] = "inaccessible"
        result["error"] = str(exc)
        return result
    result["kind"] = "directory" if path.is_dir() else "file"
    result["size_bytes"] = stat.st_size if path.is_file() else None
    result["modified_at_utc"] = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
    return result


def _runtime_ids(vault: Path) -> list[str]:
    return [str(item.get("runtime_id")) for item in list_runtime_memory(vault) if item.get("runtime_id")]


def _limited_list(value: Any, limit: int = 5) -> list[Any]:
    if not isinstance(value, list):
        return []
    return value[:limit]


def _summarize_identity(runtime_id: str, bundle: dict[str, Any]) -> dict[str, Any]:
    identity = ((bundle.get("layer_c") or {}).get("identity_ledger") or {})
    summary = identity.get("identity_summary") or {}
    return {
        "runtime_id": runtime_id,
        "status": identity.get("status"),
        "updated_at": identity.get("updated_at"),
        "current_actor_posture": summary.get("current_actor_posture"),
        "identity_confidence": summary.get("identity_confidence"),
        "behavioral_tendency_count": len(identity.get("behavioral_tendencies") or []),
        "correction_count": len(identity.get("correction_history") or []),
        "drift_signal_count": len(identity.get("drift_signals") or []),
        "drift_signals": _limited_list(identity.get("drift_signals"), 4),
        "doctrine_adherence": identity.get("doctrine_adherence") or {},
        "governance_boundary": identity.get("governance_boundary"),
    }


def _summarize_navigation(runtime_id: str, bundle: dict[str, Any]) -> dict[str, Any]:
    navigation = ((bundle.get("layer_c") or {}).get("navigation") or {})
    return {
        "runtime_id": runtime_id,
        "status": navigation.get("status"),
        "updated": navigation.get("updated"),
        "preferred_read_route_count": len(navigation.get("preferred_read_routes") or []),
        "trusted_zone_count": len(navigation.get("trusted_zones") or []),
        "safe_write_path_count": len(navigation.get("safe_write_paths") or []),
        "risk_zone_count": len(navigation.get("risk_zones") or []),
        "escalation_point_count": len(navigation.get("escalation_points") or []),
        "preferred_read_routes": _limited_list(navigation.get("preferred_read_routes"), 4),
        "trusted_zones": _limited_list(navigation.get("trusted_zones"), 6),
        "risk_zones": _limited_list(navigation.get("risk_zones"), 6),
        "governance_boundary": navigation.get("governance_boundary")
        or "Runtime navigation maps are advisory routing aids and do not grant write authority.",
    }


def build_provenance_explorer_panel(vault_root: str | Path, *, limit: int = 20) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    provenance = list_quarantine_provenance(vault, limit=limit)
    records = list(provenance.get("results") or [])
    trust_counts = Counter(str(item.get("trust_state") or "unknown") for item in records)
    source_counts = Counter(str(item.get("source_platform") or "unknown") for item in records)
    authority = _common_authority()
    return {
        "ok": True,
        "surface": "studio_provenance_explorer_panel",
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "native_panel": _native_panel("provenance-explorer"),
        "summary": {
            "overall_status": "mounted-read-only",
            "record_count": len(records),
            "limit": limit,
            "trust_state_counts": dict(trust_counts),
            "source_platform_counts": dict(source_counts),
            "content_body_read": False,
        },
        "records": records,
        "source": {
            "quarantine_root": "03_INPUTS/00_QUARANTINE",
            "sidecar_only": True,
            "dedup_cross_reference_available": True,
            "content_body_read": False,
        },
        "authority": authority,
        "allowed_actions": ["inspect-provenance-explorer-panel"],
        "possible_writes": [],
        "readiness": {
            "provenance_explorer_panel_mounted": True,
            "sidecar_metadata_visible": True,
            "trust_state_visible": True,
            "no_content_body_read": True,
            "no_writeback": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "warnings": [] if provenance.get("ok") else [str(provenance.get("error") or "provenance_list_unavailable")],
    }


def build_memory_ledger_panel(vault_root: str | Path) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    summary = build_memory_summary(vault)
    authority = _common_authority()
    return {
        "ok": True,
        "surface": "studio_memory_ledger_panel",
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "native_panel": _native_panel("memory-ledger"),
        "summary": {
            "overall_status": summary.get("memory_posture"),
            "runtime_count": (summary.get("runtime_summary") or {}).get("runtime_count", 0),
            "active_task_context_count": (summary.get("task_summary") or {}).get("active_task_context_count", 0),
            "attention_count": len(summary.get("attention_items") or []),
            "validation_error_count": (summary.get("validation") or {}).get("error_count", 0),
        },
        "runtime_summary": summary.get("runtime_summary") or {},
        "task_summary": summary.get("task_summary") or {},
        "attention_items": summary.get("attention_items") or [],
        "governance": summary.get("governance") or {},
        "stores": {
            "adapters": "runtime/memory/adapters",
            "navigation": "runtime/memory/nav",
            "repair": "runtime/memory/repair",
            "scorecards": "runtime/memory/scorecards",
            "tasks": "runtime/tasks",
        },
        "authority": authority,
        "allowed_actions": ["inspect-memory-ledger-panel"],
        "possible_writes": [],
        "readiness": {
            "memory_ledger_panel_mounted": True,
            "memory_runtime_coverage_visible": True,
            "task_contexts_visible": True,
            "memory_approval_allowed": False,
            "memory_writeback_allowed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }


def build_agent_identity_panel(vault_root: str | Path) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    runtimes = []
    for runtime_id in _runtime_ids(vault):
        runtimes.append(_summarize_identity(runtime_id, get_runtime_memory(runtime_id, vault)))
    authority = _common_authority()
    return {
        "ok": True,
        "surface": "studio_agent_identity_panel",
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "native_panel": _native_panel("agent-identity"),
        "summary": {
            "overall_status": "mounted-read-only",
            "runtime_count": len(runtimes),
            "seeded_identity_count": sum(1 for item in runtimes if item.get("status") not in {None, "missing"}),
            "drift_signal_count": sum(int(item.get("drift_signal_count") or 0) for item in runtimes),
            "correction_count": sum(int(item.get("correction_count") or 0) for item in runtimes),
        },
        "identities": runtimes,
        "source": {
            "identity_ledger_root": "runtime/memory/adapters/*/identity-ledger.json",
            "runtime_profile_docs": "06_AGENTS/*-Runtime-Profile.md",
        },
        "authority": authority,
        "allowed_actions": ["inspect-agent-identity-panel"],
        "possible_writes": [],
        "readiness": {
            "agent_identity_panel_mounted": True,
            "identity_ledgers_visible": True,
            "drift_signals_visible": True,
            "trust_tier_mutation_allowed": False,
            "permission_mutation_allowed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }


def build_runtime_navigation_map_panel(vault_root: str | Path) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    maps = []
    for runtime_id in _runtime_ids(vault):
        bundle = get_runtime_memory(runtime_id, vault)
        item = _summarize_navigation(runtime_id, bundle)
        item["file"] = _path_status(vault, f"runtime/memory/nav/{runtime_id}/nav-map.json")
        maps.append(item)
    authority = _common_authority()
    return {
        "ok": True,
        "surface": "studio_runtime_navigation_map_panel",
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "native_panel": _native_panel("runtime-navigation"),
        "summary": {
            "overall_status": "mounted-read-only",
            "runtime_count": len(maps),
            "navigation_map_count": sum(1 for item in maps if ((item.get("file") or {}).get("exists"))),
            "preferred_read_route_count": sum(int(item.get("preferred_read_route_count") or 0) for item in maps),
            "risk_zone_count": sum(int(item.get("risk_zone_count") or 0) for item in maps),
            "escalation_point_count": sum(int(item.get("escalation_point_count") or 0) for item in maps),
        },
        "runtime_navigation_maps": maps,
        "source": {
            "navigation_root": "runtime/memory/nav/*/nav-map.json",
            "folder_guide": "runtime/memory/nav/Runtime-Navigation-Folder-Guide.md",
        },
        "authority": authority,
        "allowed_actions": ["inspect-runtime-navigation-map-panel"],
        "possible_writes": [],
        "readiness": {
            "runtime_navigation_map_panel_mounted": True,
            "navigation_maps_visible": True,
            "risk_zones_visible": True,
            "safe_write_paths_visible": True,
            "runtime_navigation_writeback_allowed": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }


def build_runtime_intelligence_panels(vault_root: str | Path) -> dict[str, Any]:
    vault = _vault_path(vault_root)
    panels = {
        "provenance_explorer": build_provenance_explorer_panel(vault),
        "memory_ledger": build_memory_ledger_panel(vault),
        "agent_identity": build_agent_identity_panel(vault),
        "runtime_navigation": build_runtime_navigation_map_panel(vault),
    }
    return {
        "ok": all(bool(panel.get("ok")) for panel in panels.values()),
        "surface": "studio_runtime_intelligence_panels",
        "model_version": MODEL_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "panels": panels,
        "authority": _common_authority(),
        "allowed_actions": [
            "inspect-provenance-explorer-panel",
            "inspect-memory-ledger-panel",
            "inspect-agent-identity-panel",
            "inspect-runtime-navigation-map-panel",
        ],
        "possible_writes": [],
        "readiness": {
            "runtime_intelligence_panels_mounted": True,
            "provenance_explorer_mounted": True,
            "memory_ledger_mounted": True,
            "agent_identity_mounted": True,
            "runtime_navigation_mounted": True,
            "no_memory_writeback": True,
            "no_identity_trust_mutation": True,
            "no_runtime_navigation_writeback": True,
            "no_canonical_mutation": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }
