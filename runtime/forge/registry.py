"""Registry and sandbox approval request surfaces for Chaser Forge."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.forge.validator import validate_manifest


MODEL_VERSION = "forge.registry.v1"
REGISTRY_ENTRY_SCHEMA_VERSION = "forge.registry.entry.v1"
SANDBOX_APPROVAL_SCHEMA_VERSION = "forge.sandbox_approval_request.v1"
SANDBOX_REGISTRY_WRITE_SCHEMA_VERSION = "forge.sandbox_registry_write.v1"
LIVE_INSTALL_APPROVAL_SCHEMA_VERSION = "forge.live_install_approval_request.v1"
LIVE_INSTALL_EXECUTION_SCHEMA_VERSION = "forge.live_install_execution.v1"
ROLLBACK_APPROVAL_SCHEMA_VERSION = "forge.rollback_approval_request.v1"
ROLLBACK_EXECUTION_SCHEMA_VERSION = "forge.rollback_execution.v1"
REGISTRY_SURFACE_ID = "chaser_forge_extension_registry"
SANDBOX_APPROVAL_SURFACE_ID = "chaser_forge_sandbox_install_approval"
SANDBOX_REGISTRY_WRITE_SURFACE_ID = "chaser_forge_sandbox_registry_writer"
LIVE_INSTALL_APPROVAL_SURFACE_ID = "chaser_forge_live_install_approval"
LIVE_INSTALL_EXECUTION_SURFACE_ID = "chaser_forge_live_install_executor"
ROLLBACK_APPROVAL_SURFACE_ID = "chaser_forge_rollback_approval"
ROLLBACK_EXECUTION_SURFACE_ID = "chaser_forge_rollback_executor"
FORGE_APPROVAL_DECISION_SCHEMA_VERSION = "forge.approval_decision.v1"
FORGE_APPROVAL_DECISION_SURFACE_ID = "chaser_forge_approval_center_decision_handoff"
FORGE_APPROVAL_DECISION_RECORD_TYPE = "forge_approval_decision_handoff"
FORGE_APPROVAL_DECISION_API_METHOD = "review_chaser_forge_approval_decision"
SANDBOX_APPROVAL_RECORD_TYPE = "forge_sandbox_install_approval_request"
SANDBOX_REGISTRY_WRITE_MARKER_RECORD_TYPE = "forge_sandbox_registry_write_exact_once_marker"
LIVE_INSTALL_APPROVAL_RECORD_TYPE = "forge_live_install_approval_request"
LIVE_INSTALL_MARKER_RECORD_TYPE = "forge_live_install_exact_once_marker"
ROLLBACK_APPROVAL_RECORD_TYPE = "forge_rollback_approval_request"
ROLLBACK_MARKER_RECORD_TYPE = "forge_rollback_exact_once_marker"
SANDBOX_APPROVAL_SCOPE = "one_forge_sandbox_install_request_only"
LIVE_INSTALL_APPROVAL_SCOPE = "one_forge_live_install_request_only"
ROLLBACK_APPROVAL_SCOPE = "one_forge_rollback_request_only"
REGISTRY_RELATIVE_PATH = Path("runtime") / "forge" / "registry" / "extensions.json"
SANDBOX_APPROVAL_RELATIVE_DIR = Path("07_LOGS") / "Agent-Activity" / "_forge_sandbox_approvals"
SANDBOX_MARKER_RELATIVE_DIR = SANDBOX_APPROVAL_RELATIVE_DIR / "_sandbox_markers"
SANDBOX_DECISION_RELATIVE_DIR = SANDBOX_APPROVAL_RELATIVE_DIR / "_decisions"
LIVE_INSTALL_APPROVAL_RELATIVE_DIR = Path("07_LOGS") / "Agent-Activity" / "_forge_live_install_approvals"
LIVE_INSTALL_MARKER_RELATIVE_DIR = LIVE_INSTALL_APPROVAL_RELATIVE_DIR / "_live_install_markers"
LIVE_INSTALL_DECISION_RELATIVE_DIR = LIVE_INSTALL_APPROVAL_RELATIVE_DIR / "_decisions"
ROLLBACK_APPROVAL_RELATIVE_DIR = Path("07_LOGS") / "Agent-Activity" / "_forge_rollback_approvals"
ROLLBACK_MARKER_RELATIVE_DIR = ROLLBACK_APPROVAL_RELATIVE_DIR / "_rollback_markers"
ROLLBACK_DECISION_RELATIVE_DIR = ROLLBACK_APPROVAL_RELATIVE_DIR / "_decisions"
DEMO_MANIFEST_PATH = Path(__file__).with_name("examples") / "ugc_campaign_studio.manifest.json"

FORGE_APPROVAL_DECISION_FAMILY_SPECS: dict[str, dict[str, Any]] = {
    "sandbox": {
        "decision_root": SANDBOX_DECISION_RELATIVE_DIR,
        "record_type": SANDBOX_APPROVAL_RECORD_TYPE,
        "schema_version": SANDBOX_APPROVAL_SCHEMA_VERSION,
        "scope": SANDBOX_APPROVAL_SCOPE,
    },
    "live-install": {
        "decision_root": LIVE_INSTALL_DECISION_RELATIVE_DIR,
        "record_type": LIVE_INSTALL_APPROVAL_RECORD_TYPE,
        "schema_version": LIVE_INSTALL_APPROVAL_SCHEMA_VERSION,
        "scope": LIVE_INSTALL_APPROVAL_SCOPE,
    },
    "rollback": {
        "decision_root": ROLLBACK_DECISION_RELATIVE_DIR,
        "record_type": ROLLBACK_APPROVAL_RECORD_TYPE,
        "schema_version": ROLLBACK_APPROVAL_SCHEMA_VERSION,
        "scope": ROLLBACK_APPROVAL_SCOPE,
    },
}

BLOCKED_AUTHORITY = {
    "writes_extension_registry": False,
    "writes_extension_files": False,
    "executes_sandbox_install": False,
    "executes_live_install": False,
    "executes_rollback": False,
    "consumes_approval": False,
    "reserves_exact_once_marker": False,
    "mutates_protected_core": False,
    "mutates_studio_shell": False,
    "mutates_runtime_policy": False,
    "activates_schedule": False,
    "writes_agent_bus_task": False,
    "reads_secret_or_credential": False,
    "calls_provider_or_model": False,
    "calls_external_connector": False,
    "canonical_mutation_allowed": False,
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative_to_vault(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _safe_identifier(value: str) -> str:
    safe = "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
    return safe or "forge-request"


def _safe_json_path(vault: Path, base_relative: Path, identifier: str) -> Path:
    base = (vault / base_relative).resolve()
    path = (base / f"{_safe_identifier(identifier)}.json").resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"Forge approval path escapes base directory: {path}") from exc
    return path


def _resolve_under_base(vault: Path, path_value: str | Path, base_relative: Path) -> tuple[Path | None, str | None]:
    base = (vault / base_relative).resolve()
    raw = Path(path_value)
    path = raw.resolve() if raw.is_absolute() else (vault / raw).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        return None, "path_outside_allowed_forge_base"
    return path, None


def _resolve_artifact_path(value: str | Path | None) -> Path | None:
    if value in (None, ""):
        return None
    return Path(value).resolve()


def _resolve_vault_path_value(vault: Path, value: str | Path | None) -> Path | None:
    if value in (None, ""):
        return None
    raw = Path(str(value))
    return raw.resolve() if raw.is_absolute() else (vault / raw).resolve()


def _path_value_matches_vault_path(vault: Path, value: str | Path | None, expected: Path) -> bool:
    resolved = _resolve_vault_path_value(vault, value)
    return bool(resolved and resolved == expected.resolve())


def load_demo_manifest() -> dict[str, Any]:
    return json.loads(DEMO_MANIFEST_PATH.read_text(encoding="utf-8"))


def _extension_point_summary(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for point in manifest.get("extensionPoints") or []:
        if not isinstance(point, dict):
            continue
        points.append(
            {
                "id": point.get("id"),
                "type": point.get("type"),
                "label": point.get("label") or point.get("title") or point.get("name"),
                "route": point.get("route"),
                "permissions": list(point.get("permissions") or []),
            }
        )
    return points


def build_registry_entry(
    manifest: dict[str, Any],
    validation: dict[str, Any] | None = None,
    *,
    registry_status: str = "pending_sandbox_approval",
    install_environment: str = "sandbox",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a registry entry preview without writing the registry."""

    manifest_copy = deepcopy(manifest)
    validation_result = validation or validate_manifest(manifest_copy)
    path_guard = (validation_result.get("protectedCore") or {}).get("targetPathValidation") or {}
    manifest_digest = _sha256_payload(manifest_copy)
    return {
        "schema_version": REGISTRY_ENTRY_SCHEMA_VERSION,
        "extension_id": manifest_copy.get("id"),
        "name": manifest_copy.get("name"),
        "description": manifest_copy.get("description"),
        "version": manifest_copy.get("version"),
        "manifest_status": manifest_copy.get("status"),
        "registry_status": registry_status,
        "install_environment": install_environment,
        "manifest_digest_sha256": manifest_digest,
        "validation_status": validation_result.get("status"),
        "validation_valid": bool(validation_result.get("valid")),
        "target_paths": list(path_guard.get("normalized_paths") or []),
        "extension_points": _extension_point_summary(manifest_copy),
        "permissions": list(manifest_copy.get("permissions") or []),
        "required_approvals": list(validation_result.get("requiredApprovals") or []),
        "rollback": deepcopy(manifest_copy.get("rollback") or {}),
        "created_by": deepcopy(manifest_copy.get("createdBy") or {}),
        "registered_at": generated_at or _now_utc(),
        "authority": dict(BLOCKED_AUTHORITY),
    }


def build_extension_registry(vault_root: str | Path) -> dict[str, Any]:
    """Return the Forge extension registry read model without writing it."""

    vault = _vault_path(vault_root)
    registry_path = (vault / REGISTRY_RELATIVE_PATH).resolve()
    payload = _read_json(registry_path) if registry_path.is_file() else None
    blockers: list[str] = []
    entries: list[dict[str, Any]] = []
    if payload is None and registry_path.exists():
        blockers.append("registry_json_unreadable")
    elif payload:
        if payload.get("schema_version") != MODEL_VERSION:
            blockers.append("registry_schema_version_unsupported")
        raw_entries = payload.get("entries")
        if not isinstance(raw_entries, list):
            blockers.append("registry_entries_not_list")
        else:
            entries = [entry for entry in raw_entries if isinstance(entry, dict)]

    return {
        "ok": not blockers,
        "surface": REGISTRY_SURFACE_ID,
        "model_version": MODEL_VERSION,
        "status": "registry_ready" if not blockers else "blocked_registry_read",
        "generated_at": _now_utc(),
        "vault_root": str(vault),
        "registry_path": _relative_to_vault(vault, registry_path),
        "registry_exists": registry_path.is_file(),
        "entry_count": len(entries),
        "entries": entries,
        "write_policy": {
            "generated_extensions_may_write_registry_directly": False,
            "sandbox_registry_write_requires_approval": True,
            "live_install_approval_packet_requires_sandbox_proof": True,
            "live_registry_write_requires_separate_approval": True,
            "rollback_approval_packet_requires_live_proof": True,
            "rollback_registry_write_requires_separate_approval": True,
            "approved_sandbox_registry_writer_built": True,
            "live_install_approval_packet_built": True,
            "approved_live_install_executor_built": True,
            "rollback_approval_packet_built": True,
            "approved_rollback_executor_built": True,
            "registry_writer_built": True,
        },
        "authority": dict(BLOCKED_AUTHORITY),
        "blockers": blockers,
    }


def _sandbox_material(manifest: dict[str, Any], validation: dict[str, Any], registry_entry: dict[str, Any]) -> dict[str, Any]:
    path_guard = (validation.get("protectedCore") or {}).get("targetPathValidation") or {}
    stable_registry_entry = deepcopy(registry_entry)
    stable_registry_entry.pop("registered_at", None)
    return {
        "schema_version": "forge.sandbox_approval.material.v1",
        "requested_action": "request_forge_sandbox_install",
        "extension_id": manifest.get("id"),
        "extension_name": manifest.get("name"),
        "extension_version": manifest.get("version"),
        "manifest_digest_sha256": registry_entry.get("manifest_digest_sha256"),
        "validation_status": validation.get("status"),
        "target_paths": list(path_guard.get("normalized_paths") or []),
        "registry_entry_preview": stable_registry_entry,
        "approval_effect": "authorizes one future sandbox registry write and extension-owned root write attempt only after a separate approved executor revalidates the manifest",
        "direct_core_mutation_allowed": False,
    }


