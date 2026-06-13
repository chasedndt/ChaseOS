"""CLI tests for the Phase 11 chat router contract command."""

from __future__ import annotations

import json
import sys
from pathlib import Path


VAULT_ROOT = Path(__file__).resolve().parents[2]
if str(VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402
from runtime.studio.service import StudioService  # noqa: E402


def test_phase11_chat_router_contract_json_blocks_without_credentials(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-router-contract",
            "--vault-root",
            str(tmp_path),
            "--message",
            "Use OpenAI for this answer",
            "--intent",
            "model-chat",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    result = payload["result"]
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-router-contract"
    assert result["surface"] == "phase11_chat_router_readonly_intent_contract"
    assert result["intent_result"]["intent_class"] == "model-chat"
    assert result["route_decision"]["route_execution_allowed"] is False
    assert result["authority"]["provider_calls_allowed"] is False
    assert result["authority"]["conversation_persistence_allowed"] is False
    assert "provider_route_contract_not_satisfied" in result["route_decision"]["blocked_reasons"]


def test_phase11_chat_router_contract_text_output_states_boundary(tmp_path, capsys) -> None:
    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-router-contract",
            "--vault-root",
            str(tmp_path),
            "--message",
            "/runtime status",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase 11 Chat Router Read-Only Intent Contract" in output
    assert "intent_class: dashboard-query" in output
    assert "route_execution_allowed: False" in output
    assert "Boundary: read-only intent contract only" in output


def test_phase11_chat_conversation_persistence_contract_json_is_no_write(tmp_path, capsys) -> None:
    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-conversation-persistence-contract",
            "--vault-root",
            str(tmp_path),
            "--message",
            "Save this as a governed conversation preview",
            "--intent",
            "chat-answer",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    target = result["conversation_descriptor"]["target_path_preview"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-conversation-persistence-contract"
    assert result["surface"] == "phase11_chat_conversation_persistence_contract"
    assert target.startswith("07_LOGS/Conversations/")
    assert result["conversation_log_preview"]["target_file_written"] is False
    assert result["future_approval_packet_preview"]["approval_request_created"] is False
    assert not (tmp_path / target).exists()


def test_phase11_chat_conversation_persistence_contract_json_redacts_secret_input(tmp_path, capsys) -> None:
    raw_secret = "test-key-testsecret1234567890"
    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-conversation-persistence-contract",
            "--vault-root",
            str(tmp_path),
            "--message",
            f"save this token {raw_secret} in chat history",
            "--json",
        ]
    )

    output = capsys.readouterr().out
    payload = json.loads(output)
    result = payload["result"]

    assert exit_code == 0
    assert raw_secret not in output
    assert result["summary"]["conversation_preview_ready"] is False
    assert "secret_or_credential_indicator_present" in result["blocked_reasons"]
    assert result["preflight_checks"]["secret_bearing_input_absent"] is False
    assert result["conversation_log_preview"]["secret_material_redacted"] is True
    assert result["conversation_log_preview"]["target_file_written"] is False
    assert result["future_approval_packet_preview"]["approval_request_created"] is False
    assert not (tmp_path / "07_LOGS" / "Conversations").exists()
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()


def test_phase11_chat_conversation_persistence_contract_text_output(tmp_path, capsys) -> None:
    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-conversation-persistence-contract",
            "--vault-root",
            str(tmp_path),
            "--message",
            "Capture this chat",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Phase 11 Chat Conversation Persistence Session History Contract" in output
    assert "conversation_write_allowed_now: False" in output
    assert "approval_queue_write_allowed_now: False" in output


def test_phase11_chat_conversation_persistence_contract_text_output_redacts_secret_input(tmp_path, capsys) -> None:
    raw_secret = "test-key-testsecret1234567890"
    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-conversation-persistence-contract",
            "--vault-root",
            str(tmp_path),
            "--message",
            f"save this token {raw_secret} in chat history",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert raw_secret not in output
    assert "preview_ready: False" in output
    assert "[REDACTED_SECRET]" in output


def test_phase11_chat_conversation_persistence_contract_json_redacts_secret_title_input(tmp_path, capsys) -> None:
    raw_secret = "titleSecret12345"
    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-conversation-persistence-contract",
            "--vault-root",
            str(tmp_path),
            "--message",
            "ordinary conversation",
            "--title",
            f"password={raw_secret}",
            "--json",
        ]
    )

    output = capsys.readouterr().out
    payload = json.loads(output)
    result = payload["result"]

    assert exit_code == 0
    assert raw_secret not in output
    assert "password-titlesecret12345" not in output.lower()
    assert result["summary"]["conversation_preview_ready"] is False
    assert "secret_or_credential_indicator_present" in result["blocked_reasons"]
    assert result["preflight_checks"]["secret_bearing_input_absent"] is False
    assert result["conversation_descriptor"]["title"] == "password=[REDACTED_SECRET]"
    assert result["conversation_log_preview"]["target_file_written"] is False
    assert result["future_approval_packet_preview"]["approval_request_created"] is False
    assert not (tmp_path / "07_LOGS" / "Conversations").exists()
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()


