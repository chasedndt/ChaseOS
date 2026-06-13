"""Tests for runtime/pulse/bus_enqueue.py — live Pulse Agent Bus enqueue."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.pulse.bus_enqueue import (
    PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED,
    PULSE_BUS_ENQUEUE_RESULT_STATUS_BUS_ERROR,
    PULSE_BUS_ENQUEUE_RESULT_STATUS_DUPLICATE,
    PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED,
    PulseAgentBusEnqueueResult,
    enqueue_pulse_review_task,
    enqueue_pulse_review_task_by_request_id,
    load_enqueue_results,
)
from runtime.pulse.bus_enqueue_approval_validation import (
    PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED,
    PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY,
    PulseAgentBusApprovalValidationEvidence,
    PulseAgentBusApprovalValidationResult,
)
from runtime.pulse.bus_enqueue_approval_request import PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ready_validation(
    candidate_id: str = "cand-001",
    candidate_kind: str = "feedback",
    recipient: str = "Hermes",
    work_fingerprint: str = "test-wfp-abc123",
) -> PulseAgentBusApprovalValidationResult:
    """Build a ready (all approvals satisfied) validation result."""
    return PulseAgentBusApprovalValidationResult(
        validation_id="pulse-bus-approval-validation-aabbccdd0011",
        request_id="pulse-bus-enqueue-approval-aabbccdd0011",
        preflight_id="pulse-bus-enqueue-preflight-aabbccdd0011",
        contract_id="pulse-bus-review-contract-aabbccdd0011",
        candidate_id=candidate_id,
        candidate_kind=candidate_kind,
        recipient=recipient,
        work_fingerprint=work_fingerprint,
        validation_status=PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY,
        satisfied_approvals=PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS,
        missing_approvals=(),
        reviewer="operator",
    )


def _blocked_validation(
    candidate_id: str = "cand-001",
    missing: tuple[str, ...] = ("operator_enqueue_approval",),
) -> PulseAgentBusApprovalValidationResult:
    """Build a blocked (missing approvals) validation result."""
    all_required = set(PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS)
    satisfied = tuple(sorted(all_required - set(missing)))
    return PulseAgentBusApprovalValidationResult(
        validation_id="pulse-bus-approval-validation-bbccddee0022",
        request_id="pulse-bus-enqueue-approval-bbccddee0022",
        preflight_id="pulse-bus-enqueue-preflight-bbccddee0022",
        contract_id="pulse-bus-review-contract-bbccddee0022",
        candidate_id=candidate_id,
        candidate_kind="feedback",
        recipient="Hermes",
        work_fingerprint="test-wfp-blocked",
        validation_status=PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED,
        satisfied_approvals=satisfied,
        missing_approvals=missing,
        reviewer="operator",
    )


# ── Result dataclass ──────────────────────────────────────────────────────────

class TestPulseAgentBusEnqueueResult:
    def test_valid_enqueued_result(self):
        r = PulseAgentBusEnqueueResult(
            result_id="pulse-bus-enqueue-result-aabb",
            validation_id="vld-001",
            request_id="req-001",
            candidate_id="cand-001",
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint="wfp-001",
            result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED,
            enqueued=True,
            task_id="task-001",
            reason="Task created on Agent Bus.",
        )
        r.validate()
        assert r.enqueued is True
        assert r.task_id == "task-001"

    def test_valid_blocked_result(self):
        r = PulseAgentBusEnqueueResult(
            result_id="pulse-bus-enqueue-result-ccdd",
            validation_id="vld-002",
            request_id="req-002",
            candidate_id="cand-002",
            candidate_kind="personal_map",
            recipient="Hermes",
            work_fingerprint="wfp-002",
            result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED,
            enqueued=False,
            reason="validation blocked",
        )
        r.validate()
        assert r.enqueued is False
        assert r.task_id is None

    def test_enqueued_without_task_id_raises(self):
        r = PulseAgentBusEnqueueResult(
            result_id="pulse-bus-enqueue-result-xxyy",
            validation_id="vld-003",
            request_id="req-003",
            candidate_id="cand-003",
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint="wfp-003",
            result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED,
            enqueued=True,
            task_id=None,
        )
        with pytest.raises(ValueError, match="task_id"):
            r.validate()

    def test_not_enqueued_with_task_id_raises(self):
        r = PulseAgentBusEnqueueResult(
            result_id="pulse-bus-enqueue-result-zz11",
            validation_id="vld-004",
            request_id="req-004",
            candidate_id="cand-004",
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint="wfp-004",
            result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED,
            enqueued=False,
            task_id="task-should-not-exist",
        )
        with pytest.raises(ValueError, match="task_id"):
            r.validate()

    def test_governance_flags_immutable(self):
        r = PulseAgentBusEnqueueResult(
            result_id="pulse-bus-enqueue-result-govv",
            validation_id="vld-005",
            request_id="req-005",
            candidate_id="cand-005",
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint="wfp-005",
            result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED,
            enqueued=True,
            task_id="task-005",
            candidate_apply_allowed=True,
        )
        with pytest.raises(ValueError, match="candidate apply"):
            r.validate()

    def test_invalid_result_status_raises(self):
        r = PulseAgentBusEnqueueResult(
            result_id="pulse-bus-enqueue-result-stat",
            validation_id="vld-006",
            request_id="req-006",
            candidate_id="cand-006",
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint="wfp-006",
            result_status="made_up_status",
            enqueued=False,
        )
        with pytest.raises(ValueError, match="invalid result_status"):
            r.validate()

    def test_to_dict(self):
        r = PulseAgentBusEnqueueResult(
            result_id="pulse-bus-enqueue-result-dict",
            validation_id="vld-007",
            request_id="req-007",
            candidate_id="cand-007",
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint="wfp-007",
            result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED,
            enqueued=False,
            reason="test reason",
        )
        d = r.to_dict()
        assert d["enqueued"] is False
        assert d["result_status"] == PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED
        assert d["candidate_apply_allowed"] is False
        assert d["canonical_writeback_allowed"] is False


# ── enqueue_pulse_review_task ─────────────────────────────────────────────────

class TestEnqueuePulseReviewTask:
    def test_blocked_validation_returns_blocked_result(self, tmp_path):
        validation = _blocked_validation()
        result = enqueue_pulse_review_task(tmp_path, validation)
        assert result.result_status == PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED
        assert result.enqueued is False
        assert "validation_status" in result.reason

    def test_blocked_result_is_persisted(self, tmp_path):
        validation = _blocked_validation()
        result = enqueue_pulse_review_task(tmp_path, validation)
        log_root = tmp_path / "07_LOGS" / "Pulse-Decks" / "agent-bus-enqueue-results"
        assert log_root.exists()
        logs = list(log_root.glob("*.jsonl"))
        assert len(logs) == 1
        lines = logs[0].read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["result_status"] == PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED
        assert data["candidate_id"] == result.candidate_id

    def test_duplicate_fingerprint_returns_duplicate_result(self, tmp_path):
        validation = _ready_validation(work_fingerprint="wfp-dup-001")
        existing_task = {
            "task_id": "task-existing-001",
            "work_fingerprint": "wfp-dup-001",
            "status": "open",
        }
        with patch("runtime.pulse.bus_enqueue._duplicate_check", return_value=existing_task):
            result = enqueue_pulse_review_task(tmp_path, validation)
        assert result.result_status == PULSE_BUS_ENQUEUE_RESULT_STATUS_DUPLICATE
        assert result.enqueued is False
        assert result.duplicate_found is True
        assert result.duplicate_task_id == "task-existing-001"

    def test_duplicate_result_is_persisted(self, tmp_path):
        validation = _ready_validation(work_fingerprint="wfp-dup-002")
        existing_task = {
            "task_id": "task-existing-002",
            "work_fingerprint": "wfp-dup-002",
            "status": "claimed",
        }
        with patch("runtime.pulse.bus_enqueue._duplicate_check", return_value=existing_task):
            enqueue_pulse_review_task(tmp_path, validation)
        log_root = tmp_path / "07_LOGS" / "Pulse-Decks" / "agent-bus-enqueue-results"
        logs = list(log_root.glob("*.jsonl"))
        assert len(logs) == 1
        data = json.loads(logs[0].read_text(encoding="utf-8").strip())
        assert data["result_status"] == PULSE_BUS_ENQUEUE_RESULT_STATUS_DUPLICATE

    def test_skip_duplicate_check_bypasses_dedup(self, tmp_path):
        validation = _ready_validation(work_fingerprint="wfp-skip-dup")
        mock_bus_result = {"created": True, "task_id": "task-new-001"}
        with patch("runtime.pulse.bus_enqueue._duplicate_check") as mock_dup, \
             patch("runtime.agent_bus.bus.create_task", return_value=mock_bus_result):
            result = enqueue_pulse_review_task(tmp_path, validation, skip_duplicate_check=True)
        mock_dup.assert_not_called()
        assert result.result_status == PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED
        assert result.task_id == "task-new-001"

    def test_successful_enqueue_returns_enqueued_result(self, tmp_path):
        validation = _ready_validation(work_fingerprint="wfp-success-001")
        mock_bus_result = {"created": True, "task_id": "task-success-001"}
        with patch("runtime.pulse.bus_enqueue._duplicate_check", return_value=None), \
             patch("runtime.agent_bus.bus.create_task", return_value=mock_bus_result):
            result = enqueue_pulse_review_task(tmp_path, validation)
        assert result.result_status == PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED
        assert result.enqueued is True
        assert result.task_id == "task-success-001"
        assert result.candidate_apply_allowed is False
        assert result.canonical_writeback_allowed is False

    def test_successful_enqueue_persists_result(self, tmp_path):
        validation = _ready_validation(work_fingerprint="wfp-persist-001")
        mock_bus_result = {"created": True, "task_id": "task-persist-001"}
        with patch("runtime.pulse.bus_enqueue._duplicate_check", return_value=None), \
             patch("runtime.agent_bus.bus.create_task", return_value=mock_bus_result):
            enqueue_pulse_review_task(tmp_path, validation)
        log_root = tmp_path / "07_LOGS" / "Pulse-Decks" / "agent-bus-enqueue-results"
        assert log_root.exists()
        logs = list(log_root.glob("*.jsonl"))
        assert len(logs) == 1
        data = json.loads(logs[0].read_text(encoding="utf-8").strip())
        assert data["result_status"] == PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED
        assert data["task_id"] == "task-persist-001"

    def test_bus_create_task_not_created_returns_bus_error(self, tmp_path):
        validation = _ready_validation(work_fingerprint="wfp-error-001")
        mock_bus_result = {"created": False, "reason": "recipient capacity full"}
        with patch("runtime.pulse.bus_enqueue._duplicate_check", return_value=None), \
             patch("runtime.agent_bus.bus.create_task", return_value=mock_bus_result):
            result = enqueue_pulse_review_task(tmp_path, validation)
        assert result.result_status == PULSE_BUS_ENQUEUE_RESULT_STATUS_BUS_ERROR
        assert result.enqueued is False
        assert "recipient capacity full" in result.reason

    def test_bus_exception_returns_bus_error(self, tmp_path):
        validation = _ready_validation(work_fingerprint="wfp-exc-001")
        with patch("runtime.pulse.bus_enqueue._duplicate_check", return_value=None), \
             patch("runtime.agent_bus.bus.create_task", side_effect=RuntimeError("bus unavailable")):
            result = enqueue_pulse_review_task(tmp_path, validation)
        assert result.result_status == PULSE_BUS_ENQUEUE_RESULT_STATUS_BUS_ERROR
        assert result.enqueued is False
        assert "bus unavailable" in result.reason

    def test_bus_error_is_persisted(self, tmp_path):
        validation = _ready_validation(work_fingerprint="wfp-exc-persist")
        with patch("runtime.pulse.bus_enqueue._duplicate_check", return_value=None), \
             patch("runtime.agent_bus.bus.create_task", side_effect=RuntimeError("bus down")):
            enqueue_pulse_review_task(tmp_path, validation)
        log_root = tmp_path / "07_LOGS" / "Pulse-Decks" / "agent-bus-enqueue-results"
        logs = list(log_root.glob("*.jsonl"))
        assert len(logs) == 1
        data = json.loads(logs[0].read_text(encoding="utf-8").strip())
        assert data["result_status"] == PULSE_BUS_ENQUEUE_RESULT_STATUS_BUS_ERROR

    def test_governance_flags_always_false_on_enqueued_result(self, tmp_path):
        validation = _ready_validation(work_fingerprint="wfp-gov-001")
        with patch("runtime.pulse.bus_enqueue._duplicate_check", return_value=None), \
             patch("runtime.agent_bus.bus.create_task", return_value={"created": True, "task_id": "task-gov-001"}):
            result = enqueue_pulse_review_task(tmp_path, validation)
        assert result.enqueued is True
        assert result.candidate_apply_allowed is False
        assert result.canonical_writeback_allowed is False
        assert result.review_response_ingest_allowed is False
        assert result.mutates_canonical_state is False
        assert result.second_datastore_write_allowed is False
        assert result.provider_or_connector_call_allowed is False
        assert result.schedule_activation_allowed is False

    def test_empty_fingerprint_skips_duplicate_call(self, tmp_path):
        from runtime.pulse.bus_enqueue import _duplicate_check
        # _duplicate_check returns None immediately for empty fingerprint.
        result = _duplicate_check(tmp_path, "", "Hermes")
        assert result is None

    def test_no_matching_task_returns_none_from_duplicate_check(self, tmp_path):
        from runtime.pulse.bus_enqueue import _duplicate_check
        existing = [{"task_id": "t-001", "work_fingerprint": "other-wfp", "status": "open"}]
        with patch("runtime.agent_bus.bus.list_tasks", return_value=existing):
            result = _duplicate_check(tmp_path, "different-fingerprint", "Hermes")
        assert result is None

    def test_done_task_not_treated_as_duplicate(self, tmp_path):
        from runtime.pulse.bus_enqueue import _duplicate_check
        existing = [{"task_id": "t-done", "work_fingerprint": "wfp-done", "status": "done"}]
        with patch("runtime.agent_bus.bus.list_tasks", return_value=existing):
            result = _duplicate_check(tmp_path, "wfp-done", "Hermes")
        assert result is None


# ── enqueue_pulse_review_task_by_request_id ───────────────────────────────────

class TestEnqueueByRequestId:
    def test_not_found_raises(self, tmp_path):
        evidence = PulseAgentBusApprovalValidationEvidence(
            operator_enqueue_approval_present=True,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
        )
        with pytest.raises(ValueError, match="not found"):
            enqueue_pulse_review_task_by_request_id(
                tmp_path, "nonexistent-request-id", evidence=evidence
            )

    def test_blocked_evidence_returns_blocked_result(self, tmp_path):
        # Simulate partial evidence (operator approval missing) via mocked validation.
        blocked_validation = _blocked_validation(
            candidate_id="cand-byreq-001",
            missing=("operator_enqueue_approval",),
        )
        partial_evidence = PulseAgentBusApprovalValidationEvidence(
            operator_enqueue_approval_present=False,
            gate_policy_defined=True,
            external_sender_allowance_present=True,
            duplicate_work_fingerprint_reviewed=True,
        )
        with patch(
            "runtime.pulse.bus_enqueue.validate_agent_bus_enqueue_approval_request_by_id",
            return_value=blocked_validation,
        ):
            result = enqueue_pulse_review_task_by_request_id(
                tmp_path, "pulse-bus-enqueue-approval-fake-id", evidence=partial_evidence
            )
        assert result.result_status == PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED
        assert result.enqueued is False


# ── load_enqueue_results ──────────────────────────────────────────────────────

class TestLoadEnqueueResults:
    def test_empty_returns_empty(self, tmp_path):
        results = load_enqueue_results(tmp_path)
        assert results == []

    def test_loads_persisted_results(self, tmp_path):
        validation = _blocked_validation(candidate_id="cand-load-001")
        enqueue_pulse_review_task(tmp_path, validation)
        results = load_enqueue_results(tmp_path)
        assert len(results) == 1
        assert results[0].candidate_id == "cand-load-001"

    def test_filters_by_candidate_id(self, tmp_path):
        v1 = _blocked_validation(candidate_id="cand-filter-a")
        v2 = _blocked_validation(candidate_id="cand-filter-b")
        v2.validation_id  # just access to ensure it's usable
        enqueue_pulse_review_task(tmp_path, v1)
        enqueue_pulse_review_task(tmp_path, v2)
        results = load_enqueue_results(tmp_path, candidate_id="cand-filter-a")
        assert len(results) == 1
        assert results[0].candidate_id == "cand-filter-a"

    def test_filters_by_result_status(self, tmp_path):
        v_blocked = _blocked_validation(candidate_id="cand-status-filter")
        enqueue_pulse_review_task(tmp_path, v_blocked)
        blocked = load_enqueue_results(tmp_path, result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED)
        assert len(blocked) == 1
        enqueued = load_enqueue_results(tmp_path, result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED)
        assert len(enqueued) == 0

    def test_missing_log_root_returns_empty(self, tmp_path):
        results = load_enqueue_results(tmp_path / "nonexistent_vault")
        assert results == []

    def test_corrupt_line_skipped_gracefully(self, tmp_path):
        log_root = tmp_path / "07_LOGS" / "Pulse-Decks" / "agent-bus-enqueue-results"
        log_root.mkdir(parents=True)
        log_file = log_root / "2026-04-30-enqueue-results.jsonl"
        log_file.write_text("not-json\n", encoding="utf-8")
        results = load_enqueue_results(tmp_path)
        assert results == []
