from __future__ import annotations

import json
from pathlib import Path

from runtime.agent_bus.bus import list_tasks
from runtime.studio.agent_bus_client import (
    StudioAgentBusClient,
    derive_portable_vault_paths,
    load_recipient_map,
    resolve_recipient,
)


def test_portable_vault_paths_are_derived_from_selected_vault_not_hardcoded_user() -> None:
    paths = derive_portable_vault_paths(Path("<WINDOWS_USER_HOME_WSL>/<path>"))

    assert paths["wsl_vault_path"] == "<WINDOWS_USER_HOME_WSL>/<path>"
    assert paths["windows_vault_path"] == "C:\\Users\\example\\Documents\\chaseos_obsidian"
    assert "chaseos\\Documents" not in str(paths["windows_vault_path"])


def test_recipient_map_can_be_configured_without_changing_chat_code(tmp_path: Path) -> None:
    config = tmp_path / ".chaseos" / "companion_config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps({"recipient_names": {"claude-code": "ClaudeCode", "custom": "Hermes"}}), encoding="utf-8")

    mapping = load_recipient_map(tmp_path)

    assert mapping["claude-code"] == "ClaudeCode"
    assert resolve_recipient(tmp_path, "custom") == "Hermes"
    assert resolve_recipient(tmp_path, "unknown-runtime") == "Hermes"


def test_status_is_passive_and_does_not_launch_wsl_or_terminals(tmp_path: Path) -> None:
    client = StudioAgentBusClient(tmp_path)

    status = client.runtime_status("hermes")

    assert status["ok"] is True
    assert status["recipient"] == "Hermes"
    assert status["launch_policy"]["passive_status_only"] is True
    assert status["launch_policy"]["starts_wsl"] is False
    assert status["launch_policy"]["spawns_terminal"] is False
    assert status["launch_policy"]["starts_runtime_daemon"] is False
    assert status["launch_policy"]["provider_call_performed"] is False
    assert "python -m runtime.workflows.hermes_watch" in status["startup_guide"]


def test_create_task_routes_studio_chat_through_agent_bus_only(tmp_path: Path) -> None:
    client = StudioAgentBusClient(tmp_path, sender="Codex")

    result = client.create_task(
        runtime_id="hermes",
        request="hello hermes",
        expected_output="chat-response",
        notes="task_type: chat\nsource_surface: studio_chat",
    )

    assert result["created"] is True
    assert result["recipient"] == "Hermes"
    assert result["authority"]["runtime_dispatch_via_agent_bus"] is True
    assert result["authority"]["provider_call_performed"] is False
    assert result["authority"]["starts_wsl"] is False
    assert result["authority"]["spawns_terminal"] is False
    tasks = list_tasks(tmp_path, recipient="Hermes")
    assert any(task["task_id"] == result["task_id"] for task in tasks)
