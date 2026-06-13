"""Tests for Pulse Agent Bus enqueue approval-request records."""

from __future__ import annotations

import inspect
import shutil
import unittest
from pathlib import Path

import runtime.pulse.bus_enqueue_approval_request as approval_module
from runtime.pulse.bus_enqueue_approval_request import (
    PULSE_BUS_APPROVAL_BLOCKED_EFFECTS,
    PulseAgentBusEnqueueApprovalRequest,
    build_agent_bus_enqueue_approval_ledger,
    build_agent_bus_enqueue_approval_request,
    build_agent_bus_enqueue_approval_request_for_candidate,
    load_agent_bus_enqueue_approval_requests,
    persist_agent_bus_enqueue_approval_request,
)
from runtime.pulse.bus_enqueue_design import build_agent_bus_enqueue_preflight
from runtime.pulse.bus_review_contract import build_agent_bus_review_request_contract
from runtime.pulse.candidate_inspector import PulseCandidateInspectorItem
from runtime.pulse.feedback import PulseFeedbackRecord, load_feedback_candidates, persist_feedback_candidate


_TMP_ROOT = Path(__file__).resolve().parent / "_tmp_bus_enqueue_approval_request"


class PulseAgentBusEnqueueApprovalRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_root = _TMP_ROOT
        self._clean_tmp_root()
        self.tmp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self._clean_tmp_root()

    def _clean_tmp_root(self) -> None:
        if self.tmp_root.exists():
            resolved = self.tmp_root.resolve()
            if resolved.name != "_tmp_bus_enqueue_approval_request":
                raise AssertionError(f"refusing to remove unexpected path: {resolved}")
            shutil.rmtree(resolved)

    def _review_contract(self):
        item = PulseCandidateInspectorItem(
            item_id="candidate-approval-001",
            item_kind="feedback_candidate",
            record_id="candidate-approval-001",
            status="pending_review",
            title="Feedback candidate",
            candidate_kind="feedback",
            candidate_id="candidate-approval-001",
            source_log_path="07_LOGS/Pulse-Decks/feedback-candidates/2026-04-30-feedback-candidates.jsonl",
            source_deck_path="07_LOGS/Pulse-Decks/users/2026-04-30-user-pulse.json",
            source_card_id="pulse-card-approval-001",
            target_ref="pulse-card-approval-001",
            created_at="2026-04-30T10:30:00+01:00",
        )
        return build_agent_bus_review_request_contract(
            item,
            requested_by="codex",
            created_at="2026-04-30T10:31:00+01:00",
        )

    def _preflight(self):
        return build_agent_bus_enqueue_preflight(
            self._review_contract(),
            requested_by="codex",
            created_at="2026-04-30T10:32:00+01:00",
        )

    def _seed_feedback_candidate(self):
        deck_path = self.tmp_root / "07_LOGS" / "Pulse-Decks" / "users" / "2026-04-30-user-pulse.json"
        deck_path.parent.mkdir(parents=True, exist_ok=True)
        deck_path.write_text('{"deck_id": "pulse-deck-test", "cards": []}', encoding="utf-8")
        artifact = persist_feedback_candidate(
            self.tmp_root,
            PulseFeedbackRecord(
                feedback_id="feedback-approval-001",
                card_id="pulse-card-approval-001",
                feedback_type="show_more_like_this",
                operator_note="Ask Hermes to review this before enqueue.",
                created_at="2026-04-30T10:35:00+01:00",
            ),
            source_deck_path=deck_path,
        )
        candidate = load_feedback_candidates(self.tmp_root)[0]
        return candidate, artifact

    def test_module_does_not_import_agent_bus_writer_or_backend(self) -> None:
        source = inspect.getsource(approval_module)

        forbidden_tokens = (
            "runtime.agent_bus.bus",
            "create_task",
            "init_db",
            "get_backend",
            "update_task_status",
            "claim_task",
        )
        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, source)

    def test_builds_approval_request_from_preflight_without_granting_approval(self) -> None:
        request = build_agent_bus_enqueue_approval_request(
            self._preflight(),
            requested_by="codex",
            requested_at="2026-04-30T10:40:00+01:00",
        )
        payload = request.to_dict()

        self.assertEqual(request.status, "approval_requested")
        self.assertEqual(request.operation, "pulse.agent_bus.enqueue_review")
        self.assertEqual(request.intent, "REVIEW")
        self.assertEqual(request.sender, "Operator")
        self.assertEqual(request.recipient, "Hermes")
        self.assertTrue(request.approval_request_only)
        self.assertTrue(request.persisted_request)
        self.assertFalse(request.approval_granted)
        self.assertFalse(request.gate_policy_defined)
        self.assertFalse(request.duplicate_check_performed)
        self.assertFalse(request.live_agent_bus_handoff_allowed)
        self.assertFalse(request.agent_bus_task_written)
        self.assertFalse(request.approval_executed)
        self.assertFalse(request.review_response_ingest_allowed)
        self.assertFalse(request.candidate_apply_allowed)
        self.assertFalse(request.canonical_writeback_allowed)
        self.assertEqual(set(payload["blocked_effects"]), set(PULSE_BUS_APPROVAL_BLOCKED_EFFECTS))
        self.assertFalse(payload["task_payload_preview"]["enqueue_allowed"])
        self.assertFalse(payload["task_payload_preview"]["agent_bus_task_written"])

    def test_persists_approval_request_without_bus_or_candidate_apply_state(self) -> None:
        request = build_agent_bus_enqueue_approval_request(
            self._preflight(),
            requested_by="codex",
            requested_at="2026-04-30T10:45:00+01:00",
        )

        artifact = persist_agent_bus_enqueue_approval_request(self.tmp_root, request)
        loaded = load_agent_bus_enqueue_approval_requests(self.tmp_root)

        self.assertEqual(
            artifact.path,
            "07_LOGS/Pulse-Decks/agent-bus-approval-requests/"
            "2026-04-30-agent-bus-approval-requests.jsonl",
        )
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].request_id, request.request_id)
        self.assertFalse(loaded[0].approval_granted)
        self.assertFalse(loaded[0].agent_bus_task_written)
        self.assertFalse(loaded[0].candidate_apply_allowed)
        self.assertFalse(loaded[0].canonical_writeback_allowed)
        self.assertFalse((self.tmp_root / ".chaseos").exists())

    def test_builds_request_for_candidate_read_only_until_persist_called(self) -> None:
        candidate, artifact = self._seed_feedback_candidate()
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        request = build_agent_bus_enqueue_approval_request_for_candidate(
            self.tmp_root,
            candidate.candidate_id,
            requested_by="codex",
            requested_at="2026-04-30T10:50:00+01:00",
        )
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(request.candidate_id, candidate.candidate_id)
        self.assertEqual(request.source_log_path, artifact.path)
        self.assertFalse(request.approval_granted)
        self.assertFalse(request.live_agent_bus_handoff_allowed)

    def test_approval_ledger_is_read_only_and_empty_read_creates_no_folders(self) -> None:
        ledger = build_agent_bus_enqueue_approval_ledger(self.tmp_root)

        self.assertEqual(ledger.ledger_status, "read_only")
        self.assertEqual(ledger.request_count, 0)
        self.assertEqual(ledger.source_log_paths, [])
        self.assertEqual(ledger.writes, [])
        self.assertFalse(ledger.approval_granted)
        self.assertFalse(ledger.agent_bus_task_written)
        self.assertFalse(ledger.canonical_writeback_allowed)
        self.assertFalse((self.tmp_root / "07_LOGS").exists())

    def test_ledger_loads_persisted_requests_without_apply_effects(self) -> None:
        request = build_agent_bus_enqueue_approval_request(
            self._preflight(),
            requested_at="2026-04-30T10:55:00+01:00",
        )
        persist_agent_bus_enqueue_approval_request(self.tmp_root, request)
        before = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        ledger = build_agent_bus_enqueue_approval_ledger(self.tmp_root)
        after = sorted(path.as_posix() for path in self.tmp_root.rglob("*"))

        self.assertEqual(before, after)
        self.assertEqual(ledger.request_count, 1)
        self.assertEqual(ledger.requests[0].request_id, request.request_id)
        self.assertFalse(ledger.approval_executed)
        self.assertFalse(ledger.agent_bus_task_written)
        self.assertFalse(ledger.second_datastore_write_allowed)

    def test_rejects_approval_execution_or_authority_flags(self) -> None:
        base = build_agent_bus_enqueue_approval_request(
            self._preflight(),
            requested_at="2026-04-30T11:00:00+01:00",
        ).to_dict()

        forbidden_true_flags = (
            "approval_granted",
            "gate_policy_defined",
            "duplicate_check_performed",
            "live_agent_bus_handoff_allowed",
            "agent_bus_task_written",
            "approval_executed",
            "review_response_ingest_allowed",
            "candidate_apply_allowed",
            "canonical_writeback_allowed",
            "mutates_canonical_state",
            "second_datastore_write_allowed",
            "provider_or_connector_call_allowed",
            "schedule_activation_allowed",
        )
        for flag in forbidden_true_flags:
            payload = dict(base)
            payload[flag] = True
            with self.subTest(flag=flag):
                with self.assertRaises(ValueError):
                    PulseAgentBusEnqueueApprovalRequest.from_dict(payload)

        payload = dict(base)
        payload["approval_request_only"] = False
        with self.assertRaises(ValueError):
            PulseAgentBusEnqueueApprovalRequest.from_dict(payload)

    def test_rejects_log_path_outside_approval_request_root(self) -> None:
        outside = self.tmp_root.parent / "outside-agent-bus-approval-requests.jsonl"

        with self.assertRaises(ValueError):
            load_agent_bus_enqueue_approval_requests(self.tmp_root, log_path=outside)


if __name__ == "__main__":
    unittest.main()
