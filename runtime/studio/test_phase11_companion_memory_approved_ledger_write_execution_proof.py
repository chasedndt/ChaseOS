"""Tests for Phase 11 companion memory approved ledger-write execution proof."""

from __future__ import annotations

import json
from pathlib import Path
import uuid

from runtime.studio.phase11_companion_memory_approved_ledger_write_execution_proof import (
    NEXT_RECOMMENDED_PASS,
    execute_phase11_companion_memory_approved_ledger_write_execution_proof,
)
from runtime.studio.phase11_companion_memory_ledger_write_approval_preview import (
    build_phase11_companion_memory_ledger_write_approval_preview,
)
from runtime.studio.service import StudioService, StudioServiceError
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
from runtime.studio.test_phase11_companion_memory_ledger_write_approval_preview import (
    _executed_source_proof,
)


def _queue_ledger_write_approval(root: Path) -> tuple[str, str, str]:
    source_approval_id, _source_digest = _executed_source_proof(root)
    preview = build_phase11_companion_memory_ledger_write_approval_preview(
        root,
        source_approval_id=source_approval_id,
    )
    digest = str(preview["digest_proof"]["ledger_write_approval_digest"])
    written = build_phase11_companion_memory_ledger_write_approval_preview(
        root,
        source_approval_id=source_approval_id,
        expected_ledger_write_approval_digest=digest,
        write_approval=True,
        operator_id="test",
    )
    return str(written["approval_record"]["approval_id"]), digest, source_approval_id


def _ledger_lines(root: Path) -> list[dict]:
    path = root / "07_LOGS" / "Companion-Memory" / "hermes" / "memory-ledger.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_approved_ledger_write_consumes_once_and_appends_real_jsonl_entry(tmp_path: Path) -> None:
    approval_id, digest, source_approval_id = _queue_ledger_write_approval(tmp_path)
    StudioService(tmp_path).approve(approval_id, reviewed_by="test")

    result = execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_ledger_write_approval_digest=digest,
        execute=True,
        operator_id="test",
    )

    approval_path = tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json"
    marker_path = tmp_path / result["exact_once_marker"]["marker_path"]
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    ledger_lines = _ledger_lines(tmp_path)

    assert result["ok"] is True
    assert result["surface"] == "phase11_companion_memory_approved_ledger_write_execution_proof"
    assert result["pass"] == "phase11-companion-memory-approved-ledger-write-execution-proof"
    assert result["summary"]["approval_consumed"] is True
    assert result["summary"]["approval_status_mutated"] is True
    assert result["summary"]["exact_once_marker_written"] is True
    assert result["summary"]["marker_reserved_before_ledger_append"] is True
    assert result["summary"]["memory_ledger_written"] is True
    assert result["summary"]["memory_write_executed"] is True
    assert result["summary"]["memory_root_created"] is True
    assert result["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert result["digest_proof"]["ledger_write_approval_digest_matched"] is True
    assert result["ledger"]["target_path"] == "07_LOGS/Companion-Memory/hermes/memory-ledger.jsonl"
    assert result["ledger"]["entry_written"] is True
    assert len(ledger_lines) == 1
    assert ledger_lines[0]["source_approval_id"] == source_approval_id
    assert ledger_lines[0]["ledger_write_performed"] is True
    assert ledger_lines[0]["ledger_write_approval_id"] == approval_id
    assert ledger_lines[0]["ledger_write_approval_digest"] == digest
    assert ledger_lines[0]["trust_state"] == "raw"
    assert ledger_lines[0]["canonical"] is False
    assert ledger_lines[0]["authoritative"] is False
    assert ledger_lines[0]["provider_call_performed"] is False
    assert ledger_lines[0]["runtime_dispatch_performed"] is False
    assert ledger_lines[0]["agent_bus_task_written"] is False
    assert marker_payload["status"] == "executed"
    assert marker_payload["approval_id"] == approval_id
    assert marker_payload["marker_reserved_before_ledger_append"] is True
    assert marker_payload["ledger_entry_written"] is True
    assert approval_payload["status"] == "executed"
    assert approval_payload["execution_status"] == "completed"
    assert approval_payload["result_action_id"] == result["execution_record"]["execution_id"]
    assert approval_payload["action_spec"]["metadata"][
        "phase11_companion_memory_approved_ledger_write_execution_proof"
    ] is True
    for item in result["evidence_outputs"].values():
        assert (tmp_path / item["path"]).is_file()
    assert Path(tmp_path / result["audit_record"]["audit_record_path"]).is_file()


def test_pending_without_operator_statement_blocks_before_marker_or_ledger(tmp_path: Path) -> None:
    approval_id, digest, _source_approval_id = _queue_ledger_write_approval(tmp_path)

    result = execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_ledger_write_approval_digest=digest,
        execute=True,
        operator_id="test",
    )

    approval_payload = json.loads(
        (tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json").read_text(encoding="utf-8")
    )
    assert result["ok"] is False
    assert "operator_decision_not_approved" in result["blocked_reasons"]
    assert result["summary"]["memory_ledger_written"] is False
    assert approval_payload["status"] == "pending"
    assert not (tmp_path / "runtime" / "studio" / "approvals" / "_companion_memory_ledger_write_markers").exists()
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()


def test_pending_with_operator_statement_records_approval_then_writes_ledger(tmp_path: Path) -> None:
    approval_id, digest, _source_approval_id = _queue_ledger_write_approval(tmp_path)

    result = execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_ledger_write_approval_digest=digest,
        execute=True,
        operator_id="test",
        operator_approval_statement="operator approved companion memory ledger write",
    )

    approval_payload = json.loads(
        (tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json").read_text(encoding="utf-8")
    )
    assert result["ok"] is True
    assert result["summary"]["operator_approval_recorded_from_statement"] is True
    assert result["summary"]["memory_ledger_written"] is True
    assert approval_payload["reviewed_by"] == "test"
    assert approval_payload["reason"] == "operator approved companion memory ledger write"
    assert len(_ledger_lines(tmp_path)) == 1


def test_execute_flag_digest_mismatch_duplicate_and_ledger_collision_block_before_writes(tmp_path: Path) -> None:
    approval_id, digest, _source_approval_id = _queue_ledger_write_approval(tmp_path)
    StudioService(tmp_path).approve(approval_id, reviewed_by="test")

    missing_execute = execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_ledger_write_approval_digest=digest,
        execute=False,
        operator_id="test",
    )
    assert missing_execute["ok"] is False
    assert "execute_flag_required" in missing_execute["blocked_reasons"]

    mismatch = execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_ledger_write_approval_digest="0" * 64,
        execute=True,
        operator_id="test",
    )
    assert mismatch["ok"] is False
    assert "ledger_write_approval_digest_mismatch" in mismatch["blocked_reasons"]
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()

    first = execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_ledger_write_approval_digest=digest,
        execute=True,
        operator_id="test",
    )
    marker_bytes = (tmp_path / first["exact_once_marker"]["marker_path"]).read_bytes()
    duplicate = execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_ledger_write_approval_digest=digest,
        execute=True,
        operator_id="test",
    )
    assert first["ok"] is True
    assert duplicate["ok"] is False
    assert "exact_once_marker_already_present" in duplicate["blocked_reasons"]
    assert duplicate["summary"]["duplicate_blocked_before_ledger_append"] is True
    assert len(_ledger_lines(tmp_path)) == 1
    assert (tmp_path / first["exact_once_marker"]["marker_path"]).read_bytes() == marker_bytes

    collision_root = tmp_path.parent / f"collision-{uuid.uuid4().hex[:8]}"
    collision_root.mkdir()
    collision_approval_id, collision_digest, _collision_source_id = _queue_ledger_write_approval(collision_root)
    StudioService(collision_root).approve(collision_approval_id, reviewed_by="test")
    ledger_path = collision_root / "07_LOGS" / "Companion-Memory" / "hermes" / "memory-ledger.jsonl"
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_text("{not-json}\n", encoding="utf-8")
    collision = execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        collision_root,
        approval_id=collision_approval_id,
        expected_ledger_write_approval_digest=collision_digest,
        execute=True,
        operator_id="test",
    )
    assert collision["ok"] is False
    assert any(str(item).startswith("existing_ledger_line_malformed") for item in collision["blocked_reasons"])
    assert not (
        collision_root
        / "runtime"
        / "studio"
        / "approvals"
        / "_companion_memory_ledger_write_markers"
        / f"{collision_approval_id}.json"
    ).exists()


