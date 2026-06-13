"""Signal-driven local ChaseOS Pulse deck generation.

This module is still local and log-only. It reads narrow repo evidence from
existing Pulse proof surfaces, recent build/activity logs, schedule manifests,
completion status, hardening status, and current deck inventory. It does not
scan the web, call providers/connectors, dispatch runtimes, activate schedules,
approve memory, write Agent Bus tasks, or mutate canonical state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import (
    EvidenceRef,
    PulseCard,
    PulseCardScope,
    PulseDeck,
    RecommendedAction,
    RelatedNodeRef,
    SourceLinkRef,
    ThumbnailRef,
    now_utc,
)
from runtime.pulse.completion_status import build_pulse_completion_status
from runtime.pulse.deck_schema import PulseDeckArtifact
from runtime.pulse.multi_audience_decks import build_pulse_deck_inventory
from runtime.pulse.post_completion_hardening import (
    build_pulse_post_completion_hardening_report,
)
from runtime.pulse.signal_collector import PulseSignal
from runtime.pulse.writeback import AUDIENCE_DIRS, PULSE_DECK_ROOT, write_deck_artifacts


SIGNAL_DRIVEN_AUDIENCES = ("user", "agent", "shared_coordination")
RECENT_LOG_LIMIT = 6
SCHEDULE_MANIFESTS = (
    "runtime/schedules/manifests/chaseos_pulse_daily.yaml",
    "runtime/schedules/manifests/hermes_runtime_pulse.yaml",
    "runtime/schedules/manifests/openflow_runtime_pulse.yaml",
)


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _relative(vault: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(vault).as_posix()
    except ValueError:
        return str(path.resolve())


def _latest_files(vault: Path, relative_dir: str, *, limit: int = RECENT_LOG_LIMIT) -> tuple[Path, ...]:
    directory = vault / relative_dir
    if not directory.exists() or not directory.is_dir():
        return ()
    files = [item for item in directory.iterdir() if item.is_file()]
    return tuple(sorted(files, key=lambda item: (item.stat().st_mtime, item.name), reverse=True)[:limit])


def _latest_matching_file(vault: Path, relative_dir: str, tokens: tuple[str, ...]) -> Path | None:
    directory = vault / relative_dir
    if not directory.exists() or not directory.is_dir():
        return None
    lowered = tuple(token.lower() for token in tokens)
    candidates = [
        item
        for item in directory.iterdir()
        if item.is_file() and all(token in item.name.lower() for token in lowered)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item.stat().st_mtime, item.name))


def _read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _has_all_tokens(text: str, tokens: tuple[str, ...]) -> bool:
    return all(token in text for token in tokens)


def _source_link(label: str, path: str, source_type: str = "local") -> SourceLinkRef:
    return SourceLinkRef(label=label, path=path, source_type=source_type)


def _evidence(path: str, source_type: str, summary: str, *, trust_label: str = "repo-observed") -> EvidenceRef:
    return EvidenceRef(
        source_path=path,
        source_type=source_type,
        summary=summary,
        trust_label=trust_label,
    )


def _node(node_id: str, node_type: str, label: str, relation: str) -> RelatedNodeRef:
    return RelatedNodeRef(
        node_id=node_id,
        node_type=node_type,
        label=label,
        relation=relation,
    )


def _action(
    action_id: str,
    label: str,
    action_type: str,
    *,
    approval: bool = True,
    target_ref: str | None = None,
) -> RecommendedAction:
    return RecommendedAction(
        action_id=action_id,
        label=label,
        action_type=action_type,
        target_ref=target_ref,
        requires_operator_approval=approval,
    )


def _thumb(label: str) -> ThumbnailRef:
    return ThumbnailRef(
        path="05_TEMPLATES/Pulse-Card-Template.md",
        alt=f"Local placeholder thumbnail for {label}",
        source_type="local_template",
    )


@dataclass(frozen=True)
class PulseLocalSignalSnapshot:
    generated_at: str
    latest_build_logs: tuple[str, ...]
    latest_agent_activity_logs: tuple[str, ...]
    latest_pulse_build_log: str | None
    latest_pulse_agent_activity_log: str | None
    latest_hermes_activity_log: str | None
    schedule_manifests: tuple[str, ...]
    inactive_schedule_manifests: tuple[str, ...]
    deck_inventory: tuple[dict[str, Any], ...]
    completion_status: str
    pulse_feature_done: bool
    hardening_status: str
    hardening_required_passed: int
    hardening_required_total: int
    canonical_writeback_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    schedule_activation_allowed: bool = False
    agent_bus_task_write_allowed: bool = False
    rd_workbook_update_allowed: bool = False

    def validate(self) -> None:
        if not self.generated_at:
            raise ValueError("generated_at is required")
        if self.canonical_writeback_allowed:
            raise ValueError("signal-driven Pulse snapshot cannot allow canonical writeback")
        if self.provider_or_connector_call_allowed:
            raise ValueError("signal-driven Pulse snapshot cannot call providers/connectors")
        if self.runtime_dispatch_allowed:
            raise ValueError("signal-driven Pulse snapshot cannot dispatch runtimes")
        if self.schedule_activation_allowed:
            raise ValueError("signal-driven Pulse snapshot cannot activate schedules")
        if self.agent_bus_task_write_allowed:
            raise ValueError("signal-driven Pulse snapshot cannot write Agent Bus tasks")
        if self.rd_workbook_update_allowed:
            raise ValueError("signal-driven Pulse snapshot cannot update the R&D workbook")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["latest_build_logs"] = list(self.latest_build_logs)
        payload["latest_agent_activity_logs"] = list(self.latest_agent_activity_logs)
        payload["schedule_manifests"] = list(self.schedule_manifests)
        payload["inactive_schedule_manifests"] = list(self.inactive_schedule_manifests)
        payload["deck_inventory"] = list(self.deck_inventory)
        return payload


@dataclass(frozen=True)
class PulseSignalDrivenDeckResult:
    generated_at: str
    snapshot: PulseLocalSignalSnapshot
    signals: tuple[PulseSignal, ...]
    decks: tuple[PulseDeck, ...]
    write_requested: bool
    write_executed: bool
    artifacts: tuple[PulseDeckArtifact, ...] = ()
    writes: tuple[str, ...] = ()
    read_only: bool = True
    log_only: bool = True
    canonical_writeback_allowed: bool = False
    memory_approval_allowed: bool = False
    provider_or_connector_call_allowed: bool = False
    runtime_dispatch_allowed: bool = False
    schedule_activation_allowed: bool = False
    agent_bus_task_write_allowed: bool = False
    rd_workbook_update_allowed: bool = False
    second_datastore_created: bool = False
    allowed_write_root: str = "07_LOGS/Pulse-Decks/"
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "Signal-driven decks read local repo evidence only.",
            "Dry-run by default; --write only creates markdown/json artifacts under 07_LOGS/Pulse-Decks/.",
            "No provider calls, connector calls, runtime dispatch, schedule activation, memory approval, or canonical writeback are performed.",
        )
    )

    @property
    def deck_count(self) -> int:
        return len(self.decks)

    @property
    def signal_count(self) -> int:
        return len(self.signals)

    def validate(self) -> None:
        self.snapshot.validate()
        for signal in self.signals:
            signal.validate(external_sources_enabled=False)
        if tuple(deck.audience for deck in self.decks) != SIGNAL_DRIVEN_AUDIENCES:
            raise ValueError("signal-driven Pulse decks must include user, agent, and shared_coordination decks")
        for deck in self.decks:
            deck.validate()
        for artifact in self.artifacts:
            artifact.validate()
        if self.write_executed and not self.write_requested:
            raise ValueError("write_executed requires write_requested")
        if self.write_executed and self.read_only:
            raise ValueError("write_executed cannot be read_only")
        if self.write_executed and not self.writes:
            raise ValueError("write execution must report written paths")
        if not self.log_only:
            raise ValueError("signal-driven Pulse decks must remain log-only")
        if self.canonical_writeback_allowed:
            raise ValueError("canonical writeback cannot be allowed")
        if self.memory_approval_allowed:
            raise ValueError("memory approval cannot be allowed")
        if self.provider_or_connector_call_allowed:
            raise ValueError("provider/connector calls cannot be allowed")
        if self.runtime_dispatch_allowed:
            raise ValueError("runtime dispatch cannot be allowed")
        if self.schedule_activation_allowed:
            raise ValueError("schedule activation cannot be allowed")
        if self.agent_bus_task_write_allowed:
            raise ValueError("Agent Bus task writes cannot be allowed")
        if self.rd_workbook_update_allowed:
            raise ValueError("R&D workbook update cannot be allowed")
        if self.second_datastore_created:
            raise ValueError("signal-driven Pulse decks cannot create a second datastore")
        for written in self.writes:
            if not written.replace("\\", "/").startswith(self.allowed_write_root):
                raise ValueError("signal-driven Pulse writes must stay under 07_LOGS/Pulse-Decks/")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "snapshot": self.snapshot.to_dict(),
            "signal_count": self.signal_count,
            "signals": [signal.to_dict() for signal in self.signals],
            "deck_count": self.deck_count,
            "decks": [deck.to_dict() for deck in self.decks],
            "write_requested": self.write_requested,
            "write_executed": self.write_executed,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "writes": list(self.writes),
            "read_only": self.read_only,
            "log_only": self.log_only,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "memory_approval_allowed": self.memory_approval_allowed,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "runtime_dispatch_allowed": self.runtime_dispatch_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "agent_bus_task_write_allowed": self.agent_bus_task_write_allowed,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "second_datastore_created": self.second_datastore_created,
            "allowed_write_root": self.allowed_write_root,
            "notes": list(self.notes),
        }


def build_pulse_local_signal_snapshot(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> PulseLocalSignalSnapshot:
    """Build a narrow local Pulse evidence snapshot without writing."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    latest_build_logs = tuple(
        path for path in (_relative(vault, item) for item in _latest_files(vault, "07_LOGS/Build-Logs"))
        if path is not None
    )
    latest_agent_logs = tuple(
        path for path in (_relative(vault, item) for item in _latest_files(vault, "07_LOGS/Agent-Activity"))
        if path is not None
    )
    latest_pulse_build = _relative(
        vault,
        _latest_matching_file(vault, "07_LOGS/Build-Logs", ("pulse",)),
    )
    latest_pulse_agent = _relative(
        vault,
        _latest_matching_file(vault, "07_LOGS/Agent-Activity", ("pulse",)),
    )
    latest_hermes_activity = _relative(
        vault,
        _latest_matching_file(vault, "07_LOGS/Agent-Activity", ("hermes",)),
    )

    present_manifests: list[str] = []
    inactive_manifests: list[str] = []
    for manifest in SCHEDULE_MANIFESTS:
        path = vault / manifest
        if not path.exists():
            continue
        present_manifests.append(manifest)
        text = _read_text(path)
        if _has_all_tokens(
            text,
            (
                "owner: chaseos",
                "enabled: false",
                "activation_state: planned",
                "external_runtime_owner: false",
            ),
        ):
            inactive_manifests.append(manifest)

    completion = build_pulse_completion_status(vault)
    hardening = build_pulse_post_completion_hardening_report(vault, generated_at=generated)
    inventory = tuple(item.to_dict() for item in build_pulse_deck_inventory(vault))
    snapshot = PulseLocalSignalSnapshot(
        generated_at=generated,
        latest_build_logs=latest_build_logs,
        latest_agent_activity_logs=latest_agent_logs,
        latest_pulse_build_log=latest_pulse_build,
        latest_pulse_agent_activity_log=latest_pulse_agent,
        latest_hermes_activity_log=latest_hermes_activity,
        schedule_manifests=tuple(present_manifests),
        inactive_schedule_manifests=tuple(inactive_manifests),
        deck_inventory=inventory,
        completion_status=completion.overall_status,
        pulse_feature_done=bool(completion.feature_done),
        hardening_status=hardening.hardening_status,
        hardening_required_passed=hardening.passed_required_check_count,
        hardening_required_total=hardening.required_check_count,
    )
    snapshot.validate()
    return snapshot


