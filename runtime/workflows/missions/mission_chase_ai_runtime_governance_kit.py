"""AOR dry-review handler for the Chase AI Runtime Governance Kit mission.

The handler executes a bounded local review of an existing Mission Mode dry-run
workspace. It writes proof/review artifacts only through AOR Stage 7 and never
activates the mission, enqueues Agent Bus work, applies workflow evolution, or
touches external systems.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.agent_bus.mission_tasks import (
    build_mission_task_packet,
    validate_mission_task_packet,
    vault_relative_path,
)
from runtime.ventureops.mission_activation_readiness import (
    DEFAULT_MISSION_WORKSPACE,
    build_mission_activation_readiness,
)
from runtime.ventureops.mission_dry_runs import validate_mission_dry_run_workspace
from runtime.ventureops.proof_cards import build_proof_card
from runtime.ventureops.validation import validate_agent_scorecard


WORKFLOW_ID = "mission_chase_ai_runtime_governance_kit"
MISSION_ID = "mission-chase-ai-runtime-governance-kit"
DEFAULT_APPROVAL_PACKET_NAME = "activation-approval-packet-draft.json"


class WorkflowExecutionError(RuntimeError):
    """Fail-closed workflow error surfaced by AOR as an escalation."""


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _safe_slug(value: Any, *, fallback: str = "run") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip()).strip("-")
    return slug[:96] or fallback


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WorkflowExecutionError(f"{label} is invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise WorkflowExecutionError(f"{label} must contain a JSON object")
    return data


def _resolve_vault_path(vault_root: Path, value: Any, *, field_name: str) -> Path:
    raw = str(value or "").strip()
    if not raw:
        raise WorkflowExecutionError(f"{field_name} is required")
    candidate = Path(raw)
    resolved = candidate.resolve() if candidate.is_absolute() else (vault_root / candidate).resolve()
    try:
        resolved.relative_to(vault_root.resolve())
    except ValueError as exc:
        raise WorkflowExecutionError(f"{field_name} escapes vault root") from exc
    return resolved


def _default_workspace(vault_root: Path) -> Path:
    return (vault_root / DEFAULT_MISSION_WORKSPACE).resolve()


def _next_available_relative(vault_root: Path, relative_path: str) -> str:
    candidate = (vault_root / relative_path).resolve()
    try:
        candidate.relative_to(vault_root.resolve())
    except ValueError as exc:
        raise WorkflowExecutionError(f"writeback path escapes vault root: {relative_path}") from exc
    if not candidate.exists():
        return relative_path.replace("\\", "/")

    suffix = 2
    stem = candidate.stem
    suffix_text = "".join(candidate.suffixes)
    parent = candidate.parent
    while True:
        next_name = f"{stem}-{suffix}{suffix_text}"
        next_path = parent / next_name
        if not next_path.exists():
            return next_path.relative_to(vault_root.resolve()).as_posix()
        suffix += 1


def _render_review_markdown(
    *,
    run_id: str,
    run_date: str,
    mission_id: str,
    mission_workspace_path: str,
    readiness: dict[str, Any],
    mission_task_packet_validation: dict[str, Any],
    proof_path: str,
    workspace_review_path: str,
) -> str:
    blockers = readiness.get("blockers") or []
    blocker_lines = "\n".join(f"- {item}" for item in blockers) or "- none"
    validation_errors = mission_task_packet_validation.get("errors") or []
    validation_lines = "\n".join(f"- {item}" for item in validation_errors) or "- none"
    return f"""---
type: ventureops-mission-aor-dry-review
workflow_id: {WORKFLOW_ID}
mission_id: {mission_id}
run_id: {run_id}
date: {run_date}
status: internal_dry_review
mission_activation_performed: false
agent_bus_task_written: false
external_side_effects_performed: false
---

# VentureOps Mission AOR Dry Review

Mission workspace: `{mission_workspace_path}`

## Result

- Artifact validation: {readiness.get("artifact_validation_ok")}
- Readiness status: {readiness.get("readiness_status")}
- Ready for activation: {readiness.get("ready_for_activation")}
- Ready for AOR dispatch: {readiness.get("ready_for_aor_dispatch")}
- Mission task packet valid: {mission_task_packet_validation.get("ok")}

## Remaining Blockers

