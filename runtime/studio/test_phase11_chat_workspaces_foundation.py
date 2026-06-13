"""Tests for the native Studio Chat workspace/thread foundation."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.studio.phase11_chat_workspaces_foundation import build_phase11_chat_workspaces_foundation


def _write_caps(root: Path, runtime_name: str, bus_name: str, handles: list[str]) -> None:
    path = root / "runtime" / runtime_name / "capabilities.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    handle_lines = []
    for task_type in handles:
        handle_lines.extend(
            [
                f"  - task_type: {task_type}",
                "    priority: primary",
                f"    notes: {bus_name} test capability.",
            ]
        )
    path.write_text(
        "\n".join(
            [
                f"bus_name: {bus_name}",
                "heartbeat_stale_seconds: 900",
                "max_concurrent_tasks: 1",
                "priority_ceiling: normal",
                "handles:",
                *handle_lines,
            ]
        ),
        encoding="utf-8",
    )


def _seed_discord_binding(root: Path) -> None:
    (root / ".gitignore").write_text(".chaseos/\n", encoding="utf-8")
    channels = [
        "control_plane_routing",
        "approvals",
        "audit_writeback",
        "runtime_chat_openclaw",
        "alerts_openclaw",
        "debug_openclaw",
        "docs_archive",
        "runtime_chat_hermes",
        "alerts_hermes",
        "debug_hermes",
    ]
    channel_yaml = []
    for index, channel in enumerate(channels, start=1):
        channel_yaml.extend(
            [
                f"  {channel}:",
                f"    id: fake-channel-{index}",
                f"    name: {channel}",
                "    channel_class: runtime_control",
                "    bound: true",
                "    execution_authority: none",
                "    interactive_mode: true",
                "    posting_eligible_runtimes:",
                "      - OpenClaw",
                "      - Hermes",
                "      - Codex",
            ]
        )
    path = root / ".chaseos" / "discord_instance_bindings.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "server:",
                "  id: fake-server-id",
                "  name: Test Server",
                "operator:",
                "  user_id: fake-operator-id",
                "  display_name: Operator",
                "  approval_authority: true",
                "runtimes:",
                "  openclaw:",
                "    bot_user_id: fake-openclaw-bot",
                "    application_id: fake-openclaw-app",
                "    public_key: fake-openclaw-public-key",
                "    execution_lane_status: live",
                "    execution_eligible: true",
                "    approval_authority: false",
                "    allowed_adapters:",
                "      - agent_bus",
                "  hermes:",
                "    bot_user_id: fake-hermes-bot",
                "    application_id: fake-hermes-app",
                "    public_key: fake-hermes-public-key",
                "    execution_lane_status: live",
                "    execution_eligible: true",
                "    approval_authority: false",
                "    allowed_adapters:",
                "      - agent_bus",
                "primary_channels:",
                *channel_yaml,
                "default_unmapped_policy: deny",
            ]
        ),
        encoding="utf-8",
    )


def _seed_runtime_context(root: Path) -> None:
    _write_caps(root, "openclaw", "OpenClaw", ["runtime.handoff", "workflow.dispatch", "code.patch"])
    _write_caps(root, "hermes", "Hermes", ["runtime.handoff", "repo.inspect", "operator.brief"])
    _write_caps(root, "codex", "Codex", ["repo.inspect", "code.patch", "test.run", "code.review"])
    _seed_discord_binding(root)


def test_foundation_renders_native_workspace_thread_model_without_writes(tmp_path: Path) -> None:
    _seed_runtime_context(tmp_path)

    payload = build_phase11_chat_workspaces_foundation(tmp_path, message="Open an OpenClaw thread")

    assert payload["ok"] is True
    assert payload["read_only"] is True
    assert payload["summary"]["native_chat_project_model_ready"] is True
    assert payload["summary"]["workspace_count"] >= 4
    assert payload["summary"]["folder_count"] >= 8
    assert payload["summary"]["tab_count"] >= 12
    assert payload["summary"]["thread_count"] >= 6
    assert payload["authority"]["chat_thread_create_allowed"] is False
    assert payload["authority"]["chat_message_send_allowed"] is False
    assert payload["authority"]["agent_bus_task_write_allowed"] is False
    assert payload["authority"]["runtime_board_write_allowed"] is False
    assert payload["authority"]["schedule_mutation_allowed"] is False
    assert payload["authority"]["provider_calls_allowed"] is False
    assert payload["readiness"]["studio_runtime_chat_workspaces_foundation_ready"] is True
    assert payload["readiness"]["native_thread_creation_blocked"] is True
    assert payload["readiness"]["agent_bus_task_write_blocked"] is True
    assert payload["readiness"]["schedule_mutation_blocked"] is True
    assert "chat_thread_create" in payload["denied_by_this_surface"]
    assert "runtime_board_write" in payload["denied_by_this_surface"]


def test_foundation_redacts_discord_binding_values(tmp_path: Path) -> None:
    _seed_runtime_context(tmp_path)

    payload = build_phase11_chat_workspaces_foundation(tmp_path)
    discord = payload["transport_bridge"]["discord"]
    serialized = json.dumps(payload)

    assert discord["status"] == "valid"
    assert discord["ids_visible"] is False
    assert discord["secret_values_visible"] is False
    assert discord["discord_api_calls_performed"] is False
    assert discord["thread_creation_performed"] is False
    assert "runtime_chat_openclaw" in discord["bound_channel_names"]
    assert "runtime_chat_hermes" in discord["bound_channel_names"]
    assert "fake-server-id" not in serialized
    assert "fake-operator-id" not in serialized
    assert "fake-channel-1" not in serialized


def test_workspace_threads_cover_hermes_openclaw_codex_and_future_actions(tmp_path: Path) -> None:
    _seed_runtime_context(tmp_path)

    payload = build_phase11_chat_workspaces_foundation(tmp_path)
    runtime_ids = {runtime["runtime_id"] for runtime in payload["runtime_lanes"]}
    thread_runtime_ids = {thread["runtime_id"] for thread in payload["threads"] if thread["runtime_id"]}
    action_ids = {action["action_id"] for action in payload["proposal_actions"]}

    assert {"OpenClaw", "Hermes", "Codex"}.issubset(runtime_ids)
    assert {"OpenClaw", "Hermes", "Codex"}.issubset(thread_runtime_ids)
    assert "create_runtime_thread" in action_ids
    assert "send_to_runtime_board" in action_ids
    assert "manage_cron_tasks" in action_ids
    assert "chat_driven_runtime_setup" in action_ids
    assert all(action["writes_allowed_now"] is False for action in payload["proposal_actions"])
    assert all(
        thread["actions_allowed_now"]["agent_bus_task_write"] is False
        and thread["actions_allowed_now"]["runtime_board_write"] is False
        and thread["actions_allowed_now"]["schedule_mutation"] is False
        for thread in payload["threads"]
    )
    assert all(workspace["chat_thread_create_allowed_now"] is False for workspace in payload["workspaces"])


def test_foundation_includes_local_saved_folders_and_threads(tmp_path: Path) -> None:
    from runtime.studio.phase11_chat_thread_conversations import (
        create_chat_folder,
        create_chat_thread_conversation,
    )

    _seed_runtime_context(tmp_path)
    folder = create_chat_folder(tmp_path, workspace_id="runtime-ops", label="Client Alpha")["folder"]
    conversation = create_chat_thread_conversation(
        tmp_path,
        title="Client Alpha runtime chat",
        workspace_id="runtime-ops",
        folder_id=folder["folder_id"],
        folder_label=folder["label"],
        runtime_id="hermes",
    )["conversation"]

    payload = build_phase11_chat_workspaces_foundation(tmp_path)
    folders = {(item["workspace_id"], item["folder_id"]): item for item in payload["folders"]}
    threads = {item["thread_id"]: item for item in payload["threads"]}

    assert (folder["workspace_id"], folder["folder_id"]) in folders
    assert conversation["thread_id"] in threads
    assert threads[conversation["thread_id"]]["folder_label"] == "Client Alpha"
    assert threads[conversation["thread_id"]]["runtime_id"] == "Hermes"
    assert threads[conversation["thread_id"]]["conversation_persisted"] is True
