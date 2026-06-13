"""Dry-run-only production runner for SiteOps."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.siteops.approvals import create_approval_request
from runtime.siteops.audit import append_audit_event, audit_path, now_iso, run_path, write_run_record
from runtime.siteops.errors import SiteOpsNotFoundError, SiteOpsPolicyError, SiteOpsValidationError
from runtime.siteops.executor import run_siteops_live as _run_siteops_live_impl  # re-exported below
from runtime.siteops.models import SiteOpsAuditEvent, SiteOpsRun, SiteOpsScope
from runtime.siteops.policy import evaluate_siteops_policy, select_policy_pack
from runtime.siteops.tenancy import load_catalog, load_tenant, objects_by_id, require_scope
from runtime.siteops.validator import validate_production_siteops


def _slug(value: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in clean.split("-") if part) or "siteops"


def _run_id(workflow_id: str) -> str:
    return f"siteops_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{_slug(workflow_id)}"


def _find_workflow_installation(tenant: dict[str, Any], workflow_id: str) -> dict[str, Any]:
    installs = tenant.get("workflow_installations", [])
    for item in installs:
        if item.get("workflow_installation_id") == workflow_id or item.get("workflow_template_id") == workflow_id:
            return item
    raise SiteOpsNotFoundError(f"WorkflowInstallation not found for workflow: {workflow_id}")


def _find_skill_installation(catalog: dict[str, Any], tenant: dict[str, Any], workflow_template_id: str) -> dict[str, Any]:
    templates = catalog.get("site_skill_templates", [])
    matching_skill_ids = [
        item["skill_template_id"]
        for item in templates
        if workflow_template_id in item.get("workflow_template_ids", [])
    ]
    for item in tenant.get("site_skill_installations", []):
        if item.get("skill_template_id") in matching_skill_ids:
            return item
    raise SiteOpsNotFoundError(f"Tenant has not installed a Site Skill for workflow: {workflow_template_id}")


def _required_inputs(workflow_template: dict[str, Any]) -> list[str]:
    schema = workflow_template.get("inputs_schema", {})
    values = schema.get("required", [])
    return [str(item) for item in values if item]


def _resolve_provider_context(
    catalog: dict[str, Any],
    tenant: dict[str, Any],
    workflow_installation: dict[str, Any],
    workflow_template: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    provider_id = workflow_template.get("provider_adapter_id")
    provider_template = objects_by_id(catalog.get("provider_templates", []), "provider_adapter_id").get(provider_id) if provider_id else None
    provider_binding = None
    credential_ref = None
    budget_policy = None
    if workflow_installation.get("provider_account_binding"):
        provider_binding = objects_by_id(tenant.get("provider_account_bindings", []), "provider_account_binding_id").get(workflow_installation["provider_account_binding"])
    if provider_binding:
        credential_ref = objects_by_id(tenant.get("credential_refs", []), "credential_ref_id").get(provider_binding.get("credential_ref_id"))
        budget_policy = objects_by_id(tenant.get("budget_policies", []), "budget_policy_id").get(provider_binding.get("budget_policy_id"))
    return provider_template, provider_binding, credential_ref, budget_policy


def _resolve_browser_profile(tenant: dict[str, Any], workflow_installation: dict[str, Any]) -> dict[str, Any] | None:
    binding = workflow_installation.get("browser_profile_binding")
    if not binding:
        return None
    return objects_by_id(tenant.get("browser_profile_refs", []), "browser_profile_ref_id").get(binding)


def run_siteops_dry_run(
    *,
    root: Path | str | None = None,
    workflow_id: str,
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    inputs: dict[str, str] | None = None,
    action: str | None = None,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    scope = require_scope(tenant_id=tenant_id, workspace_id=workspace_id, user_id=user_id)
    validation = validate_production_siteops(root, scope.tenant_id)
    if not validation["ok"]:
        raise SiteOpsValidationError("; ".join(validation["errors"]))

    catalog = load_catalog(root)
    tenant = load_tenant(root, scope.tenant_id)
    workflow_installation = _find_workflow_installation(tenant, workflow_id)
    workflow_template_id = workflow_installation["workflow_template_id"]
    workflow_templates = objects_by_id(catalog.get("workflow_templates", []), "workflow_template_id")
    workflow_template = workflow_templates.get(workflow_template_id)
    if not workflow_template:
        raise SiteOpsNotFoundError(f"WorkflowTemplate not found: {workflow_template_id}")
    skill_installation = _find_skill_installation(catalog, tenant, workflow_template_id)
    provider_template, provider_binding, credential_ref, budget_policy = _resolve_provider_context(catalog, tenant, workflow_installation, workflow_template)
    browser_profile_ref = _resolve_browser_profile(tenant, workflow_installation)
    policy_pack = select_policy_pack(catalog, skill_installation.get("default_policy_pack") or "siteops_default_v1")

    supplied = inputs or {}
    missing = [name for name in _required_inputs(workflow_template) if not supplied.get(name)]
    if missing:
        raise SiteOpsValidationError(f"Missing required workflow inputs: {', '.join(missing)}")

    run_id = _run_id(workflow_template_id)
    policy = evaluate_siteops_policy(
        root=root,
        run_id=run_id,
        scope=scope,
        tenant=tenant,
        skill_installation=skill_installation,
        workflow_installation=workflow_installation,
        workflow_template=workflow_template,
        provider_template=provider_template,
        provider_binding=provider_binding,
        credential_ref=credential_ref,
        browser_profile_ref=browser_profile_ref,
        budget_policy=budget_policy,
        policy_pack_version=policy_pack["version"],
        action=action,
    )

    status = policy["status"]
    now = now_iso()
    run = SiteOpsRun(
        run_id=run_id,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
        skill_id=skill_installation["skill_template_id"],
        workflow_id=workflow_template_id,
        site_profile_id=workflow_template.get("site_profile_id"),
        provider_id=workflow_template.get("provider_adapter_id"),
        mode="dry_run",
        status=status,
        inputs_ref=None,
        outputs_ref=None,
        audit_ref=str(audit_path(root, scope.tenant_id, scope.workspace_id, run_id)),
        cost_estimate={
            "provider": workflow_template.get("provider_adapter_id"),
            "estimated_cost_per_run": provider_template.get("estimated_cost_per_run") if provider_template else "0",
            "charged": False,
        },
        cost_actual=None,
        started_at=now,
        ended_at=now,
    )

    approval = None
    if status == "approval_needed" and policy.get("approval_action"):
        approval = create_approval_request(
            root,
            scope=scope,
            run_id=run_id,
            workflow_id=workflow_template_id,
            action=policy["approval_action"],
            risk_level=skill_installation.get("risk_level", "medium"),
            approval_reason=policy.get("approval_reason") or "SiteOps approval required",
        )

    run_ref = None
    audit_ref = None
    if write_artifacts:
        run_ref = write_run_record(root, run)
        for decision in policy["decisions"]:
            event = SiteOpsAuditEvent(
                event_id=f"event_{decision.decision_id}",
                run_id=run_id,
                tenant_id=scope.tenant_id,
                workspace_id=scope.workspace_id,
                user_id=scope.user_id,
                event_type="policy_decision",
                action=decision.action,
                target=decision.target,
                policy_decision=decision.decision,
                timestamp=decision.evaluated_at,
                metadata={"reasons": decision.reasons, "inputs": supplied},
                redacted_fields=[],
            )
            audit_ref = append_audit_event(root, event)
        planned_event = SiteOpsAuditEvent(
            event_id=f"event_{run_id}_planned",
            run_id=run_id,
            tenant_id=scope.tenant_id,
            workspace_id=scope.workspace_id,
            user_id=scope.user_id,
            event_type="run_planned",
            action="dry_run",
            target=workflow_template_id,
            policy_decision=status,
            timestamp=now,
            metadata={"approval_id": approval.get("approval_id") if approval else None},
            redacted_fields=[],
        )
        audit_ref = append_audit_event(root, planned_event)

    return {
        "ok": status != "blocked",
        "scope": scope.as_dict(),
        "run": run.as_dict(),
        "run_ref": run_ref,
        "audit_ref": audit_ref or run.audit_ref,
        "approval": approval,
        "policy_decisions": [decision.as_dict() for decision in policy["decisions"]],
        "selected": {
            "skill_installation_id": skill_installation["installation_id"],
            "skill_template_id": skill_installation["skill_template_id"],
            "workflow_installation_id": workflow_installation["workflow_installation_id"],
            "workflow_template_id": workflow_template_id,
            "provider_account_binding_id": provider_binding.get("provider_account_binding_id") if provider_binding else None,
            "browser_profile_ref_id": browser_profile_ref.get("browser_profile_ref_id") if browser_profile_ref else None,
            "budget_policy_id": budget_policy.get("budget_policy_id") if budget_policy else None,
        },
        "provider": {
            "provider_adapter_id": provider_template.get("provider_adapter_id") if provider_template else None,
            "required_capability": workflow_template.get("required_capability"),
            "estimated_cost_per_run": provider_template.get("estimated_cost_per_run") if provider_template else "0",
            "credentials_configured": credential_ref is not None and bool(credential_ref.get("secret_store_ref")),
            "fallback_provider_exists": bool(workflow_template.get("fallback_provider_adapter_ids")),
            "charged": False,
        },
        "browser_profile": {
            "required": bool(workflow_template.get("site_profile_id")),
            "configured": browser_profile_ref is not None,
            "session_value_visible": False,
        },
        "would_execute": False,
        "live_execution_status": "NOT BUILT",
    }


def run_siteops_live(
    workflow_id: str,
    *,
    approval_id: str,
    inputs: dict[str, str] | None = None,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    user_id: str | None = None,
    vault_root: Path | str | None = None,
) -> dict:
    """Execute an approved SiteOps workflow via the live browser executor.

    Public wrapper around executor.run_siteops_live(). No API keys required.
    Returns would_execute=True and live_execution_status="ok" or "failed".
    """
    return _run_siteops_live_impl(
        root=vault_root,
        workflow_id=workflow_id,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        approval_id=approval_id,
        inputs=inputs,
    )


def dry_run_workflow(
    workflow_id: str,
    *,
    inputs: dict[str, str],
    tenant_id: str | None,
    workspace_id: str | None,
    user_id: str | None,
    action: str | None = None,
    vault_root: Path | str | None = None,
    artifact_root: Path | str | None = None,
    write_audit: bool = False,
) -> dict[str, Any]:
    payload = run_siteops_dry_run(
        root=vault_root,
        workflow_id=workflow_id,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        user_id=user_id,
        inputs=inputs,
        action=action,
        write_artifacts=write_audit,
    )
    payload["status"] = payload["run"]["status"]
    payload["approval_request"] = payload.get("approval")
    payload["dry_run"] = {
        "would_execute": payload.get("would_execute", False),
        "workflow_id": payload["run"]["workflow_id"],
    }
    return payload