{blocker_lines}

## Packet Validation Errors

{validation_lines}

## Evidence

- Proof JSON: `{proof_path}`
- Workspace dry-review record: `{workspace_review_path}`

## Boundary

This handler performed a local AOR dry-review only. It did not activate the mission,
write an Agent Bus task, apply workflow evolution, call a provider, use a browser,
send externally, mutate CRM/payment systems, execute live trading, or promote
canonical state.
"""


def _render_audit_markdown(
    *,
    run_id: str,
    run_date: str,
    mission_id: str,
    proof_path: str,
    review_path: str,
    workspace_review_path: str,
) -> str:
    return f"""---
type: ventureops-mission-runtime-audit
workflow_id: {WORKFLOW_ID}
mission_id: {mission_id}
run_id: {run_id}
date: {run_date}
status: internal_run_passed
---

# Mission Runtime Audit

- Runtime: AOR
- Handler: `{WORKFLOW_ID}`
- Execution mode: dry_review
- Mission activation performed: false
- Agent Bus task written: false
- Workflow evolution applied: false
- Provider calls: 0
- Browser actions: 0
- External sends: 0
- CRM/payment mutations: 0
- Live trading actions: 0
- Protected file edits: 0
- Canonical promotions: 0

## Evidence

- Proof JSON: `{proof_path}`
- Review note: `{review_path}`
- Workspace dry-review record: `{workspace_review_path}`
"""


def build_mission_chase_ai_runtime_governance_kit(
    *,
    inputs: dict[str, Any] | None = None,
    vault_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build AOR writebacks for a local Mission Mode dry-review."""

    root = Path(vault_root).resolve() if vault_root is not None else Path(__file__).resolve().parents[3]
    raw_inputs = dict(inputs or {})
    execution_mode = str(raw_inputs.get("execution_mode") or "dry_review").strip()
    if execution_mode != "dry_review":
        raise WorkflowExecutionError("execution_mode must be dry_review")

    workspace = (
        _resolve_vault_path(root, raw_inputs["mission_workspace_path"], field_name="mission_workspace_path")
        if raw_inputs.get("mission_workspace_path")
        else _default_workspace(root)
    )
    if not workspace.exists():
        raise WorkflowExecutionError(f"mission workspace missing: {vault_relative_path(workspace, root)}")

    approval_packet = (
        _resolve_vault_path(
            root,
            raw_inputs["activation_approval_packet_path"],
            field_name="activation_approval_packet_path",
        )
        if raw_inputs.get("activation_approval_packet_path")
        else workspace / DEFAULT_APPROVAL_PACKET_NAME
    )
    if not approval_packet.exists():
        raise WorkflowExecutionError(f"activation approval packet missing: {vault_relative_path(approval_packet, root)}")

    workspace_validation = validate_mission_dry_run_workspace(workspace)
    if not workspace_validation.get("ok"):
        errors = "; ".join(str(item) for item in workspace_validation.get("errors") or [])
        raise WorkflowExecutionError(f"mission dry-run workspace validation failed: {errors}")

    manifest = _load_json_object(workspace / "mission-manifest.json", label="mission-manifest.json")
    mission_id = str(manifest.get("mission_id") or workspace_validation.get("mission_id") or MISSION_ID)
    if mission_id != MISSION_ID:
        raise WorkflowExecutionError(f"unexpected mission_id {mission_id!r}; expected {MISSION_ID!r}")

    activation_packet = _load_json_object(approval_packet, label="activation approval packet")
    packet_mission_id = str(activation_packet.get("mission_id") or activation_packet.get("packet", {}).get("mission_id") or "")
    if packet_mission_id and packet_mission_id != mission_id:
        raise WorkflowExecutionError("activation approval packet mission_id does not match mission workspace")

    readiness = build_mission_activation_readiness(root, mission_workspace=workspace)
    run_date = str(raw_inputs.get("date") or _today_utc())
    run_id = _safe_slug(raw_inputs.get("run_id") or f"{run_date}-{WORKFLOW_ID}", fallback=WORKFLOW_ID)
    workspace_relative = vault_relative_path(workspace, root)
    approval_packet_relative = vault_relative_path(approval_packet, root)

    mission_task_packet = build_mission_task_packet(
        mission_id=mission_id,
        mission_workspace_path=workspace_relative,
        activation_approval_packet_path=approval_packet_relative,
        task_id=f"mission-task-preview-{run_id}",
        run_id=f"mission-bus-preview-{run_id}",
        created_at=_now_utc(),
        artifacts=[workspace_relative, approval_packet_relative],
        notes="AOR dry-review preview only; no Agent Bus task was written.",
    )
    mission_task_packet_validation = validate_mission_task_packet(mission_task_packet)
    if not mission_task_packet_validation.get("ok"):
        errors = "; ".join(str(item) for item in mission_task_packet_validation.get("errors") or [])
        raise WorkflowExecutionError(f"mission task packet contract validation failed: {errors}")

    workspace_review_path = _next_available_relative(
        root,
        f"{workspace_relative}/aor-dry-review-{run_id}.json",
    )
    proof_path = _next_available_relative(
        root,
        f"07_LOGS/Workflow-Proofs/{run_date}_{WORKFLOW_ID}_{run_id}.json",
    )
    review_path = _next_available_relative(
        root,
        f"07_LOGS/Mission-Reviews/{run_date}_{mission_id}_{run_id}.md",
    )
    audit_path = _next_available_relative(
        root,
        f"07_LOGS/Runtime-Audits/{run_date}_{WORKFLOW_ID}_{run_id}.md",
    )
    files_written = [workspace_review_path, proof_path, review_path, audit_path]

    authority_boundary = {
        "aor_dry_review_handler_executed": True,
        "mission_activation_performed": False,
        "aor_dispatch_performed": True,
        "agent_bus_task_written": False,
        "workflow_mutation_performed": False,
        "workflow_evolution_applied": False,
        "provider_call_performed": False,
        "browser_action_performed": False,
        "browser_skill_activated": False,
        "external_send_performed": False,
        "crm_or_payment_mutation_performed": False,
        "live_trading_performed": False,
        "protected_file_edit_performed": False,
        "canonical_promotion_performed": False,
    }

    proof_card = build_proof_card(
        workflow_id=WORKFLOW_ID,
        run_id=run_id,
        before_state="Mission Mode had a validated dry-run workspace and draft activation packet.",
        after_state="AOR dry-review handler validated workspace artifacts and produced local proof writebacks.",
        input_sources=[
            f"{workspace_relative}/mission-manifest.json",
            f"{workspace_relative}/mission-state-ledger.json",
            f"{workspace_relative}/mission-review.json",
            f"{workspace_relative}/workflow-evolution-proposal.json",
            approval_packet_relative,
            "runtime/agent_bus/mission_tasks.py",
            "runtime/agent_bus/schemas/mission_task_packet.schema.json",
        ],
        runtimes_used=["AOR", "Codex"],
        actions_taken=[
            "loaded declared Mission Mode dry-run workspace",
            "validated required dry-run artifacts",
            "loaded draft activation approval packet",
            "validated Agent Bus mission task packet preview",
            "prepared local mission dry-review proof artifacts",
            "blocked activation, live bus enqueue, workflow evolution apply, provider calls, browser actions, external sends, payment/CRM mutations, live trading, protected edits, and canonical promotion",
        ],
        outputs_generated=[
            "mission AOR dry-review proof JSON",
            "mission AOR dry-review markdown review",
            "mission runtime audit note",
            "workspace-local dry-review record",
        ],
        files_written=files_written,
        approvals_used=[],
        unresolved_risks=[
            "Mission manifest remains draft until a separate activation executor consumes explicit approval.",
            "Workflow evolution proposal remains pending review and has not been applied.",
            "Agent Bus task packet was validated only as an inert preview; no live task was written.",
        ],
        internal_audit_link=audit_path,
        customer_facing_summary="Internal Mission Mode dry-review only; not client-facing delivery.",
        cta_or_follow_up="Prepare exact-once activation approval consumption before any active mission execution.",
    )

    scorecard = {
        "workflow_id": WORKFLOW_ID,
        "run_id": run_id,
        "runtime": "AOR+Codex",
        "operator": "local-operator",
        "timestamp": proof_card["timestamp"],
        "status": "internal_run_passed",
        "metrics": {
            "workspace_validation_passed": True,
            "mission_task_packet_valid": True,
            "mission_activation_performed": False,
            "agent_bus_task_written": False,
            "provider_calls": 0,
            "browser_actions": 0,
            "external_sends": 0,
            "payment_or_crm_mutations": 0,
            "live_trading_actions": 0,
            "canonical_promotions": 0,
        },
        "evidence_links": [proof_path, review_path, audit_path, workspace_review_path],
        "unresolved_risks": list(proof_card["unresolved_risks"]),
        "recommended_next_action": "Implement exact-once activation approval consumption before active mission execution.",
    }
    scorecard_validation = validate_agent_scorecard(scorecard)
    if not scorecard_validation["ok"]:
        raise WorkflowExecutionError("; ".join(scorecard_validation["errors"]))

    proof_payload = {
        "schema_version": "0.1",
        "type": "ventureops-mission-aor-dry-review-proof",
        "workflow_id": WORKFLOW_ID,
        "mission_id": mission_id,
        "run_id": run_id,
        "date": run_date,
        "execution_mode": execution_mode,
        "mission_workspace_path": workspace_relative,
        "activation_approval_packet_path": approval_packet_relative,
        "artifact_validation_ok": bool(workspace_validation.get("ok")),
        "readiness_status": readiness.get("readiness_status"),
        "readiness_blockers": list(readiness.get("blockers") or []),
        "mission_task_packet_valid": bool(mission_task_packet_validation.get("ok")),
        "mission_task_packet_preview": mission_task_packet,
        "mission_task_packet_validation": mission_task_packet_validation,
        "proof_card": proof_card,
        "scorecard": scorecard,
        "authority_boundary": authority_boundary,
        "activation_performed": False,
        "agent_bus_task_written": False,
        "workflow_evolution_applied": False,
        "files_written": files_written,
    }
    proof_json = json.dumps(proof_payload, indent=2, sort_keys=True) + "\n"
    review_markdown = _render_review_markdown(
        run_id=run_id,
        run_date=run_date,
        mission_id=mission_id,
        mission_workspace_path=workspace_relative,
        readiness=readiness,
        mission_task_packet_validation=mission_task_packet_validation,
        proof_path=proof_path,
        workspace_review_path=workspace_review_path,
    )
    audit_markdown = _render_audit_markdown(
        run_id=run_id,
        run_date=run_date,
        mission_id=mission_id,
        proof_path=proof_path,
        review_path=review_path,
        workspace_review_path=workspace_review_path,
    )

    workspace_record = {
        "schema_version": "0.1",
        "type": "ventureops-mission-aor-dry-review-record",
        "workflow_id": WORKFLOW_ID,
        "mission_id": mission_id,
        "run_id": run_id,
        "timestamp": proof_card["timestamp"],
        "proof_path": proof_path,
        "review_path": review_path,
        "audit_path": audit_path,
        "mission_activation_performed": False,
        "agent_bus_task_written": False,
        "workflow_evolution_applied": False,
        "authority_boundary": authority_boundary,
    }
    workspace_record_json = json.dumps(workspace_record, indent=2, sort_keys=True) + "\n"

    return {
        "workflow_id": WORKFLOW_ID,
        "mission_id": mission_id,
        "run_id": run_id,
        "date": run_date,
        "execution_mode": execution_mode,
        "mission_workspace_path": workspace_relative,
        "activation_approval_packet_path": approval_packet_relative,
        "artifact_validation_ok": True,
        "readiness_status": readiness.get("readiness_status"),
        "readiness_blockers": list(readiness.get("blockers") or []),
        "mission_task_packet_valid": True,
        "mission_task_packet_preview": mission_task_packet,
        "authority_boundary": authority_boundary,
        "proof_path": proof_path,
        "review_path": review_path,
        "audit_path": audit_path,
        "workspace_review_path": workspace_review_path,
        "proof_card": proof_card,
        "scorecard": scorecard,
        "writebacks": [
            {"path": workspace_review_path, "content": workspace_record_json},
            {"path": proof_path, "content": proof_json},
            {"path": review_path, "content": review_markdown},
            {"path": audit_path, "content": audit_markdown},
        ],
    }


def run_mission_chase_ai_runtime_governance_kit(
    *,
    inputs: dict[str, Any] | None = None,
    vault_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_mission_chase_ai_runtime_governance_kit(inputs=inputs, vault_root=vault_root)
