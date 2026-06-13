"""Source-specific decision handoff for Chaser Forge approval artifacts."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.forge.registry import (
    BLOCKED_AUTHORITY,
    LIVE_INSTALL_APPROVAL_RECORD_TYPE,
    LIVE_INSTALL_APPROVAL_RELATIVE_DIR,
    LIVE_INSTALL_APPROVAL_SCOPE,
    ROLLBACK_APPROVAL_RECORD_TYPE,
    ROLLBACK_APPROVAL_RELATIVE_DIR,
    ROLLBACK_APPROVAL_SCOPE,
    SANDBOX_APPROVAL_RECORD_TYPE,
    SANDBOX_APPROVAL_RELATIVE_DIR,
    SANDBOX_APPROVAL_SCOPE,
)
from runtime.forge.marketplace import (
    FORGE_MARKETPLACE_IMPORT_APPROVAL_RECORD_TYPE,
    FORGE_MARKETPLACE_IMPORT_APPROVAL_RELATIVE_DIR,
    FORGE_MARKETPLACE_IMPORT_APPROVAL_SCOPE,
)


FORGE_APPROVAL_DECISION_SCHEMA_VERSION = "forge.approval_decision.v1"
FORGE_APPROVAL_DECISION_SURFACE_ID = "chaser_forge_approval_center_decision_handoff"
FORGE_APPROVAL_DECISION_RECORD_TYPE = "forge_approval_decision_handoff"
FORGE_APPROVAL_DECISION_API_METHOD = "review_chaser_forge_approval_decision"
SUPPORTED_DECISIONS = ("approved", "rejected")


_FAMILY_SPECS: dict[str, dict[str, Any]] = {
    "sandbox": {
        "label": "Forge Sandbox Approval",
        "approval_root": SANDBOX_APPROVAL_RELATIVE_DIR,
        "decision_root": SANDBOX_APPROVAL_RELATIVE_DIR / "_decisions",
        "record_type": SANDBOX_APPROVAL_RECORD_TYPE,
        "scope": SANDBOX_APPROVAL_SCOPE,
    },
    "live-install": {
        "label": "Forge Live Install Approval",
        "approval_root": LIVE_INSTALL_APPROVAL_RELATIVE_DIR,
        "decision_root": LIVE_INSTALL_APPROVAL_RELATIVE_DIR / "_decisions",
        "record_type": LIVE_INSTALL_APPROVAL_RECORD_TYPE,
        "scope": LIVE_INSTALL_APPROVAL_SCOPE,
    },
    "rollback": {
        "label": "Forge Rollback Approval",
        "approval_root": ROLLBACK_APPROVAL_RELATIVE_DIR,
        "decision_root": ROLLBACK_APPROVAL_RELATIVE_DIR / "_decisions",
        "record_type": ROLLBACK_APPROVAL_RECORD_TYPE,
        "scope": ROLLBACK_APPROVAL_SCOPE,
    },
    "marketplace-import": {
        "label": "Forge Marketplace Import Sandbox Review",
        "approval_root": FORGE_MARKETPLACE_IMPORT_APPROVAL_RELATIVE_DIR,
        "decision_root": FORGE_MARKETPLACE_IMPORT_APPROVAL_RELATIVE_DIR / "_decisions",
        "record_type": FORGE_MARKETPLACE_IMPORT_APPROVAL_RECORD_TYPE,
        "scope": FORGE_MARKETPLACE_IMPORT_APPROVAL_SCOPE,
    },
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _rel(vault: Path, path: Path) -> str:
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
    return safe or "forge-decision"


def _normalize_decision(value: str) -> str | None:
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized in {"approve", "approved"}:
        return "approved"
    if normalized in {"reject", "rejected", "deny", "denied"}:
        return "rejected"
    return None


def _resolve_forge_artifact(vault: Path, path_value: str | Path | None) -> tuple[Path | None, str | None, list[str]]:
    blockers: list[str] = []
    if path_value in (None, ""):
        return None, None, ["approval_artifact_path_required"]

    raw_path = Path(str(path_value))
    path = raw_path.resolve() if raw_path.is_absolute() else (vault / raw_path).resolve()
    for family_id, spec in _FAMILY_SPECS.items():
        approval_root = (vault / spec["approval_root"]).resolve()
        try:
            relative = path.relative_to(approval_root)
        except ValueError:
            continue
        if len(relative.parts) != 1 or path.suffix.lower() != ".json":
            blockers.append("approval_artifact_path_must_be_direct_forge_request_json")
        return path, family_id, blockers
    return None, None, ["approval_artifact_path_outside_forge_approval_roots"]


def forge_rejection_confirmation_text(payload: dict[str, Any], family_id: str) -> str:
    """Return the exact rejection statement required for a Forge approval artifact."""

    lines = [
        "REJECT FORGE APPROVAL REQUEST ONLY:",
        f"- approval_packet_id: {payload.get('approval_packet_id') or 'unknown'}",
        f"- request_digest_sha256: {payload.get('request_digest_sha256') or 'unknown'}",
        f"- approval_family: {family_id}",
        f"- extension_id: {payload.get('extension_id') or 'unknown-extension'}",
        "",
        "No approval consumption.",
        "No Forge execution.",
        "No registry write.",
        "No extension file mutation.",
        "No exact-once marker reservation.",
        "No protected-core, Studio shell, runtime policy, schedule, Agent Bus, provider, credential, external connector, or canonical mutation.",
    ]
    return "\n".join(lines)


def _pending_request_blockers(payload: dict[str, Any] | None, family_id: str) -> list[str]:
    if payload is None:
        return ["approval_artifact_missing_or_unreadable"]

    spec = _FAMILY_SPECS[family_id]
    blockers: list[str] = []
    if payload.get("record_type") != spec["record_type"]:
        blockers.append("approval_record_type_mismatch")
    if payload.get("approval_scope") != spec["scope"]:
        blockers.append("approval_scope_mismatch")
    if payload.get("status") != "pending_operator_decision":
        blockers.append("approval_status_not_pending_operator_decision")
    if payload.get("operator_decision") != "pending":
        blockers.append("operator_decision_not_pending")
    if payload.get("approval_consumed") is not False:
        blockers.append("approval_already_consumed_or_unknown")
    if not payload.get("approval_packet_id"):
        blockers.append("approval_packet_id_missing")
    if not payload.get("request_digest_sha256"):
        blockers.append("request_digest_missing")
    if not str(payload.get("operator_confirmation_text") or "").strip():
        blockers.append("operator_confirmation_text_missing")
    if not isinstance(payload.get("approved_material"), dict):
        blockers.append("approved_material_missing")
    return blockers


def _decision_artifact_path(vault: Path, family_id: str, payload: dict[str, Any], decision: str) -> Path:
    spec = _FAMILY_SPECS[family_id]
    packet_id = _safe_identifier(str(payload.get("approval_packet_id") or "forge-approval"))[:32]
    digest = _safe_identifier(str(payload.get("request_digest_sha256") or "missing"))[:12]
    filename = f"{packet_id}-{digest}-{decision}.json"
    return (vault / spec["decision_root"] / filename).resolve()


def _decision_record(
    *,
    vault: Path,
    source_artifact_path: Path,
    decision_artifact_path: Path,
    payload: dict[str, Any],
    family_id: str,
    decision: str,
    operator_statement: str,
    reviewer_id: str,
    reason: str,
    generated_at: str,
) -> dict[str, Any]:
    record = {
        "record_type": FORGE_APPROVAL_DECISION_RECORD_TYPE,
        "schema_version": FORGE_APPROVAL_DECISION_SCHEMA_VERSION,
        "generated_at": generated_at,
        "status": "forge_approval_decision_recorded",
        "surface": FORGE_APPROVAL_DECISION_SURFACE_ID,
        "api_method": FORGE_APPROVAL_DECISION_API_METHOD,
        "source_specific": True,
        "generic_approval_center_control": False,
        "family": family_id,
        "operator_decision": decision,
        "reviewer_id": reviewer_id,
        "reason": reason,
        "operator_statement": operator_statement,
        "source_approval_artifact_path": _rel(vault, source_artifact_path),
        "decision_artifact_path": _rel(vault, decision_artifact_path),
        "source_approval_record_type": payload.get("record_type"),
        "source_approval_schema_version": payload.get("schema_version"),
        "approval_scope": payload.get("approval_scope"),
        "approval_packet_id": payload.get("approval_packet_id"),
        "request_digest_sha256": payload.get("request_digest_sha256"),
        "extension_id": payload.get("extension_id"),
        "extension_name": payload.get("extension_name"),
        "extension_version": payload.get("extension_version"),
        "decision_effect": "updates the source Forge approval artifact decision fields only; source-specific executors must still revalidate before any future consumption",
        "approval_artifact_mutation": {
            "allowed": True,
            "status_after": decision,
            "approval_consumed_after": False,
        },
        "approval_consumed": False,
        "forge_execution_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "extension_files_deleted": [],
        "exact_once_marker_reserved": False,
        "protected_core_mutation_allowed": False,
        "runtime_policy_mutation_allowed": False,
        "schedule_activation_allowed": False,
        "agent_bus_dispatch_allowed": False,
        "provider_call_allowed": False,
        "connector_call_allowed": False,
        "canonical_mutation_allowed": False,
        "authority": {
            **dict(BLOCKED_AUTHORITY),
            "writes_review_decision": True,
            "writes_approval_artifact": True,
            "approval_decision_handoff_only": True,
            "consumes_approval": False,
            "executes_forge": False,
            "writes_extension_registry": False,
            "writes_extension_files": False,
            "reserves_exact_once_marker": False,
        },
    }
    record["decision_record_digest_sha256"] = _sha256_payload(record)
    return record


def _updated_approval_payload(
    *,
    payload: dict[str, Any],
    family_id: str,
    decision: str,
    decision_record: dict[str, Any],
    operator_statement: str,
    reviewer_id: str,
    generated_at: str,
) -> dict[str, Any]:
    updated = deepcopy(payload)
    updated["status"] = decision
    updated["operator_decision"] = decision
    updated["approval_consumed"] = False
    updated["approval_decision_recorded"] = True
    updated["approval_decision_family"] = family_id
    updated["decision_artifact_path"] = decision_record["decision_artifact_path"]
    updated["approval_decision_digest_sha256"] = decision_record["decision_record_digest_sha256"]
    updated["approval_decision_record_type"] = FORGE_APPROVAL_DECISION_RECORD_TYPE
    updated["approval_decision_recorded_at"] = generated_at
    updated["approval_decision_handoff"] = {
        "surface": FORGE_APPROVAL_DECISION_SURFACE_ID,
        "api_method": FORGE_APPROVAL_DECISION_API_METHOD,
        "source_specific": True,
        "generic_approval_center_control": False,
        "decision_artifact_path": decision_record["decision_artifact_path"],
        "decision_record_digest_sha256": decision_record["decision_record_digest_sha256"],
        "approval_consumed": False,
        "forge_execution_allowed": False,
    }
    if decision == "approved":
        updated["operator_approval_statement"] = operator_statement
        updated["approved_at"] = generated_at
        updated["approved_by"] = reviewer_id
    else:
        updated["operator_rejection_statement"] = operator_statement
        updated["rejected_at"] = generated_at
        updated["rejected_by"] = reviewer_id
    return updated


def build_forge_approval_decision_handoff(
    vault_root: str | Path,
    *,
    approval_artifact_path: str | Path | None,
    decision: str,
    expected_request_digest: str | None = None,
    operator_statement: str | None = None,
    reviewer_id: str = "operator",
    reason: str | None = None,
    write_decision: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Preview or write an approve/reject decision for one Forge approval artifact.

    This source-specific handoff records a decision and updates the source Forge
    approval artifact. It never consumes approvals, executes Forge work, writes
    the registry, writes extension files, or reserves exact-once markers.
    """

    vault = _vault_path(vault_root)
    timestamp = generated_at or _now_utc()
    resolved_path, family_id, blockers = _resolve_forge_artifact(vault, approval_artifact_path)
    normalized_decision = _normalize_decision(decision)
    if normalized_decision is None:
        blockers.append("decision_must_be_approved_or_rejected")

    payload = _read_json(resolved_path) if resolved_path and resolved_path.is_file() else None
    if resolved_path is None or family_id is None:
        payload = None
    else:
        blockers.extend(_pending_request_blockers(payload, family_id))

    decision_path: Path | None = None
    required_statement = ""
    decision_record: dict[str, Any] | None = None
    source_update_preview: dict[str, Any] | None = None
    if payload is not None and family_id is not None and normalized_decision is not None:
        request_digest = str(payload.get("request_digest_sha256") or "")
        if expected_request_digest:
            if expected_request_digest != request_digest:
                blockers.append("expected_request_digest_mismatch")
        elif write_decision:
            blockers.append("expected_request_digest_required")

        if normalized_decision == "approved":
            required_statement = str(payload.get("operator_confirmation_text") or "").strip()
            if write_decision and str(operator_statement or "").strip() != required_statement:
                blockers.append("operator_approval_statement_missing_or_mismatched")
        else:
            required_statement = forge_rejection_confirmation_text(payload, family_id)
            if write_decision and str(operator_statement or "").strip() != required_statement:
                blockers.append("operator_rejection_statement_missing_or_mismatched")

        if write_decision and not str(operator_statement or "").strip():
            blockers.append("operator_statement_required")

        decision_path = _decision_artifact_path(vault, family_id, payload, normalized_decision)
        if decision_path.exists():
            blockers.append("decision_artifact_already_present")

        statement = str(operator_statement or "").strip()
        if not statement and not write_decision:
            statement = required_statement
        decision_record = _decision_record(
            vault=vault,
            source_artifact_path=resolved_path,
            decision_artifact_path=decision_path,
            payload=payload,
            family_id=family_id,
            decision=normalized_decision,
            operator_statement=statement,
            reviewer_id=reviewer_id,
            reason=str(reason or ""),
            generated_at=timestamp,
        )
        source_update_preview = _updated_approval_payload(
            payload=payload,
            family_id=family_id,
            decision=normalized_decision,
            decision_record=decision_record,
            operator_statement=statement,
            reviewer_id=reviewer_id,
            generated_at=timestamp,
        )

    blockers = list(dict.fromkeys(blockers))
    can_record = not blockers
    decision_written = False
    approval_mutated = False
    if write_decision and can_record and decision_path is not None and resolved_path is not None and source_update_preview is not None:
        decision_path.parent.mkdir(parents=True, exist_ok=True)
        decision_path.write_text(json.dumps(decision_record, indent=2, ensure_ascii=True, default=str) + "\n", encoding="utf-8")
        resolved_path.write_text(json.dumps(source_update_preview, indent=2, ensure_ascii=True, default=str) + "\n", encoding="utf-8")
        decision_written = True
        approval_mutated = True

    status = (
        "forge_approval_decision_recorded"
        if decision_written
        else "forge_approval_decision_preview_ready"
        if can_record
        else "blocked_forge_approval_decision_handoff"
    )

    return {
        "ok": can_record,
        "surface": FORGE_APPROVAL_DECISION_SURFACE_ID,
        "model_version": FORGE_APPROVAL_DECISION_SCHEMA_VERSION,
        "status": status,
        "generated_at": timestamp,
        "vault_root": str(vault),
        "preview_only": not decision_written,
        "write_decision_requested": bool(write_decision),
        "decision_artifact_written": decision_written,
        "approval_artifact_mutated": approval_mutated,
        "source_specific": True,
        "generic_approval_center_control": False,
        "family": family_id or "",
        "decision": normalized_decision or "",
        "supported_decisions": list(SUPPORTED_DECISIONS),
        "approval_packet_id": payload.get("approval_packet_id") if payload else "",
        "request_digest_sha256": payload.get("request_digest_sha256") if payload else "",
        "expected_request_digest_sha256": expected_request_digest or "",
        "source_approval_artifact_path": _rel(vault, resolved_path) if resolved_path else str(approval_artifact_path or ""),
        "decision_artifact_path": _rel(vault, decision_path) if decision_path else "",
        "required_operator_statement": required_statement,
        "decision_record_preview": decision_record or {},
        "source_update_preview": source_update_preview or {},
        "approval_consumed": False,
        "forge_execution_allowed": False,
        "registry_written": False,
        "extension_files_written": [],
        "extension_files_deleted": [],
        "exact_once_marker_reserved": False,
        "authority": {
            **dict(BLOCKED_AUTHORITY),
            "writes_review_decision": bool(write_decision and decision_written),
            "writes_approval_artifact": bool(write_decision and approval_mutated),
            "approval_decision_handoff_only": True,
            "consumes_approval": False,
            "executes_forge": False,
            "writes_extension_registry": False,
            "writes_extension_files": False,
            "reserves_exact_once_marker": False,
        },
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-decision-bound-executor-consumption-proof"
            if can_record
            else "chaser-forge-approval-decision-handoff-repair"
        ),
    }
