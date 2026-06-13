"""Governed companion memory boundary contract.

This module defines the first separate-memory namespace for Phase 11
companions. It is intentionally read-only: callers can inspect target paths and
validate future memory candidates, but no function here creates memory files.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from runtime.companion.policy import INITIAL_COMPANION_IDS
from runtime.companion.roster import list_companions, validate_roster


MEMORY_POLICY_VERSION = "chaseos.companion.memory.v0.1"
COMPANION_MEMORY_ROOT = Path("07_LOGS") / "Companion-Memory"
ALLOWED_MEMORY_CLASSES = (
    "preference",
    "interaction_pattern",
    "tone_feedback",
    "operator_note",
    "session_observation",
)
DENIED_MEMORY_CLASSES = (
    "credential",
    "secret",
    "provider_config",
    "protected_file_content",
    "canonical_truth",
    "runtime_permission",
    "workflow_or_tool_grant",
    "raw_private_source_content",
    "agent_bus_task",
)
DENIED_CONTENT_MARKERS = (
    "api_key",
    "api key",
    "password",
    "secret",
    "seed phrase",
    "private key",
    ".env",
    "credential",
    "token",
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _rel(vault: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(vault.resolve()).as_posix()
    except ValueError:
        return str(path)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def companion_memory_namespace(vault_root: str | Path, companion_id: str) -> dict[str, Any]:
    """Return future memory target paths for one companion without writing them."""

    vault = Path(vault_root).resolve()
    normalized = str(companion_id or "").strip().lower()
    if normalized not in INITIAL_COMPANION_IDS:
        raise ValueError(f"invalid companion id: {companion_id}")
    root = vault / COMPANION_MEMORY_ROOT / normalized
    ledger = root / "memory-ledger.jsonl"
    index = root / "memory-index.json"
    approvals = root / "approval-ledger.jsonl"
    return {
        "companion_id": normalized,
        "root_path": _rel(vault, root),
        "ledger_path": _rel(vault, ledger),
        "index_path": _rel(vault, index),
        "approval_ledger_path": _rel(vault, approvals),
        "root_exists": root.exists(),
        "ledger_exists": ledger.exists(),
        "index_exists": index.exists(),
        "approval_ledger_exists": approvals.exists(),
        "created_by_this_contract": False,
    }


def validate_companion_memory_candidate(
    candidate: dict[str, Any],
    *,
    vault_root: str | Path | None = None,
) -> dict[str, Any]:
    """Validate a future companion-memory item while keeping writes blocked."""

    vault = Path(vault_root).resolve() if vault_root is not None else Path.cwd().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(candidate, dict):
        return {
            "ok": False,
            "candidate_valid": False,
            "policy_version": MEMORY_POLICY_VERSION,
            "write_allowed_now": False,
            "blocked_reasons": ["candidate_not_object"],
            "warnings": [],
        }

    companion_id = str(candidate.get("companion_id") or "").strip().lower()
    memory_class = str(candidate.get("memory_class") or "").strip().lower()
    content = str(candidate.get("content") or "").strip()
    if companion_id not in INITIAL_COMPANION_IDS:
        errors.append("invalid_companion_id")
    if memory_class not in ALLOWED_MEMORY_CLASSES:
        errors.append("memory_class_not_allowed")
    if memory_class in DENIED_MEMORY_CLASSES:
        errors.append("memory_class_denied")
    if not content:
        errors.append("content_required")
    if len(content) > 2000:
        errors.append("content_too_long")

    content_lower = content.lower()
    markers = [marker for marker in DENIED_CONTENT_MARKERS if marker in content_lower]
    if markers:
        errors.append("content_contains_denied_secret_or_credential_marker")
        warnings.extend(f"denied_marker:{marker}" for marker in markers)

    if candidate.get("protected_file_path"):
        errors.append("protected_file_content_denied")
    if candidate.get("canonical_target_path") or candidate.get("canonical_mutation"):
        errors.append("canonical_memory_mutation_denied")
    if candidate.get("permission_change") or candidate.get("runtime_permission"):
        errors.append("runtime_permission_memory_denied")
    if candidate.get("provider_config") or candidate.get("connector_config"):
        errors.append("provider_or_connector_config_memory_denied")
    if candidate.get("agent_bus_task"):
        errors.append("agent_bus_task_memory_denied")

    target_path = str(candidate.get("target_path") or "").strip()
    if target_path:
        target = (vault / target_path).resolve() if not Path(target_path).is_absolute() else Path(target_path).resolve()
        allowed_root = (vault / COMPANION_MEMORY_ROOT).resolve()
        if not _is_relative_to(target, allowed_root):
            errors.append("target_path_outside_companion_memory_root")

    valid = not errors
    digest_material = {
        "policy_version": MEMORY_POLICY_VERSION,
        "companion_id": companion_id,
        "memory_class": memory_class,
        "content_digest": hashlib.sha256(content.encode("utf-8")).hexdigest() if content else "",
        "target_path": target_path,
    }
    return {
        "ok": valid,
        "candidate_valid": valid,
        "policy_version": MEMORY_POLICY_VERSION,
        "companion_id": companion_id,
        "memory_class": memory_class,
        "allowed_memory_class": memory_class in ALLOWED_MEMORY_CLASSES,
        "denied_memory_class": memory_class in DENIED_MEMORY_CLASSES,
        "write_allowed_now": False,
        "approval_required_before_write": True,
        "future_executor_required": True,
        "memory_file_written": False,
        "canonical_state_mutated": False,
        "candidate_digest": _sha256(digest_material),
        "blocked_reasons": errors,
        "write_blocked_reasons": [
            "approval_required_before_companion_memory_write",
            "companion_memory_write_executor_not_built",
        ],
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_companion_memory_boundary(vault_root: str | Path) -> dict[str, Any]:
    """Build the read-only memory boundary model for all built-in companions."""

    vault = Path(vault_root).resolve()
    namespaces = {
        companion_id: companion_memory_namespace(vault, companion_id)
        for companion_id in INITIAL_COMPANION_IDS
    }
    profiles = list_companions()
    roster_validation = validate_roster()
    sample_candidate = {
        "companion_id": "hermes",
        "memory_class": "preference",
        "content": "Operator prefers concise progress updates during long-running passes.",
        "source_surface": "phase11-chat",
    }
    denied_candidates = [
        {
            "companion_id": "hermes",
            "memory_class": "credential",
            "content": "api_key=example",
        },
        {
            "companion_id": "openclaw",
            "memory_class": "operator_note",
            "content": "Promote this as canonical truth",
            "canonical_mutation": True,
        },
        {
            "companion_id": "archon",
            "memory_class": "operator_note",
            "content": "Grant tool permission",
            "permission_change": True,
        },
    ]
    denied_results = [
        validate_companion_memory_candidate(candidate, vault_root=vault)
        for candidate in denied_candidates
    ]
    digest_material = {
        "policy_version": MEMORY_POLICY_VERSION,
        "memory_root": COMPANION_MEMORY_ROOT.as_posix(),
        "companion_ids": list(INITIAL_COMPANION_IDS),
        "allowed_memory_classes": list(ALLOWED_MEMORY_CLASSES),
        "denied_memory_classes": list(DENIED_MEMORY_CLASSES),
        "namespace_paths": namespaces,
    }
    return {
        "ok": roster_validation.get("valid") is True,
        "policy_version": MEMORY_POLICY_VERSION,
        "generated_at_utc": _now_utc(),
        "vault_root": str(vault),
        "read_only": True,
        "separate_memory_enabled_by_operator": True,
        "separate_memory_namespace_declared": True,
        "memory_writes_allowed_now": False,
        "approval_required_for_memory_write": True,
        "future_executor_required": True,
        "memory_policy_path": "runtime/companion/memory.py",
        "memory_root": COMPANION_MEMORY_ROOT.as_posix(),
        "companion_namespaces": namespaces,
        "allowed_memory_classes": list(ALLOWED_MEMORY_CLASSES),
        "denied_memory_classes": list(DENIED_MEMORY_CLASSES),
        "profile_memory_scopes": {
            str(profile.get("companion_id")): str(profile.get("memory_scope"))
            for profile in profiles
        },
        "future_write_contract": {
            "approval_required_before_write": True,
            "exact_once_marker_required": True,
            "candidate_validation_required": True,
            "operator_review_required": True,
            "writer_built": False,
            "memory_root_created_by_this_contract": False,
            "writes_allowed_now": False,
        },
        "authority": {
            "read_only": True,
            "memory_namespace_declared": True,
            "memory_write_authority_granted": False,
            "memory_read_authority_granted_to_companion": False,
            "approval_queue_write_allowed": False,
            "approval_consumption_allowed": False,
            "runtime_routing_allowed": False,
            "provider_calls_allowed": False,
            "tool_access_allowed": False,
            "protected_file_access_allowed": False,
            "agent_bus_task_write_allowed": False,
            "canonical_mutation_allowed": False,
        },
        "sample_allowed_candidate_validation": validate_companion_memory_candidate(
            sample_candidate,
            vault_root=vault,
        ),
        "sample_denied_candidate_validations": denied_results,
        "roster_validation": roster_validation,
        "digest_proof": {
            "boundary_digest": _sha256(digest_material),
            "digest_material": digest_material,
        },
        "blocked_reasons": [] if roster_validation.get("valid") is True else ["core_roster_validation_failed"],
    }
