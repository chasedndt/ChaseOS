from __future__ import annotations

from dataclasses import replace
import inspect
import json
from pathlib import Path
import zipfile

import pytest

import runtime.pulse.post_completion_hardening as hardening_module
from runtime.pulse.bus_enqueue import PulseAgentBusEnqueueResult
from runtime.pulse.bus_enqueue_evidence import PulseAgentBusEnqueueEvidenceRecord
from runtime.pulse.card_schema import EvidenceRef, PulseCard, PulseDeck, RecommendedAction
from runtime.pulse.post_completion_hardening import (
    CHECK_STATUS_FAIL,
    CHECK_STATUS_NOT_APPLICABLE,
    CHECK_STATUS_PASS,
    HARDENING_STATUS_FAIL,
    HARDENING_STATUS_PASS,
    PulsePostCompletionHardeningReport,
    build_pulse_post_completion_hardening_report,
)
from runtime.pulse.multi_audience_decks import build_pulse_multi_audience_decks
from runtime.pulse.renderer_json import render_deck_json
from runtime.pulse.review_decision_log import (
    DECISION_FOLLOWUP_SIGNALS,
    PulseCandidateReviewDecision,
    persist_review_decision,
)


def _write_user_deck(vault: Path) -> None:
    deck_dir = vault / "07_LOGS" / "Pulse-Decks" / "users"
    deck_dir.mkdir(parents=True, exist_ok=True)
    deck = PulseDeck(
        deck_id="pulse-user-hardening-proof",
        audience="user",
        generated_at="2026-05-02T15:00:00+01:00",
        cards=[
            PulseCard(
                card_id="pulse-hardening-proof-001",
                audience="user",
                card_class="Today's Operating Brief",
                title="Pulse hardening proof card",
                summary="A valid user deck card for the local Pulse app plan.",
                generated_at="2026-05-02T15:00:00+01:00",
                evidence=[
                    EvidenceRef(
                        source_path="06_AGENTS/ChaseOS-Pulse-Phase10-UI-Proof.md",
                        source_type="proof_doc",
                        summary="Pulse local UI proof exists.",
                        trust_label="repo-observed",
                    )
                ],
                recommended_actions=[
                    RecommendedAction(
                        action_id="review",
                        label="Review hardening report",
                        action_type="review",
                        requires_operator_approval=False,
                    )
                ],
                urgency=2,
                confidence=0.9,
            )
        ],
    )
    (deck_dir / "2026-05-02-user-pulse.json").write_text(
        render_deck_json(deck),
        encoding="utf-8",
    )


def _write_fake_pulse_workbook(vault: Path) -> None:
    workbook_path = (
        vault
        / "99_ARCHIVE"
        / "Reporting"
        / "ChaseOS_RnD_Canonical_Full_2026-04-28.xlsx"
    )
    workbook_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(workbook_path, "w") as archive:
        archive.writestr(
            "xl/sharedStrings.xml",
            "<sst><si><t>FR-028 F176 F198 FIT-132 FIT-139 CH-1005 ChaseOS Pulse</t></si></sst>",
        )


