"""
runtime.chaser.models

Dataclasses for ChaserAgent session/tool/terminal/artifact records.

These are evidence/transcript objects. They are NOT canonical ChaseOS truth.
All free-text content carried here is treated as untrusted (Tier 4) until
separately verified — see 06_AGENTS/Session-Export-and-Artifacts-Architecture.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Trust tier applied to any output that originated from a tool, terminal, or
# external surface. Mirrors TerminalAdapter.UNTRUSTED_TERMINAL_TIER.
UNTRUSTED_TIER = "Tier 4"


def _as_str(value: Any) -> str:
    return "" if value is None else str(value)


@dataclass(frozen=True)
class SessionMessage:
    """A single transcript message."""

    role: str
    content: str
    timestamp: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "SessionMessage":
        return cls(
            role=_as_str(data.get("role")),
            content=_as_str(data.get("content")),
            timestamp=_as_str(data.get("timestamp")),
        )

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content, "timestamp": self.timestamp}


@dataclass(frozen=True)
class ToolRun:
    """A tool invocation record. Arguments/results are untrusted output."""

    tool: str
    args: dict = field(default_factory=dict)
    result_summary: str = ""
    trust_tier: str = UNTRUSTED_TIER
    audit_id: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ToolRun":
        args = data.get("args")
        return cls(
            tool=_as_str(data.get("tool")),
            args=dict(args) if isinstance(args, dict) else {},
            result_summary=_as_str(data.get("result_summary")),
            trust_tier=_as_str(data.get("trust_tier")) or UNTRUSTED_TIER,
            audit_id=_as_str(data.get("audit_id")),
        )

    def to_dict(self) -> dict:
        return {
            "tool": self.tool,
            "args": dict(self.args),
            "result_summary": self.result_summary,
            "trust_tier": self.trust_tier,
            "audit_id": self.audit_id,
        }


@dataclass(frozen=True)
class TerminalRun:
    """A governed terminal run record (see TerminalAdapter run records)."""

    run_id: str
    command: str
    cwd: str = ""
    classification: str = ""
    blocked: bool = False
    returncode: int | None = None
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""
    trust_tier: str = UNTRUSTED_TIER
    audit_id: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "TerminalRun":
        rc = data.get("returncode")
        return cls(
            run_id=_as_str(data.get("run_id")),
            command=_as_str(data.get("command")),
            cwd=_as_str(data.get("cwd")),
            classification=_as_str(data.get("classification")),
            blocked=bool(data.get("blocked", False)),
            returncode=int(rc) if isinstance(rc, (int, float)) else None,
            stdout_excerpt=_as_str(data.get("stdout_excerpt")),
            stderr_excerpt=_as_str(data.get("stderr_excerpt")),
            trust_tier=_as_str(data.get("trust_tier")) or UNTRUSTED_TIER,
            audit_id=_as_str(data.get("audit_id")),
        )

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "command": self.command,
            "cwd": self.cwd,
            "classification": self.classification,
            "blocked": self.blocked,
            "returncode": self.returncode,
            "stdout_excerpt": self.stdout_excerpt,
            "stderr_excerpt": self.stderr_excerpt,
            "trust_tier": self.trust_tier,
            "audit_id": self.audit_id,
        }


@dataclass(frozen=True)
class ArtifactRef:
    """A reference to a session artifact (file/link/image/log/export)."""

    artifact_id: str
    artifact_type: str
    title: str = ""
    path_or_uri: str = ""
    source: str = ""
    trust_tier: str = UNTRUSTED_TIER
    generated: bool = True
    created_at: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ArtifactRef":
        return cls(
            artifact_id=_as_str(data.get("artifact_id")),
            artifact_type=_as_str(data.get("artifact_type") or data.get("type")),
            title=_as_str(data.get("title") or data.get("name")),
            path_or_uri=_as_str(data.get("path_or_uri") or data.get("path") or data.get("uri")),
            source=_as_str(data.get("source")),
            trust_tier=_as_str(data.get("trust_tier")) or UNTRUSTED_TIER,
            generated=bool(data.get("generated", True)),
            created_at=_as_str(data.get("created_at")),
        )

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "title": self.title,
            "path_or_uri": self.path_or_uri,
            "source": self.source,
            "trust_tier": self.trust_tier,
            "generated": self.generated,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class SessionRecord:
    """A ChaserAgent session transcript + manifests.

    This is the unit of session export. It is evidence, not canonical truth.
    """

    session_id: str
    title: str = ""
    runtime: str = ""
    profile: str = ""
    model: str = ""
    provider: str = ""
    created_at: str = ""
    updated_at: str = ""
    pinned: bool = False
    messages: tuple[SessionMessage, ...] = ()
    tool_runs: tuple[ToolRun, ...] = ()
    terminal_runs: tuple[TerminalRun, ...] = ()
    artifacts: tuple[ArtifactRef, ...] = ()

    @classmethod
    def from_dict(cls, data: dict) -> "SessionRecord":
        if not isinstance(data, dict):
            raise ValueError("session record must be a JSON object")
        session_id = _as_str(data.get("session_id"))
        if not session_id:
            raise ValueError("session record is missing 'session_id'")
        return cls(
            session_id=session_id,
            title=_as_str(data.get("title")),
            runtime=_as_str(data.get("runtime")),
            profile=_as_str(data.get("profile")),
            model=_as_str(data.get("model")),
            provider=_as_str(data.get("provider")),
            created_at=_as_str(data.get("created_at")),
            updated_at=_as_str(data.get("updated_at")),
            pinned=bool(data.get("pinned", False)),
            messages=tuple(SessionMessage.from_dict(m) for m in data.get("messages", []) if isinstance(m, dict)),
            tool_runs=tuple(ToolRun.from_dict(t) for t in data.get("tool_runs", []) if isinstance(t, dict)),
            terminal_runs=tuple(
                TerminalRun.from_dict(t) for t in data.get("terminal_runs", []) if isinstance(t, dict)
            ),
            artifacts=tuple(ArtifactRef.from_dict(a) for a in data.get("artifacts", []) if isinstance(a, dict)),
        )

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "runtime": self.runtime,
            "profile": self.profile,
            "model": self.model,
            "provider": self.provider,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "pinned": self.pinned,
            "messages": [m.to_dict() for m in self.messages],
            "tool_runs": [t.to_dict() for t in self.tool_runs],
            "terminal_runs": [t.to_dict() for t in self.terminal_runs],
            "artifacts": [a.to_dict() for a in self.artifacts],
        }
