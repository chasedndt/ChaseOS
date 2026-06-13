"""Tests for Phase 11 companion memory ledger-write approval preview."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_companion_memory_approval_preview import (
    build_phase11_companion_memory_approval_preview,
)
from runtime.studio.phase11_companion_memory_approved_execution_proof import (
    execute_phase11_companion_memory_approved_execution_proof,
)
from runtime.studio.phase11_companion_memory_ledger_write_approval_preview import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_companion_memory_ledger_write_approval_preview,
)
from runtime.studio.service import StudioService, StudioServiceError
from runtime.studio.test_phase11_operator_companion_direction import _files, _seed_registry
from runtime.studio.test_phase11_operator_companion_direction_answers import _seed_direction


CONTENT = "Operator prefers direct progress updates during long implementation passes."


def _seed(root: Path) -> None:
    _seed_registry(root)
    _seed_direction(root)


def _executed_source_proof(root: Path, *, content: str = CONTENT) -> tuple[str, str]:
    _seed(root)
    preview = build_phase11_companion_memory_approval_preview(
        root,
        companion_id="hermes",
        memory_class="preference",
        content=content,
        source_surface="phase11-chat",
        source_event_id="ledger-write-test",
    )
    digest = str(preview["digest_proof"]["memory_approval_digest"])
    written = build_phase11_companion_memory_approval_preview(
        root,
        companion_id="hermes",
        memory_class="preference",
        content=content,
        source_surface="phase11-chat",
        source_event_id="ledger-write-test",
        expected_memory_approval_digest=digest,
        write_approval=True,
        operator_id="test",
    )
    approval_id = str(written["approval_record"]["approval_id"])
    executed = execute_phase11_companion_memory_approved_execution_proof(
        root,
        approval_id=approval_id,
        expected_memory_approval_digest=digest,
        execute=True,
        operator_id="test",
        operator_approval_statement="operator approved companion memory proof execution",
    )
    assert executed["ok"] is True
    return approval_id, digest


def test_ledger_write_approval_preview_uses_executed_proof_without_memory_writes(tmp_path: Path) -> None:
    source_approval_id, source_digest = _executed_source_proof(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_companion_memory_ledger_write_approval_preview(
        tmp_path,
        source_approval_id=source_approval_id,
    )
    after = _files(tmp_path)

    approval = payload["future_approval_packet_preview"]
    digest = payload["digest_proof"]["ledger_write_approval_digest"]
    entry = payload["ledger_entry_preview"]["entry"]

    assert payload["ok"] is True
    assert payload["surface"] == "phase11_companion_memory_ledger_write_approval_preview"
    assert payload["pass"] == "phase11-companion-memory-ledger-write-approval-preview"
    assert payload["summary"]["source_approval_id"] == source_approval_id
    assert payload["summary"]["ledger_write_approval_preview_ready"] is True
    assert payload["summary"]["approval_request_created"] is False
    assert payload["summary"]["memory_ledger_written"] is False
    assert payload["summary"]["memory_root_created"] is False
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert payload["source_proof"]["memory_approval_digest"] == source_digest
    assert entry["companion_id"] == "hermes"
    assert entry["memory_class"] == "preference"
    assert entry["source_approval_id"] == source_approval_id
    assert entry["source_memory_approval_digest"] == source_digest
    assert entry["ledger_write_performed"] is False
    assert approval["approval_request_created"] is False
    assert approval["action_spec_preview"]["action_type"] == "companion_memory_ledger_append"
    assert approval["action_spec_preview"]["target_path"] == "07_LOGS/Companion-Memory/hermes/memory-ledger.jsonl"
    assert approval["action_spec_preview"]["metadata"]["phase11_companion_memory_ledger_write_approval_digest"] == digest
    assert payload["authority"]["approval_queue_write_allowed_with_digest"] is True
    assert payload["authority"]["memory_ledger_write_allowed"] is False
    assert payload["authority"]["real_memory_ledger_read_allowed"] is False
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()
    assert before == after


def test_ledger_write_approval_write_creates_pending_approval_only(tmp_path: Path) -> None:
    source_approval_id, _source_digest = _executed_source_proof(tmp_path)
    preview = build_phase11_companion_memory_ledger_write_approval_preview(
        tmp_path,
        source_approval_id=source_approval_id,
    )
    digest = preview["digest_proof"]["ledger_write_approval_digest"]

    payload = build_phase11_companion_memory_ledger_write_approval_preview(
        tmp_path,
        source_approval_id=source_approval_id,
        expected_ledger_write_approval_digest=digest,
        write_approval=True,
        operator_id="test-operator",
    )

    approval_path = tmp_path / payload["approval_record"]["approval_path"]
    audit_path = tmp_path / payload["audit_record"]["audit_record_path"]
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    audit = audit_path.read_text(encoding="utf-8")

    assert payload["ok"] is True
    assert payload["status"].startswith("COMPLETE / APPROVAL-QUEUE-WRITE")
    assert payload["summary"]["write_approval_requested"] is True
    assert payload["summary"]["approval_request_created"] is True
    assert payload["summary"]["approval_status"] == "pending"
    assert payload["summary"]["memory_ledger_written"] is False
    assert payload["summary"]["memory_root_created"] is False
    assert approval_path.exists()
    assert audit_path.exists()
    assert approval["status"] == "pending"
    assert approval["action_spec"]["action_type"] == "companion_memory_ledger_append"
    assert approval["action_spec"]["metadata"]["phase11_companion_memory_ledger_write_approval_preview"] is True
    assert approval["action_spec"]["metadata"]["phase11_companion_memory_ledger_write_approval_digest"] == digest
    assert "memory_ledger_written: false" in audit
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()


def test_ledger_write_approval_blocks_mismatch_missing_proof_and_duplicate(tmp_path: Path) -> None:
    missing = build_phase11_companion_memory_ledger_write_approval_preview(tmp_path)
    assert missing["ok"] is False
    assert "no_executed_companion_memory_proof_found" in missing["blocked_reasons"]

    source_approval_id, _source_digest = _executed_source_proof(tmp_path)
    before_mismatch = _files(tmp_path)
    mismatch = build_phase11_companion_memory_ledger_write_approval_preview(
        tmp_path,
        source_approval_id=source_approval_id,
        expected_ledger_write_approval_digest="wrong",
        write_approval=True,
    )
    after_mismatch = _files(tmp_path)
    assert mismatch["ok"] is False
    assert "expected_ledger_write_approval_digest_mismatch" in mismatch["blocked_reasons"]
    assert mismatch["summary"]["approval_request_created"] is False
    assert before_mismatch == after_mismatch

    preview = build_phase11_companion_memory_ledger_write_approval_preview(tmp_path, source_approval_id=source_approval_id)
    digest = preview["digest_proof"]["ledger_write_approval_digest"]
    first = build_phase11_companion_memory_ledger_write_approval_preview(
        tmp_path,
        source_approval_id=source_approval_id,
        expected_ledger_write_approval_digest=digest,
        write_approval=True,
    )
    second = build_phase11_companion_memory_ledger_write_approval_preview(
        tmp_path,
        source_approval_id=source_approval_id,
        expected_ledger_write_approval_digest=digest,
        write_approval=True,
    )
    assert first["ok"] is True
    assert second["ok"] is False
    assert "approval_queue_request_already_exists_for_digest" in second["blocked_reasons"]


def test_generic_studio_execution_blocks_ledger_write_approval(tmp_path: Path) -> None:
    source_approval_id, _source_digest = _executed_source_proof(tmp_path)
    preview = build_phase11_companion_memory_ledger_write_approval_preview(
        tmp_path,
        source_approval_id=source_approval_id,
    )
    digest = preview["digest_proof"]["ledger_write_approval_digest"]
    written = build_phase11_companion_memory_ledger_write_approval_preview(
        tmp_path,
        source_approval_id=source_approval_id,
        expected_ledger_write_approval_digest=digest,
        write_approval=True,
    )
    approval_id = written["approval_record"]["approval_id"]
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


def test_api_registry_and_chat_panel_expose_ledger_write_approval_preview(tmp_path: Path) -> None:
    source_approval_id, _source_digest = _executed_source_proof(tmp_path)

    from runtime.studio.phase11_chat_panel_contract import build_phase11_chat_panel_contract
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_companion_memory_ledger_write_approval_preview(source_approval_id)
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}
    panel = build_phase11_chat_panel_contract(tmp_path, message="/memory ledger approve direct progress")

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_companion_memory_ledger_write_approval_preview"
    assert api_status["data"]["summary"]["ledger_write_approval_preview_ready"] is True
    assert "get_phase11_companion_memory_ledger_write_approval_preview" in (chat_panel.get("api_methods") or [])
    assert "request_phase11_companion_memory_ledger_write_approval" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_companion_memory_ledger_write_approval_preview_ready"] is True
    assert readiness["phase11_companion_memory_ledger_write_approval_queue_write_gated"] is True
    assert readiness["phase11_companion_memory_real_ledger_write_blocked"] is True
    assert panel["companion_memory_ledger_write_approval_preview"]["surface"] == (
        "phase11_companion_memory_ledger_write_approval_preview"
    )
    posture = panel["companion_memory_ledger_write_approval_posture"]
    assert posture["ledger_write_approval_preview_visible"] is True
    assert posture["approval_queue_write_allowed_after_digest"] is True
    assert posture["memory_ledger_write_allowed"] is False
    assert posture["real_memory_ledger_read_allowed"] is False
    assert panel["readiness"]["companion_memory_ledger_write_approval_preview_ready"] is True
