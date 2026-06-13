"""Tests for Phase 11 P0 runtime completion surfaces.

Covers:
- phase11_chat_conversation_log_writer
- phase11_chat_runtime_result_display
- phase11_chat_manual_ui_verification_harness (readiness check only)
- phase11_chat_discord_control_handler
- phase11_chat_schedule_apply_handler
- phase11_credential_setup_ux
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def vault(tmp_path: Path) -> Path:
    """Minimal vault fixture with required structure."""
    (tmp_path / "runtime" / "schedules").mkdir(parents=True)
    (tmp_path / "runtime" / "workflows" / "registry").mkdir(parents=True)
    (tmp_path / "runtime" / "studio" / "chat").mkdir(parents=True)
    (tmp_path / "runtime" / "studio" / "approvals").mkdir(parents=True)
    (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    (tmp_path / "07_LOGS" / "Conversations").mkdir(parents=True)
    (tmp_path / ".chaseos").mkdir(parents=True)
    (tmp_path / "runtime" / "agent_bus").mkdir(parents=True)
    _write_minimal_bus_db(tmp_path)
    return tmp_path


def _write_minimal_bus_db(vault: Path) -> None:
    """Initialize a minimal Agent Bus SQLite DB for tests."""
    try:
        from runtime.agent_bus.backends.backend_loader import get_backend
        backend = get_backend(vault)
        backend.init()
    except Exception:
        pass


def _write_discord_bindings(vault: Path) -> None:
    content = """schema_version: "1.0"
server:
  id: "1111111111111111111"
  name: "TestServer"
operator:
  user_id: "2222222222222222222"
  display_name: "TestOperator"
  trust_tier: 1
  execution_eligible: true
  allowed_adapters: [openclaw, hermes]
  approval_authority: true
runtimes:
  openclaw:
    bot_user_id: "3333333333333333333"
    display_name: "OpenClaw"
    trust_tier: 2
    execution_eligible: true
    allowed_adapters: [openclaw]
    execution_lane_status: live
  hermes:
    bot_user_id: "4444444444444444444"
    display_name: "Hermes"
    trust_tier: 2
    execution_eligible: true
    allowed_adapters: [hermes]
    execution_lane_status: live
primary_channels:
  audit_writeback:
    id: "5555555555555555555"
    name: "audit-writeback"
    channel_class: audit-writeback
    bound: true
    execution_authority: none
    interactive_eligible_runtimes: []
    interactive_mode: output_only
    posting_eligible_runtimes: [openclaw, hermes]
  runtime_chat_openclaw:
    id: "6666666666666666666"
    name: "openclaw-chat"
    channel_class: runtime-chat
    bound: true
    execution_authority: advisory_only
    interactive_eligible_runtimes: [openclaw]
    interactive_mode: free_response
    posting_eligible_runtimes: [openclaw]
  unbound_channel:
    id: ""
    name: "unbound-test"
    channel_class: runtime-chat
    bound: false
    interactive_eligible_runtimes: []
    interactive_mode: output_only
    posting_eligible_runtimes: []
hermes_discord_lane_present: true
hermes_execution_via_discord_enabled: true
default_unmapped_policy: deny
"""
    path = vault / ".chaseos" / "discord_instance_bindings.yaml"
    path.write_text(content, encoding="utf-8")


def _write_minimal_schedule(vault: Path, schedule_id: str, enabled: bool = False) -> None:
    enabled_str = str(enabled).lower()
    content = f"""schedule_id: {schedule_id}
workflow_id: operator_today
owner: operator
cadence:
  type: cron
  cron_expression: "0 7 * * 1-5"
  timezone: America/New_York
  event_type: null
  event_source: null
trigger_source: openclaw
runtime_adapter_target: openclaw
delivery:
  primary_target: vault-local
  vault_writeback_targets:
    - "07_LOGS/Operator-Briefs/"
  external_delivery_declared: false
  vault_local_only: true
approval_policy: none
shadow_mode: false
failure_behavior: escalate
audit_requirements:
  - workflow_id
  - schedule_id
  - trigger_time
  - status
allowed_workflow_task_types:
  - operator-briefing
