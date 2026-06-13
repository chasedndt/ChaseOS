"""Deterministic backend minimal deck for ChaseOS Pulse Phase B.

This is not the final topic model. It creates a small, evidence-linked user
deck from known ChaseOS local surfaces so the renderer/writeback path can be
validated without visual UI, browsing, schedule activation, or canonical writes.
"""

from __future__ import annotations

from pathlib import Path

from runtime.pulse.card_schema import (
    EvidenceRef,
    PulseCard,
    PulseDeck,
    RecommendedAction,
    RelatedNodeRef,
    ThumbnailRef,
    now_utc,
)
from runtime.pulse.deck_schema import PulseDeckArtifact
from runtime.pulse.signal_collector import collect_file_presence_signals
from runtime.pulse.writeback import write_deck_artifacts


DEFAULT_MINIMAL_USER_CLASSES = [
    "Today's Operating Brief",
    "Carry-Forward",
    "Project Momentum",
    "Manual Input Needed",
    "Runtime Blocker",
    "Research Watch",
    "Memory Update",
    "Suggested Delegation",
]

DEFAULT_MINIMAL_AGENT_CLASSES = [
    "Runtime Reflection",
    "Workflow Improvement",
    "Memory Drift Warning",
]

DEFAULT_MINIMAL_SHARED_CLASSES = [
    "Agent Handoff",
    "Review Queue",
    "Governance Risk",
]


