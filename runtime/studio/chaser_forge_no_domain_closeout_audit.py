"""No-domain closeout audit for Chaser Forge Studio wiring.

This audit proves the current no-domain state only. It does not fetch live
URLs, upload static files, mutate an external registry, install packages, call
providers, dispatch Agent Bus tasks, or grant new Studio authority.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.forge.marketplace import (
    FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES,
    build_forge_marketplace_live_index_input_readiness,
)
from runtime.forge.panel import build_chaser_forge_panel
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry


MODEL_VERSION = "studio.chaser_forge_no_domain_closeout_audit.v1"
SURFACE_ID = "chaser_forge_no_domain_closeout_audit"
STATUS_COMPLETE = "COMPLETE / NO-DOMAIN CLOSEOUT VERIFIED / OPERATOR DOMAIN ACTION REQUIRED"
PREFILL_ROOT = (
    Path("07_LOGS")
    / "Operator-Briefs"
    / "Chaser-Forge-Live-Index-Input-Prefills"
)
HANDOVER_PATH = (
    Path("07_LOGS")
    / "Operator-Briefs"
    / "2026-05-24-chaser-forge-live-index-json-input-handover.md"
)
FRONTEND_ROOT = Path(__file__).resolve().parent / "shell" / "frontend"
FRONTEND_APP_PATH = FRONTEND_ROOT / "app.js"
FRONTEND_INDEX_PATH = FRONTEND_ROOT / "index.html"
NEXT_RECOMMENDED_PASS = "operator-purchase-domain-upload-static-files-and-finalize-live-index-input-packet"

REQUIRED_API_METHODS = (
    "get_chaser_forge_panel",
    "get_chaser_forge_marketplace_live_index_input_prefill",
    "write_chaser_forge_marketplace_live_index_input_prefill",
    "get_chaser_forge_marketplace_live_index_input_readiness",
    "get_chaser_forge_no_domain_closeout_audit",
)

REQUIRED_APP_TOKENS = (
    "loadChaserForgePanel",
    "marketplaceLiveIndexInputPrefill",
    "marketplaceLiveIndexInputReadiness",
    "marketplaceDomainDeferred",
    "Hosted Marketplace - Coming Soon",
    "Coming soon: official ChaseOS domain required",
    "chaser-forge-write-live-index-input-prefill",
    "Prefill Live Input Packet",
    "chaser-forge-write-published-static-index-registration",
)

REQUIRED_INDEX_TOKENS = (
    'id="panel-chaser-forge"',
    'data-panel-id="chaser-forge"',
    "Extensions",
    'id="chaser-forge-status"',
    'id="chaser-forge-body"',
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _resolve_vault_child(vault: Path, value: str | Path | None) -> tuple[Path | None, str | None]:
    if value is None or str(value).strip() == "":
        return None, "path_required"
    raw = Path(str(value))
    path = raw.resolve() if raw.is_absolute() else (vault / raw).resolve()
    try:
        path.relative_to(vault)
    except ValueError:
        return path, "path_outside_vault_root"
    return path, None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _latest_prefill_packet(vault: Path) -> Path | None:
    root = (vault / PREFILL_ROOT).resolve()
    if not root.is_dir():
        return None
    candidates = sorted(
        (path for path in root.glob("live-index-input-prefill-*.json") if path.is_file()),
        key=lambda item: (item.stat().st_mtime, item.name),
        reverse=True,
    )
    return candidates[0] if candidates else None


def _frontend_contract() -> dict[str, Any]:
    app_text = _read_text(FRONTEND_APP_PATH)
    index_text = _read_text(FRONTEND_INDEX_PATH)
    missing_app_tokens = [token for token in REQUIRED_APP_TOKENS if token not in app_text]
    missing_index_tokens = [token for token in REQUIRED_INDEX_TOKENS if token not in index_text]
    return {
        "app_path": str(FRONTEND_APP_PATH),
        "index_path": str(FRONTEND_INDEX_PATH),
        "app_present": FRONTEND_APP_PATH.is_file(),
        "index_present": FRONTEND_INDEX_PATH.is_file(),
        "required_app_tokens": list(REQUIRED_APP_TOKENS),
        "required_index_tokens": list(REQUIRED_INDEX_TOKENS),
        "missing_app_tokens": missing_app_tokens,
        "missing_index_tokens": missing_index_tokens,
        "app_tokens_present": not missing_app_tokens,
        "index_tokens_present": not missing_index_tokens,
        "source_ui_tokens_present": not missing_app_tokens and not missing_index_tokens,
    }


def _registry_contract(vault: Path) -> dict[str, Any]:
    registry = build_native_shell_panel_registry(vault)
    panels = {str(panel.get("id")): panel for panel in registry.get("panels") or []}
    panel = panels.get("chaser-forge") or {}
    api_methods = [str(item) for item in panel.get("api_methods") or []]
    missing_api_methods = [method for method in REQUIRED_API_METHODS if method not in api_methods]
    readiness = registry.get("readiness") if isinstance(registry.get("readiness"), dict) else {}
    return {
        "panel_present": bool(panel),
        "panel_status": panel.get("status"),
        "frontend_target": panel.get("frontend_target"),
        "route_hint": panel.get("route_hint"),
        "api_methods": api_methods,
        "missing_api_methods": missing_api_methods,
        "required_api_methods": list(REQUIRED_API_METHODS),
        "api_methods_present": not missing_api_methods,
        "frontend_target_wired": panel.get("frontend_target") == "panel-chaser-forge",
        "route_wired": panel.get("route_hint") == "#/chaser-forge",
        "readiness_flags": {
            "live_index_input_prefill_built": readiness.get(
                "chaser_forge_marketplace_live_index_input_prefill_built"
            ),
            "live_index_input_prefill_ready": readiness.get(
                "chaser_forge_marketplace_live_index_input_prefill_ready"
            ),
            "live_index_input_readiness_built": readiness.get(
                "chaser_forge_marketplace_live_index_input_readiness_built"
            ),
            "live_index_input_domain_deferred": readiness.get(
                "chaser_forge_marketplace_live_index_input_domain_deferred"
            ),
            "no_domain_closeout_audit_built": readiness.get(
                "chaser_forge_no_domain_closeout_audit_built"
            ),
        },
    }


def _static_publication_contract(vault: Path, packet: dict[str, Any]) -> dict[str, Any]:
    static_dir_ref = str(packet.get("local_static_publication_dir") or "").strip()
    static_dir, path_blocker = _resolve_vault_child(vault, static_dir_ref)
    required_files = list(FORGE_MARKETPLACE_STATIC_PUBLICATION_REQUIRED_FILES)
    missing_files: list[str] = []
    file_digests: dict[str, str] = {}
    if static_dir is not None and static_dir.is_dir():
        for name in required_files:
            child = static_dir / name
            if child.is_file():
                file_digests[name] = _sha256_file(child)
            else:
                missing_files.append(name)
    else:
        missing_files = required_files
    index_sha256 = file_digests.get("index.json", "")
    packet_sha256 = str(packet.get("local_index_sha256") or "").strip()
    return {
        "local_static_publication_dir": static_dir_ref,
        "local_static_publication_dir_path": _relative_to_vault(vault, static_dir),
        "path_blocker": path_blocker,
        "present": bool(static_dir and static_dir.is_dir()),
        "required_files": required_files,
        "missing_required_files": missing_files,
        "required_files_present": not missing_files,
        "file_digests": file_digests,
        "index_sha256": index_sha256,
        "packet_local_index_sha256": packet_sha256,
        "local_index_sha256_matches_packet": bool(
            index_sha256 and packet_sha256 and index_sha256.lower() == packet_sha256.lower()
        ),
    }


def _packet_contract(vault: Path, input_packet_path: str | Path | None) -> dict[str, Any]:
    packet_path = None
    path_blocker = None
    if input_packet_path is not None:
        packet_path, path_blocker = _resolve_vault_child(vault, input_packet_path)
    else:
        packet_path = _latest_prefill_packet(vault)
    packet = _read_json(packet_path)
    markdown_path = packet_path.with_suffix(".md") if packet_path else None
    public_index_url = str(packet.get("public_index_url") or "")
    hosted_base_url = str(packet.get("hosted_base_url") or "")
    upload_confirmation = str(packet.get("operator_upload_confirmation") or "")
    fetch_approval = str(packet.get("operator_fetch_approval_statement") or "")
    local_index_sha256 = str(packet.get("local_index_sha256") or "")
    domain_placeholder_present = (
        "<official-chaseos-domain>" in public_index_url
        and "<official-chaseos-domain>" in hosted_base_url
    )
    pending_operator_fields = (
        upload_confirmation.upper().startswith("PENDING")
        and fetch_approval.upper().startswith("PENDING")
    )
    return {
        "path": _relative_to_vault(vault, packet_path),
        "path_blocker": path_blocker,
        "present": bool(packet_path and packet_path.is_file()),
        "loaded": bool(packet),
        "packet": packet,
        "markdown_path": _relative_to_vault(vault, markdown_path),
        "markdown_present": bool(markdown_path and markdown_path.is_file()),
        "packet_type": packet.get("packet_type"),
        "schema_version": packet.get("schema_version"),
        "public_index_url": public_index_url,
        "hosted_base_url": hosted_base_url,
        "domain_placeholder_present": domain_placeholder_present,
        "pending_operator_fields": pending_operator_fields,
        "local_index_sha256": local_index_sha256,
        "local_index_sha256_shape_valid": bool(
            len(local_index_sha256) == 64
            and all(char in "0123456789abcdefABCDEF" for char in local_index_sha256)
        ),
    }


def _handover_contract(vault: Path) -> dict[str, Any]:
    path = vault / HANDOVER_PATH
    text = _read_text(path)
    lowered = text.lower()
    return {
        "path": HANDOVER_PATH.as_posix(),
        "present": path.is_file(),
        "domain_deferred_text_present": (
            "official chaseos domain is purchased" in lowered
            or "blocked on domain purchase" in lowered
            or "domain is purchased" in lowered
        ),
        "prefill_path_text_present": "live-index-input-prefill-" in text,
        "coming_soon_text_present": "Hosted Marketplace - Coming Soon" in text,
    }


def _check(check_id: str, satisfied: bool, evidence: str) -> dict[str, Any]:
    return {"id": check_id, "satisfied": bool(satisfied), "evidence": evidence}


def _authority() -> dict[str, Any]:
    return {
        "read_only": True,
        "network_fetch_allowed": False,
        "network_upload_allowed": False,
        "external_registry_mutation_allowed": False,
        "package_install_allowed": False,
        "payment_mutation_allowed": False,
        "license_checkout_allowed": False,
        "provider_or_model_call_allowed": False,
        "agent_bus_dispatch_allowed": False,
        "protected_core_mutation_allowed": False,
        "canonical_mutation_allowed": False,
        "studio_write_control_added": False,
    }


def build_chaser_forge_no_domain_closeout_audit(
    vault_root: str | Path,
    *,
    input_packet_path: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a read-only closeout report for the no-domain Chaser Forge state."""

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    packet_contract = _packet_contract(vault, input_packet_path)
    packet = packet_contract["packet"] if isinstance(packet_contract.get("packet"), dict) else {}
    static_contract = _static_publication_contract(vault, packet)
    handover_contract = _handover_contract(vault)
    registry_contract = _registry_contract(vault)
    frontend_contract = _frontend_contract()
    panel = build_chaser_forge_panel(vault)
    marketplace = panel.get("marketplace") if isinstance(panel.get("marketplace"), dict) else {}
    summary = panel.get("summary") if isinstance(panel.get("summary"), dict) else {}

    readiness = {}
    if packet_contract["path"]:
        readiness = build_forge_marketplace_live_index_input_readiness(
            vault,
            input_packet_path=str(packet_contract["path"]),
            generated_at=timestamp,
        )

    ui_wired = all(
        [
            registry_contract["panel_present"],
            registry_contract["frontend_target_wired"],
            registry_contract["route_wired"],
            registry_contract["api_methods_present"],
            frontend_contract["source_ui_tokens_present"],
        ]
    )
    prefill_packet_ready = all(
        [
            packet_contract["present"],
            packet_contract["loaded"],
            packet_contract["markdown_present"],
            packet_contract["domain_placeholder_present"],
            packet_contract["pending_operator_fields"],
            packet_contract["local_index_sha256_shape_valid"],
            static_contract["present"],
            static_contract["required_files_present"],
            static_contract["local_index_sha256_matches_packet"],
        ]
    )
    readiness_domain_deferred = readiness.get("domain_purchase_deferred") is True
    live_fetch_deferred = all(
        [
            readiness.get("ready_for_live_verification") is False,
            readiness_domain_deferred,
            readiness.get("network_fetch_allowed") is False,
            readiness.get("network_upload_allowed") is False,
            readiness.get("external_registry_mutation_allowed") is False,
        ]
    )
    coming_soon_ready = all(
        [
            frontend_contract["source_ui_tokens_present"],
            "Hosted Marketplace - Coming Soon" in frontend_contract["required_app_tokens"],
            summary.get("public_marketplace_deferred") is True
            or marketplace.get("live_index_input_readiness", {}).get("domain_purchase_deferred") is True
            or readiness_domain_deferred,
        ]
    )

    checks = [
        _check("studio_panel_registered", registry_contract["panel_present"], "Panel id chaser-forge exists."),
        _check(
            "studio_frontend_target_wired",
            registry_contract["frontend_target_wired"],
            "Panel registry targets panel-chaser-forge.",
        ),
        _check(
            "studio_api_methods_wired",
            registry_contract["api_methods_present"],
            "Registry exposes prefill, readiness, and no-domain audit API methods.",
        ),
        _check(
            "frontend_source_tokens_present",
            frontend_contract["source_ui_tokens_present"],
            "Frontend source contains Chaser Forge panel, Coming Soon state, and prefill control tokens.",
        ),
        _check(
            "prefill_packet_materialized",
            prefill_packet_ready,
            "Prefill packet, Markdown handoff, static publication files, and local index SHA all match.",
        ),
        _check(
            "live_fetch_domain_deferred",
            live_fetch_deferred,
            "Readiness remains blocked on domain purchase and grants no network fetch/upload/registry mutation.",
        ),
        _check(
            "handover_records_deferred_domain",
            handover_contract["domain_deferred_text_present"],
            "Operator handover records official-domain deferral.",
        ),
        _check(
            "hosted_marketplace_coming_soon",
            coming_soon_ready,
            "Studio source and panel state represent the hosted marketplace as Coming Soon while domain is missing.",
        ),
    ]
    code_owned_blockers = [f"check_failed:{item['id']}" for item in checks if item["satisfied"] is not True]
    if readiness and readiness.get("ok") is not True:
        code_owned_blockers.append("live_index_input_readiness_builder_failed")

    operator_owned_domain_blockers = [
        str(item)
        for item in readiness.get("blockers") or []
        if str(item)
        in {
            "domain_purchase_deferred_until_official_domain_is_purchased",
            "public_index_url_required",
            "hosted_base_url_required",
            "operator_upload_confirmation_must_confirm_upload",
            "operator_fetch_approval_statement_must_name_local_index_sha256",
        }
    ]
    status = (
        STATUS_COMPLETE
        if not code_owned_blockers
        else "BLOCKED / NO-DOMAIN CLOSEOUT AUDIT HAS CODE-OWNED GAPS"
    )
    ok = not code_owned_blockers

    return {
        "ok": ok,
        "record_type": SURFACE_ID,
        "schema_version": MODEL_VERSION,
        "surface": SURFACE_ID,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "summary": {
            "ui_wired_to_studio": ui_wired,
            "prefill_packet_ready": prefill_packet_ready,
            "hosted_marketplace_coming_soon": coming_soon_ready,
            "live_fetch_deferred": live_fetch_deferred,
            "code_owned_no_domain_work_remaining": bool(code_owned_blockers),
            "operator_owned_domain_work_remaining": True,
            "domain_purchase_required": True,
            "ready_for_live_verification": False,
            "next_recommended_pass": NEXT_RECOMMENDED_PASS,
        },
        "checks": checks,
        "code_owned_blockers": code_owned_blockers,
        "operator_owned_domain_blockers": operator_owned_domain_blockers,
        "packet": packet_contract | {"packet": None},
        "static_publication": static_contract,
        "handover": handover_contract,
        "registry": registry_contract,
        "frontend": frontend_contract,
        "panel_summary": {
            "public_marketplace_deferred": summary.get("public_marketplace_deferred"),
            "public_marketplace_status": summary.get("public_marketplace_status"),
            "marketplace_live_index_input_prefill_ready": summary.get(
                "marketplace_live_index_input_prefill_ready"
            ),
            "marketplace_live_index_input_domain_deferred": summary.get(
                "marketplace_live_index_input_domain_deferred"
            ),
        },
        "readiness": readiness,
        "authority": _authority(),
        "next_recommended_pass": NEXT_RECOMMENDED_PASS,
    }
