from __future__ import annotations

import os
import shutil
from pathlib import Path
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.pulse.bus_enqueue_approval_request import (
    build_agent_bus_enqueue_approval_request,
    persist_agent_bus_enqueue_approval_request,
)
from runtime.pulse.bus_enqueue_design import build_agent_bus_enqueue_preflight
from runtime.pulse.bus_review_queue import build_agent_bus_review_queue_preview
from runtime.pulse.card_schema import EvidenceRef, PulseCard, PulseDeck, RecommendedAction, RelatedNodeRef, ThumbnailRef
from runtime.pulse.feedback import PulseFeedbackRecord, persist_feedback_candidate
from runtime.pulse.local_surface import (
    SURFACE_ID,
    USER_DECK_DIR,
    PulseSurfaceError,
    build_feedback_candidate,
    build_pulse_surface_model,
    find_latest_user_deck_json,
    render_pulse_surface_html,
    write_pulse_surface_html,
)
from runtime.pulse.renderer_json import render_deck_json


_TMP_ROOT = Path("runtime/pulse/_tmp_local_surface")


def _make_vault() -> Path:
    root = (_TMP_ROOT / f"vault-{uuid4().hex}").resolve()
    (root / USER_DECK_DIR).mkdir(parents=True, exist_ok=True)
    return root


def _cleanup(root: Path) -> None:
    base = _TMP_ROOT.resolve()
    target = root.resolve()
    if target == base or base in target.parents:
        shutil.rmtree(target, ignore_errors=True)


def _deck(
    deck_id: str,
    *,
    title: str = "Today focus",
    source_path: str = "00_HOME/Now.md",
    source_url: str | None = None,
    target_ref: str | None = "07_LOGS/Pulse-Decks/users/",
) -> PulseDeck:
    return PulseDeck(
        deck_id=deck_id,
        audience="user",
        generated_at="2026-04-30T07:30:00+01:00",
        cards=[
            PulseCard(
                card_id=f"{deck_id}-01",
                audience="user",
                card_class="Today's Operating Brief",
                title=title,
                summary="Review the latest Pulse deck as a proposal surface.",
                generated_at="2026-04-30T07:30:00+01:00",
                evidence=[
                    EvidenceRef(
                        source_path=source_path,
                        source_type="test_artifact",
                        source_url=source_url,
                        summary="Test deck evidence.",
                        trust_label="repo-observed",
                    )
                ],
                related_nodes=[
                    RelatedNodeRef(
                        node_id="chaseos_pulse",
                        node_type="feature",
                        relation="primary_surface",
                        label="ChaseOS Pulse",
                    )
                ],
                thumbnails=[
                    ThumbnailRef(
                        path="05_TEMPLATES/Pulse-Card-Template.md",
                        alt="Pulse template placeholder",
                        source_type="local_template",
                    )
                ],
                recommended_actions=[
                    RecommendedAction(
                        action_id="review",
                        label="Review deck",
                        action_type="review",
                        target_ref=target_ref,
                        requires_operator_approval=False,
                    )
                ],
                urgency=3,
                confidence=0.8,
            )
        ],
        source_summary=["test"],
        schedule_ref="runtime/schedules/manifests/chaseos_pulse_daily.yaml",
    )


