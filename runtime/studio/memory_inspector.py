"""
studio/memory_inspector.py — Studio Memory Inspector

Read-only surface for inspecting per-runtime ChaseOS memory state:
  - behavioral profile (goals, domains, interaction style)
  - identity ledger (correction history, drift signals, doctrine adherence)
  - nav-map (successful routes, escalation triggers)
  - scorecard (aggregate execution stats)
  - repair patterns (recent incident candidates)

Governance:
  - Read-only: no memory file mutations
  - Nav-map and repair patterns contain execution history — never modify via Studio
  - Scorecard data is advisory; not used for authorization decisions
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_BOUNDARY = {
    "reads_memory_files": True,
    "writes_memory_files": False,
    "writes_vault": False,
    "canonical_mutation_allowed": False,
}

_MEMORY_ROOT = "runtime/memory"
_ADAPTERS_DIR = "runtime/memory/adapters"
_NAV_DIR = "runtime/memory/nav"
_SCORECARDS_DIR = "runtime/memory/scorecards"
_REPAIR_DIR = "runtime/memory/repair"


def _load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _summarize_profile(profile: dict) -> dict[str, Any]:
    bp = profile.get("behavioral_profile", {})
    return {
        "runtime_id": profile.get("runtime_id"),
        "runtime_label": profile.get("runtime_label"),
        "status": profile.get("status"),
        "updated_at": profile.get("updated_at"),
        "primary_goals": bp.get("primary_goals", []),
        "domain_focus": bp.get("domain_focus", []),
        "interaction_style": bp.get("interaction_style"),
        "governance_boundary": profile.get("governance_boundary", {}),
    }


def _summarize_ledger(ledger: dict) -> dict[str, Any]:
    return {
        "runtime_id": ledger.get("runtime_id"),
        "status": ledger.get("status"),
        "updated_at": ledger.get("updated_at"),
        "identity_summary": ledger.get("identity_summary"),
        "correction_count": len(ledger.get("correction_history", [])),
        "drift_signals": ledger.get("drift_signals", []),
        "doctrine_adherence": ledger.get("doctrine_adherence", {}),
        "authority_boundaries": ledger.get("authority_boundaries", {}),
    }


def _summarize_nav_map(nav_map: dict) -> dict[str, Any]:
    return {
        "runtime_id": nav_map.get("runtime_id"),
        "updated_at": nav_map.get("updated_at"),
        "route_pattern_count": len(nav_map.get("successful_route_patterns", [])),
        "escalation_trigger_count": len(nav_map.get("common_escalation_triggers", [])),
        "successful_route_patterns": nav_map.get("successful_route_patterns", [])[:5],
        "common_escalation_triggers": nav_map.get("common_escalation_triggers", [])[:5],
    }


def _summarize_scorecard(scorecard: dict) -> dict[str, Any]:
    agg = scorecard.get("aggregate_stats", {})
    return {
        "runtime_id": scorecard.get("runtime_id"),
        "status": scorecard.get("status"),
        "last_updated": scorecard.get("last_updated"),
        "total_executions": agg.get("total_executions", 0),
        "success_rate": agg.get("success_rate"),
        "avg_duration_seconds": agg.get("avg_duration_seconds"),
        "escalation_rate": agg.get("escalation_rate"),
        "recent_executions": scorecard.get("executions", [])[-5:],
    }


def _summarize_repair(repair: dict) -> dict[str, Any]:
    candidates = repair.get("candidates") or repair.get("incident_candidates") or []
    patterns = repair.get("patterns") or repair.get("repair_patterns") or []
    return {
        "candidate_count": len(candidates),
        "pattern_count": len(patterns),
        "recent_candidates": candidates[-3:] if candidates else [],
        "recent_patterns": patterns[-3:] if patterns else [],
    }


# ── Public API ────────────────────────────────────────────────────────────────

def list_registered_runtimes(vault_root: str | Path) -> dict[str, Any]:
    """
    List all registered runtimes with their memory file presence flags.
    """
    vault = Path(vault_root).resolve()
    adapters_dir = vault / _ADAPTERS_DIR
    nav_dir = vault / _NAV_DIR
    scorecards_dir = vault / _SCORECARDS_DIR
    repair_dir = vault / _REPAIR_DIR

    if not adapters_dir.exists():
        return {
            "ok": True,
            "surface": "studio_memory_runtime_list",
            "runtimes": [],
            "runtime_count": 0,
            "boundary": _BOUNDARY,
        }

    runtimes = []
    for d in sorted(adapters_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        runtime_id = d.name
        runtimes.append({
            "runtime_id": runtime_id,
            "has_profile": (d / "profile.json").exists(),
            "has_identity_ledger": (d / "identity-ledger.json").exists(),
            "has_nav_map": (d / "nav-map.json").exists() or (nav_dir / runtime_id / "nav-map.json").exists(),
            "has_scorecard": (scorecards_dir / f"{runtime_id}.json").exists(),
            "has_repair": (repair_dir / f"{runtime_id}.json").exists(),
        })

    return {
        "ok": True,
        "surface": "studio_memory_runtime_list",
        "runtimes": runtimes,
        "runtime_count": len(runtimes),
        "boundary": _BOUNDARY,
    }


def inspect_runtime_memory(
    vault_root: str | Path,
    runtime_id: str,
) -> dict[str, Any]:
    """
    Return a structured memory inspection model for a single runtime.

    Includes profile summary, identity ledger summary, nav-map summary,
    scorecard summary, and repair pattern summary. Missing files return
    None for that section (not an error).
    """
    vault = Path(vault_root).resolve()
    adapter_dir = vault / _ADAPTERS_DIR / runtime_id

    if not adapter_dir.exists():
        return {
            "ok": False,
            "error": f"Runtime '{runtime_id}' not found in memory adapters.",
            "surface": "studio_memory_inspector",
            "runtime_id": runtime_id,
            "boundary": _BOUNDARY,
        }

    # Load all memory files
    profile_raw = _load_json(adapter_dir / "profile.json")
    ledger_raw = _load_json(adapter_dir / "identity-ledger.json")
    nav_map_raw = _load_json(adapter_dir / "nav-map.json") or _load_json(
        vault / _NAV_DIR / runtime_id / "nav-map.json"
    )
    scorecard_raw = _load_json(vault / _SCORECARDS_DIR / f"{runtime_id}.json")
    repair_raw = _load_json(vault / _REPAIR_DIR / f"{runtime_id}.json")

    return {
        "ok": True,
        "surface": "studio_memory_inspector",
        "runtime_id": runtime_id,
        "profile": _summarize_profile(profile_raw) if profile_raw else None,
        "identity_ledger": _summarize_ledger(ledger_raw) if ledger_raw else None,
        "nav_map": _summarize_nav_map(nav_map_raw) if nav_map_raw else None,
        "scorecard": _summarize_scorecard(scorecard_raw) if scorecard_raw else None,
        "repair": _summarize_repair(repair_raw) if repair_raw else None,
        "files_present": {
            "profile": profile_raw is not None,
            "identity_ledger": ledger_raw is not None,
            "nav_map": nav_map_raw is not None,
            "scorecard": scorecard_raw is not None,
            "repair": repair_raw is not None,
        },
        "boundary": _BOUNDARY,
    }
