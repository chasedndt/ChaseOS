"""Governed Pulse cards from local connector/source preview candidates.

This module converts metadata-only local source preview candidates into Pulse
cards. It does not read source content, call connectors/providers, browse,
activate schedules, apply candidates, approve memory, or write canonical state.
Optional writes are limited to normal Pulse deck artifacts under
07_LOGS/Pulse-Decks/.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.pulse.card_schema import (
    EvidenceRef,
    PulseCard,
    PulseDeck,
    RecommendedAction,
    RelatedNodeRef,
    SourceLinkRef,
    ThumbnailRef,
    now_utc,
)
from runtime.pulse.connector_source_scanner_local_preview import (
    BLOCKED_EFFECTS,
    PulseSourcePreviewCandidate,
    build_pulse_connector_source_scanner_local_preview,
)
from runtime.pulse.deck_schema import PulseDeckArtifact
from runtime.pulse.writeback import write_deck_artifacts


DEFAULT_LIMIT = 18
MAX_LIMIT = 60
SUPPORTED_AUDIENCES = ("user", "agent", "shared_coordination")
ALLOWED_WRITE_ROOT = "07_LOGS/Pulse-Decks/"


def _vault_path(vault_root: str | Path) -> Path:
    return Path(vault_root).resolve()


def _date_slug(generated_at: str) -> str:
    return (generated_at or now_utc())[:10]


def _audience_label(audience: str) -> str:
    return "shared" if audience == "shared_coordination" else audience


def _deck_id(audience: str, generated_at: str) -> str:
    return f"pulse-source-scanner-{_audience_label(audience)}-{_date_slug(generated_at)}"


def _deck_slug(audience: str, generated_at: str, slug_prefix: str | None) -> str:
    prefix = slug_prefix or _date_slug(generated_at)
    return f"{prefix}-source-scanner-{_audience_label(audience)}-cards"


def _candidate_audience(candidate: PulseSourcePreviewCandidate) -> str:
    if candidate.source_surface_id == "agent_activity":
        return "agent"
    if candidate.source_surface_id == "pulse_decks":
        return "shared_coordination"
    return "user"


def _candidate_card_class(candidate: PulseSourcePreviewCandidate) -> str:
    if candidate.source_surface_id == "agent_activity":
        return "Runtime Reflection"
    if candidate.source_surface_id == "pulse_decks":
        return "Review Queue"
    if candidate.source_surface_id == "build_logs":
        return "Project Momentum"
    if candidate.source_surface_id in {"source_intelligence", "acquisition_runtime"}:
        return "Research Watch"
    if candidate.source_surface_id == "capture_inputs":
        return "Research Watch"
    return "Research Watch"


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
    target_ref: str | None = None,
    approval: bool = True,
) -> RecommendedAction:
    return RecommendedAction(
        action_id=action_id,
        label=label,
        action_type=action_type,
        target_ref=target_ref,
        requires_operator_approval=approval,
        mutates_canonical_state=False,
    )


def _candidate_card(
    candidate: PulseSourcePreviewCandidate,
    *,
    deck_id: str,
    index: int,
    generated_at: str,
) -> PulseCard:
    audience = _candidate_audience(candidate)
    card_class = _candidate_card_class(candidate)
    short_path = candidate.source_path
    title = f"Review local source candidate: {candidate.file_name}"
    summary = (
        f"Pulse found a metadata-only {candidate.artifact_kind} candidate at "
        f"`{short_path}` from the `{candidate.source_surface_id}` source surface. "
        "The source file content has not been read."
    )
    why_it_matters = (
        "This candidate can be reviewed for future Pulse synthesis without granting "
        "live connector execution, unrestricted scanning, memory approval, source "
        "promotion, or canonical writeback."
    )
    card = PulseCard(
        card_id=f"{deck_id}-{index:02d}",
        deck_id=deck_id,
        audience=audience,
        card_class=card_class,
        title=title,
        summary=summary,
        why_it_matters=why_it_matters,
        generated_at=generated_at,
        evidence=[
            EvidenceRef(
                source_path=short_path,
                source_type="local_source_candidate_metadata",
                summary=(
                    f"Metadata-only candidate discovered from {candidate.source_surface_id}; "
                    f"extension={candidate.extension}, size_bytes={candidate.size_bytes}, "
                    f"modified_at={candidate.modified_at}."
                ),
                trust_label="repo-observed",
                observed_at=generated_at,
            )
        ],
        source_links=[
            SourceLinkRef(
                label=candidate.file_name,
                path=short_path,
                source_type=candidate.source_class,
            )
        ],
        related_nodes=[
            _node("chaseos_pulse", "feature", "ChaseOS Pulse", "candidate_card_origin"),
            _node(
                "connector_source_scanner",
                "pulse_lane",
                "Connector / Source Scanner",
                "source_candidate_lane",
            ),
            _node(
                candidate.source_surface_id,
                "source_surface",
                candidate.source_surface_id.replace("_", " ").title(),
                "candidate_source",
            ),
        ],
        thumbnails=[
            ThumbnailRef(
                path="05_TEMPLATES/Pulse-Card-Template.md",
                alt="Pulse source candidate card template placeholder",
                source_type="local_template",
            )
        ],
        recommended_actions=[
            _action(
                f"review-{candidate.candidate_id}",
                "Review candidate metadata",
                "review",
                target_ref=short_path,
                approval=False,
            ),
            _action(
                f"open-{candidate.candidate_id}",
                "Open source artifact for manual inspection",
                "open_source",
                target_ref=short_path,
                approval=False,
            ),
            _action(
                f"defer-live-{candidate.candidate_id}",
                "Keep live connector scan deferred",
                "skip",
                approval=False,
            ),
        ],
        urgency=2,
        confidence=0.72,
        promotion_status="not_promoted",
        writeback_status="card_generated",
        governance_state="proposal",
        canonical_writeback_enabled=False,
    )
    card.validate()
    return card


@dataclass(frozen=True)
class PulseSourceScannerCandidateDeckResult:
    audience: str
    deck_id: str
    card_count: int
    artifact_written: bool = False
    markdown_path: str | None = None
    json_path: str | None = None
    canonical_writeback_enabled: bool = False

    def validate(self) -> None:
        if self.audience not in SUPPORTED_AUDIENCES:
            raise ValueError("invalid source scanner candidate deck audience")
        if not self.deck_id:
            raise ValueError("deck_id is required")
        if self.card_count < 0:
            raise ValueError("card_count cannot be negative")
        if self.artifact_written and (not self.markdown_path or not self.json_path):
            raise ValueError("written deck artifacts require markdown and JSON paths")
        if self.canonical_writeback_enabled:
            raise ValueError("source scanner candidate decks cannot enable canonical writeback")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class PulseConnectorSourceScannerCandidateCards:
    generated_at: str
    status: str
    preview_candidate_count: int
    card_count: int
    deck_count: int
    write_requested: bool
    write_executed: bool
    decks: tuple[PulseSourceScannerCandidateDeckResult, ...]
    writes: tuple[str, ...] = ()
    next_recommended_pass: str = "chaseos-pulse-connector-source-scanner-live-approved-proof"
    read_only: bool = True
    local_only: bool = True
    source_content_read: bool = False
    writes_artifacts: bool = False
    live_connector_execution_enabled: bool = False
    provider_or_connector_call_allowed: bool = False
    unrestricted_web_scan_allowed: bool = False
    browser_history_ingest_allowed: bool = False
    credential_or_secret_read_allowed: bool = False
    schedule_activation_allowed: bool = False
    approval_execution_allowed: bool = False
    memory_approval_allowed: bool = False
    source_promotion_allowed: bool = False
    autonomous_promotion_allowed: bool = False
    canonical_writeback_allowed: bool = False
    rd_workbook_update_allowed: bool = False
    allowed_write_root: str = ALLOWED_WRITE_ROOT
    blocked_effects: tuple[str, ...] = BLOCKED_EFFECTS
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "Cards are built from local preview metadata only; source file content is not read.",
            "Dry-run by default; --write creates Pulse markdown/JSON deck artifacts only under 07_LOGS/Pulse-Decks/.",
        )
    )

    def validate(self) -> None:
        if self.status not in {"ready", "empty"}:
            raise ValueError("invalid source scanner candidate card status")
        if self.preview_candidate_count < 0:
            raise ValueError("preview_candidate_count cannot be negative")
        if self.card_count < 0:
            raise ValueError("card_count cannot be negative")
        if self.deck_count != len(self.decks):
            raise ValueError("deck_count must match deck result count")
        for deck in self.decks:
            deck.validate()
        if self.write_executed and not self.write_requested:
            raise ValueError("write_executed requires write_requested")
        if self.write_executed and self.read_only:
            raise ValueError("written result cannot be read_only")
        if self.write_executed and not self.writes_artifacts:
            raise ValueError("written result must report writes_artifacts")
        if self.source_content_read:
            raise ValueError("candidate card generation cannot read source content")
        if self.live_connector_execution_enabled:
            raise ValueError("candidate card generation cannot enable live connector execution")
        if self.provider_or_connector_call_allowed:
            raise ValueError("candidate card generation cannot call providers/connectors")
        if self.unrestricted_web_scan_allowed:
            raise ValueError("candidate card generation cannot allow unrestricted web scan")
        if self.browser_history_ingest_allowed:
            raise ValueError("candidate card generation cannot ingest browser history")
        if self.credential_or_secret_read_allowed:
            raise ValueError("candidate card generation cannot read secrets")
        if self.schedule_activation_allowed:
            raise ValueError("candidate card generation cannot activate schedules")
        if self.approval_execution_allowed:
            raise ValueError("candidate card generation cannot execute approvals")
        if self.memory_approval_allowed:
            raise ValueError("candidate card generation cannot approve memory")
        if self.source_promotion_allowed or self.autonomous_promotion_allowed:
            raise ValueError("candidate card generation cannot promote sources")
        if self.canonical_writeback_allowed:
            raise ValueError("candidate card generation cannot write canonical state")
        if self.rd_workbook_update_allowed:
            raise ValueError("candidate card generation cannot update the R&D workbook")
        for written in self.writes:
            if not written.replace("\\", "/").startswith(self.allowed_write_root):
                raise ValueError("source scanner candidate card writes must stay under Pulse decks")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "generated_at": self.generated_at,
            "status": self.status,
            "preview_candidate_count": self.preview_candidate_count,
            "card_count": self.card_count,
            "deck_count": self.deck_count,
            "write_requested": self.write_requested,
            "write_executed": self.write_executed,
            "decks": [deck.to_dict() for deck in self.decks],
            "writes": list(self.writes),
            "next_recommended_pass": self.next_recommended_pass,
            "read_only": self.read_only,
            "local_only": self.local_only,
            "source_content_read": self.source_content_read,
            "writes_artifacts": self.writes_artifacts,
            "live_connector_execution_enabled": self.live_connector_execution_enabled,
            "provider_or_connector_call_allowed": self.provider_or_connector_call_allowed,
            "unrestricted_web_scan_allowed": self.unrestricted_web_scan_allowed,
            "browser_history_ingest_allowed": self.browser_history_ingest_allowed,
            "credential_or_secret_read_allowed": self.credential_or_secret_read_allowed,
            "schedule_activation_allowed": self.schedule_activation_allowed,
            "approval_execution_allowed": self.approval_execution_allowed,
            "memory_approval_allowed": self.memory_approval_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "autonomous_promotion_allowed": self.autonomous_promotion_allowed,
            "canonical_writeback_allowed": self.canonical_writeback_allowed,
            "rd_workbook_update_allowed": self.rd_workbook_update_allowed,
            "allowed_write_root": self.allowed_write_root,
            "blocked_effects": list(self.blocked_effects),
            "notes": list(self.notes),
        }


def build_pulse_connector_source_scanner_candidate_decks(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> tuple[PulseDeck, ...]:
    """Build user/agent/shared decks from local preview metadata only."""

    if limit < 1:
        raise ValueError("limit must be at least 1")
    bounded_limit = min(limit, MAX_LIMIT)
    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    preview = build_pulse_connector_source_scanner_local_preview(
        vault,
        generated_at=generated,
        limit=bounded_limit,
    )
    grouped: dict[str, list[PulseCard]] = {audience: [] for audience in SUPPORTED_AUDIENCES}
    deck_ids = {audience: _deck_id(audience, generated) for audience in SUPPORTED_AUDIENCES}

    for candidate in preview.candidates:
        audience = _candidate_audience(candidate)
        grouped[audience].append(
            _candidate_card(
                candidate,
                deck_id=deck_ids[audience],
                index=len(grouped[audience]) + 1,
                generated_at=generated,
            )
        )

    decks: list[PulseDeck] = []
    for audience in SUPPORTED_AUDIENCES:
        cards = grouped[audience]
        if not cards:
            continue
        deck = PulseDeck(
            deck_id=deck_ids[audience],
            audience=audience,
            generated_at=generated,
            cards=cards,
            source_summary=[
                "connector_source_scanner_local_preview",
                "metadata_only",
                f"preview_candidate_count={preview.candidate_count}",
            ],
            schedule_ref="runtime/schedules/manifests/chaseos_pulse_daily.yaml",
            canonical_writeback_enabled=False,
        )
        deck.validate()
        decks.append(deck)
    return tuple(decks)


def build_pulse_connector_source_scanner_candidate_cards(
    vault_root: str | Path,
    *,
    generated_at: str | None = None,
    limit: int = DEFAULT_LIMIT,
    slug_prefix: str | None = None,
    write: bool = False,
) -> PulseConnectorSourceScannerCandidateCards:
    """Build or write Pulse cards from local preview candidates."""

    vault = _vault_path(vault_root)
    generated = generated_at or now_utc()
    preview = build_pulse_connector_source_scanner_local_preview(
        vault,
        generated_at=generated,
        limit=min(limit, MAX_LIMIT),
    )
    decks = build_pulse_connector_source_scanner_candidate_decks(
        vault,
        generated_at=generated,
        limit=limit,
    )
    writes: list[str] = []
    deck_results: list[PulseSourceScannerCandidateDeckResult] = []
    for deck in decks:
        artifact: PulseDeckArtifact | None = None
        if write:
            artifact = write_deck_artifacts(
                vault,
                deck,
                slug=_deck_slug(deck.audience, generated, slug_prefix),
            )
            writes.extend([artifact.markdown_path, artifact.json_path])
        result = PulseSourceScannerCandidateDeckResult(
            audience=deck.audience,
            deck_id=deck.deck_id,
            card_count=len(deck.cards),
            artifact_written=artifact is not None,
            markdown_path=artifact.markdown_path if artifact is not None else None,
            json_path=artifact.json_path if artifact is not None else None,
            canonical_writeback_enabled=deck.canonical_writeback_enabled,
        )
        result.validate()
        deck_results.append(result)

    model = PulseConnectorSourceScannerCandidateCards(
        generated_at=generated,
        status="ready" if decks else "empty",
        preview_candidate_count=preview.candidate_count,
        card_count=sum(len(deck.cards) for deck in decks),
        deck_count=len(decks),
        write_requested=write,
        write_executed=write,
        decks=tuple(deck_results),
        writes=tuple(writes),
        read_only=not write,
        writes_artifacts=write,
    )
    model.validate()
    return model
