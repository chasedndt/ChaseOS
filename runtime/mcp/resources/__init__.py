"""Resource handler registry for Runtime MCP V1."""

from runtime.mcp.resources.audit_stream import runtime_audit_recent
from runtime.mcp.resources.boot_frame import context_boot_frame
from runtime.mcp.resources.briefing import operator_briefing_latest
from runtime.mcp.resources.current_truth import chaseos_current_truth
from runtime.mcp.resources.chaseos_safe import (
    chaseos_adapter_status,
    chaseos_current_state,
    chaseos_operator_brief_latest,
    chaseos_project_summary,
    chaseos_rnd_register_summary,
    chaseos_sic_workspace_summary,
)
from runtime.mcp.resources.handoff import runtime_handoff_current
from runtime.mcp.resources.permission_envelope import runtime_permission_envelope
from runtime.mcp.resources.runtime_capabilities import runtime_capabilities
from runtime.mcp.resources.runtime_identity import runtime_identity
from runtime.mcp.resources.runtime_surfaces import (
    chaseos_runtime_surfaces_summary,
    runtime_surfaces,
)
from runtime.mcp.resources.workflows import workflows_registry, workflows_role_boundaries


RESOURCE_HANDLERS = {
    "context.boot_frame": context_boot_frame,
    "runtime.identity": runtime_identity,
    "runtime.capabilities": runtime_capabilities,
    "runtime.surfaces": runtime_surfaces,
    "chaseos.current_truth": chaseos_current_truth,
    "workflows.registry": workflows_registry,
    "workflows.role_boundaries": workflows_role_boundaries,
    "runtime.permission_envelope": runtime_permission_envelope,
    "runtime.handoff.current": runtime_handoff_current,
    "runtime.audit.recent": runtime_audit_recent,
    "operator.briefing.latest": operator_briefing_latest,
    "chaseos.current_state": chaseos_current_state,
    "chaseos.project_summary": chaseos_project_summary,
    "chaseos.operator_brief_latest": chaseos_operator_brief_latest,
    "chaseos.sic_workspace_summary": chaseos_sic_workspace_summary,
    "chaseos.adapter_status": chaseos_adapter_status,
    "chaseos.rnd_register_summary": chaseos_rnd_register_summary,
    "chaseos.runtime_surfaces_summary": chaseos_runtime_surfaces_summary,
}

__all__ = ["RESOURCE_HANDLERS"]
