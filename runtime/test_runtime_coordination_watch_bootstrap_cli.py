"""Runtime CLI compatibility shim tests for coordination-watch-bootstrap."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import runtime.cli.main as cli


MODULE_PATH = Path(__file__).resolve().parent / "cli.py"
SPEC = importlib.util.spec_from_file_location("runtime_cli_script", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
runtime_cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_cli)


def test_runtime_cli_shim_accepts_coordination_watch_bootstrap_command():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-bootstrap",
        "--runtime",
        "hermes",
        "--action",
        "plan",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "coordination-watch-bootstrap"
    assert args.runtime_id == "hermes"
    assert args.action == "plan"


def test_canonical_runtime_dispatches_coordination_watch_bootstrap_plan(monkeypatch):
    captured: dict[str, object] = {}

    def fake_plan(runtime_id):
        captured["runtime_id"] = runtime_id
        return {"runtime_id": runtime_id, "action": "plan"}

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_coordination_watch_bootstrap_plan", fake_plan)
    monkeypatch.setattr(cli, "_print_coordination_watch_bootstrap_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-bootstrap",
        "--runtime",
        "hermes",
        "--action",
        "plan",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["payload"] == {"runtime_id": "hermes", "action": "plan"}
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_coordination_watch_bootstrap_apply(monkeypatch):
    captured: dict[str, object] = {}

    def fake_apply(runtime_id):
        captured["runtime_id"] = runtime_id
        return {"runtime_id": runtime_id, "action": "apply", "applied": True}

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "apply_coordination_watch_bootstrap", fake_apply)
    monkeypatch.setattr(cli, "_print_coordination_watch_bootstrap_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-bootstrap",
        "--runtime",
        "openclaw",
        "--action",
        "apply",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "openclaw"
    assert captured["payload"] == {"runtime_id": "openclaw", "action": "apply", "applied": True}
