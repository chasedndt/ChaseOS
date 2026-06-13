from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.pulse.approval_queue_ui import (
    build_pulse_approval_queue_ui,
    render_pulse_approval_queue_ui_html,
    write_pulse_approval_queue_ui_html,
)
from runtime.pulse.real_approval_artifact_rehearsal import run_real_approval_artifact_rehearsal


def _snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def _write_user_deck(vault: Path) -> None:
    deck_path = vault / "07_LOGS" / "Pulse-Decks" / "users" / "2026-05-03-user-pulse.json"
    deck_path.parent.mkdir(parents=True, exist_ok=True)
    deck_path.write_text(
        json.dumps(
            {
                "deck_id": "pulse-approval-queue-test",
                "audience": "user",
                "generated_at": "2026-05-03T10:40:00+01:00",
                "cards": [
                    {
                        "card_id": "pulse-card-approval-queue-001",
                        "audience": "user",
                        "card_class": "Decision Needed",
                        "title": "Approval queue test card",
                        "summary": "Test card.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _seed_request(vault: Path) -> str:
    _write_user_deck(vault)
    rehearsal = run_real_approval_artifact_rehearsal(
        vault,
        generated_at="2026-05-03T10:41:00+01:00",
    )
    return rehearsal.approval_request_artifact.request_id


def test_approval_queue_ui_empty_vault_is_read_only(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    before = _snapshot(vault)

    model = build_pulse_approval_queue_ui(
        vault,
        generated_at="2026-05-03T10:42:00+01:00",
    )

    assert _snapshot(vault) == before
    assert model["surface"] == "chaseos_pulse_approval_queue_ui"
    assert model["summary"]["approval_center_status"] == "no_review_items"
    assert model["summary"]["lane_count"] == 8
    assert model["authority"]["grants_approvals"] is False
    assert model["authority"]["canonical_writeback_allowed"] is False
    assert model["writes"] == []


def test_approval_queue_ui_reads_blocked_request_without_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    request_id = _seed_request(vault)
    before = _snapshot(vault)

    model = build_pulse_approval_queue_ui(
        vault,
        request_id=request_id,
        generated_at="2026-05-03T10:43:00+01:00",
    )

    assert _snapshot(vault) == before
    assert model["summary"]["approval_center_status"] == "blocked_or_waiting_for_evidence"
    assert model["summary"]["approval_request_count"] == 1
    assert model["summary"]["missing_approval_key_count"] > 0
    assert model["summary"]["candidate_row_count"] >= 1
    assert any(row["item_kind"] == "feedback_candidate" for row in model["candidate_rows"])
    assert all(action["execution_allowed"] is False for action in model["action_previews"])


def test_approval_queue_ui_render_contains_core_regions(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    request_id = _seed_request(vault)

    html = render_pulse_approval_queue_ui_html(
        build_pulse_approval_queue_ui(vault, request_id=request_id)
    )

    assert "<!doctype html>" in html
    assert "ChaseOS Pulse Approval Queue" in html
    assert "Review Lanes" in html
    assert "Candidate Queue" in html
    assert "Display Actions" in html
    assert "Blocked Authority" in html


def test_approval_queue_ui_write_stays_inside_approval_queue_dir(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    request_id = _seed_request(vault)

    model = write_pulse_approval_queue_ui_html(
        vault,
        request_id=request_id,
        generated_at="2026-05-03T10:44:00+01:00",
    )
    output = vault / model["html_output_path"]

    assert output.exists()
    assert output.name == "2026-05-03-approval-queue.html"
    assert output.parent == vault / "07_LOGS" / "Pulse-Decks" / "approval-queue"
    assert model["writes"] == ["07_LOGS/Pulse-Decks/approval-queue/2026-05-03-approval-queue.html"]


def test_approval_queue_ui_rejects_output_outside_approval_queue_dir(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    with pytest.raises(ValueError):
        write_pulse_approval_queue_ui_html(
            vault,
            output_path=vault / "07_LOGS" / "bad-approval-queue.html",
        )
