"""Gated ChaserAgent runtime activation approval request writer.

This is N18: it may write one pending Studio approval request for future
ChaserAgent runtime activation, but it never consumes approvals, activates
ChaserAgent, binds terminal tools, executes terminal commands, writes Agent Bus
state, calls providers, or mutates canonical ChaseOS state.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.chaser.runtime_activation_approval import (
    build_chaser_runtime_activation_approval_preview,
)


SURFACE = "chaser_runtime_activation_approval_request_write_gate"
SCHEMA_VERSION = "chaser_runtime_activation_approval_request_write_gate.v1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _authority(*, approval_queue_write: bool = False) -> dict[str, bool]:
    return {
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_toolset_binding_now": False,
        "studio_execution_now": False,
        "terminal_execution_now": False,
        "approval_queue_write_now": approval_queue_write,
        "approval_consumption_now": False,
        "agent_bus_write_now": False,
        "agent_bus_claim_now": False,
        "provider_call_now": False,
        "canonical_writeback_now": False,
        "external_network_now": False,
        "host_mutation_now": False,
    }


def _approval_spec(preview: dict[str, Any]) -> Any:
    from runtime.studio.service import ActionSpec

    request = (
        preview.get("approval_request_preview")
        if isinstance(preview.get("approval_request_preview"), dict)
        else {}
    )
    preview_id = str(preview.get("activation_approval_preview_id") or "")
    return ActionSpec(
        action_type="execute_process",
        target_path=f"runtime/chaser/activation-approval-requests/{preview_id}.json",
        content=None,
        submitted_by="chaser-runtime-activation-gate",
        note=(
            "Request operator approval for future ChaserAgent runtime activation. "
            "This request does not activate ChaserAgent, bind terminal tools, "
            "consume approvals, write Agent Bus state, or call providers."
        ),
        metadata={
            "chaser_runtime_activation_approval_request": True,
            "ambient_studio_approval_execution_blocked": True,
            "activation_approval_consumption_executor_required": True,
            "activation_approval_preview_id": preview_id,
            "runtime_id": request.get("runtime_id") or "chaser",
            "profile_id": request.get("profile_id") or "ops",
            "toolset_id": request.get("toolset_id") or "terminal-preview",
            "operator_intent": request.get("operator_intent") or "",
            "activation_scope": request.get("activation_scope") or "",
            "terminal_binding_mode": request.get("terminal_binding_mode") or "",
            "agent_bus_mutation_requested": bool(
                request.get("agent_bus_mutation_requested")
            ),
            "provider_dispatch_requested": bool(
                request.get("provider_dispatch_requested")
            ),
            "evidence_refs": request.get("evidence_refs") or {},
            "authority_ceiling": request.get("authority_ceiling") or {},
            "terminal_binding_contract": preview.get("terminal_binding_contract") or {},
            "gate_design": preview.get("gate_design") or {},
            "terminal_output_trusted": False,
            "trust_tier": "Tier 4",
            "authority": _authority(),
        },
    )


def _find_existing_activation_approval(root: Path, preview_id: str) -> dict[str, Any] | None:
    approval_dir = root / "runtime" / "studio" / "approvals"
    if not approval_dir.exists():
        return None
    for path in sorted(approval_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        spec = data.get("action_spec") if isinstance(data.get("action_spec"), dict) else {}
        metadata = spec.get("metadata") if isinstance(spec.get("metadata"), dict) else {}
        if (
            data.get("status") == "pending"
            and metadata.get("chaser_runtime_activation_approval_request") is True
            and metadata.get("activation_approval_preview_id") == preview_id
        ):
            return {
                "approval_id": data.get("approval_id") or path.stem,
                "approval_path": path.relative_to(root).as_posix(),
                "approval_status": data.get("status") or "pending",
                "duplicate_of_existing_pending": True,
            }
    return None


def build_chaser_runtime_activation_approval_request(
    vault_root: str | Path,
    *,
    profile_id: str = "ops",
    toolset_id: str = "terminal-preview",
    operator_intent: str = "",
    activation_scope: str = "local_runtime_activation",
    terminal_binding_mode: str = "read_only_policy_preview_and_audit_history_only",
    agent_bus_mutation_requested: bool = False,
    provider_dispatch_requested: bool = False,
    write_request: bool = False,
) -> dict[str, Any]:
    """Preview or write a pending Chaser runtime activation approval request."""

    root = Path(vault_root).resolve()
    preview = build_chaser_runtime_activation_approval_preview(
        root,
        profile_id=profile_id,
        toolset_id=toolset_id,
        operator_intent=operator_intent,
        activation_scope=activation_scope,
        terminal_binding_mode=terminal_binding_mode,
        agent_bus_mutation_requested=agent_bus_mutation_requested,
        provider_dispatch_requested=provider_dispatch_requested,
    )
    preview_id = str(preview.get("activation_approval_preview_id") or "")
    blockers = list(preview.get("blockers") or [])
    eligible = preview.get("ok") is True and not blockers
    result: dict[str, Any] = {
        "ok": eligible,
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "vault_root": str(root),
        "request_status": "ready_for_activation_approval_request" if eligible else "blocked",
        "write_request_requested": bool(write_request),
        "activation_approval_preview_id": preview_id,
        "approval_request_preview": preview.get("approval_request_preview") or {},
        "approval_request_written": False,
        "approval_id": None,
        "approval_path": None,
        "approval_status": None,
        "duplicate_of_existing_pending": False,
        "ready_to_write_activation_request_now": eligible,
        "activation_approval_consumption_available": False,
        "runtime_activation_now": False,
        "profile_activation_now": False,
        "toolset_activation_now": False,
        "terminal_binding_contract": preview.get("terminal_binding_contract") or {},
        "gate_design": preview.get("gate_design") or {},
        "blockers": blockers,
        "authority": _authority(),
        "terminal_output_trusted": False,
        "trust_tier": "Tier 4",
        "warnings": [
            "approval_request_only_no_runtime_activation",
            "no_approval_consumption",
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
    if not eligible or not write_request:
        return result

    existing = _find_existing_activation_approval(root, preview_id)
    if existing:
        result.update(existing)
        result["request_status"] = "existing_pending_activation_approval_request"
        return result

    from runtime.studio.service import StudioService

    req = StudioService(root).queue_for_approval(_approval_spec(preview))
    result["approval_request_written"] = True
    result["approval_id"] = req.approval_id
    result["approval_path"] = f"runtime/studio/approvals/{req.approval_id}.json"
    result["approval_status"] = req.status
    result["request_status"] = "pending_activation_approval_request_written"
    result["authority"] = _authority(approval_queue_write=True)
    return result
