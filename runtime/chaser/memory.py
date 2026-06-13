"""
runtime.chaser.memory

Read-only memory/bootstrap boundary previews for ChaserAgent Phase A.
No memory root is created and no memory item is written by this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.chaser.policies import CHASER_RUNTIME_ID, build_no_authority_report


CHASER_MEMORY_ROOT = Path("07_LOGS") / "Chaser-Memory"

ALLOWED_REFERENCE_CLASSES = (
    "profile_reference",
    "session_reference",
    "artifact_reference",
    "operator_note_candidate",
)

DENIED_REFERENCE_CLASSES = (
    "credential",
    "secret",
    "permission_change",
    "canonical_mutation",
    "agent_bus_task",
)


def build_memory_boundary(vault_root: str | Path) -> dict[str, Any]:
    vault = Path(vault_root).resolve()
    root = vault / CHASER_MEMORY_ROOT
    return {
        "runtime_id": CHASER_RUNTIME_ID,
        "memory_root": CHASER_MEMORY_ROOT.as_posix(),
        "root_exists": root.exists(),
        "read_only": True,
        "memory_writes_allowed_now": False,
        "future_executor_required": True,
        "allowed_reference_classes": list(ALLOWED_REFERENCE_CLASSES),
        "denied_reference_classes": list(DENIED_REFERENCE_CLASSES),
        "authority": build_no_authority_report(),
    }


def validate_memory_reference(candidate: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(candidate, dict):
        return {
            "ok": False,
            "candidate_valid": False,
            "write_allowed_now": False,
            "blocked_reasons": ["candidate_not_object"],
        }
    ref_class = str(candidate.get("reference_class") or "").strip().lower()
    target = str(candidate.get("target") or "").strip()
    if ref_class not in ALLOWED_REFERENCE_CLASSES:
        errors.append("reference_class_not_allowed")
    if ref_class in DENIED_REFERENCE_CLASSES:
        errors.append("reference_class_denied")
    if not target:
        errors.append("target_required")
    if candidate.get("credential") or candidate.get("secret") or candidate.get("permission_change"):
        errors.append("authority_or_secret_marker_denied")
    return {
        "ok": not errors,
        "candidate_valid": not errors,
        "write_allowed_now": False,
        "runtime_id": CHASER_RUNTIME_ID,
        "reference_class": ref_class,
        "blocked_reasons": errors,
        "authority": build_no_authority_report(),
    }