def test_phase11_chat_conversation_persistence_contract_text_output_redacts_secret_title_input(tmp_path, capsys) -> None:
    raw_secret = "titleSecret12345"
    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-conversation-persistence-contract",
            "--vault-root",
            str(tmp_path),
            "--message",
            "ordinary conversation",
            "--title",
            f"password={raw_secret}",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert raw_secret not in output
    assert "password-titlesecret12345" not in output.lower()
    assert "title: password=[REDACTED_SECRET]" in output
    assert "preview_ready: False" in output
    assert not (tmp_path / "07_LOGS" / "Conversations").exists()
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()


def test_phase11_chat_approval_queue_write_preview_and_write(tmp_path, capsys) -> None:
    preview_exit = cli.main(
        [
            "studio",
            "phase11-chat-approval-queue-write-execution-proof",
            "--vault-root",
            str(tmp_path),
            "--message",
            "Create a new project from chat",
            "--intent",
            "project-create",
            "--json",
        ]
    )
    preview_payload = json.loads(capsys.readouterr().out)
    digest = preview_payload["result"]["digest_proof"]["action_digest"]

    write_exit = cli.main(
        [
            "studio",
            "phase11-chat-approval-queue-write-execution-proof",
            "--vault-root",
            str(tmp_path),
            "--message",
            "Create a new project from chat",
            "--intent",
            "project-create",
            "--expected-action-digest",
            digest,
            "--write-approval",
            "--json",
        ]
    )
    write_payload = json.loads(capsys.readouterr().out)
    result = write_payload["result"]

    assert preview_exit == 0
    assert write_exit == 0
    assert preview_payload["action"] == "studio.phase11-chat-approval-queue-write-execution-proof"
    assert write_payload["action"] == "studio.phase11-chat-approval-queue-write-execution-proof"
    assert result["surface"] == "phase11_chat_approval_queue_write_execution_proof"
    assert result["summary"]["approval_request_created"] is True
    assert result["target_write_proof"]["target_file_written"] is False
    assert (tmp_path / result["summary"]["approval_artifact_path"]).exists()
    assert not (tmp_path / result["summary"]["target_path_preview"]).exists()


