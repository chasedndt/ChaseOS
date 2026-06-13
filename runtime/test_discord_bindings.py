from __future__ import annotations

import json
from pathlib import Path

from runtime.discord_bindings import build_discord_binding_validation
from runtime.cli import main as cli
from runtime.studio.dashboard import get_dashboard


def _write_valid_binding(root: Path) -> None:
    (root / ".chaseos").mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text(".chaseos/\n", encoding="utf-8")
    (root / "runtime" / "bindings").mkdir(parents=True, exist_ok=True)
    (root / "runtime" / "bindings" / "discord_instance_bindings.example.yaml").write_text(
        "schema_version: '1.0'\ndefault_unmapped_policy: deny\n",
        encoding="utf-8",
    )
    (root / "04_SOPS").mkdir(parents=True, exist_ok=True)
    (root / "04_SOPS" / "Discord-Control-Plane-Setup-SOP.md").write_text(
        "# Discord Control Plane Setup SOP\n",
        encoding="utf-8",
    )
    (root / ".chaseos" / "discord_instance_bindings.yaml").write_text(
        """
schema_version: "1.0"
server:
  id: "111111111111111111"
  name: "Test Server"
operator:
  user_id: "222222222222222222"
  display_name: "Operator"
  approval_authority: true
runtimes:
  openclaw:
    bot_user_id: "333333333333333333"
    application_id: "444444444444444444"
    public_key: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    execution_eligible: true
    allowed_adapters: ["openclaw"]
    approval_authority: false
    execution_lane_status: live
  hermes:
    bot_user_id: "555555555555555555"
    application_id: "666666666666666666"
    public_key: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    execution_eligible: true
    allowed_adapters: ["hermes"]
    approval_authority: false
    execution_lane_status: live
primary_channels:
  control_plane_routing: {id: "777777777777777777", name: "chaseos-ops", channel_class: control-plane-routing, bound: true}
  approvals: {id: "888888888888888888", name: "approvals", channel_class: approvals, bound: true}
  audit_writeback: {id: "999999999999999999", name: "audit-writeback", channel_class: audit-writeback, bound: true}
  runtime_chat_openclaw: {id: "111111111111111112", name: "openclaw-chat", channel_class: runtime-chat, bound: true}
  alerts_openclaw: {id: "111111111111111113", name: "alerts-openclaw", channel_class: alerts, bound: true}
  debug_openclaw: {id: "111111111111111114", name: "debug-openclaw", channel_class: debug, bound: true}
  docs_archive: {id: "111111111111111115", name: "server-notes", channel_class: docs-archive, bound: true}
  runtime_chat_hermes: {id: "111111111111111116", name: "hermes-chat", channel_class: runtime-chat, bound: true}
  alerts_hermes: {id: "111111111111111117", name: "alerts-hermes", channel_class: alerts, bound: true}
  debug_hermes: {id: "111111111111111118", name: "debug-hermes", channel_class: debug, bound: true}
supplemental_channels: {}
default_unmapped_policy: deny
        """.strip()
        + "\n",
        encoding="utf-8",
    )


def test_discord_binding_validation_redacts_ids_and_reports_studio_capabilities(tmp_path: Path) -> None:
    _write_valid_binding(tmp_path)

    payload = build_discord_binding_validation(tmp_path)
    serialized = json.dumps(payload, sort_keys=True)

    assert payload["valid"] is True
    assert payload["ids_visible"] is False
    assert payload["secret_values_visible"] is False
    assert payload["summary"]["active_runtime_ids"] == ["hermes", "openclaw"]
    assert payload["summary"]["bound_channel_count"] == 10
    assert "111111111111111111" not in serialized
    assert "222222222222222222" not in serialized
    capability_ids = {
        item["id"]
        for item in payload["studio_runtime_control_plane"]["capabilities"]
    }
    assert "quick_open_runtime_chat" in capability_ids
    assert "manage_cron_tasks" in capability_ids
    assert "send_to_runtime_board" in capability_ids


def test_discord_binding_validation_blocks_webhook_values_in_binding_file(tmp_path: Path) -> None:
    _write_valid_binding(tmp_path)
    binding = tmp_path / ".chaseos" / "discord_instance_bindings.yaml"
    binding.write_text(
        binding.read_text(encoding="utf-8")
        + "\nwebhook_url: https://discord.com/api/webhooks/123456789012345678/token\n",
        encoding="utf-8",
    )

    payload = build_discord_binding_validation(tmp_path)

    assert payload["valid"] is False
    assert "secret_like_values_in_binding_file" in payload["blockers"]
    assert payload["secret_like_findings"][0]["value_visible"] is False


def test_setup_discord_validate_cli_json(capsys, tmp_path: Path) -> None:
    _write_valid_binding(tmp_path)

    exit_code = cli.main([
        "setup",
        "discord",
        "validate",
        "--vault-root",
        str(tmp_path),
        "--json",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    result = payload["result"]
    assert payload["action"] == "setup.discord.validate"
    assert result["surface"] == "chaseos_discord_binding_validation"
    assert result["valid"] is True
    assert result["ids_visible"] is False


def test_studio_dashboard_surfaces_discord_control_plane_panel(tmp_path: Path) -> None:
    _write_valid_binding(tmp_path)

    dashboard = get_dashboard(tmp_path, probe_child_apps=False)
    panel = dashboard["discord_control_plane_panel"]

    assert panel["surface"] == "studio_discord_control_plane_panel"
    assert panel["valid"] is True
    assert panel["authority"]["ids_visible"] is False
