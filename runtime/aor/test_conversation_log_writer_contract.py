"""Tests for the lower-phase governed conversation log writer contract."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.aor.conversation_log_writer_contract import (
    AGENT_ACTIVITY_ROOT,
    CONVERSATION_ROOT,
    MODEL_VERSION,
    RETENTION_CLASS,
    build_conversation_log_writer_contract,
)


def test_preview_builds_inspectable_artifact_plan_without_writes(tmp_path: Path) -> None:
    payload = build_conversation_log_writer_contract(
        tmp_path,
        title="Long Goal Session",
        conversation_text="User asked for a Phase 11 continuation summary.",
        operator_id="operator-test",
    )

    assert payload["ok"] is True
    assert payload["model_version"] == MODEL_VERSION
    assert payload["read_only"] is True
    assert payload["summary"]["writer_enabled_now"] is False
    assert payload["summary"]["conversation_log_write_allowed"] is False
    assert payload["conversation_log_artifact"]["target_path"].startswith(f"{CONVERSATION_ROOT}/")
    assert payload["conversation_log_artifact"]["content_preview"].startswith("---\ntype: conversation-log")
    assert payload["conversation_log_artifact"]["content_sha256"]
    assert payload["audit_cross_reference"]["agent_activity_root"] == AGENT_ACTIVITY_ROOT
    assert payload["retention_privacy_manifest"]["retention_class"] == RETENTION_CLASS
    assert payload["retention_privacy_manifest"]["canonical_memory"] is False
    assert payload["retention_privacy_manifest"]["hidden_memory"] is False
    assert not (tmp_path / "07_LOGS" / "Conversations").exists()
    assert not (tmp_path / "07_LOGS" / "Agent-Activity").exists()


def test_secret_bearing_input_is_rejected_and_redacted_from_payload(tmp_path: Path) -> None:
    payload = build_conversation_log_writer_contract(
        tmp_path,
        title="Secret test",
        conversation_text="Please save api_key=test-key-live-1234567890abcdef and password=hunter2 in history.",
    )
    encoded = json.dumps(payload)

    assert payload["ok"] is False
    assert payload["summary"]["secret_material_detected"] is True
    assert "secret_material_detected" in payload["blocked_reasons"]
    assert payload["secret_handling"]["raw_secret_rejected"] is True
    assert payload["secret_handling"]["redaction_applied_to_preview"] is True
    assert "test-key-live-1234567890abcdef" not in encoded
    assert "hunter2" not in encoded
    assert "[REDACTED-SECRET]" in encoded
    assert payload["conversation_log_artifact"]["target_file_written"] is False


def test_approval_gate_requires_approved_status_and_exact_content_digest(tmp_path: Path) -> None:
    preview = build_conversation_log_writer_contract(
        tmp_path,
        title="Approved target",
        conversation_text="Persist this only after an approved Gate packet.",
    )
    digest = preview["conversation_log_artifact"]["content_sha256"]

    missing = build_conversation_log_writer_contract(
        tmp_path,
        title="Approved target",
        conversation_text="Persist this only after an approved Gate packet.",
        requested_write=True,
    )
    pending = build_conversation_log_writer_contract(
        tmp_path,
        title="Approved target",
        conversation_text="Persist this only after an approved Gate packet.",
        requested_write=True,
        approval_id="gate-chat-log-1",
        approval_status="pending",
        expected_content_sha256=digest,
    )
    mismatch = build_conversation_log_writer_contract(
        tmp_path,
        title="Approved target",
        conversation_text="Persist this only after an approved Gate packet.",
        requested_write=True,
        approval_id="gate-chat-log-1",
        approval_status="approved",
        expected_content_sha256="wrong",
    )

    assert missing["ok"] is False
    assert "approved_gate_packet_required" in missing["blocked_reasons"]
    assert pending["ok"] is False
    assert "approval_status_not_approved" in pending["blocked_reasons"]
    assert mismatch["ok"] is False
    assert "expected_content_sha256_mismatch" in mismatch["blocked_reasons"]
    assert missing["approval_gate"]["approval_consumed"] is False
    assert pending["approval_gate"]["approval_consumed"] is False
    assert mismatch["conversation_log_artifact"]["target_file_written"] is False


def test_collision_and_idempotency_are_explicit_and_create_new_only(tmp_path: Path) -> None:
    preview = build_conversation_log_writer_contract(
        tmp_path,
        title="Duplicate Session",
        conversation_text="The same session should resolve to a stable target.",
    )
    target = tmp_path / preview["conversation_log_artifact"]["target_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("existing record must not be overwritten\n", encoding="utf-8")

    blocked = build_conversation_log_writer_contract(
        tmp_path,
        title="Duplicate Session",
        conversation_text="The same session should resolve to a stable target.",
        requested_write=True,
        approval_id="gate-chat-log-2",
        approval_status="approved",
        expected_content_sha256=preview["conversation_log_artifact"]["content_sha256"],
    )

    assert blocked["ok"] is False
    assert "conversation_target_collision" in blocked["blocked_reasons"]
    assert blocked["idempotency_and_collision"]["write_mode"] == "create_new_only"
    assert blocked["idempotency_and_collision"]["target_collision_absent"] is False
    assert blocked["conversation_log_artifact"]["target_file_written"] is False
    assert target.read_text(encoding="utf-8") == "existing record must not be overwritten\n"


def test_export_delete_manager_is_review_only_and_non_canonical(tmp_path: Path) -> None:
    payload = build_conversation_log_writer_contract(
        tmp_path,
        title="Retention review",
        conversation_text="Keep this inspectable but deletable/exportable only through review.",
    )
    manager = payload["retention_export_delete_manager"]

    assert manager["export_requires_operator_review"] is True
    assert manager["delete_requires_operator_review"] is True
    assert manager["export_performed"] is False
    assert manager["delete_performed"] is False
    assert manager["delete_mode"] == "tombstone_or_remove_after_review_only"
    assert payload["authority_boundaries"]["canonical_promotion_allowed"] is False
    assert payload["authority_boundaries"]["hidden_memory_persistence_allowed"] is False
    assert payload["closeout_evidence"]["conversation_log_written"] is False
    assert payload["closeout_evidence"]["canonical_writeback_performed"] is False
