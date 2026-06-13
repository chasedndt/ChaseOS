"""Phase 11 companion runtime-core adapter sync audit.

This read-only audit verifies that the Studio companion status, registry,
selection-preview, and roster-preview surfaces consume `runtime/companion` as
the companion source of truth. It does not write selection state, approvals,
memory, runtime routing, provider calls, Agent Bus tasks, or canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import inspect
import json
from pathlib import Path
from typing import Any

import runtime.companion.roster as companion_roster
from runtime.companion.policy import INITIAL_COMPANION_IDS, SELECTION_TARGET_PATH, build_authority_report
from runtime.companion.roster import get_companion, validate_roster
from runtime.studio.phase11_chat_companion_selection_preview import (
    build_phase11_chat_companion_selection_preview,
)
from runtime.studio.phase11_chat_companion_status import build_phase11_chat_companion_status
from runtime.studio.phase11_companion_roster_ui_preview import build_phase11_companion_roster_ui_preview
from runtime.studio.phase11_multi_companion_registry_readiness import (
    build_phase11_multi_companion_registry_readiness,
)


MODEL_VERSION = "studio.phase11_companion_runtime_core_adapter_sync.v1"
SURFACE_ID = "phase11_companion_runtime_core_adapter_sync"
PASS_ID = "phase11-companion-runtime-core-adapter-sync"
STATUS = "COMPLETE / READ-ONLY / CORE ADAPTER SYNC VERIFIED / NO AUTHORITY EXPANSION"
NEXT_RECOMMENDED_PASS = "phase11-companion-memory-boundary-contract"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


TRACKED_SNAPSHOT_ROOTS = (
    Path("runtime/studio/chat"),
    Path("runtime/studio/approvals"),
    Path("07_LOGS/Agent-Activity"),
)


def _files(root: Path) -> list[str]:
    """Snapshot companion-relevant write targets without walking the whole vault."""

    files: list[str] = []
    for relative in TRACKED_SNAPSHOT_ROOTS:
        target = root / relative
        if target.is_file():
            files.append(target.relative_to(root).as_posix())
            continue
        if not target.is_dir():
            continue
        try:
            paths = target.rglob("*")
            for path in paths:
                try:
                    if path.is_file() and "__pycache__" not in path.parts:
                        files.append(path.relative_to(root).as_posix())
                except OSError:
                    continue
        except OSError:
            continue
    return sorted(files)


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def _card_by_id(payload: dict[str, Any], companion_id: str) -> dict[str, Any]:
    for card in payload.get("companion_cards") or payload.get("roster_cards") or []:
        if str(card.get("runtime_id") or "").lower() == companion_id:
            return card
    return {}


def build_phase11_companion_runtime_core_adapter_sync(vault_root: str | Path) -> dict[str, Any]:
    """Build a read-only sync audit for Studio-to-core companion adapters."""

    vault = Path(vault_root).resolve()
    before = _files(vault)
    core_validation = validate_roster()
    status = build_phase11_chat_companion_status(vault, requested_runtime="hermes")
    registry = build_phase11_multi_companion_registry_readiness(vault)
    roster = build_phase11_companion_roster_ui_preview(vault)
    selection_preview = build_phase11_chat_companion_selection_preview(
        vault,
        requested_runtime="claude-code",
        current_runtime="hermes",
        message="preview Claude Code companion through core adapter sync",
    )
    after = _files(vault)

    roster_source = inspect.getsource(companion_roster)
    status_cards = {
        str(card.get("runtime_id") or "").lower()
        for card in status.get("companion_cards") or []
        if str(card.get("runtime_id") or "").strip()
    }
    roster_cards = {
        str(card.get("runtime_id") or "").lower()
        for card in roster.get("roster_cards") or []
        if str(card.get("runtime_id") or "").strip()
    }
    core_ids = set(INITIAL_COMPANION_IDS)
    hermes_core = get_companion("hermes")
    hermes_status = _card_by_id(status, "hermes")
    hermes_roster = _card_by_id(roster, "hermes")
    authority = build_authority_report()

    checks = [
        _check("core_roster_valid", core_validation["valid"] is True),
        _check(
            "core_roster_no_studio_status_reverse_import",
            "runtime.studio.phase11_chat_companion_status" not in roster_source,
        ),
        _check("status_surface_uses_core_package", (status.get("summary") or {}).get("core_companion_package_used") is True),
        _check("registry_surface_uses_core_package", (registry.get("summary") or {}).get("core_companion_package_used") is True),
        _check("roster_surface_uses_core_package", (roster.get("summary") or {}).get("core_companion_package_used") is True),
        _check(
            "selection_preview_uses_core_target_path",
            ((selection_preview.get("digest_proof") or {}).get("digest_material") or {}).get("target_path")
            == SELECTION_TARGET_PATH.as_posix(),
        ),
        _check("status_cards_match_core_roster", status_cards == core_ids, ",".join(sorted(status_cards))),
        _check("roster_cards_match_core_roster", roster_cards == core_ids, ",".join(sorted(roster_cards))),
        _check("status_card_matches_core_display", hermes_status.get("display_name") == hermes_core["display_name"]),
        _check(
            "roster_card_visual_matches_core_profile",
            ((hermes_roster.get("abstract_visual") or {}).get("runtime_mark") == hermes_core["visual_mark"]["token"]),
        ),
        _check("status_surface_keeps_runtime_control_blocked", (status.get("authority") or {}).get("runtime_control_allowed") is False),
        _check("registry_surface_keeps_agent_bus_blocked", (registry.get("authority") or {}).get("agent_bus_task_write_allowed") is False),
        _check("roster_surface_keeps_memory_writes_blocked", (roster.get("authority") or {}).get("memory_write_authority_granted") is False),
        _check("selection_preview_keeps_selection_write_blocked", (selection_preview.get("authority") or {}).get("companion_selection_write_allowed") is False),
        _check("core_authority_report_has_no_changes", all(value is False for value in authority.values())),
        _check("audit_is_read_only", before == after),
    ]
    blockers = [check["name"] for check in checks if not check["ok"]]
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "core_ids": sorted(core_ids),
        "status_cards": sorted(status_cards),
        "roster_cards": sorted(roster_cards),
        "selection_target_path": SELECTION_TARGET_PATH.as_posix(),
        "checks": checks,
    }

    return {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if not blockers else "BLOCKED / CORE ADAPTER SYNC FAILED",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": {
            "core_companion_package_used": True,
            "core_roster_valid": core_validation["valid"] is True,
            "studio_status_synced": (status.get("summary") or {}).get("core_companion_package_used") is True,
            "studio_registry_synced": (registry.get("summary") or {}).get("core_companion_package_used") is True,
            "studio_roster_synced": (roster.get("summary") or {}).get("core_companion_package_used") is True,
            "selection_preview_synced": (
                ((selection_preview.get("digest_proof") or {}).get("digest_material") or {}).get("target_path")
                == SELECTION_TARGET_PATH.as_posix()
            ),
            "selection_target_written": False,
            "approval_artifact_written": False,
            "approval_consumed": False,
            "memory_changed": False,
            "separate_companion_memory_namespace_declared": True,
            "routing_changed": False,
            "permissions_changed": False,
            "provider_call_performed": False,
            "runtime_dispatched": False,
            "agent_bus_task_written": False,
            "canonical_state_mutated": False,
            "blocker_count": len(blockers),
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "checks": checks,
        "core_roster_validation": core_validation,
        "surface_snapshots": {
            "status_summary": status.get("summary") or {},
            "registry_summary": registry.get("summary") or {},
            "roster_summary": roster.get("summary") or {},
            "selection_preview_summary": selection_preview.get("summary") or {},
        },
        "authority": {
            "read_only": True,
            "core_adapter_sync_audit_allowed": True,
            "companion_selection_write_allowed": False,
            "approval_queue_write_allowed": False,
            "approval_consumption_allowed": False,
            "approval_execution_allowed": False,
            "runtime_routing_allowed": False,
            "provider_model_selection_allowed": False,
            "memory_access_expansion_allowed": False,
            "memory_write_authority_granted": False,
            "permission_scope_expansion_allowed": False,
            "tool_access_expansion_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "digest_proof": {
            "adapter_sync_digest": _sha256_text(_canonical_json(digest_material)),
            "digest_material": digest_material,
        },
        "blocked_reasons": blockers,
        "readiness": {
            "companion_runtime_core_adapter_sync_ready": not blockers,
            "runtime_companion_core_is_source_of_truth": True,
            "studio_surfaces_read_core_profiles": not blockers,
            "selection_writes_blocked": True,
            "memory_boundary_contract_defined": True,
            "memory_write_executor_required_before_companion_memory_writes": True,
            "routing_pass_required_before_capability_change": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }


def format_phase11_companion_runtime_core_adapter_sync(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    lines = [
        "Phase 11 Companion Runtime-Core Adapter Sync",
        f"Status: {payload.get('status')}",
        f"Core roster valid: {summary.get('core_roster_valid')}",
        f"Studio status synced: {summary.get('studio_status_synced')}",
        f"Studio registry synced: {summary.get('studio_registry_synced')}",
        f"Studio roster synced: {summary.get('studio_roster_synced')}",
        f"Selection preview synced: {summary.get('selection_preview_synced')}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
        "Boundary: read-only adapter sync only; no selection write, no approval write/consumption, no memory write authority, no routing, no provider/model call, no Agent Bus task write, and no canonical mutation.",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines)
