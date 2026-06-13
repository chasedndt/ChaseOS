"""Entrypoint consolidation tests for the package-native ChaseOS CLI."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import json
import tomllib

import chaseos
import runtime.cli.main as cli
import runtime.cli.agent_bus_commands as agent_bus_commands


ROOT = Path(__file__).resolve().parents[2]


def _load_script_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_console_scripts_target_canonical_package_cli():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["scripts"]["chaseos"] == "runtime.cli.main:main"
    assert data["project"]["scripts"]["chase"] == "runtime.cli.main:main"


def test_root_shim_exports_canonical_entrypoints():
    # build_parser is re-exported directly — same object as the canonical CLI.
    assert chaseos.build_parser is cli.build_parser
    # main is a fast-path wrapper for studio panel probes; it delegates to cli.main
    # for all other commands. It is callable and re-exports build_parser correctly.
    assert callable(chaseos.main)


def test_runtime_script_shim_exports_canonical_entrypoints():
    runtime_script = _load_script_module("runtime_cli_script_test", ROOT / "runtime" / "cli.py")

    assert runtime_script.main is cli.main
    assert runtime_script.build_parser is cli.build_parser


def test_canonical_cli_exposes_runtime_and_setup_families():
    runtime_args = cli.build_parser().parse_args(["runtime", "inventory", "--json"])
    setup_args = cli.build_parser().parse_args(["setup", "provider", "list", "--json"])

    assert runtime_args.func is cli.cmd_runtime
    assert setup_args.func is cli.setup_cli.cmd_provider


def test_develop_explain_dry_run_returns_readonly_deprecated_workflow_envelope(capsys):
    args = cli.build_parser().parse_args([
        "develop",
        "explain",
        "--focus",
        "runtime/aor",
        "--question",
        "What is this?",
        "--target",
        "CLAUDE.md",
        "--scope",
        "ChaseOS Phase 9",
        "--dry-run",
        "--json",
    ])
    rc = args.func(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["workflow_id"] == "developer_repo_explain_shadow"
    assert payload["status"] == "dry_run_ok"
    assert payload["dry_run"] is True
    assert payload["outputs"]["dry_run"]["inputs"] == [
        "focus_area=runtime/aor",
        "question=What is this?",
        "target_paths=CLAUDE.md",
        "project_scope=ChaseOS Phase 9",
    ]
    assert payload["outputs"]["dry_run"]["workflow_execution_performed"] is False
    assert payload["outputs"]["dry_run"]["writes_performed"] is False
    assert payload["outputs"]["dry_run"]["deprecated_workflow_execution_blocked"] is True
    assert payload["authority_flags"]["workflow_execution_performed"] is False
    assert payload["authority_flags"]["canonical_writeback_allowed"] is False


def test_direct_setup_cli_parser_reuses_setup_subcommand_builder():
    parser = cli.setup_cli.build_parser()
    args = parser.parse_args(["provider", "list", "--json"])

    assert args.func is cli.setup_cli.cmd_provider
    assert args.setup_command == "list"


def test_setup_set_dry_run_plans_reference_only_update_without_writing(tmp_path, monkeypatch, capsys):
    setup_state = cli.setup_cli.load_setup_state.__globals__
    example_path = tmp_path / "setup_state.example.json"
    state_path = tmp_path / "setup_state.json"
    example_path.write_text(
        json.dumps(
            {
                "providers": {
                    "openai": {
                        "configured": True,
                        "secret_reference_present": True,
                        "secret_reference_kind": "env-var-or-local-secret-ref",
                        "secret_reference_target": "SET_OPENAI_SECRET_REF",
                    }
                },
                "integrations": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setitem(setup_state, "SETUP_STATE_EXAMPLE", example_path)
    monkeypatch.setitem(setup_state, "SETUP_STATE_PATH", state_path)

    args = cli.build_parser().parse_args(
        [
            "setup",
            "set",
            "provider",
            "openai",
            "secret_reference_kind=env-var-or-local-secret-ref",
            "secret_reference_present=true",
            "secret_reference_target=OPENAI_API_KEY",
            "--dry-run",
            "--json",
        ]
    )
    rc = args.func(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["surface"] == "chaseos_setup_state_set_dry_run"
    assert payload["dry_run"] is True
    assert payload["writes_setup_state"] is False
    assert payload["patch"]["secret_reference_target"] == "OPENAI_API_KEY"
    assert payload["secret_values_visible"] is False
    assert not state_path.exists()


def test_agent_bus_legacy_to_aliases_still_map_to_recipient():
    ingress_args = cli.build_parser().parse_args([
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
    ])
    create_args = cli.build_parser().parse_args([
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
    ])

    assert ingress_args.func is cli.cmd_agent_bus_ingress_discord
    assert ingress_args.recipient == "OpenClaw"
    assert create_args.func is cli.cmd_agent_bus_task_create
    assert create_args.recipient == "OpenClaw"


def test_gate_legacy_aliases_still_map_to_canonical_handlers():
    list_args = cli.build_parser().parse_args(["gate", "list"])
    show_args = cli.build_parser().parse_args(["gate", "show", "openclaw"])

    assert list_args.func is cli.cmd_gate_list_adapters
    assert show_args.func is cli.cmd_gate_show_adapter
    assert show_args.adapter_id == "openclaw"


def test_agent_bus_task_update_accepts_legacy_event_type_flag():
    args = cli.build_parser().parse_args([
        "agent-bus",
        "task",
        "update",
        "task-123",
        "--runtime",
        "OpenClaw",
        "--status",
        "review",
        "--event-type",
        "review_requested",
        "--message",
        "Ready for review",
    ])

    assert args.func is cli.cmd_agent_bus_task_update
    assert args.event_type == "review_requested"


def test_agent_bus_task_update_event_type_remains_optional():
    args = cli.build_parser().parse_args([
        "agent-bus",
        "task",
        "update",
        "task-123",
        "--runtime",
        "OpenClaw",
        "--status",
        "review",
        "--message",
        "Ready for review",
    ])

    assert args.func is cli.cmd_agent_bus_task_update
    assert args.event_type is None


def test_canonical_agent_bus_runtimes_json_includes_heartbeat_instances(monkeypatch, capsys):
    class _Cap:
        def __init__(self, task_type: str, priority: str):
            self.task_type = task_type
            self.priority = priority

    class _Caps:
        bus_name = "OpenClaw"
        display_name = "OpenClaw"
        description = "Primary runtime"
        handles = [_Cap("review", "high")]
        max_concurrent_tasks = 2
        heartbeat_stale_seconds = 300

    class _Live:
        last_seen = "2026-04-27T02:40:00Z"
        status = "busy"
        health = "ok"
        age_seconds = 12

    monkeypatch.setattr(agent_bus_commands, "_resolve_vault", lambda _: Path("."))
    monkeypatch.setattr(agent_bus_commands, "load_all_capabilities", lambda _: {"OpenClaw": _Caps()})
    monkeypatch.setattr(agent_bus_commands, "get_runtime_liveness", lambda _: {"OpenClaw": _Live()})
    monkeypatch.setattr(agent_bus_commands, "get_stale_runtimes", lambda _: set())

    class _Backend:
        def list_heartbeats(self):
            return [
                {
                    "runtime": "OpenClaw",
                    "runtime_instance_id": "discord-thread-1",
                    "status": "busy",
                },
                {
                    "runtime": "OpenClaw",
                    "runtime_instance_id": "discord-thread-2",
                    "status": "idle",
                },
            ]

    monkeypatch.setattr(agent_bus_commands, "get_backend", lambda _: _Backend())

    args = cli.build_parser().parse_args(["agent-bus", "runtimes", "--json"])
    rc = args.func(args)

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["bus_name"] == "OpenClaw"
    assert payload[0]["heartbeat_instance_count"] == 2
    assert len(payload[0]["heartbeat_instances"]) == 2


def test_doctor_cli_json_reports_canonical_entrypoints(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "_console_script_targets",
        lambda: {
            "chaseos": ["runtime.cli.main:main"],
            "chase": ["runtime.cli.main:main"],
        },
    )
    monkeypatch.setattr(cli.shutil, "which", lambda name: f"C:/fake/bin/{name}.exe")

    exit_code = cli.main(["doctor", "cli", "--vault-root", str(ROOT), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "doctor.cli"
    assert payload["result"]["expected_entrypoint"] == "runtime.cli.main:main"
    assert payload["result"]["pyproject_scripts"]["chaseos"] == "runtime.cli.main:main"
    assert payload["result"]["pyproject_scripts"]["chase"] == "runtime.cli.main:main"
