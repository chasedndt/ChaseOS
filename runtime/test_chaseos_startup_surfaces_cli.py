"""Top-level chaseos shim tests for startup-surfaces."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import runtime.cli.main as cli


MODULE_PATH = Path(__file__).resolve().parents[1] / "chaseos.py"
SPEC = importlib.util.spec_from_file_location("chaseos_top_startup_surfaces", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
chaseos_top = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(chaseos_top)


def test_top_level_shim_accepts_startup_surfaces():
    args = chaseos_top.build_parser().parse_args([
        "runtime",
        "startup-surfaces",
        "--runtime",
        "hermes",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surfaces"
    assert args.runtime_id == "hermes"


def test_top_level_shim_accepts_launch_smoke_inventory():
    args = chaseos_top.build_parser().parse_args([
        "runtime",
        "launch-smoke-inventory",
        "--json",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "launch-smoke-inventory"
    assert args.output_json is True


def test_top_level_shim_accepts_startup_surface_toggle_plan():
    args = chaseos_top.build_parser().parse_args([
        "runtime",
        "startup-surface-toggle-plan",
        "--runtime",
        "openclaw",
        "--surface",
        "coordination_watch_supervisor",
        "--intent",
        "disable",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-toggle-plan"
    assert args.runtime_id == "openclaw"
    assert args.surface_id == "coordination_watch_supervisor"
    assert args.startup_intent == "disable"


def test_top_level_shim_accepts_startup_surface_settings():
    args = chaseos_top.build_parser().parse_args([
        "runtime",
        "startup-surface-settings",
        "--runtime",
        "hermes",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-settings"
    assert args.runtime_id == "hermes"


def test_top_level_shim_accepts_startup_surface_mutation_contract():
    args = chaseos_top.build_parser().parse_args([
        "runtime",
        "startup-surface-mutation-contract",
        "--runtime",
        "hermes",
        "--surface",
        "coordination_watch_bootstrap",
        "--intent",
        "enable",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-mutation-contract"
    assert args.runtime_id == "hermes"
    assert args.surface_id == "coordination_watch_bootstrap"
    assert args.startup_intent == "enable"


def test_top_level_shim_accepts_startup_surface_executor_preflight():
    args = chaseos_top.build_parser().parse_args([
        "runtime",
        "startup-surface-executor-preflight",
        "--runtime",
        "openclaw",
        "--surface",
        "coordination_watch_supervisor",
        "--intent",
        "disable",
        "--gate-approval-id",
        "startup-appr-test",
        "--plan-digest",
        "a" * 64,
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-executor-preflight"
    assert args.runtime_id == "openclaw"
    assert args.surface_id == "coordination_watch_supervisor"
    assert args.startup_intent == "disable"
    assert args.gate_approval_id == "startup-appr-test"
    assert args.plan_digest == "a" * 64


def test_top_level_shim_accepts_startup_surface_toggle():
    args = chaseos_top.build_parser().parse_args([
        "runtime",
        "startup-surface-toggle",
        "--runtime",
        "hermes",
        "--surface",
        "gateway",
        "--intent",
        "disable",
        "--confirm",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-toggle"
    assert args.runtime_id == "hermes"
    assert args.surface_id == "gateway"
    assert args.startup_intent == "disable"
    assert args.confirm is True