def collect_signal_driven_pulse_signals(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
) -> tuple[PulseSignal, ...]:
    """Collect local signals from the current Pulse proof surface."""

    snapshot = build_pulse_local_signal_snapshot(vault_root, generated_at=generated_at)
    signals = [
        PulseSignal(
            signal_id="pulse-local-completion-state",
            source_type="build_log",
            source_path=snapshot.latest_pulse_build_log or "07_LOGS/Build-Logs/",
            summary=(
                f"Pulse completion status is {snapshot.completion_status}; "
                f"feature_done={snapshot.pulse_feature_done}."
            ),
            audience_hint="user",
            tags=["pulse_product_grade_progress"],
            evidence=[
                _evidence(
                    snapshot.latest_pulse_build_log or "07_LOGS/Build-Logs/",
                    "build_log",
                    "Latest local Pulse build evidence is available.",
                )
            ],
            priority=5,
            observed_at=snapshot.generated_at,
        ),
        PulseSignal(
            signal_id="pulse-hardening-boundary-state",
            source_type="runtime_reflection",
            source_path="runtime/pulse/post_completion_hardening.py",
            summary=(
                f"Pulse hardening status is {snapshot.hardening_status}; "
                f"{snapshot.hardening_required_passed}/{snapshot.hardening_required_total} required checks pass."
            ),
            audience_hint="agent",
            tags=["pulse_hardening"],
            evidence=[
                _evidence(
                    "runtime/pulse/post_completion_hardening.py",
                    "runtime_code",
                    "Post-completion hardening is read-only and boundary-focused.",
                )
            ],
            priority=5,
            observed_at=snapshot.generated_at,
        ),
        PulseSignal(
            signal_id="pulse-parallel-runtime-activity",
            source_type="agent_activity",
            source_path=snapshot.latest_hermes_activity_log or "07_LOGS/Agent-Activity/",
            summary="Recent agent activity logs show parallel runtime work that needs coordinated Pulse handoff.",
            audience_hint="shared_coordination",
            tags=["parallel_runtime_coordination"],
            evidence=[
                _evidence(
                    snapshot.latest_hermes_activity_log or "07_LOGS/Agent-Activity/",
                    "agent_activity",
                    "Latest Hermes or runtime activity is available for coordination.",
                ),
                _evidence(
                    snapshot.latest_pulse_agent_activity_log or "07_LOGS/Agent-Activity/",
                    "agent_activity",
                    "Latest Pulse-related activity is available for coordination.",
                ),
            ],
            priority=4,
            observed_at=snapshot.generated_at,
        ),
        PulseSignal(
            signal_id="pulse-native-schedule-inactive-state",
            source_type="aor_workflow",
            source_path="runtime/schedules/manifests/",
            summary=(
                f"{len(snapshot.inactive_schedule_manifests)}/{len(snapshot.schedule_manifests)} "
                "Pulse schedule manifests are present and still planned/inactive."
            ),
            audience_hint="user",
            tags=["native_schedule_boundary"],
            evidence=[
                _evidence(
                    "runtime/schedules/manifests/chaseos_pulse_daily.yaml",
                    "schedule_manifest",
                    "ChaseOS owns schedule intent; live activation remains separate.",
                )
            ],
            priority=4,
            observed_at=snapshot.generated_at,
        ),
        PulseSignal(
            signal_id="pulse-deck-artifact-inventory",
            source_type="feedback_history",
            source_path="07_LOGS/Pulse-Decks/",
            summary="Latest local user, agent, and shared Pulse deck artifacts are inventoried for review.",
            audience_hint="shared_coordination",
            tags=["deck_artifact_inventory"],
            evidence=[
                _evidence(
                    "07_LOGS/Pulse-Decks/",
                    "pulse_deck_archive",
                    "Deck inventory reads artifacts without writing or approving anything.",
                )
            ],
            priority=3,
            observed_at=snapshot.generated_at,
        ),
        PulseSignal(
            signal_id="pulse-governed-writeback-state",
            source_type="feedback_history",
            source_path="runtime/pulse/writeback.py",
            summary="Pulse deck writes remain log-only and do not mutate Now.md, Project-OS, governance docs, or 02_KNOWLEDGE.",
            audience_hint="agent",
            tags=["governed_writeback_boundary"],
            evidence=[
                _evidence(
                    "runtime/pulse/writeback.py",
                    "runtime_code",
                    "Deck artifacts are constrained to 07_LOGS/Pulse-Decks/.",
                )
            ],
            priority=4,
            observed_at=snapshot.generated_at,
        ),
    ]
    for signal in signals:
        signal.validate(external_sources_enabled=False)
    return tuple(signals)


