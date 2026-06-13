"""Tests for Phase 11 companion memory ledger read-model preview."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_companion_memory_approved_ledger_write_execution_proof import (
    execute_phase11_companion_memory_approved_ledger_write_execution_proof,
)
from runtime.studio.phase11_companion_memory_ledger_read_model_preview import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_companion_memory_ledger_read_model_preview,
)
from runtime.studio.test_phase11_companion_memory_approved_ledger_write_execution_proof import (
    _queue_ledger_write_approval,
)
from runtime.studio.test_phase11_operator_companion_direction import _files


def _execute_ledger_write(root: Path) -> tuple[str, str, dict]:
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


def test_ledger_read_model_reads_executed_jsonl_entries_without_writes(tmp_path: Path) -> None:
    approval_id, source_approval_id, executed = _execute_ledger_write(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_companion_memory_ledger_read_model_preview(tmp_path, limit=25)
    after = _files(tmp_path)
    ledger_records = [item for item in payload["results"] if item["source_type"] == "ledger_entry"]

    assert payload["ok"] is True
    assert payload["surface"] == "phase11_companion_memory_ledger_read_model_preview"
    assert payload["pass"] == "phase11-companion-memory-ledger-read-model-preview"
    assert payload["read_only"] is True
    assert payload["summary"]["ledger_read_model_preview_ready"] is True
    assert payload["summary"]["memory_root_exists"] is True
    assert payload["summary"]["memory_ledger_read"] is True
    assert payload["summary"]["ledger_file_count"] == 1
    assert payload["summary"]["ledger_entry_count"] == 1
    assert payload["summary"]["memory_ledger_written"] is False
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert ledger_records[0]["ledger_write_approval_id"] == approval_id
    assert ledger_records[0]["source_approval_id"] == source_approval_id
    assert ledger_records[0]["ledger_write_execution_id"] == executed["execution_record"]["execution_id"]
    assert ledger_records[0]["trust_state"] == "raw"
    assert ledger_records[0]["canonical"] is False
    assert ledger_records[0]["authoritative"] is False
    assert ledger_records[0]["provider_call_performed"] is False
    assert ledger_records[0]["runtime_dispatch_performed"] is False
    assert ledger_records[0]["agent_bus_task_written"] is False
    assert payload["authority"]["real_companion_memory_read_allowed"] is True
    assert payload["authority"]["memory_ledger_write_allowed"] is False
    assert payload["authority"]["approval_execution_allowed"] is False
    assert payload["authority"]["provider_calls_allowed"] is False
    assert payload["authority"]["runtime_dispatch_allowed"] is False
    assert payload["authority"]["agent_bus_task_write_allowed"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
    assert before == after


def test_ledger_read_model_filters_by_companion_class_and_query(tmp_path: Path) -> None:
    approval_id, _source_approval_id, _executed = _execute_ledger_write(tmp_path)

    filtered = build_phase11_companion_memory_ledger_read_model_preview(
        tmp_path,
        companion_id="hermes",
        memory_class="preference",
        query="direct progress",
        limit=10,
    )
    empty = build_phase11_companion_memory_ledger_read_model_preview(
        tmp_path,
        companion_id="archon",
        query="direct progress",
        limit=10,
    )

    assert filtered["ok"] is True
    assert filtered["summary"]["results_count"] == 1
    assert filtered["results"][0]["ledger_write_approval_id"] == approval_id
    assert filtered["results"][0]["companion_id"] == "hermes"
    assert filtered["results"][0]["memory_class"] == "preference"
    assert filtered["filters"]["query"] == "direct progress"
    assert empty["ok"] is True
    assert empty["summary"]["results_count"] == 0


def test_ledger_read_model_uses_proof_backfill_when_real_ledger_absent(tmp_path: Path) -> None:
    approval_id, _digest, source_approval_id = _queue_ledger_write_approval(tmp_path)
    # Leave the ledger-write approval pending: source proof exists, real ledger does not.
    payload = build_phase11_companion_memory_ledger_read_model_preview(tmp_path, query="direct progress", limit=25)

    assert approval_id
    assert payload["ok"] is True
    assert payload["summary"]["memory_root_exists"] is False
    assert payload["summary"]["ledger_entry_count"] == 0
    assert payload["summary"]["proof_backfill_count"] >= 1
    assert payload["summary"]["combined_record_count"] >= 1
    assert any(item["source_type"] == "proof_only_evidence" for item in payload["results"])
    assert any(item["source_approval_id"] == source_approval_id for item in payload["results"])
    assert payload["proof_backfill_source"]["memory_root_read_by_proof_backfill"] is False
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()


def test_ledger_read_model_tolerates_malformed_jsonl_lines(tmp_path: Path) -> None:
    _execute_ledger_write(tmp_path)
    ledger_path = tmp_path / "07_LOGS" / "Companion-Memory" / "hermes" / "memory-ledger.jsonl"
    with ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("{not-json}\n")
        handle.write(json.dumps(["not", "object"]) + "\n")

    payload = build_phase11_companion_memory_ledger_read_model_preview(tmp_path, limit=25)

    assert payload["ok"] is True
    assert payload["summary"]["ledger_entry_count"] == 1
    assert payload["summary"]["malformed_line_count"] == 2
    assert any(str(item["error"]).startswith("ledger_line_malformed") for item in payload["malformed_lines"])
    assert any(str(item["error"]) == "ledger_line_not_object" for item in payload["malformed_lines"])


def test_shell_api_registry_and_chat_panel_expose_ledger_read_model(tmp_path: Path) -> None:
    _execute_ledger_write(tmp_path)

    from runtime.studio.phase11_chat_panel_contract import build_phase11_chat_panel_contract
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_companion_memory_ledger_read_model_preview(
        query="direct progress",
        limit=10,
    )
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}
    panel = build_phase11_chat_panel_contract(tmp_path, message="/memory ledger direct progress")

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_companion_memory_ledger_read_model_preview"
    assert api_status["data"]["summary"]["ledger_entry_count"] == 1
    assert "get_phase11_companion_memory_ledger_read_model_preview" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_companion_memory_ledger_read_model_preview_ready"] is True
    assert readiness["phase11_companion_memory_real_ledger_read_model_ready"] is True
    assert readiness["phase11_companion_memory_ledger_writes_blocked"] is True
    assert panel["companion_memory_ledger_read_model_preview"]["surface"] == (
        "phase11_companion_memory_ledger_read_model_preview"
    )
    posture = panel["companion_memory_ledger_read_model_posture"]
    assert posture["ledger_read_model_visible"] is True
    assert posture["real_memory_ledger_read_allowed"] is True
    assert posture["memory_ledger_write_allowed"] is False
    assert panel["readiness"]["companion_memory_ledger_read_model_preview_ready"] is True
