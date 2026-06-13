"""Tool handler registry for Runtime MCP."""

from runtime.mcp.tools.approval import approval_request_create
from runtime.mcp.tools.proposal import proposal_diff_preview, proposal_submit, proposal_validate
from runtime.mcp.tools.workflow_invoke import workflow_invoke_bounded
from runtime.mcp.tools.maintenance import vault_maintain
from runtime.mcp.tools.chaseos_safe import (
    chaseos_create_research_digest_draft,
    chaseos_generate_operator_brief_draft,
    chaseos_prepare_discord_alert_draft,
    chaseos_query_sic_evidence,
    chaseos_validate_writeback_target,
)

TOOL_HANDLERS = {
    "proposal.submit": proposal_submit,
    "proposal.validate": proposal_validate,
    "proposal.diff_preview": proposal_diff_preview,
    "approval_request.create": approval_request_create,
    "workflow.invoke_bounded": workflow_invoke_bounded,
    "vault.maintain": vault_maintain,
    "chaseos.generate_operator_brief_draft": chaseos_generate_operator_brief_draft,
    "chaseos.create_research_digest_draft": chaseos_create_research_digest_draft,
    "chaseos.prepare_discord_alert_draft": chaseos_prepare_discord_alert_draft,
    "chaseos.query_sic_evidence": chaseos_query_sic_evidence,
    "chaseos.validate_writeback_target": chaseos_validate_writeback_target,
}

__all__ = ["TOOL_HANDLERS"]
