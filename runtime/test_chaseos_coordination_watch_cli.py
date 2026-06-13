"""Top-level chaseos compatibility shim tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import runtime.cli.main as cli


MODULE_PATH = Path(__file__).resolve().parents[1] / "chaseos.py"
SPEC = importlib.util.spec_from_file_location("chaseos_top", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
chaseos_top = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(chaseos_top)


def test_top_level_shim_uses_canonical_parser():
    args = chaseos_top.build_parser().parse_args([
        "runtime",
        "coordination-watch",
        "--runtime",
        "hermes",
        "--once",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "coordination-watch"
    assert args.runtime_id == "hermes"
    assert args.once is True


def test_canonical_runtime_dispatches_coordination_watch(monkeypatch):
    captured: dict[str, object] = {}

    def fake_run_coordination_watch(runtime_id, *, once=False, interval_seconds=None):
        captured["runtime_id"] = runtime_id
        captured["once"] = once
        captured["interval_seconds"] = interval_seconds
        return {"runtime": "Hermes", "mode": "once"}

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "run_coordination_watch", fake_run_coordination_watch)
    monkeypatch.setattr(cli, "_print_coordination_watch_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "coordination-watch",
        "--runtime",
        "hermes",
        "--once",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["once"] is True
    assert captured["payload"] == {"runtime": "Hermes", "mode": "once"}
    assert captured["as_json"] is True


def test_canonical_agent_bus_ingress_discord_accepts_coordination_flags():
    args = cli.build_parser().parse_args([
        "agent-bus",
        "ingress",
        "discord",
        "--to",
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
    ])

    assert args.func is cli.cmd_agent_bus_ingress_discord
    assert args.recipient == "OpenClaw"
    assert args.coordination_sensitive is True
    assert args.source_thread_id == "1496197360382906398"


def test_canonical_agent_bus_task_create_accepts_ingress_context():
    args = cli.build_parser().parse_args([
        "agent-bus",
        "task",
        "create",
        "--sender",
        "Hermes",
        "--to",
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
        "--control-plane-route",
        "discord:1493226848409358426:1496197360382906398",
        "--work-fingerprint",
        "discord-shared-work-001",
    ])

    assert args.func is cli.cmd_agent_bus_task_create
    assert args.sender == "Hermes"
    assert args.recipient == "OpenClaw"
    assert args.source_platform == "discord"
    assert args.work_fingerprint == "discord-shared-work-001"


def test_canonical_agent_bus_watch_accepts_interval():
    args = cli.build_parser().parse_args([
        "agent-bus",
        "watch",
        "--runtime",
        "OpenClaw",
        "--interval",
        "30",
        "--claim-next",
    ])

    assert args.func is cli.cmd_agent_bus_watch
    assert args.runtime == "OpenClaw"
    assert args.interval == 30
    assert args.claim_next is True


def test_canonical_agent_bus_heartbeat_accepts_instance_scope():
    args = cli.build_parser().parse_args([
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
        "--json",
    ])

    assert args.func is cli.cmd_agent_bus_heartbeat
    assert args.runtime_instance_id == "discord-thread-1496197360382906398"
    assert args.heartbeat_scope == "instance"
    assert args.output_json is True


def test_canonical_agent_bus_task_cleanup_accepts_hygiene_filters():
    args = cli.build_parser().parse_args([
        "agent-bus",
        "task",
        "cleanup",
        "--runtime",
        "Hermes",
        "--to",
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
        "5",
        "--reason",
        "Queue hygiene cleanup",
        "--apply",
        "--json",
    ])

    assert args.func is cli.cmd_agent_bus_task_cleanup
    assert args.runtime == "Hermes"
    assert args.recipient == "OpenClaw"
    assert args.sender == "Hermes"
    assert args.request_exact == "test"
    assert args.work_fingerprint == "discord:OpenClaw:message-a"
    assert args.conversation_key == "discord:ops:thread-a"
    assert args.origin_message_id == "message-a"
    assert args.limit == 5
    assert args.apply is True
