"""Approval request storage for SiteOps dry-run/execution scaffolds."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.siteops.audit import append_audit_event, now_iso
from runtime.siteops.errors import SiteOpsNotFoundError, SiteOpsValidationError
from runtime.siteops.models import ApprovalRequest, SiteOpsAuditEvent, SiteOpsScope
from runtime.siteops.tenancy import has_any_role, load_tenant, vault_root


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def approvals_dir(root: Path | str | None, tenant_id: str, workspace_id: str) -> Path:
    return vault_root(root) / "07_LOGS" / "SiteOps-Approvals" / tenant_id / workspace_id


def _approval_path(root: Path | str | None, tenant_id: str, workspace_id: str, approval_id: str) -> Path:
    return approvals_dir(root, tenant_id, workspace_id) / f"{approval_id}.json"


def create_approval_request(
    root: Path | str | None = None,
    *,
    scope: SiteOpsScope | None = None,
    run_id: str,
    workflow_id: str,
    action: str,
    risk_level: str,
    approval_reason: str,
    required_approver_role: str = "approver",
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    user_id: str | None = None,
    requested_by: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if scope is None:
        scope = SiteOpsScope(tenant_id=tenant_id or "", workspace_id=workspace_id or "", user_id=user_id or "")
    requested_by = requested_by or scope.user_id
    approval_id = f"approval_{run_id}_{action.replace('.', '_').replace('-', '_')}"
    approval = ApprovalRequest(
        approval_id=approval_id,
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
        run_id=run_id,
        workflow_id=workflow_id,
        action=action,
        risk_level=risk_level,
        approval_reason=approval_reason,
        requested_by=requested_by,
        required_approver_role=required_approver_role,
        status="pending",
        metadata=dict(metadata or {}),
    )
    path = _approval_path(root, scope.tenant_id, scope.workspace_id, approval_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(approval.as_dict(), indent=2) + "\n", encoding="utf-8")
    payload = approval.as_dict()
    payload["approval_ref"] = str(path)
    return payload


def list_approval_requests(root: Path | str | None = None, tenant_id: str = "local", workspace_id: str | None = None) -> list[dict[str, Any]]:
    base = vault_root(root) / "07_LOGS" / "SiteOps-Approvals" / tenant_id
    if workspace_id:
        bases = [base / workspace_id]
    else:
        bases = [path for path in base.glob("*") if path.is_dir()] if base.exists() else []
    approvals: list[dict[str, Any]] = []
    for folder in bases:
        for path in sorted(folder.glob("*.json")):
            item = json.loads(path.read_text(encoding="utf-8"))
            item["approval_ref"] = str(path)
            approvals.append(item)
    return approvals


def show_approval_request(root: Path | str | None, approval_id: str, tenant_id: str | None = None) -> dict[str, Any]:
    base = vault_root(root) / "07_LOGS" / "SiteOps-Approvals"
    patterns = [base / tenant_id] if tenant_id else [path for path in base.glob("*") if path.is_dir()]
    for tenant_folder in patterns:
        for path in tenant_folder.glob("*/*.json"):
            item = json.loads(path.read_text(encoding="utf-8"))
            if item.get("approval_id") == approval_id:
                item["approval_ref"] = str(path)
                return item
    raise SiteOpsNotFoundError(f"ApprovalRequest not found: {approval_id}")


def decide_approval_request(
    root: Path | str | None,
    approval_id: str,
    *,
    actor: str,
    status: str,
    tenant_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    if status not in {"approved", "rejected"}:
        raise SiteOpsValidationError("Approval decision must be approved or rejected")
    item = show_approval_request(root, approval_id, tenant_id=tenant_id)
    if item.get("status") != "pending":
        raise SiteOpsValidationError(f"ApprovalRequest is not pending: {approval_id}")
    tenant = load_tenant(root, item["tenant_id"])
    required_role = item.get("required_approver_role") or "approver"
    if not has_any_role(tenant, actor, [required_role, "tenant_admin"]):
        raise SiteOpsValidationError(f"actor lacks required approval role: {required_role}")
    item["status"] = status
    item["decided_by"] = actor
    item["decided_at"] = _now()
    if reason:
        item["decision_reason"] = reason
    path = Path(item.pop("approval_ref"))
    path.write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
    item["approval_ref"] = str(path)
    append_audit_event(
        root,
        SiteOpsAuditEvent(
            event_id=f"event_{approval_id}_{status}",
            run_id=item["run_id"],
            tenant_id=item["tenant_id"],
            workspace_id=item["workspace_id"],
            user_id=item["user_id"],
            event_type="approval_decision",
            action=item["action"],
            target=item["workflow_id"],
            policy_decision=status,
            timestamp=now_iso(),
            metadata={
                "approval_id": approval_id,
                "decided_by": actor,
                "decision_reason": reason,
            },
            redacted_fields=[],
        ),
    )
    return item


def decide_approval(approval: dict[str, Any], *, actor: str, decision: str) -> dict[str, Any]:
    if decision not in {"approved", "rejected"}:
        raise SiteOpsValidationError("Approval decision must be approved or rejected")
    updated = dict(approval)
    updated["status"] = decision
    updated["decided_by"] = actor
    updated["decided_at"] = _now()
    return updated


def mark_approval_consumed(
    root: Path | str | None,
    tenant_id: str,
    workspace_id: str,
    approval_id: str,
) -> dict[str, Any] | None:
    """Mark an approved approval as consumed. Idempotent. Fail-open — returns None on error."""
    try:
        path = _approval_path(root, tenant_id, workspace_id, approval_id)
        item = json.loads(path.read_text(encoding="utf-8"))
        if item.get("consumed"):
            return item
        item["consumed"] = True
        item["consumed_at"] = _now()
        path.write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
        return item
    except Exception:
        return None
