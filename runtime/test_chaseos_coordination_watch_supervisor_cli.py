"""Top-level chaseos shim tests for coordination-watch-supervisor."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import runtime.cli.main as cli


MODULE_PATH = Path(__file__).resolve().parents[1] / "chaseos.py"
SPEC = importlib.util.spec_from_file_location("chaseos_top", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
chaseos_top = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(chaseos_top)


def test_top_level_shim_accepts_coordination_watch_supervisor():
    args = chaseos_top.build_parser().parse_args([
        "runtime",
        "coordination-watch-supervisor",
        "--runtime",
        "hermes",
        "--action",
        "status",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "coordination-watch-supervisor"
    assert args.runtime_id == "hermes"
    assert args.action == "status"


def test_canonical_runtime_dispatches_coordination_watch_supervisor_status(monkeypatch):
    captured: dict[str, object] = {}

    def fake_status(runtime_id):
        captured["runtime_id"] = runtime_id
        return {"runtime_id": runtime_id, "action": "status", "running": False}

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "get_supervised_coordination_watch_status", fake_status)
    monkeypatch.setattr(cli, "_print_coordination_watch_supervisor_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "coordination-watch-supervisor",
        "--runtime",
        "hermes",
        "--action",
        "status",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["payload"] == {"runtime_id": "hermes", "action": "status", "running": False}
    assert captured["as_json"] is True

def test_top_level_shim_accepts_coordination_watch_supervisor_cleanup_stale():
    args = chaseos_top.build_parser().parse_args([
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