def test_missing_approval_and_generic_studio_service_execution_remain_blocked(tmp_path: Path) -> None:
    missing = execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        tmp_path,
        approval_id="missing",
        expected_ledger_write_approval_digest="0" * 64,
        execute=True,
    )
    assert missing["ok"] is False
    assert "approval_request_not_found" in missing["blocked_reasons"]
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()

    approval_id, _digest, _source_approval_id = _queue_ledger_write_approval(tmp_path)
    service = StudioService(tmp_path)
    service.approve(approval_id, reviewed_by="test")

    try:
        service.execute_approved(approval_id)
    except StudioServiceError as exc:
        error = str(exc)
    else:  # pragma: no cover
        error = ""

    approval_payload = json.loads(
        (tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json").read_text(encoding="utf-8")
    )
    assert "ledger-write" in error
    assert approval_payload["status"] == "approved"
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()


def test_api_registry_and_chat_panel_expose_approved_ledger_write_executor(tmp_path: Path) -> None:
    approval_id, digest, _source_approval_id = _queue_ledger_write_approval(tmp_path)

    api_status = StudioAPI(tmp_path).execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        approval_id=approval_id,
        expected_ledger_write_approval_digest=digest,
        execute=True,
        operator_id="test",
        operator_approval_statement="operator approved companion memory ledger write",
    )
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next(panel for panel in registry["panels"] if panel["id"] == "chat")
    panel = StudioAPI(tmp_path).get_phase11_chat_panel_contract("/memory ledger execute direct progress")

    assert api_status["ok"] is True
    assert api_status["data"]["summary"]["memory_ledger_written"] is True
    assert "execute_phase11_companion_memory_approved_ledger_write_execution_proof" in (
        chat_panel.get("api_methods") or []
    )
    assert registry["readiness"]["phase11_companion_memory_approved_ledger_write_execution_proof_ready"] is True
    assert registry["readiness"]["phase11_companion_memory_real_ledger_write_approval_gated"] is True
    assert panel["data"]["companion_memory_approved_ledger_write_execution_proof"]["surface"] == (
        "phase11_companion_memory_approved_ledger_write_execution_proof"
    )
    posture = panel["data"]["companion_memory_approved_ledger_write_execution_posture"]
    assert posture["approved_ledger_write_executor_visible"] is True
    assert posture["memory_ledger_write_allowed_through_explicit_executor"] is True
    assert posture["ambient_chat_ledger_write_allowed"] is False
