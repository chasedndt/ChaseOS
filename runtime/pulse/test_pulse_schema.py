from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.pulse.card_schema import (
    EvidenceRef,
    PulseCard,
    PulseCardScope,
    PulseDeck,
    RecommendedAction,
    SourceLinkRef,
)
from runtime.pulse.deck_generator import generate_deck
from runtime.pulse.feedback import PulseFeedbackRecord, apply_feedback
from runtime.pulse.renderer_json import render_deck_json
from runtime.pulse.renderer_markdown import render_deck_markdown
from runtime.pulse.signal_collector import PulseSignal, collect_declared_signals


def test_pulse_card_supports_required_user_shape() -> None:
    card = PulseCard(
        card_id="card-1",
        audience="user",
        card_class="Future Prep",
        title="Prepare next pass",
        summary="Review Pulse truth before enabling runtime writeback.",
        evidence=[
            EvidenceRef(
                source_path="00_HOME/Now.md",
                source_type="now",
                summary="Phase 9 active state observed.",
            )
        ],
        recommended_actions=[
            RecommendedAction(
                action_id="review",
                label="Review checklist",
                action_type="review",
            )
        ],
        urgency=3,
        confidence=0.8,
    )

    payload = card.to_dict()
    assert payload["audience"] == "user"
    assert payload["card_class"] == "Future Prep"
    assert payload["canonical_writeback_enabled"] is False
    assert payload["evidence"][0]["source_path"] == "00_HOME/Now.md"


def test_invalid_card_class_fails_closed() -> None:
    card = PulseCard(
        card_id="bad",
        audience="agent",
        card_class="Future Prep",
        title="Wrong audience",
        summary="This class is user-only.",
    )

    try:
        card.validate()
    except ValueError as exc:
        assert "not valid for audience" in str(exc)
    else:
        raise AssertionError("invalid card class should fail")


def test_deck_json_round_trip_and_markdown_render() -> None:
    deck = PulseDeck(
        deck_id="deck-1",
        audience="shared",
        cards=[
            PulseCard(
                card_id="shared-1",
                audience="shared",
                card_class="Governance Risk",
                title="Writeback boundary",
                summary="Canonical writeback remains disabled.",
            )
        ],
    )

    rendered = render_deck_json(deck)
    parsed = json.loads(rendered)
    assert parsed["canonical_writeback_enabled"] is False
    assert "Writeback boundary" in render_deck_markdown(deck)
    round_trip = PulseDeck.from_dict(parsed)
    assert round_trip.deck_id == "deck-1"


def test_generate_deck_from_declared_local_signals() -> None:
    signals = collect_declared_signals(
        [
            {
                "signal_id": "s1",
                "source_type": "build_log",
                "source_path": "07_LOGS/Build-Logs/example.md",
                "summary": "Pulse scaffold created.",
                "tags": ["pulse"],
                "priority": 4,
            }
        ]
    )

    deck = generate_deck(signals, audience="user", deck_id="pulse-user-test")
    assert deck.deck_id == "pulse-user-test"
    assert deck.cards[0].card_class == "Today's Operating Brief"
    assert deck.cards[0].evidence[0].source_type == "build_log"


def test_external_signal_requires_explicit_enablement() -> None:
    try:
        collect_declared_signals(
            [
                {
                    "signal_id": "web",
                    "source_type": "external_connector",
                    "summary": "External source",
                }
            ]
        )
    except ValueError as exc:
        assert "explicit enablement" in str(exc)
    else:
        raise AssertionError("external connector should require enablement")


def test_feedback_does_not_enable_canonical_writeback() -> None:
    card = PulseCard(
        card_id="card-feedback",
        audience="user",
        card_class="Memory Update",
        title="Memory candidate",
        summary="Candidate only.",
    )
    record = PulseFeedbackRecord(
        feedback_id="fb-1",
        card_id="card-feedback",
        feedback_type="memory_candidate",
    )

    updated = apply_feedback(card, record)
    assert updated.feedback[0].feedback_type == "memory_candidate"
    assert record.creates_memory_candidate is True
    assert record.canonical_writeback_allowed is False


def test_signal_dataclass_validates_audience_and_priority() -> None:
    signal = PulseSignal(
        signal_id="agent-signal",
        source_type="runtime_reflection",
        summary="Runtime reflected on bounded scope.",
        audience_hint="agent",
        priority=5,
    )

    signal.validate()
    assert signal.audience_hint == "agent"


def test_pulse_card_supports_master_context_fields() -> None:
    card = PulseCard(
        card_id="card-master",
        deck_id="deck-master",
        audience="user",
        card_class="Manual Input Needed",
        type="manual_input_needed",
        title="Product images needed",
        summary="OpenFlow-style upload work is blocked by missing assets.",
        why_it_matters="The workflow should request assets before attempting a live upload.",
        scope=PulseCardScope(user_id="chase", project_ids=["BusinessOS"]),
        evidence=[
            EvidenceRef(
                source_path="07_LOGS/Agent-Activity/openflow/example.md",
                source_type="agent_log",
                summary="Upload blocker observed.",
            )
        ],
        source_links=[
            SourceLinkRef(
                label="Business OS blocker log",
                path="07_LOGS/Agent-Activity/openflow/example.md",
            )
        ],
        recommended_actions=[
            RecommendedAction(
                action_id="request-images",
                label="Request product image batch",
                action_type="request_manual_input",
                requires_operator_approval=False,
            )
        ],
        promotion_status="not_promoted",
        writeback_status="draft_only",
        confidence=0.7,
    )

    payload = card.to_dict()
    assert payload["deck_id"] == "deck-master"
    assert payload["type"] == "manual_input_needed"
    assert payload["why_it_matters"].startswith("The workflow")
    assert payload["scope"]["project_ids"] == ["BusinessOS"]
    assert payload["source_links"][0]["label"] == "Business OS blocker log"
    assert payload["promotion_status"] == "not_promoted"
    assert payload["writeback_status"] == "draft_only"


def test_shared_coordination_audience_is_supported() -> None:
    deck = PulseDeck(
        deck_id="shared-coordination-deck",
        audience="shared_coordination",
        cards=[
            PulseCard(
                card_id="shared-coordination-card",
                audience="shared_coordination",
                card_class="Agent Handoff",
                title="Handoff needed",
                summary="One runtime needs another runtime to review a bounded draft.",
            )
        ],
    )

    payload = deck.to_dict()
    assert payload["audience"] == "shared_coordination"
    assert payload["cards"][0]["type"] == "agent_handoff"
