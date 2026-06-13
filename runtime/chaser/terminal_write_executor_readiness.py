"""N6 terminal write executor readiness contract.

This module validates whether a queued terminal write approval request is
structurally ready for the dedicated N6 executor. It does not execute a
terminal command, consume an approval, reserve an exact-once marker, write a
terminal audit record, write Agent Bus tasks, call providers, or mutate
canonical state.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from runtime.chaser.board import build_action_proposal
from runtime.studio.service import StudioService


SURFACE = "terminal_write_executor_readiness"
SCHEMA_VERSION = "terminal_write_executor_readiness.v1"
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def _safe_approval_id(approval_id: str) -> bool:
    return bool(_SAFE_ID_RE.fullmatch(str(approval_id or "")))


def _marker_rel_path(approval_id: str) -> str:
    return f"07_LOGS/Terminal-Runs/_execution_markers/{approval_id}.json"


def _authority_flags() -> dict[str, bool]:
    return {
        "terminal_execution_now": False,
        "terminal_audit_write_now": False,
        "approval_consumption_now": False,
        "exact_once_marker_write_now": False,
        "studio_execution_now": False,
        "agent_bus_write_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "external_upload_now": False,
        "host_mutation_now": False,
    }


def build_terminal_write_executor_readiness(
    vault_root: str | Path,
    *,
    approval_id: str,
    expected_proposal_id: str = "",
    executor_implemented: bool = True,
) -> dict[str, Any]:
    """Validate an N6 terminal write approval without consuming or executing it."""

    root = Path(vault_root).resolve()
    approval_id = str(approval_id or "").strip()
    marker_rel = _marker_rel_path(approval_id or "unsafe-approval-id")
    marker_path = root / marker_rel
    blockers: list[str] = []
    warnings: list[str] = [
        "readiness_only_no_terminal_execution",
        "terminal_output_and_terminal_intent_are_not_instruction_trusted",
    ]

    if not _safe_approval_id(approval_id):
        blockers.append("unsafe_approval_id")
        return _readiness_payload(
            root=root,
            approval_id=approval_id,
            proposal_id="",
            marker_rel=marker_rel,
            blockers=blockers,
            warnings=warnings,
            metadata={},
            proposal={},
        )

    service = StudioService(root)
    approval = service.get_approval(approval_id)
    if approval is None:
        blockers.append("approval_request_missing")
        return _readiness_payload(
            root=root,
            approval_id=approval_id,
            proposal_id="",
            marker_rel=marker_rel,
            blockers=blockers,
            warnings=warnings,
            metadata={},
            proposal={},
        )

    spec = approval.action_spec
    metadata = spec.metadata if isinstance(spec.metadata, dict) else {}
    proposal_id = str(metadata.get("proposal_id") or "")
    command = str(metadata.get("command") or "")
    cwd = str(metadata.get("cwd") or "")

    if approval.status != "approved":
        blockers.append(f"approval_status_not_approved:{approval.status}")
    if spec.action_type != "execute_process":
        blockers.append(f"unexpected_action_type:{spec.action_type}")
    if metadata.get("terminal_write_lane_approval_request") is not True:
        blockers.append("not_terminal_write_lane_approval_request")
    if not proposal_id:
        blockers.append("proposal_id_missing")
    if expected_proposal_id and expected_proposal_id != proposal_id:
        blockers.append("expected_proposal_id_mismatch")
    if not command:
        blockers.append("command_missing")
    expected_target = f"07_LOGS/Terminal-Runs/_approval_requests/{proposal_id}.json"
    if proposal_id and spec.target_path != expected_target:
        blockers.append("approval_target_path_mismatch")

    authority = metadata.get("authority") if isinstance(metadata.get("authority"), dict) else {}
    for key in (
        "terminal_execution_now",
        "studio_execution_now",
        "approval_consumption_now",
        "agent_bus_write_now",
        "provider_call_now",
        "canonical_writeback_now",
    ):
        if authority.get(key) is True:
            blockers.append(f"metadata_authority_claims_now:{key}")

    proposal: dict[str, Any] = {}
    if command and cwd:
        proposal = build_action_proposal(
            root,
            action_type="terminal_command",
            command=command,
            cwd=cwd,
            actor="n6-readiness",
        )
        if proposal.get("proposal_id") != proposal_id:
            blockers.append("fresh_proposal_id_mismatch")
        if proposal.get("status") != "approval_required_future_n6":
            blockers.append(f"fresh_proposal_not_write_eligible:{proposal.get('status')}")
    else:
        proposal = {}

    classification = metadata.get("classification") if isinstance(metadata.get("classification"), dict) else {}
    if classification.get("action_class") != "write_command":
        blockers.append(f"classification_not_write_command:{classification.get('action_class')}")
    if classification.get("approval_required") is not True:
        blockers.append("classification_missing_approval_required")
    if classification.get("allowed") is True:
        blockers.append("write_command_marked_allowed_now")

    if marker_path.exists():
        blockers.append("exact_once_marker_already_present")

    return _readiness_payload(
        root=root,
        approval_id=approval_id,
        proposal_id=proposal_id,
        marker_rel=marker_rel,
        blockers=blockers,
        warnings=warnings,
        metadata=metadata,
        proposal=proposal,
        approval_status=approval.status,
        approval_path=f"runtime/studio/approvals/{approval_id}.json",
        executor_implemented=executor_implemented,
    )


def _readiness_payload(
    *,
    root: Path,
    approval_id: str,
    proposal_id: str,
    marker_rel: str,
    blockers: list[str],
    warnings: list[str],
    metadata: dict[str, Any],
    proposal: dict[str, Any],
    approval_status: str = "missing",
    approval_path: str = "",
    executor_implemented: bool = True,
) -> dict[str, Any]:
    structural_ready = not blockers
    remaining_gates = [] if blockers or executor_implemented else [
        "n6_executor_review_gate_required",
        "terminal_write_executor_not_implemented",
    ]
    return {
        "ok": structural_ready,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "vault_root": str(root),
        "approval_id": approval_id,
        "approval_path": approval_path,
        "approval_status": approval_status,
        "proposal_id": proposal_id,
        "command": metadata.get("command") or "",
        "cwd": metadata.get("cwd") or "",
        "readiness_status": (
            "blocked" if blockers else ("ready_for_executor" if executor_implemented else "review_gate_required")
        ),
        "scope_validation_ok": structural_ready,
        "ready_for_future_executor_after_review": structural_ready,
        "terminal_write_executor_implemented": bool(executor_implemented),
        "ready_for_execution_now": bool(structural_ready and executor_implemented),
        "terminal_execution_now": False,
        "terminal_audit_write_now": False,
        "approval_consumption_now": False,
        "exact_once_marker_write_now": False,
        "agent_bus_write_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "exact_once_marker_path": marker_rel,
        "exact_once_marker_exists": (root / marker_rel).exists(),
        "blockers": blockers,
        "remaining_gates": remaining_gates,
        "authority": _authority_flags(),
        "classification": metadata.get("classification") or {},
        "fresh_proposal": proposal,
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": warnings,
        "next_recommended_pass": (
            "execute-terminal-approval-via-dedicated-n6-cli"
            if structural_ready and executor_implemented
            else "terminal-write-executor-review-gate"
            if structural_ready
            else "resolve-terminal-write-executor-readiness-blockers"
        ),
    }
