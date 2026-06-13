"""Tests for Phase 11 companion-selection approval consumption readiness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.phase11_chat_companion_selection_approval_consumption_readiness import (
    NEXT_RECOMMENDED_PASS,
    build_phase11_chat_companion_selection_approval_consumption_readiness,
)
from runtime.studio.phase11_chat_companion_selection_queue_write_execution import (
    execute_phase11_chat_companion_selection_queue_write,
)
from runtime.studio.phase11_chat_companion_selection_queue_write_readiness import (
    build_phase11_chat_companion_selection_queue_write_readiness,
)
from runtime.studio.service import StudioService, StudioServiceError


MESSAGE = "Switch companion to Hermes"


def _files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def _queue_companion_selection(root: Path, *, message: str = MESSAGE) -> tuple[str, dict]:
    readiness = build_phase11_chat_companion_selection_queue_write_readiness(
        root,
        requested_runtime="hermes",
        current_runtime="openclaw",
        message=message,
    )
    written = execute_phase11_chat_companion_selection_queue_write(
        root,
        requested_runtime="hermes",
        current_runtime="openclaw",
        message=message,
        expected_queue_write_digest=readiness["digest_proof"]["queue_write_digest"],
        operator_id="test",
    )
    return written["approval_record"]["approval_id"], written


def test_pending_companion_selection_consumption_readiness_is_read_only(tmp_path: Path) -> None:
    approval_id, written = _queue_companion_selection(tmp_path)
    before = _files(tmp_path)

    payload = build_phase11_chat_companion_selection_approval_consumption_readiness(
        tmp_path,
        approval_id=approval_id,
        message=MESSAGE,
    )
    after = _files(tmp_path)

    assert payload["ok"] is True
    assert payload["pass"] == "phase11-chat-companion-selection-approval-consumption-readiness"
    assert payload["summary"]["selected_approval_id"] == approval_id
    assert payload["summary"]["approval_status"] == "pending"
    assert payload["summary"]["consumption_preview_ready"] is True
    assert payload["summary"]["consumption_preconditions_met"] is False
    assert payload["summary"]["approval_status_mutated"] is False
    assert payload["summary"]["approval_execution_called"] is False
    assert payload["summary"]["exact_once_marker_written"] is False
    assert payload["summary"]["companion_selection_written"] is False
    assert payload["summary"]["target_write_performed"] is False
    assert payload["summary"]["runtime_control_performed"] is False
    assert payload["summary"]["provider_call_performed"] is False
    assert payload["summary"]["agent_bus_task_written"] is False
    assert payload["summary"]["next_recommended_pass"] == NEXT_RECOMMENDED_PASS
    assert "operator_decision_not_approved" in payload["blocked_reasons"]
    assert payload["digest_proof"]["consumption_digest"]
    assert payload["selected_approval"]["metadata"]["phase11_companion_selection_queue_write_execution_proof"] is True
    assert payload["target_write_preflight"]["target_path"] == "runtime/studio/chat/companion-selection.json"
    assert payload["exact_once_marker_preview"]["marker_written_now"] is False
    assert not (tmp_path / "runtime" / "studio" / "chat" / "companion-selection.json").exists()
    assert written["summary"]["approval_request_created"] is True
    assert before == after


def test_approved_companion_selection_consumption_readiness_still_does_not_execute(tmp_path: Path) -> None:
    approval_id, _ = _queue_companion_selection(tmp_path)
    StudioService(tmp_path).approve(approval_id, reviewed_by="test")

    payload = build_phase11_chat_companion_selection_approval_consumption_readiness(
        tmp_path,
        approval_id=approval_id,
        message=MESSAGE,
    )
    marker_path = tmp_path / payload["exact_once_marker_preview"]["marker_path_preview"]

    assert payload["ok"] is True
    assert payload["summary"]["operator_approved"] is True
    assert payload["summary"]["consumption_preconditions_met"] is False
    assert payload["preflight_checks"]["studio_service_execute_approved_called"] is False
    assert payload["future_consumption_packet_preview"]["companion_selection_written"] is False
    assert not marker_path.exists()
    assert not (tmp_path / "runtime" / "studio" / "chat" / "companion-selection.json").exists()


def test_missing_non_companion_and_digest_mismatch_block_without_writes(tmp_path: Path) -> None:
    approval_id, _ = _queue_companion_selection(tmp_path)
    before = _files(tmp_path)

    missing = build_phase11_chat_companion_selection_approval_consumption_readiness(tmp_path, approval_id="missing")

    approvals = tmp_path / StudioService.APPROVAL_DIR
    non_companion = approvals / "non-companion.json"
    non_companion.write_text(
        json.dumps(
            {
                "approval_id": "non-companion",
                "action_spec": {
                    "action_type": "create_file",
                    "target_path": "07_LOGS/not-companion.md",
                    "content": "x",
                    "metadata": {"source_surface": "phase11_chat_panel"},
                    "submitted_by": "studio-chat",
                    "note": "",
                },
                "status": "pending",
                "submitted_at": "2026-05-12T00:00:00Z",
                "updated_at": "2026-05-12T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    non_companion_payload = build_phase11_chat_companion_selection_approval_consumption_readiness(
        tmp_path,
        approval_id="non-companion",
    )
    mismatch = build_phase11_chat_companion_selection_approval_consumption_readiness(
        tmp_path,
        approval_id=approval_id,
        message="Switch companion to Archon",
    )

    assert missing["ok"] is False
    assert "approval_artifact_not_found" in missing["blocked_reasons"]
    assert non_companion_payload["ok"] is False
    assert "approval_not_companion_selection" in non_companion_payload["blocked_reasons"]
    assert mismatch["ok"] is False
    assert "queue_write_digest_mismatch" in mismatch["blocked_reasons"]
    assert before + ["runtime/studio/approvals/non-companion.json"] == _files(tmp_path)


def test_service_execute_approved_blocks_companion_selection_before_status_or_target_mutation(tmp_path: Path) -> None:
    approval_id, _ = _queue_companion_selection(tmp_path)
    service = StudioService(tmp_path)
    service.approve(approval_id, reviewed_by="test")

    before = json.loads((tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json").read_text(encoding="utf-8"))
    with pytest.raises(StudioServiceError, match="Phase 11 companion selection"):
        service.execute_approved(approval_id)
    after = json.loads((tmp_path / StudioService.APPROVAL_DIR / f"{approval_id}.json").read_text(encoding="utf-8"))

    assert before["status"] == "approved"
    assert after["status"] == "approved"
    assert after.get("execution_status") is None
    assert not (tmp_path / "runtime" / "studio" / "chat" / "companion-selection.json").exists()


def test_shell_api_registry_and_panel_expose_companion_selection_consumption_readiness(tmp_path: Path) -> None:
    approval_id, _ = _queue_companion_selection(tmp_path)

    from runtime.studio.phase11_chat_panel_contract import build_phase11_chat_panel_contract
    from runtime.studio.shell.api import StudioAPI
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    api_status = StudioAPI(tmp_path).get_phase11_chat_companion_selection_approval_consumption_readiness(
        approval_id,
        MESSAGE,
    )
    registry = build_native_shell_panel_registry(tmp_path)
    chat_panel = next((panel for panel in registry.get("panels", []) if panel.get("id") == "chat"), {})
    readiness = registry.get("readiness") or {}
    panel = build_phase11_chat_panel_contract(tmp_path, message="/companion hermes select", explicit_intent="handoff")

    assert api_status["ok"] is True
    assert api_status["surface"] == "phase11_chat_companion_selection_approval_consumption_readiness"
    assert "get_phase11_chat_companion_selection_approval_consumption_readiness" in (
        chat_panel.get("api_methods") or []
    )
    assert readiness["phase11_chat_companion_selection_approval_consumption_readiness_ready"] is True
    assert readiness["phase11_chat_companion_selection_approval_consumption_blocked"] is True
    assert panel["companion_selection_approval_consumption_posture"]["consumption_readiness_visible"] is True
    assert panel["companion_selection_approval_consumption_posture"]["approval_execution_allowed"] is False
    assert panel["companion_selection_approval_consumption_posture"]["companion_selection_write_allowed"] is False
    assert panel["readiness"]["companion_selection_approval_consumption_readiness_ready"] is True
