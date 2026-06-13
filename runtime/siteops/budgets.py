"""Budget policy helpers for SiteOps."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from runtime.siteops.errors import SiteOpsNotFoundError
from runtime.siteops.tenancy import load_tenant, objects_by_id


def _money(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def list_budget_policies(root=None, tenant_id: str = "local") -> list[dict[str, Any]]:
    tenant = load_tenant(root, tenant_id)
    return list(tenant.get("budget_policies", []))


def check_budget_policy(
    root=None,
    *,
    tenant_id: str = "local",
    budget_policy_id: str | None = None,
    provider_id: str | None = None,
    estimated_cost: Any = "0",
) -> dict[str, Any]:
    tenant = load_tenant(root, tenant_id)
    policies = list(tenant.get("budget_policies", []))
    policy = None
    if budget_policy_id:
        policy = objects_by_id(policies, "budget_policy_id").get(budget_policy_id)
    elif provider_id:
        policy = next((item for item in policies if item.get("provider_id") in (provider_id, None)), None)
    if not policy:
        raise SiteOpsNotFoundError("BudgetPolicy not found")
    cost = _money(estimated_cost)
    approval_threshold = _money(policy.get("require_approval_above"))
    max_per_run = _money(policy.get("max_cost_per_run"))
    if max_per_run and cost > max_per_run:
        decision = "deny"
        reason = "estimated cost exceeds max_cost_per_run"
    elif approval_threshold and cost > approval_threshold:
        decision = "approval_required"
        reason = "estimated cost exceeds require_approval_above"
    else:
        decision = "allow"
        reason = "estimated cost within budget policy"
    return {
        "budget_policy_id": policy["budget_policy_id"],
        "tenant_id": tenant_id,
        "provider_id": policy.get("provider_id") or provider_id,
        "estimated_cost": str(cost),
        "decision": decision,
        "reason": reason,
        "dry_run_required": bool(policy.get("dry_run_required", True)),
        "charged": False,
    }


def evaluate_budget(
    *,
    tenant_id: str,
    provider_id: str,
    estimated_cost: float,
    budget_policy: dict[str, Any] | None,
) -> dict[str, Any]:
    if budget_policy is None:
        return {"decision": "deny", "reasons": ["paid provider requires budget policy"]}
    if budget_policy.get("tenant_id") != tenant_id:
        return {"decision": "deny", "reasons": ["budget policy tenant mismatch"]}
    cost = _money(estimated_cost)
    max_per_run = _money(budget_policy.get("max_cost_per_run"))
    approval_threshold = _money(budget_policy.get("require_approval_above"))
    if max_per_run and cost > max_per_run:
        return {"decision": "deny", "reasons": ["estimated cost exceeds max_cost_per_run"]}
    if approval_threshold and cost > approval_threshold:
        return {"decision": "approval_required", "reasons": ["estimated cost exceeds require_approval_above"]}
    return {"decision": "allow", "reasons": ["estimated cost within budget policy"]}
