"""Runtime CLI compatibility shim tests for coordination-watch."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import runtime.cli.main as cli


MODULE_PATH = Path(__file__).resolve().parent / "cli.py"
SPEC = importlib.util.spec_from_file_location("runtime_cli_script", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
runtime_cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_cli)


def test_runtime_cli_shim_uses_canonical_parser():
    args = runtime_cli.build_parser().parse_args([
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