def _card(
    *,
    deck_id: str,
    index: int,
    audience: str,
    card_class: str,
    title: str,
    summary: str,
    why_it_matters: str,
    evidence: list[EvidenceRef],
    source_links: list[SourceLinkRef],
    related_nodes: list[RelatedNodeRef],
    recommended_actions: list[RecommendedAction],
    generated_at: str,
    urgency: int,
    confidence: float,
    scope: PulseCardScope | None = None,
) -> PulseCard:
    return PulseCard(
        card_id=f"{deck_id}-{index:02d}",
        deck_id=deck_id,
        audience=audience,
        card_class=card_class,
        title=title,
        summary=summary,
        why_it_matters=why_it_matters,
        generated_at=generated_at,
        created_at=generated_at,
        scope=scope or PulseCardScope(user_id="chase"),
        evidence=evidence,
        source_links=source_links,
        related_nodes=related_nodes,
        thumbnails=[_thumb(card_class)],
        recommended_actions=recommended_actions,
        urgency=urgency,
        confidence=confidence,
        promotion_status="not_promoted",
        writeback_status="card_generated",
    )


def _build_user_deck(snapshot: PulseLocalSignalSnapshot, signals: tuple[PulseSignal, ...]) -> PulseDeck:
    deck_id = f"pulse-user-{snapshot.generated_at[:10]}-signal"
    cards = [
        _card(
            deck_id=deck_id,
            index=1,
            audience="user",
            card_class="Project Momentum",
            title="Pulse has moved from fixed proof decks to local signal decks",
            summary=(
                f"Pulse status is {snapshot.completion_status}, and the next product-grade step is "
                "using current repo evidence to generate richer cards without external runtimes."
            ),
            why_it_matters="This turns Pulse from a static scaffold into a repeatable local intelligence surface while preserving governance.",
            evidence=[signals[0].evidence[0]],
            source_links=[_source_link("Latest Pulse build log", snapshot.latest_pulse_build_log or "07_LOGS/Build-Logs/")],
            related_nodes=[
                _node("chaseos_pulse", "feature", "ChaseOS Pulse", "primary_feature"),
                _node("pulse_deck_generator", "runtime_module", "Pulse deck generator", "enriched_by"),
            ],
            recommended_actions=[
                _action("review-signal-deck", "Review the signal-driven Pulse deck output", "review", approval=False, target_ref="07_LOGS/Pulse-Decks/users/")
            ],
            generated_at=snapshot.generated_at,
            urgency=4,
            confidence=0.86,
        ),
        _card(
            deck_id=deck_id,
            index=2,
            audience="user",
            card_class="Schedule Catch-Up",
            title="Native Pulse schedules remain ChaseOS-owned and inactive",
            summary=(
                f"{len(snapshot.inactive_schedule_manifests)} inactive Pulse schedule manifests are present; "
                "no live schedule runner is enabled by this deck pass."
            ),
            why_it_matters="The product can prove schedule intent without turning OpenClaw, cron, or Task Scheduler into the owner.",
            evidence=[
                _evidence("runtime/schedules/manifests/chaseos_pulse_daily.yaml", "schedule_manifest", "Daily Pulse schedule manifest remains planned/inactive.")
            ],
            source_links=[_source_link("Pulse schedule manifests", "runtime/schedules/manifests/")],
            related_nodes=[
                _node("native_schedule_engine", "runtime_system", "Native Schedule Engine", "owns_intent"),
                _node("openclaw", "runtime_adapter", "OpenClaw", "executor_only"),
            ],
            recommended_actions=[
                _action("defer-live-schedule", "Keep live scheduler activation for a separate approval pass", "skip", approval=False)
            ],
            generated_at=snapshot.generated_at,
            urgency=3,
            confidence=0.82,
        ),
        _card(
            deck_id=deck_id,
            index=3,
            audience="user",
            card_class="Decision Needed",
            title="Product-grade Pulse still needs approval UX and real-runtime closure",
            summary="The local Pulse lane is strong, but full product-grade status still needs approval UI, runtime brain dashboard, and live schedule runner approval.",
            why_it_matters="This keeps the feature status honest while multiple runtimes continue building around the Agent Bus.",
            evidence=[
                _evidence("06_AGENTS/ChaseOS-Pulse-Completion-Tracker.md", "tracker", "Pulse tracker separates completed local lane from future product surfaces.")
            ],
            source_links=[_source_link("Pulse completion tracker", "06_AGENTS/ChaseOS-Pulse-Completion-Tracker.md")],
            related_nodes=[
                _node("pulse_approval_queue", "planned_surface", "Pulse approval queue", "remaining_work"),
                _node("runtime_brain_dashboard", "planned_surface", "Runtime Brain dashboard", "remaining_work"),
            ],
            recommended_actions=[
                _action("queue-product-grade-passes", "Continue the six-pass product-grade sequence", "create_task", approval=False)
            ],
            generated_at=snapshot.generated_at,
            urgency=4,
            confidence=0.78,
        ),
    ]
    deck = PulseDeck(
        deck_id=deck_id,
        audience="user",
        generated_at=snapshot.generated_at,
        cards=cards,
        source_summary=["signal_driven_local_snapshot", *sorted({signal.source_type for signal in signals})],
        schedule_ref="runtime/schedules/manifests/chaseos_pulse_daily.yaml",
    )
    deck.validate()
    return deck


