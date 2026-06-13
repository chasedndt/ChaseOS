"""Top-level chaseos shim tests for coordination-watch-bootstrap."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import runtime.cli.main as cli


MODULE_PATH = Path(__file__).resolve().parents[1] / "chaseos.py"
SPEC = importlib.util.spec_from_file_location("chaseos_top", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
chaseos_top = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(chaseos_top)


def test_top_level_shim_accepts_coordination_watch_bootstrap():
    args = chaseos_top.build_parser().parse_args([
        "runtime",
        "coordination-watch-bootstrap",
        "--runtime",
        "hermes",
        "--action",
        "status",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "coordination-watch-bootstrap"
    assert args.runtime_id == "hermes"
    assert args.action == "status"


def test_canonical_runtime_dispatches_coordination_watch_bootstrap_status(monkeypatch):
    captured: dict[str, object] = {}

    def fake_status(runtime_id):
        captured["runtime_id"] = runtime_id
        return {"runtime_id": runtime_id, "action": "status", "installed": False}

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "get_coordination_watch_bootstrap_status", fake_status)
    monkeypatch.setattr(cli, "_print_coordination_watch_bootstrap_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-bootstrap",
        "--runtime",
        "hermes",
        "--action",
        "status",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["payload"] == {"runtime_id": "hermes", "action": "status", "installed": False}
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_coordination_watch_bootstrap_verify(monkeypatch):
    captured: dict[str, object] = {}

    def fake_verify(runtime_id):
        captured["runtime_id"] = runtime_id
        return {"runtime_id": runtime_id, "action": "verify", "registered": True}

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "verify_coordination_watch_bootstrap", fake_verify)
    monkeypatch.setattr(cli, "_print_coordination_watch_bootstrap_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-bootstrap",
        "--runtime",
        "hermes",
        "--action",
        "verify",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["payload"] == {"runtime_id": "hermes", "action": "verify", "registered": True}
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_coordination_watch_bootstrap_activation_report(monkeypatch):
    captured: dict[str, object] = {}

    def fake_activation_report(runtime_id):
        captured["runtime_id"] = runtime_id
        return {
            "runtime_id": runtime_id,
            "action": "activation-report",
            "activation_state": "proven",
            "proof_ready": True,
        }

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_coordination_watch_activation_report", fake_activation_report)
    monkeypatch.setattr(cli, "_print_coordination_watch_bootstrap_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-bootstrap",
        "--runtime",
        "hermes",
        "--action",
        "activation-report",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["payload"] == {
        "runtime_id": "hermes",
        "action": "activation-report",
        "activation_state": "proven",
        "proof_ready": True,
    }
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_coordination_watch_bootstrap_activation_checklist(monkeypatch):
    captured: dict[str, object] = {}

    def fake_activation_checklist(runtime_id):
        captured["runtime_id"] = runtime_id
        return {
            "runtime_id": runtime_id,
            "action": "activation-checklist",
            "activation_state": "partial",
            "proof_complete": False,
        }

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_coordination_watch_activation_checklist", fake_activation_checklist)
    monkeypatch.setattr(cli, "_print_coordination_watch_bootstrap_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-bootstrap",
        "--runtime",
        "hermes",
        "--action",
        "activation-checklist",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["payload"] == {
        "runtime_id": "hermes",
        "action": "activation-checklist",
        "activation_state": "partial",
        "proof_complete": False,
    }
    assert captured["as_json"] is True
