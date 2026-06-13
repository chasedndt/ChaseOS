"""Runtime profile schema for AgentHub."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


RUNTIME_PROFILE_STATUSES = {
    "draft",
    "registered",
    "shadow",
    "execution-capable",
    "suspended",
}


@dataclass
class RuntimeProfile:
    runtime_id: str
    provider: str
    execution_surface: str
    access_mode: str
    trust_tier: str
    status: str = "draft"
    authority: str = "bounded editor / proposer"
    allowed_task_families: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=lambda: [
        "secrets",
        "credentials",
        "unapproved_protected_file_edits",
        "unapproved_canonical_promotion",
        "destructive_delete",
    ])
    memory_surfaces: list[str] = field(default_factory=list)
    policy_refs: list[str] = field(default_factory=list)
    canonical_promotion_authority: bool = False

    def validate(self) -> None:
        if not self.runtime_id:
            raise ValueError("runtime_id is required")
        if not self.provider:
            raise ValueError("provider is required")
        if not self.execution_surface:
            raise ValueError("execution_surface is required")
        if self.status not in RUNTIME_PROFILE_STATUSES:
            raise ValueError(f"status must be one of {sorted(RUNTIME_PROFILE_STATUSES)}")
        if self.canonical_promotion_authority:
            raise ValueError("runtime profiles cannot grant canonical promotion authority")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