def _operator_confirmation_text(extension_id: str, target_paths: list[str]) -> str:
    lines = [
        "APPROVE FORGE SANDBOX INSTALL REQUEST ONLY:",
        f"- extension_id: {extension_id}",
        "- environment: sandbox",
        "- future executor must revalidate manifest digest and target paths",
        "- future writes are limited to extension-owned roots plus Forge registry metadata",
        "",
        "Target paths:",
        *[f"- {path}" for path in target_paths],
        "",
        "No live install.",
        "No protected-core writes.",
        "No Studio shell patch.",
        "No runtime policy, schedule, Agent Bus, provider, credential, or canonical mutation.",
    ]
    return "\n".join(lines)


def _approval_artifact_payload(
    *,
    packet_id: str,
    request_digest: str,
    material: dict[str, Any],
    approval_path: Path,
    marker_path: Path,
    registry_path: Path,
    requested_by: str,
    generated_at: str,
) -> dict[str, Any]:
    extension_id = str(material.get("extension_id") or "")
    target_paths = list(material.get("target_paths") or [])
    return {
        "record_type": SANDBOX_APPROVAL_RECORD_TYPE,
        "schema_version": SANDBOX_APPROVAL_SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": "pending_operator_decision",
        "approval_packet_id": packet_id,
        "request_digest_sha256": request_digest,
        "operator_decision": "pending",
        "approval_scope": SANDBOX_APPROVAL_SCOPE,
        "requested_by": requested_by,
        "extension_id": extension_id,
        "extension_name": material.get("extension_name"),
        "extension_version": material.get("extension_version"),
        "approval_artifact_path": str(approval_path),
        "future_exact_once_marker_path": str(marker_path),
        "future_registry_path": str(registry_path),
        "future_extension_target_paths": target_paths,
        "operator_confirmation_text": _operator_confirmation_text(extension_id, target_paths),
        "approved_material": material,
        "future_executor_requirements": [
            "operator_decision must be approved in this artifact",
            "approval_packet_id and request_digest_sha256 must match",
            "manifest digest must be revalidated before any write",
            "target paths must be revalidated by the protected-core guard",
            "executor must reserve exact-once marker before registry or extension-owned writes",
            "executor must write registry metadata and extension-owned files only",
            "live install requires a separate live-install approval artifact",
        ],
        "approval_consumed": False,
        "sandbox_install_allowed_in_this_pass": False,
        "live_install_allowed_in_this_pass": False,
        "registry_write_allowed_in_this_pass": False,
        "extension_file_write_allowed_in_this_pass": False,
        **BLOCKED_AUTHORITY,
    }


def _approval_matches(payload: dict[str, Any] | None, packet_id: str, request_digest: str) -> bool:
    return bool(
        payload
        and payload.get("record_type") == SANDBOX_APPROVAL_RECORD_TYPE
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest_sha256") == request_digest
        and payload.get("status") == "pending_operator_decision"
        and payload.get("operator_decision") == "pending"
        and payload.get("approval_scope") == SANDBOX_APPROVAL_SCOPE
        and payload.get("sandbox_install_allowed_in_this_pass") is False
        and payload.get("live_install_allowed_in_this_pass") is False
    )


