"""Product-facing Workflow Packs foundation for ChaseOS.

This package is deliberately local/demo-first. It defines shared WorkflowPack,
WorkflowRun, Artifact, ApprovalGate, and ProofCard primitives without granting
external execution authority.
"""

from .approval_resume_contract import build_approval_resume_contract
from .approval_consumption_dry_run import build_approval_consumption_dry_run
from .approval_marker_reservation import build_approval_marker_reservation
from .approval_review_artifact import build_approval_review_artifact
from .approved_local_resume_executor import build_approved_local_resume_executor
from .automation_audit import create_automation_audit_run
from .agent_governance import create_agent_governance_run
from .creative_studio import create_creative_studio_run
from .demo_provider import create_demo_workflow_run
from .panel import build_workflow_packs_panel
from .research_intelligence import create_research_intelligence_run
from .registry import get_workflow_pack, list_workflow_packs
from .store import WorkflowPackStore

__all__ = [
    "WorkflowPackStore",
    "build_approved_local_resume_executor",
    "build_approval_consumption_dry_run",
    "build_approval_marker_reservation",
    "build_approval_resume_contract",
    "build_approval_review_artifact",
    "build_workflow_packs_panel",
    "create_agent_governance_run",
    "create_automation_audit_run",
    "create_creative_studio_run",
    "create_demo_workflow_run",
    "create_research_intelligence_run",
    "get_workflow_pack",
    "list_workflow_packs",
]
