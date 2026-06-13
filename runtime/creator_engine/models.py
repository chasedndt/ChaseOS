"""Creator Engine Pass 1 artifact models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import re
import uuid
from typing import Any


SCHEMA_VERSION = "creator_engine.v1"
OWNER_LAYER = "runtime.creator_engine"

CREATOR_JOB_STATUSES = (
    "created",
    "intake_ready",
    "transcript_ready",
    "context_ready",
    "draft_ready",
    "approval_ready",
    "approved",
    "complete",
    "blocked",
)

MVP_SOURCE_ADAPTERS = (
    "manual_file",
    "provided_transcript",
    "recordly_folder",
    "obs_folder",
)

BLOCKED_FUTURE_ACTIONS = (
    "direct_publish",
    "auto_upload",
    "openscreen_mcp",
    "recordly_fork_or_api_coupling",
    "canonical_memory_promotion",
    "external_delivery",
)


def utc_now() -> str:
    """Return a stable UTC timestamp for artifact records."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_id_part(value: str, default: str = "creator") -> str:
    lowered = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9_-]+", "-", lowered).strip("-_")
    return cleaned or default


def new_id(prefix: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{clean_id_part(prefix)}-{stamp}-{uuid.uuid4().hex[:8]}"


class DictModel:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SourceRecording(DictModel):
    recording_id: str
    adapter: str
    path: str
    media_kind: str
    file_size_bytes: int
    sha256: str
    created_at: str
    modified_at: str
    duration_seconds: float | None = None
    probe_status: str = "not_probed"
    trust_tier: str = "tier-3"
    adapter_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CreatorJob(DictModel):
    job_id: str
    source_adapter: str
    source_recording_id: str
    artifact_root: str
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION
    owner_layer: str = OWNER_LAYER
    status: str = "created"
    target_platforms: list[str] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    approval_state: dict[str, Any] = field(
        default_factory=lambda: {"requires_approval": False, "approval_ids": []}
    )
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


@dataclass
class TranscriptArtifact(DictModel):
    artifact_id: str
    job_id: str
    source_recording_id: str
    transcript_path: str
    created_at: str = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "transcript_artifact"
    language: str | None = None
    status: str = "provided_or_pending"
    word_count: int = 0
    segments: list[dict[str, Any]] = field(default_factory=list)
    transformation_chain: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ContextPack(DictModel):
    artifact_id: str
    job_id: str
    context_path: str
    created_at: str = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "context_pack"
    project_refs: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    trust_summary: dict[str, Any] = field(default_factory=dict)
    status: str = "draft"


@dataclass
class EditPlan(DictModel):
    artifact_id: str
    job_id: str
    plan_path: str
    created_at: str = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "edit_plan"
    target_formats: list[str] = field(default_factory=list)
    approval_required: bool = True
    status: str = "draft"
    blocked_actions: list[str] = field(default_factory=lambda: list(BLOCKED_FUTURE_ACTIONS))


@dataclass
class CaptionArtifact(DictModel):
    artifact_id: str
    job_id: str
    caption_path: str
    created_at: str = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "caption_artifact"
    format: str = "srt"
    status: str = "draft"
    line_count: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class SocialPack(DictModel):
    artifact_id: str
    job_id: str
    pack_path: str
    created_at: str = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "social_pack"
    target_platforms: list[str] = field(default_factory=list)
    posts: list[dict[str, Any]] = field(default_factory=list)
    approval_required: bool = True
    status: str = "draft"


@dataclass
class ContentMemoryCard(DictModel):
    artifact_id: str
    job_id: str
    card_path: str
    created_at: str = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION
    artifact_type: str = "content_memory_card"
    summary: str = ""
    source_refs: list[str] = field(default_factory=list)
    canonical_promotion_allowed: bool = False
    approval_required: bool = True
    status: str = "draft"
