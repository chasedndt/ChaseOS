"""Typed SiteOps production scaffold objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


OwnerType = Literal["system", "tenant", "workspace", "user"]
Visibility = Literal["private", "workspace", "tenant", "public_catalog"]
RunMode = Literal["scout", "dry_run", "assisted", "execution"]
RunStatus = Literal["planned", "running", "approval_needed", "blocked", "failed", "succeeded", "cancelled"]
PolicyDecisionValue = Literal["allow", "deny", "approval_required"]


@dataclass(frozen=True)
class SiteSkillTemplate:
    skill_template_id: str
    display_name: str
    category: str
    site_profile_id: str | None
    workflow_template_ids: list[str]
    provider_adapter_ids: list[str]
    risk_level: str
    required_capabilities: list[str]
    required_approvals: list[str]
    default_policy_pack: str
    owner_type: OwnerType
    visibility: Visibility
    version: str
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TenantSiteSkillInstallation:
    installation_id: str
    tenant_id: str
    skill_template_id: str
    enabled: bool
    allowed_workspaces: list[str]
    allowed_roles: list[str]
    policy_overrides: dict[str, Any]
    provider_overrides: dict[str, Any]
    approval_overrides: dict[str, Any]
    budget_policy_id: str | None
    created_by: str
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowTemplate:
    workflow_template_id: str
    workflow_type: str
    site_profile_id: str | None
    provider_adapter_id: str | None
    default_mode: str
    inputs_schema: dict[str, Any]
    steps: list[str]
    approval_required: list[str]
    blocked_actions: list[str]
    output_schema: dict[str, Any]
    audit_required: bool
    version: str
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowInstallation:
    workflow_installation_id: str
    tenant_id: str
    workspace_id: str | None
    workflow_template_id: str
    enabled: bool
    allowed_users: list[str]
    allowed_roles: list[str]
    configured_inputs: dict[str, Any]
    policy_overrides: dict[str, Any]
    provider_account_binding: str | None
    browser_profile_binding: str | None
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UserBrowserProfileRef:
    browser_profile_ref_id: str
    tenant_id: str
    user_id: str
    provider: str
    allowed_domains: list[str]
    status: str
    created_at: str
    last_verified_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CredentialRef:
    credential_ref_id: str
    tenant_id: str
    user_id: str | None
    provider_id: str
    credential_type: str
    secret_store_ref: str
    status: str
    last_verified_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderAccountBinding:
    provider_account_binding_id: str
    tenant_id: str
    user_id: str | None
    provider_id: str
    credential_ref_id: str
    budget_policy_id: str | None
    allowed_capabilities: list[str]
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BudgetPolicy:
    budget_policy_id: str
    tenant_id: str
    workspace_id: str | None
    user_id: str | None
    provider_id: str | None
    max_cost_per_run: str
    max_cost_per_day: str
    max_cost_per_month: str
    require_approval_above: str
    dry_run_required: bool
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SiteOpsScope:
    tenant_id: str
    workspace_id: str
    user_id: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class PolicyDecision:
    decision_id: str
    run_id: str
    tenant_id: str
    user_id: str
    action: str
    target: str
    decision: PolicyDecisionValue
    reasons: list[str]
    policy_pack_version: str
    evaluated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovalRequest:
    approval_id: str
    tenant_id: str
    workspace_id: str
    user_id: str
    run_id: str
    workflow_id: str
    action: str
    risk_level: str
    approval_reason: str
    requested_by: str
    required_approver_role: str
    status: str
    decided_by: str | None = None
    decided_at: str | None = None
    metadata: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SiteOpsRun:
    run_id: str
    tenant_id: str
    workspace_id: str
    user_id: str
    skill_id: str
    workflow_id: str
    site_profile_id: str | None
    provider_id: str | None
    mode: str
    status: str
    inputs_ref: str | None
    outputs_ref: str | None
    audit_ref: str | None
    cost_estimate: Any
    cost_actual: Any
    started_at: str
    ended_at: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SiteOpsAuditEvent:
    event_id: str
    run_id: str
    tenant_id: str
    workspace_id: str
    user_id: str
    event_type: str
    action: str
    target: str
    policy_decision: Any
    timestamp: str
    metadata: dict[str, Any]
    redacted_fields: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_siteops_run(
    *,
    tenant_id: str,
    workspace_id: str,
    user_id: str,
    workflow_id: str,
    skill_id: str | None = None,
    site_profile_id: str | None = None,
    provider_id: str | None = None,
    mode: str = "dry_run",
    status: str = "planned",
    inputs_ref: str | None = None,
    outputs_ref: str | None = None,
    audit_ref: str | None = None,
    cost_estimate: Any = None,
) -> dict[str, Any]:
    from datetime import datetime, timezone
    from uuid import uuid4

    now = datetime.now(timezone.utc).isoformat()
    return {
        "run_id": f"siteops_run_{uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "skill_id": skill_id,
        "workflow_id": workflow_id,
        "site_profile_id": site_profile_id,
        "provider_id": provider_id,
        "mode": mode,
        "status": status,
        "inputs_ref": inputs_ref,
        "outputs_ref": outputs_ref,
        "audit_ref": audit_ref,
        "cost_estimate": cost_estimate,
        "cost_actual": None,
        "started_at": now,
        "ended_at": None,
    }
