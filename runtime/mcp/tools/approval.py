"""Approval request artifact tool.

Response shape frozen against ChaseOS-MCP-Data-Contracts.md v1.0.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from runtime.mcp.config import MCPConfig
from runtime.mcp.errors import ERR_PROPOSAL_NOT_FOUND, ERR_WRITE_FAILED, domain_error, input_error, system_error
from runtime.mcp.staging.store import ProposalStore
from runtime.mcp.types import HandlerResult, PermissionEnvelope


def approval_request_create(
    params: dict[str, Any],
    config: MCPConfig,
    envelope: PermissionEnvelope,
) -> HandlerResult:
    proposal_id = params.get("proposal_id")
    if not isinstance(proposal_id, str) or not proposal_id:
        return HandlerResult(False, error=input_error(ERR_PROPOSAL_NOT_FOUND, "proposal_id is required"))

    artifact = ProposalStore(config.staging_dir).read(proposal_id)
    if artifact is None:
        return HandlerResult(
            False,
            error=domain_error(ERR_PROPOSAL_NOT_FOUND, "Proposal artifact was not found.", proposal_id=proposal_id),
        )

    approval_request_id = f"aprq-{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    human_context = params.get("human_context") or ""

    date_str = created_at[:10]
    filename = f"{date_str}-approval-request-{proposal_id[:16]}.md"
    path = config.operator_briefs_dir / filename
    content = "\n".join(
        [
            "# Runtime MCP Approval Request",
            "",
            f"- approval_request_id: {approval_request_id}",
            f"- proposal_id: {proposal_id}",
            f"- target_file: {artifact.target_file}",
            f"- change_type: {artifact.change_type}",
            f"- created_at_utc: {created_at}",
            f"- protected_file: {artifact.governance_flags.get('is_protected_file')}",
            f"- writeback_scope_declared: {artifact.governance_flags.get('writeback_scope_declared')}",
            "",
            "## Description",
            artifact.description or "(none provided)",
            "",
            "## Human Context",
            human_context or "(none provided)",
            "",
            "## Governance",
            "This is a human review artifact only. Runtime MCP V1 has no apply or commit path.",
        ]
    )

    try:
        config.operator_briefs_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(content + "\n", encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        return HandlerResult(
            False,
            error=system_error(ERR_WRITE_FAILED, str(exc), proposal_id=proposal_id),
            audit_metadata={
                "tool": "approval_request.create",
                "proposal_id": proposal_id,
                "artifact_write": "failed",
            },
        )

    artifact_rel = str(path.relative_to(config.vault_root))
    return HandlerResult(
        True,
        {
            "approval_request_id": approval_request_id,
            "proposal_id": proposal_id,
            "approval_status": "pending_human_review",
            "created_at": created_at,
            "delivery_confirmed": True,
            "delivered_to": [artifact_rel],
            "next_action": "Human operator must review and approve before proposal can be applied",
        },
        files_written=[artifact_rel],
        audit_metadata={
            "tool": "approval_request.create",
            "proposal_id": proposal_id,
            "artifact_path": artifact_rel,
        },
    )