def test_phase11_chat_live_provider_execution_approval_preview_json_is_no_call(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-live-provider-execution-approval-preview",
            "--vault-root",
            str(tmp_path),
            "--message",
            "Use a model to summarize Studio status",
            "--intent",
            "model-chat",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-live-provider-execution-approval-preview"
    assert result["surface"] == "phase11_chat_live_provider_execution_approval_preview"
    assert result["summary"]["approval_preview_ready"] is True
    assert result["future_approval_packet_preview"]["approval_request_created"] is False
    assert result["future_provider_execution_preview"]["provider_call_performed"] is False
    assert result["conversation_audit_preflight"]["conversation_log_written"] is False
    assert not (tmp_path / "runtime" / "studio" / "approvals").exists()
    assert not (tmp_path / "07_LOGS" / "Conversations").exists()


def test_phase11_chat_runtime_dispatch_readiness_json_is_no_dispatch(tmp_path, capsys) -> None:
    cap_path = tmp_path / "runtime/codex/capabilities.yaml"
    cap_path.parent.mkdir(parents=True, exist_ok=True)
    cap_path.write_text(
        "\n".join(
            [
                "bus_name: Codex",
                "heartbeat_stale_seconds: 900",
                "max_concurrent_tasks: 1",
                "priority_ceiling: normal",
                "handles:",
                "  - task_type: repo.inspect",
                "    priority: primary",
                "    notes: Read-only repository inspection.",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-runtime-dispatch-readiness-contract",
            "--vault-root",
            str(tmp_path),
            "--message",
            "Ask Codex to inspect runtime queue",
            "--intent",
            "runtime-task",
            "--requested-runtime-id",
            "Codex",
            "--requested-action",
            "repo.inspect",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-runtime-dispatch-readiness-contract"
    assert result["surface"] == "phase11_chat_runtime_dispatch_readiness_contract"
    assert result["summary"]["selected_runtime_id"] == "Codex"
    assert result["future_dispatch_packet_preview"]["agent_bus_task_created"] is False
    assert result["future_dispatch_packet_preview"]["workflow_dispatch_called"] is False



def test_phase11_chat_runtime_status_explanation_json_and_text_outputs(tmp_path, capsys) -> None:
    (tmp_path / "runtime/codex").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runtime/codex/capabilities.yaml").write_text(
        "\n".join(
            [
                "bus_name: Codex",
                "heartbeat_stale_seconds: 900",
                "max_concurrent_tasks: 1",
                "priority_ceiling: normal",
                "handles:",
                "  - task_type: repo.inspect",
                "    priority: primary",
                "    notes: Read-only repository inspection.",
            ]
        ),
        encoding="utf-8",
    )
    json_exit = cli.main(
        [
            "studio",
            "phase11-chat-runtime-status-explanation",
            "--vault-root",
            str(tmp_path),
            "--message",
            "Ask Codex to inspect runtime queue",
            "--intent",
            "runtime-task",
            "--requested-runtime-id",
            "Codex",
            "--requested-action",
            "repo.inspect",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    text_exit = cli.main(
        [
            "studio",
            "phase11-chat-runtime-status-explanation",
            "--vault-root",
            str(tmp_path),
            "--message",
            "Ask Codex to inspect runtime queue",
            "--intent",
            "runtime-task",
            "--requested-runtime-id",
            "Codex",
            "--requested-action",
            "repo.inspect",
        ]
    )
    output = capsys.readouterr().out

    assert json_exit == 0
    assert text_exit == 0
    assert payload["action"] == "studio.phase11-chat-runtime-status-explanation"
    assert result["surface"] == "phase11_chat_runtime_status_explanation"
    assert result["runtime_cockpit_alignment"]["shares_runtime_cockpit_wording"] is True
    assert result["no_dispatch_proof"]["agent_bus_task_created"] is False
    assert result["no_dispatch_proof"]["workflow_dispatched"] is False
    assert "Phase 11 Chat Runtime Status Explanation" in output
    assert "Boundary: explanation only" in output


def test_phase11_chat_readonly_slash_command_responses_json_and_text_outputs(tmp_path, capsys) -> None:
    (tmp_path / "README.md").write_text("# Test Vault\n\nSee [[Runtime Status]].\n", encoding="utf-8")

    json_exit = cli.main(
        [
            "studio",
            "phase11-chat-readonly-slash-command-responses",
            "--vault-root",
            str(tmp_path),
            "--message",
            "/runtime status",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    text_exit = cli.main(
        [
            "studio",
            "phase11-chat-readonly-slash-command-responses",
            "--vault-root",
            str(tmp_path),
            "--message",
            "/runtime status",
        ]
    )
    output = capsys.readouterr().out

    assert json_exit == 0
    assert text_exit == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-readonly-slash-command-responses"
    assert result["surface"] == "phase11_chat_readonly_slash_command_responses"
    assert result["summary"]["slash_token"] == "/runtime"
    assert result["summary"]["subcommand"] == "status"
    assert result["summary"]["response_cards_ready"] is True
    assert result["summary"]["runtime_dispatch_performed"] is False
    assert result["authority"]["vault_writes_allowed"] is False
    assert "Phase 11 Chat Read-Only Slash Command Responses" in output
    assert "Boundary: read-only slash response cards only" in output


def test_phase11_readonly_card_visual_qa_json_preview_and_write_evidence(tmp_path, capsys) -> None:
    (tmp_path / "README.md").write_text("# Test Vault\n\nSee [[Runtime Status]].\n", encoding="utf-8")

    json_exit = cli.main(
        [
            "studio",
            "phase11-chat-readonly-card-visual-qa",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    write_exit = cli.main(
        [
            "studio",
            "phase11-chat-readonly-card-visual-qa",
            "--vault-root",
            str(tmp_path),
            "--write-evidence",
            "--evidence-slug",
            "test-phase11-card-visual-qa-cli",
            "--json",
        ]
    )
    written_payload = json.loads(capsys.readouterr().out)
    written = written_payload["result"]

    assert json_exit == 0
    assert write_exit == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-readonly-card-visual-qa"
    assert result["surface"] == "phase11_readonly_card_visual_qa"
    assert result["summary"]["visual_artifact_ready"] is True
    assert result["summary"]["visual_browser_qa_complete"] is False
    assert result["authority"]["command_execution_allowed"] is False
    assert result["authority"]["runtime_dispatch_allowed"] is False
    assert result["authority"]["provider_calls_allowed"] is False
    assert result["evidence"]["written"] is False
    assert written["evidence"]["written"] is True
    assert (tmp_path / written["evidence"]["html_path"]).is_file()
    assert written["summary"]["screenshot_captured"] is False


def test_phase11_no_hitl_feature_family_selection_audit_json_preview_and_write_evidence(tmp_path, capsys) -> None:
    (tmp_path / "ROADMAP.md").write_text(
        "Phase 11 read-only card visual QA is complete. "
        "Next marker: phase11-chat-no-hitl-feature-family-selection-audit.\n",
        encoding="utf-8",
    )

    json_exit = cli.main(
        [
            "studio",
            "phase11-chat-no-hitl-feature-family-selection-audit",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    write_exit = cli.main(
        [
            "studio",
            "phase11-chat-no-hitl-feature-family-selection-audit",
            "--vault-root",
            str(tmp_path),
            "--write-evidence",
            "--evidence-slug",
            "test-phase11-no-hitl-feature-family-selection-audit-cli",
            "--json",
        ]
    )
    written_payload = json.loads(capsys.readouterr().out)
    written = written_payload["result"]

    assert json_exit == 0
    assert write_exit == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-no-hitl-feature-family-selection-audit"
    assert result["surface"] == "phase11_no_hitl_feature_family_selection_audit"
    assert result["summary"]["selected_next_recommended_pass"] == (
        "phase11-chat-readonly-slash-command-catalog-audit"
    )
    assert result["selected_candidate"]["authority_class"] == "read_only"
    assert result["authority"]["approval_consumption_allowed"] is False
    assert result["authority"]["provider_calls_allowed"] is False
    assert result["authority"]["runtime_dispatch_allowed"] is False
    assert result["authority"]["browser_control_allowed"] is False
    assert result["authority"]["canonical_mutation_allowed"] is False
    assert result["evidence"]["written"] is False
    assert written["evidence"]["written"] is True
    assert (tmp_path / written["evidence"]["json_path"]).is_file()
    assert (tmp_path / written["evidence"]["markdown_path"]).is_file()


def test_phase11_readonly_slash_command_catalog_audit_json_preview_and_write_evidence(tmp_path, capsys) -> None:
    (tmp_path / "README.md").write_text("# Test Vault\n\nSee [[Runtime Status]].\n", encoding="utf-8")
    profile = tmp_path / "06_AGENTS" / "Hermes-Runtime-Profile.md"
    profile.parent.mkdir(parents=True)
    profile.write_text(
        "---\ntitle: Hermes Runtime Profile\nruntime: hermes\nstatus: active test lane\n---\n# Hermes\n",
        encoding="utf-8",
    )

    json_exit = cli.main(
        [
            "studio",
            "phase11-chat-readonly-slash-command-catalog-audit",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    write_exit = cli.main(
        [
            "studio",
            "phase11-chat-readonly-slash-command-catalog-audit",
            "--vault-root",
            str(tmp_path),
            "--write-evidence",
            "--evidence-slug",
            "test-phase11-readonly-slash-command-catalog-audit-cli",
            "--json",
        ]
    )
    written_payload = json.loads(capsys.readouterr().out)
    written = written_payload["result"]

    assert json_exit == 0
    assert write_exit == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-readonly-slash-command-catalog-audit"
    assert result["surface"] == "phase11_readonly_slash_command_catalog_audit"
    assert result["summary"]["catalog_audit_ready"] is True
    assert result["summary"]["supported_readonly_commands_covered"] is True
    assert result["summary"]["write_and_execution_commands_blocked"] is True
    assert result["summary"]["selected_next_recommended_pass"] == (
        "phase11-chat-readonly-operator-dashboard-aggregate-audit"
    )
    assert result["authority"]["approval_consumption_allowed"] is False
    assert result["authority"]["provider_calls_allowed"] is False
    assert result["authority"]["runtime_dispatch_allowed"] is False
    assert result["authority"]["browser_control_allowed"] is False
    assert result["authority"]["canonical_mutation_allowed"] is False
    assert result["evidence"]["written"] is False
    assert written["evidence"]["written"] is True
    assert (tmp_path / written["evidence"]["json_path"]).is_file()
    assert (tmp_path / written["evidence"]["markdown_path"]).is_file()


def test_phase11_readonly_operator_dashboard_aggregate_audit_json_preview_and_write_evidence(
    tmp_path,
    capsys,
) -> None:
    (tmp_path / "README.md").write_text("# Test Vault\n\nSee [[Runtime Status]].\n", encoding="utf-8")
    logs = tmp_path / "07_LOGS" / "Build-Logs"
    logs.mkdir(parents=True)
    (logs / "2026-05-12-ChaseOS-test.md").write_text("# Test Build Log\n", encoding="utf-8")

    json_exit = cli.main(
        [
            "studio",
            "phase11-chat-readonly-operator-dashboard-aggregate-audit",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    write_exit = cli.main(
        [
            "studio",
            "phase11-chat-readonly-operator-dashboard-aggregate-audit",
            "--vault-root",
            str(tmp_path),
            "--write-evidence",
            "--evidence-slug",
            "test-phase11-readonly-operator-dashboard-aggregate-audit-cli",
            "--json",
        ]
    )
    written_payload = json.loads(capsys.readouterr().out)
    written = written_payload["result"]

    assert json_exit == 0
    assert write_exit == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-readonly-operator-dashboard-aggregate-audit"
    assert result["surface"] == "phase11_readonly_operator_dashboard_aggregate_audit"
    assert result["summary"]["aggregate_audit_ready"] is True
    assert result["summary"]["dashboard_response_ready"] is True
    assert result["summary"]["source_cards_covered"] is True
    assert result["summary"]["selected_next_recommended_pass"] == (
        "phase11-chat-no-hitl-lane-completion-audit"
    )
    assert result["authority"]["approval_consumption_allowed"] is False
    assert result["authority"]["provider_calls_allowed"] is False
    assert result["authority"]["runtime_dispatch_allowed"] is False
    assert result["authority"]["browser_control_allowed"] is False
    assert result["authority"]["canonical_mutation_allowed"] is False
    assert result["evidence"]["written"] is False
    assert written["evidence"]["written"] is True
    assert (tmp_path / written["evidence"]["json_path"]).is_file()
    assert (tmp_path / written["evidence"]["markdown_path"]).is_file()


def test_phase11_no_hitl_lane_completion_audit_json_preview_and_write_evidence(
    tmp_path,
    capsys,
) -> None:
    from runtime.studio.test_phase11_no_hitl_lane_completion_audit import _seed_completion_vault

    _seed_completion_vault(tmp_path)

    json_exit = cli.main(
        [
            "studio",
            "phase11-chat-no-hitl-lane-completion-audit",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    write_exit = cli.main(
        [
            "studio",
            "phase11-chat-no-hitl-lane-completion-audit",
            "--vault-root",
            str(tmp_path),
            "--write-evidence",
            "--evidence-slug",
            "test-phase11-no-hitl-lane-completion-audit-cli",
            "--json",
        ]
    )
    written_payload = json.loads(capsys.readouterr().out)
    written = written_payload["result"]

    assert json_exit == 0
    assert write_exit == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-no-hitl-lane-completion-audit"
    assert result["surface"] == "phase11_no_hitl_lane_completion_audit"
    assert result["summary"]["completion_audit_ready"] is True
    assert result["summary"]["no_hitl_lane_complete"] is True
    assert result["summary"]["eligible_no_hitl_remaining_count"] == 0
    assert result["summary"]["selected_next_recommended_pass"] == (
        "operator-selected-governed-executor-or-deferred-closeout"
    )
    assert result["authority"]["approval_consumption_allowed"] is False
    assert result["authority"]["provider_calls_allowed"] is False
    assert result["authority"]["runtime_dispatch_allowed"] is False
    assert result["authority"]["browser_control_allowed"] is False
    assert result["authority"]["canonical_mutation_allowed"] is False
    assert result["evidence"]["written"] is False
    assert written["evidence"]["written"] is True
    assert (tmp_path / written["evidence"]["json_path"]).is_file()
    assert (tmp_path / written["evidence"]["markdown_path"]).is_file()


def test_phase11_operator_governed_executor_deferred_closeout_json_preview_and_write_evidence(
    tmp_path,
    capsys,
) -> None:
    from runtime.studio.test_phase11_no_hitl_lane_completion_audit import _seed_completion_vault

    _seed_completion_vault(tmp_path)

    json_exit = cli.main(
        [
            "studio",
            "operator-selected-governed-executor-or-deferred-closeout",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    write_exit = cli.main(
        [
            "studio",
            "operator-selected-governed-executor-or-deferred-closeout",
            "--vault-root",
            str(tmp_path),
            "--write-evidence",
            "--evidence-slug",
            "test-phase11-operator-governed-executor-deferred-closeout-cli",
            "--json",
        ]
    )
    written_payload = json.loads(capsys.readouterr().out)
    written = written_payload["result"]

    assert json_exit == 0
    assert write_exit == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.operator-selected-governed-executor-or-deferred-closeout"
    assert result["surface"] == "phase11_operator_governed_executor_deferred_closeout"
    assert result["summary"]["handoff_ready"] is True
    assert result["summary"]["substantial_no_hitl_passes_remaining"] == 0
    assert result["summary"]["operator_selection_required"] is True
    assert result["summary"]["implementation_authority_granted"] is False
    assert result["authority"]["approval_consumption_allowed"] is False
    assert result["authority"]["provider_calls_allowed"] is False
    assert result["authority"]["runtime_dispatch_allowed"] is False
    assert result["authority"]["browser_control_allowed"] is False
    assert result["authority"]["canonical_mutation_allowed"] is False
    assert result["evidence"]["written"] is False
    assert written["evidence"]["written"] is True
    assert (tmp_path / written["evidence"]["json_path"]).is_file()
    assert (tmp_path / written["evidence"]["markdown_path"]).is_file()


def test_phase11_operator_action_required_no_autonomous_pass_json_preview_and_write_evidence(
    tmp_path,
    capsys,
) -> None:
    from runtime.studio.test_phase11_no_hitl_lane_completion_audit import _seed_completion_vault

    _seed_completion_vault(tmp_path)

    json_exit = cli.main(
        [
            "studio",
            "operator-action-required-no-autonomous-phase11-pass",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    write_exit = cli.main(
        [
            "studio",
            "operator-action-required-no-autonomous-phase11-pass",
            "--vault-root",
            str(tmp_path),
            "--write-evidence",
            "--evidence-slug",
            "test-phase11-operator-action-required-no-autonomous-pass-cli",
            "--json",
        ]
    )
    written_payload = json.loads(capsys.readouterr().out)
    written = written_payload["result"]

    assert json_exit == 0
    assert write_exit == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.operator-action-required-no-autonomous-phase11-pass"
    assert result["surface"] == "phase11_operator_action_required_no_autonomous_pass"
    assert result["summary"]["decision_gate_ready"] is True
    assert result["summary"]["autonomous_phase11_passes_remaining"] == 0
    assert result["summary"]["operator_decision_required"] is True
    assert result["summary"]["implementation_authority_granted"] is False
    assert result["summary"]["selected_lane_id"] is None
    assert result["authority"]["approval_consumption_allowed"] is False
    assert result["authority"]["provider_calls_allowed"] is False
    assert result["authority"]["runtime_dispatch_allowed"] is False
    assert result["authority"]["browser_control_allowed"] is False
    assert result["authority"]["canonical_mutation_allowed"] is False
    assert result["evidence"]["written"] is False
    assert written["evidence"]["written"] is True
    assert (tmp_path / written["evidence"]["json_path"]).is_file()
    assert (tmp_path / written["evidence"]["markdown_path"]).is_file()


def test_phase11_chat_approval_consumption_readiness_json_is_no_consumption(tmp_path, capsys) -> None:
    preview_exit = cli.main(
        [
            "studio",
            "phase11-chat-approval-queue-write-execution-proof",
            "--vault-root",
            str(tmp_path),
            "--message",
            "Create a new project for consumption CLI",
            "--intent",
            "project-create",
            "--json",
        ]
    )
    preview_payload = json.loads(capsys.readouterr().out)
    digest = preview_payload["result"]["digest_proof"]["action_digest"]
    write_exit = cli.main(
        [
            "studio",
            "phase11-chat-approval-queue-write-execution-proof",
            "--vault-root",
            str(tmp_path),
            "--message",
            "Create a new project for consumption CLI",
            "--intent",
            "project-create",
            "--expected-action-digest",
            digest,
            "--write-approval",
            "--json",
        ]
    )
    write_payload = json.loads(capsys.readouterr().out)
    approval_id = write_payload["result"]["summary"]["approval_id"]

    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-approval-consumption-readiness-contract",
            "--vault-root",
            str(tmp_path),
            "--approval-id",
            approval_id,
            "--message",
            "Create a new project for consumption CLI",
            "--intent",
            "approval-action",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert preview_exit == 0
    assert write_exit == 0
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-approval-consumption-readiness-contract"
    assert result["surface"] == "phase11_chat_approval_consumption_readiness_contract"
    assert result["summary"]["selected_approval_id"] == approval_id
    assert result["summary"]["approval_status_mutated"] is False
    assert result["summary"]["approval_execution_called"] is False
    assert result["summary"]["target_write_performed"] is False
    assert result["exact_once_marker_preview"]["marker_written_now"] is False


def test_phase11_chat_approval_consumption_executor_json_writes_marker_target_and_audit(tmp_path, capsys) -> None:
    message = "Create a new project for consumption executor CLI"
    preview_exit = cli.main(
        [
            "studio",
            "phase11-chat-approval-queue-write-execution-proof",
            "--vault-root",
            str(tmp_path),
            "--message",
            message,
            "--intent",
            "project-create",
            "--json",
        ]
    )
    preview_payload = json.loads(capsys.readouterr().out)
    action_digest = preview_payload["result"]["digest_proof"]["action_digest"]
    write_exit = cli.main(
        [
            "studio",
            "phase11-chat-approval-queue-write-execution-proof",
            "--vault-root",
            str(tmp_path),
            "--message",
            message,
            "--intent",
            "project-create",
            "--expected-action-digest",
            action_digest,
            "--write-approval",
            "--json",
        ]
    )
    write_payload = json.loads(capsys.readouterr().out)
    approval_id = write_payload["result"]["summary"]["approval_id"]
    target_path = write_payload["result"]["summary"]["target_path_preview"]
    StudioService(tmp_path).approve(approval_id, reviewed_by="cli-test")
    readiness_exit = cli.main(
        [
            "studio",
            "phase11-chat-approval-consumption-readiness-contract",
            "--vault-root",
            str(tmp_path),
            "--approval-id",
            approval_id,
            "--message",
            message,
            "--json",
        ]
    )
    readiness_payload = json.loads(capsys.readouterr().out)
    consumption_digest = readiness_payload["result"]["digest_proof"]["consumption_digest"]

    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-approval-consumption-executor",
            "--vault-root",
            str(tmp_path),
            "--approval-id",
            approval_id,
            "--expected-consumption-digest",
            consumption_digest,
            "--message",
            message,
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert preview_exit == 0
    assert write_exit == 0
    assert readiness_exit == 0
    assert exit_code == 0
    assert payload["action"] == "studio.phase11-chat-approval-consumption-executor"
    assert result["surface"] == "phase11_chat_approval_consumption_executor"
    assert result["summary"]["approval_consumed"] is True
    assert result["summary"]["target_write_performed"] is True
    assert result["summary"]["agent_bus_task_written"] is False
    assert (tmp_path / target_path).exists()
    assert (tmp_path / result["exact_once_marker"]["marker_path"]).exists()
    assert (tmp_path / result["audit_record"]["audit_record_path"]).exists()


def test_phase11_chat_companion_selection_preview_json_blocks_writes(tmp_path, capsys) -> None:
    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-approval-preview",
            "--vault-root",
            str(tmp_path),
            "--requested-runtime",
            "hermes",
            "--current-runtime",
            "openclaw",
            "--message",
            "Switch companion to Hermes",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-companion-selection-approval-preview"
    assert result["surface"] == "phase11_chat_companion_selection_approval_preview"
    assert result["summary"]["approval_preview_ready"] is True
    assert result["summary"]["companion_selection_written"] is False
    assert result["future_approval_packet_preview"]["approval_request_created"] is False
    assert result["authority"]["companion_selection_write_allowed"] is False
    assert result["authority"]["identity_ledger_mutation_allowed"] is False


def test_phase11_chat_companion_selection_queue_write_readiness_json_blocks_writes(tmp_path, capsys) -> None:
    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-queue-write-readiness",
            "--vault-root",
            str(tmp_path),
            "--requested-runtime",
            "hermes",
            "--current-runtime",
            "openclaw",
            "--message",
            "Switch companion to Hermes",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-companion-selection-queue-write-readiness"
    assert result["surface"] == "phase11_chat_companion_selection_queue_write_readiness"
    assert result["summary"]["queue_write_readiness_ready"] is True
    assert result["summary"]["approval_request_created"] is False
    assert result["summary"]["approval_queue_writer_called"] is False
    assert result["summary"]["companion_selection_written"] is False
    assert result["future_queue_write_packet_preview"]["approval_request_created"] is False
    assert result["authority"]["approval_queue_write_allowed"] is False
    assert result["authority"]["companion_selection_write_allowed"] is False


def test_phase11_chat_companion_selection_queue_write_execution_json_creates_approval_only(tmp_path, capsys) -> None:
    preview_exit = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-queue-write-readiness",
            "--vault-root",
            str(tmp_path),
            "--requested-runtime",
            "hermes",
            "--current-runtime",
            "openclaw",
            "--message",
            "Switch companion to Hermes",
            "--json",
        ]
    )
    preview_payload = json.loads(capsys.readouterr().out)
    digest = preview_payload["result"]["digest_proof"]["queue_write_digest"]

    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-queue-write-execution-proof",
            "--vault-root",
            str(tmp_path),
            "--requested-runtime",
            "hermes",
            "--current-runtime",
            "openclaw",
            "--message",
            "Switch companion to Hermes",
            "--expected-queue-write-digest",
            digest,
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert preview_exit == 0
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-companion-selection-queue-write-execution-proof"
    assert result["surface"] == "phase11_chat_companion_selection_queue_write_execution_proof"
    assert result["summary"]["approval_request_created"] is True
    assert result["summary"]["approval_status"] == "pending"
    assert result["summary"]["approval_execution_called"] is False
    assert result["summary"]["companion_selection_written"] is False
    assert result["summary"]["runtime_control_performed"] is False
    assert result["summary"]["provider_call_performed"] is False
    assert result["authority"]["companion_selection_write_allowed"] is False
    assert (tmp_path / result["approval_record"]["approval_path"]).exists()
    assert not (tmp_path / "runtime" / "studio" / "chat" / "companion-selection.json").exists()


def test_phase11_chat_companion_selection_approval_consumption_readiness_json_is_read_only(
    tmp_path,
    capsys,
) -> None:
    preview_exit = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-queue-write-readiness",
            "--vault-root",
            str(tmp_path),
            "--requested-runtime",
            "hermes",
            "--current-runtime",
            "openclaw",
            "--message",
            "Switch companion to Hermes",
            "--json",
        ]
    )
    preview_payload = json.loads(capsys.readouterr().out)
    digest = preview_payload["result"]["digest_proof"]["queue_write_digest"]
    write_exit = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-queue-write-execution-proof",
            "--vault-root",
            str(tmp_path),
            "--requested-runtime",
            "hermes",
            "--current-runtime",
            "openclaw",
            "--message",
            "Switch companion to Hermes",
            "--expected-queue-write-digest",
            digest,
            "--json",
        ]
    )
    write_payload = json.loads(capsys.readouterr().out)
    approval_id = write_payload["result"]["approval_record"]["approval_id"]

    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-approval-consumption-readiness",
            "--vault-root",
            str(tmp_path),
            "--approval-id",
            approval_id,
            "--message",
            "Switch companion to Hermes",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]

    assert preview_exit == 0
    assert write_exit == 0
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-companion-selection-approval-consumption-readiness"
    assert result["surface"] == "phase11_chat_companion_selection_approval_consumption_readiness"
    assert result["summary"]["approval_status"] == "pending"
    assert result["summary"]["consumption_preview_ready"] is True
    assert result["summary"]["approval_execution_called"] is False
    assert result["summary"]["companion_selection_written"] is False
    assert result["summary"]["target_write_performed"] is False
    assert result["authority"]["approval_execution_allowed"] is False
    assert result["authority"]["companion_selection_write_allowed"] is False
    assert not (tmp_path / "runtime" / "studio" / "chat" / "companion-selection.json").exists()


def test_phase11_chat_companion_selection_approval_consumption_executor_json_writes_selection_once(
    tmp_path,
    capsys,
) -> None:
    preview_exit = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-queue-write-readiness",
            "--vault-root",
            str(tmp_path),
            "--requested-runtime",
            "hermes",
            "--current-runtime",
            "openclaw",
            "--message",
            "Switch companion to Hermes",
            "--json",
        ]
    )
    preview_payload = json.loads(capsys.readouterr().out)
    queue_digest = preview_payload["result"]["digest_proof"]["queue_write_digest"]
    write_exit = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-queue-write-execution-proof",
            "--vault-root",
            str(tmp_path),
            "--requested-runtime",
            "hermes",
            "--current-runtime",
            "openclaw",
            "--message",
            "Switch companion to Hermes",
            "--expected-queue-write-digest",
            queue_digest,
            "--json",
        ]
    )
    write_payload = json.loads(capsys.readouterr().out)
    approval_id = write_payload["result"]["approval_record"]["approval_id"]
    readiness_exit = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-approval-consumption-readiness",
            "--vault-root",
            str(tmp_path),
            "--approval-id",
            approval_id,
            "--message",
            "Switch companion to Hermes",
            "--json",
        ]
    )
    readiness_payload = json.loads(capsys.readouterr().out)
    consumption_digest = readiness_payload["result"]["digest_proof"]["consumption_digest"]

    exit_code = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-approval-consumption-executor",
            "--vault-root",
            str(tmp_path),
            "--approval-id",
            approval_id,
            "--message",
            "Switch companion to Hermes",
            "--expected-consumption-digest",
            consumption_digest,
            "--operator-id",
            "cli-test",
            "--operator-approval-statement",
            "operator approved companion selection consumption",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    duplicate_exit = cli.main(
        [
            "studio",
            "phase11-chat-companion-selection-approval-consumption-executor",
            "--vault-root",
            str(tmp_path),
            "--approval-id",
            approval_id,
            "--message",
            "Switch companion to Hermes",
            "--expected-consumption-digest",
            consumption_digest,
            "--operator-id",
            "cli-test",
            "--operator-approval-statement",
            "operator approved companion selection consumption",
            "--json",
        ]
    )
    duplicate_payload = json.loads(capsys.readouterr().out)
    target = json.loads(
        (tmp_path / "runtime" / "studio" / "chat" / "companion-selection.json").read_text(encoding="utf-8")
    )

    assert preview_exit == 0
    assert write_exit == 0
    assert readiness_exit == 0
    assert exit_code == 0
    assert duplicate_exit == 1
    assert payload["ok"] is True
    assert payload["action"] == "studio.phase11-chat-companion-selection-approval-consumption-executor"
    assert result["surface"] == "phase11_chat_companion_selection_approval_consumption_executor"
    assert result["summary"]["approval_consumed"] is True
    assert result["summary"]["exact_once_marker_written"] is True
    assert result["summary"]["companion_selection_written"] is True
    assert result["authority"]["companion_selection_write_allowed"] is True
    assert result["authority"]["runtime_dispatch_allowed"] is False
    assert result["authority"]["provider_calls_allowed"] is False
    assert target["selected_runtime_id"] == "hermes"
    assert "exact_once_marker_already_present" in duplicate_payload["result"]["blocked_reasons"]
