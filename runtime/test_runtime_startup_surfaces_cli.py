"""Runtime CLI compatibility shim tests for startup-surfaces."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import runtime.cli.main as cli


MODULE_PATH = Path(__file__).resolve().parent / "cli.py"
SPEC = importlib.util.spec_from_file_location("runtime_cli_script_startup_surfaces", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
runtime_cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_cli)


def test_runtime_cli_shim_accepts_startup_surfaces_command():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "startup-surfaces",
        "--runtime",
        "all",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surfaces"
    assert args.runtime_id == "all"


def test_runtime_cli_shim_accepts_launch_smoke_inventory_command():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "launch-smoke-inventory",
        "--json",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "launch-smoke-inventory"
    assert args.output_json is True


def test_runtime_cli_shim_accepts_startup_surface_toggle_plan_command():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "startup-surface-toggle-plan",
        "--runtime",
        "hermes",
        "--surface",
        "gateway",
        "--intent",
        "enable",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-toggle-plan"
    assert args.runtime_id == "hermes"
    assert args.surface_id == "gateway"
    assert args.startup_intent == "enable"


def test_runtime_cli_shim_accepts_startup_surface_settings_command():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "startup-surface-settings",
        "--runtime",
        "hermes",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-settings"
    assert args.runtime_id == "hermes"


def test_runtime_cli_shim_accepts_startup_surface_mutation_contract_command():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "startup-surface-mutation-contract",
        "--runtime",
        "hermes",
        "--surface",
        "gateway",
        "--intent",
        "enable",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-mutation-contract"
    assert args.runtime_id == "hermes"
    assert args.surface_id == "gateway"
    assert args.startup_intent == "enable"


def test_runtime_cli_shim_accepts_startup_surface_executor_preflight_command():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "startup-surface-executor-preflight",
        "--runtime",
        "hermes",
        "--surface",
        "gateway",
        "--intent",
        "enable",
        "--gate-approval-id",
        "startup-appr-test",
        "--plan-digest",
        "a" * 64,
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-executor-preflight"
    assert args.runtime_id == "hermes"
    assert args.surface_id == "gateway"
    assert args.startup_intent == "enable"
    assert args.gate_approval_id == "startup-appr-test"
    assert args.plan_digest == "a" * 64


def test_runtime_cli_shim_accepts_startup_surface_approval_request_command():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "startup-surface-approval-request",
        "--runtime",
        "hermes",
        "--surface",
        "gateway",
        "--intent",
        "disable",
        "--gate-approval-id",
        "startup-appr-request-test",
        "--write-approval-request",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-approval-request"
    assert args.runtime_id == "hermes"
    assert args.surface_id == "gateway"
    assert args.startup_intent == "disable"
    assert args.gate_approval_id == "startup-appr-request-test"
    assert args.write_approval_request is True


def test_runtime_cli_shim_accepts_startup_surface_approval_decision_command():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "startup-surface-approval-decision",
        "--gate-approval-id",
        "startup-appr-request-test",
        "--decision",
        "approved",
        "--write-approval-decision",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-approval-decision"
    assert args.gate_approval_id == "startup-appr-request-test"
    assert args.decision == "approved"
    assert args.write_approval_decision is True


def test_runtime_cli_shim_accepts_startup_surface_approval_consumption_command():
    args = runtime_cli.build_parser().parse_args([
        "runtime",
        "startup-surface-approval-consumption",
        "--runtime",
        "hermes",
        "--surface",
        "gateway",
        "--intent",
        "disable",
        "--gate-approval-id",
        "startup-appr-request-test",
        "--plan-digest",
        "a" * 64,
        "--write-approval-consumption",
    ])

    assert args.func is cli.cmd_runtime
    assert args.runtime_command == "startup-surface-approval-consumption"
    assert args.runtime_id == "hermes"
    assert args.surface_id == "gateway"
    assert args.startup_intent == "disable"
    assert args.gate_approval_id == "startup-appr-request-test"
    assert args.plan_digest == "a" * 64
    assert args.write_approval_consumption is True


def test_runtime_cli_shim_accepts_startup_surface_toggle_command():
    args = runtime_cli.build_parser().parse_args([
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


def test_canonical_runtime_dispatches_startup_surfaces_report(monkeypatch):
    captured: dict[str, object] = {}

    def fake_report(runtime_id):
        captured["runtime_id"] = runtime_id
        return {
            "action": "startup-surfaces",
            "schema_version": 1,
            "read_only": True,
            "mutation_enabled": False,
            "runtimes": [],
        }

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_startup_surfaces_report", fake_report)
    monkeypatch.setattr(cli, "_print_startup_surfaces_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "startup-surfaces",
        "--runtime",
        "hermes",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["payload"] == {
        "action": "startup-surfaces",
        "schema_version": 1,
        "read_only": True,
        "mutation_enabled": False,
        "runtimes": [],
    }
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_startup_surface_toggle_plan(monkeypatch):
    captured: dict[str, object] = {}

    def fake_plan(runtime_id, surface_id, intent):
        captured["runtime_id"] = runtime_id
        captured["surface_id"] = surface_id
        captured["intent"] = intent
        return {
            "action": "startup-surface-toggle-plan",
            "schema_version": 1,
            "runtime_id": runtime_id,
            "surface_id": surface_id,
            "intent": intent,
            "read_only": True,
            "mutation_enabled": False,
            "steps": [],
        }

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_startup_surface_toggle_plan", fake_plan)
    monkeypatch.setattr(cli, "_print_startup_surface_toggle_plan_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "startup-surface-toggle-plan",
        "--runtime",
        "hermes",
        "--surface",
        "coordination_watch_bootstrap",
        "--intent",
        "disable",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["surface_id"] == "coordination_watch_bootstrap"
    assert captured["intent"] == "disable"
    assert captured["payload"] == {
        "action": "startup-surface-toggle-plan",
        "schema_version": 1,
        "runtime_id": "hermes",
        "surface_id": "coordination_watch_bootstrap",
        "intent": "disable",
        "read_only": True,
        "mutation_enabled": False,
        "steps": [],
    }
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_startup_surface_settings(monkeypatch):
    captured: dict[str, object] = {}

    def fake_settings(runtime_id):
        captured["runtime_id"] = runtime_id
        return {
            "action": "startup-surface-settings",
            "schema_version": 1,
            "read_only": True,
            "settings_write_enabled": False,
            "mutation_enabled": False,
            "runtimes": [],
        }

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_startup_surface_settings_report", fake_settings)
    monkeypatch.setattr(cli, "_print_startup_surface_settings_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "startup-surface-settings",
        "--runtime",
        "hermes",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["payload"] == {
        "action": "startup-surface-settings",
        "schema_version": 1,
        "read_only": True,
        "settings_write_enabled": False,
        "mutation_enabled": False,
        "runtimes": [],
    }
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_startup_surface_mutation_contract(monkeypatch):
    captured: dict[str, object] = {}

    def fake_contract(runtime_id, surface_id, intent):
        captured["runtime_id"] = runtime_id
        captured["surface_id"] = surface_id
        captured["intent"] = intent
        return {
            "action": "startup-surface-mutation-contract",
            "schema_version": 1,
            "runtime_id": runtime_id,
            "surface_id": surface_id,
            "intent": intent,
            "read_only": True,
            "execution_enabled": False,
            "executor_implemented": False,
        }

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_startup_surface_mutation_contract", fake_contract)
    monkeypatch.setattr(cli, "_print_startup_surface_mutation_contract_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "startup-surface-mutation-contract",
        "--runtime",
        "hermes",
        "--surface",
        "gateway",
        "--intent",
        "enable",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["surface_id"] == "gateway"
    assert captured["intent"] == "enable"
    assert captured["payload"] == {
        "action": "startup-surface-mutation-contract",
        "schema_version": 1,
        "runtime_id": "hermes",
        "surface_id": "gateway",
        "intent": "enable",
        "read_only": True,
        "execution_enabled": False,
        "executor_implemented": False,
    }
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_startup_surface_executor_preflight(monkeypatch):
    captured: dict[str, object] = {}

    def fake_preflight(runtime_id, surface_id, intent, *, gate_approval_id, plan_digest):
        captured["runtime_id"] = runtime_id
        captured["surface_id"] = surface_id
        captured["intent"] = intent
        captured["gate_approval_id"] = gate_approval_id
        captured["plan_digest"] = plan_digest
        return {
            "action": "startup-surface-executor-preflight",
            "schema_version": 1,
            "runtime_id": runtime_id,
            "surface_id": surface_id,
            "intent": intent,
            "read_only": True,
            "execution_enabled": False,
            "executor_invocation_allowed": False,
        }

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_startup_surface_executor_preflight", fake_preflight)
    monkeypatch.setattr(cli, "_print_startup_surface_executor_preflight_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "startup-surface-executor-preflight",
        "--runtime",
        "hermes",
        "--surface",
        "gateway",
        "--intent",
        "enable",
        "--gate-approval-id",
        "startup-appr-test",
        "--plan-digest",
        "a" * 64,
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["surface_id"] == "gateway"
    assert captured["intent"] == "enable"
    assert captured["gate_approval_id"] == "startup-appr-test"
    assert captured["plan_digest"] == "a" * 64
    assert captured["payload"] == {
        "action": "startup-surface-executor-preflight",
        "schema_version": 1,
        "runtime_id": "hermes",
        "surface_id": "gateway",
        "intent": "enable",
        "read_only": True,
        "execution_enabled": False,
        "executor_invocation_allowed": False,
    }
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_startup_surface_approval_request(monkeypatch):
    captured: dict[str, object] = {}

    def fake_request(runtime_id, surface_id, intent, *, gate_approval_id, requested_by, write):
        captured["runtime_id"] = runtime_id
        captured["surface_id"] = surface_id
        captured["intent"] = intent
        captured["gate_approval_id"] = gate_approval_id
        captured["requested_by"] = requested_by
        captured["write"] = write
        return {
            "action": "startup-surface-approval-request",
            "schema_version": 1,
            "runtime_id": runtime_id,
            "surface_id": surface_id,
            "intent": intent,
            "gate_approval_id": gate_approval_id,
            "written": write,
        }

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_startup_surface_approval_request", fake_request)
    monkeypatch.setattr(cli, "_print_startup_surface_approval_request_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "startup-surface-approval-request",
        "--runtime",
        "hermes",
        "--surface",
        "gateway",
        "--intent",
        "disable",
        "--gate-approval-id",
        "startup-appr-test",
        "--requested-by",
        "operator",
        "--write-approval-request",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["surface_id"] == "gateway"
    assert captured["intent"] == "disable"
    assert captured["gate_approval_id"] == "startup-appr-test"
    assert captured["requested_by"] == "operator"
    assert captured["write"] is True
    assert captured["payload"]["action"] == "startup-surface-approval-request"
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_startup_surface_approval_decision(monkeypatch):
    captured: dict[str, object] = {}

    def fake_decision(gate_approval_id, decision, *, decided_by, reason, write):
        captured["gate_approval_id"] = gate_approval_id
        captured["decision"] = decision
        captured["decided_by"] = decided_by
        captured["reason"] = reason
        captured["write"] = write
        return {
            "action": "startup-surface-approval-decision",
            "schema_version": 1,
            "gate_approval_id": gate_approval_id,
            "decision": decision,
            "written": write,
        }

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_startup_surface_approval_decision", fake_decision)
    monkeypatch.setattr(cli, "_print_startup_surface_approval_decision_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "startup-surface-approval-decision",
        "--gate-approval-id",
        "startup-appr-test",
        "--decision",
        "approved",
        "--requested-by",
        "operator",
        "--reason",
        "test",
        "--write-approval-decision",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["gate_approval_id"] == "startup-appr-test"
    assert captured["decision"] == "approved"
    assert captured["decided_by"] == "operator"
    assert captured["reason"] == "test"
    assert captured["write"] is True
    assert captured["payload"]["action"] == "startup-surface-approval-decision"
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_startup_surface_approval_consumption(monkeypatch):
    captured: dict[str, object] = {}

    def fake_consumption(runtime_id, surface_id, intent, *, gate_approval_id, plan_digest, consumed_by, write):
        captured["runtime_id"] = runtime_id
        captured["surface_id"] = surface_id
        captured["intent"] = intent
        captured["gate_approval_id"] = gate_approval_id
        captured["plan_digest"] = plan_digest
        captured["consumed_by"] = consumed_by
        captured["write"] = write
        return {
            "action": "startup-surface-approval-consumption",
            "schema_version": 1,
            "runtime_id": runtime_id,
            "surface_id": surface_id,
            "intent": intent,
            "gate_approval_id": gate_approval_id,
            "written": write,
        }

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_startup_surface_approval_consumption", fake_consumption)
    monkeypatch.setattr(cli, "_print_startup_surface_approval_consumption_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "startup-surface-approval-consumption",
        "--runtime",
        "hermes",
        "--surface",
        "gateway",
        "--intent",
        "disable",
        "--gate-approval-id",
        "startup-appr-test",
        "--plan-digest",
        "a" * 64,
        "--write-approval-consumption",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["runtime_id"] == "hermes"
    assert captured["surface_id"] == "gateway"
    assert captured["intent"] == "disable"
    assert captured["gate_approval_id"] == "startup-appr-test"
    assert captured["plan_digest"] == "a" * 64
    assert captured["consumed_by"] == "operator"
    assert captured["write"] is True
    assert captured["payload"]["action"] == "startup-surface-approval-consumption"
    assert captured["as_json"] is True


def test_canonical_runtime_dispatches_startup_surface_toggle(monkeypatch):
    captured: dict[str, object] = {}

    def fake_gate_context(runtime_id, surface_id, intent):
        captured["gate_context_args"] = (runtime_id, surface_id, intent)
        return {
            "operation": "lifecycle.startup_surface.gateway.disable",
            "write_targets": ["runtime/lifecycle/run/startup-surface-mutations/events.jsonl"],
            "external_api": "host.startup_folder",
            "external_side_effect": True,
        }

    def fake_toggle(runtime_id, surface_id, intent, *, confirm, dry_run, requested_by, interval_seconds):
        captured["toggle_args"] = (runtime_id, surface_id, intent)
        captured["confirm"] = confirm
        captured["dry_run"] = dry_run
        captured["requested_by"] = requested_by
        captured["interval_seconds"] = interval_seconds
        return {
            "action": "startup-surface-toggle",
            "schema_version": 1,
            "runtime_id": runtime_id,
            "surface_id": surface_id,
            "intent": intent,
            "confirmed": confirm,
            "dry_run": dry_run,
            "mutation_enabled": True,
            "executes_mutation": True,
            "before_state": "registered",
            "after_state": "off",
            "target_state": "off",
            "target_reached": True,
            "gate_operation": "lifecycle.startup_surface.gateway.disable",
            "verification_commands": [],
        }

    def fake_print(payload, as_json):
        captured["payload"] = payload
        captured["as_json"] = as_json
        return 0

    monkeypatch.setattr(cli, "build_startup_surface_gate_context", fake_gate_context)
    monkeypatch.setattr(cli, "execute_startup_surface_toggle", fake_toggle)
    monkeypatch.setattr(cli, "_print_startup_surface_toggle_execution_result", fake_print)

    args = cli.build_parser().parse_args([
        "runtime",
        "startup-surface-toggle",
        "--runtime",
        "hermes",
        "--surface",
        "gateway",
        "--intent",
        "disable",
        "--confirm",
        "--json",
    ])

    result = cli.cmd_runtime(args)

    assert result == 0
    assert captured["gate_context_args"] == ("hermes", "gateway", "disable")
    assert captured["toggle_args"] == ("hermes", "gateway", "disable")
    assert captured["confirm"] is True
    assert captured["dry_run"] is False
    assert captured["payload"]["action"] == "startup-surface-toggle"
    assert captured["as_json"] is True