provenance:
  created_by: operator
  created_at: "2026-05-16T00:00:00Z"
  rationale: Test schedule for P0 verification
enabled: {enabled_str}
"""
    sched_dir = vault / "runtime" / "schedules"
    sched_dir.mkdir(parents=True, exist_ok=True)
    (sched_dir / f"{schedule_id}.yaml").write_text(content, encoding="utf-8")
    _write_minimal_workflow_manifest(vault)
    _write_schedule_index(vault, schedule_id, enabled)


def _write_minimal_workflow_manifest(vault: Path) -> None:
    manifest = "id: operator_today\nname: Operator Today\nstatus: active\ntask_type: operator-briefing\n"
    reg_dir = vault / "runtime" / "workflows" / "registry"
    reg_dir.mkdir(parents=True, exist_ok=True)
    (reg_dir / "operator_today.yaml").write_text(manifest, encoding="utf-8")


def _write_schedule_index(vault: Path, schedule_id: str, enabled: bool) -> None:
    index = f"schedules:\n  - id: {schedule_id}\n    enabled: {str(enabled).lower()}\n"
    (vault / "runtime" / "schedules" / "index.yaml").write_text(index, encoding="utf-8")


# ---------------------------------------------------------------------------
# Conversation Log Writer Tests
# ---------------------------------------------------------------------------


class TestConversationLogWriter:
    def test_dry_run_returns_content_preview(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_conversation_log_writer import write_conversation_log
        result = write_conversation_log(
            vault,
            operator_approval_statement="Test approval",
            user_prompt="What is the market outlook?",
            dry_run=True,
        )
        assert result["ok"] is True
        assert result["file_written"] is False
        assert result["dry_run"] is True
        assert result["secret_values_stored"] is False
        assert "session_id" in result
        assert result["target_path"].startswith("07_LOGS/Conversations/")

    def test_live_write_creates_file(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_conversation_log_writer import write_conversation_log
        result = write_conversation_log(
            vault,
            operator_approval_statement="P0 live test approval",
            user_prompt="Tell me about today's AOR runs",
            provider_output="The AOR ran three workflows successfully.",
            provider_id="openai",
            provider_model="gpt-4o",
            hermes_task_id="hermes-task-abc123",
            hermes_status="done",
            dry_run=False,
        )
        assert result["ok"] is True
        assert result["file_written"] is True
        target = vault / result["target_path"]
        assert target.exists()
        content = target.read_text(encoding="utf-8")
        assert "conversation-log" in content
        assert "Tell me about today" in content
        assert result["secret_values_stored"] is False

    def test_blocks_without_approval_statement_in_live_mode(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_conversation_log_writer import write_conversation_log
        result = write_conversation_log(
            vault,
            operator_approval_statement="",
            user_prompt="Some question",
            dry_run=False,
        )
        assert result["ok"] is False
        assert "operator_approval_statement_required_for_live_write" in result["blocked_reasons"]

    def test_blocks_without_user_prompt(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_conversation_log_writer import write_conversation_log
        result = write_conversation_log(
            vault,
            operator_approval_statement="Approved",
            user_prompt="",
            dry_run=True,
        )
        assert result["ok"] is False
        assert "user_prompt_required" in result["blocked_reasons"]

    def test_secret_pattern_redacted_in_prompt(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_conversation_log_writer import write_conversation_log
        result = write_conversation_log(
            vault,
            operator_approval_statement="Approved",
            user_prompt="My key is test-key-abcdefghijklmnopqrstuvwx",
            dry_run=True,
        )
        assert result["ok"] is True
        assert "test-key-abcdef" not in result["content_preview"]

    def test_idempotent_exact_once_blocks_second_live_write(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_conversation_log_writer import write_conversation_log
        kwargs: dict[str, Any] = {
            "operator_approval_statement": "First write",
            "user_prompt": "Unique prompt for idempotency test",
            "dry_run": False,
        }
        r1 = write_conversation_log(vault, **kwargs)
        assert r1["ok"] is True
        assert r1["file_written"] is True
        r2 = write_conversation_log(vault, **kwargs)
        assert r2["ok"] is False
        assert any("marker" in b or "collision" in b for b in r2["blocked_reasons"])

    def test_audit_record_written_on_live_write(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_conversation_log_writer import write_conversation_log
        result = write_conversation_log(
            vault,
            operator_approval_statement="Audit test",
            user_prompt="Does the audit record get written?",
            dry_run=False,
        )
        assert result["ok"] is True
        assert result["audit_path"] is not None
        assert (vault / result["audit_path"]).exists()

    def test_all_lane_fields_included(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_conversation_log_writer import write_conversation_log
        result = write_conversation_log(
            vault,
            operator_approval_statement="Lane test",
            user_prompt="Check all lanes",
            provider_output="Provider OK",
            hermes_task_id="htask-001",
            hermes_status="done",
            openclaw_discord_task_id="odtask-001",
            openclaw_discord_status="done",
            openclaw_cron_task_id="octask-001",
            openclaw_cron_status="done",
            dry_run=False,
        )
        assert result["ok"] is True
        content = (vault / result["target_path"]).read_text(encoding="utf-8")
        assert "htask-001" in content
        assert "odtask-001" in content
        assert "octask-001" in content

    def test_canonical_mutation_not_allowed(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_conversation_log_writer import write_conversation_log
        result = write_conversation_log(
            vault,
            operator_approval_statement="Check authority",
            user_prompt="Authority check",
            dry_run=False,
        )
        assert result.get("canonical_mutation_performed") is False
        assert result["authority"]["canonical_memory_write_allowed"] is False


# ---------------------------------------------------------------------------
# Runtime Result Display Tests
# ---------------------------------------------------------------------------


class TestRuntimeResultDisplay:
    def test_returns_ok_with_empty_bus(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_runtime_result_display import build_chat_runtime_result_display
        result = build_chat_runtime_result_display(vault)
        assert result["ok"] is True
        assert result["read_only"] is True
        assert "lanes" in result
        assert result["authority"]["task_claim_allowed"] is False

    def test_lanes_for_default_runtimes(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_runtime_result_display import build_chat_runtime_result_display
        result = build_chat_runtime_result_display(vault)
        runtimes = [lane["runtime"] for lane in result["lanes"]]
        assert "Hermes" in runtimes
        assert "OpenClaw" in runtimes

    def test_custom_runtimes(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_runtime_result_display import build_chat_runtime_result_display
        result = build_chat_runtime_result_display(vault, runtimes=["Archon"])
        runtimes = [lane["runtime"] for lane in result["lanes"]]
        assert "Archon" in runtimes
        assert "Hermes" not in runtimes

    def test_read_only_authority(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_runtime_result_display import build_chat_runtime_result_display
        result = build_chat_runtime_result_display(vault)
        authority = result["authority"]
        assert authority["task_claim_allowed"] is False
        assert authority["task_write_allowed"] is False
        assert authority["result_promote_to_canonical_auto"] is False

    def test_session_task_id_filter(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_runtime_result_display import build_chat_runtime_result_display
        result = build_chat_runtime_result_display(vault, session_task_ids=["nonexistent-task-xyz"])
        for lane in result["lanes"]:
            assert lane["task_count"] == 0

    def test_get_task_result_card_missing_returns_none(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_runtime_result_display import get_task_result_card
        card = get_task_result_card(vault, "task-does-not-exist", "Hermes")
        assert card is None

    def test_summary_counts(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_runtime_result_display import build_chat_runtime_result_display
        result = build_chat_runtime_result_display(vault)
        summary = result["summary"]
        assert "total_tasks" in summary
        assert "complete_count" in summary
        assert "blocked_count" in summary
        assert "active_count" in summary


# ---------------------------------------------------------------------------
# Manual UI Verification Harness Tests
# ---------------------------------------------------------------------------


class TestManualUIVerificationHarness:
    def test_readiness_check_returns_ok(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_manual_ui_verification_harness import check_harness_readiness
        result = check_harness_readiness(vault)
        assert result["ok"] is True
        assert result["readiness"]["loopback_only"] is True
        assert result["readiness"]["credential_value_displayed"] is False

    def test_readiness_reflects_env_key_presence(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_manual_ui_verification_harness import check_harness_readiness
        old = os.environ.pop("OPENAI_API_KEY", None)
        try:
            result = check_harness_readiness(vault)
            assert result["readiness"]["openai_api_key_present"] is False
        finally:
            if old:
                os.environ["OPENAI_API_KEY"] = old

    def test_requires_loopback_raises_on_external_host(self) -> None:
        from runtime.studio.phase11_chat_manual_ui_verification_harness import HarnessError, _require_loopback
        with pytest.raises(HarnessError):
            _require_loopback("0.0.0.0")

    def test_secret_indicator_detection(self) -> None:
        from runtime.studio.phase11_chat_manual_ui_verification_harness import _has_secret_indicator
        assert _has_secret_indicator("test-key-abc123def")
        assert _has_secret_indicator("OPENAI_API_KEY=mykey")
        assert not _has_secret_indicator("what is the market outlook?")

    def test_verification_steps_present(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_manual_ui_verification_harness import check_harness_readiness
        result = check_harness_readiness(vault)
        assert len(result["verification_steps"]) >= 5
        assert result["readiness"]["harness_port"] == 8772


# ---------------------------------------------------------------------------
# Discord Control Handler Tests
# ---------------------------------------------------------------------------


class TestDiscordControlHandler:
    def test_dry_run_no_api_call(self, vault: Path) -> None:
        _write_discord_bindings(vault)
        from runtime.studio.phase11_chat_discord_control_handler import handle_discord_control
        result = handle_discord_control(
            vault,
            action="post_audit",
            channel_name="audit-writeback",
            message_content="Test dry run audit message",
            runtime_id="openclaw",
            dry_run=True,
        )
        assert result["ok"] is True
        assert result["dry_run"] is True
        assert result["discord_api_called"] is False
        assert result["credential_value_displayed"] is False

    def test_blocked_missing_bindings(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_discord_control_handler import handle_discord_control
        result = handle_discord_control(
            vault,
            action="post_audit",
            channel_name="audit-writeback",
            dry_run=True,
        )
        assert result["ok"] is False
        assert any("channel_not_found" in b for b in result["blocked_reasons"])

    def test_blocked_invalid_action(self, vault: Path) -> None:
        _write_discord_bindings(vault)
        from runtime.studio.phase11_chat_discord_control_handler import handle_discord_control
        result = handle_discord_control(
            vault,
            action="delete_channel",
            channel_name="audit-writeback",
            dry_run=True,
        )
        assert result["ok"] is False
        assert any("action_not_permitted" in b for b in result["blocked_reasons"])

    def test_blocked_unbound_channel(self, vault: Path) -> None:
        _write_discord_bindings(vault)
        from runtime.studio.phase11_chat_discord_control_handler import handle_discord_control
        result = handle_discord_control(
            vault,
            action="post_audit",
            channel_name="unbound-test",
            dry_run=True,
        )
        assert result["ok"] is False
        assert any("not_bound" in b for b in result["blocked_reasons"])

    def test_blocked_live_without_approval(self, vault: Path) -> None:
        _write_discord_bindings(vault)
        from runtime.studio.phase11_chat_discord_control_handler import handle_discord_control
        result = handle_discord_control(
            vault,
            action="post_audit",
            channel_name="audit-writeback",
            dry_run=False,
            operator_approved=False,
        )
        assert result["ok"] is False
        assert any("operator_approved" in b for b in result["blocked_reasons"])

    def test_digest_mismatch_blocked(self, vault: Path) -> None:
        _write_discord_bindings(vault)
        from runtime.studio.phase11_chat_discord_control_handler import handle_discord_control
        result = handle_discord_control(
            vault,
            action="post_audit",
            channel_name="audit-writeback",
            message_content="Test",
            expected_action_digest="wrongdigest123456789012345678901",
            dry_run=True,
        )
        assert result["ok"] is False
        assert "action_digest_mismatch" in result["blocked_reasons"]

    def test_evidence_written_on_dry_run(self, vault: Path) -> None:
        _write_discord_bindings(vault)
        from runtime.studio.phase11_chat_discord_control_handler import handle_discord_control
        result = handle_discord_control(
            vault,
            action="post_audit",
            channel_name="audit-writeback",
            message_content="Evidence test",
            dry_run=True,
        )
        assert result["ok"] is True
        assert result["evidence_path"] is not None
        assert (vault / result["evidence_path"]).exists()

    def test_bindings_status_no_ids_displayed(self, vault: Path) -> None:
        _write_discord_bindings(vault)
        from runtime.studio.phase11_chat_discord_control_handler import get_discord_bindings_status
        result = get_discord_bindings_status(vault)
        assert result["ok"] is True
        assert result["credential_values_displayed"] is False
        raw = json.dumps(result)
        assert "5555555555555555555" not in raw

    def test_credential_never_in_result(self, vault: Path) -> None:
        _write_discord_bindings(vault)
        os.environ["OPENCLAW_DISCORD_BOT_TOKEN"] = "fake-test-token-123"
        try:
            from runtime.studio.phase11_chat_discord_control_handler import handle_discord_control
            result = handle_discord_control(
                vault,
                action="dry_run_ping",
                channel_name="audit-writeback",
                dry_run=True,
            )
            raw = json.dumps(result)
            assert "fake-test-token-123" not in raw
        finally:
            del os.environ["OPENCLAW_DISCORD_BOT_TOKEN"]

    def test_runtime_not_eligible_blocked(self, vault: Path) -> None:
        _write_discord_bindings(vault)
        from runtime.studio.phase11_chat_discord_control_handler import handle_discord_control
        result = handle_discord_control(
            vault,
            action="post_audit",
            channel_name="openclaw-chat",
            runtime_id="hermes",
            dry_run=True,
        )
        assert result["ok"] is False
        assert any("not_eligible" in b for b in result["blocked_reasons"])


# ---------------------------------------------------------------------------
# Schedule Apply Handler Tests
# ---------------------------------------------------------------------------


class TestScheduleApplyHandler:
    def test_dry_run_validate_only(self, vault: Path) -> None:
        _write_minimal_schedule(vault, "sch-test-0700")
        from runtime.studio.phase11_chat_schedule_apply_handler import handle_schedule_apply
        result = handle_schedule_apply(
            vault,
            schedule_id="sch-test-0700",
            action="validate_only",
            dry_run=True,
        )
        assert result["ok"] is True
        assert result["dry_run"] is True
        assert result["schedule_written"] is False
        assert result["external_cron_mutated"] is False

    def test_dry_run_blocks_no_actual_write(self, vault: Path) -> None:
        _write_minimal_schedule(vault, "sch-test-0700")
        from runtime.studio.phase11_chat_schedule_apply_handler import handle_schedule_apply
        result = handle_schedule_apply(
            vault,
            schedule_id="sch-test-0700",
            action="enable_schedule",
            dry_run=True,
        )
        assert result["ok"] is True
        assert result["schedule_written"] is False

    def test_blocked_missing_schedule_id(self, vault: Path) -> None:
        from runtime.studio.phase11_chat_schedule_apply_handler import handle_schedule_apply
        result = handle_schedule_apply(vault, schedule_id=None, dry_run=True)
        assert result["ok"] is False
        assert "schedule_id_required" in result["blocked_reasons"]

    def test_blocked_apply_without_approval(self, vault: Path) -> None:
        _write_minimal_schedule(vault, "sch-apply-test")
        from runtime.studio.phase11_chat_schedule_apply_handler import handle_schedule_apply
        result = handle_schedule_apply(
            vault,
            schedule_id="sch-apply-test",
            action="enable_schedule",
            dry_run=False,
            apply_mode=True,
            operator_approved=False,
        )
        assert result["ok"] is False
        assert "operator_approved_required_for_apply_mode" in result["blocked_reasons"]

    def test_blocked_apply_without_statement(self, vault: Path) -> None:
        _write_minimal_schedule(vault, "sch-apply-test")
        from runtime.studio.phase11_chat_schedule_apply_handler import handle_schedule_apply
        result = handle_schedule_apply(
            vault,
            schedule_id="sch-apply-test",
            action="enable_schedule",
            dry_run=False,
            apply_mode=True,
            operator_approved=True,
            operator_approval_statement="",
        )
        assert result["ok"] is False
        assert "operator_approval_statement_required_for_apply_mode" in result["blocked_reasons"]

    def test_blocked_invalid_action(self, vault: Path) -> None:
        _write_minimal_schedule(vault, "sch-test-inv")
        from runtime.studio.phase11_chat_schedule_apply_handler import handle_schedule_apply
        result = handle_schedule_apply(
            vault,
            schedule_id="sch-test-inv",
            action="delete_schedule",
            dry_run=True,
        )
        assert result["ok"] is False
        assert any("action_not_permitted" in b for b in result["blocked_reasons"])

    def test_evidence_written(self, vault: Path) -> None:
        _write_minimal_schedule(vault, "sch-evidence-test")
        from runtime.studio.phase11_chat_schedule_apply_handler import handle_schedule_apply
        result = handle_schedule_apply(
            vault,
            schedule_id="sch-evidence-test",
            action="dry_run",
            dry_run=True,
        )
        assert result["ok"] is True
        assert result["evidence_path"] is not None
        assert (vault / result["evidence_path"]).exists()

    def test_external_cron_never_mutated(self, vault: Path) -> None:
        _write_minimal_schedule(vault, "sch-cron-test")
        from runtime.studio.phase11_chat_schedule_apply_handler import handle_schedule_apply
        result = handle_schedule_apply(
            vault,
            schedule_id="sch-cron-test",
            action="enable_schedule",
            dry_run=False,
            apply_mode=True,
            operator_approved=True,
            operator_approval_statement="Approve schedule enable",
        )
        assert result.get("external_cron_mutated") is False

    def test_live_apply_enables_disabled_schedule(self, vault: Path) -> None:
        _write_minimal_schedule(vault, "sch-live-apply", enabled=False)
        from runtime.studio.phase11_chat_schedule_apply_handler import handle_schedule_apply
        result = handle_schedule_apply(
            vault,
            schedule_id="sch-live-apply",
            action="enable_schedule",
            dry_run=False,
            apply_mode=True,
            operator_approved=True,
            operator_approval_statement="Enabling test schedule for P0 verification",
        )
        assert result["ok"] is True
        assert result["schedule_written"] is True
        assert result["post_apply_state"] == "enabled"
        assert result["external_cron_mutated"] is False


# ---------------------------------------------------------------------------
# Credential Setup UX Tests
# ---------------------------------------------------------------------------


class TestCredentialSetupUX:
    def test_status_returns_ok(self, vault: Path) -> None:
        from runtime.studio.phase11_credential_setup_ux import get_credential_status
        result = get_credential_status(vault)
        assert result["ok"] is True
        assert result["read_only"] is True
        assert result["authority"]["credential_value_display_allowed"] is False

    def test_no_credential_values_in_status(self, vault: Path) -> None:
        os.environ["OPENAI_API_KEY"] = "test-key-test-key-value-never-display"
        try:
            from runtime.studio.phase11_credential_setup_ux import get_credential_status
            result = get_credential_status(vault)
            raw = json.dumps(result)
            assert "test-key-test-key-value-never-display" not in raw
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_openai_key_detected_when_present(self, vault: Path) -> None:
        os.environ["OPENAI_API_KEY"] = "test-key-fakekeyfortesting"
        try:
            from runtime.studio.phase11_credential_setup_ux import get_credential_status
            result = get_credential_status(vault)
            openai_entry = next(
                (c for c in result["credentials"] if c["key_id"] == "openai_provider"), None
            )
            assert openai_entry is not None
            assert openai_entry["present_in_environment"] is True
            assert openai_entry["value_displayed"] is False
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_openai_key_missing_detected(self, vault: Path) -> None:
        old = os.environ.pop("OPENAI_API_KEY", None)
        try:
            from runtime.studio.phase11_credential_setup_ux import get_credential_status
            result = get_credential_status(vault)
            openai_entry = next(
                (c for c in result["credentials"] if c["key_id"] == "openai_provider"), None
            )
            assert openai_entry is not None
            assert openai_entry["present_in_environment"] is False
            assert "OPENAI_API_KEY" in result["summary"]["direct_provider_missing"]
        finally:
            if old:
                os.environ["OPENAI_API_KEY"] = old

    def test_confirm_blocked_when_env_var_absent(self, vault: Path) -> None:
        old = os.environ.pop("OPENAI_API_KEY", None)
        try:
            from runtime.studio.phase11_credential_setup_ux import confirm_credential_setup
            result = confirm_credential_setup(
                vault,
                key_id="openai_provider",
                dry_run=False,
            )
            assert result["ok"] is False
            assert "env_var_not_present" in result["blocked_reasons"][0]
        finally:
            if old:
                os.environ["OPENAI_API_KEY"] = old

    def test_confirm_dry_run_no_file_written(self, vault: Path) -> None:
        os.environ["OPENAI_API_KEY"] = "test-key-dryruntest"
        try:
            from runtime.studio.phase11_credential_setup_ux import confirm_credential_setup, SETUP_METADATA_PATH
            result = confirm_credential_setup(vault, key_id="openai_provider", dry_run=True)
            assert result["ok"] is True
            assert result["dry_run"] is True
            assert result["metadata_path"] is None
            assert not (vault / SETUP_METADATA_PATH).exists()
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_confirm_live_writes_metadata_no_value(self, vault: Path) -> None:
        os.environ["OPENAI_API_KEY"] = "test-key-livetestkey"
        try:
            from runtime.studio.phase11_credential_setup_ux import confirm_credential_setup, SETUP_METADATA_PATH
            result = confirm_credential_setup(vault, key_id="openai_provider", dry_run=False)
            assert result["ok"] is True
            assert (vault / SETUP_METADATA_PATH).exists()
            metadata = json.loads((vault / SETUP_METADATA_PATH).read_text(encoding="utf-8"))
            assert metadata["secret_values_stored"] is False
            raw = json.dumps(metadata)
            assert "test-key-livetestkey" not in raw
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_confirm_unknown_key_id(self, vault: Path) -> None:
        from runtime.studio.phase11_credential_setup_ux import confirm_credential_setup
        result = confirm_credential_setup(vault, key_id="nonexistent_key")
        assert result["ok"] is False

    def test_get_setup_guide_all_creds(self) -> None:
        from runtime.studio.phase11_credential_setup_ux import get_setup_guide
        result = get_setup_guide()
        assert result["ok"] is True
        assert len(result["credentials"]) >= 4

    def test_get_setup_guide_single_key(self) -> None:
        from runtime.studio.phase11_credential_setup_ux import get_setup_guide
        result = get_setup_guide("openai_provider")
        assert result["ok"] is True
        assert result["env_var"] == "OPENAI_API_KEY"
        assert result["value_display_allowed"] is False

    def test_ensure_env_example_creates_file(self, vault: Path) -> None:
        from runtime.studio.phase11_credential_setup_ux import ensure_env_example
        result = ensure_env_example(vault)
        assert result["ok"] is True
        path = vault / ".env.example"
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "OPENAI_API_KEY" in content
        raw_env_value_hints = ["test-key-your-key-here", "pplx-your-key-here"]
        for hint in raw_env_value_hints:
            assert hint in content

    def test_ensure_env_example_no_real_secrets(self, vault: Path) -> None:
        os.environ["OPENAI_API_KEY"] = "test-key-realkey-shouldnotappear"
        try:
            from runtime.studio.phase11_credential_setup_ux import ensure_env_example
            ensure_env_example(vault)
            content = (vault / ".env.example").read_text(encoding="utf-8")
            assert "test-key-realkey-shouldnotappear" not in content
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_value_length_never_reveals_secret(self, vault: Path) -> None:
        os.environ["OPENAI_API_KEY"] = "test-key-secret123"
        try:
            from runtime.studio.phase11_credential_setup_ux import get_credential_status
            result = get_credential_status(vault)
            entry = next(c for c in result["credentials"] if c["key_id"] == "openai_provider")
            assert entry["value_length"] == len("test-key-secret123")
            raw = json.dumps(result)
            assert "test-key-secret123" not in raw
        finally:
            del os.environ["OPENAI_API_KEY"]
