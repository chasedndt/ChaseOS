"""Shared data models for Product-Facing Workflow Packs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


WorkflowPackCategory = Literal[
    "creative",
    "automation_audit",
    "research_intelligence",
    "agent_governance",
]

WorkflowRunStatus = Literal[
    "created",
    "intake_ready",
    "sources_attached",
    "plan_drafted",
    "approval_required",
    "approved",
    "running",
    "artifact_ready",
    "review_required",
    "completed",
    "archived",
    "failed",
    "cancelled",
]

ArtifactType = Literal[
    "brief",
    "report",
    "asset",
    "copy_pack",
    "scorecard",
    "manifest",
    "policy",
    "proof_card",
    "screenshot",
    "html_mockup",
    "markdown",
    "json",
    "yaml",
]

ReviewStatus = Literal[
    "not_required",
    "pending_review",
    "approved",
    "rejected",
    "needs_revision",
]

ApprovalActionType = Literal[
    "write_file",
    "send_email",
    "publish_content",
    "browser_action",
    "runtime_execution",
    "agent_policy_change",
    "graph_promotion",
    "external_api_call",
]

ApprovalStatus = Literal["pending", "approved", "rejected", "expired"]

ProofCardStatus = Literal[
    "draft",
    "review_required",
    "approved",
    "public_safe",
    "internal_only",
    "archived",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RiskFlag:
    id: str
    severity: str
    summary: str
    blocked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactReference:
    id: str
    local_path: str
    title: str
    artifact_type: ArtifactType
    review_status: ReviewStatus

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceReference:
    id: str
    source_type: str
    captured_at: str
    provenance_status: str = "candidate"
    sensitivity_status: str = "unknown"
    uri: str = ""
    local_path: str = ""
    title: str = ""
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeReference:
    id: str
    runtime: str
    mode: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovalReference:
    id: str
    action_type: ApprovalActionType
    status: ApprovalStatus
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowPack:
    id: str
    name: str
    description: str
    version: str
    category: WorkflowPackCategory
    user_facing: bool
    enabled: bool
    input_schema_ref: str
    output_schema_ref: str
    default_approval_policy_id: str
    supported_runtimes: list[str]
    required_capabilities: list[str]
    artifact_types: list[ArtifactType]
    proof_card_template_id: str
    created_at: str
    updated_at: str
    examples: list[str] = field(default_factory=list)
    safety_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowArtifact:
    id: str
    run_id: str
    artifact_type: ArtifactType
    title: str
    local_path: str
    mime_type: str
    created_at: str
    created_by: str
    review_status: ReviewStatus
    public_share_safe: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApprovalGate:
    id: str
    run_id: str
    action_type: ApprovalActionType
    status: ApprovalStatus
    requested_by: str
    requested_at: str
    reason: str
    preview_artifact_refs: list[str]
    risk_flags: list[RiskFlag]
    approved_by: str = ""
    approved_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["risk_flags"] = [flag.to_dict() for flag in self.risk_flags]
        return data


@dataclass(frozen=True)
class WorkflowRun:
    id: str
    pack_id: str
    title: str
    status: WorkflowRunStatus
    input: dict[str, Any]
    source_refs: list[SourceReference]
    runtime_refs: list[RuntimeReference]
    approval_refs: list[ApprovalReference]
    artifact_refs: list[ArtifactReference]
    risk_flags: list[RiskFlag]
    created_at: str
    updated_at: str
    proof_card_id: str = ""
    audit_log_ref: str = ""
    provider_mode: str = "demo_manual"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_refs"] = [item.to_dict() for item in self.source_refs]
        data["runtime_refs"] = [item.to_dict() for item in self.runtime_refs]
        data["approval_refs"] = [item.to_dict() for item in self.approval_refs]
        data["artifact_refs"] = [item.to_dict() for item in self.artifact_refs]
        data["risk_flags"] = [item.to_dict() for item in self.risk_flags]
        return data


@dataclass(frozen=True)
class ProofCard:
    id: str
    run_id: str
    pack_id: str
    title: str
    created_at: str
    status: ProofCardStatus
    user_goal: str
    input_summary: str
    workflow_summary: str
    outputs_summary: str
    artifact_refs: list[ArtifactReference]
    source_refs: list[SourceReference]
    runtime_trace: dict[str, Any]
    approval_summary: dict[str, Any]
    risk_summary: dict[str, Any]
    public_share_mode: str
    metrics: dict[str, Any] = field(default_factory=dict)
    before_state: dict[str, Any] = field(default_factory=dict)
    after_state: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["artifact_refs"] = [item.to_dict() for item in self.artifact_refs]
        data["source_refs"] = [item.to_dict() for item in self.source_refs]
        return data
