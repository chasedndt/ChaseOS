"""Fail-closed SiteOps referee checks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from runtime.siteops.budgets import check_budget_policy
from runtime.siteops.errors import SiteOpsPolicyError, SiteOpsValidationError
from runtime.siteops.models import PolicyDecision, SiteOpsScope
from runtime.siteops.tenancy import has_any_role, objects_by_id, user_roles


HIGH_RISK_APPROVAL_ACTIONS = {
    "export_file",
    "external_share",
    "publish_publicly",
    "purchase",
    "billing_action",
    "destructive_action",
    "account_mutation",
    "broker_connection",
    "live_trade",
    "invite_users",
    "credential_scope_expansion",
    "paid_provider_call",
}


def _decision(
    *,
    run_id: str,
    scope: SiteOpsScope,
    action: str,
    target: str,
    decision: str,
    reasons: list[str],
    policy_pack_version: str,
) -> PolicyDecision:
    return PolicyDecision(
        decision_id=f"decision_{run_id}_{len(action)}_{abs(hash((action, target, tuple(reasons)))) % 1000000}",
        run_id=run_id,
        tenant_id=scope.tenant_id,
        user_id=scope.user_id,
        action=action,
        target=target,
        decision=decision,  # type: ignore[arg-type]
        reasons=reasons,
        policy_pack_version=policy_pack_version,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )


def _require_scope_match(scope: SiteOpsScope, tenant: dict[str, Any]) -> None:
    if not scope.tenant_id or not scope.workspace_id or not scope.user_id:
        raise SiteOpsValidationError("tenant_id, workspace_id, and user_id are required")
    if tenant.get("tenant", {}).get("tenant_id") != scope.tenant_id:
        raise SiteOpsValidationError("Tenant scope mismatch")


def evaluate_siteops_policy(
    *,
    root,
    run_id: str,
    scope: SiteOpsScope,
    tenant: dict[str, Any],
    skill_installation: dict[str, Any],
    workflow_installation: dict[str, Any],
    workflow_template: dict[str, Any],
    provider_template: dict[str, Any] | None,
    provider_binding: dict[str, Any] | None,
    credential_ref: dict[str, Any] | None,
    browser_profile_ref: dict[str, Any] | None,
    budget_policy: dict[str, Any] | None,
    policy_pack_version: str,
    action: str | None = None,
    target_domain: str | None = None,
) -> dict[str, Any]:
    _require_scope_match(scope, tenant)
    decisions: list[PolicyDecision] = []

    roles = user_roles(tenant, scope.user_id)
    if not roles:
        raise SiteOpsPolicyError("user has no SiteOps roles in tenant")

    if not skill_installation.get("enabled"):
        raise SiteOpsPolicyError("site skill installation is disabled")
    if scope.workspace_id not in set(skill_installation.get("allowed_workspaces", [])):
        raise SiteOpsPolicyError("workspace is not allowed for this Site Skill installation")
    if not has_any_role(tenant, scope.user_id, skill_installation.get("allowed_roles", [])) and "tenant_admin" not in roles:
        raise SiteOpsPolicyError("user role is not allowed for this Site Skill installation")

    if not workflow_installation.get("enabled"):
        raise SiteOpsPolicyError("workflow installation is disabled")
    allowed_users = set(workflow_installation.get("allowed_users", []))
    if allowed_users and scope.user_id not in allowed_users:
        raise SiteOpsPolicyError("user is not allowed for this workflow installation")
    if not has_any_role(tenant, scope.user_id, workflow_installation.get("allowed_roles", [])) and "tenant_admin" not in roles:
        raise SiteOpsPolicyError("user role is not allowed for this workflow installation")

    checked_action = action or "dry_run"
    blocked = set(workflow_template.get("blocked_actions", []))
    if checked_action in blocked:
        decisions.append(
            _decision(
                run_id=run_id,
                scope=scope,
                action=checked_action,
                target=workflow_template["workflow_template_id"],
                decision="deny",
                reasons=["action is blocked by workflow template"],
                policy_pack_version=policy_pack_version,
            )
        )
        return {"status": "blocked", "decisions": decisions, "approval_action": None, "approval_reason": None}

    if target_domain and workflow_installation.get("allowed_domains"):
        allowed_domains = set(workflow_installation.get("allowed_domains", []))
        if target_domain not in allowed_domains:
            decisions.append(
                _decision(
                    run_id=run_id,
                    scope=scope,
                    action="domain_allowlist",
                    target=target_domain,
                    decision="deny",
                    reasons=["domain is not allowlisted for workflow installation"],
                    policy_pack_version=policy_pack_version,
                )
            )
            return {"status": "blocked", "decisions": decisions, "approval_action": None, "approval_reason": None}

    if workflow_template.get("site_profile_id"):
        if not browser_profile_ref:
            raise SiteOpsPolicyError("browser profile binding is required for site workflow")
        if browser_profile_ref.get("tenant_id") != scope.tenant_id or browser_profile_ref.get("user_id") != scope.user_id:
            raise SiteOpsPolicyError("browser profile scope mismatch")

    if provider_template:
        if not provider_binding:
            raise SiteOpsPolicyError("provider account binding is required for provider workflow")
        if provider_binding.get("tenant_id") != scope.tenant_id:
            raise SiteOpsPolicyError("provider account binding tenant mismatch")
        if provider_binding.get("user_id") not in (None, scope.user_id):
            raise SiteOpsPolicyError("provider account binding user mismatch")
        if not credential_ref:
            raise SiteOpsPolicyError("credential ref is required for provider workflow")
        if credential_ref.get("tenant_id") != scope.tenant_id:
            raise SiteOpsPolicyError("credential ref tenant mismatch")
        if credential_ref.get("user_id") not in (None, scope.user_id):
            raise SiteOpsPolicyError("credential ref user mismatch")
        if provider_template.get("requires_paid_credits") and not budget_policy:
            raise SiteOpsPolicyError("paid provider requires a budget policy")
        if budget_policy:
            budget = check_budget_policy(
                root,
                tenant_id=scope.tenant_id,
                budget_policy_id=budget_policy["budget_policy_id"],
                provider_id=provider_template["provider_adapter_id"],
                estimated_cost=provider_template.get("estimated_cost_per_run", "0"),
            )
            decisions.append(
                _decision(
                    run_id=run_id,
                    scope=scope,
                    action="provider_budget",
                    target=provider_template["provider_adapter_id"],
                    decision=budget["decision"],
                    reasons=[budget["reason"]],
                    policy_pack_version=policy_pack_version,
                )
            )
            if budget["decision"] == "deny":
                return {"status": "blocked", "decisions": decisions, "approval_action": None, "approval_reason": budget["reason"]}
            if budget["decision"] == "approval_required":
                return {
                    "status": "approval_needed",
                    "decisions": decisions,
                    "approval_action": "paid_provider_call",
                    "approval_reason": budget["reason"],
                }

    if checked_action in HIGH_RISK_APPROVAL_ACTIONS or checked_action in set(workflow_template.get("approval_required", [])):
        decisions.append(
            _decision(
                run_id=run_id,
                scope=scope,
                action=checked_action,
                target=workflow_template["workflow_template_id"],
                decision="approval_required",
                reasons=["action requires explicit SiteOps approval"],
                policy_pack_version=policy_pack_version,
            )
        )
        return {
            "status": "approval_needed",
            "decisions": decisions,
            "approval_action": checked_action,
            "approval_reason": "action requires explicit SiteOps approval",
        }

    decisions.append(
        _decision(
            run_id=run_id,
            scope=scope,
            action=checked_action,
            target=workflow_template["workflow_template_id"],
            decision="allow",
            reasons=["dry-run planning allowed within scoped installation"],
            policy_pack_version=policy_pack_version,
        )
    )
    return {"status": "planned", "decisions": decisions, "approval_action": None, "approval_reason": None}


def select_policy_pack(catalog: dict[str, Any], policy_pack_id: str) -> dict[str, Any]:
    packs = objects_by_id(catalog.get("policy_packs", []), "policy_pack_id")
    pack = packs.get(policy_pack_id)
    if not pack:
        raise SiteOpsPolicyError(f"policy pack not found: {policy_pack_id}")
    return pack


def evaluate_policy(
    *,
    tenant_id: str,
    user_id: str,
    action: str,
    target: str,
    allowed_domains: list[str],
    blocked_actions: list[str],
    roles: list[str],
    required_roles: list[str] | None = None,
    policy_pack_version: str = "siteops-production-scaffold-v1",
) -> dict[str, Any]:
    from urllib.parse import urlparse

    reasons: list[str] = []
    decision = "allow"
    if action in blocked_actions:
        decision = "deny"
        reasons.append(f"action blocked: {action}")
    if target.startswith(("http://", "https://")):
        hostname = urlparse(target).hostname or ""
        if allowed_domains and not any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed_domains):
            decision = "deny"
            reasons.append("target domain is not allowlisted")
    missing_roles = sorted(set(required_roles or []) - set(roles or []))
    if missing_roles:
        decision = "deny"
        reasons.append(f"missing required role(s): {', '.join(missing_roles)}")
    if decision == "allow" and action in HIGH_RISK_APPROVAL_ACTIONS:
        decision = "approval_required"
        reasons.append(f"action requires approval: {action}")
    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "action": action,
        "target": target,
        "decision": decision,
        "reasons": reasons,
        "policy_pack_version": policy_pack_version,
    }
