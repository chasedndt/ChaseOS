"""CLI-level tests for canonical runtime.cli.main agent-bus ingress-aware task creation."""

from __future__ import annotations

import json
import sys
from pathlib import Path


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402
import runtime.cli.agent_bus_commands as agent_bus_cli  # noqa: E402


def test_agent_bus_ingress_discord_parser_accepts_coordination_surface(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_translate(vault_root, **kwargs):
        captured["vault_root"] = vault_root
        captured.update(kwargs)
        return {"translated": True, "created": True, "task_id": "task-ops"}

    monkeypatch.setattr(agent_bus_cli, "agent_bus_translate_discord_control_plane_request", fake_translate)

    exit_code = cli.main(
        [
            "agent-bus",
            "ingress",
            "discord",
            "--recipient",
            "OpenClaw",
            "--request",
            "Coordinate review execution",
            "--expected-output",
            "Structured review result",
            "--source-channel-id",
            "1493226873080119397",
            "--source-thread-id",
            "1496197360382906398",
            "--origin-message-id",
            "1497000000000000001",
            "--coordination-sensitive",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    assert exit_code == 0
    assert captured["recipient"] == "OpenClaw"
    assert captured["coordination_sensitive"] is True
    assert captured["source_channel_id"] == "1493226873080119397"


def test_agent_bus_task_create_parser_accepts_ingress_metadata(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_task(vault_root, **kwargs):
        captured["vault_root"] = vault_root
        captured.update(kwargs)
        return {"created": True, "task_id": "task-xyz", "run_id": "run-xyz"}

    monkeypatch.setattr(agent_bus_cli, "agent_bus_create_task", fake_create_task)

    exit_code = cli.main(
        [
            "agent-bus",
            "task",
            "create",
            "--sender",
            "Hermes",
            "--recipient",
            "OpenClaw",
            "--request",
            "Do the work",
            "--expected-output",
            "Return result",
            "--source-platform",
            "discord",
            "--source-channel-id",
            "1493226848409358426",
            "--source-thread-id",
            "1496197360382906398",
            "--source-channel-class",
            "runtime-chat",
            "--conversation-key",
            "discord:1493226848409358426:1496197360382906398",
            "--origin-message-id",
            "1497000000000000001",
            "--work-fingerprint",
            "discord-shared-work-001",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    assert exit_code == 0
    assert captured["ingress_context"]["source_thread_id"] == "1496197360382906398"
    assert captured["work_fingerprint"] == "discord-shared-work-001"


def test_agent_bus_task_create_forwards_ingress_metadata(monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}

    def fake_create_task(vault_root, **kwargs):
        captured["vault_root"] = vault_root
        captured.update(kwargs)
        return {"created": True, "task_id": "task-xyz", "run_id": "run-xyz"}

    monkeypatch.setattr(agent_bus_cli, "agent_bus_create_task", fake_create_task)

    exit_code = cli.main(
        [
            "agent-bus",
            "task",
            "create",
            "--sender",
            "Hermes",
            "--recipient",
            "OpenClaw",
            "--request",
            "Do the work",
            "--expected-output",
            "Return result",
            "--source-platform",
            "discord",
            "--source-channel-id",
            "1493226848409358426",
            "--source-thread-id",
            "1496197360382906398",
            "--source-channel-class",
            "runtime-chat",
            "--conversation-key",
            "discord:1493226848409358426:1496197360382906398",
            "--origin-message-id",
            "1497000000000000001",
            "--work-fingerprint",
            "discord-shared-work-001",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "agent-bus.task.create"
    assert payload["result"]["task_id"] == "task-xyz"
    assert captured["ingress_context"] == {
        "source_platform": "discord",
        "source_channel_id": "1493226848409358426",
        "source_thread_id": "1496197360382906398",
        "source_channel_class": "runtime-chat",
        "conversation_key": "discord:1493226848409358426:1496197360382906398",
        "origin_message_id": "1497000000000000001",
    }
    assert captured["work_fingerprint"] == "discord-shared-work-001"


def test_agent_bus_task_list_accepts_runtime_generic_filters_and_limit(monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}

    def fake_list_tasks(vault_root, **kwargs):
        captured["vault_root"] = vault_root
        captured.update(kwargs)
        return [
            {
                "task_id": "task-generic-1",
                "status": "open",
                "sender": "Operator",
                "recipient": "Codex",
                "owner": "NewRuntime",
                "request": "first",
                "expected_output": "result",
                "updated_at": "2026-04-29T00:00:00Z",
            },
            {
                "task_id": "task-generic-2",
                "status": "open",
                "sender": "Operator",
                "recipient": "Codex",
                "owner": "NewRuntime",
                "request": "second",
                "expected_output": "result",
                "updated_at": "2026-04-29T00:01:00Z",
            },
        ]

    monkeypatch.setattr(agent_bus_cli, "agent_bus_list_tasks", fake_list_tasks)

    exit_code = cli.main(
        [
            "agent-bus",
            "task",
            "list",
            "--recipient",
            "Codex",
            "--owner",
            "NewRuntime",
            "--status",
            "open",
            "--limit",
            "1",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert captured["recipient"] == "Codex"
    assert captured["owner"] == "NewRuntime"
    assert captured["status"] == "open"
    assert payload["ok"] is True
    assert payload["action"] == "agent-bus.task.list"
    assert payload["result"]["count"] == 1
    assert payload["result"]["matched_count"] == 2
    assert [task["task_id"] for task in payload["result"]["tasks"]] == ["task-generic-1"]


def test_agent_bus_heartbeat_forwards_instance_scope(monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}

    def fake_upsert_heartbeat(vault_root, **kwargs):
        captured["vault_root"] = vault_root
        captured.update(kwargs)
        return {
            "runtime": kwargs["runtime"],
            "heartbeat_scope": kwargs["heartbeat_scope"],
            "runtime_instance_id": kwargs["runtime_instance_id"],
        }

    monkeypatch.setattr(agent_bus_cli, "agent_bus_upsert_heartbeat", fake_upsert_heartbeat)

    exit_code = cli.main(
        [
            "agent-bus",
            "heartbeat",
            "--runtime",
            "Hermes",
            "--status",
            "busy",
            "--health",
            "ok",
            "--current-task-id",
            "task-123",
            "--summary",
            "discord lane active",
            "--runtime-instance-id",
            "discord-thread-1496197360382906398",
            "--heartbeat-scope",
            "instance",
            "--control-surface",
            "discord",
            "--control-surface-key",
            "discord:1493226848409358426:1496197360382906398",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "agent-bus.heartbeat"
    assert payload["result"]["heartbeat_scope"] == "instance"
    assert payload["result"]["runtime_instance_id"] == "discord-thread-1496197360382906398"
    assert captured["runtime_instance_id"] == "discord-thread-1496197360382906398"
    assert captured["heartbeat_scope"] == "instance"
    assert captured["control_surface"] == "discord"
    assert captured["control_surface_key"] == "discord:1493226848409358426:1496197360382906398"


def test_agent_bus_watch_forwards_instance_scope(monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}

    def fake_watch_once(vault_root, **kwargs):
        captured["vault_root"] = vault_root
        captured.update(kwargs)
        return {"runtime": kwargs["runtime"], "open_task_count": 0, "claimed_task_count": 0, "expired_count": 0}

    monkeypatch.setattr(agent_bus_cli, "agent_bus_watch_once", fake_watch_once)

    exit_code = cli.main(
        [
            "agent-bus",
            "watch",
            "--runtime",
            "Hermes",
            "--once",
            "--runtime-instance-id",
            "discord-thread-1496197360382906398",
            "--control-surface",
            "discord",
            "--control-surface-key",
            "discord:1493226848409358426:1496197360382906398",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "agent-bus.watch"
    assert captured["runtime_instance_id"] == "discord-thread-1496197360382906398"
    assert captured["control_surface"] == "discord"
    assert captured["control_surface_key"] == "discord:1493226848409358426:1496197360382906398"



def test_agent_bus_watch_interval_forwards_instance_scope(monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(agent_bus_cli, "check_runtime_operation", lambda *args, **kwargs: (True, "allowed"))

    def fake_run_watch_loop(vault_root, **kwargs):
        captured["vault_root"] = vault_root
        captured.update(kwargs)
        raise KeyboardInterrupt

    monkeypatch.setattr(agent_bus_cli, "agent_bus_run_watch_loop", fake_run_watch_loop)

    exit_code = cli.main(
        [
            "agent-bus",
            "watch",
            "--runtime",
            "Hermes",
            "--interval",
            "30",
            "--claim-next",
            "--runtime-instance-id",
            "discord-thread-1496197360382906398",
            "--control-surface",
            "discord",
            "--control-surface-key",
            "discord:1493226848409358426:1496197360382906398",
            "--vault-root",
            str(_VAULT_ROOT),
        ]
    )

    assert exit_code == 0
    assert captured["runtime"] == "Hermes"
    assert captured["interval_seconds"] == 30
    assert captured["claim_next"] is True
    assert captured["runtime_instance_id"] == "discord-thread-1496197360382906398"
    assert captured["control_surface"] == "discord"
    assert captured["control_surface_key"] == "discord:1493226848409358426:1496197360382906398"



def test_agent_bus_task_list_unknown_runtime_returns_json_error(monkeypatch, capsys) -> None:
    def fake_list_tasks(*args, **kwargs):
        raise ValueError("Unknown runtime identity: 'NotARealRuntime'. Known: ['Codex', 'Hermes', 'OpenClaw']")

    monkeypatch.setattr(agent_bus_cli, "agent_bus_list_tasks", fake_list_tasks)

    exit_code = cli.main(
        [
            "agent-bus",
            "task",
            "list",
            "--recipient",
            "NotARealRuntime",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "agent-bus.task.list"
    assert "Unknown runtime identity" in payload["result"]["reason"]


def test_agent_bus_heartbeats_unknown_runtime_returns_json_error(monkeypatch, capsys) -> None:
    def fake_list_heartbeats(*args, **kwargs):
        raise ValueError("Unknown runtime identity: 'NotARealRuntime'. Known: ['Codex', 'Hermes', 'OpenClaw']")

    monkeypatch.setattr(agent_bus_cli, "agent_bus_list_heartbeats", fake_list_heartbeats)

    exit_code = cli.main(
        [
            "agent-bus",
            "heartbeats",
            "--runtime",
            "NotARealRuntime",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "agent-bus.heartbeats"
    assert "Unknown runtime identity" in payload["result"]["reason"]


def test_agent_bus_task_cleanup_unknown_filter_runtime_returns_json_error(monkeypatch, capsys) -> None:
    def fake_cleanup_tasks(*args, **kwargs):
        raise ValueError("Unknown runtime identity: 'NotARealRuntime'. Known: ['Codex', 'Hermes', 'OpenClaw']")

    monkeypatch.setattr(agent_bus_cli, "agent_bus_cleanup_tasks", fake_cleanup_tasks)

    exit_code = cli.main(
        [
            "agent-bus",
            "task",
            "cleanup",
            "--runtime",
            "Hermes",
            "--sender",
            "NotARealRuntime",
            "--status",
            "open",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "agent-bus.task.cleanup"
    assert "Unknown runtime identity" in payload["result"]["reason"]


def test_agent_bus_heartbeat_unknown_runtime_bus_error_returns_json_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(agent_bus_cli, "check_runtime_operation", lambda *args, **kwargs: (True, "allowed"))

    def fake_upsert(*args, **kwargs):
        raise ValueError("Unknown runtime identity: 'NotARealRuntime'. Known: ['Codex', 'Hermes', 'OpenClaw']")

    monkeypatch.setattr(agent_bus_cli, "agent_bus_upsert_heartbeat", fake_upsert)

    exit_code = cli.main(
        [
            "agent-bus",
            "heartbeat",
            "--runtime",
            "NotARealRuntime",
            "--status",
            "idle",
            "--health",
            "ok",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "agent-bus.heartbeat"
    assert "Unknown runtime identity" in payload["result"]["reason"]


def test_agent_bus_watch_unknown_runtime_bus_error_returns_json_error(monkeypatch, capsys) -> None:
    monkeypatch.setattr(agent_bus_cli, "check_runtime_operation", lambda *args, **kwargs: (True, "allowed"))

    def fake_watch_once(*args, **kwargs):
        raise ValueError("Unknown runtime identity: 'NotARealRuntime'. Known: ['Codex', 'Hermes', 'OpenClaw']")

    monkeypatch.setattr(agent_bus_cli, "agent_bus_watch_once", fake_watch_once)

    exit_code = cli.main(
        [
            "agent-bus",
            "watch",
            "--runtime",
            "NotARealRuntime",
            "--once",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "agent-bus.watch"
    assert "Unknown runtime identity" in payload["result"]["reason"]


def test_agent_bus_heartbeat_accepts_runtime_alias_and_forwards_to_bus(monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}

    def fake_upsert_heartbeat(vault_root, **kwargs):
        captured["vault_root"] = vault_root
        captured.update(kwargs)
        return {"runtime": "Codex", "runtime_instance_id": "Axiom-Codex"}

    gate_calls: list[dict[str, object]] = []

    def fake_check_runtime_operation(*args, **kwargs):
        gate_calls.append(dict(kwargs))
        return True, "allowed"

    monkeypatch.setattr(agent_bus_cli, "check_runtime_operation", fake_check_runtime_operation)
    monkeypatch.setattr(agent_bus_cli, "agent_bus_upsert_heartbeat", fake_upsert_heartbeat)

    exit_code = cli.main(
        [
            "agent-bus",
            "heartbeat",
            "--runtime",
            "Axiom-Codex",
            "--status",
            "idle",
            "--health",
            "ok",
            "--summary",
            "alias parser parity",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "agent-bus.heartbeat"
    assert captured["runtime"] == "Axiom-Codex"
    assert captured["status"] == "idle"
    assert captured["health"] == "ok"
    assert gate_calls[0]["actor_adapter_id"] == "Codex"


def test_agent_bus_alias_policy_resolution_fails_closed_on_capability_error(monkeypatch, capsys) -> None:
    def fake_resolve_runtime_identity(*args, **kwargs):
        raise agent_bus_cli.CapabilityError("alias collision: Axiom-Codex")

    def fail_if_called(*args, **kwargs):  # pragma: no cover - should not be reached
        raise AssertionError("Gate policy check should not run after capability resolution failure")

    monkeypatch.setattr(agent_bus_cli, "resolve_runtime_identity", fake_resolve_runtime_identity)
    monkeypatch.setattr(agent_bus_cli, "check_runtime_operation", fail_if_called)

    exit_code = cli.main(
        [
            "agent-bus",
            "heartbeat",
            "--runtime",
            "Axiom-Codex",
            "--status",
            "idle",
            "--health",
            "ok",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "agent-bus.heartbeat"
    assert payload["result"]["allowed"] is False
    assert payload["result"]["operation"] == "agent_bus.heartbeat"
    assert "Runtime capability resolution failed" in payload["result"]["reason"]
    assert "alias collision" in payload["result"]["reason"]


def test_agent_bus_runtime_actor_commands_accept_aliases_and_forward_to_bus(monkeypatch, capsys) -> None:
    captured: dict[str, dict[str, object]] = {}

    monkeypatch.setattr(agent_bus_cli, "check_runtime_operation", lambda *args, **kwargs: (True, "allowed"))

    def fake_claim(vault_root, **kwargs):
        captured["claim"] = {"vault_root": vault_root, **kwargs}
        return {"claimed": True, "task_id": kwargs["task_id"], "owner": "Codex"}

    def fake_update(vault_root, **kwargs):
        captured["update"] = {"vault_root": vault_root, **kwargs}
        return {"updated": True, "task_id": kwargs["task_id"], "status": kwargs["status"]}

    def fake_cleanup(vault_root, **kwargs):
        captured["cleanup"] = {"vault_root": vault_root, **kwargs}
        return {"ok": True, "matched_count": 0, "selected_count": 0, "updated_count": 0}

    def fake_watch_once(vault_root, **kwargs):
        captured["watch_once"] = {"vault_root": vault_root, **kwargs}
        return {"open_task_count": 0, "claimed_task_count": 0, "expired_count": 0}

    monkeypatch.setattr(agent_bus_cli, "agent_bus_claim_task", fake_claim)
    monkeypatch.setattr(agent_bus_cli, "agent_bus_update_task_status", fake_update)
    monkeypatch.setattr(agent_bus_cli, "agent_bus_cleanup_tasks", fake_cleanup)
    monkeypatch.setattr(agent_bus_cli, "agent_bus_watch_once", fake_watch_once)

    commands = [
        [
            "agent-bus", "task", "claim", "task-alias-claim",
            "--runtime", "Axiom-Codex", "--vault-root", str(_VAULT_ROOT), "--json",
        ],
        [
            "agent-bus", "task", "update", "task-alias-update",
            "--runtime", "Axiom-Codex", "--status", "done", "--message", "done",
            "--vault-root", str(_VAULT_ROOT), "--json",
        ],
        [
            "agent-bus", "task", "cleanup",
            "--runtime", "Axiom-Codex", "--sender", "Axiom-Codex", "--owner", "Axiom-Codex",
            "--status", "open", "--vault-root", str(_VAULT_ROOT), "--json",
        ],
        [
            "agent-bus", "watch",
            "--runtime", "Axiom-Codex", "--once", "--claim-next", "--stale-after-seconds", "120",
            "--vault-root", str(_VAULT_ROOT), "--json",
        ],
    ]

    for argv in commands:
        assert cli.main(argv) == 0

    capsys.readouterr()
    assert captured["claim"]["runtime"] == "Axiom-Codex"
    assert captured["update"]["runtime"] == "Axiom-Codex"
    assert captured["update"]["event_type"] == "completed"
    assert captured["cleanup"]["runtime"] == "Axiom-Codex"
    assert captured["cleanup"]["sender"] == "Axiom-Codex"
    assert captured["cleanup"]["owner"] == "Axiom-Codex"
    assert captured["watch_once"]["runtime"] == "Axiom-Codex"
    assert captured["watch_once"]["claim_next"] is True
    assert captured["watch_once"]["stale_after_seconds"] == 120


def test_agent_bus_task_cleanup_forwards_filters(monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}

    def fake_cleanup_tasks(vault_root, **kwargs):
        captured["vault_root"] = vault_root
        captured.update(kwargs)
        return {"matched_count": 2, "updated_count": 1, "updated_task_ids": ["task-noise-1"]}

    monkeypatch.setattr(agent_bus_cli, "agent_bus_cleanup_tasks", fake_cleanup_tasks)

    exit_code = cli.main(
        [
            "agent-bus",
            "task",
            "cleanup",
            "--runtime",
            "Hermes",
            "--recipient",
            "OpenClaw",
            "--sender",
            "Hermes",
            "--status",
            "open",
            "--request-exact",
            "test",
            "--work-fingerprint",
            "discord:OpenClaw:message-a",
            "--conversation-key",
            "discord:ops:thread-a",
            "--origin-message-id",
            "message-a",
            "--limit",
            "1",
            "--reason",
            "Queue hygiene cleanup",
            "--apply",
            "--vault-root",
            str(_VAULT_ROOT),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "agent-bus.task.cleanup"
    assert captured["runtime"] == "Hermes"
    assert captured["recipient"] == "OpenClaw"
    assert captured["sender"] == "Hermes"
    assert captured["status"] == "open"
    assert captured["request_exact"] == "test"
    assert captured["work_fingerprint"] == "discord:OpenClaw:message-a"
    assert captured["conversation_key"] == "discord:ops:thread-a"
    assert captured["origin_message_id"] == "message-a"
    assert captured["limit"] == 1
    assert captured["apply"] is True