def _build_agent_deck(snapshot: PulseLocalSignalSnapshot, signals: tuple[PulseSignal, ...]) -> PulseDeck:
    deck_id = f"pulse-agent-{snapshot.generated_at[:10]}-signal"
    cards = [
        _card(
            deck_id=deck_id,
            index=1,
            audience="agent",
            card_class="Runtime Reflection",
            title="Runtime agents should consume local Pulse evidence before adding new surfaces",
            summary=(
                f"Hardening is {snapshot.hardening_status} with "
                f"{snapshot.hardening_required_passed}/{snapshot.hardening_required_total} required checks passing."
            ),
            why_it_matters="This gives Hermes, Codex, and OpenClaw-style runtimes a current repo-truth baseline without live dispatch.",
            evidence=[signals[1].evidence[0]],
            source_links=[_source_link("Post-completion hardening module", "runtime/pulse/post_completion_hardening.py")],
            related_nodes=[
                _node("agenthub", "runtime_system", "AgentHub", "coordination_context"),
                _node("runtime_brain", "runtime_system", "Runtime Brain", "consumes_signal"),
            ],
            recommended_actions=[
                _action("read-hardening-before-patch", "Read hardening status before proposing authority expansion", "review", approval=False)
            ],
            generated_at=snapshot.generated_at,
            urgency=3,
            confidence=0.86,
            scope=PulseCardScope(agent_id="codex", project_ids=["ChaseOS"]),
        ),
        _card(
            deck_id=deck_id,
            index=2,
            audience="agent",
            card_class="Workflow Improvement",
            title="Use signal decks as the handoff artifact for parallel Pulse work",
            summary="The deck inventory and latest activity logs can now be summarized into cards instead of relying on chat memory.",
            why_it_matters="Parallel runtime work needs a repo-native handoff object that does not write bus tasks or memory automatically.",
            evidence=[signals[4].evidence[0]],
            source_links=[_source_link("Pulse deck archive", "07_LOGS/Pulse-Decks/")],
            related_nodes=[
                _node("runtime_agent_bus", "coordination_bus", "Runtime Agent Bus", "handoff_surface"),
                _node("pulse_deck_archive", "log_surface", "Pulse deck archive", "handoff_artifact"),
            ],
            recommended_actions=[
                _action("use-deck-inventory", "Use deck inventory before creating duplicate Pulse artifacts", "review", approval=False, target_ref="chaseos pulse deck-inventory --json")
            ],
            generated_at=snapshot.generated_at,
            urgency=3,
            confidence=0.8,
            scope=PulseCardScope(agent_id="codex", project_ids=["ChaseOS"]),
        ),
        _card(
            deck_id=deck_id,
            index=3,
            audience="agent",
            card_class="Permission Request",
            title="Authority expansion is still blocked behind operator approval",
            summary="Signal decks do not grant writeback, memory approval, runtime dispatch, provider calls, Agent Bus writes, or schedule activation.",
            why_it_matters="This prevents product-grade work from silently becoming autonomous authority.",
            evidence=[signals[5].evidence[0]],
            source_links=[_source_link("Pulse writeback boundary", "runtime/pulse/writeback.py")],
            related_nodes=[
                _node("gate_governance", "governance_process", "Gate governance", "approval_required"),
                _node("pulse_writeback_layer", "runtime_module", "Pulse Writeback Layer", "bounded_by"),
            ],
            recommended_actions=[
                _action("preserve-authority-boundary", "Keep authority expansion in separate approval passes", "skip", approval=False)
            ],
            generated_at=snapshot.generated_at,
            urgency=4,
            confidence=0.88,
            scope=PulseCardScope(agent_id="codex", project_ids=["ChaseOS"]),
        ),
    ]
    deck = PulseDeck(
        deck_id=deck_id,
        audience="agent",
        generated_at=snapshot.generated_at,
        cards=cards,
        source_summary=["signal_driven_local_snapshot", *sorted({signal.source_type for signal in signals})],
        schedule_ref="runtime/schedules/manifests/hermes_runtime_pulse.yaml",
    )
    deck.validate()
    return deck


