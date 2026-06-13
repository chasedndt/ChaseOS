"""Runtime CLI compatibility shim tests for coordination-watch-supervisor."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import runtime.cli.main as cli


MODULE_PATH = Path(__file__).resolve().parent / "cli.py"
SPEC = importlib.util.spec_from_file_location("runtime_cli_script", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
runtime_cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_cli)


def test_runtime_cli_shim_accepts_coordination_watch_supervisor_command():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-supervisor",
        "--runtime",
        "hermes",
        "--action",
        "plan",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "coordination-watch-supervisor"
    assert args.runtime_id == "hermes"
    assert args.action == "plan"


def test_canonical_runtime_dispatches_coordination_watch_supervisor_plan(monkeypatch):
    captured: dict[str, object] = {}

    def fake_plan(runtime_id, *, interval_seconds=None):
        captured["runtime_id"] = runtime_id
        captured["interval_seconds"] = interval_seconds
        return {"runtime_id": runtime_id, "action": "plan"}

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_supervised_coordination_watch_plan", fake_plan)
    monkeypatch.setattr(cli, "_print_coordination_watch_supervisor_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-supervisor",
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

def test_runtime_cli_shim_accepts_coordination_watch_supervisor_cleanup_stale():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-supervisor",
        "--runtime",
        "openclaw",
        "--action",
        "cleanup-stale",
        "--dry-run",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "coordination-watch-supervisor"
    assert args.runtime_id == "openclaw"
    assert args.action == "cleanup-stale"
    assert args.dry_run is True


def test_canonical_runtime_dispatches_coordination_watch_supervisor_cleanup_stale_dry_run(monkeypatch):
    captured: dict[str, object] = {}

    def fake_cleanup(runtime_id, *, dry_run=False):
        captured["runtime_id"] = runtime_id
        captured["dry_run"] = dry_run
        return {"runtime_id": runtime_id, "action": "cleanup-stale", "dry_run": dry_run}

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "cleanup_stale_supervised_coordination_watch", fake_cleanup)
    monkeypatch.setattr(cli, "_print_coordination_watch_supervisor_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-supervisor",
        "--runtime",
        "openclaw",
        "--action",
        "cleanup-stale",
        "--dry-run",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "openclaw"
    assert captured["dry_run"] is True
    assert captured["payload"] == {"runtime_id": "openclaw", "action": "cleanup-stale", "dry_run": True}
    assert captured["as_json"] is True

