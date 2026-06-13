"""Tests for Phase 11 companion memory readback/search preview."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_companion_memory_approval_preview import (
    build_phase11_companion_memory_approval_preview,
)
from runtime.studio.phase11_companion_memory_approved_execution_proof import (
    execute_phase11_companion_memory_approved_execution_proof,
)
from runtime.studio.phase11_companion_memory_readback_search_preview import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_companion_memory_readback_search_preview,
)
from runtime.studio.service import StudioService
from runtime.studio.test_phase11_operator_companion_direction import _files, _seed_registry
from runtime.studio.test_phase11_operator_companion_direction_answers import _seed_direction


PREFERENCE_CONTENT = "Operator prefers direct progress updates during long implementation passes."
NOTE_CONTENT = "Operator asked Hermes to remember that readback is proof-only for now."


def _seed(root: Path) -> None:
    _seed_registry(root)
    _seed_direction(root)


def _queue_memory_approval(
    root: Path,
    *,
    content: str = PREFERENCE_CONTENT,
    memory_class: str = "preference",
    source_event_id: str = "readback-test",
) -> tuple[str, str]:
    _seed(root)
    preview = build_phase11_companion_memory_approval_preview(
        root,
        companion_id="hermes",
        memory_class=memory_class,
        content=content,
        source_surface="phase11-chat",
        source_event_id=source_event_id,
    )
    digest = str(preview["digest_proof"]["memory_approval_digest"])
    written = build_phase11_companion_memory_approval_preview(
        root,
        companion_id="hermes",
        memory_class=memory_class,
        content=content,
        source_surface="phase11-chat",
        source_event_id=source_event_id,
        expected_memory_approval_digest=digest,
        write_approval=True,
        operator_id="test",
    )
    return str(written["approval_record"]["approval_id"]), digest


def _execute_memory_approval(root: Path, approval_id: str, digest: str) -> dict:
    return execute_phase11_companion_memory_approved_execution_proof(
        root,
        approval_id=approval_id,
        expected_memory_approval_digest=digest,
        execute=True,
        operator_id="test",
        operator_approval_statement="operator approved companion memory proof execution",
    )


def test_readback_indexes_executed_and_pending_proof_records_without_memory_root(tmp_path: Path) -> None:
    executed_id, executed_digest = _queue_memory_approval(tmp_path)
    pending_id, _pending_digest = _queue_memory_approval(
        tmp_path,
        content=NOTE_CONTENT,
        memory_class="operator_note",
        source_event_id="pending-readback-test",
    )
    execution = _execute_memory_approval(tmp_path, executed_id, executed_digest)
    before = _files(tmp_path)

    payload = build_phase11_companion_memory_readback_search_preview(tmp_path, limit=25)
    after = _files(tmp_path)
    result_by_id = {item["approval_id"]: item for item in payload["results"]}

    assert execution["ok"] is True
    assert payload["ok"] is True
    assert payload["surface"] == "phase11_companion_memory_readback_search_preview"
    assert payload["pass"] == "phase11-companion-memory-readback-search-preview"
    assert payload["read_only"] is True
    assert payload["summary"]["proof_record_count"] >= 1
    assert payload["summary"]["executed_approval_count"] >= 1
    assert payload["summary"]["pending_approval_count"] >= 1
    assert payload["summary"]["memory_root_exists"] is False
    assert payload["summary"]["memory_ledger_written"] is False
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert result_by_id[executed_id]["proof_status"] == "proof_written"
    assert result_by_id[executed_id]["proof_outputs"]["proof_memory_record"]["exists"] is True
    assert result_by_id[pending_id]["proof_status"] == "approval_pending"
    assert result_by_id[pending_id]["proof_outputs"]["proof_memory_record"]["exists"] is False
    assert payload["authority"]["read_only"] is True
    assert payload["authority"]["memory_ledger_write_allowed"] is False
    assert payload["authority"]["provider_calls_allowed"] is False
    assert payload["authority"]["runtime_dispatch_allowed"] is False
    assert payload["authority"]["agent_bus_task_write_allowed"] is False
    assert payload["authority"]["canonical_mutation_allowed"] is False
    assert not (tmp_path / "07_LOGS" / "Companion-Memory").exists()
    assert before == after


def test_readback_search_filters_by_companion_class_status_and_query(tmp_path: Path) -> None:
    executed_id, executed_digest = _queue_memory_approval(tmp_path, source_event_id="progress-filter")
    _execute_memory_approval(tmp_path, executed_id, executed_digest)
    _queue_memory_approval(
        tmp_path,
        content=NOTE_CONTENT,
        memory_class="operator_note",
        source_event_id="operator-note-filter",
    )

    payload = build_phase11_companion_memory_readback_search_preview(
        tmp_path,
        companion_id="hermes",
        memory_class="preference",
        query="direct progress",
        status_filter="proof_written",
        limit=10,
    )
    empty = build_phase11_companion_memory_readback_search_preview(
        tmp_path,
        companion_id="archon",
        query="direct progress",
        limit=10,
    )

    assert payload["ok"] is True
    assert payload["summary"]["results_count"] == 1
    assert payload["results"][0]["approval_id"] == executed_id
    assert payload["results"][0]["companion_id"] == "hermes"
    assert payload["results"][0]["memory_class"] == "preference"
    assert payload["results"][0]["proof_status"] == "proof_written"
    assert payload["filters"]["query"] == "direct progress"
    assert empty["ok"] is True
    assert empty["summary"]["results_count"] == 0


def test_readback_tolerates_malformed_optional_approval_content(tmp_path: Path) -> None:
    approval_id, _digest = _queue_memory_approval(tmp_path)
    approval_path = tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json"
    approval_payload = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_payload["action_spec"]["content"] = "{not-json"
    approval_path.write_text(json.dumps(approval_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    payload = build_phase11_companion_memory_readback_search_preview(tmp_path, query=approval_id)

    assert payload["ok"] is True
    assert payload["summary"]["malformed_record_count"] == 1
    assert payload["results"][0]["approval_id"] == approval_id
    assert payload["results"][0]["parse_error"]
    assert any("approval_content_json_malformed" in item for item in payload["warnings"])


def test_shell_api_registry_and_chat_panel_expose_readback_search_preview(tmp_path: Path) -> None:
    approval_id, digest = _queue_memory_approval(tmp_path)
    _execute_memory_approval(tmp_path, approval_id, digest)

    from runtime.studio.phase11_chat_panel_contract import build_phase11_chat_panel_contract
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_companion_memory_readback_search_preview(
        query="direct progress",
        status_filter="proof_written",
    )
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}
    panel = build_phase11_chat_panel_contract(tmp_path, message="/memory search direct progress")

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_companion_memory_readback_search_preview"
    assert api_status["data"]["summary"]["results_count"] >= 1
    assert "get_phase11_companion_memory_readback_search_preview" in (chat_panel.get("api_methods") or [])
    assert readiness["phase11_companion_memory_readback_search_preview_ready"] is True
    assert readiness["phase11_companion_memory_proof_search_ready"] is True
    assert readiness["phase11_companion_memory_real_ledger_read_blocked"] is False
    assert readiness["phase11_companion_memory_real_ledger_read_model_ready"] is True
    assert readiness["phase11_companion_memory_ledger_writes_blocked"] is True
    assert panel["companion_memory_readback_search_preview"]["surface"] == "phase11_companion_memory_readback_search_preview"
    assert panel["companion_memory_readback_search_posture"]["readback_search_visible"] is True
    assert panel["companion_memory_readback_search_posture"]["memory_ledger_write_allowed"] is False
    assert panel["companion_memory_readback_search_posture"]["real_memory_ledger_read_allowed"] is False
    assert panel["readiness"]["companion_memory_readback_search_preview_ready"] is True
