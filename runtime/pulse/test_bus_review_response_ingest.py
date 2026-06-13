"""Tests for runtime/pulse/bus_review_response_ingest.py"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from runtime.pulse.bus_review_response_ingest import (
    INGEST_REGISTRY_FILENAME,
    PulseReviewIngestItem,
    PulseReviewResponseIngestResult,
    _decision_type_for,
    _find_result_attached_event,
    _load_ingest_registry,
    _parse_notes_field,
    _parse_verdict,
    _save_ingest_registry,
    ingest_pulse_review_responses,
)
from runtime.pulse.bus_enqueue import (
    PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED,
    PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED,
    PULSE_BUS_ENQUEUE_RESULTS_ROOT,
    PulseAgentBusEnqueueResult,
)


_RUN_AT = "2026-04-30T14:00:00Z"
_TASK_ID = "task-pulse-abc123"
_CANDIDATE_ID = "cand-feedback-001"
_CANDIDATE_KIND = "feedback"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _enqueue_result(
    task_id: str = _TASK_ID,
    candidate_id: str = _CANDIDATE_ID,
    candidate_kind: str = _CANDIDATE_KIND,
    status: str = PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED,
) -> PulseAgentBusEnqueueResult:
    is_enqueued = status == PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED
    return PulseAgentBusEnqueueResult(
        result_id=f"result-{candidate_id}",
        candidate_id=candidate_id,
        candidate_kind=candidate_kind,
        request_id=f"req-{candidate_id}",
        validation_id=f"val-{candidate_id}",
        recipient="Hermes",
        work_fingerprint=f"wfp-{candidate_id}",
        result_status=status,
        enqueued=is_enqueued,
        enqueued_at=_RUN_AT,
        task_id=task_id if is_enqueued else None,
    )


def _done_task(task_id: str = _TASK_ID, candidate_kind: str = _CANDIDATE_KIND) -> dict:
    return {
        "task_id": task_id,
        "status": "done",
        "request": f"Pulse candidate review: {_CANDIDATE_ID}",
        "notes": (
            f"pulse_candidate_id={_CANDIDATE_ID} "
            f"pulse_candidate_kind={candidate_kind} "
            f"pulse_validation_id=val-001 "
            f"pulse_request_id=req-001"
        ),
        "work_fingerprint": f"wfp-{_CANDIDATE_ID}",
        "recipient": "Hermes",
        "created_at": _RUN_AT,
        "updated_at": _RUN_AT,
    }


def _result_attached_event(message: str = "## Hermes Review — PASS\n**Verdict:** PASS — 3 endorsed, 0 flagged.") -> dict:
    return {
        "event_id": "evt-result-001",
        "task_id": _TASK_ID,
        "event_type": "result_attached",
        "message": message,
        "created_at": _RUN_AT,
        "artifacts": [],
    }


# ── Unit tests ────────────────────────────────────────────────────────────────

class TestParseVerdict:
    def test_pass_verdict(self) -> None:
        assert _parse_verdict("## Hermes Review — PASS\nVerdict: PASS") == "pass"

    def test_conditional_pass_verdict(self) -> None:
        assert _parse_verdict("Verdict: CONDITIONAL PASS") == "conditional_pass"

    def test_flagged_verdict(self) -> None:
        assert _parse_verdict("Verdict: FLAGGED — 2 endorsed, 3 flagged.") == "flagged"

    def test_conditional_pass_beats_pass(self) -> None:
        # "CONDITIONAL PASS" contains "PASS" but must match conditional_pass first
        assert _parse_verdict("CONDITIONAL PASS — something") == "conditional_pass"

    def test_unreadable_when_no_match(self) -> None:
        assert _parse_verdict("no verdict here") == "unreadable"

    def test_empty_message(self) -> None:
        assert _parse_verdict("") == "unreadable"


class TestDecisionTypeFor:
    def test_feedback_pass_maps_to_accept(self) -> None:
        assert _decision_type_for("feedback", "pass") == "accept_for_future_ranking"

    def test_feedback_flagged_maps_to_defer(self) -> None:
        assert _decision_type_for("feedback", "flagged") == "defer_candidate"

    def test_personal_map_pass_maps_to_approve(self) -> None:
        assert _decision_type_for("personal_map", "pass") == "approve_for_future_apply"

    def test_execution_repair_pass_maps_to_approve(self) -> None:
        assert _decision_type_for("execution_repair", "pass") == "approve_for_future_apply"

    def test_unreadable_maps_to_request_more_context(self) -> None:
        assert _decision_type_for("feedback", "unreadable") == "request_more_context"

    def test_unknown_kind_falls_back_to_feedback_map(self) -> None:
        # Unknown kind falls back to feedback mapping
        result = _decision_type_for("unknown_kind", "pass")
        assert result == "accept_for_future_ranking"


class TestFindResultAttachedEvent:
    def test_returns_last_result_attached(self) -> None:
        events = [
            {"event_type": "created", "message": "created"},
            {"event_type": "result_attached", "message": "first result"},
            {"event_type": "result_attached", "message": "final result"},
        ]
        evt = _find_result_attached_event(events)
        assert evt is not None
        assert evt["message"] == "final result"

    def test_returns_none_when_no_result_attached(self) -> None:
        events = [
            {"event_type": "created", "message": "created"},
            {"event_type": "started", "message": "started"},
        ]
        assert _find_result_attached_event(events) is None

    def test_returns_none_on_empty_list(self) -> None:
        assert _find_result_attached_event([]) is None


class TestParseNotesField:
    def test_parses_key_value_pairs(self) -> None:
        notes = "pulse_candidate_id=cand-001 pulse_candidate_kind=feedback"
        parsed = _parse_notes_field(notes)
        assert parsed["pulse_candidate_id"] == "cand-001"
        assert parsed["pulse_candidate_kind"] == "feedback"

    def test_empty_notes_returns_empty_dict(self) -> None:
        assert _parse_notes_field("") == {}

    def test_ignores_parts_without_equals(self) -> None:
        parsed = _parse_notes_field("key=value plain_word")
        assert "plain_word" not in parsed
        assert parsed["key"] == "value"


class TestIngestRegistry:
    def test_load_empty_when_file_missing(self, tmp_path: Path) -> None:
        assert _load_ingest_registry(tmp_path) == set()

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        ids = {"task-001", "task-002"}
        _save_ingest_registry(tmp_path, ids)
        loaded = _load_ingest_registry(tmp_path)
        assert loaded == ids

    def test_load_fail_open_on_corrupt_file(self, tmp_path: Path) -> None:
        path = tmp_path / PULSE_BUS_ENQUEUE_RESULTS_ROOT / INGEST_REGISTRY_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not valid json", encoding="utf-8")
        assert _load_ingest_registry(tmp_path) == set()


class TestIngestResultDataclass:
    def test_valid_result_passes_validate(self) -> None:
        r = PulseReviewResponseIngestResult(
            run_at=_RUN_AT,
            ingested_count=1,
            skipped_already_ingested=0,
            skipped_not_done=0,
            skipped_no_event=0,
            error_count=0,
        )
        r.validate()

    def test_governance_flags_immutable(self) -> None:
        r = PulseReviewResponseIngestResult(
            run_at=_RUN_AT,
            ingested_count=0,
            skipped_already_ingested=0,
            skipped_not_done=0,
            skipped_no_event=0,
            error_count=0,
        )
        assert r.review_response_ingest_allowed is True
        assert r.candidate_apply_allowed is False
        assert r.canonical_writeback_allowed is False
        assert r.mutates_canonical_state is False
        assert r.second_datastore_write_allowed is False
        assert r.provider_or_connector_call_allowed is False
        assert r.schedule_activation_allowed is False

    def test_validate_raises_if_candidate_apply_set(self) -> None:
        r = PulseReviewResponseIngestResult(
            run_at=_RUN_AT,
            ingested_count=0,
            skipped_already_ingested=0,
            skipped_not_done=0,
            skipped_no_event=0,
            error_count=0,
            candidate_apply_allowed=True,
        )
        with pytest.raises(ValueError, match="cannot allow candidate apply"):
            r.validate()

    def test_to_dict_includes_governance_flags(self) -> None:
        r = PulseReviewResponseIngestResult(
            run_at=_RUN_AT,
            ingested_count=0,
            skipped_already_ingested=0,
            skipped_not_done=0,
            skipped_no_event=0,
            error_count=0,
        )
        d = r.to_dict()
        assert d["review_response_ingest_allowed"] is True
        assert d["candidate_apply_allowed"] is False


# ── Integration-style tests against ingest_pulse_review_responses() ──────────

class TestIngestDryRun:
    def _patch_bus(self, task=None, events=None):
        return (
            patch("runtime.pulse.bus_review_response_ingest._bus.get_task",
                  return_value=task),
            patch("runtime.pulse.bus_review_response_ingest._bus.list_events",
                  return_value=events or []),
        )

    def test_dry_run_does_not_write_decisions(self, tmp_path: Path) -> None:
        enqueue_res = _enqueue_result()
        task = _done_task()
        events = [_result_attached_event()]

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[enqueue_res]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task",
                   return_value=task), \
             patch("runtime.pulse.bus_review_response_ingest._bus.list_events",
                   return_value=events), \
             patch("runtime.pulse.bus_review_response_ingest.persist_review_decision") as mock_persist:

            result = ingest_pulse_review_responses(tmp_path, dry_run=True, run_at=_RUN_AT)

        mock_persist.assert_not_called()
        assert result.ingested_count == 1
        assert len(result.items) == 1
        assert result.items[0].verdict == "pass"
        assert result.items[0].decision_type == "accept_for_future_ranking"

    def test_dry_run_does_not_update_registry(self, tmp_path: Path) -> None:
        enqueue_res = _enqueue_result()
        task = _done_task()
        events = [_result_attached_event()]

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[enqueue_res]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task",
                   return_value=task), \
             patch("runtime.pulse.bus_review_response_ingest._bus.list_events",
                   return_value=events):

            ingest_pulse_review_responses(tmp_path, dry_run=True, run_at=_RUN_AT)

        # Registry should not exist
        registry_path = tmp_path / PULSE_BUS_ENQUEUE_RESULTS_ROOT / INGEST_REGISTRY_FILENAME
        assert not registry_path.exists()


class TestIngestLiveMode:
    def test_live_mode_persists_decision(self, tmp_path: Path) -> None:
        enqueue_res = _enqueue_result()
        task = _done_task()
        events = [_result_attached_event()]

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[enqueue_res]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task",
                   return_value=task), \
             patch("runtime.pulse.bus_review_response_ingest._bus.list_events",
                   return_value=events), \
             patch("runtime.pulse.bus_review_response_ingest.persist_review_decision") as mock_persist:

            result = ingest_pulse_review_responses(tmp_path, dry_run=False, run_at=_RUN_AT)

        mock_persist.assert_called_once()
        assert result.ingested_count == 1

    def test_live_mode_writes_ingest_registry(self, tmp_path: Path) -> None:
        enqueue_res = _enqueue_result()
        task = _done_task()
        events = [_result_attached_event()]

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[enqueue_res]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task",
                   return_value=task), \
             patch("runtime.pulse.bus_review_response_ingest._bus.list_events",
                   return_value=events), \
             patch("runtime.pulse.bus_review_response_ingest.persist_review_decision"):

            ingest_pulse_review_responses(tmp_path, dry_run=False, run_at=_RUN_AT)

        loaded = _load_ingest_registry(tmp_path)
        assert _TASK_ID in loaded

    def test_live_mode_skips_already_ingested(self, tmp_path: Path) -> None:
        # Pre-seed the registry with the task_id
        _save_ingest_registry(tmp_path, {_TASK_ID})
        enqueue_res = _enqueue_result()

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[enqueue_res]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task") as mock_get, \
             patch("runtime.pulse.bus_review_response_ingest.persist_review_decision") as mock_persist:

            result = ingest_pulse_review_responses(tmp_path, dry_run=False, run_at=_RUN_AT)

        mock_get.assert_not_called()
        mock_persist.assert_not_called()
        assert result.skipped_already_ingested == 1
        assert result.ingested_count == 0


class TestIngestSkipConditions:
    def test_skips_non_enqueued_results(self, tmp_path: Path) -> None:
        blocked = _enqueue_result(status=PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED)

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[blocked]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task") as mock_get:

            result = ingest_pulse_review_responses(tmp_path, dry_run=True, run_at=_RUN_AT)

        mock_get.assert_not_called()
        assert result.ingested_count == 0

    def test_skips_task_not_done(self, tmp_path: Path) -> None:
        enqueue_res = _enqueue_result()
        in_progress_task = {**_done_task(), "status": "in_progress"}

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[enqueue_res]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task",
                   return_value=in_progress_task):

            result = ingest_pulse_review_responses(tmp_path, dry_run=True, run_at=_RUN_AT)

        assert result.skipped_not_done == 1
        assert result.ingested_count == 0

    def test_skips_task_not_found(self, tmp_path: Path) -> None:
        enqueue_res = _enqueue_result()

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[enqueue_res]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task",
                   return_value=None):

            result = ingest_pulse_review_responses(tmp_path, dry_run=True, run_at=_RUN_AT)

        assert result.skipped_not_done == 1

    def test_skips_task_with_no_result_attached_event(self, tmp_path: Path) -> None:
        enqueue_res = _enqueue_result()
        task = _done_task()
        no_result_events = [{"event_type": "created", "message": "created", "artifacts": []}]

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[enqueue_res]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task",
                   return_value=task), \
             patch("runtime.pulse.bus_review_response_ingest._bus.list_events",
                   return_value=no_result_events):

            result = ingest_pulse_review_responses(tmp_path, dry_run=True, run_at=_RUN_AT)

        assert result.skipped_no_event == 1


class TestIngestVerdictVariants:
    def _ingest_with_message(self, tmp_path: Path, message: str, kind: str = "feedback") -> PulseReviewResponseIngestResult:
        enqueue_res = _enqueue_result(candidate_kind=kind)
        task = _done_task(candidate_kind=kind)
        events = [_result_attached_event(message=message)]

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[enqueue_res]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task",
                   return_value=task), \
             patch("runtime.pulse.bus_review_response_ingest._bus.list_events",
                   return_value=events):
            return ingest_pulse_review_responses(tmp_path, dry_run=True, run_at=_RUN_AT)

    def test_pass_verdict_for_feedback(self, tmp_path: Path) -> None:
        result = self._ingest_with_message(tmp_path, "**Verdict:** PASS — 3 endorsed, 0 flagged.")
        assert result.items[0].verdict == "pass"
        assert result.items[0].decision_type == "accept_for_future_ranking"

    def test_conditional_pass_verdict(self, tmp_path: Path) -> None:
        result = self._ingest_with_message(tmp_path, "**Verdict:** CONDITIONAL PASS — mixed findings.")
        assert result.items[0].verdict == "conditional_pass"
        assert result.items[0].decision_type == "defer_candidate"

    def test_flagged_verdict(self, tmp_path: Path) -> None:
        result = self._ingest_with_message(tmp_path, "**Verdict:** FLAGGED — 0 endorsed, 2 flagged.")
        assert result.items[0].verdict == "flagged"
        assert result.items[0].decision_type == "defer_candidate"

    def test_unreadable_verdict_maps_to_request_more_context(self, tmp_path: Path) -> None:
        result = self._ingest_with_message(tmp_path, "Could not complete review.")
        assert result.items[0].verdict == "unreadable"
        assert result.items[0].decision_type == "request_more_context"

    def test_personal_map_pass_maps_to_approve(self, tmp_path: Path) -> None:
        result = self._ingest_with_message(tmp_path, "## Hermes Review — PASS\n**Verdict:** PASS — 2 endorsed.", kind="personal_map")
        assert result.items[0].decision_type == "approve_for_future_apply"


class TestIngestErrorIsolation:
    def test_error_in_one_task_does_not_block_next(self, tmp_path: Path) -> None:
        result1 = _enqueue_result(task_id="task-001", candidate_id="cand-001")
        result2 = _enqueue_result(task_id="task-002", candidate_id="cand-002")
        task = _done_task()
        events = [_result_attached_event()]

        def get_task_side_effect(vault, task_id):
            if task_id == "task-001":
                raise RuntimeError("simulated bus error")
            return task

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[result1, result2]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task",
                   side_effect=get_task_side_effect), \
             patch("runtime.pulse.bus_review_response_ingest._bus.list_events",
                   return_value=events):

            result = ingest_pulse_review_responses(tmp_path, dry_run=True, run_at=_RUN_AT)

        assert result.error_count == 1
        assert result.ingested_count == 1
        assert len(result.errors) == 1

    def test_unsupported_candidate_kind_counted_as_error(self, tmp_path: Path) -> None:
        bad_result = _enqueue_result(candidate_kind="unknown_kind")
        task = {**_done_task(), "notes": "pulse_candidate_kind=unknown_kind pulse_candidate_id=cand-001"}
        events = [_result_attached_event()]

        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[bad_result]), \
             patch("runtime.pulse.bus_review_response_ingest._bus.get_task",
                   return_value=task), \
             patch("runtime.pulse.bus_review_response_ingest._bus.list_events",
                   return_value=events):

            result = ingest_pulse_review_responses(tmp_path, dry_run=True, run_at=_RUN_AT)

        assert result.error_count == 1

    def test_no_enqueued_results_returns_zero_counts(self, tmp_path: Path) -> None:
        with patch("runtime.pulse.bus_review_response_ingest.load_enqueue_results",
                   return_value=[]):
            result = ingest_pulse_review_responses(tmp_path, dry_run=True, run_at=_RUN_AT)

        assert result.ingested_count == 0
        assert result.error_count == 0
