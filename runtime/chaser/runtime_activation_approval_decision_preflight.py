"""Read-only ChaserAgent runtime activation approval decision preflight.

This is N19: it validates a pending/decided N18 activation approval request
before a future consumption executor may exist. It never writes an approval
decision, consumes approval, activates ChaserAgent, binds terminal tools,
executes terminal commands, writes Agent Bus state, calls providers, or mutates
canonical ChaseOS state.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.runtime_activation_approval import (
    build_chaser_runtime_activation_approval_preview,
)
from runtime.studio.service import StudioService


SURFACE = "chaser_runtime_activation_approval_decision_preflight"
SCHEMA_VERSION = "chaser_runtime_activation_approval_decision_preflight.v1"

_SAFE_APPROVAL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _authority() -> dict[str, bool]:
    return {
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_toolset_binding_now": False,
        "studio_execution_now": False,
        "terminal_execution_now": False,
        "approval_queue_write_now": False,
        "approval_decision_write_now": False,
        "approval_consumption_now": False,
        "exact_once_marker_write_now": False,
        "agent_bus_write_now": False,
        "agent_bus_claim_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "external_network_now": False,
        "host_mutation_now": False,
    }


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "required": True,
        "status": "passed" if passed else "blocked",
        "detail": detail,
    }


def _blocked(
    root: Path,
    approval_id: str,
    status: str,
    blockers: list[str],
    *,
    checks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "vault_root": str(root),
        "activation_approval_id": approval_id,
        "approval_path": None,
        "decision_preflight_status": status,
        "approval_status": "missing",
        "approval_decision_written": False,
        "approval_status_mutated": False,
        "approval_consumed": False,
        "activation_consumption_marker_written": False,
        "ready_for_activation_consumer_next_pass": False,
        "approved_for_future_activation_consumer_review": False,
        "activation_allowed": False,
        "activation_performed": False,
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_binding_now": False,
        "decision_preflight_checks": list(checks or []),
        "blockers": list(blockers),
        "authority": _authority(),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "decision_preflight_only_no_approval_decision",
            "no_approval_consumption",
            "no_chaser_runtime_activation",
            "no_terminal_to_chaser_binding",
            "no_terminal_execution",
            "no_studio_execution",
            "no_agent_bus_write_or_claim",
            "no_provider_call",
            "terminal_output_remains_tier4_untrusted",
        ],
        "next_recommended_pass": (
            "terminal-n22-chaser-runtime-activation-post-consumption-readiness"
        ),
    }


def build_chaser_runtime_activation_approval_decision_preflight(
    vault_root: str | Path,
    approval_id: str,
    *,
    expected_preview_id: str = "",
) -> dict[str, Any]:
    """Validate activation approval decision posture without mutating state."""

    root = Path(vault_root).resolve()
    requested_id = str(approval_id or "").strip()
    if not requested_id or not _SAFE_APPROVAL_ID.fullmatch(requested_id):
        return _blocked(
            root,
            requested_id,
            "blocked_unsafe_activation_approval_id",
            ["unsafe_activation_approval_id"],
            checks=[
                _check(
                    "approval_id_is_safe",
                    False,
                    "approval ids must be vault-local slugs without path separators",
                )
            ],
        )

    service = StudioService(root)
    approval = service.get_approval(requested_id)
    if approval is None:
        return _blocked(
            root,
            requested_id,
            "blocked_missing_activation_approval",
            ["activation_approval_not_found"],
            checks=[
                _check("approval_id_is_safe", True, requested_id),
                _check("approval_record_found", False, requested_id),
            ],
        )

    spec = approval.action_spec
    metadata = dict(spec.metadata or {})
    metadata_authority = (
        metadata.get("authority") if isinstance(metadata.get("authority"), dict) else {}
    )
    preview_id = str(metadata.get("activation_approval_preview_id") or "")
    profile_id = str(metadata.get("profile_id") or "ops")
    toolset_id = str(metadata.get("toolset_id") or "terminal-preview")
    activation_scope = str(metadata.get("activation_scope") or "local_runtime_activation")
    terminal_binding_mode = str(
        metadata.get("terminal_binding_mode")
        or "read_only_policy_preview_and_audit_history_only"
    )
    operator_intent = str(metadata.get("operator_intent") or "")
    preview = build_chaser_runtime_activation_approval_preview(
        root,
        profile_id=profile_id,
        toolset_id=toolset_id,
        operator_intent=operator_intent,
        activation_scope=activation_scope,
        terminal_binding_mode=terminal_binding_mode,
    )
    current_preview_id = str(preview.get("activation_approval_preview_id") or "")
    approval_path = f"runtime/studio/approvals/{approval.approval_id}.json"
    expected_preview = str(expected_preview_id or "").strip()
    target_path_ok = spec.target_path == (
        f"runtime/chaser/activation-approval-requests/{preview_id}.json"
    )
    metadata_authority_all_false = all(value is False for value in metadata_authority.values())
    no_agent_bus_or_provider_requested = (
        metadata.get("agent_bus_mutation_requested") is False
        and metadata.get("provider_dispatch_requested") is False
    )
    checks = [
        _check("approval_id_is_safe", True, requested_id),
        _check("approval_record_found", True, approval_path),
        _check(
            "approval_is_chaser_runtime_activation_request",
            metadata.get("chaser_runtime_activation_approval_request") is True,
            str(metadata.get("chaser_runtime_activation_approval_request")),
        ),
        _check(
            "ambient_studio_execution_blocked",
            metadata.get("ambient_studio_approval_execution_blocked") is True,
            str(metadata.get("ambient_studio_approval_execution_blocked")),
        ),
        _check(
            "action_type_is_execute_process_request_only",
            spec.action_type == "execute_process",
            spec.action_type,
        ),
        _check(
            "target_path_matches_preview_id",
            target_path_ok,
            spec.target_path,
        ),
        _check(
            "metadata_preview_id_matches_current_preview",
            bool(preview_id) and preview_id == current_preview_id,
            f"{preview_id} / {current_preview_id}",
        ),
        _check(
            "expected_preview_id_matches_when_supplied",
            not expected_preview or expected_preview == preview_id,
            expected_preview or "not supplied",
        ),
        _check(
            "profile_and_toolset_still_preview_valid",
            preview.get("ok") is True,
            str(preview.get("preview_status")),
        ),
        _check(
            "no_agent_bus_or_provider_requested",
            no_agent_bus_or_provider_requested,
            (
                f"agent_bus={metadata.get('agent_bus_mutation_requested')} "
                f"provider={metadata.get('provider_dispatch_requested')}"
            ),
        ),
        _check(
            "metadata_authority_preserves_no_mutation",
            metadata_authority_all_false,
            "all metadata authority flags must be false",
        ),
        _check(
            "terminal_output_remains_tier4_untrusted",
            metadata.get("terminal_output_trusted") is False
            and metadata.get("trust_tier") == "Tier 4",
            f"{metadata.get('trust_tier')} trusted={metadata.get('terminal_output_trusted')}",
        ),
        _check(
            "decision_preflight_is_no_mutation",
            True,
            "does not decide, consume, activate, bind terminal tools, write Agent Bus state, call providers, or mutate canonical state",
        ),
    ]
    required_checks_pass = all(item["passed"] for item in checks if item.get("required"))
    blockers = [
        f"failed_check:{item['name']}" for item in checks if item.get("passed") is not True
    ]
    approval_status = str(approval.status or "")
    if not required_checks_pass:
        preflight_status = (
            "blocked_activation_approval_decision_preflight_metadata_or_readiness_mismatch"
        )
        review_decision = "blocked_before_activation_approval_consumer"
    elif approval_status == "pending":
        preflight_status = "blocked_pending_activation_approval"
        review_decision = "pending_operator_decision_no_activation"
    elif approval_status == "approved":
        preflight_status = "activation_approval_decision_preflight_ready_no_mutation"
        review_decision = "approved_for_separate_activation_consumer_review"
    elif approval_status == "rejected":
        preflight_status = "activation_approval_decision_preflight_rejected_blocks_activation"
        review_decision = "rejected_no_activation"
    else:
        preflight_status = (
            f"blocked_activation_approval_decision_preflight_unknown_status:{approval_status}"
        )
        review_decision = "blocked_before_activation_approval_consumer"
        blockers.append(f"unknown_approval_status:{approval_status}")

    approved_for_future_consumer = required_checks_pass and approval_status == "approved"
    return {
        "ok": required_checks_pass and approval_status in {"pending", "approved", "rejected"},
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "vault_root": str(root),
        "activation_approval_id": approval.approval_id,
        "approval_path": approval_path,
        "activation_approval_preview_id": preview_id,
        "expected_preview_id": expected_preview or None,
        "decision_preflight_status": preflight_status,
        "review_decision": review_decision,
        "approval_status": approval_status,
        "approval_reviewed_by": approval.reviewed_by,
        "approval_updated_at": approval.updated_at,
        "profile_id": profile_id,
        "toolset_id": toolset_id,
        "activation_scope": activation_scope,
        "terminal_binding_mode": terminal_binding_mode,
        "operator_intent": operator_intent,
        "current_preview_status": preview.get("preview_status"),
        "current_preview_id": current_preview_id,
        "digest_or_preview_matches": preview_id == current_preview_id,
        "decision_preflight_checks": checks,
        "approved_for_future_activation_consumer_review": approved_for_future_consumer,
        "ready_for_activation_consumer_next_pass": approved_for_future_consumer,
        "activation_approval_consumption_available": False,
        "approval_decision_written": False,
        "approval_status_mutated": False,
        "approval_consumed": False,
        "activation_consumption_marker_written": False,
        "activation_allowed": False,
        "activation_performed": False,
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_binding_now": False,
        "terminal_binding_contract": preview.get("terminal_binding_contract") or {},
        "blockers": blockers,
        "authority": _authority(),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "decision_preflight_only_no_approval_decision",
            "no_approval_consumption",
            "no_chaser_runtime_activation",
            "no_profile_or_toolset_activation",
            "no_terminal_to_chaser_binding",
            "no_terminal_execution",
            "no_studio_execution",
            "no_agent_bus_write_or_claim",
            "no_provider_call",
            "terminal_output_remains_tier4_untrusted",
        ],
        "next_recommended_pass": (
            "terminal-n22-chaser-runtime-activation-post-consumption-readiness"
        ),
    }
