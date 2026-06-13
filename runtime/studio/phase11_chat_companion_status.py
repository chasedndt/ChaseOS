"""Phase 11 Chat companion-status read-only contract.

This surface renders authority-neutral runtime companion cards for Chat. It reads
runtime profile and role-card metadata when present, but it does not write
profiles, mutate identity ledgers, dispatch runtimes, change permissions, or
alter companion assignments.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.companion.policy import INITIAL_COMPANION_IDS
from runtime.companion.roster import get_companion, get_companion_status_metadata, validate_roster
from runtime.companion.schema import validate_companion_profile


MODEL_VERSION = "studio.phase11_chat_companion_status.v1"
SURFACE_ID = "phase11_chat_companion_status_readonly"
PASS_ID = "phase11-chat-companion-status-readonly"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / AUTHORITY NEUTRAL"
NEXT_RECOMMENDED_PASS = "phase11-chat-companion-status-ui-shell"

BUILTIN_COMPANIONS: dict[str, dict[str, str]] = {
    companion_id: {
        "display_name": str(get_companion_status_metadata(companion_id)["display_name"]),
        "role": str(get_companion_status_metadata(companion_id)["role"]),
        "style": str(get_companion_status_metadata(companion_id)["style"]),
    }
    for companion_id in INITIAL_COMPANION_IDS
}

ROLE_CARD_HINTS = {
    companion_id: list(get_companion_status_metadata(companion_id)["role_card_hints"])
    for companion_id in INITIAL_COMPANION_IDS
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(value: str | None) -> str:
    return " ".join(str(value or "").strip().split()).lower()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path)


def _parse_frontmatter(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _parse_simple_yaml_scalars(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    data: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped == "---" or stripped.startswith("#") or stripped.startswith("-"):
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        value = value.strip().strip('"').strip("'")
        if value:
            data[key.strip()] = value
    return data


def _profile_path(vault: Path, runtime_id: str) -> Path | None:
    candidates = [
        vault / "06_AGENTS" / f"{runtime_id.title()}-Runtime-Profile.md",
        vault / "06_AGENTS" / f"{runtime_id.capitalize()}-Runtime-Profile.md",
        vault / "06_AGENTS" / f"{runtime_id}-Runtime-Profile.md",
    ]
    for path in candidates:
        if path.is_file():
            return path
    for path in (vault / "06_AGENTS").glob("*-Runtime-Profile.md") if (vault / "06_AGENTS").is_dir() else []:
        meta = _parse_frontmatter(path)
        if str(meta.get("runtime") or "").strip().lower() == runtime_id:
            return path
    return None


def _role_card_paths(vault: Path, runtime_id: str) -> list[Path]:
    root = vault / "06_AGENTS" / "role-cards"
    if not root.is_dir():
        return []
    hints = ROLE_CARD_HINTS.get(runtime_id, [runtime_id])
    results: list[Path] = []
    for path in sorted(root.glob("*.yaml")):
        lower_name = path.name.lower()
        if any(hint in lower_name for hint in hints):
            results.append(path)
    return results


def _build_card(vault: Path, runtime_id: str) -> dict[str, Any]:
    builtin = get_companion_status_metadata(runtime_id)
    core_profile = get_companion(runtime_id)
    core_profile_validation = validate_companion_profile(core_profile)
    core_profile_digest = _sha256_text(_canonical_json(core_profile))
    from runtime.companion.name_loader import resolve_companion_profile_path
    profile = resolve_companion_profile_path(runtime_id, vault)
    role_cards = _role_card_paths(vault, runtime_id)
    profile_meta = _parse_frontmatter(profile) if profile else {}
    role_meta = [_parse_simple_yaml_scalars(path) for path in role_cards]
    status_notes: list[str] = []
    if profile is None:
        status_notes.append("runtime_profile_missing_using_planned_builtin_card")
    if not role_cards:
        status_notes.append("no_connected_role_cards_found")

    display = profile_meta.get("title") or builtin.get("display_name") or runtime_id.title()
    display = display.replace(" Runtime Profile", "")
    role_names = [item.get("name") for item in role_meta if item.get("name")]
    material = {
        "runtime_id": runtime_id,
        "profile_path": _rel(vault, profile) if profile else "",
        "role_card_paths": [_rel(vault, path) for path in role_cards],
        "profile_updated": profile_meta.get("updated"),
        "core_profile_digest": core_profile_digest,
        "model_version": MODEL_VERSION,
    }

    return {
        "runtime_id": runtime_id,
        "companion_id": f"{runtime_id}-companion",
        "display_name": display,
        "runtime_role": builtin.get("role") or profile_meta.get("status") or "runtime companion",
        "style_hint": builtin.get("style") or "authority-neutral companion",
        "core_companion_package_used": True,
        "core_profile_valid": core_profile_validation["valid"] is True,
        "core_profile_digest": core_profile_digest,
        "core_policy_version": core_profile.get("governance_boundary"),
        "runtime_profile_path": _rel(vault, profile) if profile else "",
        "runtime_profile_status": profile_meta.get("status") or ("missing" if profile is None else "present"),
        "runtime_profile_updated": profile_meta.get("updated"),
        "connected_role_card_paths": [_rel(vault, path) for path in role_cards],
        "connected_role_card_names": role_names,
        "authority_ceiling": "read_only_status_only",
        "actions_allowed_now": [],
        "profile_writes_performed": False,
        "role_card_writes_performed": False,
        "runtime_control_performed": False,
        "identity_ledger_mutated": False,
        "status_notes": status_notes,
        "card_digest": _sha256_text(_canonical_json(material)),
    }


def build_phase11_chat_companion_status(
    vault_root: str | Path,
    *,
    requested_runtime: str | None = None,
) -> dict[str, Any]:
    """Build an authority-neutral companion status payload for the Chat panel."""

    vault = Path(vault_root).resolve()
    requested = _norm(requested_runtime)
    runtime_ids = list(INITIAL_COMPANION_IDS)
    core_roster_validation = validate_roster()
    cards = [_build_card(vault, runtime_id) for runtime_id in runtime_ids]
    selected = next((card for card in cards if card["runtime_id"] == requested), None) if requested else cards[0]

    blockers: list[str] = []
    if requested and selected is None:
        blockers.append("requested_companion_runtime_not_registered")
        selected_runtime_id = requested
    else:
        selected_runtime_id = str((selected or {}).get("runtime_id") or "")

    return {
        "ok": not blockers,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": {
            "requested_runtime": requested,
            "selected_runtime_id": selected_runtime_id,
            "registered_companion_count": len(cards),
            "core_companion_package_used": True,
            "core_roster_valid": core_roster_validation["valid"] is True,
            "companion_cards_visible": True,
            "authority_ceiling_visible": True,
            "profile_writes_performed": False,
            "role_card_writes_performed": False,
            "runtime_control_performed": False,
            "identity_ledger_mutated": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(blockers),
        },
        "selected_companion": selected,
        "companion_cards": cards,
        "authority": {
            "read_only": True,
            "companion_identity_is_runtime_authority": False,
            "runtime_control_allowed": False,
            "runtime_dispatch_allowed": False,
            "identity_ledger_mutation_allowed": False,
            "role_card_mutation_allowed": False,
            "profile_write_allowed": False,
            "permission_change_allowed": False,
            "provider_calls_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "runtime_control",
            "runtime_dispatch",
            "identity_ledger_mutation",
            "role_card_mutation",
            "profile_write",
            "permission_change",
            "provider_api_call",
            "agent_bus_task_write",
            "canonical_writeback",
        ],
        "blocked_reasons": blockers,
        "readiness": {
            "companion_status_contract_ready": True,
            "runtime_companion_core_adapter_synced": True,
            "companion_cards_renderable": True,
            "authority_neutral": True,
            "profile_writes_blocked": True,
            "role_card_writes_blocked": True,
            "runtime_control_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
    }
