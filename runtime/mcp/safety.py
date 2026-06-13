"""Runtime MCP safety mode and surface availability checks."""

from __future__ import annotations

from runtime.mcp.config import MCPConfig
from runtime.mcp.errors import ERR_SURFACE_UNAVAILABLE, domain_error
from runtime.mcp.types import MCPError, MCPRequest, PermissionEnvelope, SurfaceClass


V1_RESOURCES = [
    "runtime.identity",
    "runtime.capabilities",
    "runtime.surfaces",
    "chaseos.current_truth",
    "workflows.registry",
    "workflows.role_boundaries",
    "runtime.permission_envelope",
    "runtime.handoff.current",
    "runtime.audit.recent",
    "operator.briefing.latest",
    "chaseos.current_state",
    "chaseos.project_summary",
    "chaseos.operator_brief_latest",
    "chaseos.sic_workspace_summary",
    "chaseos.adapter_status",
    "chaseos.rnd_register_summary",
    "chaseos.runtime_surfaces_summary",
]

V1_TOOLS = [
    "proposal.submit",
    "proposal.validate",
    "proposal.diff_preview",
    "approval_request.create",
    "chaseos.generate_operator_brief_draft",
    "chaseos.create_research_digest_draft",
    "chaseos.prepare_discord_alert_draft",
    "chaseos.query_sic_evidence",
    "chaseos.validate_writeback_target",
]

V2_WORKFLOW_TOOLS = ["workflow.invoke_bounded"]

V1_PROMPTS = [
    "handoff.runtime_draft_frame",
    "chaseos.operator_today_prompt",
    "chaseos.research_ingest_prompt",
    "chaseos.adapter_handoff_prompt",
    "chaseos.risk_review_prompt",
]

DEFERRED_SURFACES = [
    "schedule.intent.read",
    "schedule.proposal.submit",
    "source.workspace.lookup",
    "operator.briefing.synthesis_frame",
    "proposal.drafting_frame",
]

EXCLUDED_SURFACES = [
    "writeback.commit_canonical",
    "bridge.shell",
    "bridge.git",
    "bridge.browser",
    "bridge.network",
]


def resolve_session_mode(
    runtime_id: str,
    requested_mode: str | None,
    config: MCPConfig,
) -> str:
    runtime = config.runtimes.get(runtime_id, config.runtimes["_unregistered"])
    mode = requested_mode or config.default_mode
    if mode not in config.allowed_modes:
        raise PermissionError(f"Unknown safety mode: {mode}")
    if mode not in runtime.allowed_modes:
        raise PermissionError(
            f"Runtime {runtime_id!r} is not permitted to use mode {mode!r}"
        )
    return mode


def resolve_permission_envelope(
    runtime_id: str,
    mode: str,
    config: MCPConfig,
) -> PermissionEnvelope:
    runtime = config.runtimes.get(runtime_id, config.runtimes["_unregistered"])
    tools: list[str] = []
    prompts: list[str] = []
    if mode in {"read_plus_proposal", "draft_execution"}:
        tools = list(V1_TOOLS)
        prompts = list(V1_PROMPTS)
    if mode == "draft_execution":
        tools.extend(V2_WORKFLOW_TOOLS)
    return PermissionEnvelope(
        runtime_id=runtime_id if runtime_id in config.runtimes else "_unregistered",
        trust_tier=runtime.trust_tier,
        mode=mode,
        allowed_modes=list(runtime.allowed_modes),
        resources=list(V1_RESOURCES),
        tools=tools,
        prompts=prompts,
        write_targets=[
            ".chaseos/mcp-proposals/",
            "07_LOGS/Agent-Activity/",
            "07_LOGS/Operator-Briefs/",
        ],
        denied_surfaces=DEFERRED_SURFACES + EXCLUDED_SURFACES,
    )


def check_surface_available(
    request: MCPRequest,
    envelope: PermissionEnvelope,
) -> MCPError | None:
    if request.surface_class == SurfaceClass.RESOURCE:
        available = envelope.resources
    elif request.surface_class == SurfaceClass.TOOL:
        available = envelope.tools
    else:
        available = envelope.prompts

    if request.surface_name in available:
        return None
    return domain_error(
        ERR_SURFACE_UNAVAILABLE,
        "Surface is not available in the resolved permission envelope.",
        surface_class=request.surface_class.value,
        surface_name=request.surface_name,
        mode=envelope.mode,
    )
