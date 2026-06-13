"""
brain_bootstrap.py — ChaseOS Brain Bootstrap Sequence

Seeds empty runtime-specific Layer C memory surfaces on first registration
so that all inspection commands work from day one.

Called by cmd_agent_register() after register_runtime() writes the registry
entry. Safe to call multiple times — existing seed files are never overwritten
(idempotent by design).

Seeds written (all stubs with status "bootstrap-seeded"):
  runtime/memory/adapters/<runtime_id>/profile.json        — Layer C behavioral profile
  runtime/memory/adapters/<runtime_id>/identity-ledger.json — agent identity record
  runtime/memory/nav/<runtime_id>/nav-map.json             — navigation routing hints

No permissions are pre-granted. Seeds cannot raise trust tier, bypass Gate,
or expand allowed task families. All surfaces are inspectable via:
  chaseos memory show <runtime_id>
  chaseos memory ledger <runtime_id>
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from datetime import datetime, timezone


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_seed(path: Path, content: dict) -> bool:
    """Write seed JSON; return True if written, False if already exists (skipped)."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")
    return True


def _profile_seed(runtime_id: str) -> dict:
    return {
        "schema_version": "1.0",
        "layer": "C",
        "memory_family": "runtime_behavior_profile",
        "runtime_id": runtime_id,
        "status": "bootstrap-seeded",
        "updated_at": _utc_now(),
        "sources": [],
        "behavioral_profile": {
            "primary_role": f"Newly registered runtime: {runtime_id}",
            "strengths": [],
            "known_failure_modes": [],
            "routing_guidance": [
                "orient through adapter docs and ChaseOS-CLI-Command-Reference.md before acting",
                "escalate protected-file writes, canonical-promotion, and undeclared capability expansion",
            ],
            "confidence_signals": [],
        },
        "governance_boundary": (
            "Layer C memory is advisory and cannot override Gate, role cards, "
            "workflow manifests, or operator approval."
        ),
    }


def _identity_ledger_seed(runtime_id: str) -> dict:
    return {
        "schema_version": "1.0",
        "layer": "C",
        "memory_family": "agent_identity_ledger",
        "runtime_id": runtime_id,
        "status": "bootstrap-seeded",
        "updated_at": _utc_now(),
        "identity_summary": {
            "current_actor_posture": (
                f"{runtime_id} is a newly declared runtime. No execution history yet. "
                "Trust tier, allowed task families, and behavioral tendencies will accumulate "
                "through AOR execution and operator review."
            ),
            "execution_surface": "unknown — populate from adapter docs after registration",
            "trust_tier": "tier-4 (default; upgrade requires Decision Ledger entry)",
            "identity_confidence": "bootstrap-seeded",
            "summary_boundary": (
                "This is a behavioral identity summary, not permission authority. "
                "Gate, role cards, adapter manifests, workflow manifests, and "
                "operator approvals remain authoritative."
            ),
        },
        "behavioral_tendencies": [],
        "doctrine_adherence": {
            "status": "unobserved",
            "notes": "No AOR execution history. Will populate after first governed run.",
        },
        "correction_history": [],
        "drift_signals": [],
        "authority_boundaries": {
            "trust_ceiling": "tier-4",
            "write_scope": "declared manifest writeback_targets only",
            "forbidden_actions": [
                "write to protected files",
                "bypass Gate or approval gate",
                "auto-promote trust tier",
                "expand task families without Decision Ledger entry",
            ],
        },
        "promotion_rules": {
            "scorecard_ref": None,
            "minimum_executions": 10,
            "minimum_compliance_rate": 0.95,
            "requires_operator_acceptance": True,
        },
        "governance_boundary": (
            "Layer C memory is advisory only. Cannot raise trust tier, bypass Gate, "
            "or override operator approval."
        ),
    }


def _nav_map_seed(runtime_id: str) -> dict:
    return {
        "runtime_id": runtime_id,
        "version": "0.1",
        "status": "bootstrap-seeded",
        "updated": _utc_now()[:10],
        "preferred_read_routes": [
            {
                "task_class": "initial-orientation",
                "route": [
                    "CLAUDE.md",
                    "06_AGENTS/Vault-Map.md",
                    "06_AGENTS/ChaseOS-CLI-Command-Reference.md",
                ],
                "notes": (
                    "Default bootstrap route. Replace with runtime-specific adapter docs "
                    "after governance onboarding."
                ),
            }
        ],
        "trusted_zones": [
            "runtime/aor/",
            "runtime/workflows/registry/",
            "06_AGENTS/",
            "07_LOGS/Build-Logs/",
        ],
        "risk_zones": [
            "SOUL.md",
            "00_HOME/Principles.md",
            "00_HOME/Assistant-Contract.md",
            "06_AGENTS/Permission-Matrix.md",
        ],
        "governance_boundary": (
            "Navigation map is advisory. Preferred routes do not grant read permissions "
            "beyond what the role card write_scope and Gate policy allow."
        ),
    }


def run_brain_bootstrap(
    runtime_id: str,
    *,
    vault_root: Optional[Path] = None,
) -> dict[str, Any]:
    """
    Seed Layer C memory surfaces for a newly registered runtime.

    Parameters
    ----------
    runtime_id : str
        The runtime ID from register_runtime() (e.g. "openclaw", "hermes").
    vault_root : Path, optional
        Vault root path. Auto-detected from file location if not provided.

    Returns
    -------
    dict with keys:
        runtime_id       — echoed
        seeds_written    — list of relative paths written
        seeds_skipped    — list of relative paths skipped (already existed)
        ok               — True always (bootstrap failure must never block registration)
    """
    if vault_root is None:
        here = Path(__file__).resolve()
        vault_root = here.parents[2]

    seeds_written: list[str] = []
    seeds_skipped: list[str] = []

    _seeds: list[tuple[Path, dict]] = [
        (
            vault_root / "runtime" / "memory" / "adapters" / runtime_id / "profile.json",
            _profile_seed(runtime_id),
        ),
        (
            vault_root / "runtime" / "memory" / "adapters" / runtime_id / "identity-ledger.json",
            _identity_ledger_seed(runtime_id),
        ),
        (
            vault_root / "runtime" / "memory" / "nav" / runtime_id / "nav-map.json",
            _nav_map_seed(runtime_id),
        ),
    ]

    for path, content in _seeds:
        rel = str(path.relative_to(vault_root)).replace("\\", "/")
        try:
            written = _write_seed(path, content)
        except Exception:  # noqa: BLE001
            written = False
        if written:
            seeds_written.append(rel)
        else:
            seeds_skipped.append(rel)

    return {
        "runtime_id": runtime_id,
        "seeds_written": seeds_written,
        "seeds_skipped": seeds_skipped,
        "ok": True,
    }
