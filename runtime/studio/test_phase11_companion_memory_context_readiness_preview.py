"""Tests for Phase 11 companion memory context-readiness preview."""

from __future__ import annotations

from pathlib import Path

from runtime.studio.phase11_companion_memory_approved_ledger_write_execution_proof import (
    execute_phase11_companion_memory_approved_ledger_write_execution_proof,
)
from runtime.studio.phase11_companion_memory_context_readiness_preview import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_companion_memory_context_readiness_preview,
    format_phase11_companion_memory_context_readiness_preview,
)
from runtime.studio.test_phase11_companion_memory_approved_ledger_write_execution_proof import (
    _queue_ledger_write_approval,
)
from runtime.studio.test_phase11_operator_companion_direction import _files


def _execute_context_source(root: Path) -> tuple[str, str, dict]:
    approval_id, digest, source_approval_id = _queue_ledger_write_approval(root)
    executed = execute_phase11_companion_memory_approved_ledger_write_execution_proof(
        root,
        approval_id=approval_id,
        expected_ledger_write_approval_digest=digest,
        execute=True,
        operator_id="test",
        operator_approval_statement="operator approved companion memory ledger write",
    )
    assert executed["ok"] is True
    return approval_id, source_approval_id, executed


def test_context_readiness_builds_bounded_packet_from_real_ledger_without_writes(tmp_path: Path) -> None:
    ledger_approval_id, source_approval_id, _executed = _execute_context_source(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_companion_memory_context_readiness_preview(
        tmp_path,
        companion_id="hermes",
        memory_class="preference",
        query="direct progress",
        limit=5,
        max_context_chars=1200,
    )
    after = _files(tmp_path)

    assert payload["ok"] is True
    assert payload["surface"] == "phase11_companion_memory_context_readiness_preview"
    assert payload["pass"] == "phase11-companion-memory-context-readiness-preview"
    assert payload["status"] == "COMPLETE / READ-ONLY / CONTEXT READINESS PREVIEW / VERIFIED"
    assert payload["read_only"] is True
    assert payload["summary"]["context_readiness_preview_ready"] is True
    assert payload["summary"]["context_packet_ready"] is True
    assert payload["summary"]["context_item_count"] == 1
    assert payload["summary"]["ledger_entry_count"] == 1
    assert payload["summary"]["raw_noncanonical_context_only"] is True
    assert payload["summary"]["provider_call_performed"] is False
    assert payload["summary"]["model_call_performed"] is False
    assert payload["summary"]["memory_ledger_written"] is False
    assert payload["summary"]["conversation_written"] is False
    assert payload["summary"]["runtime_dispatch_performed"] is False
    assert payload["summary"]["agent_bus_task_written"] is False
    assert payload["summary"]["canonical_mutation_performed"] is False
    assert payload["summary"]["memory_snapshot_unchanged"] is True
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS

    item = payload["context_items"][0]
    assert item["safe_for_provider_context_preview"] is True
    assert item["raw_noncanonical_boundary"] is True
    assert item["canonical"] is False
    assert item["authoritative"] is False
    assert item["source_ref"]["ledger_write_approval_id"] == ledger_approval_id
    assert item["source_ref"]["source_approval_id"] == source_approval_id
    assert "direct progress" in item["context_line"]

    packet = payload["context_packet_preview"]
    assert packet["ready_for_chat_display"] is True
    assert packet["ready_for_provider_context_preview"] is True
    assert packet["provider_execution_allowed"] is False
    assert packet["requires_openai_secret_reference_before_live_use"] is True
    assert packet["requires_operator_approval_before_live_model_call"] is True
    assert packet["packet_digest"] == payload["digest_proof"]["context_readiness_digest"]
    assert payload["authority"]["provider_calls_allowed"] is False
    assert payload["authority"]["model_calls_allowed"] is False
    assert payload["authority"]["approval_queue_write_allowed"] is False
    assert payload["authority"]["memory_ledger_write_allowed"] is False
    assert payload["authority"]["conversation_persistence_allowed"] is False
    assert payload["authority"]["runtime_dispatch_allowed"] is False
    assert payload["authority"]["agent_bus_task_write_allowed"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
    assert before == after


def test_context_readiness_handles_no_records_without_creating_memory(tmp_path: Path) -> None:
    before = _files(tmp_path)

    payload = build_phase11_companion_memory_context_readiness_preview(
        tmp_path,
        companion_id="hermes",
        query="missing",
    )
    after = _files(tmp_path)

    assert payload["ok"] is True
    assert payload["status"] == "READY / READ-ONLY / NO CONTEXT RECORDS"
    assert payload["summary"]["context_readiness_preview_ready"] is True
    assert payload["summary"]["context_packet_ready"] is False
    assert payload["summary"]["context_item_count"] == 0
    assert "no_context_records_found" in payload["blocked_reasons"]
    assert payload["context_packet_preview"]["ready_for_chat_display"] is True
    assert payload["context_packet_preview"]["provider_execution_allowed"] is False
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()
    assert before == after


def test_context_readiness_respects_budget_and_filters(tmp_path: Path) -> None:
    _execute_context_source(tmp_path)

    filtered = build_phase11_companion_memory_context_readiness_preview(
        tmp_path,
        companion_id="hermes",
        memory_class="preference",
        query="direct progress",
        max_context_chars=256,
    )
    empty = build_phase11_companion_memory_context_readiness_preview(
        tmp_path,
        companion_id="archon",
        query="direct progress",
    )

    assert filtered["summary"]["context_packet_ready"] is True
    assert filtered["summary"]["context_chars"] <= filtered["summary"]["max_context_chars"]
    assert filtered["filters"]["max_context_chars"] == 256
    assert filtered["context_items"][0]["source_ref"]["companion_id"] == "hermes"
    assert empty["summary"]["context_packet_ready"] is False
    assert empty["summary"]["context_item_count"] == 0


def test_context_readiness_uses_proof_backfill_when_real_ledger_absent(tmp_path: Path) -> None:
    _ledger_approval_id, _ledger_digest, source_approval_id = _queue_ledger_write_approval(tmp_path)
    # Leave the ledger-write approval pending: proof evidence exists, real ledger does not.

    payload = build_phase11_companion_memory_context_readiness_preview(
        tmp_path,
        query="direct progress",
        include_proof_backfill=True,
    )

    assert payload["ok"] is True
    assert payload["summary"]["context_packet_ready"] is True
    assert payload["summary"]["ledger_entry_count"] == 0
    assert payload["summary"]["proof_backfill_count"] >= 1
    assert any(item["source_ref"]["source_approval_id"] == source_approval_id for item in payload["context_items"])
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()


def test_shell_api_registry_and_chat_panel_expose_context_readiness(tmp_path: Path) -> None:
    _execute_context_source(tmp_path)

    from runtime.studio.phase11_chat_panel_contract import build_phase11_chat_panel_contract
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_companion_memory_context_readiness_preview(
        query="direct progress",
        limit=5,
        max_context_chars=1200,
    )
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}
    panel = build_phase11_chat_panel_contract(tmp_path, message="/memory context direct progress")

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_companion_memory_context_readiness_preview"
    assert api_status["data"]["summary"]["context_packet_ready"] is True
    assert "get_phase11_companion_memory_context_readiness_preview" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_companion_memory_context_readiness_preview_ready"] is True
    assert readiness["phase11_companion_memory_context_provider_calls_blocked"] is True
    assert readiness["phase11_companion_memory_context_requires_openai_secret_reference"] is True
    assert panel["companion_memory_context_readiness_preview"]["surface"] == (
        "phase11_companion_memory_context_readiness_preview"
    )
    posture = panel["companion_memory_context_readiness_posture"]
    assert posture["context_readiness_visible"] is True
    assert posture["context_packet_ready"] is True
    assert posture["provider_context_delivery_allowed"] is False
    assert posture["provider_calls_allowed"] is False
    assert posture["model_calls_allowed"] is False
    assert panel["readiness"]["companion_memory_context_readiness_preview_ready"] is True
    assert panel["readiness"]["companion_memory_context_requires_openai_secret_reference"] is True


def test_format_context_readiness_summarizes_operator_blocker(tmp_path: Path) -> None:
    _execute_context_source(tmp_path)
    payload = build_phase11_companion_memory_context_readiness_preview(tmp_path)

    text = format_phase11_companion_memory_context_readiness_preview(payload)

    assert "Phase 11 Companion Memory Context Readiness Preview" in text
    assert "Requires OpenAI secret reference: True" in text
    assert "Provider execution allowed: False" in text