def _evidence(path: str, source_type: str, summary: str) -> EvidenceRef:
    return EvidenceRef(
        source_path=path,
        source_type=source_type,
        summary=summary,
        trust_label="repo-observed",
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


def _card(
    *,
    deck_id: str,
    index: int,
    card_class: str,
    title: str,
    summary: str,
    evidence: list[EvidenceRef],
    related_nodes: list[RelatedNodeRef],
    recommended_actions: list[RecommendedAction],
    generated_at: str,
    urgency: int,
    confidence: float,
    audience: str = "user",
) -> PulseCard:
    return PulseCard(
        card_id=f"{deck_id}-{index:02d}",
        audience=audience,
        card_class=card_class,
        title=title,
        summary=summary,
        generated_at=generated_at,
        evidence=evidence,
        related_nodes=related_nodes,
        thumbnails=[
            ThumbnailRef(
                path="05_TEMPLATES/Pulse-Card-Template.md",
                alt="Pulse card template placeholder",
                source_type="local_template",
            )
        ],
        recommended_actions=recommended_actions,
        urgency=urgency,
        confidence=confidence,
    )


def build_minimal_user_deck(
    vault_root: Path,
    *,
    deck_id: str | None = None,
    generated_at: str | None = None,
) -> PulseDeck:
    generated = generated_at or now_utc()
    target_deck_id = deck_id or f"pulse-user-{generated[:10]}"
    presence_signals = collect_file_presence_signals(vault_root)
    source_summary = sorted({signal.source_type for signal in presence_signals})
    source_summary.append("backend_minimal_deck")

    shared_nodes = [
        _node("chaseos_pulse", "feature", "ChaseOS Pulse", "primary_feature"),
        _node("context_memory_core", "memory_system", "Context Memory Core", "uses"),
    ]

    cards = [
        _card(
            deck_id=target_deck_id,
            index=1,
            card_class="Today's Operating Brief",
            title="ChaseOS Pulse backend deck path is the active focus",
            summary=(
                "Pulse remains a native ChaseOS layer; this deck validates markdown and JSON "
                "output before any live scheduler, UI, connector, or canonical writeback work."
            ),
            evidence=[
                _evidence(
                    "06_AGENTS/ChaseOS-Pulse-Architecture.md",
                    "architecture_doc",
                    "Pulse is defined as native ChaseOS proactive intelligence.",
                ),
                _evidence("00_HOME/Now.md", "now", "Now.md marks Pulse as partial scaffold."),
            ],
            related_nodes=shared_nodes,
            recommended_actions=[
                _action(
                    "review-minimal-deck",
                    "Review backend Pulse deck artifacts",
                    "review",
                    approval=False,
                    target_ref="07_LOGS/Pulse-Decks/users/",
                )
            ],
            generated_at=generated,
            urgency=4,
            confidence=0.8,
        ),
        _card(
            deck_id=target_deck_id,
            index=2,
            card_class="Carry-Forward",
            title="Carry Pulse forward without schedule activation",
            summary=(
                "The next safe increment is backend deck output and tests. Native schedules "
                "remain inactive manifest intent until a separate schedule-runner pass."
            ),
            evidence=[
                _evidence(
                    "runtime/schedules/manifests/chaseos_pulse_daily.yaml",
                    "schedule_manifest",
                    "ChaseOS Pulse daily manifest is scaffolded and disabled.",
                )
            ],
            related_nodes=shared_nodes
            + [_node("native_schedule_engine", "runtime_system", "Native Schedule Engine", "planned_owner")],
            recommended_actions=[
                _action(
                    "defer-schedule-runner",
                    "Keep live schedule runner deferred",
                    "skip",
                    approval=False,
                )
            ],
            generated_at=generated,
            urgency=3,
            confidence=0.75,
        ),
        _card(
            deck_id=target_deck_id,
            index=3,
            card_class="Project Momentum",
            title="Pulse scaffold and audit are already in place",
            summary=(
                "The architecture scaffold and audit established the ChaseOS-owned boundary; "
                "this pass adds the first reusable backend artifact path."
            ),
            evidence=[
                _evidence(
                    "07_LOGS/Build-Logs/2026-04-29-ChaseOS-chaseos-pulse-architecture-scaffolding.md",
                    "build_log",
                    "Initial Pulse architecture scaffold build log exists.",
                ),
                _evidence(
                    "07_LOGS/Build-Logs/2026-04-29-ChaseOS-chaseos-pulse-scaffold-audit.md",
                    "build_log",
                    "Pulse scaffold audit passed with partial-status caveats.",
                ),
            ],
            related_nodes=shared_nodes,
            recommended_actions=[
                _action(
                    "run-tests",
                    "Run focused Pulse backend tests",
                    "review",
                    approval=False,
                    target_ref="runtime/pulse/test_backend_minimal_deck.py",
                )
            ],
            generated_at=generated,
            urgency=3,
            confidence=0.85,
        ),
        _card(
            deck_id=target_deck_id,
            index=4,
            card_class="Manual Input Needed",
            title="R&D workbook update still needs explicit approval",
            summary=(
                "Pulse R&D rows are staged conceptually, but the workbook should stay untouched "
                "until the operator approves post-audit insertion."
            ),
            evidence=[
                _evidence(
                    "07_LOGS/Build-Logs/2026-04-29-ChaseOS-chaseos-pulse-scaffold-audit.md",
                    "build_log",
                    "Audit confirmed the R&D workbook was left untouched.",
                )
            ],
            related_nodes=[
                _node("rnd_register", "governance_surface", "R&D Register", "approval_needed")
            ],
            recommended_actions=[
                _action(
                    "decide-rnd",
                    "Approve or defer Pulse R&D row insertion",
                    "decide",
                    target_ref="06_AGENTS/Feature-Register.md",
                )
            ],
            generated_at=generated,
            urgency=2,
            confidence=0.8,
        ),
        _card(
            deck_id=target_deck_id,
            index=5,
            card_class="Runtime Blocker",
            title="Live Pulse execution is blocked on native schedule runner work",
            summary=(
                "The manifest shape exists, but no runner, queue, lease, catch-up, or delivery "
                "integration is active for Pulse yet."
            ),
            evidence=[
                _evidence(
                    "06_AGENTS/ChaseOS-Pulse-Architecture.md",
                    "architecture_doc",
                    "Implementation status marks schedule manifests as inactive partial shapes.",
                ),
                _evidence(
                    "runtime/schedules/manifests/hermes_runtime_pulse.yaml",
                    "schedule_manifest",
                    "Hermes runtime Pulse manifest is scaffolded and disabled.",
                ),
            ],
            related_nodes=[
                _node("aor", "runtime_system", "AOR", "future_executor"),
                _node("hermes", "runtime", "Hermes", "agent_pulse_subject"),
            ],
            recommended_actions=[
                _action(
                    "create-schedule-pass",
                    "Plan native schedule runner pass after backend validation",
                    "create_task",
                )
            ],
            generated_at=generated,
            urgency=3,
            confidence=0.75,
        ),
        _card(
            deck_id=target_deck_id,
            index=6,
            card_class="Research Watch",
            title="External connectors remain opt-in only",
            summary=(
                "Pulse can later use external sources, but this backend deck uses local repo "
                "truth only and keeps unrestricted browsing disabled."
            ),
            evidence=[
                _evidence(
                    "runtime/pulse/signal_collector.py",
                    "runtime_code",
                    "External connector signals require explicit enablement.",
                )
            ],
            related_nodes=[
                _node("source_intelligence", "runtime_system", "Source Intelligence Core", "future_input")
            ],
            recommended_actions=[
                _action(
                    "keep-connectors-disabled",
                    "Keep connector ingestion disabled in this pass",
                    "skip",
                    approval=False,
                )
            ],
            generated_at=generated,
            urgency=2,
            confidence=0.8,
        ),
        _card(
            deck_id=target_deck_id,
            index=7,
            card_class="Memory Update",
            title="Context Memory Core remains candidate-first",
            summary=(
                "Context events, atoms, clusters, temporal facts, and feedback rules can inform "
                "Pulse cards, but promotion stays review-gated."
            ),
            evidence=[
                _evidence(
                    "06_AGENTS/Context-Memory-Core.md",
                    "architecture_doc",
                    "Context Memory Core produces candidates and review queues, not direct truth writes.",
                )
            ],
            related_nodes=[
                _node("personal_map", "memory_system", "Personal Map", "related_memory_surface")
            ],
            recommended_actions=[
                _action(
                    "review-memory-candidates",
                    "Review memory candidates before promotion",
                    "review",
                    target_ref="runtime/memory/",
                )
            ],
            generated_at=generated,
            urgency=2,
            confidence=0.8,
        ),
        _card(
            deck_id=target_deck_id,
            index=8,
            card_class="Suggested Delegation",
            title="Run a truth-state audit before expanding Pulse authority",
            summary=(
                "Before connecting Pulse to schedules, external sources, or writeback queues, "
                "run the truth-state checklist against the new backend artifacts."
            ),
            evidence=[
                _evidence(
                    "06_AGENTS/Pulse-Truth-State-Audit-Checklist.md",
                    "audit_checklist",
                    "Pulse truth-state checklist exists for the next verification pass.",
                )
            ],
            related_nodes=[
                _node("pulse_truth_audit", "governance_process", "Pulse Truth-State Audit", "next_review")
            ],
            recommended_actions=[
                _action(
                    "run-truth-audit",
                    "Run Pulse truth-state audit after backend deck pass",
                    "run_truth_audit",
                    approval=False,
                    target_ref="06_AGENTS/Pulse-Truth-State-Audit-Checklist.md",
                )
            ],
            generated_at=generated,
            urgency=3,
            confidence=0.8,
        ),
    ]

    deck = PulseDeck(
        deck_id=target_deck_id,
        audience="user",
        generated_at=generated,
        cards=cards,
        source_summary=source_summary,
        schedule_ref="runtime/schedules/manifests/chaseos_pulse_daily.yaml",
    )
    deck.validate()
    return deck


def build_minimal_agent_deck(
    vault_root: Path,
    *,
    deck_id: str | None = None,
    generated_at: str | None = None,
) -> PulseDeck:
    generated = generated_at or now_utc()
    target_deck_id = deck_id or f"pulse-agent-{generated[:10]}"
    presence_signals = collect_file_presence_signals(vault_root)
    source_summary = sorted({signal.source_type for signal in presence_signals})
    source_summary.append("backend_minimal_agent_deck")
    runtime_nodes = [
        _node("hermes", "runtime", "Hermes", "runtime_subject"),
        _node("openclaw", "runtime", "OpenClaw", "peer_runtime"),
        _node("chaseos_pulse", "feature", "ChaseOS Pulse", "feature_context"),
    ]
    cards = [
        _card(
            deck_id=target_deck_id,
            index=1,
            audience="agent",
            card_class="Runtime Reflection",
            title="Pulse v1 local lane is complete from repo evidence",
            summary="Runtime agents can treat Pulse as locally complete while keeping future authority-gated expansions separate.",
            evidence=[_evidence("06_AGENTS/ChaseOS-Pulse-Completion-Tracker.md", "tracker", "Pulse tracker records v1 local lane completion.")],
            related_nodes=runtime_nodes,
            recommended_actions=[_action("review-pulse-completion", "Review Pulse completion evidence", "review", approval=False, target_ref="06_AGENTS/ChaseOS-Pulse-Completion-Tracker.md")],
            generated_at=generated,
            urgency=3,
            confidence=0.85,
        ),
        _card(
            deck_id=target_deck_id,
            index=2,
            audience="agent",
            card_class="Workflow Improvement",
            title="Post-completion hardening remains read-only",
            summary="Future Pulse checks should reconcile proofs and boundaries without writing approvals, bus tasks, schedules, or canonical state.",
            evidence=[_evidence("runtime/pulse/post_completion_hardening.py", "runtime_code", "Post-completion hardening report is read-only.")],
            related_nodes=runtime_nodes,
            recommended_actions=[_action("run-hardening-report", "Run post-completion hardening report", "review", approval=False, target_ref="chaseos pulse post-completion-hardening --json")],
            generated_at=generated,
            urgency=2,
            confidence=0.8,
        ),
        _card(
            deck_id=target_deck_id,
            index=3,
            audience="agent",
            card_class="Memory Drift Warning",
            title="Do not infer canonical memory promotion from Pulse cards",
            summary="Pulse decks can expose candidates and signals, but memory approval and knowledge promotion remain separately governed.",
            evidence=[_evidence("runtime/pulse/card_schema.py", "runtime_code", "Pulse card schemas carry writeback state without direct canonical mutation.")],
            related_nodes=runtime_nodes,
            recommended_actions=[_action("keep-memory-gated", "Keep memory approval behind governed writeback", "skip", approval=False)],
            generated_at=generated,
            urgency=2,
            confidence=0.8,
        ),
    ]
    deck = PulseDeck(
        deck_id=target_deck_id,
        audience="agent",
        generated_at=generated,
        cards=cards,
        source_summary=source_summary,
        schedule_ref="runtime/schedules/manifests/hermes_runtime_pulse.yaml",
    )
    deck.validate()
    return deck


def build_minimal_shared_coordination_deck(
    vault_root: Path,
    *,
    deck_id: str | None = None,
    generated_at: str | None = None,
) -> PulseDeck:
    generated = generated_at or now_utc()
    target_deck_id = deck_id or f"pulse-shared-{generated[:10]}"
    presence_signals = collect_file_presence_signals(vault_root)
    source_summary = sorted({signal.source_type for signal in presence_signals})
    source_summary.append("backend_minimal_shared_coordination_deck")
    shared_nodes = [
        _node("runtime_agent_bus", "coordination_bus", "Runtime Agent Bus", "coordination_surface"),
        _node("chaseos_pulse", "feature", "ChaseOS Pulse", "feature_context"),
    ]
    cards = [
        _card(
            deck_id=target_deck_id,
            index=1,
            audience="shared_coordination",
            card_class="Agent Handoff",
            title="Pulse handoff chain is artifact-complete",
            summary="Hermes review, ingest, candidate apply, audit, workbook sync, schedule proof, and local deck proof are now represented as repo evidence.",
            evidence=[_evidence("07_LOGS/Agent-Activity/Agent-Activity-Index.md", "agent_activity_index", "Pulse completion and proof logs are indexed for runtime handoff.")],
            related_nodes=shared_nodes,
            recommended_actions=[_action("read-handoff-evidence", "Read indexed Pulse handoff evidence", "review", approval=False, target_ref="07_LOGS/Agent-Activity/Agent-Activity-Index.md")],
            generated_at=generated,
            urgency=3,
            confidence=0.85,
        ),
        _card(
            deck_id=target_deck_id,
            index=2,
            audience="shared_coordination",
            card_class="Review Queue",
            title="Post-completion checks should stay regression-focused",
            summary="The next shared-runtime activity is evidence regression and drift detection, not another live enqueue or candidate apply.",
            evidence=[_evidence("runtime/pulse/post_completion_hardening.py", "runtime_code", "Read-only hardening report enumerates proof and boundary checks.")],
            related_nodes=shared_nodes,
            recommended_actions=[_action("run-regression-checks", "Run Pulse post-completion regression checks", "review", approval=False, target_ref="runtime/pulse/test_post_completion_hardening.py")],
            generated_at=generated,
            urgency=2,
            confidence=0.8,
        ),
        _card(
            deck_id=target_deck_id,
            index=3,
            audience="shared_coordination",
            card_class="Governance Risk",
            title="Broad UI and live schedule activation remain separate approvals",
            summary="Pulse feature-lane completion does not authorize broad Studio product-shell work or persistent schedule activation.",
            evidence=[_evidence("00_HOME/Now.md", "now", "Now-state separates current Pulse local completion from future broad Studio and schedule activation work.")],
            related_nodes=shared_nodes,
            recommended_actions=[_action("preserve-boundaries", "Preserve Pulse authority boundaries", "skip", approval=False)],
            generated_at=generated,
            urgency=3,
            confidence=0.85,
        ),
    ]
    deck = PulseDeck(
        deck_id=target_deck_id,
        audience="shared_coordination",
        generated_at=generated,
        cards=cards,
        source_summary=source_summary,
        schedule_ref="runtime/schedules/manifests/chaseos_pulse_daily.yaml",
    )
    deck.validate()
    return deck


def generate_and_write_minimal_agent_deck(
    vault_root: Path,
    *,
    deck_id: str | None = None,
    slug: str | None = None,
    generated_at: str | None = None,
) -> PulseDeckArtifact:
    deck = build_minimal_agent_deck(vault_root, deck_id=deck_id, generated_at=generated_at)
    return write_deck_artifacts(vault_root, deck, slug=slug)


def generate_and_write_minimal_shared_coordination_deck(
    vault_root: Path,
    *,
    deck_id: str | None = None,
    slug: str | None = None,
    generated_at: str | None = None,
) -> PulseDeckArtifact:
    deck = build_minimal_shared_coordination_deck(vault_root, deck_id=deck_id, generated_at=generated_at)
    return write_deck_artifacts(vault_root, deck, slug=slug)


def generate_and_write_minimal_user_deck(
    vault_root: Path,
    *,
    deck_id: str | None = None,
    slug: str | None = None,
    generated_at: str | None = None,
) -> PulseDeckArtifact:
    deck = build_minimal_user_deck(vault_root, deck_id=deck_id, generated_at=generated_at)
    return write_deck_artifacts(vault_root, deck, slug=slug)
