"""Source-specific operator form contract for Chaser Forge approval decisions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.forge.approval_decision import (
    FORGE_APPROVAL_DECISION_API_METHOD,
    SUPPORTED_DECISIONS,
    build_forge_approval_decision_handoff,
)
from runtime.forge.registry import BLOCKED_AUTHORITY


FORGE_APPROVAL_DECISION_FORM_SCHEMA_VERSION = "forge.approval_decision_form.v1"
FORGE_APPROVAL_DECISION_FORM_SURFACE_ID = "chaser_forge_operator_decision_form"
FORGE_APPROVAL_DECISION_FORM_API_METHOD = "get_chaser_forge_approval_decision_form"


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(item for item in values if item))


def _decision_label(decision: str) -> str:
    return "Approve Forge request" if decision == "approved" else "Reject Forge request"


def _decision_option(preview: dict[str, Any]) -> dict[str, Any]:
    decision = str(preview.get("decision") or "")
    approval_artifact_path = str(preview.get("source_approval_artifact_path") or "")
    request_digest = str(preview.get("request_digest_sha256") or "")
    required_statement = str(preview.get("required_operator_statement") or "")
    return {
        "decision": decision,
        "label": _decision_label(decision),
        "available": bool(preview.get("ok")),
        "status": preview.get("status") or "",
        "blockers": list(preview.get("blockers") or []),
        "required_operator_statement": required_statement,
        "copyable_statement_required": True,
        "expected_request_digest_sha256": request_digest,
        "future_decision_artifact_path": preview.get("decision_artifact_path") or "",
        "submit_api_method": FORGE_APPROVAL_DECISION_API_METHOD,
        "submit_payload": {
            "approval_artifact_path": approval_artifact_path,
            "decision": decision,
            "expected_request_digest": request_digest,
            "operator_statement": required_statement,
            "write_decision": True,
        },
    }


def build_forge_approval_decision_form(
    vault_root: str | Path,
    *,
    approval_artifact_path: str | Path | None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a read-only approve/reject form model for one Forge approval artifact.

    The form prepares the exact source-specific handoff payload. It never records
    a decision, consumes an approval, executes Forge work, writes registry state,
    writes extension files, or reserves exact-once markers.
    """

    previews = {
        decision: build_forge_approval_decision_handoff(
            vault_root,
            approval_artifact_path=approval_artifact_path,
            decision=decision,
            write_decision=False,
            generated_at=generated_at,
        )
        for decision in SUPPORTED_DECISIONS
    }
    primary = previews["approved"]
    decision_options = [_decision_option(previews[decision]) for decision in SUPPORTED_DECISIONS]
    blockers = _unique(
        [
            blocker
            for preview in previews.values()
            for blocker in list(preview.get("blockers") or [])
        ]
    )
    can_submit = all(bool(previews[decision].get("ok")) for decision in SUPPORTED_DECISIONS)

    return {
        "ok": can_submit,
        "surface": FORGE_APPROVAL_DECISION_FORM_SURFACE_ID,
        "model_version": FORGE_APPROVAL_DECISION_FORM_SCHEMA_VERSION,
        "status": "forge_approval_decision_form_ready" if can_submit else "blocked_forge_approval_decision_form",
        "generated_at": primary.get("generated_at") or "",
        "vault_root": str(Path(vault_root).resolve()),
        "preview_only": True,
        "form_preview_only": True,
        "source_specific": True,
        "generic_approval_center_control": False,
        "approval_artifact_path": primary.get("source_approval_artifact_path") or str(approval_artifact_path or ""),
        "approval_family": primary.get("family") or "",
        "approval_packet_id": primary.get("approval_packet_id") or "",
        "request_digest_sha256": primary.get("request_digest_sha256") or "",
        "extension_id": (primary.get("decision_record_preview") or {}).get("extension_id") or "",
        "extension_name": (primary.get("decision_record_preview") or {}).get("extension_name") or "",
        "extension_version": (primary.get("decision_record_preview") or {}).get("extension_version") or "",
        "available_decisions": list(SUPPORTED_DECISIONS),
        "decision_options": decision_options,
        "submit_contract": {
            "api_method": FORGE_APPROVAL_DECISION_API_METHOD,
            "source_specific": True,
            "generic_approval_center_control": False,
            "requires_pending_forge_approval_artifact": True,
            "requires_selected_decision": True,
            "requires_exact_request_digest": True,
            "requires_exact_operator_statement": True,
            "operator_statement_source": "decision_options[].required_operator_statement",
            "payload_fields": [
                "approval_artifact_path",
                "decision",
                "expected_request_digest",
                "operator_statement",
                "write_decision",
            ],
            "write_decision": True,
        },
        "copyable_statement_required": True,
        "write_decision_enabled_by_form_preview": False,
        "approval_artifact_mutated": False,
        "decision_artifact_written": False,
        "approval_consumption_allowed": False,
        "forge_execution_allowed": False,
        "registry_write_allowed": False,
        "extension_file_write_allowed": False,
        "exact_once_marker_reservation_allowed": False,
        "protected_core_mutation_allowed": False,
        "runtime_policy_mutation_allowed": False,
        "schedule_activation_allowed": False,
        "agent_bus_dispatch_allowed": False,
        "provider_call_allowed": False,
        "connector_call_allowed": False,
        "canonical_mutation_allowed": False,
        "authority": {
            **dict(BLOCKED_AUTHORITY),
            "approval_decision_form_only": True,
            "writes_review_decision": False,
            "writes_approval_artifact": False,
            "consumes_approval": False,
            "executes_forge": False,
            "writes_extension_registry": False,
            "writes_extension_files": False,
            "reserves_exact_once_marker": False,
        },
        "blockers": blockers,
        "next_recommended_pass": (
            "chaser-forge-marketplace-import-export-foundation"
            if can_submit
            else "chaser-forge-operator-decision-form-repair"
        ),
    }
