"""Approval-gated companion selection for ChaseOS Companion Layer v0.1."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.companion.policy import (
    ALLOWED_EFFECTS,
    DEFAULT_COMPANION_ID,
    FORBIDDEN_EFFECTS,
    PLANNED_COMPANION_IDS,
    SELECTION_TARGET_PATH,
    SWITCH_LEDGER_PATH,
    assert_v0_1_no_authority_change,
    build_authority_report,
)
from runtime.companion.roster import get_companion


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_rel(vault: Path, relative: Path) -> Path:
    target = (vault / relative).resolve()
    if not str(target).startswith(str(vault.resolve())):
        raise ValueError(f"refusing path outside vault: {relative}")
    return target


def _load_selection(vault: Path) -> dict[str, Any] | None:
    target = _safe_rel(vault, SELECTION_TARGET_PATH)
    if not target.is_file():
        return None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def get_active_companion(vault_root: str | Path, *, session_id: str = "default") -> dict[str, Any]:
    """Return active companion state, defaulting to Hermes when no target exists."""

    vault = Path(vault_root).resolve()
    payload = _load_selection(vault)
    selected = str((payload or {}).get("selected_companion_id") or (payload or {}).get("selected_runtime_id") or "").lower()
    if not selected:
        selected = DEFAULT_COMPANION_ID
    try:
        profile = get_companion(selected)
    except ValueError:
        selected = DEFAULT_COMPANION_ID
        profile = get_companion(DEFAULT_COMPANION_ID)
    return {
        "ok": True,
        "selected_companion_id": selected,
        "session_id": str((payload or {}).get("session_id") or session_id),
        "selection_file_present": payload is not None,
        "selection_target_path": SELECTION_TARGET_PATH.as_posix(),
        "profile": profile,
        "authority": build_authority_report(),
    }


def preview_companion_switch(
    vault_root: str | Path,
    target_id: str,
    *,
    session_id: str = "default",
    current_id: str | None = None,
) -> dict[str, Any]:
    """Preview a switch without mutating active selection or ledger state."""

    vault = Path(vault_root).resolve()
    normalized = str(target_id or "").strip().lower()
    try:
        target = get_companion(normalized)
    except ValueError:
        return {
            "ok": False,
            "read_only": True,
            "selection_written": False,
            "ledger_written": False,
            "blocked_reasons": ["invalid_companion_id"],
        }
    if normalized in PLANNED_COMPANION_IDS or str(target.get("current_status") or "").lower() != "available":
        return {
            "ok": False,
            "read_only": True,
            "selection_written": False,
            "ledger_written": False,
            "blocked_reasons": ["companion_unavailable"],
            "target_profile": target,
        }
    active = get_active_companion(vault, session_id=session_id)
    previous = str(current_id or active["selected_companion_id"]).strip().lower() or DEFAULT_COMPANION_ID
    material = {
        "previous_companion": previous,
        "new_companion": normalized,
        "session_id": session_id,
        "target_path": SELECTION_TARGET_PATH.as_posix(),
        "allowed_effects": list(ALLOWED_EFFECTS),
        "forbidden_effects": list(FORBIDDEN_EFFECTS),
    }
    authority = assert_v0_1_no_authority_change()
    return {
        "ok": authority["ok"],
        "read_only": True,
        "approval_required": True,
        "selection_written": False,
        "ledger_written": False,
        "previous_companion": previous,
        "new_companion": normalized,
        "session_id": session_id,
        "target_profile": target,
        "allowed_effects": list(ALLOWED_EFFECTS),
        "forbidden_effects": list(FORBIDDEN_EFFECTS),
        "selection_target_path": SELECTION_TARGET_PATH.as_posix(),
        "selection_digest": _sha256_text(_canonical_json(material)),
        "authority": authority["authority"],
        "blocked_reasons": authority["blocked_reasons"],
    }


def record_companion_switch(
    vault_root: str | Path,
    *,
    previous_companion: str,
    new_companion: str,
    session_id: str,
    approved_by: str,
    notes: str = "",
) -> dict[str, Any]:
    """Create and append a companion switch ledger entry."""

    vault = Path(vault_root).resolve()
    entry = {
        "timestamp": _now_utc(),
        "previous_companion": previous_companion,
        "new_companion": new_companion,
        "scope": "chat_session",
        "session_id": session_id,
        "approved_by": approved_by,
        "effect": list(ALLOWED_EFFECTS),
        "routing_changed": False,
        "memory_changed": False,
        "permissions_changed": False,
        "write_target": SELECTION_TARGET_PATH.as_posix(),
        "notes": notes,
    }
    ledger_path = _safe_rel(vault, SWITCH_LEDGER_PATH)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        (ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else "")
        + _canonical_json(entry)
        + "\n",
        encoding="utf-8",
    )
    return {
        "ledger_written": True,
        "ledger_path": SWITCH_LEDGER_PATH.as_posix(),
        "ledger_entry": entry,
    }


def select_companion(
    vault_root: str | Path,
    target_id: str,
    *,
    approved: bool = False,
    approved_by: str = "operator",
    session_id: str = "default",
    notes: str = "",
) -> dict[str, Any]:
    """Write active companion selection only when an approval flag is present."""

    vault = Path(vault_root).resolve()
    preview = preview_companion_switch(vault, target_id, session_id=session_id)
    if not preview["ok"]:
        preview["approved"] = approved
        return preview
    if not approved:
        preview.update(
            {
                "ok": False,
                "approved": False,
                "selection_written": False,
                "ledger_written": False,
                "blocked_reasons": ["approval_required"],
            }
        )
        return preview

    selected = preview["new_companion"]
    previous = preview["previous_companion"]
    payload = {
        "schema_version": "chaseos.companion.selection.v0.1",
        "selected_companion_id": selected,
        "selected_runtime_id": selected,
        "previous_companion_id": previous,
        "previous_runtime_id": previous,
        "session_id": session_id,
        "approved_by": approved_by,
        "selected_at_utc": _now_utc(),
        "selection_digest": preview["selection_digest"],
        "allowed_effects": list(ALLOWED_EFFECTS),
        "forbidden_effects": list(FORBIDDEN_EFFECTS),
        "routing_changed": False,
        "memory_changed": False,
        "permissions_changed": False,
        "provider_model_changed": False,
        "tool_access_changed": False,
        "connector_access_changed": False,
        "canonical_state_mutated": False,
    }
    authority = assert_v0_1_no_authority_change(payload)
    if not authority["ok"]:
        return {
            "ok": False,
            "approved": True,
            "selection_written": False,
            "ledger_written": False,
            "blocked_reasons": authority["blocked_reasons"],
        }

    target = _safe_rel(vault, SELECTION_TARGET_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ledger = record_companion_switch(
        vault,
        previous_companion=previous,
        new_companion=selected,
        session_id=session_id,
        approved_by=approved_by,
        notes=notes,
    )
    return {
        "ok": True,
        "approved": True,
        "selection_written": True,
        "selection_target_path": SELECTION_TARGET_PATH.as_posix(),
        "selection_payload": payload,
        "ledger_written": ledger["ledger_written"],
        "ledger_path": ledger["ledger_path"],
        "ledger_entry": ledger["ledger_entry"],
        "authority": authority["authority"],
        "blocked_reasons": [],
    }
