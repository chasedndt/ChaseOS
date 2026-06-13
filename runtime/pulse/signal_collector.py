"""Signal collection contracts for ChaseOS Pulse.

The collector is declaration-driven in this scaffold. It does not browse the web,
scan broadly, or infer authority from external sources. External connector signals
must be explicitly enabled by the caller.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import CARD_AUDIENCES, EvidenceRef, now_utc


SIGNAL_SOURCE_TYPES = {
    "context_memory",
    "personal_map",
    "active_project",
    "now",
    "dashboard",
    "source_intelligence",
    "build_log",
    "agent_activity",
    "aor_workflow",
    "runtime_profile",
    "runtime_reflection",
    "feedback_history",
    "external_connector",
}

EXTERNAL_SOURCE_TYPES = {"external_connector"}


@dataclass
class PulseSignal:
    signal_id: str
    source_type: str
    summary: str
    source_path: str = ""
    audience_hint: str = "user"
    tags: list[str] = field(default_factory=list)
    evidence: list[EvidenceRef] = field(default_factory=list)
    priority: int = 0
    observed_at: str = field(default_factory=now_utc)

    def validate(self, *, external_sources_enabled: bool = False) -> None:
        if not self.signal_id:
            raise ValueError("signal_id is required")
        if self.source_type not in SIGNAL_SOURCE_TYPES:
            raise ValueError(f"source_type must be one of {sorted(SIGNAL_SOURCE_TYPES)}")
        if self.source_type in EXTERNAL_SOURCE_TYPES and not external_sources_enabled:
            raise ValueError("external connector signals require explicit enablement")
        if self.audience_hint not in CARD_AUDIENCES:
            raise ValueError(
                "audience_hint must be user, agent, shared, or shared_coordination"
            )
        if not self.summary:
            raise ValueError("summary is required")
        if not 0 <= self.priority <= 5:
            raise ValueError("priority must be between 0 and 5")
        for item in self.evidence:
            item.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate(external_sources_enabled=True)
        return asdict(self)


def signal_from_declaration(
    declaration: dict[str, Any],
    *,
    external_sources_enabled: bool = False,
) -> PulseSignal:
    evidence = [
        item if isinstance(item, EvidenceRef) else EvidenceRef(**item)
        for item in declaration.get("evidence", [])
    ]
    signal = PulseSignal(
        signal_id=str(declaration.get("signal_id") or ""),
        source_type=str(declaration.get("source_type") or ""),
        summary=str(declaration.get("summary") or ""),
        source_path=str(declaration.get("source_path") or ""),
        audience_hint=str(declaration.get("audience_hint") or "user"),
        tags=[str(item) for item in declaration.get("tags", [])],
        evidence=evidence,
        priority=int(declaration.get("priority", 0)),
        observed_at=str(declaration.get("observed_at") or now_utc()),
    )
    signal.validate(external_sources_enabled=external_sources_enabled)
    return signal


def collect_declared_signals(
    declarations: list[dict[str, Any]],
    *,
    external_sources_enabled: bool = False,
) -> list[PulseSignal]:
    return [
        signal_from_declaration(item, external_sources_enabled=external_sources_enabled)
        for item in declarations
    ]


def collect_file_presence_signals(vault_root: Path) -> list[PulseSignal]:
    """Return narrow presence signals for core Pulse inputs.

    This is intentionally not a content scanner. It only confirms whether the
    main local-first Pulse source surfaces exist.
    """
    candidates = [
        ("now", "00_HOME/Now.md", "Current Now.md state is available"),
        ("dashboard", "00_HOME/Dashboard.md", "Dashboard state is available"),
        ("context_memory", "runtime/memory/README.md", "Runtime memory substrate is available"),
        ("agent_activity", "07_LOGS/Agent-Activity", "Agent activity log lane is available"),
        ("build_log", "07_LOGS/Build-Logs", "Build log lane is available"),
    ]
    signals: list[PulseSignal] = []
    for index, (source_type, rel_path, summary) in enumerate(candidates, start=1):
        if (vault_root / rel_path).exists():
            signals.append(
                PulseSignal(
                    signal_id=f"file-presence-{index}",
                    source_type=source_type,
                    source_path=rel_path,
                    summary=summary,
                    priority=1,
                )
            )
    return signals