def _build_shared_deck(snapshot: PulseLocalSignalSnapshot, signals: tuple[PulseSignal, ...]) -> PulseDeck:
    deck_id = f"pulse-shared-{snapshot.generated_at[:10]}-signal"
    cards = [
        _card(
            deck_id=deck_id,
            index=1,
            audience="shared_coordination",
            card_class="Multi-Agent Coordination",
            title="Pulse work is now parallel-runtime coordinated",
            summary="Recent activity logs show Codex and Hermes/OpenClaw-style runtime work occurring on the same ChaseOS Pulse lane.",
            why_it_matters="Pulse needs a single repo-grounded coordination surface so parallel runtimes do not duplicate or overclaim work.",
            evidence=signals[2].evidence,
            source_links=[
                _source_link("Agent activity index", "07_LOGS/Agent-Activity/Agent-Activity-Index.md"),
                _source_link("Latest Hermes activity", snapshot.latest_hermes_activity_log or "07_LOGS/Agent-Activity/"),
            ],
            related_nodes=[
                _node("codex_runtime", "runtime_adapter", "Codex", "participant"),
                _node("hermes_runtime", "runtime_adapter", "Hermes", "participant"),
                _node("agent_bus", "coordination_bus", "Agent Bus", "coordination_surface"),
            ],
            recommended_actions=[
                _action("read-latest-logs", "Check recent build and agent activity logs before the next Pulse pass", "review", approval=False)
            ],
            generated_at=snapshot.generated_at,
            urgency=4,
            confidence=0.82,
            scope=PulseCardScope(coordination_ids=["pulse_parallel_runtime_lane"], project_ids=["ChaseOS"]),
        ),
        _card(
            deck_id=deck_id,
            index=2,
            audience="shared_coordination",
            card_class="Governance Risk",
            title="Do not treat signal decks as schedule activation or canonical writeback",
            summary="The signal-driven path can write deck artifacts only when requested; it cannot mutate canonical truth or execute schedules.",
            why_it_matters="This keeps Pulse product-grade progress separate from live autonomy, connector access, and R&D workbook writes.",
            evidence=[
                _evidence("runtime/pulse/signal_driven_decks.py", "runtime_code", "Signal-driven decks declare blocked authority flags.")
            ],
            source_links=[_source_link("Signal-driven deck module", "runtime/pulse/signal_driven_decks.py")],
            related_nodes=[
                _node("pulse_governance", "governance_process", "Pulse Governance", "guards"),
                _node("rnd_workbook", "governance_surface", "R&D Workbook", "not_written"),
            ],
            recommended_actions=[
                _action("keep-rnd-untouched", "Do not update the R&D workbook in this pass", "skip", approval=False)
            ],
            generated_at=snapshot.generated_at,
            urgency=4,
            confidence=0.86,
            scope=PulseCardScope(coordination_ids=["pulse_parallel_runtime_lane"], project_ids=["ChaseOS"]),
        ),
        _card(
            deck_id=deck_id,
            index=3,
            audience="shared_coordination",
            card_class="Review Queue",
            title="Signal deck output should feed the next truth-state review",
            summary="The next Pulse pass should validate generated signal decks against completion, hardening, and Agent Bus handoff evidence.",
            why_it_matters="This gives the six-pass sequence a measurable checkpoint after each substantial pass.",
            evidence=[
                _evidence("06_AGENTS/ChaseOS-Pulse-Post-Apply-Truth-State-Audit.md", "audit_doc", "Pulse truth-state proof docs exist for review.")
            ],
            source_links=[_source_link("Pulse proof docs", "06_AGENTS/")],
            related_nodes=[
                _node("truth_state_audit", "governance_process", "Truth-State Audit", "next_review"),
                _node("pulse_deck_inventory", "runtime_command", "Pulse deck inventory", "input"),
            ],
            recommended_actions=[
                _action("run-signal-tests", "Run signal deck tests and CLI proof", "review", approval=False, target_ref="runtime/pulse/test_signal_driven_decks.py")
            ],
            generated_at=snapshot.generated_at,
            urgency=3,
            confidence=0.8,
            scope=PulseCardScope(coordination_ids=["pulse_parallel_runtime_lane"], project_ids=["ChaseOS"]),
        ),
    ]
    deck = PulseDeck(
        deck_id=deck_id,
        audience="shared_coordination",
        generated_at=snapshot.generated_at,
        cards=cards,
        source_summary=["signal_driven_local_snapshot", *sorted({signal.source_type for signal in signals})],
        schedule_ref="runtime/schedules/manifests/chaseos_pulse_daily.yaml",
    )
    deck.validate()
    return deck


