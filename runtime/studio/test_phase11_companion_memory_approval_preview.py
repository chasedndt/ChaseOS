"""Tests for Phase 11 companion memory approval preview and queue-write proof."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_companion_memory_approval_preview import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_companion_memory_approval_preview,
)
from runtime.studio.service import StudioService
from runtime.studio.test_phase11_operator_companion_direction import _files, _seed_registry
from runtime.studio.test_phase11_operator_companion_direction_answers import _seed_direction


def _seed(root: Path) -> None:
    _seed_registry(root)
    _seed_direction(root)


def _candidate() -> dict:
    return {
        "companion_id": "hermes",
        "memory_class": "preference",
        "content": "Operator prefers direct progress updates during long implementation passes.",
        "source_surface": "phase11-chat",
        "source_event_id": "test-event-001",
    }


def test_companion_memory_approval_preview_is_readonly_and_digest_bound(tmp_path: Path) -> None:
    _seed(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_companion_memory_approval_preview(tmp_path, candidate=_candidate())
    after = _files(tmp_path)

    approval = payload["future_approval_packet_preview"]
    digest = payload["digest_proof"]["memory_approval_digest"]

    assert payload["ok"] is True
    assert payload["pass"] == "phase11-companion-memory-approval-preview"
    assert payload["surface"] == "phase11_companion_memory_approval_preview"
    assert payload["summary"]["approval_preview_ready"] is True
    assert payload["summary"]["approval_request_created"] is False
    assert payload["summary"]["memory_file_written"] is False
    assert payload["summary"]["memory_write_executed"] is False
    assert payload["summary"]["approval_consumed"] is False
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert digest
    assert approval["approval_request_created"] is False
    assert approval["approval_id_preview"].endswith(digest[:16])
    assert approval["action_spec_preview"]["action_type"] == "companion_memory_write"
    assert approval["action_spec_preview"]["target_path"] == "07_LOGS/Companion-Memory/hermes/memory-ledger.jsonl"
    assert approval["action_spec_preview"]["metadata"]["phase11_companion_memory_approval_digest"] == digest
    assert payload["authority"]["approval_queue_write_allowed_with_digest"] is True
    assert payload["authority"]["approval_queue_write_performed"] is False
    assert payload["authority"]["memory_write_allowed"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
    assert before == after


def test_companion_memory_approval_write_creates_pending_approval_only(tmp_path: Path) -> None:
    _seed(tmp_path)
    preview = build_phase11_companion_memory_approval_preview(tmp_path, candidate=_candidate())
    digest = preview["digest_proof"]["memory_approval_digest"]

    payload = build_phase11_companion_memory_approval_preview(
        tmp_path,
        candidate=_candidate(),
        expected_memory_approval_digest=digest,
        write_approval=True,
        operator_id="test-operator",
    )

    approval_path = tmp_path / payload["approval_record"]["approval_path"]
    audit_path = tmp_path / payload["audit_record"]["audit_record_path"]
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    assert payload["ok"] is True
    assert payload["status"].startswith("COMPLETE / APPROVAL-QUEUE-WRITE")
    assert payload["summary"]["write_approval_requested"] is True
    assert payload["summary"]["approval_request_created"] is True
    assert payload["summary"]["approval_status"] == "pending"
    assert payload["summary"]["memory_file_written"] is False
    assert payload["summary"]["memory_write_executed"] is False
    assert payload["summary"]["approval_consumed"] is False
    assert approval_path.exists()
    assert audit_path.exists()
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()
    assert approval["status"] == "pending"
    assert approval["action_spec"]["action_type"] == "companion_memory_write"
    assert approval["action_spec"]["target_path"] == "07_LOGS/Companion-Memory/hermes/memory-ledger.jsonl"
    assert approval["action_spec"]["metadata"]["phase11_companion_memory_approval_digest"] == digest
    assert approval["action_spec"]["metadata"]["companion_memory_file_written"] is False
    assert audit["memory_approval_digest"] == digest
    assert audit["approval_execution_allowed"] is False
    assert audit["memory_file_written"] is False


def test_companion_memory_approval_write_requires_matching_digest_before_writes(tmp_path: Path) -> None:
    _seed(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_companion_memory_approval_preview(
        tmp_path,
        candidate=_candidate(),
        expected_memory_approval_digest="wrong",
        write_approval=True,
    )

    after = _files(tmp_path)
    assert payload["ok"] is False
    assert "expected_memory_approval_digest_mismatch" in payload["blocked_reasons"]
    assert payload["summary"]["approval_request_created"] is False
    assert payload["summary"]["approval_queue_writer_called"] is False
    assert before == after


def test_companion_memory_approval_preview_blocks_denied_candidate_without_writes(tmp_path: Path) -> None:
    _seed(tmp_path)
    candidate = {
        "companion_id": "hermes",
        "memory_class": "credential",
        "content": "api_key=example",
        "source_surface": "phase11-chat",
    }
    before = _files(tmp_path)

    payload = build_phase11_companion_memory_approval_preview(tmp_path, candidate=candidate, write_approval=True)

    after = _files(tmp_path)
    assert payload["ok"] is False
    assert "candidate_validation_failed" in payload["blocked_reasons"]
    assert "memory_class_denied" in payload["candidate_validation"]["blocked_reasons"]
    assert payload["summary"]["approval_request_created"] is False
    assert payload["summary"]["memory_file_written"] is False
    assert before == after


def test_companion_memory_approval_write_blocks_duplicate_digest_before_second_write(tmp_path: Path) -> None:
    _seed(tmp_path)
    preview = build_phase11_companion_memory_approval_preview(tmp_path, candidate=_candidate())
    digest = preview["digest_proof"]["memory_approval_digest"]

    first = build_phase11_companion_memory_approval_preview(
        tmp_path,
        candidate=_candidate(),
        expected_memory_approval_digest=digest,
        write_approval=True,
    )
    second = build_phase11_companion_memory_approval_preview(
        tmp_path,
        candidate=_candidate(),
        expected_memory_approval_digest=digest,
        write_approval=True,
    )

    approvals = list((tmp_path / StudioService.APPROVAL_DIR).glob("*.json"))
    assert first["ok"] is True
    assert second["ok"] is False
    assert "approval_queue_request_already_exists_for_digest" in second["blocked_reasons"]
    assert second["summary"]["approval_request_created"] is False
    assert len(approvals) == 1


def test_shell_api_registry_and_chat_panel_expose_companion_memory_approval_preview(tmp_path: Path) -> None:
    _seed(tmp_path)

    from runtime.studio.phase11_chat_panel_contract import build_phase11_chat_panel_contract
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_companion_memory_approval_preview(
        "hermes",
        "preference",
        "Operator prefers direct progress updates during long implementation passes.",
    )
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}
    panel = build_phase11_chat_panel_contract(tmp_path, message="/memory save preference", explicit_intent="memory-save")

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_companion_memory_approval_preview"
    assert "get_phase11_companion_memory_approval_preview" in (chat_panel.get("api_methods") or [])
    assert "request_phase11_companion_memory_approval" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_companion_memory_approval_preview_ready"] is True
    assert readiness["phase11_companion_memory_approval_queue_write_gated"] is True
    assert readiness["phase11_companion_memory_writes_blocked"] is True
    assert panel["companion_memory_approval_preview"]["surface"] == "phase11_companion_memory_approval_preview"
    assert panel["companion_memory_approval_posture"]["approval_preview_visible"] is True
    assert panel["companion_memory_approval_posture"]["approval_queue_write_allowed_after_digest"] is True
    assert panel["companion_memory_approval_posture"]["memory_write_allowed"] is False
    assert panel["readiness"]["companion_memory_approval_preview_ready"] is True
