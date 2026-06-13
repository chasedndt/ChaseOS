"""Lightweight models for the ChaseOS Browser Runtime Adapter spike."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse


BrowserRunStatus = Literal["succeeded", "blocked", "failed"]
BrowserActionStatus = Literal["succeeded", "blocked", "failed", "planned"]
BrowserRunMode = Literal["shadow", "read_only"]
SkillGenerationMode = Literal["draft_only", "disabled"]


def now_iso() -> str:
    """Return an aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str, fallback: str = "browser-runtime") -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in clean.split("-") if part) or fallback


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.hostname or ""


class BrowserRuntimeProvider(str, Enum):
    """Supported provider identifiers for the bounded spike."""

    SHADOW = "shadow"
    BROWSER_USE_CLI = "browser-use-cli"


@dataclass(frozen=True)
class BrowserRuntimeConfig:
    """Policy/configuration for one browser runtime invocation."""

    enabled: bool = False
    allowed_providers: list[str] = field(default_factory=lambda: [BrowserRuntimeProvider.SHADOW.value])
    allowed_domains: list[str] = field(default_factory=lambda: ["example.com", "localhost", "127.0.0.1"])
    forbidden_domains: list[str] = field(
        default_factory=lambda: [
            "accounts.google.com",
            "gmail.com",
            "mail.google.com",
            "bank",
            "paypal.com",
            "coinbase.com",
        ]
    )
    browser_profile_policy: str = "throwaway_only"
    allow_real_profile: bool = False
    allow_credentials: bool = False
    allow_shell_execution: bool = False
    allow_cookie_export: bool = False
    allow_public_tunnel: bool = False
    screenshot_retention: str = "log_artifact_only"
    artifact_retention: str = "log_artifact_only"
    skill_generation: SkillGenerationMode = "draft_only"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrowserRunRequest:
    """A bounded browser runtime request."""

    url: str
    task: str
    provider: BrowserRuntimeProvider = BrowserRuntimeProvider.SHADOW
    mode: BrowserRunMode = "shadow"
    run_id: str | None = None
    requested_by: str = "Codex"
    harmless_action: str | None = "read_state"
    allowed_domains: list[str] = field(default_factory=list)
    use_real_profile: bool = False
    allow_credentials: bool = False
    write_skill_draft: bool = True

    def effective_run_id(self) -> str:
        if self.run_id:
            return self.run_id
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        domain = slugify(domain_from_url(self.url), "local")
        return f"browser_runtime_{timestamp}_{domain}"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["provider"] = self.provider.value
        return payload


@dataclass(frozen=True)
class BrowserArtifact:
    """Artifact produced by a browser run."""

    artifact_type: str
    path: str
    description: str
    redacted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrowserActionRecord:
    """One action or observation in a browser run."""

    action_type: str
    target: str
    status: BrowserActionStatus
    timestamp: str = field(default_factory=now_iso)
    notes: str = ""
    blocked_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrowserRunResult:
    """Result object returned by a browser runtime adapter."""

    run_id: str
    status: BrowserRunStatus
    provider: BrowserRuntimeProvider
    mode: BrowserRunMode
    url: str
    task: str
    actions: list[BrowserActionRecord] = field(default_factory=list)
    artifacts: list[BrowserArtifact] = field(default_factory=list)
    browser_run_log_path: str | None = None
    agent_activity_log_path: str | None = None
    skill_candidate_path: str | None = None
    skill_draft_path: str | None = None
    site_activity_log_path: str | None = None
    error: str | None = None
    summary: str = ""
    started_at: str = field(default_factory=now_iso)
    ended_at: str | None = None
    security_flags: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["provider"] = self.provider.value
        payload["actions"] = [item.as_dict() for item in self.actions]
        payload["artifacts"] = [item.as_dict() for item in self.artifacts]
        return payload


@dataclass(frozen=True)
class SiteSkillDraft:
    """Draft-only site skill candidate generated from run evidence."""

    draft_id: str
    domain: str
    status: str
    run_id: str
    source_log_path: str
    created_at: str = field(default_factory=now_iso)
    observed_urls: list[str] = field(default_factory=list)
    safe_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    selectors: list[str] = field(default_factory=list)
    workflow_notes: list[str] = field(default_factory=list)
    evidence_links: list[str] = field(default_factory=list)
    review_required: bool = True
    activation_allowed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrowserSkillCandidate:
    """Untrusted browser skill candidate generated from run evidence."""

    candidate_id: str
    skill_id: str
    domain: str
    intent: str
    status: str
    approval_status: str
    risk_level: str
    source_run_id: str
    source_run_log_path: str
    created_at: str = field(default_factory=now_iso)
    allowed_domains: list[str] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)
    proposed_steps: list[dict[str, Any]] = field(default_factory=list)
    proposed_selectors: dict[str, Any] = field(default_factory=dict)
    proposed_wait_conditions: list[dict[str, Any]] = field(default_factory=list)
    proposed_verification: dict[str, Any] = field(default_factory=dict)
    learned_patterns: list[str] = field(default_factory=list)
    rejected_patterns: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    review_required: bool = True
    activation_allowed: bool = False
    validator_ok: bool | None = None
    validator_errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def path_as_posix(path: Path | str) -> str:
    return Path(path).as_posix()
