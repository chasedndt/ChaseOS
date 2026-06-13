from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.aor.engine import AORRunResult, run_workflow
from runtime.osril.wait_resume import build_wait_resume_state


def _result_payload(item: dict[str, Any], result: AORRunResult) -> dict[str, Any]:
    approval_gate = result.outputs.get("approval_gate", {}) if isinstance(result.outputs, dict) else {}
    return {
        "approval_id": item.get("approval_id"),
        "workflow_id": item.get("workflow_id"),
        "runtime_id": item.get("runtime_id"),
        "status": result.status,
        "audit_id": result.audit_id,
        "stage_reached": result.stage_reached,
        "resume_executed": bool(approval_gate.get("resume_executed")),
        "resume_id": approval_gate.get("resume_id"),
        "resume_path": approval_gate.get("resume_path"),
        "escalation_reason": result.escalation_reason,
        "error": result.error,
        "outputs": result.outputs,
    }


def _planned_payload(item: dict[str, Any]) -> dict[str, Any]:
    approval_id = str(item.get("approval_id") or "")
    workflow_id = str(item.get("workflow_id") or "")
    return {
        "approval_id": approval_id,
        "workflow_id": workflow_id,
        "runtime_id": item.get("runtime_id"),
        "status": "planned",
        "resume_executed": False,
        "command_hint": f"chaseos run {workflow_id} --input operator_approval_ref={approval_id}",
    }


def resume_ready_approvals(
    vault_root: str | Path,
    *,
    approval_id: str | None = None,
    runtime_id: str | None = None,
    workflow_id: str | None = None,
    session_id: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Resume OSRIL approvals that are already approved and applied.

    This is a bounded one-shot runner. It does not wait for new approvals and it
    does not bypass AOR approval-gate checks; each item is resumed through the
    same `operator_approval_ref` path as a manual `chaseos run` command.
    """
    root = Path(vault_root)
    state = build_wait_resume_state(
        root,
        approval_id=approval_id,
        runtime_id=runtime_id,
        workflow_id=workflow_id,
        session_id=session_id,
        decision="APPROVE",
        wait_status="ready_to_resume",
        limit=limit,
    )
    ready_items = list(state.get("items") or [])
    results: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for item in ready_items:
        item_approval_id = str(item.get("approval_id") or "").strip()
        item_workflow_id = str(item.get("workflow_id") or "").strip()
        item_runtime_id = str(item.get("runtime_id") or "").strip() or "openclaw"
        if not item_approval_id or not item_workflow_id:
            skipped.append(
                {
                    "approval_id": item.get("approval_id"),
                    "workflow_id": item.get("workflow_id"),
                    "runtime_id": item.get("runtime_id"),
                    "status": "skipped",
                    "reason": "missing approval_id or workflow_id",
                }
            )
            continue
        if dry_run:
            results.append(_planned_payload(item))
            continue

        result = run_workflow(
            item_workflow_id,
            inputs={"operator_approval_ref": item_approval_id},
            vault_root=root,
            runtime_id=item_runtime_id,
        )
        results.append(_result_payload(item, result))

    resumed_count = sum(1 for item in results if item.get("resume_executed") is True)
    failed_count = sum(
        1
        for item in results
        if item.get("status") not in {"success", "dry_run_ok", "planned"}
    )
    planned_count = sum(1 for item in results if item.get("status") == "planned")
    return {
        "mode": "single" if approval_id else "list",
        "dry_run": bool(dry_run),
        "ready_count": len(ready_items),
        "attempted_count": 0 if dry_run else len(results),
        "planned_count": planned_count,
        "resumed_count": resumed_count,
        "failed_count": failed_count,
        "skipped_count": len(skipped),
        "results": results,
        "skipped": skipped,
        "wait_resume_state": state,
        "filters": {
            "approval_id": approval_id,
            "runtime_id": runtime_id,
            "workflow_id": workflow_id,
            "session_id": session_id,
            "limit": limit,
        },
    }