def build_sandbox_install_approval(
    vault_root: str | Path,
    *,
    manifest: dict[str, Any] | None = None,
    approval_packet_id: str | None = None,
    request_digest: str | None = None,
    write_approval_request: bool = False,
    requested_by: str = "Codex",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or optionally write a digest-gated Forge sandbox approval request.

    This surface never writes the Forge registry, never writes extension files,
    and never consumes an approval decision.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    manifest_payload = deepcopy(manifest) if manifest is not None else load_demo_manifest()
    validation = validate_manifest(manifest_payload)
    registry = build_extension_registry(vault)
    registry_entry = build_registry_entry(manifest_payload, validation, generated_at=timestamp)
    material = _sandbox_material(manifest_payload, validation, registry_entry)
    digest = _sha256_payload(material)
    extension_id = str(manifest_payload.get("id") or "invalid-extension")
    packet_id = approval_packet_id or f"forge-sandbox-appr-{_safe_identifier(extension_id)}-{digest[:12]}"
    approval_path = _safe_json_path(vault, SANDBOX_APPROVAL_RELATIVE_DIR, packet_id)
    marker_path = _safe_json_path(vault, SANDBOX_MARKER_RELATIVE_DIR, packet_id)
    registry_path = (vault / REGISTRY_RELATIVE_PATH).resolve()
    existing_payload = _read_json(approval_path) if approval_path.is_file() else None
    existing_matches = _approval_matches(existing_payload, packet_id, digest)
    approval_preview = _approval_artifact_payload(
        packet_id=packet_id,
        request_digest=digest,
        material=material,
        approval_path=approval_path,
        marker_path=marker_path,
        registry_path=registry_path,
        requested_by=requested_by,
        generated_at=timestamp,
    )

    blockers: list[str] = []
    if not validation.get("valid"):
        blockers.append("manifest_validation_blocked")
    blockers.extend(str(issue.get("code") or "validation_issue") for issue in validation.get("errors") or [])
    if not registry.get("ok"):
        blockers.extend(str(item) for item in registry.get("blockers") or [])
    if marker_path.exists():
        blockers.append("sandbox_exact_once_marker_already_present")
    if approval_path.exists() and not existing_matches:
        blockers.append("existing_sandbox_approval_artifact_mismatch")
    if write_approval_request and request_digest != digest:
        blockers.append("request_digest_required_or_mismatched")

    approval_written = False
    approval_reused = False
    if write_approval_request and not blockers:
        if existing_matches:
            approval_reused = True
        else:
            approval_path.parent.mkdir(parents=True, exist_ok=True)
            approval_path.write_text(json.dumps(approval_preview, indent=2, default=str) + "\n", encoding="utf-8")
            approval_written = True

    approval_present = approval_path.is_file()
    ready_for_operator_decision = not blockers
    status = (
        "forge_sandbox_approval_request_written"
        if approval_written
        else "forge_sandbox_approval_request_existing_matching"
        if approval_reused or existing_matches
        else "forge_sandbox_approval_request_ready"
        if ready_for_operator_decision
        else "blocked_forge_sandbox_approval_request"
    )

    return {
        "ok": ready_for_operator_decision,
        "surface": SANDBOX_APPROVAL_SURFACE_ID,
        "model_version": SANDBOX_APPROVAL_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not approval_written,
        "approval_request_write_requested": write_approval_request,
        "approval_request_written": approval_written,
        "approval_request_reused": approval_reused,
        "approval_packet_id": packet_id,
        "request_digest_sha256": digest,
        "approval_artifact_path": _relative_to_vault(vault, approval_path),
        "approval_artifact_exists": approval_present,
        "approval_artifact_preview": approval_preview,
        "operator_confirmation_text": approval_preview["operator_confirmation_text"],
        "registry": registry,
        "registry_entry_preview": registry_entry,
        "future_registry_path": _relative_to_vault(vault, registry_path),
        "future_exact_once_marker_path": _relative_to_vault(vault, marker_path),
        "manifest_validation": validation,
        "authority": {
            **dict(BLOCKED_AUTHORITY),
            "approval_request_write_requested": write_approval_request,
            "writes_approval_artifact": approval_written,
            "approval_request_surface_only": True,
            "sandbox_registry_write_allowed_after_future_approval": True,
            "live_install_requires_separate_approval": True,
        },
        "blockers": list(dict.fromkeys(blockers)),
        "next_recommended_pass": (
            "chaser-forge-sandbox-approved-registry-writer"
            if ready_for_operator_decision
            else "chaser-forge-sandbox-approval-repair"
        ),
    }


def _registry_entry_for_extension(registry: dict[str, Any], extension_id: str) -> dict[str, Any] | None:
    for entry in registry.get("entries") or []:
        if isinstance(entry, dict) and entry.get("extension_id") == extension_id:
            return entry
    return None


def _repo_relative_path(vault: Path, repo_path: str) -> tuple[Path | None, str | None]:
    path = (vault / repo_path).resolve()
    try:
        path.relative_to(vault.resolve())
    except ValueError:
        return None, "path_outside_vault"
    return path, None


def _sandbox_marker_payload(vault: Path, registry_entry: dict[str, Any]) -> tuple[Path | None, dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    sandbox_execution = registry_entry.get("sandbox_execution")
    if not isinstance(sandbox_execution, dict):
        return None, None, ["sandbox_execution_metadata_missing"]

    marker_path_value = sandbox_execution.get("exact_once_marker_path")
    if not marker_path_value:
        return None, None, ["sandbox_exact_once_marker_path_missing"]

    marker_path, path_blocker = _repo_relative_path(vault, str(marker_path_value))
    if path_blocker:
        return None, None, ["sandbox_exact_once_marker_path_outside_vault"]
    if marker_path is None or not marker_path.is_file():
        return marker_path, None, ["sandbox_exact_once_marker_missing"]

    payload = _read_json(marker_path)
    if payload is None:
        blockers.append("sandbox_exact_once_marker_unreadable")
    return marker_path, payload, blockers


def _live_material(
    *,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    sandbox_registry_entry: dict[str, Any] | None,
    sandbox_marker_path: Path | None,
    target_paths: list[str],
) -> dict[str, Any]:
    registry_entry = deepcopy(sandbox_registry_entry or {})
    sandbox_execution = deepcopy(registry_entry.get("sandbox_execution") or {})
    return {
        "schema_version": "forge.live_install_approval.material.v1",
        "requested_action": "request_forge_live_install",
        "extension_id": manifest.get("id"),
        "extension_name": manifest.get("name"),
        "extension_version": manifest.get("version"),
        "manifest_digest_sha256": _sha256_payload(deepcopy(manifest)),
        "validation_status": validation.get("status"),
        "sandbox_registry_entry_digest_sha256": _sha256_payload(registry_entry) if registry_entry else "",
        "sandbox_registry_status": registry_entry.get("registry_status"),
        "sandbox_install_environment": registry_entry.get("install_environment"),
        "sandbox_execution": sandbox_execution,
        "sandbox_exact_once_marker_path": str(sandbox_marker_path) if sandbox_marker_path else "",
        "target_paths": target_paths,
        "rollback": deepcopy(manifest.get("rollback") or {}),
        "approval_effect": (
            "authorizes one future live install executor attempt only after a separate executor "
            "revalidates the manifest, sandbox registry entry, sandbox marker, target files, "
            "approval digest, and exact-once live marker state"
        ),
        "live_executor_requirements": [
            "operator_decision must be approved in this artifact",
            "approval_packet_id and request_digest_sha256 must match",
            "sandbox registry entry must still be sandbox_installed",
            "sandbox exact-once marker must still be completed and match the registry entry",
            "extension-owned target files must still exist and match the manifest target set",
            "executor must reserve a separate live exact-once marker before any live-state mutation",
            "live install must not grant generated extensions protected-core mutation authority",
        ],
        "direct_core_mutation_allowed": False,
        "generated_extension_registry_write_allowed": False,
    }


def _live_operator_confirmation_text(extension_id: str, target_paths: list[str]) -> str:
    lines = [
        "APPROVE FORGE LIVE INSTALL REQUEST ONLY:",
        f"- extension_id: {extension_id}",
        "- environment: live",
        "- sandbox proof must remain valid at execution time",
        "- future live executor must revalidate manifest digest, registry entry, marker, and target paths",
        "- future live writes require a separate exact-once live marker",
        "",
        "Target paths:",
        *[f"- {path}" for path in target_paths],
        "",
        "No live install is executed by this approval request.",
        "No protected-core writes.",
        "No Studio shell patch.",
        "No runtime policy, schedule, Agent Bus, provider, credential, external connector, or canonical mutation.",
    ]
    return "\n".join(lines)


def _live_approval_artifact_payload(
    *,
    packet_id: str,
    request_digest: str,
    material: dict[str, Any],
    approval_path: Path,
    marker_path: Path,
    registry_path: Path,
    requested_by: str,
    generated_at: str,
) -> dict[str, Any]:
    extension_id = str(material.get("extension_id") or "")
    target_paths = list(material.get("target_paths") or [])
    return {
        "record_type": LIVE_INSTALL_APPROVAL_RECORD_TYPE,
        "schema_version": LIVE_INSTALL_APPROVAL_SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": "pending_operator_decision",
        "approval_packet_id": packet_id,
        "request_digest_sha256": request_digest,
        "operator_decision": "pending",
        "approval_scope": LIVE_INSTALL_APPROVAL_SCOPE,
        "requested_by": requested_by,
        "extension_id": extension_id,
        "extension_name": material.get("extension_name"),
        "extension_version": material.get("extension_version"),
        "approval_artifact_path": str(approval_path),
        "future_live_exact_once_marker_path": str(marker_path),
        "future_registry_path": str(registry_path),
        "future_extension_target_paths": target_paths,
        "operator_confirmation_text": _live_operator_confirmation_text(extension_id, target_paths),
        "approved_material": material,
        "future_executor_requirements": list(material.get("live_executor_requirements") or []),
        "approval_consumed": False,
        "sandbox_install_allowed_in_this_pass": False,
        "live_install_allowed_in_this_pass": False,
        "live_install_executor_built": False,
        "registry_write_allowed_in_this_pass": False,
        "extension_file_write_allowed_in_this_pass": False,
        **BLOCKED_AUTHORITY,
    }


def _live_approval_matches(payload: dict[str, Any] | None, packet_id: str, request_digest: str) -> bool:
    return bool(
        payload
        and payload.get("record_type") == LIVE_INSTALL_APPROVAL_RECORD_TYPE
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest_sha256") == request_digest
        and payload.get("status") == "pending_operator_decision"
        and payload.get("operator_decision") == "pending"
        and payload.get("approval_scope") == LIVE_INSTALL_APPROVAL_SCOPE
        and payload.get("approval_consumed") is False
        and payload.get("live_install_allowed_in_this_pass") is False
        and payload.get("live_install_executor_built") is False
    )


def _sandbox_proof_blockers(
    *,
    vault: Path,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    registry: dict[str, Any],
    registry_entry: dict[str, Any] | None,
    sandbox_marker_payload: dict[str, Any] | None,
    target_paths: list[str],
) -> list[str]:
    blockers: list[str] = []
    extension_id = str(manifest.get("id") or "")
    manifest_digest = _sha256_payload(deepcopy(manifest))
    if registry_entry is None:
        return ["sandbox_registry_entry_missing"]

    if registry_entry.get("registry_status") != "sandbox_installed":
        blockers.append("sandbox_registry_entry_not_installed")
    if registry_entry.get("install_environment") != "sandbox":
        blockers.append("sandbox_registry_entry_environment_mismatch")
    if registry_entry.get("manifest_digest_sha256") != manifest_digest:
        blockers.append("sandbox_registry_entry_manifest_digest_mismatch")
    if registry_entry.get("validation_valid") is not True:
        blockers.append("sandbox_registry_entry_validation_not_valid")

    sandbox_execution = registry_entry.get("sandbox_execution")
    if not isinstance(sandbox_execution, dict):
        blockers.append("sandbox_execution_metadata_missing")
    else:
        if sandbox_execution.get("approval_packet_id") in (None, ""):
            blockers.append("sandbox_execution_approval_packet_missing")
        if sandbox_execution.get("request_digest_sha256") in (None, ""):
            blockers.append("sandbox_execution_request_digest_missing")
        if sandbox_execution.get("live_install") is not False:
            blockers.append("sandbox_execution_live_install_unexpected")

    if sandbox_marker_payload is None:
        blockers.append("sandbox_exact_once_marker_missing")
    else:
        if sandbox_marker_payload.get("record_type") != SANDBOX_REGISTRY_WRITE_MARKER_RECORD_TYPE:
            blockers.append("sandbox_marker_record_type_mismatch")
        if sandbox_marker_payload.get("schema_version") != SANDBOX_REGISTRY_WRITE_SCHEMA_VERSION:
            blockers.append("sandbox_marker_schema_version_mismatch")
        if sandbox_marker_payload.get("completed") is not True:
            blockers.append("sandbox_marker_not_completed")
        if sandbox_marker_payload.get("extension_id") != extension_id:
            blockers.append("sandbox_marker_extension_id_mismatch")
        if isinstance(sandbox_execution, dict):
            if sandbox_marker_payload.get("approval_packet_id") != sandbox_execution.get("approval_packet_id"):
                blockers.append("sandbox_marker_approval_packet_mismatch")
            if sandbox_marker_payload.get("request_digest_sha256") != sandbox_execution.get("request_digest_sha256"):
                blockers.append("sandbox_marker_request_digest_mismatch")

    registry_target_paths = list(registry_entry.get("target_paths") or [])
    if registry_target_paths != target_paths:
        blockers.append("sandbox_registry_entry_target_paths_mismatch")

    missing_target_paths: list[str] = []
    for repo_path in target_paths:
        target_path, path_blocker = _repo_relative_path(vault, repo_path)
        if path_blocker:
            blockers.append("extension_target_path_outside_vault")
        elif target_path is not None and not target_path.is_file():
            missing_target_paths.append(repo_path)
    if missing_target_paths:
        blockers.append("extension_target_missing")

    if not registry.get("ok"):
        blockers.extend(str(item) for item in registry.get("blockers") or [])
    if not validation.get("valid"):
        blockers.append("manifest_validation_blocked")
    blockers.extend(str(issue.get("code") or "validation_issue") for issue in validation.get("errors") or [])
    return blockers


def build_live_install_approval(
    vault_root: str | Path,
    *,
    manifest: dict[str, Any] | None = None,
    approval_packet_id: str | None = None,
    request_digest: str | None = None,
    write_approval_request: bool = False,
    requested_by: str = "Codex",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or optionally write a Forge live-install approval request.

    This surface is request-only. It requires an existing sandbox registry entry,
    completed sandbox marker, and extension-owned target files before it can
    write a pending live approval artifact. It never executes a live install.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    manifest_payload = deepcopy(manifest) if manifest is not None else load_demo_manifest()
    validation = validate_manifest(manifest_payload)
    path_guard = (validation.get("protectedCore") or {}).get("targetPathValidation") or {}
    target_paths = list(path_guard.get("normalized_paths") or [])
    extension_id = str(manifest_payload.get("id") or "invalid-extension")
    registry = build_extension_registry(vault)
    sandbox_registry_entry = _registry_entry_for_extension(registry, extension_id)
    sandbox_marker_path, sandbox_marker, marker_blockers = _sandbox_marker_payload(vault, sandbox_registry_entry or {})
    material = _live_material(
        manifest=manifest_payload,
        validation=validation,
        sandbox_registry_entry=sandbox_registry_entry,
        sandbox_marker_path=sandbox_marker_path,
        target_paths=target_paths,
    )
    digest = _sha256_payload(material)
    packet_id = approval_packet_id or f"forge-live-install-appr-{_safe_identifier(extension_id)}-{digest[:12]}"
    approval_path = _safe_json_path(vault, LIVE_INSTALL_APPROVAL_RELATIVE_DIR, packet_id)
    marker_path = _safe_json_path(vault, LIVE_INSTALL_MARKER_RELATIVE_DIR, packet_id)
    registry_path = (vault / REGISTRY_RELATIVE_PATH).resolve()
    existing_payload = _read_json(approval_path) if approval_path.is_file() else None
    existing_matches = _live_approval_matches(existing_payload, packet_id, digest)
    approval_preview = _live_approval_artifact_payload(
        packet_id=packet_id,
        request_digest=digest,
        material=material,
        approval_path=approval_path,
        marker_path=marker_path,
        registry_path=registry_path,
        requested_by=requested_by,
        generated_at=timestamp,
    )

    blockers = _sandbox_proof_blockers(
        vault=vault,
        manifest=manifest_payload,
        validation=validation,
        registry=registry,
        registry_entry=sandbox_registry_entry,
        sandbox_marker_payload=sandbox_marker,
        target_paths=target_paths,
    )
    blockers.extend(marker_blockers)
    if marker_path.exists():
        blockers.append("live_install_exact_once_marker_already_present")
    if approval_path.exists() and not existing_matches:
        blockers.append("existing_live_install_approval_artifact_mismatch")
    if write_approval_request and request_digest != digest:
        blockers.append("request_digest_required_or_mismatched")
    blockers = list(dict.fromkeys(blockers))

    approval_written = False
    approval_reused = False
    if write_approval_request and not blockers:
        if existing_matches:
            approval_reused = True
        else:
            approval_path.parent.mkdir(parents=True, exist_ok=True)
            approval_path.write_text(json.dumps(approval_preview, indent=2, default=str) + "\n", encoding="utf-8")
            approval_written = True

    approval_present = approval_path.is_file()
    ready_for_operator_decision = not blockers
    status = (
        "forge_live_install_approval_request_written"
        if approval_written
        else "forge_live_install_approval_request_existing_matching"
        if approval_reused or existing_matches
        else "forge_live_install_approval_request_ready"
        if ready_for_operator_decision
        else "blocked_forge_live_install_approval_request"
    )

    return {
        "ok": ready_for_operator_decision,
        "surface": LIVE_INSTALL_APPROVAL_SURFACE_ID,
        "model_version": LIVE_INSTALL_APPROVAL_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not approval_written,
        "approval_request_write_requested": write_approval_request,
        "approval_request_written": approval_written,
        "approval_request_reused": approval_reused,
        "approval_packet_id": packet_id,
        "request_digest_sha256": digest,
        "approval_artifact_path": _relative_to_vault(vault, approval_path),
        "approval_artifact_exists": approval_present,
        "approval_artifact_preview": approval_preview,
        "operator_confirmation_text": approval_preview["operator_confirmation_text"],
        "registry": registry,
        "sandbox_registry_entry": sandbox_registry_entry or {},
        "sandbox_exact_once_marker_path": _relative_to_vault(vault, sandbox_marker_path) if sandbox_marker_path else "",
        "sandbox_exact_once_marker_exists": bool(sandbox_marker_path and sandbox_marker_path.is_file()),
        "future_registry_path": _relative_to_vault(vault, registry_path),
        "future_live_exact_once_marker_path": _relative_to_vault(vault, marker_path),
        "future_extension_target_paths": target_paths,
        "manifest_validation": validation,
        "authority": {
            **dict(BLOCKED_AUTHORITY),
            "approval_request_write_requested": write_approval_request,
            "writes_approval_artifact": approval_written,
            "live_install_approval_request_surface_only": True,
            "live_install_executor_built": False,
            "live_install_allowed_in_this_pass": False,
            "live_install_requires_future_approved_executor": True,
        },
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-live-install-executor"
            if ready_for_operator_decision
            else "chaser-forge-sandbox-approved-registry-writer"
        ),
    }


def _empty_registry_payload(generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": MODEL_VERSION,
        "status": "sandbox_registry_ready",
        "generated_extensions_may_write_registry_directly": False,
        "sandbox_registry_write_requires_approval": True,
        "live_install_approval_packet_requires_sandbox_proof": True,
        "live_registry_write_requires_separate_approval": True,
        "rollback_approval_packet_requires_live_proof": True,
        "rollback_registry_write_requires_separate_approval": True,
        "live_install_approval_packet_built": True,
        "approved_live_install_executor_built": True,
        "rollback_approval_packet_built": True,
        "approved_rollback_executor_built": True,
        "created_at": generated_at,
        "updated_at": generated_at,
        "entries": [],
    }


def _load_registry_for_write(registry_path: Path, generated_at: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not registry_path.exists():
        return _empty_registry_payload(generated_at), []
    payload = _read_json(registry_path)
    if payload is None:
        return None, ["registry_json_unreadable"]
    blockers: list[str] = []
    if payload.get("schema_version") != MODEL_VERSION:
        blockers.append("registry_schema_version_unsupported")
    if not isinstance(payload.get("entries"), list):
        blockers.append("registry_entries_not_list")
    return payload, blockers


def _sandbox_extension_file_payload(
    *,
    manifest: dict[str, Any],
    repo_path: str,
    approval_packet_id: str,
    request_digest: str,
    generated_at: str,
) -> dict[str, Any]:
    extension_id = str(manifest.get("id") or "")
    common = {
        "schema_version": "forge.sandbox_extension_file.v1",
        "generated_at": generated_at,
        "install_environment": "sandbox",
        "extension_id": extension_id,
        "approval_packet_id": approval_packet_id,
        "request_digest_sha256": request_digest,
        "live_install": False,
        "protected_core_mutation": False,
    }
    if repo_path.endswith("/manifest.json"):
        return {
            **common,
            "file_kind": "manifest",
            "manifest": deepcopy(manifest),
        }
    if "/ui/" in repo_path:
        return {
            **common,
            "file_kind": "ui",
            "ui": deepcopy(manifest.get("ui") or {}),
            "extension_points": [
                deepcopy(point)
                for point in manifest.get("extensionPoints") or []
                if isinstance(point, dict) and point.get("type") in {"sidebar.nav.item", "workspace.page", "dashboard.widget"}
            ],
        }
    if "/workflows/" in repo_path:
        return {
            **common,
            "file_kind": "workflow",
            "workflows": deepcopy(manifest.get("workflows") or []),
            "approval_required": True,
        }
    return {
        **common,
        "file_kind": "generic",
        "source_manifest_id": extension_id,
    }


def _expected_artifact_paths(
    vault: Path,
    packet_id: str,
    approval_artifact_path: str | Path | None,
) -> tuple[Path | None, Path, Path, list[str]]:
    blockers: list[str] = []
    default_approval_path = _safe_json_path(vault, SANDBOX_APPROVAL_RELATIVE_DIR, packet_id)
    marker_path = _safe_json_path(vault, SANDBOX_MARKER_RELATIVE_DIR, packet_id)
    registry_path = (vault / REGISTRY_RELATIVE_PATH).resolve()
    approval_path = default_approval_path
    if approval_artifact_path:
        resolved, blocker = _resolve_under_base(vault, approval_artifact_path, SANDBOX_APPROVAL_RELATIVE_DIR)
        if blocker:
            blockers.append("approval_artifact_path_outside_sandbox_approval_root")
            approval_path = None
        else:
            approval_path = resolved
    return approval_path, marker_path, registry_path, blockers


def _path_matches_expected(path_value: str | None, expected: Path) -> bool:
    resolved = _resolve_artifact_path(path_value)
    return bool(resolved and resolved == expected.resolve())


def _approval_decision_sidecar_blockers(
    *,
    vault: Path,
    approval_path: Path,
    approval_payload: dict[str, Any],
    family_id: str,
    packet_id: str,
    request_digest: str,
) -> list[str]:
    spec = FORGE_APPROVAL_DECISION_FAMILY_SPECS[family_id]
    blockers: list[str] = []
    if approval_payload.get("approval_decision_recorded") is not True:
        blockers.append("approval_decision_record_missing")
    if approval_payload.get("approval_decision_family") != family_id:
        blockers.append("approval_decision_family_mismatch")
    if approval_payload.get("approval_decision_record_type") != FORGE_APPROVAL_DECISION_RECORD_TYPE:
        blockers.append("approval_decision_record_type_mismatch")

    source_decision_digest = str(approval_payload.get("approval_decision_digest_sha256") or "")
    if not source_decision_digest:
        blockers.append("approval_decision_digest_missing")

    handoff = approval_payload.get("approval_decision_handoff")
    if not isinstance(handoff, dict):
        blockers.append("approval_decision_handoff_metadata_missing")
    else:
        if handoff.get("surface") != FORGE_APPROVAL_DECISION_SURFACE_ID:
            blockers.append("approval_decision_handoff_surface_mismatch")
        if handoff.get("api_method") != FORGE_APPROVAL_DECISION_API_METHOD:
            blockers.append("approval_decision_handoff_api_method_mismatch")
        if handoff.get("source_specific") is not True:
            blockers.append("approval_decision_handoff_not_source_specific")
        if handoff.get("generic_approval_center_control") is not False:
            blockers.append("approval_decision_handoff_generic_control_unexpected")
        if handoff.get("approval_consumed") is not False:
            blockers.append("approval_decision_handoff_consumed_unexpected")
        if handoff.get("forge_execution_allowed") is not False:
            blockers.append("approval_decision_handoff_execution_unexpected")
        if source_decision_digest and handoff.get("decision_record_digest_sha256") != source_decision_digest:
            blockers.append("approval_decision_handoff_digest_mismatch")

    decision_path_value = approval_payload.get("decision_artifact_path")
    if not decision_path_value:
        blockers.append("approval_decision_artifact_path_missing")
        return blockers

    decision_root = (vault / spec["decision_root"]).resolve()
    decision_path = _resolve_vault_path_value(vault, decision_path_value)
    if decision_path is None:
        blockers.append("approval_decision_artifact_path_missing")
        return blockers
    try:
        decision_relative = decision_path.relative_to(decision_root)
    except ValueError:
        blockers.append("approval_decision_artifact_path_outside_decision_root")
        decision_relative = None
    if decision_relative is not None and (len(decision_relative.parts) != 1 or decision_path.suffix.lower() != ".json"):
        blockers.append("approval_decision_artifact_path_not_direct_json")
    if not decision_path.is_file():
        blockers.append("approval_decision_artifact_missing")
        return blockers

    decision_payload = _read_json(decision_path)
    if decision_payload is None:
        blockers.append("approval_decision_artifact_unreadable")
        return blockers

    decision_record_digest = str(decision_payload.get("decision_record_digest_sha256") or "")
    if not decision_record_digest:
        blockers.append("approval_decision_digest_missing")
    elif source_decision_digest and decision_record_digest != source_decision_digest:
        blockers.append("approval_decision_source_digest_mismatch")
    recompute_payload = dict(decision_payload)
    recompute_payload.pop("decision_record_digest_sha256", None)
    if decision_record_digest and _sha256_payload(recompute_payload) != decision_record_digest:
        blockers.append("approval_decision_digest_mismatch")

    if decision_payload.get("record_type") != FORGE_APPROVAL_DECISION_RECORD_TYPE:
        blockers.append("approval_decision_artifact_record_type_mismatch")
    if decision_payload.get("schema_version") != FORGE_APPROVAL_DECISION_SCHEMA_VERSION:
        blockers.append("approval_decision_artifact_schema_version_mismatch")
    if decision_payload.get("status") != "forge_approval_decision_recorded":
        blockers.append("approval_decision_artifact_status_mismatch")
    if decision_payload.get("surface") != FORGE_APPROVAL_DECISION_SURFACE_ID:
        blockers.append("approval_decision_artifact_surface_mismatch")
    if decision_payload.get("api_method") != FORGE_APPROVAL_DECISION_API_METHOD:
        blockers.append("approval_decision_artifact_api_method_mismatch")
    if decision_payload.get("source_specific") is not True:
        blockers.append("approval_decision_artifact_not_source_specific")
    if decision_payload.get("generic_approval_center_control") is not False:
        blockers.append("approval_decision_artifact_generic_control_unexpected")
    if decision_payload.get("family") != family_id:
        blockers.append("approval_decision_artifact_family_mismatch")
    if decision_payload.get("operator_decision") != "approved":
        blockers.append("approval_decision_not_approved")
    if decision_payload.get("approval_packet_id") != packet_id:
        blockers.append("approval_decision_packet_id_mismatch")
    if decision_payload.get("request_digest_sha256") != request_digest:
        blockers.append("approval_decision_request_digest_mismatch")
    if decision_payload.get("source_approval_record_type") != spec["record_type"]:
        blockers.append("approval_decision_source_record_type_mismatch")
    if decision_payload.get("source_approval_schema_version") != spec["schema_version"]:
        blockers.append("approval_decision_source_schema_version_mismatch")
    if decision_payload.get("approval_scope") != spec["scope"]:
        blockers.append("approval_decision_scope_mismatch")
    if not _path_value_matches_vault_path(vault, decision_payload.get("source_approval_artifact_path"), approval_path):
        blockers.append("approval_decision_source_artifact_path_mismatch")
    if not _path_value_matches_vault_path(vault, decision_payload.get("decision_artifact_path"), decision_path):
        blockers.append("approval_decision_artifact_path_mismatch")
    if isinstance(handoff, dict) and handoff.get("decision_artifact_path") != approval_payload.get("decision_artifact_path"):
        blockers.append("approval_decision_handoff_path_mismatch")

    mutation = decision_payload.get("approval_artifact_mutation")
    if not isinstance(mutation, dict):
        blockers.append("approval_decision_artifact_mutation_missing")
    else:
        if mutation.get("status_after") != "approved":
            blockers.append("approval_decision_artifact_mutation_status_mismatch")
        if mutation.get("approval_consumed_after") is not False:
            blockers.append("approval_decision_artifact_mutation_consumed_unexpected")
    if decision_payload.get("approval_consumed") is not False:
        blockers.append("approval_decision_consumed_unexpected")
    if decision_payload.get("forge_execution_allowed") is not False:
        blockers.append("approval_decision_execution_allowed_unexpected")
    if decision_payload.get("registry_written") is not False:
        blockers.append("approval_decision_registry_written_unexpected")
    if decision_payload.get("extension_files_written") != []:
        blockers.append("approval_decision_extension_files_written_unexpected")
    if decision_payload.get("extension_files_deleted") != []:
        blockers.append("approval_decision_extension_files_deleted_unexpected")
    if decision_payload.get("exact_once_marker_reserved") is not False:
        blockers.append("approval_decision_exact_once_marker_reserved_unexpected")
    return blockers


def _approved_artifact_blockers(
    *,
    vault: Path,
    approval_path: Path | None,
    approval_payload: dict[str, Any] | None,
    packet_id: str,
    request_digest: str,
    expected_material: dict[str, Any],
    marker_path: Path,
    registry_path: Path,
) -> list[str]:
    blockers: list[str] = []
    if approval_payload is None:
        return ["approved_sandbox_approval_artifact_missing"]
    if approval_payload.get("record_type") != SANDBOX_APPROVAL_RECORD_TYPE:
        blockers.append("approval_record_type_mismatch")
    if approval_payload.get("schema_version") != SANDBOX_APPROVAL_SCHEMA_VERSION:
        blockers.append("approval_schema_version_mismatch")
    if approval_payload.get("approval_packet_id") != packet_id:
        blockers.append("approval_packet_id_mismatch")
    if approval_payload.get("request_digest_sha256") != request_digest:
        blockers.append("approval_request_digest_mismatch")
    if approval_payload.get("approval_scope") != SANDBOX_APPROVAL_SCOPE:
        blockers.append("approval_scope_mismatch")
    if approval_payload.get("status") != "approved":
        blockers.append("approval_status_not_approved")
    if approval_payload.get("operator_decision") != "approved":
        blockers.append("operator_decision_not_approved")
    if approval_payload.get("approval_consumed") is not False:
        blockers.append("approval_already_consumed")

    confirmation_text = str(approval_payload.get("operator_confirmation_text") or "").strip()
    approval_statement = str(approval_payload.get("operator_approval_statement") or "").strip()
    if not confirmation_text or approval_statement != confirmation_text:
        blockers.append("operator_approval_statement_missing_or_mismatched")

    approved_material = approval_payload.get("approved_material")
    if not isinstance(approved_material, dict):
        blockers.append("approved_material_missing")
    elif _sha256_payload(approved_material) != request_digest or _sha256_payload(expected_material) != request_digest:
        blockers.append("approved_material_digest_mismatch")

    if not _path_matches_expected(approval_payload.get("future_exact_once_marker_path"), marker_path):
        blockers.append("future_marker_path_mismatch")
    if not _path_matches_expected(approval_payload.get("future_registry_path"), registry_path):
        blockers.append("future_registry_path_mismatch")
    if approval_path is None:
        blockers.append("approval_artifact_path_missing")
    else:
        blockers.extend(
            _approval_decision_sidecar_blockers(
                vault=vault,
                approval_path=approval_path,
                approval_payload=approval_payload,
                family_id="sandbox",
                packet_id=packet_id,
                request_digest=request_digest,
            )
        )
    return blockers


def _expected_live_artifact_paths(
    vault: Path,
    packet_id: str,
    approval_artifact_path: str | Path | None,
) -> tuple[Path | None, Path, Path, list[str]]:
    blockers: list[str] = []
    default_approval_path = _safe_json_path(vault, LIVE_INSTALL_APPROVAL_RELATIVE_DIR, packet_id)
    marker_path = _safe_json_path(vault, LIVE_INSTALL_MARKER_RELATIVE_DIR, packet_id)
    registry_path = (vault / REGISTRY_RELATIVE_PATH).resolve()
    approval_path = default_approval_path
    if approval_artifact_path:
        resolved, blocker = _resolve_under_base(vault, approval_artifact_path, LIVE_INSTALL_APPROVAL_RELATIVE_DIR)
        if blocker:
            blockers.append("approval_artifact_path_outside_live_install_approval_root")
            approval_path = None
        else:
            approval_path = resolved
    return approval_path, marker_path, registry_path, blockers


def _approved_live_artifact_blockers(
    *,
    vault: Path,
    approval_path: Path | None,
    approval_payload: dict[str, Any] | None,
    packet_id: str,
    request_digest: str,
    expected_material: dict[str, Any],
    marker_path: Path,
    registry_path: Path,
) -> list[str]:
    blockers: list[str] = []
    if approval_payload is None:
        return ["approved_live_install_approval_artifact_missing"]
    if approval_payload.get("record_type") != LIVE_INSTALL_APPROVAL_RECORD_TYPE:
        blockers.append("approval_record_type_mismatch")
    if approval_payload.get("schema_version") != LIVE_INSTALL_APPROVAL_SCHEMA_VERSION:
        blockers.append("approval_schema_version_mismatch")
    if approval_payload.get("approval_packet_id") != packet_id:
        blockers.append("approval_packet_id_mismatch")
    if approval_payload.get("request_digest_sha256") != request_digest:
        blockers.append("approval_request_digest_mismatch")
    if approval_payload.get("approval_scope") != LIVE_INSTALL_APPROVAL_SCOPE:
        blockers.append("approval_scope_mismatch")
    if approval_payload.get("status") != "approved":
        blockers.append("approval_status_not_approved")
    if approval_payload.get("operator_decision") != "approved":
        blockers.append("operator_decision_not_approved")
    if approval_payload.get("approval_consumed") is not False:
        blockers.append("approval_already_consumed")

    confirmation_text = str(approval_payload.get("operator_confirmation_text") or "").strip()
    approval_statement = str(approval_payload.get("operator_approval_statement") or "").strip()
    if not confirmation_text or approval_statement != confirmation_text:
        blockers.append("operator_approval_statement_missing_or_mismatched")

    approved_material = approval_payload.get("approved_material")
    if not isinstance(approved_material, dict):
        blockers.append("approved_material_missing")
    elif _sha256_payload(approved_material) != request_digest or _sha256_payload(expected_material) != request_digest:
        blockers.append("approved_material_digest_mismatch")

    if not _path_matches_expected(approval_payload.get("future_live_exact_once_marker_path"), marker_path):
        blockers.append("future_live_marker_path_mismatch")
    if not _path_matches_expected(approval_payload.get("future_registry_path"), registry_path):
        blockers.append("future_registry_path_mismatch")
    if approval_path is None:
        blockers.append("approval_artifact_path_missing")
    else:
        blockers.extend(
            _approval_decision_sidecar_blockers(
                vault=vault,
                approval_path=approval_path,
                approval_payload=approval_payload,
                family_id="live-install",
                packet_id=packet_id,
                request_digest=request_digest,
            )
        )
    return blockers


def _promoted_live_registry_entry(
    *,
    vault: Path,
    sandbox_registry_entry: dict[str, Any],
    approval_packet_id: str,
    request_digest: str,
    marker_path: Path,
    extension_file_count: int,
    generated_at: str,
    requested_by: str,
) -> dict[str, Any]:
    entry = deepcopy(sandbox_registry_entry)
    entry.update(
        {
            "registry_status": "live_installed",
            "install_environment": "live",
            "live_activated_at": generated_at,
            "live_execution": {
                "schema_version": LIVE_INSTALL_EXECUTION_SCHEMA_VERSION,
                "approval_packet_id": approval_packet_id,
                "request_digest_sha256": request_digest,
                "exact_once_marker_path": _relative_to_vault(vault, marker_path),
                "extension_file_count": extension_file_count,
                "executed_at": generated_at,
                "executed_by": requested_by,
                "activated_from_sandbox": True,
                "live_install": True,
                "extension_files_written": [],
            },
            "authority": dict(BLOCKED_AUTHORITY),
        }
    )
    return entry


def build_sandbox_registry_write_execution(
    vault_root: str | Path,
    *,
    manifest: dict[str, Any] | None = None,
    approval_packet_id: str | None = None,
    request_digest: str | None = None,
    approval_artifact_path: str | Path | None = None,
    execute: bool = False,
    requested_by: str = "Codex",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Consume an approved Forge sandbox request and write sandbox registry artifacts.

    This executor writes only the Forge registry and extension-owned target files,
    and only after it validates an approved request artifact, exact digest, and
    exact-once marker state.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    manifest_payload = deepcopy(manifest) if manifest is not None else load_demo_manifest()
    validation = validate_manifest(manifest_payload)
    approval_preview = build_sandbox_install_approval(
        vault,
        manifest=manifest_payload,
        approval_packet_id=approval_packet_id,
        generated_at=timestamp,
    )
    packet_id = str(approval_preview.get("approval_packet_id") or "")
    expected_digest = str(approval_preview.get("request_digest_sha256") or "")
    supplied_digest = str(request_digest or "")
    approval_path, marker_path, registry_path, blockers = _expected_artifact_paths(vault, packet_id, approval_artifact_path)
    approval_payload = _read_json(approval_path) if approval_path and approval_path.is_file() else None
    registry_payload, registry_blockers = _load_registry_for_write(registry_path, timestamp)
    registry_entries = list((registry_payload or {}).get("entries") or []) if registry_payload else []
    path_guard = (validation.get("protectedCore") or {}).get("targetPathValidation") or {}
    target_paths = list(path_guard.get("normalized_paths") or [])
    resolved_target_paths = [(repo_path, (vault / repo_path).resolve()) for repo_path in target_paths]
    target_conflicts = [repo_path for repo_path, target_path in resolved_target_paths if target_path.exists()]

    if not validation.get("valid"):
        blockers.append("manifest_validation_blocked")
    blockers.extend(str(issue.get("code") or "validation_issue") for issue in validation.get("errors") or [])
    if supplied_digest != expected_digest:
        blockers.append("request_digest_required_or_mismatched")
    blockers.extend(registry_blockers)
    if marker_path.exists():
        blockers.append("sandbox_exact_once_marker_already_present")
    if any(entry.get("extension_id") == manifest_payload.get("id") for entry in registry_entries if isinstance(entry, dict)):
        blockers.append("registry_entry_already_exists")
    if target_conflicts:
        blockers.append("extension_target_already_exists")
    blockers.extend(
        _approved_artifact_blockers(
            vault=vault,
            approval_path=approval_path,
            approval_payload=approval_payload,
            packet_id=packet_id,
            request_digest=expected_digest,
            expected_material=approval_preview["approval_artifact_preview"]["approved_material"],
            marker_path=marker_path,
            registry_path=registry_path,
        )
    )
    blockers = list(dict.fromkeys(blockers))
    ready_for_execution = not blockers

    registry_written = False
    extension_files_written: list[str] = []
    exact_once_marker_written = False
    approval_consumed = False
    marker_payload = {
        "record_type": SANDBOX_REGISTRY_WRITE_MARKER_RECORD_TYPE,
        "schema_version": SANDBOX_REGISTRY_WRITE_SCHEMA_VERSION,
        "status": "preview",
        "generated_at": timestamp,
        "approval_packet_id": packet_id,
        "request_digest_sha256": expected_digest,
        "extension_id": manifest_payload.get("id"),
        "target_paths": target_paths,
        "reserved_before_writes": False,
        "completed": False,
    }

    if execute and ready_for_execution and registry_payload is not None and approval_path is not None:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_payload = {
            **marker_payload,
            "status": "reserved",
            "reserved_at": timestamp,
            "reserved_by": requested_by,
            "reserved_before_writes": True,
        }
        with marker_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(marker_payload, indent=2, default=str) + "\n")
        exact_once_marker_written = True

        for repo_path, target_path in resolved_target_paths:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            payload = _sandbox_extension_file_payload(
                manifest=manifest_payload,
                repo_path=repo_path,
                approval_packet_id=packet_id,
                request_digest=expected_digest,
                generated_at=timestamp,
            )
            with target_path.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, indent=2, default=str) + "\n")
            extension_files_written.append(repo_path)

        registry_entry = build_registry_entry(
            manifest_payload,
            validation,
            registry_status="sandbox_installed",
            install_environment="sandbox",
            generated_at=timestamp,
        )
        registry_entry["sandbox_execution"] = {
            "schema_version": SANDBOX_REGISTRY_WRITE_SCHEMA_VERSION,
            "approval_packet_id": packet_id,
            "request_digest_sha256": expected_digest,
            "exact_once_marker_path": _relative_to_vault(vault, marker_path),
            "extension_file_count": len(extension_files_written),
            "executed_at": timestamp,
            "executed_by": requested_by,
            "live_install": False,
        }
        registry_payload["entries"] = registry_entries + [registry_entry]
        registry_payload["status"] = "sandbox_registry_contains_entries"
        registry_payload["updated_at"] = timestamp
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(json.dumps(registry_payload, indent=2, default=str) + "\n", encoding="utf-8")
        registry_written = True

        consumed_payload = dict(approval_payload)
        consumed_payload.update(
            {
                "status": "consumed",
                "approval_consumed": True,
                "consumed_at": timestamp,
                "consumed_by": requested_by,
                "sandbox_install_allowed_in_this_pass": True,
                "registry_write_allowed_in_this_pass": True,
                "extension_file_write_allowed_in_this_pass": True,
                "sandbox_execution_result": {
                    "schema_version": SANDBOX_REGISTRY_WRITE_SCHEMA_VERSION,
                    "exact_once_marker_path": _relative_to_vault(vault, marker_path),
                    "registry_path": _relative_to_vault(vault, registry_path),
                    "extension_files_written": extension_files_written,
                    "live_install": False,
                },
            }
        )
        approval_path.write_text(json.dumps(consumed_payload, indent=2, default=str) + "\n", encoding="utf-8")
        approval_consumed = True

        marker_payload = {
            **marker_payload,
            "status": "completed",
            "completed": True,
            "completed_at": timestamp,
            "registry_path": _relative_to_vault(vault, registry_path),
            "extension_files_written": extension_files_written,
        }
        marker_path.write_text(json.dumps(marker_payload, indent=2, default=str) + "\n", encoding="utf-8")

    status = (
        "forge_sandbox_registry_write_executed"
        if registry_written
        else "forge_sandbox_registry_write_ready"
        if ready_for_execution
        else "blocked_forge_sandbox_registry_write"
    )

    return {
        "ok": ready_for_execution,
        "surface": SANDBOX_REGISTRY_WRITE_SURFACE_ID,
        "model_version": SANDBOX_REGISTRY_WRITE_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "execute_requested": execute,
        "approval_packet_id": packet_id,
        "request_digest_sha256": expected_digest,
        "approval_artifact_path": _relative_to_vault(vault, approval_path) if approval_path else "",
        "approval_artifact_exists": bool(approval_path and approval_path.is_file()),
        "registry_path": _relative_to_vault(vault, registry_path),
        "registry_written": registry_written,
        "registry_entry_preview": build_registry_entry(
            manifest_payload,
            validation,
            registry_status="sandbox_installed",
            install_environment="sandbox",
            generated_at=timestamp,
        ),
        "extension_target_paths": target_paths,
        "extension_files_written": extension_files_written,
        "target_conflicts": target_conflicts,
        "future_exact_once_marker_path": _relative_to_vault(vault, marker_path),
        "exact_once_marker_exists": marker_path.is_file(),
        "exact_once_marker_written": exact_once_marker_written,
        "approval_consumed": approval_consumed,
        "manifest_validation": validation,
        "authority": {
            **dict(BLOCKED_AUTHORITY),
            "executes_sandbox_install": registry_written,
            "writes_extension_registry": registry_written,
            "writes_extension_files": bool(extension_files_written),
            "consumes_approval": approval_consumed,
            "reserves_exact_once_marker": exact_once_marker_written,
            "executes_live_install": False,
            "mutates_protected_core": False,
            "mutates_studio_shell": False,
            "mutates_runtime_policy": False,
            "activates_schedule": False,
            "writes_agent_bus_task": False,
            "reads_secret_or_credential": False,
            "calls_provider_or_model": False,
            "calls_external_connector": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-live-install-approval-packet"
            if registry_written
            else "chaser-forge-sandbox-approved-registry-writer"
            if ready_for_execution
            else "chaser-forge-sandbox-approval-operator-decision"
        ),
    }


def build_live_install_execution(
    vault_root: str | Path,
    *,
    manifest: dict[str, Any] | None = None,
    approval_packet_id: str | None = None,
    request_digest: str | None = None,
    approval_artifact_path: str | Path | None = None,
    execute: bool = False,
    requested_by: str = "Codex",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Consume an approved Forge live-install request and promote sandbox registry state.

    This executor writes only Forge registry live metadata, a live exact-once
    marker, and consumed status metadata on the approved live artifact. It does
    not write extension files or protected core paths.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    manifest_payload = deepcopy(manifest) if manifest is not None else load_demo_manifest()
    validation = validate_manifest(manifest_payload)
    path_guard = (validation.get("protectedCore") or {}).get("targetPathValidation") or {}
    target_paths = list(path_guard.get("normalized_paths") or [])
    extension_id = str(manifest_payload.get("id") or "invalid-extension")
    registry = build_extension_registry(vault)
    sandbox_registry_entry = _registry_entry_for_extension(registry, extension_id)
    sandbox_marker_path, sandbox_marker, marker_blockers = _sandbox_marker_payload(vault, sandbox_registry_entry or {})
    material = _live_material(
        manifest=manifest_payload,
        validation=validation,
        sandbox_registry_entry=sandbox_registry_entry,
        sandbox_marker_path=sandbox_marker_path,
        target_paths=target_paths,
    )
    expected_digest = _sha256_payload(material)
    supplied_digest = str(request_digest or "")
    packet_digest = supplied_digest or expected_digest
    packet_id = approval_packet_id or f"forge-live-install-appr-{_safe_identifier(extension_id)}-{packet_digest[:12]}"
    approval_path, marker_path, registry_path, blockers = _expected_live_artifact_paths(
        vault,
        packet_id,
        approval_artifact_path,
    )
    approval_payload = _read_json(approval_path) if approval_path and approval_path.is_file() else None
    registry_payload, registry_blockers = _load_registry_for_write(registry_path, timestamp)
    registry_entries = list((registry_payload or {}).get("entries") or []) if registry_payload else []
    registry_entry_index: int | None = None
    registry_entry_for_write: dict[str, Any] | None = None
    for index, entry in enumerate(registry_entries):
        if isinstance(entry, dict) and entry.get("extension_id") == extension_id:
            registry_entry_index = index
            registry_entry_for_write = entry
            break

    approval_preview = _live_approval_artifact_payload(
        packet_id=packet_id,
        request_digest=expected_digest,
        material=material,
        approval_path=approval_path or _safe_json_path(vault, LIVE_INSTALL_APPROVAL_RELATIVE_DIR, packet_id),
        marker_path=marker_path,
        registry_path=registry_path,
        requested_by=requested_by,
        generated_at=timestamp,
    )

    blockers.extend(
        _sandbox_proof_blockers(
            vault=vault,
            manifest=manifest_payload,
            validation=validation,
            registry=registry,
            registry_entry=sandbox_registry_entry,
            sandbox_marker_payload=sandbox_marker,
            target_paths=target_paths,
        )
    )
    blockers.extend(marker_blockers)
    blockers.extend(registry_blockers)
    if supplied_digest != expected_digest:
        blockers.append("request_digest_required_or_mismatched")
    if marker_path.exists():
        blockers.append("live_install_exact_once_marker_already_present")
    if registry_entry_for_write is None:
        blockers.append("sandbox_registry_entry_missing")
    elif registry_entry_for_write.get("live_execution"):
        blockers.append("live_execution_already_recorded")
    if registry_entry_for_write and (
        registry_entry_for_write.get("registry_status") == "live_installed"
        or registry_entry_for_write.get("install_environment") == "live"
    ):
        blockers.append("live_registry_entry_already_installed")
    blockers.extend(
        _approved_live_artifact_blockers(
            vault=vault,
            approval_path=approval_path,
            approval_payload=approval_payload,
            packet_id=packet_id,
            request_digest=expected_digest,
            expected_material=material,
            marker_path=marker_path,
            registry_path=registry_path,
        )
    )
    blockers = list(dict.fromkeys(blockers))
    ready_for_execution = not blockers

    live_registry_entry_preview = _promoted_live_registry_entry(
        vault=vault,
        sandbox_registry_entry=sandbox_registry_entry
        or build_registry_entry(
            manifest_payload,
            validation,
            registry_status="sandbox_installed",
            install_environment="sandbox",
            generated_at=timestamp,
        ),
        approval_packet_id=packet_id,
        request_digest=expected_digest,
        marker_path=marker_path,
        extension_file_count=len(target_paths),
        generated_at=timestamp,
        requested_by=requested_by,
    )
    registry_updated = False
    exact_once_marker_written = False
    approval_consumed = False
    live_install_executed = False
    marker_payload = {
        "record_type": LIVE_INSTALL_MARKER_RECORD_TYPE,
        "schema_version": LIVE_INSTALL_EXECUTION_SCHEMA_VERSION,
        "status": "preview",
        "generated_at": timestamp,
        "approval_packet_id": packet_id,
        "request_digest_sha256": expected_digest,
        "extension_id": extension_id,
        "target_paths": target_paths,
        "sandbox_exact_once_marker_path": _relative_to_vault(vault, sandbox_marker_path) if sandbox_marker_path else "",
        "reserved_before_writes": False,
        "completed": False,
    }

    if (
        execute
        and ready_for_execution
        and registry_payload is not None
        and approval_path is not None
        and registry_entry_index is not None
        and registry_entry_for_write is not None
    ):
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_payload = {
            **marker_payload,
            "status": "reserved",
            "reserved_at": timestamp,
            "reserved_by": requested_by,
            "reserved_before_writes": True,
        }
        with marker_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(marker_payload, indent=2, default=str) + "\n")
        exact_once_marker_written = True

        promoted_entry = _promoted_live_registry_entry(
            vault=vault,
            sandbox_registry_entry=registry_entry_for_write,
            approval_packet_id=packet_id,
            request_digest=expected_digest,
            marker_path=marker_path,
            extension_file_count=len(target_paths),
            generated_at=timestamp,
            requested_by=requested_by,
        )
        registry_entries[registry_entry_index] = promoted_entry
        registry_payload["entries"] = registry_entries
        registry_payload["status"] = "live_registry_contains_entries"
        registry_payload["updated_at"] = timestamp
        registry_payload["approved_live_install_executor_built"] = True
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(json.dumps(registry_payload, indent=2, default=str) + "\n", encoding="utf-8")
        registry_updated = True
        live_install_executed = True
        live_registry_entry_preview = promoted_entry

        consumed_payload = dict(approval_payload)
        consumed_payload.update(
            {
                "status": "consumed",
                "approval_consumed": True,
                "consumed_at": timestamp,
                "consumed_by": requested_by,
                "live_install_allowed_in_this_pass": True,
                "live_install_executor_built": True,
                "registry_write_allowed_in_this_pass": True,
                "extension_file_write_allowed_in_this_pass": False,
                "executes_live_install": True,
                "writes_extension_registry": True,
                "writes_extension_files": False,
                "consumes_approval": True,
                "reserves_exact_once_marker": True,
                "live_execution_result": {
                    "schema_version": LIVE_INSTALL_EXECUTION_SCHEMA_VERSION,
                    "exact_once_marker_path": _relative_to_vault(vault, marker_path),
                    "registry_path": _relative_to_vault(vault, registry_path),
                    "extension_files_written": [],
                    "live_install": True,
                },
            }
        )
        approval_path.write_text(json.dumps(consumed_payload, indent=2, default=str) + "\n", encoding="utf-8")
        approval_consumed = True

        marker_payload = {
            **marker_payload,
            "status": "completed",
            "completed": True,
            "completed_at": timestamp,
            "registry_path": _relative_to_vault(vault, registry_path),
            "live_registry_entry_digest_sha256": _sha256_payload(promoted_entry),
            "extension_files_written": [],
        }
        marker_path.write_text(json.dumps(marker_payload, indent=2, default=str) + "\n", encoding="utf-8")

    status = (
        "forge_live_install_executed"
        if live_install_executed
        else "forge_live_install_execution_ready"
        if ready_for_execution
        else "blocked_forge_live_install_execution"
    )

    return {
        "ok": ready_for_execution,
        "surface": LIVE_INSTALL_EXECUTION_SURFACE_ID,
        "model_version": LIVE_INSTALL_EXECUTION_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "execute_requested": execute,
        "approval_packet_id": packet_id,
        "request_digest_sha256": expected_digest,
        "approval_artifact_path": _relative_to_vault(vault, approval_path) if approval_path else "",
        "approval_artifact_exists": bool(approval_path and approval_path.is_file()),
        "registry_path": _relative_to_vault(vault, registry_path),
        "registry_updated": registry_updated,
        "registry_written": registry_updated,
        "live_install_executed": live_install_executed,
        "live_registry_entry_preview": live_registry_entry_preview,
        "extension_target_paths": target_paths,
        "extension_files_written": [],
        "sandbox_registry_entry": sandbox_registry_entry or {},
        "sandbox_exact_once_marker_path": _relative_to_vault(vault, sandbox_marker_path) if sandbox_marker_path else "",
        "sandbox_exact_once_marker_exists": bool(sandbox_marker_path and sandbox_marker_path.is_file()),
        "future_live_exact_once_marker_path": _relative_to_vault(vault, marker_path),
        "exact_once_marker_exists": marker_path.is_file(),
        "exact_once_marker_written": exact_once_marker_written,
        "approval_consumed": approval_consumed,
        "approval_artifact_preview": approval_preview,
        "operator_confirmation_text": approval_preview["operator_confirmation_text"],
        "manifest_validation": validation,
        "authority": {
            **dict(BLOCKED_AUTHORITY),
            "executes_live_install": live_install_executed,
            "writes_extension_registry": registry_updated,
            "writes_extension_files": False,
            "consumes_approval": approval_consumed,
            "reserves_exact_once_marker": exact_once_marker_written,
            "executes_sandbox_install": False,
            "mutates_protected_core": False,
            "mutates_studio_shell": False,
            "mutates_runtime_policy": False,
            "activates_schedule": False,
            "writes_agent_bus_task": False,
            "reads_secret_or_credential": False,
            "calls_provider_or_model": False,
            "calls_external_connector": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-rollback-executor"
            if live_install_executed
            else "chaser-forge-live-install-operator-decision"
            if ready_for_execution
            else "chaser-forge-live-install-approval-packet"
        ),
    }


def _live_marker_payload(vault: Path, registry_entry: dict[str, Any]) -> tuple[Path | None, dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    live_execution = registry_entry.get("live_execution")
    if not isinstance(live_execution, dict):
        return None, None, ["live_execution_metadata_missing"]

    marker_path_value = live_execution.get("exact_once_marker_path")
    if not marker_path_value:
        return None, None, ["live_exact_once_marker_path_missing"]

    marker_path, path_blocker = _repo_relative_path(vault, str(marker_path_value))
    if path_blocker:
        return None, None, ["live_exact_once_marker_path_outside_vault"]
    if marker_path is None or not marker_path.is_file():
        return marker_path, None, ["live_exact_once_marker_missing"]

    payload = _read_json(marker_path)
    if payload is None:
        blockers.append("live_exact_once_marker_unreadable")
    return marker_path, payload, blockers


def _live_proof_blockers(
    *,
    vault: Path,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    registry: dict[str, Any],
    registry_entry: dict[str, Any] | None,
    live_marker_payload: dict[str, Any] | None,
    target_paths: list[str],
) -> list[str]:
    blockers: list[str] = []
    extension_id = str(manifest.get("id") or "")
    manifest_digest = _sha256_payload(deepcopy(manifest))
    if registry_entry is None:
        return ["live_registry_entry_missing"]

    if registry_entry.get("registry_status") != "live_installed":
        blockers.append("live_registry_entry_not_installed")
    if registry_entry.get("install_environment") != "live":
        blockers.append("live_registry_entry_environment_mismatch")
    if registry_entry.get("manifest_digest_sha256") != manifest_digest:
        blockers.append("live_registry_entry_manifest_digest_mismatch")
    if registry_entry.get("validation_valid") is not True:
        blockers.append("live_registry_entry_validation_not_valid")

    live_execution = registry_entry.get("live_execution")
    if not isinstance(live_execution, dict):
        blockers.append("live_execution_metadata_missing")
    else:
        if live_execution.get("approval_packet_id") in (None, ""):
            blockers.append("live_execution_approval_packet_missing")
        if live_execution.get("request_digest_sha256") in (None, ""):
            blockers.append("live_execution_request_digest_missing")
        if live_execution.get("live_install") is not True:
            blockers.append("live_execution_live_install_not_true")

    if live_marker_payload is None:
        blockers.append("live_exact_once_marker_missing")
    else:
        if live_marker_payload.get("record_type") != LIVE_INSTALL_MARKER_RECORD_TYPE:
            blockers.append("live_marker_record_type_mismatch")
        if live_marker_payload.get("schema_version") != LIVE_INSTALL_EXECUTION_SCHEMA_VERSION:
            blockers.append("live_marker_schema_version_mismatch")
        if live_marker_payload.get("completed") is not True:
            blockers.append("live_marker_not_completed")
        if live_marker_payload.get("extension_id") != extension_id:
            blockers.append("live_marker_extension_id_mismatch")
        if isinstance(live_execution, dict):
            if live_marker_payload.get("approval_packet_id") != live_execution.get("approval_packet_id"):
                blockers.append("live_marker_approval_packet_mismatch")
            if live_marker_payload.get("request_digest_sha256") != live_execution.get("request_digest_sha256"):
                blockers.append("live_marker_request_digest_mismatch")

    registry_target_paths = list(registry_entry.get("target_paths") or [])
    if registry_target_paths != target_paths:
        blockers.append("live_registry_entry_target_paths_mismatch")

    missing_target_paths: list[str] = []
    for repo_path in target_paths:
        target_path, path_blocker = _repo_relative_path(vault, repo_path)
        if path_blocker:
            blockers.append("extension_target_path_outside_vault")
        elif target_path is not None and not target_path.is_file():
            missing_target_paths.append(repo_path)
    if missing_target_paths:
        blockers.append("extension_target_missing")

    if registry_entry.get("rollback_execution"):
        blockers.append("rollback_execution_already_recorded")
    if not registry.get("ok"):
        blockers.extend(str(item) for item in registry.get("blockers") or [])
    if not validation.get("valid"):
        blockers.append("manifest_validation_blocked")
    blockers.extend(str(issue.get("code") or "validation_issue") for issue in validation.get("errors") or [])
    return blockers


def _rollback_material(
    *,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    live_registry_entry: dict[str, Any] | None,
    live_marker_path: Path | None,
    target_paths: list[str],
) -> dict[str, Any]:
    registry_entry = deepcopy(live_registry_entry or {})
    live_execution = deepcopy(registry_entry.get("live_execution") or {})
    return {
        "schema_version": "forge.rollback_approval.material.v1",
        "requested_action": "request_forge_live_rollback",
        "extension_id": manifest.get("id"),
        "extension_name": manifest.get("name"),
        "extension_version": manifest.get("version"),
        "manifest_digest_sha256": _sha256_payload(deepcopy(manifest)),
        "validation_status": validation.get("status"),
        "live_registry_entry_digest_sha256": _sha256_payload(registry_entry) if registry_entry else "",
        "live_registry_status": registry_entry.get("registry_status"),
        "live_install_environment": registry_entry.get("install_environment"),
        "live_execution": live_execution,
        "live_exact_once_marker_path": str(live_marker_path) if live_marker_path else "",
        "target_paths": target_paths,
        "rollback": deepcopy(manifest.get("rollback") or {}),
        "approval_effect": (
            "authorizes one future rollback executor attempt only after a separate executor "
            "revalidates the manifest, live registry entry, live marker, target files, "
            "approval digest, and exact-once rollback marker state"
        ),
        "rollback_executor_requirements": [
            "operator_decision must be approved in this artifact",
            "approval_packet_id and request_digest_sha256 must match",
            "live registry entry must still be live_installed",
            "live exact-once marker must still be completed and match the registry entry",
            "extension-owned target files must still exist and match the manifest target set",
            "executor must reserve a separate rollback exact-once marker before registry mutation",
            "rollback must not delete extension files or mutate protected core paths",
        ],
        "rollback_result": "registry entry returns to sandbox_installed/sandbox while extension files remain present",
        "direct_core_mutation_allowed": False,
        "generated_extension_registry_write_allowed": False,
    }


def _rollback_operator_confirmation_text(extension_id: str, target_paths: list[str]) -> str:
    lines = [
        "APPROVE FORGE ROLLBACK REQUEST ONLY:",
        f"- extension_id: {extension_id}",
        "- environment: rollback from live to sandbox registry state",
        "- live proof must remain valid at execution time",
        "- future rollback executor must revalidate manifest digest, registry entry, marker, and target paths",
        "- future rollback writes require a separate exact-once rollback marker",
        "",
        "Target paths retained:",
        *[f"- {path}" for path in target_paths],
        "",
        "No extension files are deleted by this rollback executor.",
        "No protected-core writes.",
        "No Studio shell patch.",
        "No runtime policy, schedule, Agent Bus, provider, credential, external connector, or canonical mutation.",
    ]
    return "\n".join(lines)


def _rollback_approval_artifact_payload(
    *,
    packet_id: str,
    request_digest: str,
    material: dict[str, Any],
    approval_path: Path,
    marker_path: Path,
    registry_path: Path,
    requested_by: str,
    generated_at: str,
) -> dict[str, Any]:
    extension_id = str(material.get("extension_id") or "")
    target_paths = list(material.get("target_paths") or [])
    return {
        "record_type": ROLLBACK_APPROVAL_RECORD_TYPE,
        "schema_version": ROLLBACK_APPROVAL_SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": "pending_operator_decision",
        "approval_packet_id": packet_id,
        "request_digest_sha256": request_digest,
        "operator_decision": "pending",
        "approval_scope": ROLLBACK_APPROVAL_SCOPE,
        "requested_by": requested_by,
        "extension_id": extension_id,
        "extension_name": material.get("extension_name"),
        "extension_version": material.get("extension_version"),
        "approval_artifact_path": str(approval_path),
        "future_rollback_exact_once_marker_path": str(marker_path),
        "future_registry_path": str(registry_path),
        "future_extension_target_paths": target_paths,
        "operator_confirmation_text": _rollback_operator_confirmation_text(extension_id, target_paths),
        "approved_material": material,
        "future_executor_requirements": list(material.get("rollback_executor_requirements") or []),
        "approval_consumed": False,
        "sandbox_install_allowed_in_this_pass": False,
        "live_install_allowed_in_this_pass": False,
        "rollback_allowed_in_this_pass": False,
        "rollback_executor_built": False,
        "registry_write_allowed_in_this_pass": False,
        "extension_file_write_allowed_in_this_pass": False,
        "extension_file_delete_allowed_in_this_pass": False,
        **BLOCKED_AUTHORITY,
    }


def _rollback_approval_matches(payload: dict[str, Any] | None, packet_id: str, request_digest: str) -> bool:
    return bool(
        payload
        and payload.get("record_type") == ROLLBACK_APPROVAL_RECORD_TYPE
        and payload.get("approval_packet_id") == packet_id
        and payload.get("request_digest_sha256") == request_digest
        and payload.get("status") == "pending_operator_decision"
        and payload.get("operator_decision") == "pending"
        and payload.get("approval_scope") == ROLLBACK_APPROVAL_SCOPE
        and payload.get("approval_consumed") is False
        and payload.get("rollback_allowed_in_this_pass") is False
        and payload.get("rollback_executor_built") is False
    )


def build_rollback_approval(
    vault_root: str | Path,
    *,
    manifest: dict[str, Any] | None = None,
    approval_packet_id: str | None = None,
    request_digest: str | None = None,
    write_approval_request: bool = False,
    requested_by: str = "Codex",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build or optionally write a Forge rollback approval request.

    This surface is request-only. It requires an existing live registry entry,
    completed live marker, and extension-owned target files before it can write
    a pending rollback approval artifact. It never executes rollback.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    manifest_payload = deepcopy(manifest) if manifest is not None else load_demo_manifest()
    validation = validate_manifest(manifest_payload)
    path_guard = (validation.get("protectedCore") or {}).get("targetPathValidation") or {}
    target_paths = list(path_guard.get("normalized_paths") or [])
    extension_id = str(manifest_payload.get("id") or "invalid-extension")
    registry = build_extension_registry(vault)
    live_registry_entry = _registry_entry_for_extension(registry, extension_id)
    live_marker_path, live_marker, marker_blockers = _live_marker_payload(vault, live_registry_entry or {})
    material = _rollback_material(
        manifest=manifest_payload,
        validation=validation,
        live_registry_entry=live_registry_entry,
        live_marker_path=live_marker_path,
        target_paths=target_paths,
    )
    digest = _sha256_payload(material)
    packet_id = approval_packet_id or f"forge-rollback-appr-{_safe_identifier(extension_id)}-{digest[:12]}"
    approval_path = _safe_json_path(vault, ROLLBACK_APPROVAL_RELATIVE_DIR, packet_id)
    marker_path = _safe_json_path(vault, ROLLBACK_MARKER_RELATIVE_DIR, packet_id)
    registry_path = (vault / REGISTRY_RELATIVE_PATH).resolve()
    existing_payload = _read_json(approval_path) if approval_path.is_file() else None
    existing_matches = _rollback_approval_matches(existing_payload, packet_id, digest)
    approval_preview = _rollback_approval_artifact_payload(
        packet_id=packet_id,
        request_digest=digest,
        material=material,
        approval_path=approval_path,
        marker_path=marker_path,
        registry_path=registry_path,
        requested_by=requested_by,
        generated_at=timestamp,
    )

    blockers = _live_proof_blockers(
        vault=vault,
        manifest=manifest_payload,
        validation=validation,
        registry=registry,
        registry_entry=live_registry_entry,
        live_marker_payload=live_marker,
        target_paths=target_paths,
    )
    blockers.extend(marker_blockers)
    if marker_path.exists():
        blockers.append("rollback_exact_once_marker_already_present")
    if approval_path.exists() and not existing_matches:
        blockers.append("existing_rollback_approval_artifact_mismatch")
    if write_approval_request and request_digest != digest:
        blockers.append("request_digest_required_or_mismatched")
    blockers = list(dict.fromkeys(blockers))

    approval_written = False
    approval_reused = False
    if write_approval_request and not blockers:
        if existing_matches:
            approval_reused = True
        else:
            approval_path.parent.mkdir(parents=True, exist_ok=True)
            approval_path.write_text(json.dumps(approval_preview, indent=2, default=str) + "\n", encoding="utf-8")
            approval_written = True

    approval_present = approval_path.is_file()
    ready_for_operator_decision = not blockers
    status = (
        "forge_rollback_approval_request_written"
        if approval_written
        else "forge_rollback_approval_request_existing_matching"
        if approval_reused or existing_matches
        else "forge_rollback_approval_request_ready"
        if ready_for_operator_decision
        else "blocked_forge_rollback_approval_request"
    )

    return {
        "ok": ready_for_operator_decision,
        "surface": ROLLBACK_APPROVAL_SURFACE_ID,
        "model_version": ROLLBACK_APPROVAL_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not approval_written,
        "approval_request_write_requested": write_approval_request,
        "approval_request_written": approval_written,
        "approval_request_reused": approval_reused,
        "approval_packet_id": packet_id,
        "request_digest_sha256": digest,
        "approval_artifact_path": _relative_to_vault(vault, approval_path),
        "approval_artifact_exists": approval_present,
        "approval_artifact_preview": approval_preview,
        "operator_confirmation_text": approval_preview["operator_confirmation_text"],
        "registry": registry,
        "live_registry_entry": live_registry_entry or {},
        "live_exact_once_marker_path": _relative_to_vault(vault, live_marker_path) if live_marker_path else "",
        "live_exact_once_marker_exists": bool(live_marker_path and live_marker_path.is_file()),
        "future_registry_path": _relative_to_vault(vault, registry_path),
        "future_rollback_exact_once_marker_path": _relative_to_vault(vault, marker_path),
        "future_extension_target_paths": target_paths,
        "manifest_validation": validation,
        "authority": {
            **dict(BLOCKED_AUTHORITY),
            "approval_request_write_requested": write_approval_request,
            "writes_approval_artifact": approval_written,
            "rollback_approval_request_surface_only": True,
            "rollback_executor_built": False,
            "rollback_allowed_in_this_pass": False,
            "rollback_requires_future_approved_executor": True,
        },
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-rollback-executor"
            if ready_for_operator_decision
            else "chaser-forge-live-install-executor"
        ),
    }


def _expected_rollback_artifact_paths(
    vault: Path,
    packet_id: str,
    approval_artifact_path: str | Path | None,
) -> tuple[Path | None, Path, Path, list[str]]:
    blockers: list[str] = []
    default_approval_path = _safe_json_path(vault, ROLLBACK_APPROVAL_RELATIVE_DIR, packet_id)
    marker_path = _safe_json_path(vault, ROLLBACK_MARKER_RELATIVE_DIR, packet_id)
    registry_path = (vault / REGISTRY_RELATIVE_PATH).resolve()
    approval_path = default_approval_path
    if approval_artifact_path:
        resolved, blocker = _resolve_under_base(vault, approval_artifact_path, ROLLBACK_APPROVAL_RELATIVE_DIR)
        if blocker:
            blockers.append("approval_artifact_path_outside_rollback_approval_root")
            approval_path = None
        else:
            approval_path = resolved
    return approval_path, marker_path, registry_path, blockers


def _approved_rollback_artifact_blockers(
    *,
    vault: Path,
    approval_path: Path | None,
    approval_payload: dict[str, Any] | None,
    packet_id: str,
    request_digest: str,
    expected_material: dict[str, Any],
    marker_path: Path,
    registry_path: Path,
) -> list[str]:
    blockers: list[str] = []
    if approval_payload is None:
        return ["approved_rollback_approval_artifact_missing"]
    if approval_payload.get("record_type") != ROLLBACK_APPROVAL_RECORD_TYPE:
        blockers.append("approval_record_type_mismatch")
    if approval_payload.get("schema_version") != ROLLBACK_APPROVAL_SCHEMA_VERSION:
        blockers.append("approval_schema_version_mismatch")
    if approval_payload.get("approval_packet_id") != packet_id:
        blockers.append("approval_packet_id_mismatch")
    if approval_payload.get("request_digest_sha256") != request_digest:
        blockers.append("approval_request_digest_mismatch")
    if approval_payload.get("approval_scope") != ROLLBACK_APPROVAL_SCOPE:
        blockers.append("approval_scope_mismatch")
    if approval_payload.get("status") != "approved":
        blockers.append("approval_status_not_approved")
    if approval_payload.get("operator_decision") != "approved":
        blockers.append("operator_decision_not_approved")
    if approval_payload.get("approval_consumed") is not False:
        blockers.append("approval_already_consumed")

    confirmation_text = str(approval_payload.get("operator_confirmation_text") or "").strip()
    approval_statement = str(approval_payload.get("operator_approval_statement") or "").strip()
    if not confirmation_text or approval_statement != confirmation_text:
        blockers.append("operator_approval_statement_missing_or_mismatched")

    approved_material = approval_payload.get("approved_material")
    if not isinstance(approved_material, dict):
        blockers.append("approved_material_missing")
    elif _sha256_payload(approved_material) != request_digest or _sha256_payload(expected_material) != request_digest:
        blockers.append("approved_material_digest_mismatch")

    if not _path_matches_expected(approval_payload.get("future_rollback_exact_once_marker_path"), marker_path):
        blockers.append("future_rollback_marker_path_mismatch")
    if not _path_matches_expected(approval_payload.get("future_registry_path"), registry_path):
        blockers.append("future_registry_path_mismatch")
    if approval_path is None:
        blockers.append("approval_artifact_path_missing")
    else:
        blockers.extend(
            _approval_decision_sidecar_blockers(
                vault=vault,
                approval_path=approval_path,
                approval_payload=approval_payload,
                family_id="rollback",
                packet_id=packet_id,
                request_digest=request_digest,
            )
        )
    return blockers


def _rolled_back_registry_entry(
    *,
    vault: Path,
    live_registry_entry: dict[str, Any],
    approval_packet_id: str,
    request_digest: str,
    marker_path: Path,
    generated_at: str,
    requested_by: str,
) -> dict[str, Any]:
    entry = deepcopy(live_registry_entry)
    prior_live_execution = entry.pop("live_execution", None)
    if prior_live_execution:
        history = list(entry.get("live_execution_history") or [])
        history.append(deepcopy(prior_live_execution))
        entry["live_execution_history"] = history
    entry.pop("live_activated_at", None)
    entry.update(
        {
            "registry_status": "sandbox_installed",
            "install_environment": "sandbox",
            "rolled_back_at": generated_at,
            "rollback_execution": {
                "schema_version": ROLLBACK_EXECUTION_SCHEMA_VERSION,
                "approval_packet_id": approval_packet_id,
                "request_digest_sha256": request_digest,
                "exact_once_marker_path": _relative_to_vault(vault, marker_path),
                "executed_at": generated_at,
                "executed_by": requested_by,
                "rolled_back_from_live": True,
                "restored_registry_status": "sandbox_installed",
                "restored_install_environment": "sandbox",
                "live_install": False,
                "rollback": True,
                "extension_files_deleted": [],
                "extension_files_written": [],
            },
            "authority": dict(BLOCKED_AUTHORITY),
        }
    )
    return entry


def build_rollback_execution(
    vault_root: str | Path,
    *,
    manifest: dict[str, Any] | None = None,
    approval_packet_id: str | None = None,
    request_digest: str | None = None,
    approval_artifact_path: str | Path | None = None,
    execute: bool = False,
    requested_by: str = "Codex",
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Consume an approved Forge rollback request and return live registry state to sandbox.

    This executor writes only Forge registry rollback metadata, a rollback
    exact-once marker, and consumed status metadata on the approved rollback
    artifact. It does not delete extension files or write protected core paths.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    manifest_payload = deepcopy(manifest) if manifest is not None else load_demo_manifest()
    validation = validate_manifest(manifest_payload)
    path_guard = (validation.get("protectedCore") or {}).get("targetPathValidation") or {}
    target_paths = list(path_guard.get("normalized_paths") or [])
    extension_id = str(manifest_payload.get("id") or "invalid-extension")
    registry = build_extension_registry(vault)
    live_registry_entry = _registry_entry_for_extension(registry, extension_id)
    live_marker_path, live_marker, marker_blockers = _live_marker_payload(vault, live_registry_entry or {})
    material = _rollback_material(
        manifest=manifest_payload,
        validation=validation,
        live_registry_entry=live_registry_entry,
        live_marker_path=live_marker_path,
        target_paths=target_paths,
    )
    expected_digest = _sha256_payload(material)
    supplied_digest = str(request_digest or "")
    packet_digest = supplied_digest or expected_digest
    packet_id = approval_packet_id or f"forge-rollback-appr-{_safe_identifier(extension_id)}-{packet_digest[:12]}"
    approval_path, marker_path, registry_path, blockers = _expected_rollback_artifact_paths(
        vault,
        packet_id,
        approval_artifact_path,
    )
    approval_payload = _read_json(approval_path) if approval_path and approval_path.is_file() else None
    registry_payload, registry_blockers = _load_registry_for_write(registry_path, timestamp)
    registry_entries = list((registry_payload or {}).get("entries") or []) if registry_payload else []
    registry_entry_index: int | None = None
    registry_entry_for_write: dict[str, Any] | None = None
    for index, entry in enumerate(registry_entries):
        if isinstance(entry, dict) and entry.get("extension_id") == extension_id:
            registry_entry_index = index
            registry_entry_for_write = entry
            break

    approval_preview = _rollback_approval_artifact_payload(
        packet_id=packet_id,
        request_digest=expected_digest,
        material=material,
        approval_path=approval_path or _safe_json_path(vault, ROLLBACK_APPROVAL_RELATIVE_DIR, packet_id),
        marker_path=marker_path,
        registry_path=registry_path,
        requested_by=requested_by,
        generated_at=timestamp,
    )

    blockers.extend(
        _live_proof_blockers(
            vault=vault,
            manifest=manifest_payload,
            validation=validation,
            registry=registry,
            registry_entry=live_registry_entry,
            live_marker_payload=live_marker,
            target_paths=target_paths,
        )
    )
    blockers.extend(marker_blockers)
    blockers.extend(registry_blockers)
    if supplied_digest != expected_digest:
        blockers.append("request_digest_required_or_mismatched")
    if marker_path.exists():
        blockers.append("rollback_exact_once_marker_already_present")
    if registry_entry_for_write is None:
        blockers.append("live_registry_entry_missing")
    elif registry_entry_for_write.get("registry_status") != "live_installed" or registry_entry_for_write.get("install_environment") != "live":
        blockers.append("live_registry_entry_not_installed")
    elif registry_entry_for_write.get("rollback_execution"):
        blockers.append("rollback_execution_already_recorded")
    blockers.extend(
        _approved_rollback_artifact_blockers(
            vault=vault,
            approval_path=approval_path,
            approval_payload=approval_payload,
            packet_id=packet_id,
            request_digest=expected_digest,
            expected_material=material,
            marker_path=marker_path,
            registry_path=registry_path,
        )
    )
    blockers = list(dict.fromkeys(blockers))
    ready_for_execution = not blockers

    rolled_back_registry_entry_preview = _rolled_back_registry_entry(
        vault=vault,
        live_registry_entry=live_registry_entry
        or build_registry_entry(
            manifest_payload,
            validation,
            registry_status="live_installed",
            install_environment="live",
            generated_at=timestamp,
        ),
        approval_packet_id=packet_id,
        request_digest=expected_digest,
        marker_path=marker_path,
        generated_at=timestamp,
        requested_by=requested_by,
    )
    registry_updated = False
    exact_once_marker_written = False
    approval_consumed = False
    rollback_executed = False
    marker_payload = {
        "record_type": ROLLBACK_MARKER_RECORD_TYPE,
        "schema_version": ROLLBACK_EXECUTION_SCHEMA_VERSION,
        "status": "preview",
        "generated_at": timestamp,
        "approval_packet_id": packet_id,
        "request_digest_sha256": expected_digest,
        "extension_id": extension_id,
        "target_paths": target_paths,
        "live_exact_once_marker_path": _relative_to_vault(vault, live_marker_path) if live_marker_path else "",
        "reserved_before_writes": False,
        "completed": False,
    }

    if (
        execute
        and ready_for_execution
        and registry_payload is not None
        and approval_path is not None
        and registry_entry_index is not None
        and registry_entry_for_write is not None
    ):
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_payload = {
            **marker_payload,
            "status": "reserved",
            "reserved_at": timestamp,
            "reserved_by": requested_by,
            "reserved_before_writes": True,
        }
        with marker_path.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(marker_payload, indent=2, default=str) + "\n")
        exact_once_marker_written = True

        rolled_back_entry = _rolled_back_registry_entry(
            vault=vault,
            live_registry_entry=registry_entry_for_write,
            approval_packet_id=packet_id,
            request_digest=expected_digest,
            marker_path=marker_path,
            generated_at=timestamp,
            requested_by=requested_by,
        )
        registry_entries[registry_entry_index] = rolled_back_entry
        registry_payload["entries"] = registry_entries
        registry_payload["status"] = "sandbox_registry_contains_entries"
        registry_payload["updated_at"] = timestamp
        registry_payload["approved_rollback_executor_built"] = True
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(json.dumps(registry_payload, indent=2, default=str) + "\n", encoding="utf-8")
        registry_updated = True
        rollback_executed = True
        rolled_back_registry_entry_preview = rolled_back_entry

        consumed_payload = dict(approval_payload)
        consumed_payload.update(
            {
                "status": "consumed",
                "approval_consumed": True,
                "consumed_at": timestamp,
                "consumed_by": requested_by,
                "rollback_allowed_in_this_pass": True,
                "rollback_executor_built": True,
                "registry_write_allowed_in_this_pass": True,
                "extension_file_write_allowed_in_this_pass": False,
                "extension_file_delete_allowed_in_this_pass": False,
                "executes_rollback": True,
                "writes_extension_registry": True,
                "writes_extension_files": False,
                "consumes_approval": True,
                "reserves_exact_once_marker": True,
                "rollback_execution_result": {
                    "schema_version": ROLLBACK_EXECUTION_SCHEMA_VERSION,
                    "exact_once_marker_path": _relative_to_vault(vault, marker_path),
                    "registry_path": _relative_to_vault(vault, registry_path),
                    "extension_files_deleted": [],
                    "extension_files_written": [],
                    "rollback": True,
                },
            }
        )
        approval_path.write_text(json.dumps(consumed_payload, indent=2, default=str) + "\n", encoding="utf-8")
        approval_consumed = True

        marker_payload = {
            **marker_payload,
            "status": "completed",
            "completed": True,
            "completed_at": timestamp,
            "registry_path": _relative_to_vault(vault, registry_path),
            "rolled_back_registry_entry_digest_sha256": _sha256_payload(rolled_back_entry),
            "extension_files_deleted": [],
            "extension_files_written": [],
        }
        marker_path.write_text(json.dumps(marker_payload, indent=2, default=str) + "\n", encoding="utf-8")

    status = (
        "forge_rollback_executed"
        if rollback_executed
        else "forge_rollback_execution_ready"
        if ready_for_execution
        else "blocked_forge_rollback_execution"
    )

    return {
        "ok": ready_for_execution,
        "surface": ROLLBACK_EXECUTION_SURFACE_ID,
        "model_version": ROLLBACK_EXECUTION_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "execute_requested": execute,
        "approval_packet_id": packet_id,
        "request_digest_sha256": expected_digest,
        "approval_artifact_path": _relative_to_vault(vault, approval_path) if approval_path else "",
        "approval_artifact_exists": bool(approval_path and approval_path.is_file()),
        "registry_path": _relative_to_vault(vault, registry_path),
        "registry_updated": registry_updated,
        "registry_written": registry_updated,
        "rollback_executed": rollback_executed,
        "rolled_back_registry_entry_preview": rolled_back_registry_entry_preview,
        "extension_target_paths": target_paths,
        "extension_files_deleted": [],
        "extension_files_written": [],
        "live_registry_entry": live_registry_entry or {},
        "live_exact_once_marker_path": _relative_to_vault(vault, live_marker_path) if live_marker_path else "",
        "live_exact_once_marker_exists": bool(live_marker_path and live_marker_path.is_file()),
        "future_rollback_exact_once_marker_path": _relative_to_vault(vault, marker_path),
        "exact_once_marker_exists": marker_path.is_file(),
        "exact_once_marker_written": exact_once_marker_written,
        "approval_consumed": approval_consumed,
        "approval_artifact_preview": approval_preview,
        "operator_confirmation_text": approval_preview["operator_confirmation_text"],
        "manifest_validation": validation,
        "authority": {
            **dict(BLOCKED_AUTHORITY),
            "executes_rollback": rollback_executed,
            "writes_extension_registry": registry_updated,
            "writes_extension_files": False,
            "deletes_extension_files": False,
            "consumes_approval": approval_consumed,
            "reserves_exact_once_marker": exact_once_marker_written,
            "executes_sandbox_install": False,
            "executes_live_install": False,
            "mutates_protected_core": False,
            "mutates_studio_shell": False,
            "mutates_runtime_policy": False,
            "activates_schedule": False,
            "writes_agent_bus_task": False,
            "reads_secret_or_credential": False,
            "calls_provider_or_model": False,
            "calls_external_connector": False,
            "canonical_mutation_allowed": False,
        },
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-approval-center-routing"
            if rollback_executed
            else "chaser-forge-rollback-operator-decision"
            if ready_for_execution
            else "chaser-forge-live-install-executor"
        ),
    }