def _write_complete_backend_chain(vault: Path) -> None:
    candidate_id = "feedback-candidate-hardening-001"
    request_id = "pulse-bus-enqueue-approval-hardening-001"
    evidence = PulseAgentBusEnqueueEvidenceRecord(
        evidence_id="pulse-bus-enqueue-evidence-hardening-001",
        request_id=request_id,
        created_at="2026-05-02T15:01:00+01:00",
        reviewer="Hermes-Optimus",
        operator_enqueue_approval_present=True,
        gate_policy_defined=True,
        external_sender_allowance_present=True,
        duplicate_work_fingerprint_reviewed=True,
        evidence_note="operator-approval:test-hardening-chain",
        gate_policy_ref="06_AGENTS/Pulse-Feedback-Policy.md#next-pass",
        external_sender_allowance_ref="HERMES.md#current-local-truth",
        duplicate_review_ref="07_LOGS/Agent-Activity/test-pulse-duplicate-review.md",
    )
    evidence_path = (
        vault
        / "07_LOGS"
        / "Pulse-Decks"
        / "agent-bus-enqueue-evidence"
        / "2026-05-02-agent-bus-enqueue-evidence.jsonl"
    )
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence.to_dict(), sort_keys=True) + "\n",
        encoding="utf-8",
    )

    enqueue_result = PulseAgentBusEnqueueResult(
        result_id="pulse-bus-enqueue-result-hardening-001",
        validation_id="pulse-bus-approval-validation-hardening-001",
        request_id=request_id,
        candidate_id=candidate_id,
        candidate_kind="feedback",
        recipient="Hermes",
        work_fingerprint=f"pulse-candidate-review:feedback:{candidate_id}",
        result_status="enqueued",
        enqueued=True,
        enqueued_at="2026-05-02T15:02:00+01:00",
        task_id="task-hardening-001",
        reason="Task created on Agent Bus.",
    )
    enqueue_path = (
        vault
        / "07_LOGS"
        / "Pulse-Decks"
        / "agent-bus-enqueue-results"
        / "2026-05-02-enqueue-results.jsonl"
    )
    enqueue_path.parent.mkdir(parents=True, exist_ok=True)
    enqueue_path.write_text(
        json.dumps(enqueue_result.to_dict(), sort_keys=True) + "\n",
        encoding="utf-8",
    )

    decision = PulseCandidateReviewDecision(
        decision_id="pulse-review-decision-hardening-001",
        candidate_id=candidate_id,
        candidate_kind="feedback",
        decision_type="accept_for_future_ranking",
        reviewer="Hermes",
        followup_signals=DECISION_FOLLOWUP_SIGNALS["accept_for_future_ranking"],
    )
    persist_review_decision(vault, decision)

    registry_path = (
        vault
        / "07_LOGS"
        / "Pulse-Decks"
        / "apply-registry"
        / "applied-decisions.json"
    )
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps({"applied_decision_ids": [decision.decision_id]}),
        encoding="utf-8",
    )


def _write_proof_docs(vault: Path) -> None:
    agents_dir = vault / "06_AGENTS"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "ChaseOS-Pulse-Post-Apply-Truth-State-Audit.md").write_text(
        "# Post Apply Audit\n\nStatus: PASS\n",
        encoding="utf-8",
    )
    (agents_dir / "ChaseOS-Pulse-RnD-Workbook-Update-Approval.md").write_text(
        "# R&D Workbook Approval\n\nStatus: APPROVED PREVIOUSLY\n",
        encoding="utf-8",
    )
    (agents_dir / "ChaseOS-Pulse-Native-Schedule-Activation-Catchup-Proof.md").write_text(
        "# Native Schedule Proof\n\nStatus: PROOF ONLY - NO SCHEDULE ACTIVATION\n",
        encoding="utf-8",
    )
    (agents_dir / "ChaseOS-Pulse-Phase10-UI-Proof.md").write_text(
        "# Phase 10 UI Proof\n\nStatus: LOCAL UI FOOTHOLD COMPLETE\n",
        encoding="utf-8",
    )
    shell_dir = vault / "runtime" / "studio" / "shell"
    shell_dir.mkdir(parents=True, exist_ok=True)
    (shell_dir / "api.py").write_text(
        "# test evidence only\n",
        encoding="utf-8",
    )


def _write_schedule_manifests(vault: Path) -> None:
    manifest_dir = vault / "runtime" / "schedules" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "chaseos_pulse_daily.yaml").write_text(
        "\n".join(
            [
                "schedule_id: chaseos_pulse_daily",
                "owner: chaseos",
                "enabled: false",
                "activation_state: planned",
                "schedule_owner: chaseos",
                "external_runtime_owner: false",
                "openclaw_cron_owner: false",
                "windows_task_scheduler_owner: false",
                "canonical_writeback_enabled: false",
                "external_connectors_enabled: false",
                "unrestricted_browsing_enabled: false",
            ]
        ),
        encoding="utf-8",
    )
    (manifest_dir / "hermes_runtime_pulse.yaml").write_text(
        "\n".join(
            [
                "schedule_id: hermes_runtime_pulse",
                "owner: chaseos",
                "enabled: false",
                "activation_state: planned",
                "schedule_owner: chaseos",
                "runtime_target: hermes",
                "external_runtime_owner: false",
                "hermes_owner: false",
                "openclaw_cron_owner: false",
                "canonical_writeback_enabled: false",
                "external_connectors_enabled: false",
                "unrestricted_browsing_enabled: false",
            ]
        ),
        encoding="utf-8",
    )