def _write_deck(vault: Path, slug: str, deck: PulseDeck, *, mtime: int) -> Path:
    path = vault / USER_DECK_DIR / f"{slug}.json"
    path.write_text(render_deck_json(deck), encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


def test_latest_user_deck_model_is_read_only_and_governed() -> None:
    vault = _make_vault()
    try:
        older = _write_deck(vault, "2026-04-29-user-pulse", _deck("pulse-user-old"), mtime=100)
        latest = _write_deck(vault, "2026-04-30-user-pulse", _deck("pulse-user-new"), mtime=200)

        assert find_latest_user_deck_json(vault) == latest.resolve()
        model = build_pulse_surface_model(vault)

        assert model["surface"] == SURFACE_ID
        assert model["source_deck_path"] == (USER_DECK_DIR / latest.name).as_posix()
        assert model["deck"]["deck_id"] == "pulse-user-new"
        assert model["deck"]["card_count"] == 1
        assert model["writes"] == []
        assert model["authority"]["local_only"] is True
        assert model["authority"]["canonical_writeback_allowed"] is False
        assert model["authority"]["live_provider_calls_allowed"] is False
        assert model["authority"]["cron_or_scheduler_changed"] is False
        assert older.exists()
    finally:
        _cleanup(vault)


def test_surface_feedback_candidates_do_not_apply_feedback_or_enable_writeback() -> None:
    card = _deck("pulse-user-feedback").cards[0]

    record = build_feedback_candidate(card, "memory_candidate", operator_note="Candidate only")

    assert record.feedback_id == "candidate-pulse-user-feedback-01-memory_candidate"
    assert record.creates_memory_candidate is True
    assert record.canonical_writeback_allowed is False
    assert card.feedback == []


def test_surface_html_renders_deck_cards_evidence_actions_and_feedback_candidates() -> None:
    vault = _make_vault()
    try:
        _write_deck(vault, "2026-04-30-user-pulse", _deck("pulse-user-html"), mtime=100)
        model = build_pulse_surface_model(vault)
        html = render_pulse_surface_html(model)

        assert "ChaseOS Pulse" in html
        assert "Today focus" in html
        assert "00_HOME/Now.md" in html
        assert "Review deck" in html
        assert "Governed Feedback Candidates" in html
        assert "Canonical writeback" in html
        assert "blocked" in html
        assert "<script" not in html.lower()
    finally:
        _cleanup(vault)


def test_surface_writer_outputs_static_html_next_to_latest_user_deck() -> None:
    vault = _make_vault()
    try:
        _write_deck(vault, "2026-04-30-user-pulse", _deck("pulse-user-write"), mtime=100)

        model = write_pulse_surface_html(vault)
        output_path = vault / model["html_output_path"]

        assert model["writes"] == [(USER_DECK_DIR / "2026-04-30-user-pulse.surface.html").as_posix()]
        assert output_path.exists()
        assert "ChaseOS Pulse" in output_path.read_text(encoding="utf-8")
        assert output_path.parent == (vault / USER_DECK_DIR)
    finally:
        _cleanup(vault)


def test_surface_rejects_deck_input_or_output_outside_user_deck_folder() -> None:
    vault = _make_vault()
    try:
        outside = vault / "07_LOGS/Pulse-Decks/agents/agent.json"
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_text(render_deck_json(_deck("pulse-agent-path")), encoding="utf-8")
        _write_deck(vault, "2026-04-30-user-pulse", _deck("pulse-user-safe"), mtime=100)

        with pytest.raises(PulseSurfaceError, match="deck input"):
            build_pulse_surface_model(vault, deck_path=outside)

        with pytest.raises(PulseSurfaceError, match="HTML output"):
            write_pulse_surface_html(vault, output_path=vault / "runtime/pulse/surface.html")
    finally:
        _cleanup(vault)


def test_surface_redacts_protected_references_from_model_and_html() -> None:
    vault = _make_vault()
    try:
        _write_deck(
            vault,
            "2026-04-30-user-pulse",
            _deck(
                "pulse-user-redaction",
                source_path=".env",
                source_url="https://example.invalid/source?token=abc123",
                target_ref="credentials/store.json",
            ),
            mtime=100,
        )

        model = build_pulse_surface_model(vault)
        card = model["cards"][0]
        rendered = render_pulse_surface_html(model)

        assert card["evidence"][0]["source_path"] == "[redacted protected reference]"
        assert card["evidence"][0]["source_url"] == "[redacted protected reference]"
        assert card["recommended_actions"][0]["target_ref"] == "[redacted protected reference]"
        assert ".env" not in rendered
        assert "token=abc123" not in rendered
        assert "credentials/store.json" not in rendered
    finally:
        _cleanup(vault)


def test_surface_includes_read_only_candidate_inspector_snapshot() -> None:
    vault = _make_vault()
    try:
        deck_path = _write_deck(vault, "2026-04-30-user-pulse", _deck("pulse-user-inspector"), mtime=100)
        persist_feedback_candidate(
            vault,
            PulseFeedbackRecord(
                feedback_id="feedback-operator-001",
                card_id="pulse-user-inspector-01",
                feedback_type="show_more_like_this",
                operator_note="Keep this visible in the operator queue.",
                created_at="2026-04-30T22:45:00+01:00",
            ),
            source_deck_path=deck_path,
        )

        model = build_pulse_surface_model(vault)
        inspector = model["candidate_inspector"]
        bus_preview = model["agent_bus_review_queue_preview"]
        rendered = render_pulse_surface_html(model)

        assert inspector["inspector_status"] == "read_only"
        assert inspector["item_count"] == 1
        assert inspector["counts_by_kind"]["feedback_candidate"] == 1
        assert inspector["writes"] == []
        assert inspector["applies_effects"] is False
        assert inspector["second_datastore_write_allowed"] is False
        assert bus_preview["queue_status"] == "read_only"
        assert bus_preview["contract_count"] == 1
        assert bus_preview["counts_by_candidate_kind"]["feedback"] == 1
        assert bus_preview["bus_tasks_written"] is False
        assert bus_preview["approval_requests_written"] is False
        assert bus_preview["agent_bus_task_previews"][0]["intent"] == "REVIEW"
        assert bus_preview["agent_bus_task_previews"][0]["recipient"] == "Hermes"
        assert "Operator Review Queue Snapshot" in rendered
        assert "Agent Bus Review Handoff Preview" in rendered
        assert "Feedback candidate: show_more_like_this" in rendered
    finally:
        _cleanup(vault)


def test_surface_includes_supervised_handoff_readiness_without_live_authority() -> None:
    vault = _make_vault()
    try:
        deck_path = _write_deck(vault, "2026-05-01-user-pulse", _deck("pulse-user-handoff"), mtime=100)
        persist_feedback_candidate(
            vault,
            PulseFeedbackRecord(
                feedback_id="feedback-handoff-001",
                card_id="pulse-user-handoff-01",
                feedback_type="needs_more_evidence",
                operator_note="Route to review before any apply.",
                created_at="2026-05-01T00:20:00+01:00",
            ),
            source_deck_path=deck_path,
        )
        contract = build_agent_bus_review_queue_preview(vault).contracts[0]
        approval_preflight = build_agent_bus_enqueue_preflight(
            contract,
            requested_by="openclaw",
            created_at="2026-05-01T00:21:00+01:00",
        )
        approval_request = build_agent_bus_enqueue_approval_request(
            approval_preflight,
            requested_by="openclaw",
            requested_at="2026-05-01T00:22:00+01:00",
        )
        persist_agent_bus_enqueue_approval_request(vault, approval_request)

        model = build_pulse_surface_model(vault)
        handoff = model["agent_bus_handoff_readiness"]
        rendered = render_pulse_surface_html(model)

        assert handoff["snapshot_status"] == "read_only"
        assert handoff["request_count"] == 1
        assert handoff["item_count"] == 1
        assert handoff["items"][0]["handoff_status"] == "blocked_missing_required_evidence"
        assert "no_persisted_evidence_record" in handoff["items"][0]["blocked_reasons"]
        assert handoff["approval_granted"] is False
        assert handoff["live_agent_bus_handoff_allowed"] is False
        assert handoff["agent_bus_tasks_written"] is False
        assert handoff["canonical_writeback_allowed"] is False
        assert "Supervised Live Handoff Readiness" in rendered
        assert "blocked_missing_required_evidence" in rendered
    finally:
        _cleanup(vault)
