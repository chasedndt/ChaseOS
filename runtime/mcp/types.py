"""Shared datatypes for the internal ChaseOS Runtime MCP server."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class SafetyMode(str, Enum):
    READ_ONLY = "read_only"
    READ_PLUS_PROPOSAL = "read_plus_proposal"
    DRAFT_EXECUTION = "draft_execution"


class SurfaceClass(str, Enum):
    RESOURCE = "resource"
    TOOL = "tool"
    PROMPT = "prompt"


# Maps config-level string trust tier labels to integer tiers for audit records.
# Frozen doc: trust_tier in audit records is an integer (1, 2, or 3).
TRUST_TIER_INT_MAP: dict[str, int] = {
    "internal_runtime": 1,
    "operator_runtime": 2,
    "external_orchestrator": 3,
    "unknown": 3,
}


@dataclass(frozen=True)
class MCPError:
    code: str
    message: str
    category: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MCPRequest:
    request_id: str
    surface_class: SurfaceClass
    surface_name: str
    params: dict[str, Any]
    runtime_id: str
    requested_mode: str | None = None


@dataclass
class PermissionEnvelope:
    runtime_id: str
    trust_tier: str
    mode: str
    allowed_modes: list[str]
    resources: list[str]
    tools: list[str]
    prompts: list[str]
    write_targets: list[str]
    denied_surfaces: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HandlerResult:
    ok: bool
    payload: dict[str, Any] | None = None
    error: MCPError | None = None
    audit_metadata: dict[str, Any] = field(default_factory=dict)
    files_read: list[str] = field(default_factory=list)
    files_written: list[str] = field(default_factory=list)
    rollback_proposal_id: str | None = None


@dataclass(frozen=True)
class MCPResponse:
    request_id: str
    ok: bool
    result: dict[str, Any] | None = None
    error: MCPError | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"request_id": self.request_id, "ok": self.ok}
        if self.result is not None:
            data["result"] = self.result
        if self.error is not None:
            data["error"] = self.error.to_dict()
        return data


@dataclass(frozen=True)
class RuntimeTrustConfig:
    runtime_id: str
    trust_tier: str
    allowed_modes: list[str]


@dataclass(frozen=True)
class MCPConfig:
    vault_root: Path
    server_identity: str
    version: str
    transport: str
    default_mode: str
    allowed_modes: list[str]
    fail_closed_surfaces: list[str]
    fail_open_surface_classes: list[str]
    fail_open_surfaces: list[str]
    staging_dir: Path
    audit_dir: Path
    operator_briefs_dir: Path
    runtimes: dict[str, RuntimeTrustConfig]


@dataclass(frozen=True)
class ProposalArtifact:
    """Frozen V1 proposal artifact schema matching ChaseOS-MCP-Proposal-Staging.md."""

    schema_version: str
    proposal_id: str
    staged_at: str
    runtime_id: str
    safety_mode_at_staging: str
    change_type: str  # "create" | "update" | "delete"
    target_file: str
    description: str
    proposed_content: str | None
    current_sha256: str | None
    proposed_sha256: str | None
    governance_flags: dict[str, Any]
    status: str
    status_history: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuditRecord:
    """Frozen V1 audit record schema matching ChaseOS-MCP-Audit-Policy.md."""

    schema_version: str
    request_id: str
    recorded_at: str
    surface_id: str
    surface_class: str
    runtime_id: str
    trust_tier: int
    safety_mode: str
    outcome: str  # "success" | "error" | "partial"
    outcome_detail: str | None
    files_read: list[str]
    files_written: list[str]
    error_code: str | None
    error_message: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