def _make_complete_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    _write_user_deck(vault)
    _write_complete_backend_chain(vault)
    _write_proof_docs(vault)
    _write_fake_pulse_workbook(vault)
    _write_schedule_manifests(vault)
    build_pulse_multi_audience_decks(
        vault,
        generated_at="2026-05-02T15:05:00+01:00",
        slug_prefix="2026-05-02-hardening-test",
        write=True,
    )
    return vault


def _path_snapshot(vault: Path) -> list[str]:
    return sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*"))


def test_module_does_not_import_writers_or_runtime_dispatchers() -> None:
    source = inspect.getsource(hardening_module)
    forbidden_tokens = (
        "enqueue_pulse_review_task",
        "apply_reviewed_candidates",
        "run_pulse_review_ingest",
        "persist_feedback_candidate",
        "persist_review_decision(",
        "create_task",
        "update_task_status",
        "claim_task",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_post_completion_hardening_passes_for_complete_local_lane(tmp_path: Path) -> None:
    vault = _make_complete_vault(tmp_path)

    report = build_pulse_post_completion_hardening_report(
        vault,
        generated_at="2026-05-02T15:10:00+01:00",
    )

    assert report.hardening_status == HARDENING_STATUS_PASS
    assert report.current_pulse_v1_complete is True
    assert report.required_check_count == report.passed_required_check_count
    assert report.read_only is True
    assert report.writes_performed is False
    assert report.agent_bus_task_write_allowed is False
    assert report.schedule_activation_allowed is False
    assert report.canonical_writeback_allowed is False
    assert report.rd_workbook_update_allowed is False
    statuses = {check.check_id: check.status for check in report.checks}
    assert statuses["pulse_completion_status"] == CHECK_STATUS_PASS
    assert statuses["pulse_deck_app_boundary"] == CHECK_STATUS_PASS
    assert statuses["daily_pulse_schedule_manifest_boundary"] == CHECK_STATUS_PASS
    assert statuses["hermes_pulse_schedule_manifest_boundary"] == CHECK_STATUS_PASS
    assert statuses["openflow_pulse_schedule_manifest_boundary"] == CHECK_STATUS_NOT_APPLICABLE


def test_post_completion_hardening_does_not_write(tmp_path: Path) -> None:
    vault = _make_complete_vault(tmp_path)
    before = _path_snapshot(vault)

    build_pulse_post_completion_hardening_report(vault)

    assert _path_snapshot(vault) == before


def test_post_completion_hardening_reports_schedule_manifest_gap(tmp_path: Path) -> None:
    vault = _make_complete_vault(tmp_path)
    daily_manifest = vault / "runtime" / "schedules" / "manifests" / "chaseos_pulse_daily.yaml"
    daily_manifest.write_text("schedule_id: chaseos_pulse_daily\nowner: external\n", encoding="utf-8")

    report = build_pulse_post_completion_hardening_report(vault)
    schedule_check = next(
        check for check in report.checks if check.check_id == "daily_pulse_schedule_manifest_boundary"
    )

    assert report.hardening_status == HARDENING_STATUS_FAIL
    assert schedule_check.status == CHECK_STATUS_FAIL
    assert "owner: chaseos" in schedule_check.missing
    assert "enabled: false" in schedule_check.missing


def test_post_completion_hardening_rejects_authority_flags(tmp_path: Path) -> None:
    vault = _make_complete_vault(tmp_path)
    report = build_pulse_post_completion_hardening_report(vault)
    authority_flags = (
        "writes_performed",
        "agent_bus_task_write_allowed",
        "approval_grant_allowed",
        "approval_execution_allowed",
        "canonical_writeback_allowed",
        "memory_approval_allowed",
        "provider_or_connector_call_allowed",
        "runtime_dispatch_allowed",
        "schedule_activation_allowed",
        "rd_workbook_update_allowed",
    )

    for flag in authority_flags:
        with pytest.raises(ValueError):
            replace(report, **{flag: True}).validate()


def test_report_validate_rejects_incorrect_required_counts(tmp_path: Path) -> None:
    vault = _make_complete_vault(tmp_path)
    report = build_pulse_post_completion_hardening_report(vault)

    with pytest.raises(ValueError):
        PulsePostCompletionHardeningReport(
            generated_at=report.generated_at,
            hardening_status=report.hardening_status,
            current_pulse_v1_complete=report.current_pulse_v1_complete,
            required_check_count=report.required_check_count + 1,
            passed_required_check_count=report.passed_required_check_count,
            checks=report.checks,
        ).validate()
