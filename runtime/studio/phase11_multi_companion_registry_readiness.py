"""Phase 11 multi-companion registry readiness.

This surface reads the planned companion registry, validates its profile shape,
and compares registry entries with the builtin companion status cards. It does
not load the registry into runtime selection, write companion state, dispatch
runtimes, call providers, write Agent Bus tasks, or mutate canonical state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.companion.policy import INITIAL_COMPANION_IDS
from runtime.companion.policy import SELECTION_TARGET_PATH as CORE_SELECTION_TARGET_PATH
from runtime.studio.phase11_chat_companion_status import build_phase11_chat_companion_status


MODEL_VERSION = "studio.phase11_multi_companion_registry_readiness.v1"
SURFACE_ID = "phase11_multi_companion_registry_readiness"
PASS_ID = "phase11-multi-companion-registry-readiness"
STATUS = "COMPLETE / READ-ONLY / VERIFIED / REGISTRY READINESS ONLY"
NEXT_RECOMMENDED_PASS = "operator-companion-direction-before-roster-ui"
DEFAULT_REGISTRY_PATH = Path("runtime") / "studio" / "chat" / "companions" / "registry.example.json"
PREFERRED_REGISTRY_PATH = Path("runtime") / "studio" / "chat" / "companions" / "registry.json"
PROFILE_SCHEMA_PATH = Path("runtime") / "studio" / "chat" / "companions" / "companion-profile.schema.json"
ALLOWED_STATUSES = {"planned", "available_builtin", "available_registry", "disabled"}
ALLOWED_AVATAR_KINDS = {"brand_icon", "generated_avatar", "runtime_mark", "initials"}
ALLOWED_SURFACES = {"chat_panel", "dashboard", "runtime_status", "slash_pet", "companion_roster"}
SELECTION_TARGET_PATH = CORE_SELECTION_TARGET_PATH.as_posix()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _rel(vault: Path, path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _resolve_registry_path(vault: Path, registry_path: str | Path | None) -> tuple[Path, list[str], list[str]]:
    warnings: list[str] = []
    blockers: list[str] = []
    if registry_path:
        candidate = Path(registry_path)
        if candidate.is_absolute():
            try:
                candidate.resolve().relative_to(vault.resolve())
            except ValueError:
                blockers.append("registry_path_outside_vault")
            return candidate.resolve(), warnings, blockers
        return (vault / candidate).resolve(), warnings, blockers

    preferred = (vault / PREFERRED_REGISTRY_PATH).resolve()
    if preferred.is_file():
        return preferred, warnings, blockers
    warnings.append("preferred_registry_missing_using_example_registry")
    return (vault / DEFAULT_REGISTRY_PATH).resolve(), warnings, blockers


def _read_json(path: Path) -> tuple[Any | None, str | None, str | None]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, None, f"json_read_failed:{exc}"
    try:
        return json.loads(raw.decode("utf-8")), _sha256_bytes(raw), None
    except UnicodeDecodeError as exc:
        return None, _sha256_bytes(raw), f"json_utf8_decode_failed:{exc}"
    except json.JSONDecodeError as exc:
        return None, _sha256_bytes(raw), f"json_decode_failed:{exc}"


def _require_object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path}:not_object")
        return {}
    return value


def _require_bool_false(value: Any, path: str, errors: list[str]) -> None:
    if value is not False:
        errors.append(f"{path}:must_be_false")


def _validate_companion(item: Any, index: int) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    companion = _require_object(item, f"companions[{index}]", errors)
    required = [
        "companion_id",
        "display_name",
        "runtime_id",
        "status",
        "avatar",
        "tone_tags",
        "supported_surfaces",
        "authority",
        "selection",
        "evidence",
    ]
    for key in required:
        if key not in companion:
            errors.append(f"companions[{index}].{key}:missing")

    companion_id = str(companion.get("companion_id") or "")
    display_name = str(companion.get("display_name") or "")
    runtime_id = str(companion.get("runtime_id") or "").strip().lower()
    status = str(companion.get("status") or "")
    if not companion_id:
        errors.append(f"companions[{index}].companion_id:empty")
    if not display_name:
        errors.append(f"companions[{index}].display_name:empty")
    if not runtime_id:
        errors.append(f"companions[{index}].runtime_id:empty")
    if status not in ALLOWED_STATUSES:
        errors.append(f"companions[{index}].status:unsupported:{status}")

    avatar = _require_object(companion.get("avatar"), f"companions[{index}].avatar", errors)
    avatar_kind = str(avatar.get("kind") or "")
    if avatar_kind not in ALLOWED_AVATAR_KINDS:
        errors.append(f"companions[{index}].avatar.kind:unsupported:{avatar_kind}")
    if "asset_path" not in avatar:
        errors.append(f"companions[{index}].avatar.asset_path:missing")
    if avatar_kind in {"brand_icon", "generated_avatar"} and not str(avatar.get("asset_path") or ""):
        warnings.append(f"companions[{index}].avatar.asset_path:empty_for_asset_avatar")

    tone_tags = companion.get("tone_tags")
    if not isinstance(tone_tags, list) or not all(isinstance(value, str) for value in tone_tags):
        errors.append(f"companions[{index}].tone_tags:must_be_string_array")
    surfaces = companion.get("supported_surfaces")
    if not isinstance(surfaces, list) or not all(isinstance(value, str) for value in surfaces):
        errors.append(f"companions[{index}].supported_surfaces:must_be_string_array")
    else:
        unknown_surfaces = sorted(set(surfaces) - ALLOWED_SURFACES)
        if unknown_surfaces:
            errors.append(f"companions[{index}].supported_surfaces:unsupported:{','.join(unknown_surfaces)}")

    authority = _require_object(companion.get("authority"), f"companions[{index}].authority", errors)
    for key in [
        "personality_grants_authority",
        "runtime_control_allowed",
        "provider_calls_allowed",
        "agent_bus_task_write_allowed",
        "canonical_mutation_allowed",
    ]:
        _require_bool_false(authority.get(key), f"companions[{index}].authority.{key}", errors)

    selection = _require_object(companion.get("selection"), f"companions[{index}].selection", errors)
    if selection.get("selection_requires_approval_executor") is not True:
        errors.append(f"companions[{index}].selection.selection_requires_approval_executor:must_be_true")
    if selection.get("target_path") != SELECTION_TARGET_PATH:
        errors.append(f"companions[{index}].selection.target_path:must_equal:{SELECTION_TARGET_PATH}")
    if not isinstance(selection.get("can_be_selected"), bool):
        errors.append(f"companions[{index}].selection.can_be_selected:must_be_boolean")

    evidence = _require_object(companion.get("evidence"), f"companions[{index}].evidence", errors)
    if not str(evidence.get("source") or ""):
        errors.append(f"companions[{index}].evidence.source:empty")
    if evidence.get("profile_digest_required") is not True:
        errors.append(f"companions[{index}].evidence.profile_digest_required:must_be_true")

    return {
        "index": index,
        "companion_id": companion_id,
        "display_name": display_name,
        "runtime_id": runtime_id,
        "status": status,
        "can_be_selected": selection.get("can_be_selected") is True,
        "supported_surfaces": surfaces if isinstance(surfaces, list) else [],
        "errors": errors,
        "warnings": warnings,
        "raw": companion if isinstance(companion, dict) else {},
    }


def _validate_registry(payload: Any) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    registry = _require_object(payload, "registry", errors)
    companions = registry.get("companions")
    if not isinstance(companions, list):
        errors.append("registry.companions:must_be_array")
        companions = []

    validated = [_validate_companion(item, index) for index, item in enumerate(companions)]
    for item in validated:
        errors.extend(item["errors"])
        warnings.extend(item["warnings"])

    companion_ids = [item["companion_id"] for item in validated if item["companion_id"]]
    runtime_ids = [item["runtime_id"] for item in validated if item["runtime_id"]]
    for value in sorted({item for item in companion_ids if companion_ids.count(item) > 1}):
        errors.append(f"registry.companion_id:duplicate:{value}")
    for value in sorted({item for item in runtime_ids if runtime_ids.count(item) > 1}):
        errors.append(f"registry.runtime_id:duplicate:{value}")

    blocked_authority = registry.get("blocked_authority")
    blocked = _require_object(blocked_authority, "registry.blocked_authority", errors)
    for key in [
        "runtime_loader_implemented",
        "selection_target_written",
        "approval_consumed",
        "provider_call_performed",
        "runtime_dispatched",
        "agent_bus_task_written",
        "canonical_state_mutated",
    ]:
        _require_bool_false(blocked.get(key), f"registry.blocked_authority.{key}", errors)

    return {
        "registry_id": registry.get("registry_id"),
        "status": registry.get("status"),
        "next_recommended_pass": registry.get("next_recommended_pass"),
        "companions": [
            {key: value for key, value in item.items() if key != "raw"} for item in validated
        ],
        "blocked_authority": blocked,
    }, errors, warnings


def build_phase11_multi_companion_registry_readiness(
    vault_root: str | Path,
    *,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a read-only readiness payload for the multi-companion registry."""

    vault = Path(vault_root).resolve()
    resolved_registry, warnings, path_blockers = _resolve_registry_path(vault, registry_path)
    schema_path = (vault / PROFILE_SCHEMA_PATH).resolve()
    registry_payload, registry_sha, registry_error = _read_json(resolved_registry)
    schema_payload, schema_sha, schema_error = _read_json(schema_path)
    validation: dict[str, Any] = {
        "registry_id": None,
        "status": None,
        "next_recommended_pass": None,
        "companions": [],
        "blocked_authority": {},
    }
    validation_errors: list[str] = []
    validation_warnings: list[str] = []
    if registry_error:
        validation_errors.append(registry_error)
    elif registry_payload is not None:
        validation, validation_errors, validation_warnings = _validate_registry(registry_payload)
    warnings.extend(validation_warnings)

    if schema_error:
        validation_errors.append(f"profile_schema:{schema_error}")
    elif not isinstance(schema_payload, dict):
        validation_errors.append("profile_schema:not_object")

    companion_status = build_phase11_chat_companion_status(vault)
    status_cards = companion_status.get("companion_cards") or []
    status_runtime_ids = {
        str(card.get("runtime_id") or "").strip().lower()
        for card in status_cards
        if str(card.get("runtime_id") or "").strip()
    }
    registry_runtime_ids = {
        str(item.get("runtime_id") or "").strip().lower()
        for item in validation.get("companions") or []
        if str(item.get("runtime_id") or "").strip()
    }
    builtin_runtime_ids = set(INITIAL_COMPANION_IDS)
    missing_builtin_runtime_ids = sorted(builtin_runtime_ids - registry_runtime_ids)
    registry_runtime_ids_without_builtin_status = sorted(registry_runtime_ids - status_runtime_ids)
    if missing_builtin_runtime_ids:
        validation_errors.append("registry_missing_builtin_runtime_ids:" + ",".join(missing_builtin_runtime_ids))
    if registry_runtime_ids_without_builtin_status:
        validation_errors.append(
            "registry_runtime_ids_without_status_cards:" + ",".join(registry_runtime_ids_without_builtin_status)
        )

    selection_target = (vault / SELECTION_TARGET_PATH).resolve()
    registry_loaded_for_selection = False
    blockers = list(path_blockers) + validation_errors
    ok = not blockers
    digest_material = {
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "registry_path": _rel(vault, resolved_registry),
        "registry_sha256": registry_sha,
        "schema_path": _rel(vault, schema_path),
        "schema_sha256": schema_sha,
        "registry_runtime_ids": sorted(registry_runtime_ids),
        "status_runtime_ids": sorted(status_runtime_ids),
        "selection_target_path": SELECTION_TARGET_PATH,
    }
    readiness_digest = _sha256_text(_canonical_json(digest_material))

    return {
        "ok": ok,
        "surface": SURFACE_ID,
        "model_version": MODEL_VERSION,
        "pass": PASS_ID,
        "status": STATUS if ok else "BLOCKED / READ-ONLY / REGISTRY READINESS ONLY",
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "approval_gated": False,
        "summary": {
            "registry_path": _rel(vault, resolved_registry),
            "profile_schema_path": _rel(vault, schema_path),
            "registry_json_valid": registry_payload is not None and registry_error is None,
            "profile_schema_json_valid": schema_payload is not None and schema_error is None,
            "registry_companion_count": len(validation.get("companions") or []),
            "builtin_companion_count": len(INITIAL_COMPANION_IDS),
            "status_card_count": len(status_cards),
            "core_companion_package_used": True,
            "registry_covers_builtin_companions": not missing_builtin_runtime_ids,
            "registry_runtime_ids_have_status_cards": not registry_runtime_ids_without_builtin_status,
            "registry_loaded_for_selection": registry_loaded_for_selection,
            "selection_target_written": False,
            "approval_consumed": False,
            "provider_call_performed": False,
            "runtime_dispatched": False,
            "agent_bus_task_written": False,
            "canonical_state_mutated": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
            "blocker_count": len(list(dict.fromkeys(blockers))),
        },
        "registry": validation,
        "comparison": {
            "builtin_runtime_ids": sorted(builtin_runtime_ids),
            "status_runtime_ids": sorted(status_runtime_ids),
            "registry_runtime_ids": sorted(registry_runtime_ids),
            "missing_builtin_runtime_ids": missing_builtin_runtime_ids,
            "registry_runtime_ids_without_builtin_status": registry_runtime_ids_without_builtin_status,
            "companion_status_surface_ok": companion_status.get("ok") is True,
        },
        "files": {
            "registry_path": _rel(vault, resolved_registry),
            "registry_exists": resolved_registry.is_file(),
            "registry_sha256": registry_sha,
            "profile_schema_path": _rel(vault, schema_path),
            "profile_schema_exists": schema_path.is_file(),
            "profile_schema_sha256": schema_sha,
            "selection_target_path": SELECTION_TARGET_PATH,
            "selection_target_exists": selection_target.exists(),
            "selection_target_written_now": False,
        },
        "digest_proof": {
            "readiness_digest": readiness_digest,
            "digest_material": digest_material,
        },
        "companion_status_contract": companion_status,
        "readiness": {
            "multi_companion_registry_readiness_ready": ok,
            "runtime_companion_core_adapter_synced": True,
            "registry_file_loaded_read_only": registry_payload is not None and registry_error is None,
            "profile_schema_loaded_read_only": schema_payload is not None and schema_error is None,
            "registry_shape_valid": not validation_errors,
            "registry_compares_to_builtin_cards": not missing_builtin_runtime_ids
            and not registry_runtime_ids_without_builtin_status,
            "selection_target_write_blocked": True,
            "approval_consumption_blocked": True,
            "provider_calls_blocked": True,
            "runtime_dispatch_blocked": True,
            "agent_bus_task_write_blocked": True,
            "canonical_mutation_blocked": True,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "authority": {
            "read_only": True,
            "registry_read_allowed": True,
            "profile_schema_read_allowed": True,
            "registry_loader_activated": False,
            "registry_write_allowed": False,
            "companion_roster_ui_mutation_allowed": False,
            "approval_consumption_allowed": False,
            "approval_execution_allowed": False,
            "companion_selection_write_allowed": False,
            "runtime_control_allowed": False,
            "runtime_dispatch_allowed": False,
            "identity_ledger_mutation_allowed": False,
            "role_card_mutation_allowed": False,
            "profile_write_allowed": False,
            "provider_calls_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "denied_by_this_surface": [
            "registry_runtime_loader_activation",
            "registry_write",
            "companion_roster_ui_mutation",
            "approval_consumption",
            "approval_execution",
            "companion_selection_target_write",
            "runtime_control",
            "runtime_dispatch",
            "identity_ledger_mutation",
            "role_card_mutation",
            "profile_write",
            "provider_api_call",
            "agent_bus_task_write",
            "canonical_writeback",
        ],
        "blocked_reasons": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def format_phase11_multi_companion_registry_readiness(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") or {}
    comparison = payload.get("comparison") or {}
    digest = payload.get("digest_proof") or {}
    lines = [
        "Phase 11 Multi-Companion Registry Readiness",
        f"Status: {payload.get('status')}",
        f"Registry path: {summary.get('registry_path') or 'missing'}",
        f"Registry companions: {summary.get('registry_companion_count')}",
        f"Builtin companions: {summary.get('builtin_companion_count')}",
        f"Registry covers builtins: {summary.get('registry_covers_builtin_companions')}",
        f"Registry loaded for selection: {summary.get('registry_loaded_for_selection')}",
        f"Selection target written: {summary.get('selection_target_written')}",
        f"Readiness digest: {digest.get('readiness_digest') or 'missing'}",
        f"Registry runtime ids: {', '.join(comparison.get('registry_runtime_ids') or [])}",
        f"Next recommended pass: {summary.get('next_recommended_pass')}",
    ]
    blockers = payload.get("blocked_reasons") or []
    if blockers:
        lines.append("Blocked reasons:")
        lines.extend(f"- {item}" for item in blockers)
    warnings = payload.get("warnings") or []
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {item}" for item in warnings)
    lines.append(
        "Boundary: read-only registry readiness only; no registry activation, no roster UI mutation, "
        "no companion selection write, no approval consumption/execution, no provider/runtime/Agent Bus/canonical mutation."
    )
    return "\n".join(lines)
