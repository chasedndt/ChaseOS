"""Phase 11 Chat native Studio panel tests."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


VAULT = Path(__file__).resolve().parents[3]
SHELL = Path(__file__).resolve().parent
sys.path.insert(0, str(VAULT))


@pytest.fixture()
def api(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
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
    from runtime.studio.shell.api import StudioAPI

    return StudioAPI(str(tmp_path))


@pytest.fixture()
def registry(tmp_path):
    from runtime.studio.shell.panel_registry import build_native_shell_panel_registry

    return build_native_shell_panel_registry(str(tmp_path))


@pytest.fixture()
def html_text():
    return (SHELL / "frontend" / "index.html").read_text(encoding="utf-8")


@pytest.fixture()
def css_text():
    return (SHELL / "frontend" / "styles.css").read_text(encoding="utf-8")


@pytest.fixture()
def js_text():
    return (SHELL / "frontend" / "app.js").read_text(encoding="utf-8")


def _seed_operator_today_workflow(root: Path) -> None:
    registry = root / "runtime" / "workflows" / "registry"
    registry.mkdir(parents=True, exist_ok=True)
    (registry / "operator_today.yaml").write_text(
        "\n".join(
            [
                "id: operator_today",
                "name: Operator Today",
                "version: '1.0'",
                "description: Test operator briefing workflow.",
                "task_type: operator-briefing",
                "role_card: operator-briefing",
                "trigger_type: manual",
                "owner: operator",
                "status: active",
                "permission_ceiling: standard",
                "writeback_targets:",
                "  - 07_LOGS/Operator-Briefs/",
                "failure_behavior: escalate",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_api_returns_chat_panel_envelope(api) -> None:
    response = api.get_phase11_chat_panel_contract("Create a new project")

    assert response["ok"] is True
    assert response["status"] == "ok"
    assert response["surface"] == "phase11_chat_panel_contract"
    assert response["blocked_authority"] == []
    assert response["data"]["native_panel"]["panel_id"] == "chat"
    assert response["data"]["chat_workspaces_foundation"]["summary"]["native_chat_project_model_ready"] is True
    assert response["data"]["chat_workspace_proposal_writer"]["surface"] == "phase11_chat_workspace_proposal_writer"
    assert response["data"]["chat_workspace_proposal_writer"]["summary"]["proposal_kind"] == "create_workspace"
    assert response["data"]["chat_workspace_proposal_writer"]["summary"]["approval_request_created"] is False
    assert response["data"]["chat_workspace_proposal_consumption_executor"]["surface"] == (
        "phase11_chat_workspace_proposal_consumption_executor"
    )
    assert response["data"]["chat_workspace_target_state_executor"]["surface"] == (
        "phase11_chat_workspace_target_state_executor"
    )
    assert response["data"]["chat_route_state_and_message_drafts"]["surface"] == (
        "phase11_chat_route_state_and_message_drafts"
    )
    assert response["data"]["chat_runtime_board_handoff_proposal"]["surface"] == (
        "phase11_chat_runtime_board_handoff_proposal"
    )
    assert response["data"]["chat_schedule_proposal_packet"]["surface"] == "phase11_chat_schedule_proposal_packet"
    assert response["data"]["chat_schedule_proposal_consumption_executor"]["surface"] == (
        "phase11_chat_schedule_proposal_consumption_executor"
    )
    assert response["data"]["chat_approved_schedule_intent_writer"]["surface"] == (
        "phase11_chat_approved_schedule_intent_writer"
    )
    assert response["data"]["chat_schedule_intent_activation_readiness"]["surface"] == (
        "phase11_chat_schedule_intent_activation_readiness"
    )
    assert response["data"]["chat_approved_schedule_activation_executor"]["surface"] == (
        "phase11_chat_approved_schedule_activation_executor"
    )
    assert response["data"]["chat_schedule_adapter_export_readiness"]["surface"] == (
        "phase11_chat_schedule_adapter_export_readiness"
    )
    assert response["data"]["chat_approved_schedule_adapter_export_packet_writer"]["surface"] == (
        "phase11_chat_approved_schedule_adapter_export_packet_writer"
    )
    assert response["data"]["chat_schedule_ui_action_controls_and_readback"]["surface"] == (
        "phase11_chat_schedule_ui_action_controls_and_readback"
    )
    assert response["data"]["chat_schedule_ui_action_controls_and_readback"]["summary"]["manual_ui_test_ready"] is True
    assert response["data"]["chat_runtime_board_handoff_proposal"]["summary"]["approval_request_created"] is False
    assert response["data"]["chat_runtime_board_handoff_proposal"]["target_write_proof"]["runtime_board_written"] is False
    json.dumps(response)


def test_api_returns_chat_workspace_foundation(api) -> None:
    response = api.get_phase11_chat_workspaces_foundation("Open a Hermes thread")

    assert response["ok"] is True
    assert response["status"] == "ok"
    assert response["surface"] == "phase11_chat_workspaces_foundation"
    assert response["data"]["read_only"] is True
    assert response["data"]["authority"]["chat_thread_create_allowed"] is False
    assert response["data"]["readiness"]["native_thread_creation_blocked"] is True
    json.dumps(response)


def test_api_chat_workspace_foundation_runtime_catalog_is_passive(tmp_path, monkeypatch) -> None:
    import runtime.studio.phase11_chat_workspaces_foundation as foundation
    from runtime.studio.shell.api import StudioAPI

    calls: list[tuple[str, bool]] = []

    def fake_live_status(vault, adapter_id, *, probe_wsl_processes=True):
        calls.append((str(adapter_id), bool(probe_wsl_processes)))
        return {
            "ok": True,
            "runtime": adapter_id,
            "adapter_id": adapter_id,
            "status": "not_running",
            "status_source": "none",
            "coordination_state": "heartbeat_missing",
            "dispatch_ready": False,
            "runtime_can_receive_chat": False,
            "gateway_port_online": False,
            "gateway_port_listening": None,
            "gateway_ports_checked": [],
            "heartbeat_online": False,
            "heartbeat_freshness": "missing",
            "blocked_reasons": ["agent_bus_heartbeat_not_fresh"],
            "wsl_process_probe_enabled": bool(probe_wsl_processes),
        }

    monkeypatch.setattr(foundation, "build_runtime_live_status", fake_live_status)

    response = StudioAPI(str(tmp_path)).get_phase11_chat_workspaces_foundation("Open Hermes")

    assert response["ok"] is True
    assert calls
    assert all(probe_wsl_processes is False for _adapter_id, probe_wsl_processes in calls)


def test_api_creates_local_chat_folder_and_thread(api) -> None:
    folder = api.create_chat_folder(workspace_id="runtime-ops", label="Client Alpha")
    thread = api.create_chat_thread(
        title="Client Alpha chat",
        workspace_id="runtime-ops",
        folder_id=folder["data"]["folder"]["folder_id"],
        folder_label=folder["data"]["folder"]["label"],
        runtime_id="openclaw",
    )
    foundation = api.get_phase11_chat_workspaces_foundation("Client Alpha")

    assert folder["ok"] is True
    assert thread["ok"] is True
    assert folder["data"]["folder"]["label"] == "Client Alpha"
    assert thread["data"]["conversation"]["folder_label"] == "Client Alpha"
    assert thread["data"]["conversation"]["runtime_label"] == "OpenClaw"
    assert thread["data"]["conversation"]["thread_id"] in {
        item["thread_id"] for item in foundation["data"]["threads"]
    }


def test_api_manages_local_chat_folders_and_threads(api) -> None:
    folder = api.create_chat_folder(workspace_id="runtime-ops", label="Coding")
    thread = api.create_chat_thread(
        title="Coding chat",
        workspace_id="runtime-ops",
        folder_id=folder["data"]["folder"]["folder_id"],
        folder_label=folder["data"]["folder"]["label"],
        runtime_id="hermes",
    )
    thread_id = thread["data"]["conversation"]["thread_id"]

    renamed = api.rename_chat_folder(
        workspace_id="runtime-ops",
        folder_id=folder["data"]["folder"]["folder_id"],
        label="Engineering",
    )
    moved = api.move_chat_thread(
        thread_id=thread_id,
        workspace_id="runtime-ops",
        folder_id="runtime-control",
        folder_label="Runtime Control",
    )
    deleted_folder = api.delete_chat_folder(
        workspace_id="runtime-ops",
        folder_id=folder["data"]["folder"]["folder_id"],
        move_threads_to_folder_id="runtime-control",
        move_threads_to_folder_label="Runtime Control",
    )
    deleted_thread = api.delete_chat_thread(thread_id=thread_id)
    foundation = api.get_phase11_chat_workspaces_foundation("Coding")

    assert renamed["ok"] is True
    assert renamed["data"]["folder"]["label"] == "Engineering"
    assert moved["ok"] is True
    assert moved["data"]["conversation"]["folder_id"] == "runtime-control"
    assert deleted_folder["ok"] is True
    assert deleted_thread["ok"] is True
    assert thread_id not in {item["thread_id"] for item in foundation["data"]["threads"]}


def test_api_saves_route_state_with_folder_metadata(api) -> None:
    folder = api.create_chat_folder(workspace_id="runtime-ops", label="Operations")
    thread = api.create_chat_thread(
        title="Operations chat",
        workspace_id="runtime-ops",
        folder_id=folder["data"]["folder"]["folder_id"],
        folder_label=folder["data"]["folder"]["label"],
        runtime_id="hermes",
    )
    route = api.save_phase11_chat_route_state(
        thread_id=thread["data"]["conversation"]["thread_id"],
        workspace_id="runtime-ops",
        folder_id=folder["data"]["folder"]["folder_id"],
    )

    assert route["ok"] is True
    assert route["data"]["summary"]["route_state_written"] is True
    assert route["data"]["summary"]["selected_folder_id"] == folder["data"]["folder"]["folder_id"]


def test_api_returns_chat_workspace_proposal_writer(api) -> None:
    response = api.get_phase11_chat_workspace_proposal_writer("Open a Hermes thread")

    assert response["ok"] is True
    assert response["status"] == "ok"
    assert response["surface"] == "phase11_chat_workspace_proposal_writer"
    assert response["data"]["summary"]["proposal_kind"] == "create_thread"
    assert response["data"]["summary"]["runtime_id"] == "Hermes"
    assert response["data"]["digest_proof"]["proposal_digest"]
    assert response["data"]["summary"]["approval_request_created"] is False
    assert response["data"]["target_write_proof"]["target_file_written"] is False
    json.dumps(response)


def test_api_blocks_workspace_proposal_consumption_without_exact_inputs(api) -> None:
    response = api.execute_phase11_chat_workspace_proposal_consumption()

    assert response["ok"] is False
    assert response["surface"] == "phase11_chat_workspace_proposal_consumption_executor"
    assert response["error"]["code"] == "phase11_chat_workspace_proposal_consumption_blocked"
    assert "approval_id_required_for_workspace_proposal_consumption" in response["error"]["message"]
    assert "expected_proposal_digest_required" in response["error"]["message"]


def test_api_blocks_workspace_target_state_without_exact_inputs(api) -> None:
    response = api.execute_phase11_chat_workspace_target_state()

    assert response["ok"] is False
    assert response["surface"] == "phase11_chat_workspace_target_state_executor"
    assert response["error"]["code"] == "phase11_chat_workspace_target_state_blocked"
    assert "expected_proposal_digest_required" in response["error"]["message"]
    assert "operator_target_state_statement_required" in response["error"]["message"]


def test_api_persists_local_route_state_and_message_draft_only(api) -> None:
    preview = api.get_phase11_chat_route_state_and_message_drafts(
        selected_thread_id="runtime-ops-openclaw-chat"
    )
    route = api.save_phase11_chat_route_state(
        selected_thread_id="runtime-ops-openclaw-chat"
    )
    draft = api.save_phase11_chat_message_draft(
        selected_thread_id="runtime-ops-openclaw-chat",
        draft_text="Review the runtime status before dispatch.",
        message_intent="runtime_status_draft",
    )
    secret = api.save_phase11_chat_message_draft(
        selected_thread_id="runtime-ops-openclaw-chat",
        draft_text="OPENAI_API_KEY=test-key-thisShouldNeverPersist123456789",
    )

    assert preview["ok"] is True
    assert preview["surface"] == "phase11_chat_route_state_and_message_drafts"
    assert preview["data"]["summary"]["route_state_written"] is False
    assert route["ok"] is True
    assert route["data"]["summary"]["route_state_written"] is True
    assert route["data"]["summary"]["chat_message_sent"] is False
    assert route["data"]["summary"]["agent_bus_task_written"] is False
    assert draft["ok"] is True
    assert draft["data"]["summary"]["draft_written"] is True
    assert draft["data"]["summary"]["message_intent"] == "runtime_status_draft"
    assert draft["data"]["summary"]["chat_transcript_written"] is False
    assert draft["data"]["summary"]["runtime_board_written"] is False
    assert draft["data"]["summary"]["schedule_mutated"] is False
    assert secret["ok"] is False
    assert secret["error"]["code"] == "phase11_chat_message_draft_blocked"
    assert "secret_or_credential_indicator_present" in secret["error"]["message"]


def test_api_queues_runtime_board_handoff_approval_only_with_exact_digest(api) -> None:
    preview = api.get_phase11_chat_runtime_board_handoff_proposal(
        selected_thread_id="runtime-ops-openclaw-chat",
        handoff_summary="Send this runtime chat to the OpenClaw board.",
    )
    digest = preview["data"]["digest_proof"]["handoff_digest"]
    queued = api.request_phase11_chat_runtime_board_handoff_proposal(
        digest,
        selected_thread_id="runtime-ops-openclaw-chat",
        handoff_summary="Send this runtime chat to the OpenClaw board.",
    )
    mismatch = api.request_phase11_chat_runtime_board_handoff_proposal(
        "bad-digest",
        selected_thread_id="runtime-ops-openclaw-chat",
        handoff_summary="Send this runtime chat to the OpenClaw board.",
    )

    assert preview["ok"] is True
    assert preview["surface"] == "phase11_chat_runtime_board_handoff_proposal"
    assert preview["data"]["summary"]["approval_request_created"] is False
    assert preview["data"]["target_write_proof"]["runtime_board_written"] is False
    assert queued["ok"] is True
    assert queued["data"]["summary"]["approval_request_created"] is True
    assert queued["data"]["approval_queue_write"]["queue_writer_called"] is True
    assert queued["data"]["target_write_proof"]["target_file_written"] is False
    assert queued["data"]["target_write_proof"]["agent_bus_task_written"] is False
    assert mismatch["ok"] is False
    assert mismatch["error"]["code"] == "phase11_chat_runtime_board_handoff_blocked"
    assert "expected_handoff_digest_mismatch" in mismatch["error"]["message"]


def test_api_queues_schedule_proposal_approval_only_with_exact_digest(api) -> None:
    preview = api.get_phase11_chat_schedule_proposal_packet(
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a later morning check.",
    )
    digest = preview["data"]["digest_proof"]["schedule_digest"]
    queued = api.request_phase11_chat_schedule_proposal_packet(
        digest,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a later morning check.",
    )
    mismatch = api.request_phase11_chat_schedule_proposal_packet(
        "bad-digest",
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a later morning check.",
    )

    assert preview["ok"] is True
    assert preview["surface"] == "phase11_chat_schedule_proposal_packet"
    assert preview["data"]["summary"]["approval_request_created"] is False
    assert preview["data"]["target_write_proof"]["schedule_intent_written"] is False
    assert queued["ok"] is True
    assert queued["data"]["summary"]["approval_request_created"] is True
    assert queued["data"]["approval_queue_write"]["queue_writer_called"] is True
    assert queued["data"]["target_write_proof"]["target_file_written"] is False
    assert queued["data"]["target_write_proof"]["schedule_index_regenerated"] is False
    assert mismatch["ok"] is False
    assert mismatch["error"]["code"] == "phase11_chat_schedule_proposal_blocked"
    assert "expected_schedule_digest_mismatch" in mismatch["error"]["message"]


def test_api_consumes_schedule_proposal_into_staged_record_only(api) -> None:
    preview = api.get_phase11_chat_schedule_proposal_packet(
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a later morning check.",
    )
    digest = preview["data"]["digest_proof"]["schedule_digest"]
    queued = api.request_phase11_chat_schedule_proposal_packet(
        digest,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a later morning check.",
    )
    approval_id = queued["data"]["summary"]["approval_id"]
    target_path = queued["data"]["summary"]["target_path_preview"]
    blocked = api.execute_phase11_chat_schedule_proposal_consumption()
    consumed = api.execute_phase11_chat_schedule_proposal_consumption(
        approval_id,
        digest,
        operator_approval_statement="Approved for staged schedule proposal consumption only.",
    )

    assert blocked["ok"] is False
    assert blocked["surface"] == "phase11_chat_schedule_proposal_consumption_executor"
    assert blocked["error"]["code"] == "phase11_chat_schedule_proposal_consumption_blocked"
    assert "approval_id_required_for_schedule_proposal_consumption" in blocked["error"]["message"]
    assert consumed["ok"] is True
    assert consumed["surface"] == "phase11_chat_schedule_proposal_consumption_executor"
    assert consumed["data"]["summary"]["approval_consumed"] is True
    assert consumed["data"]["target_write"]["staged_schedule_proposal_written"] is True
    assert consumed["data"]["target_write"]["target_file_written"] is False
    assert consumed["data"]["target_write"]["schedule_intent_written"] is False
    assert (Path(api._vault_root) / consumed["data"]["target_write"]["staged_schedule_proposal_path"]).exists()
    assert (Path(api._vault_root) / target_path).exists() is False


def test_api_writes_approved_schedule_intent_and_index_only(api) -> None:
    root = Path(api._vault_root)
    _seed_operator_today_workflow(root)
    preview = api.get_phase11_chat_schedule_proposal_packet(
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a later morning check.",
    )
    digest = preview["data"]["digest_proof"]["schedule_digest"]
    queued = api.request_phase11_chat_schedule_proposal_packet(
        digest,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a later morning check.",
    )
    consumed = api.execute_phase11_chat_schedule_proposal_consumption(
        queued["data"]["summary"]["approval_id"],
        digest,
        operator_approval_statement="Approved for staged schedule proposal consumption only.",
    )
    staged_path = consumed["data"]["target_write"]["staged_schedule_proposal_path"]
    blocked = api.execute_phase11_chat_approved_schedule_intent_writer()
    written = api.execute_phase11_chat_approved_schedule_intent_writer(
        staged_proposal_path=staged_path,
        expected_schedule_digest=digest,
        operator_schedule_write_statement="Approved to write schedule YAML and regenerate the schedule index only.",
    )

    assert blocked["ok"] is False
    assert blocked["surface"] == "phase11_chat_approved_schedule_intent_writer"
    assert blocked["error"]["code"] == "phase11_chat_approved_schedule_intent_writer_blocked"
    assert "operator_schedule_write_statement_required" in blocked["error"]["message"]
    assert written["ok"] is True
    assert written["surface"] == "phase11_chat_approved_schedule_intent_writer"
    assert written["data"]["target_write"]["target_file_written"] is True
    assert written["data"]["target_write"]["schedule_intent_written"] is True
    assert written["data"]["target_write"]["schedule_index_regenerated"] is True
    assert written["data"]["target_write"]["schedule_enabled"] is False
    assert written["data"]["target_write"]["external_scheduler_changed"] is False
    assert (root / written["data"]["target_write"]["target_path"]).exists()
    assert (root / "runtime" / "schedules" / "index.yaml").exists()


def test_api_queues_schedule_activation_readiness_approval_only(api) -> None:
    root = Path(api._vault_root)
    _seed_operator_today_workflow(root)
    preview = api.get_phase11_chat_schedule_proposal_packet(
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a later morning check.",
    )
    schedule_digest = preview["data"]["digest_proof"]["schedule_digest"]
    queued_schedule = api.request_phase11_chat_schedule_proposal_packet(
        schedule_digest,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for a later morning check.",
    )
    consumed = api.execute_phase11_chat_schedule_proposal_consumption(
        queued_schedule["data"]["summary"]["approval_id"],
        schedule_digest,
        operator_approval_statement="Approved for staged schedule proposal consumption only.",
    )
    written = api.execute_phase11_chat_approved_schedule_intent_writer(
        staged_proposal_path=consumed["data"]["target_write"]["staged_schedule_proposal_path"],
        expected_schedule_digest=schedule_digest,
        operator_schedule_write_statement="Approved to write schedule YAML and regenerate the schedule index only.",
    )
    schedule_id = written["data"]["target_write"]["schedule_id"]
    activation_preview = api.get_phase11_chat_schedule_intent_activation_readiness(schedule_id)
    activation_digest = activation_preview["data"]["digest_proof"]["activation_digest"]
    activation_queued = api.request_phase11_chat_schedule_intent_activation(
        activation_digest,
        schedule_id=schedule_id,
    )
    mismatch = api.request_phase11_chat_schedule_intent_activation(
        "bad-digest",
        schedule_id=schedule_id,
    )

    assert activation_preview["ok"] is True
    assert activation_preview["surface"] == "phase11_chat_schedule_intent_activation_readiness"
    assert activation_preview["data"]["target_write_proof"]["schedule_enabled"] is False
    assert activation_queued["ok"] is True
    assert activation_queued["data"]["approval_queue_write"]["approval_request_created"] is True
    assert activation_queued["data"]["target_write_proof"]["schedule_enabled"] is False
    assert activation_queued["data"]["target_write_proof"]["external_scheduler_changed"] is False
    assert mismatch["ok"] is False
    assert mismatch["error"]["code"] == "phase11_chat_schedule_intent_activation_blocked"
    assert "expected_activation_digest_mismatch" in mismatch["error"]["message"]


def test_api_executes_approved_schedule_activation_and_index_only(api) -> None:
    root = Path(api._vault_root)
    _seed_operator_today_workflow(root)
    preview = api.get_phase11_chat_schedule_proposal_packet(
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for approved activation.",
    )
    schedule_digest = preview["data"]["digest_proof"]["schedule_digest"]
    queued_schedule = api.request_phase11_chat_schedule_proposal_packet(
        schedule_digest,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for approved activation.",
    )
    consumed = api.execute_phase11_chat_schedule_proposal_consumption(
        queued_schedule["data"]["summary"]["approval_id"],
        schedule_digest,
        operator_approval_statement="Approved for staged schedule proposal consumption only.",
    )
    written = api.execute_phase11_chat_approved_schedule_intent_writer(
        staged_proposal_path=consumed["data"]["target_write"]["staged_schedule_proposal_path"],
        expected_schedule_digest=schedule_digest,
        operator_schedule_write_statement="Approved to write schedule YAML and regenerate the schedule index only.",
    )
    schedule_id = written["data"]["target_write"]["schedule_id"]
    activation_preview = api.get_phase11_chat_schedule_intent_activation_readiness(schedule_id)
    activation_digest = activation_preview["data"]["digest_proof"]["activation_digest"]
    activation_queued = api.request_phase11_chat_schedule_intent_activation(
        activation_digest,
        schedule_id=schedule_id,
    )
    blocked = api.execute_phase11_chat_approved_schedule_activation()
    executed = api.execute_phase11_chat_approved_schedule_activation(
        approval_id=activation_queued["data"]["approval_queue_write"]["approval_id"],
        expected_activation_digest=activation_digest,
        operator_activation_statement="Approved to enable this schedule and regenerate the schedule index only.",
    )

    assert blocked["ok"] is False
    assert blocked["surface"] == "phase11_chat_approved_schedule_activation_executor"
    assert blocked["error"]["code"] == "phase11_chat_approved_schedule_activation_blocked"
    assert "operator_activation_statement_required" in blocked["error"]["message"]
    assert executed["ok"] is True
    assert executed["surface"] == "phase11_chat_approved_schedule_activation_executor"
    assert executed["data"]["target_write"]["schedule_enabled"] is True
    assert executed["data"]["target_write"]["schedule_index_regenerated"] is True
    assert executed["data"]["target_write"]["external_scheduler_changed"] is False
    assert executed["data"]["target_write"]["openclaw_cron_changed"] is False
    assert executed["data"]["target_write"]["agent_bus_task_written"] is False
    assert executed["data"]["target_write"]["runtime_dispatched"] is False
    assert executed["data"]["target_write"]["discord_api_called"] is False
    assert executed["data"]["target_write"]["provider_call_performed"] is False
    assert executed["data"]["target_write"]["credential_value_read"] is False


def test_api_queues_schedule_adapter_export_readiness_packet(api) -> None:
    root = Path(api._vault_root)
    _seed_operator_today_workflow(root)
    preview = api.get_phase11_chat_schedule_proposal_packet(
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for adapter export readiness.",
    )
    schedule_digest = preview["data"]["digest_proof"]["schedule_digest"]
    queued = api.request_phase11_chat_schedule_proposal_packet(
        expected_schedule_digest=schedule_digest,
        workflow_id="operator_today",
        cron_expression="0 8 * * 1-5",
        schedule_summary="Schedule operator_today for adapter export readiness.",
    )
    consumed = api.execute_phase11_chat_schedule_proposal_consumption(
        approval_id=queued["data"]["summary"]["approval_id"],
        expected_schedule_digest=schedule_digest,
        operator_approval_statement="Approved for staged schedule proposal.",
    )
    written = api.execute_phase11_chat_approved_schedule_intent_writer(
        staged_proposal_path=consumed["data"]["target_write"]["staged_schedule_proposal_path"],
        expected_schedule_digest=schedule_digest,
        operator_schedule_write_statement="Approved to write disabled schedule intent.",
    )
    schedule_id = written["data"]["target_write"]["schedule_id"]
    activation_preview = api.get_phase11_chat_schedule_intent_activation_readiness(schedule_id)
    activation_digest = activation_preview["data"]["digest_proof"]["activation_digest"]
    activation_queued = api.request_phase11_chat_schedule_intent_activation(
        activation_digest,
        schedule_id=schedule_id,
    )
    activated = api.execute_phase11_chat_approved_schedule_activation(
        approval_id=activation_queued["data"]["approval_queue_write"]["approval_id"],
        expected_activation_digest=activation_digest,
        operator_activation_statement="Approved to enable this schedule and regenerate the schedule index only.",
    )
    export_preview = api.get_phase11_chat_schedule_adapter_export_readiness(
        runtime_adapter_target="openclaw",
        schedule_id=schedule_id,
    )
    export_digest = export_preview["data"]["digest_proof"]["export_digest"]
    export_queued = api.request_phase11_chat_schedule_adapter_export(
        expected_export_digest=export_digest,
        runtime_adapter_target="openclaw",
        schedule_id=schedule_id,
    )
    export_written = api.execute_phase11_chat_approved_schedule_adapter_export_packet_writer(
        approval_id=export_queued["data"]["approval_queue_write"]["approval_id"],
        expected_export_digest=export_digest,
        operator_export_write_statement="Approved to write the local adapter export packet only.",
    )
    mismatch = api.request_phase11_chat_schedule_adapter_export(
        expected_export_digest="bad-digest",
        runtime_adapter_target="openclaw",
        schedule_id=schedule_id,
    )

    assert activated["ok"] is True
    assert export_preview["ok"] is True
    assert export_preview["surface"] == "phase11_chat_schedule_adapter_export_readiness"
    assert export_preview["data"]["summary"]["enabled_schedule_count"] == 1
    assert export_preview["data"]["target_write_proof"]["export_packet_written"] is False
    assert export_preview["data"]["target_write_proof"]["external_scheduler_changed"] is False
    assert export_queued["ok"] is True
    assert export_queued["data"]["approval_queue_write"]["approval_request_created"] is True
    assert export_queued["data"]["target_write_proof"]["openclaw_cron_changed"] is False
    assert export_queued["data"]["target_write_proof"]["agent_bus_task_written"] is False
    assert export_queued["data"]["target_write_proof"]["runtime_dispatched"] is False
    assert export_queued["data"]["target_write_proof"]["discord_api_called"] is False
    assert export_queued["data"]["target_write_proof"]["provider_call_performed"] is False
    assert export_queued["data"]["target_write_proof"]["credential_value_read"] is False
    assert export_written["ok"] is True
    assert export_written["surface"] == "phase11_chat_approved_schedule_adapter_export_packet_writer"
    assert export_written["data"]["target_write"]["export_packet_written"] is True
    assert export_written["data"]["target_write"]["external_scheduler_changed"] is False
    assert export_written["data"]["target_write"]["openclaw_cron_changed"] is False
    assert export_written["data"]["target_write"]["agent_bus_task_written"] is False
    assert export_written["data"]["target_write"]["runtime_dispatched"] is False
    assert export_written["data"]["target_write"]["discord_api_called"] is False
    assert export_written["data"]["target_write"]["provider_call_performed"] is False
    assert export_written["data"]["target_write"]["credential_value_read"] is False
    assert (root / export_written["data"]["target_write"]["target_path"]).exists()
    assert mismatch["ok"] is False
    assert mismatch["error"]["code"] == "phase11_chat_schedule_adapter_export_blocked"
    assert "expected_export_digest_mismatch" in mismatch["error"]["message"]


def test_api_returns_schedule_ui_action_controls_and_readback(api) -> None:
    response = api.get_phase11_chat_schedule_ui_action_controls_and_readback()

    assert response["ok"] is True
    assert response["surface"] == "phase11_chat_schedule_ui_action_controls_and_readback"
    assert response["data"]["summary"]["manual_ui_test_ready"] is True
    assert response["data"]["readiness"]["studio_chat_schedule_ui_no_secret_fields"] is True
    assert response["data"]["summary"]["external_scheduler_mutation_allowed"] is False
    assert response["data"]["summary"]["runtime_dispatch_allowed"] is False
    assert "execute_phase11_chat_approved_schedule_adapter_export_packet_writer" in response["data"]["api_methods"]
    json.dumps(response)


def test_api_blocks_no_credential_model_route(api) -> None:
    response = api.get_phase11_chat_panel_contract("Use OpenAI", "model-chat")
    data = response["data"]

    assert data["summary"]["model_route_required"] is True
    assert data["summary"]["route_execution_allowed"] is False
    assert data["authority"]["provider_calls_allowed"] is False
    assert data["live_routing_gate"]["live_routing_allowed_now"] is False
    assert data["live_routing_gate"]["provider_credentials_environment_present"] is False
    assert data["live_routing_gate"]["all_future_conditions_satisfied"] is False
    assert data["live_routing_gate"]["closeout_execution_blocked_by_design"] is False
    assert "operator_chat_execution_approval_missing" in data["live_routing_gate"]["blocked_reasons"]
    assert data["closeout_evidence"]["phase11_chat_provider_readiness_foundation_closed"] is True
    assert data["closeout_evidence"]["approval_queue_writes_added"] is True
    assert data["approval_handoff_queue_contract"]["authority"]["queue_write_allowed"] is False
    assert data["approval_queue_write_execution_proof"]["summary"]["approval_request_created"] is False


def test_panel_registry_chat_present(registry) -> None:
    panel = next(panel for panel in registry["panels"] if panel["id"] == "chat")

    assert panel["status"] == "mounted"
    assert panel["frontend_target"] == "panel-chat"
    assert panel["read_only"] is False
    assert panel["write_mode"] == "approval_gated"
    assert panel["api_methods"] == [
        "get_phase11_chat_panel_contract",
        "get_phase11_chat_workspaces_foundation",
        "get_phase11_chat_workspace_proposal_writer",
        "request_phase11_chat_workspace_proposal",
        "execute_phase11_chat_workspace_proposal_consumption",
        "execute_phase11_chat_workspace_target_state",
        "get_phase11_chat_route_state_and_message_drafts",
        "save_phase11_chat_route_state",
        "save_phase11_chat_message_draft",
        "get_phase11_chat_runtime_board_handoff_proposal",
        "request_phase11_chat_runtime_board_handoff_proposal",
        "get_phase11_chat_schedule_proposal_packet",
        "request_phase11_chat_schedule_proposal_packet",
        "execute_phase11_chat_schedule_proposal_consumption",
        "execute_phase11_chat_approved_schedule_intent_writer",
        "get_phase11_chat_schedule_intent_activation_readiness",
        "request_phase11_chat_schedule_intent_activation",
        "execute_phase11_chat_approved_schedule_activation",
        "get_phase11_chat_schedule_adapter_export_readiness",
        "request_phase11_chat_schedule_adapter_export",
        "execute_phase11_chat_approved_schedule_adapter_export_packet_writer",
        "get_phase11_chat_schedule_ui_action_controls_and_readback",
        "get_phase11_chat_authority_execution_controls",
        "execute_phase11_chat_authority_execution_controls",
        "get_phase11_chat_approval_handoff_queue_contract",
        "get_phase11_chat_conversation_persistence_contract",
        "get_phase11_chat_approval_queue_write_execution_proof",
        "request_phase11_chat_approval_queue_write",
        "get_phase11_chat_live_provider_execution_approval_preview",
        "get_phase11_chat_runtime_dispatch_readiness",
        "execute_phase11_chat_runtime_dispatch",
        "get_phase11_chat_browser_dispatch_readiness",
        "get_phase11_chat_approval_consumption_readiness",
        "get_phase11_chat_readonly_slash_command_responses",
        "get_phase11_chat_companion_status",
        "get_phase11_multi_companion_registry_readiness",
        "get_phase11_operator_companion_direction",
        "get_phase11_operator_companion_direction_answers",
        "get_phase11_companion_roster_ui_preview",
        "get_phase11_companion_memory_boundary_contract",
        "get_phase11_companion_memory_approval_preview",
        "request_phase11_companion_memory_approval",
        "execute_phase11_companion_memory_approved_execution_proof",
        "get_phase11_companion_memory_readback_search_preview",
        "get_phase11_companion_memory_ledger_write_approval_preview",
        "request_phase11_companion_memory_ledger_write_approval",
        "execute_phase11_companion_memory_approved_ledger_write_execution_proof",
        "get_phase11_companion_memory_ledger_read_model_preview",
        "get_phase11_companion_memory_real_ledger_activation_closeout",
        "get_phase11_companion_memory_context_readiness_preview",
        "get_phase11_chat_companion_selection_preview",
        "get_phase11_chat_companion_selection_queue_write_readiness",
        "execute_phase11_chat_companion_selection_queue_write",
        "get_phase11_chat_companion_selection_approval_consumption_readiness",
        "execute_phase11_chat_companion_selection_approval_consumption",
        "get_phase11_post_closeout_planning",
        "start_runtime_daemon",
        "stop_runtime_daemon",
        "get_daemon_status",
        "get_hermes_installation_info",
    ]


def test_panel_registry_chat_blocks_authority(registry) -> None:
    panel = next(panel for panel in registry["panels"] if panel["id"] == "chat")

    assert panel["blocked_authority"]["provider_calls"] is False
    assert panel["blocked_authority"]["workflow_execution"] is False
    assert panel["blocked_authority"]["approval_execution"] is False
    assert panel["blocked_authority"]["canonical_mutation"] is False
    assert registry["readiness"]["phase11_chat_panel_mounted"] is True
    assert registry["readiness"]["phase11_chat_live_routing_blocked"] is True
    assert registry["readiness"]["phase11_chat_original_objective_closed"] is True
    assert registry["readiness"]["phase11_chat_approval_handoff_queue_contract_closed"] is True
    assert registry["readiness"]["phase11_chat_conversation_persistence_contract_ready"] is True
    assert registry["readiness"]["phase11_chat_conversation_writes_blocked"] is True
    assert registry["readiness"]["phase11_post_closeout_planning_ready"] is True
    assert registry["readiness"]["phase11_chat_approval_queue_write_execution_proof_ready"] is True
    assert registry["readiness"]["phase11_chat_live_provider_execution_approval_preview_ready"] is True
    assert registry["readiness"]["phase11_chat_live_provider_calls_blocked"] is False
    assert registry["readiness"]["phase11_chat_live_provider_calls_digest_and_statement_gated"] is True
    assert registry["readiness"]["phase11_chat_authority_execution_controls_ready"] is True
    assert registry["readiness"]["phase11_chat_runtime_dispatch_readiness_contract_ready"] is True
    assert registry["readiness"]["phase11_chat_runtime_dispatch_executor_ready"] is True
    assert registry["readiness"]["phase11_chat_runtime_dispatch_blocked"] is True
    assert registry["readiness"]["phase11_chat_agent_bus_task_write_blocked"] is True
    assert registry["readiness"]["phase11_chat_agent_bus_task_write_approval_gated"] is True
    assert registry["readiness"]["phase11_chat_workflow_dispatch_blocked"] is True
    assert registry["readiness"]["phase11_chat_browser_dispatch_readiness_contract_ready"] is True
    assert registry["readiness"]["phase11_chat_browser_dispatch_blocked"] is True
    assert registry["readiness"]["phase11_chat_approval_consumption_readiness_contract_ready"] is True
    assert registry["readiness"]["phase11_chat_approval_consumption_blocked"] is True
    assert registry["readiness"]["phase11_chat_approval_status_mutation_blocked"] is True
    assert registry["readiness"]["phase11_companion_memory_approval_preview_ready"] is True
    assert registry["readiness"]["phase11_companion_memory_approved_execution_proof_ready"] is True
    assert registry["readiness"]["phase11_companion_memory_readback_search_preview_ready"] is True
    assert registry["readiness"]["phase11_companion_memory_ledger_write_approval_preview_ready"] is True
    assert registry["readiness"]["phase11_companion_memory_ledger_write_approval_queue_write_gated"] is True
    assert registry["readiness"]["phase11_companion_memory_approved_ledger_write_execution_proof_ready"] is True
    assert registry["readiness"]["phase11_companion_memory_ledger_read_model_preview_ready"] is True
    assert registry["readiness"]["phase11_companion_memory_context_readiness_preview_ready"] is True
    assert registry["readiness"]["phase11_companion_memory_context_runtime_credential_required"] is True
    assert registry["readiness"]["phase11_companion_memory_real_ledger_read_model_ready"] is True
    assert registry["readiness"]["phase11_companion_memory_real_ledger_write_approval_gated"] is True
    assert registry["readiness"]["phase11_companion_memory_proof_search_ready"] is True
    assert registry["readiness"]["phase11_companion_memory_real_ledger_read_blocked"] is False
    assert registry["readiness"]["phase11_companion_memory_real_ledger_write_blocked"] is True
    assert registry["readiness"]["phase11_companion_memory_approval_consumption_proof_only"] is True
    assert registry["readiness"]["phase11_companion_memory_ledger_writes_blocked"] is True
    assert registry["readiness"]["phase11_companion_memory_approval_queue_write_gated"] is True
    assert registry["readiness"]["phase11_chat_browser_launch_blocked"] is True
    assert registry["readiness"]["phase11_chat_readonly_slash_command_responses_ready"] is True
    assert registry["readiness"]["phase11_chat_readonly_slash_command_response_ui_ready"] is True
    assert registry["readiness"]["phase11_chat_readonly_slash_command_execution_blocked"] is True
    assert registry["readiness"]["phase11_chat_workspaces_foundation_ready"] is True
    assert registry["readiness"]["phase11_chat_workspace_proposal_writer_ready"] is True
    assert registry["readiness"]["phase11_chat_workspace_proposal_consumption_executor_ready"] is True
    assert registry["readiness"]["phase11_chat_workspace_target_state_executor_ready"] is True
    assert registry["readiness"]["phase11_chat_route_state_and_message_drafts_ready"] is True
    assert registry["readiness"]["phase11_chat_runtime_board_handoff_proposal_ready"] is True
    assert registry["readiness"]["phase11_chat_schedule_proposal_packet_ready"] is True
    assert registry["readiness"]["phase11_chat_schedule_proposal_consumption_executor_ready"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_intent_writer_ready"] is True
    assert registry["readiness"]["phase11_chat_schedule_intent_activation_readiness_ready"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_activation_executor_ready"] is True
    assert registry["readiness"]["phase11_chat_schedule_adapter_export_readiness_ready"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_adapter_export_packet_writer_ready"] is True
    assert registry["readiness"]["phase11_chat_schedule_ui_action_controls_and_readback_ready"] is True
    assert registry["readiness"]["phase11_chat_schedule_manual_ui_test_ready"] is True
    assert registry["readiness"]["phase11_chat_schedule_ui_readback_ready"] is True
    assert registry["readiness"]["phase11_chat_schedule_ui_no_secret_fields"] is True
    assert registry["readiness"]["phase11_chat_authority_tier_controls_ready"] is True
    assert registry["readiness"]["phase11_chat_authority_tier_controls_visible"] is True
    assert registry["readiness"]["phase11_chat_authority_tier_direct_execution_blocked"] is True
    assert registry["readiness"]["phase11_chat_authority_tier_no_secret_values"] is True
    assert registry["readiness"]["phase11_chat_authority_tier_provider_calls_blocked"] is True
    assert registry["readiness"]["phase11_chat_authority_tier_discord_calls_blocked"] is True
    assert registry["readiness"]["phase11_chat_authority_tier_agent_bus_writes_blocked"] is True
    assert registry["readiness"]["phase11_chat_authority_tier_runtime_dispatch_blocked"] is True
    assert registry["readiness"]["phase11_chat_authority_tier_external_cron_blocked"] is True
    assert registry["readiness"]["phase11_chat_route_state_persistence_ready"] is True
    assert registry["readiness"]["phase11_chat_message_draft_state_ready"] is True
    assert registry["readiness"]["phase11_chat_message_intent_state_ready"] is True
    assert registry["readiness"]["phase11_chat_workspace_proposal_requires_digest"] is True
    assert registry["readiness"]["phase11_chat_workspace_proposal_consumption_requires_approval_and_digest"] is True
    assert registry["readiness"]["phase11_chat_workspace_target_state_requires_proposal_digest_and_statement"] is True
    assert registry["readiness"]["phase11_chat_workspace_proposal_target_write_approval_gated"] is True
    assert registry["readiness"]["phase11_chat_workspace_proposal_target_write_blocked"] is True
    assert registry["readiness"]["phase11_chat_workspace_proposal_ambient_execution_blocked"] is True
    assert registry["readiness"]["phase11_chat_workspace_target_state_ambient_execution_blocked"] is True
    assert registry["readiness"]["phase11_chat_runtime_board_handoff_requires_digest"] is True
    assert registry["readiness"]["phase11_chat_runtime_board_handoff_approval_queue_gated"] is True
    assert registry["readiness"]["phase11_chat_runtime_board_handoff_ambient_execution_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_proposal_requires_digest"] is True
    assert registry["readiness"]["phase11_chat_schedule_proposal_approval_queue_gated"] is True
    assert registry["readiness"]["phase11_chat_schedule_proposal_ambient_execution_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_proposal_consumption_requires_approval_and_digest"] is True
    assert registry["readiness"]["phase11_chat_schedule_proposal_consumption_writes_staged_record_only"] is True
    assert registry["readiness"]["phase11_chat_schedule_proposal_consumption_schedule_yaml_write_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_proposal_consumption_index_regeneration_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_proposal_consumption_external_scheduler_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_intent_write_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_index_regeneration_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_intent_write_explicit_writer_ready"] is True
    assert registry["readiness"]["phase11_chat_schedule_index_regeneration_explicit_writer_ready"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_intent_writer_requires_staged_record_digest_statement"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_intent_writer_schedule_yaml_write_approval_gated"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_intent_writer_index_regeneration_approval_gated"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_intent_writer_external_scheduler_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_intent_activation_readiness_requires_schedule_id"] is True
    assert registry["readiness"]["phase11_chat_schedule_intent_activation_request_requires_digest"] is True
    assert registry["readiness"]["phase11_chat_schedule_intent_activation_approval_queue_gated"] is True
    assert registry["readiness"]["phase11_chat_schedule_intent_activation_execution_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_enable_still_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_enable_explicit_executor_ready"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_activation_requires_approval_and_digest"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_activation_enables_schedule_only"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_activation_external_scheduler_blocked"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_activation_cron_mutation_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_adapter_export_readiness_requires_adapter"] is True
    assert registry["readiness"]["phase11_chat_schedule_adapter_export_request_requires_digest"] is True
    assert registry["readiness"]["phase11_chat_schedule_adapter_export_packet_write_blocked"] is False
    assert registry["readiness"]["phase11_chat_approved_schedule_adapter_export_requires_approval_and_digest"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_adapter_export_writes_local_packet_only"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_adapter_export_external_scheduler_blocked"] is True
    assert registry["readiness"]["phase11_chat_approved_schedule_adapter_export_cron_mutation_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_adapter_export_external_scheduler_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_adapter_export_cron_mutation_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_external_cron_still_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_runtime_dispatch_still_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_activation_external_scheduler_blocked"] is True
    assert registry["readiness"]["phase11_chat_external_scheduler_mutation_blocked"] is True
    assert registry["readiness"]["phase11_chat_native_state_write_executor_ready"] is True
    assert registry["readiness"]["phase11_chat_native_thread_creation_blocked"] is True
    assert registry["readiness"]["phase11_chat_message_send_still_blocked"] is True
    assert registry["readiness"]["phase11_chat_transcript_write_still_blocked"] is True
    assert registry["readiness"]["phase11_chat_runtime_board_write_blocked"] is True
    assert registry["readiness"]["phase11_chat_schedule_mutation_blocked"] is True
    assert registry["readiness"]["phase11_next_recommended_pass"] == "phase11-chat-post-e2e-hardening"


def test_html_sidebar_and_panel_present(html_text) -> None:
    assert 'data-panel="chat"' in html_text
    assert 'id="panel-chat"' in html_text
    assert 'id="chat-message-input"' in html_text
    assert 'id="chat-slash-command-menu"' in html_text
    assert 'Slash command suggestions' in html_text
    assert 'id="chat-preview-button"' not in html_text
    assert 'id="chat-thread-navigator"' in html_text
    assert 'id="chat-new-thread-button"' in html_text
    assert 'id="chat-new-folder-button"' in html_text
    assert 'chat-folder-toggle' in html_text
    assert 'id="chat-create-panel"' in html_text
    assert 'id="chat-thread-search"' in html_text
    assert 'id="chat-attachment-tray"' in html_text
    assert 'id="chat-file-input"' in html_text
    assert 'id="chat-image-input"' in html_text
    assert 'class="phase11-chat-composer-box"' in html_text
    assert 'class="chat-tool-button"' in html_text
    assert 'id="chat-preview-body"' in html_text
    assert 'id="chat-provider-readiness"' in html_text
    assert 'data-write-mode="approval-gated"' in html_text
    assert "ChaseOS Chat" in html_text
    assert "Preview first" not in html_text
    assert "Runtime routed" not in html_text
    assert "Files staged locally" not in html_text
    assert "Actions governed" not in html_text


def test_css_chat_classes_present(css_text) -> None:
    assert ".phase11-chat-panel" in css_text
    assert ".phase11-chat-composer" in css_text
    assert ".phase11-chat-section" in css_text
    assert ".phase11-chat-list-item" in css_text
    assert ".phase11-chat-queue-write" in css_text
    assert ".phase11-chat-runtime-dispatch" in css_text
    assert ".phase11-chat-workspaces" in css_text
    assert ".phase11-chat-workspace-proposal-writer" in css_text
    assert ".phase11-chat-workspace-proposal-consumption" in css_text
    assert ".phase11-chat-workspace-target-state" in css_text
    assert ".phase11-chat-route-state-drafts" in css_text
    assert ".phase11-chat-runtime-board-handoff" in css_text
    assert ".phase11-chat-schedule-proposal" in css_text
    assert ".phase11-chat-schedule-proposal-consumption" in css_text
    assert ".phase11-chat-approved-schedule-intent-writer" in css_text
    assert ".phase11-chat-schedule-activation-readiness" in css_text
    assert ".phase11-chat-approved-schedule-activation" in css_text
    assert ".phase11-chat-workspace-grid-native" in css_text
    assert ".phase11-chat-thread-item" in css_text
    assert ".chat-thread-navigator" in css_text
    assert ".chat-folder-row" in css_text
    assert "body.chat-page-active #object-inspector" in css_text
    assert "body.chat-page-active #panel-chat" in css_text
    assert ".chat-rail-topline" in css_text
    assert ".chat-folder-dropdown-menu" in css_text
    assert ".chat-folder-toggle" in css_text
    assert ".chat-create-panel" in css_text
    assert ".chat-thread-search" in css_text
    assert ".phase11-chat-composer-box" in css_text
    assert ".chat-tool-button" in css_text
    assert ".phase11-chat-product-desk--fluent" in css_text
    assert ".phase11-chat-live-thread" in css_text
    assert ".phase11-chat-manage-menu" in css_text
    assert ".phase11-chat-thread-header" in css_text
    assert ".phase11-chat-thread-body" in css_text
    assert "body.chat-page-active .phase11-chat-main {\n  display: flex;" in css_text
    assert "body.chat-page-active .phase11-chat-panel .panel-title-row {\n  display: none;" in css_text
    assert "body.chat-page-active #chat-preview-body {\n  flex: 1 1 0;" in css_text
    assert "body.chat-page-active .phase11-chat-composer {\n  flex: 0 0 auto;" in css_text
    assert ".phase11-chat-inspector-block" in css_text
    assert ".phase11-chat-conversation-shell" in css_text
    assert ".phase11-chat-message" in css_text
    assert ".chat-attachment-tray" in css_text
    assert ".phase11-chat-approval-consumption" in css_text
    assert ".phase11-chat-slash-responses" in css_text
    assert ".phase11-chat-slash-card-grid" in css_text
    assert ".phase11-chat-slash-response-card" in css_text
    assert ".phase11-chat-slash-action-buttons" in css_text
    assert ".phase11-chat-slash-action-button" in css_text
    assert ".phase11-chat-companion-roster" in css_text
    assert ".phase11-chat-companion-roster-grid" in css_text
    assert ".phase11-chat-companion-roster-card" in css_text
    assert ".phase11-chat-companion-mark" in css_text
    assert ".phase11-chat-companion-memory-approval" in css_text
    assert ".phase11-chat-companion-memory-execution" in css_text
    assert ".phase11-chat-companion-memory-readback" in css_text
    assert ".phase11-chat-companion-memory-ledger-write" in css_text
    assert ".phase11-chat-companion-memory-ledger-execution" in css_text
    assert ".phase11-chat-companion-memory-ledger-read-model" in css_text
    assert ".phase11-chat-companion-memory-context-readiness" in css_text
    assert ".phase11-chat-approved-schedule-adapter-export" in css_text
    assert ".phase11-chat-schedule-ui-controls" in css_text
    assert ".phase11-schedule-ui-actions" in css_text
    assert ".phase11-schedule-ui-readback" in css_text
    assert ".phase11-chat-authority-tier-controls" in css_text
    assert ".phase11-chat-authority-lanes" in css_text
    assert "#chat-message-input" in css_text


def test_js_chat_loader_present(js_text) -> None:
    assert "function _initPhase11ChatPanel" in js_text
    assert "async function loadPhase11ChatPanel" in js_text
    assert "function renderPhase11ChatPanel" in js_text
    assert "chatLoaded" in js_text
    assert "chat_workspaces_foundation" in js_text
    assert "get_phase11_chat_workspaces_foundation" in js_text
    assert "_phase11ChatProductShellDesk" in js_text
    assert "_stageChatAttachments" in js_text
    assert "_selectChatThread" in js_text
    assert "_showChatCreatePanel" in js_text
    assert "_createChatThreadFromUi" in js_text
    assert "_createChatFolderFromUi" in js_text
    assert "create_chat_thread" in js_text
    assert "create_chat_folder" in js_text
    assert "rename_chat_folder" in js_text
    assert "delete_chat_folder" in js_text
    assert "move_chat_thread" in js_text
    assert "delete_chat_thread" in js_text
    assert "resetThread: true" in js_text
    assert "_selectChatFolder" in js_text
    assert "chat-folder-dropdown-menu" in js_text
    assert "phase11-chat-manage-menu" in js_text
    assert "Default folder stays available" in js_text
    assert "Gated actions stay in Approvals" not in js_text
    assert "_chatIsProductVisibleThread" in js_text
    assert "return 'Sync'" in js_text
    assert "Live heartbeat" not in js_text
    assert "Start heartbeat" not in js_text
    assert "Needs live heartbeat" not in js_text
    assert "Use Start Runtime only" not in js_text
    assert "_selectedChatWorkspaceId" in js_text
    assert "_selectedChatFolderId" in js_text
    assert "chat_workspace_proposal_writer" in js_text
    assert "chat_workspace_proposal_consumption_executor" in js_text
    assert "chat_workspace_target_state_executor" in js_text
    assert "chat_route_state_and_message_drafts" in js_text
    assert "chat_runtime_board_handoff_proposal" in js_text
    assert "chat_schedule_proposal_packet" in js_text
    assert "chat_schedule_proposal_consumption_executor" in js_text
    assert "chat_approved_schedule_intent_writer" in js_text
    assert "chat_schedule_intent_activation_readiness" in js_text
    assert "chat_approved_schedule_activation_executor" in js_text
    assert "chat_schedule_adapter_export_readiness" in js_text
    assert "chat_approved_schedule_adapter_export_packet_writer" in js_text
    assert "chat_schedule_ui_action_controls_and_readback" in js_text
    assert "chat_authority_tier_controls" in js_text
    assert "function _phase11ChatWorkspaceFoundation" in js_text
    assert "function _phase11ChatAuthorityTierControls" in js_text
    assert "function _phase11AuthorityOpenLane" in js_text
    assert "function _phase11ChatWorkspaceProposalWriter" in js_text
    assert "function _phase11ChatWorkspaceProposalConsumption" in js_text
    assert "function _phase11ChatWorkspaceTargetState" in js_text
    assert "function _phase11ChatRouteStateAndMessageDrafts" in js_text
    assert "function _phase11ChatRuntimeBoardHandoffProposal" in js_text
    assert "function _phase11ChatScheduleProposalPacket" in js_text
    assert "function _phase11ChatScheduleProposalConsumption" in js_text
    assert "function _phase11ChatApprovedScheduleIntentWriter" in js_text
    assert "function _phase11ChatScheduleIntentActivationReadiness" in js_text
    assert "function _phase11ChatApprovedScheduleActivationExecutor" in js_text
    assert "function _phase11ChatApprovedScheduleAdapterExportPacketWriter" in js_text
    assert "function _phase11ChatScheduleUiActionControlsAndReadback" in js_text
    assert "async function _phase11ScheduleRunAction" in js_text
    assert "if (id === 'chat')" in js_text and "loadPhase11ChatPanel()" in js_text
    assert "_initPhase11ChatPanel()" in js_text


def test_js_renders_key_readiness_and_denial_terms(js_text) -> None:
    assert "Slash Command Preview" in js_text
    assert "Proposal Card Preview" in js_text
    assert "Affected files/systems" in js_text
    assert "Dry-run target" in js_text
    assert "Handback buttons" in js_text
    assert "Approval Handoff Preflight" in js_text
    assert "Live Routing Gate" in js_text
    assert "Safety Policy" in js_text
    assert "All capabilities policy-aware" in js_text
    assert "Authority absent fails closed" in js_text
    assert "Closeout Evidence" in js_text
    assert "Post-Closeout Future Work" in js_text
    assert "Approval Queue Handoff Contract" in js_text
    assert "Queue Handoff Blockers" in js_text
    assert "Conversation Persistence Contract" in js_text
    assert "Conversation Approval Packet Preview" in js_text
    assert "Conversation Persistence Blockers" in js_text
    assert "Approval Queue Write Proof" in js_text
    assert "Live Provider Approval Preview" in js_text
    assert "Request Digest" in js_text
    assert "get_phase11_chat_live_provider_execution_approval_preview" in js_text
    assert "Runtime Dispatch Readiness" in js_text
    assert "Studio Chat Workspaces" in js_text
    assert "Projects And Threads" in js_text
    assert "Workspace Proposal Writer" in js_text
    assert "request_phase11_chat_workspace_proposal" in js_text
    assert "Workspace Proposal Consumption" in js_text
    assert "execute_phase11_chat_workspace_proposal_consumption" in js_text
    assert "Workspace Target State" in js_text
    assert "execute_phase11_chat_workspace_target_state" in js_text
    assert "Route State And Drafts" in js_text
    assert "save_phase11_chat_route_state" in js_text
    assert "save_phase11_chat_message_draft" in js_text
    assert "Runtime Board Handoff Proposal" in js_text
    assert "get_phase11_chat_runtime_board_handoff_proposal" in js_text
    assert "request_phase11_chat_runtime_board_handoff_proposal" in js_text
    assert "Handoff digest" in js_text
    assert "Schedule Proposal Packet" in js_text
    assert "get_phase11_chat_schedule_proposal_packet" in js_text
    assert "request_phase11_chat_schedule_proposal_packet" in js_text
    assert "Schedule Proposal Consumption" in js_text
    assert "execute_phase11_chat_schedule_proposal_consumption" in js_text
    assert "Staged proposal write allowed" in js_text
    assert "Approved Schedule Intent Writer" in js_text
    assert "execute_phase11_chat_approved_schedule_intent_writer" in js_text
    assert "Staged path or schedule id required" in js_text
    assert "Operator write statement required" in js_text
    assert "Schedule Activation Readiness" in js_text
    assert "get_phase11_chat_schedule_intent_activation_readiness" in js_text
    assert "request_phase11_chat_schedule_intent_activation" in js_text
    assert "Activation digest required" in js_text
    assert "Approved Schedule Activation Executor" in js_text
    assert "execute_phase11_chat_approved_schedule_activation" in js_text
    assert "Operator activation statement required" in js_text
    assert "Schedule enable via executor" in js_text
    assert "Schedule Adapter Export Readiness" in js_text
    assert "get_phase11_chat_schedule_adapter_export_readiness" in js_text
    assert "request_phase11_chat_schedule_adapter_export" in js_text
    assert "Export digest required" in js_text
    assert "Local export packet write now" in js_text
    assert "Approved Schedule Adapter Export Packet Writer" in js_text
    assert "execute_phase11_chat_approved_schedule_adapter_export_packet_writer" in js_text
    assert "Operator export write statement required" in js_text
    assert "Local export packet write via writer" in js_text
    assert "Schedule Manual Test Controls" in js_text
    assert "Preview Proposal" in js_text
    assert "Queue Proposal" in js_text
    assert "Consume Proposal" in js_text
    assert "Write Intent" in js_text
    assert "Preview Activation" in js_text
    assert "Queue Activation" in js_text
    assert "Preview Export" in js_text
    assert "Queue Export" in js_text
    assert "Write Export Packet" in js_text
    assert "phase11-schedule-ui-readback-json" in js_text
    assert "get_phase11_chat_schedule_ui_action_controls_and_readback" in js_text
    assert "Schedule digest" in js_text
    assert "Schedule intent written" in js_text
    assert "Schedule index regenerated" in js_text
    assert "External scheduler changed" in js_text
    assert "Authority Tier Controls" in js_text
    assert "get_phase11_chat_authority_tier_controls" in js_text
    assert "data-phase11-authority-target" in js_text
    assert "Open Lane" in js_text
    assert "Message intent state" in js_text
    assert "Proposal digest" in js_text
    assert "Chat thread created" in js_text
    assert "Discord API called" in js_text
    assert "Agent Bus task written" in js_text
    assert "Runtime board written" in js_text
    assert "Schedule mutated" in js_text
    assert "Provider call performed" in js_text
    assert "Future dispatch packet" in js_text
    assert "get_phase11_chat_runtime_dispatch_readiness" in js_text
    assert "Approval Consumption Readiness" in js_text
    assert "get_phase11_chat_approval_consumption_readiness" in js_text
    assert "Post-Closeout Plan" in js_text
    assert "Next Product Pass" in js_text
    assert "Denied By This Surface" in js_text
    assert "Credential values visible" in js_text
    assert "Approval queue write denied" in js_text
    assert "Blocked by closeout design" in js_text
    assert "readonly_slash_command_responses" in js_text
    assert "function _phase11ChatReadonlySlashCommandResponses" in js_text
    assert "Read-Only Slash Responses" in js_text
    assert "Response Cards Ready" in js_text
    assert "Embedded Action Buttons" in js_text
    assert "function _phase11ChatSlashActionButtons" in js_text
    assert "data-phase11-slash-action-message" in js_text
    assert "Run read-only preview" in js_text
    assert "Command Surface Explainer" in js_text
    assert "Terminal CLI" in js_text
    assert "operator-facing command surface, not a Studio Chat provider bypass" in js_text
    assert "CHAT_SLASH_COMMAND_CATALOG" in js_text
    assert "function _renderChatSlashCommandMenu" in js_text
    assert "function _applyChatSlashCommandSuggestion" in js_text
    assert "data-chat-slash-command-message" in js_text
    assert "ArrowDown" in js_text
    assert "Auto-fill read-only preview" in js_text
    assert "Command Execution" in js_text
    assert "Agent Bus Task Write" in js_text
    assert "Companion Roster Preview" in js_text
    assert "get_phase11_companion_roster_ui_preview" in js_text
    assert "phase11-chat-companion-roster" in js_text
    assert "Companion Memory Approval Preview" in js_text
    assert "get_phase11_companion_memory_approval_preview" in js_text
    assert "phase11-chat-companion-memory-approval" in js_text
    assert "Companion Memory Approved Execution Proof" in js_text
    assert "execute_phase11_companion_memory_approved_execution_proof" in js_text
    assert "phase11-chat-companion-memory-execution" in js_text
    assert "Companion Memory Readback Search Preview" in js_text
    assert "get_phase11_companion_memory_readback_search_preview" in js_text
    assert "phase11-chat-companion-memory-readback" in js_text
    assert "Companion Memory Ledger-Write Approval Preview" in js_text
    assert "get_phase11_companion_memory_ledger_write_approval_preview" in js_text
    assert "phase11-chat-companion-memory-ledger-write" in js_text
    assert "Companion Memory Approved Ledger-Write Execution Proof" in js_text
    assert "execute_phase11_companion_memory_approved_ledger_write_execution_proof" in js_text
    assert "phase11-chat-companion-memory-ledger-execution" in js_text
    assert "Companion Memory Ledger Read Model Preview" in js_text
    assert "get_phase11_companion_memory_ledger_read_model_preview" in js_text
    assert "phase11-chat-companion-memory-ledger-read-model" in js_text
    assert "Companion Memory Context Readiness Preview" in js_text
    assert "get_phase11_companion_memory_context_readiness_preview" in js_text
    assert "phase11-chat-companion-memory-context-readiness" in js_text


def test_js_p11_proposal_preview_does_not_expose_queue_write_action(js_text) -> None:
    assert "Approval Queue Write Proof" in js_text
    assert "Queue Action" not in js_text
    assert "chat-queue-write-button" not in js_text
    assert "request_phase11_chat_approval_queue_write" not in js_text


def test_project_create_proposal_preview_is_no_write_boundary(api) -> None:
    response = api.get_phase11_chat_panel_contract(
        "Create a new project for broker analytics",
        "project-create",
    )
    data = response["data"]
    proposal = data["proposal_card"]
    write_proof = data["approval_queue_write_execution_proof"]

    assert proposal["visible"] is True
    assert proposal["preview_only"] is True
    assert proposal["approval_request_created"] is False
    assert proposal["writes_queued"] is False
    assert proposal["dry_run_preview"]["writes_queued"] is False
    assert proposal["dry_run_preview"]["target_file_written"] is False
    assert write_proof["summary"]["approval_request_created"] is False
    assert write_proof["queue_write"]["queue_writer_called"] is False
    assert write_proof["target_write_proof"]["target_file_written"] is False


def test_api_returns_chat_approval_handoff_queue_contract(api) -> None:
    response = api.get_phase11_chat_approval_handoff_queue_contract("Create a new project")

    assert response["ok"] is True
    assert response["surface"] == "phase11_chat_approval_handoff_queue_contract"
    assert response["data"]["summary"]["queue_write_allowed_now"] is False
    assert response["data"]["handoff_queue_preview"]["queue_writer_called"] is False
    assert response["data"]["final_closeout_evidence"]["approval_handoff_queue_contract_closed"] is True


def test_api_returns_phase11_post_closeout_planning(api) -> None:
    response = api.get_phase11_post_closeout_planning()

    assert response["ok"] is True
    assert response["surface"] == "phase11_post_closeout_planning"
    assert response["data"]["summary"]["remaining_pass_count"] >= 1
    assert response["data"]["summary"]["writes_allowed_now"] is False
    assert response["data"]["next_pass"]["pass_id"] == "operator-action-required-no-autonomous-phase11-pass"


def test_api_returns_phase11_chat_conversation_persistence_contract(api, tmp_path) -> None:
    response = api.get_phase11_chat_conversation_persistence_contract("Save this conversation preview")

    assert response["ok"] is True
    assert response["surface"] == "phase11_chat_conversation_persistence_contract"
    assert response["data"]["summary"]["conversation_write_allowed_now"] is False
    assert response["data"]["conversation_descriptor"]["target_path_preview"].startswith("07_LOGS/Conversations/")
    assert response["data"]["conversation_log_preview"]["target_file_written"] is False
    assert response["data"]["future_approval_packet_preview"]["approval_request_created"] is False


def test_api_returns_phase11_chat_approval_queue_write_proof(api) -> None:
    response = api.get_phase11_chat_approval_queue_write_execution_proof(
        "Create a new project from chat",
        "project-create",
    )

    assert response["ok"] is True
    assert response["surface"] == "phase11_chat_approval_queue_write_execution_proof"
    assert response["data"]["summary"]["queue_write_preview_ready"] is True
    assert response["data"]["summary"]["approval_request_created"] is False
    assert response["data"]["digest_proof"]["action_digest"]
    assert response["data"]["target_write_proof"]["target_file_written"] is False


def test_api_returns_phase11_chat_live_provider_execution_approval_preview(api) -> None:
    response = api.get_phase11_chat_live_provider_execution_approval_preview(
        "Use a model to summarize Studio status",
        "model-chat",
    )

    assert response["ok"] is True
    assert response["surface"] == "phase11_chat_live_provider_execution_approval_preview"
    assert response["data"]["summary"]["approval_preview_ready"] is True
    assert response["data"]["future_approval_packet_preview"]["approval_request_created"] is False
    assert response["data"]["future_provider_execution_preview"]["provider_call_performed"] is False
    assert response["data"]["conversation_audit_preflight"]["conversation_audit_write_allowed_now"] is False


def test_api_returns_phase11_chat_runtime_dispatch_readiness(api) -> None:
    response = api.get_phase11_chat_runtime_dispatch_readiness(
        "Ask Codex to inspect the runtime queue",
        "runtime-task",
        "Codex",
        "repo.inspect",
    )

    assert response["ok"] is True
    assert response["surface"] == "phase11_chat_runtime_dispatch_readiness_contract"
    assert response["data"]["summary"]["dispatch_preview_ready"] is True
    assert response["data"]["future_dispatch_packet_preview"]["agent_bus_task_created"] is False
    assert response["data"]["future_dispatch_packet_preview"]["workflow_dispatch_called"] is False


def test_api_returns_phase11_chat_authority_tier_controls(api) -> None:
    response = api.get_phase11_chat_authority_tier_controls(
        "use openai, discord, hermes, and openclaw",
        "runtime-task",
    )

    assert response["ok"] is True
    assert response["surface"] == "phase11_chat_authority_tier_controls"
    assert response["data"]["summary"]["lane_count"] == 6
    assert response["data"]["authority"]["provider_calls_allowed"] is False
    assert response["data"]["authority"]["discord_api_calls_allowed"] is False
    assert response["data"]["authority"]["agent_bus_task_write_allowed"] is False


def test_api_returns_phase11_chat_approval_consumption_readiness(api) -> None:
    response = api.get_phase11_chat_approval_consumption_readiness()

    assert response["ok"] is True
    assert response["surface"] == "phase11_chat_approval_consumption_readiness_contract"
    assert response["data"]["surface"] == "phase11_chat_approval_consumption_readiness_contract"
    assert response["data"]["summary"]["approval_artifact_known"] is False
    assert "no_chat_originated_approval_artifacts_found" in response["data"]["blocked_reasons"]
