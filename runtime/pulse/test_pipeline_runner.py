"""Tests for runtime/pulse/pipeline_runner.py — Pulse enqueue pipeline runner."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.pulse.pipeline_runner import (
    PULSE_PIPELINE_RUNNER_STATUS_DRY_RUN,
    PULSE_PIPELINE_RUNNER_STATUS_LIVE,
    PulseEnqueuePipelineResult,
    run_pulse_enqueue_pipeline,
)
from runtime.pulse.bus_enqueue import (
    PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED,
    PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED,
    PULSE_BUS_ENQUEUE_RESULT_STATUS_BUS_ERROR,
    PulseAgentBusEnqueueResult,
)
from runtime.pulse.bus_enqueue_approval_request import PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS
from runtime.pulse.bus_enqueue_approval_validation import (
    PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY,
    PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED,
    PulseAgentBusApprovalValidationResult,
)
from runtime.pulse.bus_enqueue_design import (
    PULSE_BUS_ALLOWED_REVIEW_RECIPIENTS,
    PulseAgentBusEnqueuePlan,
    PulseAgentBusEnqueuePreflight,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

_RUN_AT = "2026-04-30T12:00:00Z"
_VAULT = Path("/vault")
_TEST_TMP_ROOT = Path(__file__).resolve().parent / ".test_tmp_pipeline_runner"


@pytest.fixture
def tmp_path(request: pytest.FixtureRequest) -> Path:
    """Repo-local temp path for environments with blocked pytest system temp."""
    root = _TEST_TMP_ROOT.resolve()
    target = (root / uuid.uuid4().hex[:12]).resolve()
    if root not in target.parents:
        raise RuntimeError("test temp path escaped expected root")
    target.mkdir(parents=True, exist_ok=False)

    def cleanup() -> None:
        if target.exists() and root in target.parents:
            shutil.rmtree(target, ignore_errors=True)
        try:
            root.rmdir()
        except OSError:
            pass

    request.addfinalizer(cleanup)
    return target


def _preflight(candidate_id: str = "cand-001", fingerprint: str = "wfp-abc") -> PulseAgentBusEnqueuePreflight:
    return PulseAgentBusEnqueuePreflight(
        preflight_id=f"pulse-bus-enqueue-preflight-{candidate_id}",
        contract_id=f"pulse-bus-review-contract-{candidate_id}",
        candidate_id=candidate_id,
        candidate_kind="feedback",
        sender="Operator",
        recipient="Hermes",
        intent="REVIEW",
        priority="normal",
        request="Review this candidate.",
        expected_output="Review result.",
        notes="test preflight",
        work_fingerprint=fingerprint,
    )


def _empty_plan(run_at: str = _RUN_AT) -> PulseAgentBusEnqueuePlan:
    return PulseAgentBusEnqueuePlan(generated_at=run_at, preflights=[])


def _plan_with(preflights: list[PulseAgentBusEnqueuePreflight], run_at: str = _RUN_AT) -> PulseAgentBusEnqueuePlan:
    return PulseAgentBusEnqueuePlan(generated_at=run_at, preflights=preflights)


def _enqueue_result(
    candidate_id: str = "cand-001",
    status: str = PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED,
    task_id: str | None = "task-abc123",
) -> PulseAgentBusEnqueueResult:
    is_enqueued = status == PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED
    return PulseAgentBusEnqueueResult(
        result_id="pipeline-result-001",
        candidate_id=candidate_id,
        candidate_kind="feedback",
        request_id="req-001",
        validation_id="val-001",
        recipient="Hermes",
        work_fingerprint="wfp-abc",
        result_status=status,
        enqueued=is_enqueued,
        enqueued_at=_RUN_AT,
        task_id=task_id if is_enqueued else None,
    )


# ── PulseEnqueuePipelineResult validation tests ───────────────────────────────

class TestPulseEnqueuePipelineResult:
    def test_valid_dry_run_result(self) -> None:
        r = PulseEnqueuePipelineResult(
            run_at=_RUN_AT,
            pipeline_status=PULSE_PIPELINE_RUNNER_STATUS_DRY_RUN,
            dry_run=True,
            operator_approved=False,
            plan_preflight_count=2,
            dry_run_previews=[{"request": "r1"}, {"request": "r2"}],
        )
        r.validate()

    def test_valid_live_result(self) -> None:
        r = PulseEnqueuePipelineResult(
            run_at=_RUN_AT,
            pipeline_status=PULSE_PIPELINE_RUNNER_STATUS_LIVE,
            dry_run=False,
            operator_approved=True,
            plan_preflight_count=1,
            enqueue_results=[_enqueue_result()],
        )
        r.validate()

    def test_dry_run_cannot_have_enqueue_results(self) -> None:
        r = PulseEnqueuePipelineResult(
            run_at=_RUN_AT,
            pipeline_status=PULSE_PIPELINE_RUNNER_STATUS_DRY_RUN,
            dry_run=True,
            operator_approved=False,
            plan_preflight_count=1,
            enqueue_results=[_enqueue_result()],
        )
        with pytest.raises(ValueError, match="dry_run pipeline cannot have live enqueue results"):
            r.validate()

    def test_live_should_not_have_dry_run_previews(self) -> None:
        r = PulseEnqueuePipelineResult(
            run_at=_RUN_AT,
            pipeline_status=PULSE_PIPELINE_RUNNER_STATUS_LIVE,
            dry_run=False,
            operator_approved=True,
            plan_preflight_count=1,
            dry_run_previews=[{"request": "r1"}],
        )
        with pytest.raises(ValueError, match="live pipeline should not populate dry_run_previews"):
            r.validate()

    def test_governance_flags_immutable(self) -> None:
        for flag in (
            "candidate_apply_allowed",
            "canonical_writeback_allowed",
            "mutates_canonical_state",
            "second_datastore_write_allowed",
            "provider_or_connector_call_allowed",
            "schedule_activation_allowed",
            "review_response_ingest_allowed",
        ):
            r = PulseEnqueuePipelineResult(
                run_at=_RUN_AT,
                pipeline_status=PULSE_PIPELINE_RUNNER_STATUS_DRY_RUN,
                dry_run=True,
                operator_approved=False,
                plan_preflight_count=0,
                **{flag: True},
            )
            with pytest.raises(ValueError):
                r.validate()

    def test_counts(self) -> None:
        enqueued = _enqueue_result(status=PULSE_BUS_ENQUEUE_RESULT_STATUS_ENQUEUED)
        blocked = _enqueue_result(candidate_id="cand-002", status=PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED, task_id=None)
        r = PulseEnqueuePipelineResult(
            run_at=_RUN_AT,
            pipeline_status=PULSE_PIPELINE_RUNNER_STATUS_LIVE,
            dry_run=False,
            operator_approved=True,
            plan_preflight_count=2,
            enqueue_results=[enqueued, blocked],
        )
        assert r.enqueued_count == 1
        assert r.blocked_count == 1
        assert r.duplicate_count == 0
        assert r.bus_error_count == 0

    def test_to_dict(self) -> None:
        r = PulseEnqueuePipelineResult(
            run_at=_RUN_AT,
            pipeline_status=PULSE_PIPELINE_RUNNER_STATUS_DRY_RUN,
            dry_run=True,
            operator_approved=False,
            plan_preflight_count=0,
        )
        d = r.to_dict()
        assert d["dry_run"] is True
        assert d["candidate_apply_allowed"] is False
        assert d["canonical_writeback_allowed"] is False


# ── run_pulse_enqueue_pipeline: dry_run tests ─────────────────────────────────

class TestRunPipelineDryRun:
    def test_dry_run_default_returns_previews_no_enqueue(self, tmp_path: Path) -> None:
        pf = _preflight()
        with patch(
            "runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
            return_value=_plan_with([pf]),
        ):
            result = run_pulse_enqueue_pipeline(tmp_path, run_at=_RUN_AT)

        result.validate()
        assert result.dry_run is True
        assert result.pipeline_status == PULSE_PIPELINE_RUNNER_STATUS_DRY_RUN
        assert result.plan_preflight_count == 1
        assert len(result.dry_run_previews) == 1
        assert result.enqueue_results == []

    def test_dry_run_empty_plan_returns_empty_previews(self, tmp_path: Path) -> None:
        with patch(
            "runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
            return_value=_empty_plan(),
        ):
            result = run_pulse_enqueue_pipeline(tmp_path, run_at=_RUN_AT)

        assert result.dry_run_previews == []
        assert result.plan_preflight_count == 0

    def test_dry_run_does_not_call_bus(self, tmp_path: Path) -> None:
        with patch(
            "runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
            return_value=_empty_plan(),
        ):
            with patch(
                "runtime.pulse.pipeline_runner.enqueue_pulse_review_task"
            ) as mock_enqueue:
                run_pulse_enqueue_pipeline(tmp_path, run_at=_RUN_AT)
                mock_enqueue.assert_not_called()

    def test_dry_run_does_not_persist_approval_requests(self, tmp_path: Path) -> None:
        pf = _preflight()
        with patch(
            "runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
            return_value=_plan_with([pf]),
        ):
            with patch(
                "runtime.pulse.pipeline_runner.persist_agent_bus_enqueue_approval_request"
            ) as mock_persist:
                run_pulse_enqueue_pipeline(tmp_path, run_at=_RUN_AT)
                mock_persist.assert_not_called()

    def test_dry_run_preview_contains_task_payload_shape(self, tmp_path: Path) -> None:
        pf = _preflight()
        with patch(
            "runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
            return_value=_plan_with([pf]),
        ):
            result = run_pulse_enqueue_pipeline(tmp_path, run_at=_RUN_AT)

        preview = result.dry_run_previews[0]
        assert preview["sender"] == "Operator"
        assert preview["recipient"] == "Hermes"
        assert preview["intent"] == "REVIEW"


# ── run_pulse_enqueue_pipeline: live + operator_approved tests ────────────────

class TestRunPipelineLiveApproved:
    def _setup_mocks(
        self,
        *,
        enqueue_return: PulseAgentBusEnqueueResult | None = None,
    ):
        enqueue_ret = enqueue_return or _enqueue_result()
        mock_request = MagicMock()
        mock_request.validate = lambda: None
        mock_request.request_id = "req-001"
        mock_request.preflight_id = "pf-001"
        mock_request.contract_id = "contract-001"
        mock_request.candidate_id = "cand-001"
        mock_request.candidate_kind = "feedback"
        mock_request.recipient = "Hermes"
        mock_request.work_fingerprint = "wfp-abc"

        mock_validation = PulseAgentBusApprovalValidationResult(
            validation_id="val-001",
            request_id="req-001",
            preflight_id="pf-001",
            contract_id="contract-001",
            candidate_id="cand-001",
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint="wfp-abc",
            validation_status=PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY,
            satisfied_approvals=PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS,
            missing_approvals=(),
            reviewer="operator",
        )

        return mock_request, mock_validation, enqueue_ret

    def test_live_all_required_evidence_calls_enqueue(self, tmp_path: Path) -> None:
        pf = _preflight()
        mock_request, mock_validation, enqueue_ret = self._setup_mocks()

        with patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
                   return_value=_plan_with([pf])), \
             patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_approval_request",
                   return_value=mock_request), \
             patch("runtime.pulse.pipeline_runner.persist_agent_bus_enqueue_approval_request"), \
             patch("runtime.pulse.pipeline_runner.validate_agent_bus_enqueue_approval_request",
                   return_value=mock_validation), \
             patch("runtime.pulse.pipeline_runner.enqueue_pulse_review_task",
                   return_value=enqueue_ret) as mock_enqueue:

            result = run_pulse_enqueue_pipeline(
                tmp_path,
                dry_run=False,
                operator_approved=True,
                gate_policy_defined=True,
                external_sender_allowance_present=True,
                duplicate_work_fingerprint_reviewed=True,
                run_at=_RUN_AT,
            )

        mock_enqueue.assert_called_once()
        assert result.pipeline_status == PULSE_PIPELINE_RUNNER_STATUS_LIVE
        assert result.dry_run is False
        assert result.enqueued_count == 1

    def test_live_all_required_evidence_persists_approval_request(self, tmp_path: Path) -> None:
        pf = _preflight()
        mock_request, mock_validation, enqueue_ret = self._setup_mocks()

        with patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
                   return_value=_plan_with([pf])), \
             patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_approval_request",
                   return_value=mock_request), \
             patch("runtime.pulse.pipeline_runner.persist_agent_bus_enqueue_approval_request") as mock_persist, \
             patch("runtime.pulse.pipeline_runner.validate_agent_bus_enqueue_approval_request",
                   return_value=mock_validation), \
             patch("runtime.pulse.pipeline_runner.enqueue_pulse_review_task",
                   return_value=enqueue_ret):

            run_pulse_enqueue_pipeline(
                tmp_path,
                dry_run=False,
                operator_approved=True,
                gate_policy_defined=True,
                external_sender_allowance_present=True,
                duplicate_work_fingerprint_reviewed=True,
                run_at=_RUN_AT,
            )

        mock_persist.assert_called_once()

    def test_live_operator_approval_alone_is_blocked(self, tmp_path: Path) -> None:
        pf = _preflight()
        with patch(
            "runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
            return_value=_plan_with([pf]),
        ), patch("runtime.agent_bus.bus.create_task") as mock_create:
            result = run_pulse_enqueue_pipeline(
                tmp_path,
                dry_run=False,
                operator_approved=True,
                run_at=_RUN_AT,
            )

        mock_create.assert_not_called()
        assert result.blocked_count == 1
        assert result.enqueued_count == 0
        assert "gate_policy_defined" in result.enqueue_results[0].reason
        assert "external_sender_allowance" in result.enqueue_results[0].reason
        assert "duplicate_work_fingerprint_review" in result.enqueue_results[0].reason

    def test_live_all_required_evidence_enqueues_with_real_validation(self, tmp_path: Path) -> None:
        pf = _preflight()
        with patch(
            "runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
            return_value=_plan_with([pf]),
        ), patch(
            "runtime.pulse.bus_enqueue._duplicate_check",
            return_value=None,
        ), patch(
            "runtime.agent_bus.bus.create_task",
            return_value={"created": True, "task_id": "task-live-evidence"},
        ) as mock_create:
            result = run_pulse_enqueue_pipeline(
                tmp_path,
                dry_run=False,
                operator_approved=True,
                gate_policy_defined=True,
                external_sender_allowance_present=True,
                duplicate_work_fingerprint_reviewed=True,
                run_at=_RUN_AT,
            )

        assert result.enqueued_count == 1, result.to_dict()
        mock_create.assert_called_once()
        assert result.enqueue_results[0].task_id == "task-live-evidence"

    def test_live_not_operator_approved_yields_blocked(self, tmp_path: Path) -> None:
        pf = _preflight()
        mock_request, _, _ = self._setup_mocks()
        blocked_validation = PulseAgentBusApprovalValidationResult(
            validation_id="val-blocked",
            request_id="req-001",
            preflight_id="pf-001",
            contract_id="contract-001",
            candidate_id="cand-001",
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint="wfp-abc",
            validation_status=PULSE_BUS_APPROVAL_VALIDATION_STATUS_BLOCKED,
            satisfied_approvals=(),
            missing_approvals=PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS,
            reviewer="operator",
        )
        blocked_result = PulseAgentBusEnqueueResult(
            result_id="res-blocked",
            candidate_id="cand-001",
            candidate_kind="feedback",
            request_id="req-001",
            validation_id="val-blocked",
            recipient="Hermes",
            work_fingerprint="wfp-abc",
            result_status=PULSE_BUS_ENQUEUE_RESULT_STATUS_BLOCKED,
            enqueued=False,
            enqueued_at=_RUN_AT,
        )

        with patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
                   return_value=_plan_with([pf])), \
             patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_approval_request",
                   return_value=mock_request), \
             patch("runtime.pulse.pipeline_runner.persist_agent_bus_enqueue_approval_request"), \
             patch("runtime.pulse.pipeline_runner.validate_agent_bus_enqueue_approval_request",
                   return_value=blocked_validation), \
             patch("runtime.pulse.pipeline_runner.enqueue_pulse_review_task",
                   return_value=blocked_result):

            result = run_pulse_enqueue_pipeline(
                tmp_path, dry_run=False, operator_approved=False, run_at=_RUN_AT
            )

        assert result.blocked_count == 1
        assert result.enqueued_count == 0

    def test_live_empty_plan_returns_empty_results(self, tmp_path: Path) -> None:
        with patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
                   return_value=_empty_plan()):
            result = run_pulse_enqueue_pipeline(
                tmp_path,
                dry_run=False,
                operator_approved=True,
                gate_policy_defined=True,
                external_sender_allowance_present=True,
                duplicate_work_fingerprint_reviewed=True,
                run_at=_RUN_AT,
            )

        assert result.enqueue_results == []
        assert result.plan_preflight_count == 0

    def test_live_multiple_preflights(self, tmp_path: Path) -> None:
        pf1 = _preflight("cand-001", "wfp-1")
        pf2 = _preflight("cand-002", "wfp-2")
        mock_request, mock_validation, _ = self._setup_mocks()
        enqueue_ret1 = _enqueue_result(candidate_id="cand-001")
        enqueue_ret2 = _enqueue_result(candidate_id="cand-002", task_id="task-xyz")

        with patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
                   return_value=_plan_with([pf1, pf2])), \
             patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_approval_request",
                   return_value=mock_request), \
             patch("runtime.pulse.pipeline_runner.persist_agent_bus_enqueue_approval_request"), \
             patch("runtime.pulse.pipeline_runner.validate_agent_bus_enqueue_approval_request",
                   return_value=mock_validation), \
             patch("runtime.pulse.pipeline_runner.enqueue_pulse_review_task",
                   side_effect=[enqueue_ret1, enqueue_ret2]):

            result = run_pulse_enqueue_pipeline(
                tmp_path,
                dry_run=False,
                operator_approved=True,
                gate_policy_defined=True,
                external_sender_allowance_present=True,
                duplicate_work_fingerprint_reviewed=True,
                run_at=_RUN_AT,
            )

        assert result.plan_preflight_count == 2
        assert len(result.enqueue_results) == 2
        assert result.enqueued_count == 2


# ── run_pulse_enqueue_pipeline: error isolation tests ─────────────────────────

class TestRunPipelineErrorIsolation:
    def test_exception_in_preflight_yields_bus_error(self, tmp_path: Path) -> None:
        pf = _preflight()

        with patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
                   return_value=_plan_with([pf])), \
             patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_approval_request",
                   side_effect=RuntimeError("approval build failed")), \
             patch("runtime.pulse.pipeline_runner.enqueue_pulse_review_task") as mock_enqueue, \
             patch("runtime.pulse.pipeline_runner._persist_error_result"):

            result = run_pulse_enqueue_pipeline(
                tmp_path,
                dry_run=False,
                operator_approved=True,
                gate_policy_defined=True,
                external_sender_allowance_present=True,
                duplicate_work_fingerprint_reviewed=True,
                run_at=_RUN_AT,
            )

        mock_enqueue.assert_not_called()
        assert result.bus_error_count == 1
        assert result.enqueued_count == 0

    def test_second_preflight_processed_after_first_exception(self, tmp_path: Path) -> None:
        pf1 = _preflight("cand-001", "wfp-1")
        pf2 = _preflight("cand-002", "wfp-2")
        mock_request = MagicMock()
        mock_request.validate = lambda: None
        mock_request.request_id = "req-001"
        mock_request.preflight_id = "pf-001"
        mock_request.contract_id = "contract-001"
        mock_request.candidate_id = "cand-002"
        mock_request.candidate_kind = "feedback"
        mock_request.recipient = "Hermes"
        mock_request.work_fingerprint = "wfp-2"

        mock_validation = PulseAgentBusApprovalValidationResult(
            validation_id="val-001",
            request_id="req-001",
            preflight_id="pf-001",
            contract_id="contract-001",
            candidate_id="cand-002",
            candidate_kind="feedback",
            recipient="Hermes",
            work_fingerprint="wfp-2",
            validation_status=PULSE_BUS_APPROVAL_VALIDATION_STATUS_READY,
            satisfied_approvals=PULSE_BUS_ENQUEUE_REQUIRED_APPROVALS,
            missing_approvals=(),
            reviewer="operator",
        )
        enqueue_ret2 = _enqueue_result(candidate_id="cand-002")

        with patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
                   return_value=_plan_with([pf1, pf2])), \
             patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_approval_request",
                   side_effect=[RuntimeError("first fails"), mock_request]), \
             patch("runtime.pulse.pipeline_runner.persist_agent_bus_enqueue_approval_request"), \
             patch("runtime.pulse.pipeline_runner.validate_agent_bus_enqueue_approval_request",
                   return_value=mock_validation), \
             patch("runtime.pulse.pipeline_runner.enqueue_pulse_review_task",
                   return_value=enqueue_ret2), \
             patch("runtime.pulse.pipeline_runner._persist_error_result"):

            result = run_pulse_enqueue_pipeline(
                tmp_path,
                dry_run=False,
                operator_approved=True,
                gate_policy_defined=True,
                external_sender_allowance_present=True,
                duplicate_work_fingerprint_reviewed=True,
                run_at=_RUN_AT,
            )

        assert len(result.enqueue_results) == 2
        assert result.bus_error_count == 1
        assert result.enqueued_count == 1


# ── run_pulse_enqueue_pipeline: guard tests ───────────────────────────────────

class TestRunPipelineGuards:
    def test_invalid_recipient_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="default_recipient must be one of"):
            run_pulse_enqueue_pipeline(tmp_path, default_recipient="Unknown", run_at=_RUN_AT)

    def test_dry_run_is_default(self, tmp_path: Path) -> None:
        with patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
                   return_value=_empty_plan()):
            result = run_pulse_enqueue_pipeline(tmp_path, run_at=_RUN_AT)
        assert result.dry_run is True

    def test_governance_flags_always_false(self, tmp_path: Path) -> None:
        with patch("runtime.pulse.pipeline_runner.build_agent_bus_enqueue_plan",
                   return_value=_empty_plan()):
            result = run_pulse_enqueue_pipeline(tmp_path, run_at=_RUN_AT)

        assert result.candidate_apply_allowed is False
        assert result.canonical_writeback_allowed is False
        assert result.mutates_canonical_state is False
        assert result.second_datastore_write_allowed is False
        assert result.provider_or_connector_call_allowed is False
        assert result.schedule_activation_allowed is False
        assert result.review_response_ingest_allowed is False