def _deck_slug(audience: str, generated_at: str, slug_prefix: str | None) -> str:
    prefix = slug_prefix or generated_at[:10]
    label = "shared" if audience == "shared_coordination" else audience
    return f"{prefix}-{label}-pulse-signal"


def build_signal_driven_pulse_decks(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    slug_prefix: str | None = None,
    write: bool = False,
) -> PulseSignalDrivenDeckResult:
    """Build or write signal-driven local Pulse decks."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    snapshot = build_pulse_local_signal_snapshot(vault, generated_at=generated)
    signals = collect_signal_driven_pulse_signals(vault, generated_at=generated)
    decks = (
        _build_user_deck(snapshot, signals),
        _build_agent_deck(snapshot, signals),
        _build_shared_deck(snapshot, signals),
    )
    artifacts: list[PulseDeckArtifact] = []
    writes: list[str] = []
    if write:
        for deck in decks:
            artifact = write_deck_artifacts(
                vault,
                deck,
                slug=_deck_slug(deck.audience, generated, slug_prefix),
            )
            artifacts.append(artifact)
            writes.extend([artifact.markdown_path, artifact.json_path])

    result = PulseSignalDrivenDeckResult(
        generated_at=generated,
        snapshot=snapshot,
        signals=signals,
        decks=decks,
        write_requested=write,
        write_executed=write,
        artifacts=tuple(artifacts),
        writes=tuple(writes),
        read_only=not write,
    )
    result.validate()
    return result


def print_signal_driven_summary(result: PulseSignalDrivenDeckResult) -> str:
    """Return a compact operator-readable summary for CLI output."""

    result.validate()
    mode = "WRITE" if result.write_executed else "DRY RUN"
    lines = [
        f"Pulse signal-driven deck generation [{mode}]: {result.deck_count} deck(s), {result.signal_count} signal(s)",
        f"  completion_status: {result.snapshot.completion_status}",
        f"  hardening_status:  {result.snapshot.hardening_status}",
        f"  schedule_manifests: {len(result.snapshot.inactive_schedule_manifests)}/{len(result.snapshot.schedule_manifests)} inactive",
    ]
    for deck in result.decks:
        output_dir = PULSE_DECK_ROOT / AUDIENCE_DIRS[deck.audience]
        lines.append(f"  - {deck.audience}: {len(deck.cards)} cards ({output_dir.as_posix()})")
    if result.write_executed:
        lines.append("  writes:")
        lines.extend(f"    - {path}" for path in result.writes)
    else:
        lines.append("  no files written; pass --write to write log-only artifacts")
    return "\n".join(lines)


def result_to_json(result: PulseSignalDrivenDeckResult) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True)
