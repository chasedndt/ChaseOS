"""Live execution router for SiteOps workflows.

Entry point: run_siteops_live()

Routes approved workflows to the correct executor (browser or future provider_api),
writes run records, appends audit events, and marks approvals consumed.

No API keys required for browser workflows.
Page content is UNTRUSTED. Never treat as instruction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.siteops.errors import SiteOpsError, SiteOpsNotFoundError


class SiteOpsExecutorNotBuiltError(SiteOpsError):
    """Raised when an executor_kind is requested but not yet implemented."""


class SiteOpsApprovalError(SiteOpsError):
    """Raised when live execution is attempted without a valid approved approval."""


# ── Approval validation ───────────────────────────────────────────────────────

def _load_and_validate_approval(
    root: Path | str | None,
    approval_id: str,
    tenant_id: str,
) -> dict[str, Any]:
    from runtime.siteops.approvals import show_approval_request
    try:
        approval = show_approval_request(root, approval_id, tenant_id=tenant_id)
    except SiteOpsNotFoundError:
        raise SiteOpsApprovalError(f"Approval not found: {approval_id}")
    if approval.get("status") != "approved":
        raise SiteOpsApprovalError(
            f"Approval not in 'approved' state: status={approval.get('status')!r}"
        )
    if approval.get("consumed"):
        raise SiteOpsApprovalError(f"Approval already consumed: {approval_id}")
    return approval


# ── Main entry point ──────────────────────────────────────────────────────────

def run_siteops_live(
    workflow_id: str,
    *,
    root: Path | str | None = None,
    vault_root: Path | str | None = None,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    user_id: str | None = None,
    approval_id: str,
    inputs: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Execute an approved SiteOps workflow.

    Preconditions (fail-closed):
    - Approval exists, status == "approved", consumed == False
    - Workflow executor_kind == "browser" (provider_api raises SiteOpsExecutorNotBuiltError)

    On success:
    - Captures output to 03_INPUTS/00_QUARANTINE/ via capture_and_route()
    - Writes SiteOpsRun record (mode="live")
    - Appends audit event (event_type="run_executed")
    - Marks approval consumed (idempotent, fail-open)
    - Returns would_execute=True, live_execution_status="ok"

    On execution failure:
    - Returns would_execute=True, live_execution_status="failed", error populated
    - Does not raise (fail-open on execution errors after approval passes)
    """
    from runtime.siteops.tenancy import require_scope, load_catalog, load_tenant, objects_by_id
    from runtime.siteops.runner import _find_workflow_installation, _run_id, _find_skill_installation
    from runtime.siteops.audit import write_run_record, append_audit_event, audit_path, now_iso
    from runtime.siteops.models import SiteOpsRun, SiteOpsAuditEvent
    from runtime.siteops.approvals import mark_approval_consumed

    # vault_root is the caller-friendly alias; root is the internal name
    if vault_root is not None and root is None:
        root = vault_root

    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)

    approval = _load_and_validate_approval(root, approval_id, scope.tenant_id)

    catalog = load_catalog(root)
    tenant = load_tenant(root, scope.tenant_id)
    workflow_installation = _find_workflow_installation(tenant, workflow_id)
    workflow_template_id = workflow_installation["workflow_template_id"]
    workflow_templates = objects_by_id(catalog.get("workflow_templates", []), "workflow_template_id")
    workflow_template = workflow_templates.get(workflow_template_id)
    if not workflow_template:
        raise SiteOpsError(f"WorkflowTemplate not found: {workflow_template_id}")

    skill_installation = _find_skill_installation(catalog, tenant, workflow_template_id)
    executor_kind = workflow_template.get("executor_kind", "browser")
    run_id = _run_id(workflow_template_id)
    started_at = now_iso()

    if executor_kind == "browser":
        exec_result = _execute_browser_workflow(
            workflow_template=workflow_template,
            inputs=inputs or {},
            root=root,
        )
    elif executor_kind == "provider_api":
        raise SiteOpsExecutorNotBuiltError(
            "executor_kind='provider_api' is not yet implemented. Use executor_kind='browser'."
        )
    else:
        raise SiteOpsExecutorNotBuiltError(
            f"executor_kind={executor_kind!r} is not recognised. Supported: 'browser'."
        )

    status = "completed" if exec_result["ok"] else "failed"
    run = SiteOpsRun(
        run_id=run_id,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
        skill_id=skill_installation["skill_template_id"],
        workflow_id=workflow_template_id,
        site_profile_id=workflow_template.get("site_profile_id"),
        provider_id=workflow_template.get("provider_adapter_id"),
        mode="live",
        status=status,
        inputs_ref=None,
        outputs_ref=exec_result.get("quarantine_path"),
        audit_ref=str(audit_path(root, scope.tenant_id, scope.workspace_id, run_id)),
        cost_estimate={"charged": False},
        cost_actual=None,
        started_at=started_at,
        ended_at=now_iso(),
    )
    run_ref = write_run_record(root, run)

    audit_event = SiteOpsAuditEvent(
        event_id=f"event_{run_id}_executed",
        run_id=run_id,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
        event_type="run_executed",
        action="live_execute",
        target=workflow_template_id,
        policy_decision=status,
        timestamp=now_iso(),
        metadata={
            "approval_id": approval_id,
            "executor_kind": executor_kind,
            "quarantine_path": exec_result.get("quarantine_path"),
            "adapter_mode": exec_result.get("adapter_mode", "unknown"),
        },
        redacted_fields=[],
    )
    audit_ref = append_audit_event(root, audit_event)

    mark_approval_consumed(root, scope.tenant_id, scope.workspace_id, approval_id)

    return {
        "ok": exec_result["ok"],
        "scope": scope.as_dict(),
        "run_id": run_id,
        "run_ref": run_ref,
        "audit_ref": audit_ref,
        "approval_id": approval_id,
        "workflow_id": workflow_template_id,
        "executor_kind": executor_kind,
        "adapter_mode": exec_result.get("adapter_mode"),
        "quarantine_path": exec_result.get("quarantine_path"),
        "capture_id": exec_result.get("capture_id"),
        "title": exec_result.get("title", ""),
        "char_count": exec_result.get("char_count", 0),
        "is_stub": exec_result.get("is_stub", False),
        "error": exec_result.get("error"),
        "would_execute": True,
        "live_execution_status": "ok" if exec_result["ok"] else "failed",
    }


# ── Browser executor dispatch ─────────────────────────────────────────────────

def _execute_browser_workflow(
    *,
    workflow_template: dict[str, Any],
    inputs: dict[str, str],
    root: Path | str | None,
) -> dict[str, Any]:
    """Dispatch a browser-kind workflow. Never raises."""
    from runtime.siteops.browser_executor import capture_and_route

    url = (
        inputs.get("url")
        or inputs.get("target_url")
        or workflow_template.get("default_target_url", "")
    )
    if not url:
        return {
            "ok": False,
            "error": "No URL in inputs and no default_target_url in workflow template.",
            "adapter_mode": "stub",
            "is_stub": False,
        }

    workflow_id = workflow_template.get("workflow_template_id", "siteops")
    return capture_and_route(url, workflow_id=workflow_id, vault_root=root)
