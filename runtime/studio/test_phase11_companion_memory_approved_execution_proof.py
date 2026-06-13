"""Tests for Phase 11 companion memory approved execution proof."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_companion_memory_approval_preview import (
    build_phase11_companion_memory_approval_preview,
)
from runtime.studio.phase11_companion_memory_approved_execution_proof import (
    NEXT_RECOMMENDED_PASS,
    execute_phase11_companion_memory_approved_execution_proof,
)
from runtime.studio.service import StudioService, StudioServiceError
from runtime.studio.shell.api import StudioAPI
from runtime.studio.shell.panel_registry import build_native_shell_panel_registry
from runtime.studio.test_phase11_operator_companion_direction import _seed_registry
from runtime.studio.test_phase11_operator_companion_direction_answers import _seed_direction


CONTENT = "Operator prefers direct progress updates during long implementation passes."


def _queue_memory_approval(root: Path, *, content: str = CONTENT) -> tuple[str, str]:
    _seed_registry(root)
    _seed_direction(root)
    preview = build_phase11_companion_memory_approval_preview(
        root,
        companion_id="hermes",
        memory_class="preference",
        content=content,
        source_surface="phase11-chat",
    )
    digest = str(preview["digest_proof"]["memory_approval_digest"])
    written = build_phase11_companion_memory_approval_preview(
        root,
        companion_id="hermes",
        memory_class="preference",
        content=content,
        source_surface="phase11-chat",
        expected_memory_approval_digest=digest,
        write_approval=True,
        operator_id="test",
    )
    return str(written["approval_record"]["approval_id"]), digest


def test_approved_companion_memory_execution_consumes_once_and_writes_proof_only_outputs(tmp_path: Path) -> None:
    approval_id, digest = _queue_memory_approval(tmp_path)
    StudioService(tmp_path).approve(approval_id, reviewed_by="test")

    result = execute_phase11_companion_memory_approved_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_memory_approval_digest=digest,
        execute=True,
        operator_id="test",
    )

    approval_path = tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json"
    marker_path = tmp_path / result["exact_once_marker"]["marker_path"]
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    marker_payload = json.loads(marker_path.read_text(encoding="utf-8"))
    proof_outputs = result["proof_outputs"]

    assert result["ok"] is True
    assert result["surface"] == "phase11_companion_memory_approved_execution_proof"
    assert result["pass"] == "phase11-companion-memory-approved-execution-proof"
    assert result["summary"]["approval_consumed"] is True
    assert result["summary"]["approval_status_mutated"] is True
    assert result["summary"]["exact_once_marker_written"] is True
    assert result["summary"]["marker_reserved_before_outputs"] is True
    assert result["summary"]["proof_outputs_written"] is True
    assert result["summary"]["memory_ledger_written"] is False
    assert result["summary"]["memory_root_created"] is False
    assert result["summary"]["provider_call_performed"] is False
    assert result["summary"]["runtime_dispatch_performed"] is False
    assert result["summary"]["agent_bus_task_written"] is False
    assert result["summary"]["canonical_mutation_performed"] is False
    assert result["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert result["digest_proof"]["memory_approval_digest_matched"] is True
    assert marker_payload["status"] == "executed"
    assert marker_payload["approval_id"] == approval_id
    assert marker_payload["marker_reserved_before_outputs"] is True
    assert marker_payload["memory_ledger_written"] is False
    assert approval_payload["status"] == "executed"
    assert approval_payload["execution_status"] == "completed"
    assert approval_payload["result_action_id"] == result["execution_record"]["execution_id"]
    assert approval_payload["action_spec"]["metadata"]["phase11_companion_memory_execution_proof"] is True
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()
    for item in proof_outputs.values():
        assert (tmp_path / item["path"]).is_file()
    assert Path(tmp_path / result["audit_record"]["audit_record_path"]).is_file()


def test_pending_without_operator_statement_blocks_before_marker_outputs_or_memory(tmp_path: Path) -> None:
    approval_id, digest = _queue_memory_approval(tmp_path)

    result = execute_phase11_companion_memory_approved_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_memory_approval_digest=digest,
        execute=True,
        operator_id="test",
    )

    approval_payload = json.loads(
        (tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json").read_text(encoding="utf-8")
    )
    assert result["ok"] is False
    assert "operator_decision_not_approved" in result["blocked_reasons"]
    assert result["summary"]["proof_outputs_written"] is False
    assert result["summary"]["memory_ledger_written"] is False
    assert approval_payload["status"] == "pending"
    assert not (tmp_path / "runtime" / "studio" / "approvals" / "_companion_memory_execution_markers").exists()
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()


def test_pending_with_operator_statement_records_approval_then_consumes(tmp_path: Path) -> None:
    approval_id, digest = _queue_memory_approval(tmp_path)

    result = execute_phase11_companion_memory_approved_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_memory_approval_digest=digest,
        execute=True,
        operator_id="test",
        operator_approval_statement="operator approved companion memory proof execution",
    )

    approval_payload = json.loads(
        (tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json").read_text(encoding="utf-8")
    )
    assert result["ok"] is True
    assert result["summary"]["operator_approval_recorded_from_statement"] is True
    assert result["summary"]["approval_consumed"] is True
    assert approval_payload["reviewed_by"] == "test"
    assert approval_payload["reason"] == "operator approved companion memory proof execution"
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()


def test_execute_flag_digest_mismatch_duplicate_and_output_collision_block_before_writes(tmp_path: Path) -> None:
    approval_id, digest = _queue_memory_approval(tmp_path)
    StudioService(tmp_path).approve(approval_id, reviewed_by="test")

    missing_execute = execute_phase11_companion_memory_approved_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_memory_approval_digest=digest,
        execute=False,
        operator_id="test",
    )
    assert missing_execute["ok"] is False
    assert "execute_flag_required" in missing_execute["blocked_reasons"]

    mismatch = execute_phase11_companion_memory_approved_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_memory_approval_digest="0" * 64,
        execute=True,
        operator_id="test",
    )
    assert mismatch["ok"] is False
    assert "memory_approval_digest_mismatch" in mismatch["blocked_reasons"]
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()

    first = execute_phase11_companion_memory_approved_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_memory_approval_digest=digest,
        execute=True,
        operator_id="test",
    )
    marker_bytes = (tmp_path / first["exact_once_marker"]["marker_path"]).read_bytes()
    duplicate = execute_phase11_companion_memory_approved_execution_proof(
        tmp_path,
        approval_id=approval_id,
        expected_memory_approval_digest=digest,
        execute=True,
        operator_id="test",
    )
    assert first["ok"] is True
    assert duplicate["ok"] is False
    assert "exact_once_marker_already_present" in duplicate["blocked_reasons"]
    assert duplicate["summary"]["duplicate_blocked_before_outputs"] is True
    assert (tmp_path / first["exact_once_marker"]["marker_path"]).read_bytes() == marker_bytes

    collision_root = tmp_path / "collision"
    collision_root.mkdir()
    collision_approval_id, collision_digest = _queue_memory_approval(collision_root)
    StudioService(collision_root).approve(collision_approval_id, reviewed_by="test")
    collision_path = (
        collision_root
        / ".pytest_tmp_env"
        / "phase11-companion-memory-proof"
        / collision_approval_id
        / "proof-memory-record.json"
    )
    collision_path.parent.mkdir(parents=True, exist_ok=True)
    collision_path.write_text("{}\n", encoding="utf-8")
    collision = execute_phase11_companion_memory_approved_execution_proof(
        collision_root,
        approval_id=collision_approval_id,
        expected_memory_approval_digest=collision_digest,
        execute=True,
        operator_id="test",
    )
    assert collision["ok"] is False
    assert "future_proof_output_collision" in collision["blocked_reasons"]
    assert not (
        collision_root
        / "runtime"
        / "studio"
        / "approvals"
        / "_companion_memory_execution_markers"
        / f"{collision_approval_id}.json"
    ).exists()


def test_generic_studio_service_execution_remains_blocked_for_companion_memory(tmp_path: Path) -> None:
    approval_id, _digest = _queue_memory_approval(tmp_path)
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
    assert "companion memory" in error
    assert approval_payload["status"] == "approved"
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()


def test_api_registry_and_static_contract_expose_companion_memory_execution_proof(tmp_path: Path) -> None:
    approval_id, digest = _queue_memory_approval(tmp_path)

    api_status = StudioAPI(tmp_path).execute_phase11_companion_memory_approved_execution_proof(
        approval_id=approval_id,
        expected_memory_approval_digest=digest,
        execute=True,
        operator_id="test",
        operator_approval_statement="operator approved companion memory proof execution",
    )
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next(panel for panel in registry["panels"] if panel["id"] == "chat")

    assert api_status["ok"] is True
    assert api_status["data"]["summary"]["approval_consumed"] is True
    assert "execute_phase11_companion_memory_approved_execution_proof" in (chat_panel.get("api_methods") or [])
    assert registry["readiness"]["phase11_companion_memory_approved_execution_proof_ready"] is True
    assert registry["readiness"]["phase11_companion_memory_ledger_writes_blocked"] is True
