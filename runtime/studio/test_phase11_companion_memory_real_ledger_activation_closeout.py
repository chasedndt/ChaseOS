"""Tests for Phase 11 companion-memory real ledger activation closeout."""

from __future__ import annotations

from pathlib import Path
import uuid

from runtime.studio.phase11_companion_memory_approved_ledger_write_execution_proof import (
    execute_phase11_companion_memory_approved_ledger_write_execution_proof,
)
from runtime.studio.phase11_companion_memory_real_ledger_activation_closeout import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_companion_memory_real_ledger_activation_closeout,
)
from runtime.studio.test_phase11_companion_memory_approved_ledger_write_execution_proof import (
    _queue_ledger_write_approval,
)
from runtime.studio.test_phase11_operator_companion_direction import _files


def _execute_real_ledger(root: Path) -> tuple[str, str, dict]:
    approval_id, digest, _source_approval_id = _queue_ledger_write_approval(root)
    executed = execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        root,
        approval_id=approval_id,
        expected_ledger_write_approval_digest=digest,
        execute=True,
        operator_id="test",
        operator_approval_statement="operator approved companion memory ledger write",
    )
    assert executed["ok"] is True
    return approval_id, digest, executed


def test_real_ledger_activation_closeout_verifies_approval_marker_evidence_and_read_model(tmp_path: Path) -> None:
    approval_id, digest, executed = _execute_real_ledger(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_companion_memory_real_ledger_activation_closeout(
        tmp_path,
        approval_id=approval_id,
    )
    after = _files(tmp_path)

    assert payload["ok"] is True
    assert payload["surface"] == "phase11_companion_memory_real_ledger_activation_closeout"
    assert payload["pass"] == "phase11-companion-memory-real-ledger-activation-closeout"
    assert payload["status"] == "COMPLETE / APPROVAL-CONSUMED / REAL LEDGER ACTIVE / VERIFIED"
    assert payload["read_only"] is True
    assert payload["summary"]["real_ledger_active"] is True
    assert payload["summary"]["approval_id"] == approval_id
    assert payload["summary"]["approval_consumed"] is True
    assert payload["summary"]["approval_status"] == "executed"
    assert payload["summary"]["approval_execution_status"] == "completed"
    assert payload["summary"]["exact_once_marker_exists"] is True
    assert payload["summary"]["exact_once_marker_executed"] is True
    assert payload["summary"]["marker_reserved_before_ledger_append"] is True
    assert payload["summary"]["evidence_outputs_present"] is True
    assert payload["summary"]["real_ledger_record_found"] is True
    assert payload["summary"]["memory_root_exists"] is True
    assert payload["summary"]["ledger_file_exists"] is True
    assert payload["summary"]["ledger_line_count"] == 1
    assert payload["summary"]["duplicate_execution_would_block_before_append"] is True
    assert payload["summary"]["provider_call_performed"] is False
    assert payload["summary"]["runtime_dispatch_performed"] is False
    assert payload["summary"]["agent_bus_task_written"] is False
    assert payload["summary"]["canonical_mutation_performed"] is False
    assert payload["summary"]["memory_snapshot_unchanged"] is True
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert payload["selected_record"]["ledger_write_approval_id"] == approval_id
    assert payload["selected_record"]["ledger_write_approval_digest"] == digest
    assert payload["selected_record"]["ledger_write_execution_id"] == executed["execution_record"]["execution_id"]
    assert payload["selected_record"]["source_type"] == "ledger_entry"
    assert payload["selected_record"]["proof_status"] == "ledger_written"
    assert payload["selected_record"]["trust_state"] == "raw"
    assert payload["selected_record"]["canonical"] is False
    assert payload["selected_record"]["authoritative"] is False
    assert payload["approval_record"]["approval_exists"] is True
    assert payload["approval_record"]["result_action_id"] == executed["execution_record"]["execution_id"]
    assert payload["exact_once_marker"]["status"] == "executed"
    assert payload["duplicate_guard"]["duplicate_execution_would_block_before_append"] is True
    assert payload["readiness"]["companion_memory_real_ledger_active"] is True
    assert payload["authority"]["real_companion_memory_read_allowed"] is True
    assert payload["authority"]["memory_ledger_write_allowed"] is False
    assert payload["authority"]["approval_consumption_allowed"] is False
    assert payload["authority"]["provider_calls_allowed"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
    assert before == after


def test_real_ledger_activation_closeout_blocks_when_ledger_absent(tmp_path: Path) -> None:
    before = _files(tmp_path)

    payload = build_phase11_companion_memory_real_ledger_activation_closeout(
        tmp_path,
        approval_id="missing",
    )
    after = _files(tmp_path)

    assert payload["ok"] is False
    assert payload["status"] == "BLOCKED / REAL LEDGER ACTIVATION / INCOMPLETE"
    assert "real_ledger_record_not_found" in payload["blocked_reasons"]
    assert "approval_artifact_not_found" in payload["blocked_reasons"]
    assert "exact_once_marker_not_found" in payload["blocked_reasons"]
    assert payload["summary"]["real_ledger_active"] is False
    assert payload["summary"]["real_ledger_record_found"] is False
    assert payload["authority"]["memory_ledger_write_allowed"] is False
    assert before == after


def test_real_ledger_activation_closeout_blocks_missing_marker_or_evidence(tmp_path: Path) -> None:
    approval_id, _digest, _executed = _execute_real_ledger(tmp_path)
    ok_payload = build_phase11_companion_memory_real_ledger_activation_closeout(tmp_path, approval_id=approval_id)
    marker_path = tmp_path / ok_payload["exact_once_marker"]["marker_path"]
    evidence_path = tmp_path / ok_payload["evidence_outputs"]["execution_evidence"]["path"]

    marker_path.unlink()
    missing_marker = build_phase11_companion_memory_real_ledger_activation_closeout(tmp_path, approval_id=approval_id)
    assert missing_marker["ok"] is False
    assert "exact_once_marker_not_found" in missing_marker["blocked_reasons"]

    second_root = Path(".pytest_tmp_env") / f"cml-closeout-second-{uuid.uuid4().hex[:8]}"
    approval_id_2, _digest_2, _executed_2 = _execute_real_ledger(second_root)
    second_payload = build_phase11_companion_memory_real_ledger_activation_closeout(
        second_root,
        approval_id=approval_id_2,
    )
    second_evidence = second_root / second_payload["evidence_outputs"]["execution_evidence"]["path"]
    second_evidence.unlink()
    missing_evidence = build_phase11_companion_memory_real_ledger_activation_closeout(
        second_root,
        approval_id=approval_id_2,
    )
    assert evidence_path.name.endswith("-execution-evidence.json")
    assert missing_evidence["ok"] is False
    assert "execution_evidence_missing" in missing_evidence["blocked_reasons"]


def test_api_registry_and_chat_panel_expose_real_ledger_activation_closeout(tmp_path: Path) -> None:
    approval_id, _digest, _executed = _execute_real_ledger(tmp_path)

    from runtime.studio.phase11_chat_panel_contract import build_phase11_chat_panel_contract
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_companion_memory_real_ledger_activation_closeout(
        approval_id=approval_id,
    )
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}
    panel = build_phase11_chat_panel_contract(tmp_path, message=f"/memory ledger {approval_id}")

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_companion_memory_real_ledger_activation_closeout"
    assert api_status["data"]["summary"]["real_ledger_active"] is True
    assert "get_phase11_companion_memory_real_ledger_activation_closeout" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_companion_memory_real_ledger_activation_closeout_ready"] is True
    assert readiness["phase11_companion_memory_real_ledger_activation_verifies_state"] is True
    assert panel["companion_memory_real_ledger_activation_closeout"]["surface"] == (
        "phase11_companion_memory_real_ledger_activation_closeout"
    )
    posture = panel["companion_memory_real_ledger_activation_posture"]
    assert posture["real_ledger_activation_closeout_visible"] is True
    assert posture["real_ledger_active"] is True
    assert posture["memory_ledger_write_allowed"] is False
    assert panel["readiness"]["companion_memory_real_ledger_activation_closeout_ready"] is True
