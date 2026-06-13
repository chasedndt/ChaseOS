"""Contract tests for the canonical ChaseOS CLI parser surface."""

from __future__ import annotations

import argparse
import ast
import json
import tomllib
from pathlib import Path

import runtime.cli.main as cli
from runtime.cli.contract_ratchet import (
    DEFERRED_SMOKE_COMMANDS,
    INTAKE_SMOKE_FIXTURE_ITEM,
    INTAKE_SMOKE_FIXTURE_VAULT,
    MAINTAIN_SMOKE_FIXTURE_VAULT,
    SITEOPS_CANDIDATE_SMOKE_VAULT,
    SETUP_STATE_SMOKE_FIXTURE,
    SMOKE_COMMANDS,
    deferred_smoke_closure_failures,
    deferred_smoke_closure_map,
    family_ratchet_dispositions,
    _append_arg_sync_failures,
    _run_cli_json_smoke,
    verify_cli_contract_ratchet,
)
from runtime.cli.generate_docs import (
    DOC_PATH,
    HANDBOOK_PATH,
    operator_handbook_coverage_failures,
    render_markdown,
    render_operator_handbook,
)
from runtime.cli.json_contract import JSON_CONTRACT_KEYS


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "runtime" / "cli" / "command_contract.json"
PYPROJECT_PATH = ROOT / "pyproject.toml"
COMMAND_CHOICE_DESTS = {"runtime_command", "setup_command"}
DEFAULT_PARSE_ARGS_BY_PATH = {
    ("agent-bus", "codex-daemon"): ["--readiness"],
    ("agent-bus", "watch"): ["--once"],
    ("events", "dispatch"): ["--pending"],
    ("events", "watch"): ["--once"],
    ("watch", "run"): ["--once"],
}


def _load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _subparser_action(parser: argparse.ArgumentParser) -> argparse._SubParsersAction | None:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    return None


def _parser_surface_paths(
    parser: argparse.ArgumentParser | None = None,
    path: tuple[str, ...] = (),
) -> set[tuple[str, ...]]:
    parser = parser or cli.build_parser()
    subparser = _subparser_action(parser)
    if subparser is not None:
        paths: set[tuple[str, ...]] = set()
        seen: set[int] = set()
        for name, child in subparser.choices.items():
            if id(child) in seen:
                continue
            seen.add(id(child))
            paths.update(_parser_surface_paths(child, path + (name,)))
        return paths

    for action in parser._actions:
        if (
            not action.option_strings
            and action.dest in COMMAND_CHOICE_DESTS
            and getattr(action, "choices", None)
        ):
            return {path + (str(choice),) for choice in action.choices}
    return {path}


def _resolve_parser(path: list[str]) -> tuple[argparse.ArgumentParser, list[str]]:
    parser = cli.build_parser()
    remaining = list(path)
    while remaining:
        subparser = _subparser_action(parser)
        if subparser is None or remaining[0] not in subparser.choices:
            break
        parser = subparser.choices[remaining.pop(0)]
    return parser, remaining


def _expand_args(contract: dict, args: list[dict]) -> list[dict]:
    expanded: list[dict] = []
    for arg in args:
        include = arg.get("include")
        if include:
            expanded.extend(_expand_args(contract, contract["arg_sets"][include]))
        else:
            expanded.append(arg)
    return expanded


def _contract_paths(contract: dict) -> set[tuple[str, ...]]:
    return {tuple(command["path"]) for command in contract["commands"]}


def _command_by_path(contract: dict, path: tuple[str, ...]) -> dict:
    for command in contract["commands"]:
        if tuple(command["path"]) == path:
            return command
    raise AssertionError(f"command path missing from contract: {' '.join(path)}")


def _actions_by_dest(parser: argparse.ArgumentParser, remaining_path: list[str]) -> tuple[dict, dict]:
    consumed_choice_dests: set[str] = set()
    for token in remaining_path:
        for action in parser._actions:
            if (
                not action.option_strings
                and getattr(action, "choices", None)
                and token in action.choices
            ):
                consumed_choice_dests.add(action.dest)
                break
        else:
            raise AssertionError(f"Could not resolve command path token {token!r}")

    option_actions = {}
    positional_actions = {}
    for action in parser._actions:
        if action.dest == "help" or isinstance(action, argparse._SubParsersAction):
            continue
        if action.option_strings:
            option_actions[action.dest] = action
        elif action.dest not in consumed_choice_dests:
            positional_actions[action.dest] = action
    return option_actions, positional_actions


def _example_value(arg: dict) -> str:
    choices = arg.get("choices")
    if choices:
        return str(choices[0])
    dest = str(arg.get("dest", "")).lower()
    if dest.endswith("_seconds") or dest in {"seconds", "interval", "limit", "max_cycles"}:
        return "1"
    return {
        "PATH": "example.md",
        "URL": "https://example.com",
        "RUNTIME": "Hermes",
        "RUNTIME_ID": "openclaw",
        "SCHEDULE_ID": "sch-example",
        "WORKFLOW_ID": "operator_today",
        "ADAPTER_ID": "openclaw",
        "TASK_ID": "task-example",
        "KEY=VALUE": "configured=true",
        "KEY": "operator.theme",
        "VALUE": "quiet",
        "NAME": "Example",
        "N": "1",
        "SECONDS": "1",
        "YYYY-MM-DD": "2026-04-27",
    }.get(str(arg.get("value", "")).upper(), "example")


def _parse_example(contract: dict, command: dict) -> list[str]:
    argv = list(command["path"])
    provided = set(command.get("parse_args", []))
    expanded_args = _expand_args(contract, command.get("args", []))

    for arg in expanded_args:
        if arg.get("kind") == "positional" and arg.get("required", False):
            argv.append(_example_value(arg))

    for arg in expanded_args:
        flags = arg.get("flags")
        if not flags or not arg.get("required", False):
            continue
        if any(flag in provided for flag in flags):
            continue
        if arg.get("kind") == "flag":
            argv.append(flags[0])
            continue
        argv.extend([flags[0], _example_value(arg)])

    parse_args = command.get("parse_args", [])
    if parse_args:
        argv.extend(parse_args)
    else:
        argv.extend(DEFAULT_PARSE_ARGS_BY_PATH.get(tuple(command["path"]), []))
    return argv


def test_contract_lists_every_parser_command_path() -> None:
    contract = _load_contract()

    assert _contract_paths(contract) == _parser_surface_paths()


def test_contract_command_paths_are_unique() -> None:
    contract = _load_contract()
    paths = [tuple(command["path"]) for command in contract["commands"]]

    assert len(paths) == len(set(paths))


def test_siteops_cli_handlers_are_defined_once() -> None:
    source = ROOT / "runtime" / "cli" / "siteops_commands.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    defs = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]

    assert len(defs) == len(set(defs))


def test_contract_metadata_is_machine_readable_and_complete() -> None:
    contract = _load_contract()

    assert contract["schema_version"] == 1
    assert contract["json_contract"]["envelope_keys"] == list(JSON_CONTRACT_KEYS)
    assert contract["entrypoints"]

    for command in contract["commands"]:
        assert command["family"] in contract["families"]
        assert command["maturity"]
        assert command["handler"]
        assert command["json_shape"] in contract["json_shapes"]
        assert isinstance(command["side_effects"], list)
        assert command["side_effects"]


def test_contract_args_match_argparse_actions() -> None:
    contract = _load_contract()

    for command in contract["commands"]:
        parser, remaining = _resolve_parser(command["path"])
        actual_options, actual_positionals = _actions_by_dest(parser, remaining)
        expected_args = _expand_args(contract, command.get("args", []))
        expected_options = {arg["dest"]: arg for arg in expected_args if arg.get("flags")}
        expected_positionals = {
            arg["dest"]: arg
            for arg in expected_args
            if arg.get("kind") == "positional"
        }

        assert set(actual_options) == set(expected_options), command["path"]
        assert set(actual_positionals) == set(expected_positionals), command["path"]

        for dest, expected in expected_options.items():
            actual = actual_options[dest]
            assert set(actual.option_strings) == set(expected["flags"]), command["path"]
            if "required" in expected:
                assert actual.required is expected["required"], command["path"]
            actual_choices = getattr(actual, "choices", None)
            if actual_choices is not None:
                assert "choices" in expected, (command["path"], dest)
                assert list(actual_choices) == expected["choices"], command["path"]
            else:
                assert "choices" not in expected, (command["path"], dest)

        for dest, expected in expected_positionals.items():
            actual = actual_positionals[dest]
            actual_choices = getattr(actual, "choices", None)
            if actual_choices is not None:
                assert "choices" in expected, (command["path"], dest)
                assert list(actual_choices) == expected["choices"], command["path"]
            else:
                assert "choices" not in expected, (command["path"], dest)
            if "nargs" in expected:
                assert actual.nargs == expected["nargs"], command["path"]


def test_contract_examples_parse_to_declared_handlers() -> None:
    contract = _load_contract()
    parser = cli.build_parser()

    for command in contract["commands"]:
        args = parser.parse_args(_parse_example(contract, command))
        assert args.func.__name__ == command["handler"], command["path"]


def test_cli_contract_arg_sync_reuses_single_parser_build() -> None:
    build_count = 0

    def build_parser() -> argparse.ArgumentParser:
        nonlocal build_count
        build_count += 1
        parser = argparse.ArgumentParser(prog="fixture")
        sub = parser.add_subparsers(dest="command")
        sub.required = True
        for name in ("alpha", "beta"):
            child = sub.add_parser(name)
            child.add_argument("--json", action="store_true", dest="output_json")
        return parser

    class FixtureCli:
        @staticmethod
        def build_parser() -> argparse.ArgumentParser:
            return build_parser()

    contract = {
        "arg_sets": {},
        "commands": [
            {
                "path": ["alpha"],
                "args": [
                    {
                        "dest": "output_json",
                        "flags": ["--json"],
                        "kind": "flag",
                    }
                ],
            },
            {
                "path": ["beta"],
                "args": [
                    {
                        "dest": "output_json",
                        "flags": ["--json"],
                        "kind": "flag",
                    }
                ],
            },
        ],
    }
    failures: list[str] = []

    _append_arg_sync_failures(contract, FixtureCli, failures)

    assert failures == []
    assert build_count == 1


def test_json_shape_support_matches_json_flag() -> None:
    contract = _load_contract()

    for command in contract["commands"]:
        args = _expand_args(contract, command.get("args", []))
        has_json_flag = any("--json" in arg.get("flags", []) for arg in args)
        shape = contract["json_shapes"][command["json_shape"]]
        supported = shape.get("supported", shape.get("supports_json_flag"))
        assert supported is has_json_flag, command["path"]


def test_generated_cli_docs_match_command_contract() -> None:
    contract = _load_contract()

    assert DOC_PATH.read_text(encoding="utf-8") == render_markdown(contract)
    handbook = HANDBOOK_PATH.read_text(encoding="utf-8")
    assert handbook == render_operator_handbook(contract)
    assert operator_handbook_coverage_failures(contract, handbook) == []


def test_cli_contract_ratchet_verifies_parser_contract_docs_and_smokes() -> None:
    result = verify_cli_contract_ratchet(run_smokes=True)

    assert result["ok"], "\n".join(result["failures"])


def test_cli_contract_ratchet_includes_read_only_smoke_profile_batch() -> None:
    smoke_specs = {spec["name"]: spec for spec in SMOKE_COMMANDS}

    assert smoke_specs["agent.list"]["required_result_paths"] == (
        ("result", "runtimes"),
        ("result", "count"),
    )
    assert smoke_specs["config.summary"]["required_result_paths"] == (
        ("result", "read_only"),
        ("result", "mutates_config"),
        ("result", "governance"),
    )
    assert smoke_specs["gate.validate"]["required_result_paths"] == (
        ("result", "valid"),
        ("result", "errors"),
    )
    assert smoke_specs["memory.status"]["required_result_paths"] == (
        ("result", "layer_c"),
        ("result", "layer_d"),
    )
    assert smoke_specs["schedule.validate"]["required_result_paths"] == (
        ("result", "valid"),
        ("result", "error_count"),
        ("result", "errors"),
    )
    assert smoke_specs["models.list"]["required_result_paths"] == (
        ("result", "*", "provider_id"),
        ("result", "*", "model_id"),
        ("result", "*", "configured"),
    )
    assert smoke_specs["providers.status"]["required_result_paths"] == (
        ("result", "*", "provider_id"),
        ("result", "*", "configured"),
        ("result", "*", "valid"),
    )
    assert smoke_specs["osril.resume-ready"]["argv"] == [
        "osril",
        "resume-ready",
        "--dry-run",
        "--json",
    ]
    assert smoke_specs["osril.resume-ready"]["required_result_paths"] == (
        ("result", "dry_run"),
        ("result", "ready_count"),
        ("result", "wait_resume_state"),
    )
    assert smoke_specs["sbp.delivery-health"]["required_result_paths"] == (
        ("result", "summary"),
        ("result", "summary", "event_count"),
        ("result", "events"),
    )
    assert smoke_specs["watch.list"]["required_result_paths"] == (
        ("result", "folders"),
        ("result", "count"),
    )
    assert smoke_specs["setup.status"]["required_result_paths"] == (
        ("result", "providers"),
        ("result", "integrations"),
    )
    assert smoke_specs["setup.status"]["setup_state_path"] == str(SETUP_STATE_SMOKE_FIXTURE)
    assert smoke_specs["setup.provider.list"]["required_result_paths"] == (
        ("result", "*", "id"),
        ("result", "*", "setup_kind"),
        ("result", "*", "status"),
    )
    assert smoke_specs["setup.integration.list"]["required_result_paths"] == (
        ("result", "*", "id"),
        ("result", "*", "setup_kind"),
        ("result", "*", "status"),
    )
    assert smoke_specs["develop.explain.dry-run"]["argv"] == [
        "develop",
        "explain",
        "--question",
        "ratchet smoke dry run",
        "--dry-run",
        "--json",
    ]
    assert smoke_specs["develop.explain.dry-run"]["expected_action"] == "develop.explain"
    assert smoke_specs["develop.explain.dry-run"]["required_result_paths"] == (
        ("result", "workflow_id"),
        ("result", "status"),
        ("result", "outputs", "dry_run"),
    )
    assert smoke_specs["capture.status"]["argv"] == [
        "capture",
        "status",
        "--vault-root",
        str(INTAKE_SMOKE_FIXTURE_VAULT),
        "--json",
    ]
    assert smoke_specs["capture.status"]["required_result_paths"] == (
        ("result", "status"),
        ("result", "read_only"),
        ("result", "mutates_capture"),
        ("result", "total_quarantine"),
        ("result", "dedup_registry", "entry_count"),
        ("result", "writes_performed"),
        ("result", "authority_flags"),
    )
    assert smoke_specs["intake.dedup-stats"]["argv"] == [
        "intake",
        "dedup-stats",
        "--vault-root",
        str(INTAKE_SMOKE_FIXTURE_VAULT),
        "--json",
    ]
    assert smoke_specs["intake.dedup-stats"]["required_result_paths"] == (
        ("result", "registry_path"),
        ("result", "entry_count"),
        ("result", "registry_exists"),
    )
    assert smoke_specs["intake.ls"]["argv"] == [
        "intake",
        "ls",
        "--vault-root",
        str(INTAKE_SMOKE_FIXTURE_VAULT),
        "--json",
    ]
    assert smoke_specs["intake.ls"]["required_result_paths"] == (
        ("result", "status"),
        ("result", "read_only"),
        ("result", "classes"),
        ("result", "total_quarantine"),
        ("result", "writes_performed"),
        ("result", "authority_flags"),
    )
    assert smoke_specs["intake.inspect"]["argv"] == [
        "intake",
        "inspect",
        str(INTAKE_SMOKE_FIXTURE_ITEM),
        "--json",
    ]
    assert smoke_specs["intake.inspect"]["required_result_paths"] == (
        ("result", "schema_version"),
        ("result", "capture_id"),
        ("result", "content_filename"),
        ("result", "input_class"),
        ("result", "quarantine_status"),
        ("result", "promotion_status"),
        ("result", "extra_metadata", "writes_performed"),
    )
    assert smoke_specs["maintain.status"]["argv"] == ["maintain", "--status", "--json"]
    assert smoke_specs["maintain.status"]["expected_action"] == "maintain"
    assert smoke_specs["maintain.status"]["required_result_paths"] == (
        ("result", "status"),
        ("result", "read_only"),
        ("result", "mutates_vault"),
        ("result", "full_scan_deferred_from_ratchet"),
        ("result", "stages"),
        ("result", "writes_performed"),
        ("result", "authority_flags"),
    )
    assert smoke_specs["capture.validate"]["argv"] == [
        "capture",
        "validate",
        "--vault-root",
        str(INTAKE_SMOKE_FIXTURE_VAULT),
        "--json",
    ]
    assert smoke_specs["capture.validate"]["expected_action"] == "capture.validate"
    assert smoke_specs["capture.validate"]["required_result_paths"] == (
        ("result", "status"),
        ("result", "valid"),
        ("result", "read_only"),
        ("result", "safe_validate_only"),
        ("result", "dedup_registry", "entry_count"),
        ("result", "validated_modes"),
        ("result", "forbidden_actions"),
        ("result", "writes_performed"),
        ("result", "authority_flags"),
    )
    assert smoke_specs["maintain.fixture-dry-run"]["argv"] == [
        "maintain",
        "--dry-run",
        "--fixture-root",
        str(MAINTAIN_SMOKE_FIXTURE_VAULT),
        "--json",
    ]
    assert smoke_specs["maintain.fixture-dry-run"]["expected_action"] == "maintain"
    assert smoke_specs["maintain.fixture-dry-run"]["required_result_paths"] == (
        ("result", "status"),
        ("result", "dry_run"),
        ("result", "read_only"),
        ("result", "bounded_fixture_mode"),
        ("result", "bounded_fixture_root"),
        ("result", "writes_performed"),
        ("result", "authority_flags"),
        ("result", "stage_1_vault_hygiene", "files_scanned"),
        ("result", "stage_2_daily_hub", "files_scanned"),
        ("result", "stage_3_provenance", "files_scanned"),
    )
    assert smoke_specs["agent-bus.status"]["required_result_paths"] == (
        ("result", "task_count"),
        ("result", "open_count"),
        ("result", "done_count"),
    )
    assert smoke_specs["events.validate"]["required_result_paths"] == (
        ("result", "valid"),
        ("result", "error_count"),
        ("result", "errors"),
    )
    assert smoke_specs["events.rules"]["required_result_paths"] == (
        ("result", "count"),
        ("result", "rules"),
    )
    assert smoke_specs["context.boot"]["required_result_paths"] == (
        ("result", "runtime_id"),
        ("result", "boot_status"),
        ("result", "sources_read"),
    )
    assert smoke_specs["operate.browser.policy"]["required_result_paths"] == (
        ("result", "read_only"),
        ("result", "mutates_browser"),
        ("result", "governance"),
    )
    assert smoke_specs["scorecard.list"]["required_result_paths"] == (
        ("result", "runtime_ids"),
        ("result", "count"),
    )
    assert smoke_specs["scaffold.project"]["argv"] == [
        "scaffold",
        "project",
        "example",
        "--json",
    ]
    assert smoke_specs["scaffold.project"]["required_result_paths"] == (
        ("result", "scaffold_type"),
        ("result", "write"),
        ("result", "draft_only"),
    )
    assert smoke_specs["run.operator_today.dry-run"]["argv"] == [
        "run",
        "operator_today",
        "--dry-run",
        "--json",
    ]
    assert smoke_specs["run.operator_today.dry-run"]["expected_action"] == "run"
    assert smoke_specs["run.operator_today.dry-run"]["required_result_paths"] == (
        ("result", "workflow_id"),
        ("result", "status"),
        ("result", "dry_run"),
        ("result", "stage_reached"),
        ("result", "outputs", "dry_run"),
        ("result", "writes_performed"),
        ("result", "authority_flags"),
    )
    assert smoke_specs["core-export.readiness"]["argv"] == [
        "core-export",
        "readiness",
        "--json",
    ]
    assert smoke_specs["core-export.readiness"]["expected_exit_code"] == 1
    assert smoke_specs["core-export.readiness"]["expected_ok"] is False
    assert smoke_specs["core-export.readiness"]["required_result_paths"] == (
        ("result", "readiness_status"),
        ("result", "blocking_issues"),
        ("result", "writes_performed"),
        ("result", "real_export_allowed_without_gate"),
    )
    assert smoke_specs["health.openclaw.gateway"]["optional_live_readiness"] is True
    assert smoke_specs["health.openclaw.gateway"]["expected_action"] == "health"
    assert smoke_specs["health.openclaw.gateway"]["allowed_statuses"] == {
        "healthy": {"exit_code": 0, "ok": True},
        "unavailable": {"exit_code": 1, "ok": False},
    }
    assert smoke_specs["health.hermes.gateway"]["optional_live_readiness"] is True
    assert smoke_specs["health.hermes.gateway"]["expected_action"] == "health"
    assert smoke_specs["health.codex.session-heartbeat"]["optional_readiness"] is True
    assert smoke_specs["health.codex.session-heartbeat"]["expected_action"] == "health"
    assert smoke_specs["health.codex.session-heartbeat"]["allowed_statuses"] == {
        "healthy": {"exit_code": 0, "ok": True},
        "unavailable": {"exit_code": 1, "ok": False},
    }
    assert smoke_specs["health.codex.session-heartbeat"]["required_result_paths"] == (
        ("result", "runtime_id"),
        ("result", "kind"),
        ("result", "status"),
        ("result", "heartbeat_runtime"),
        ("result", "heartbeat_present"),
        ("result", "heartbeat_fresh"),
        ("result", "heartbeat_stale_after_seconds"),
        ("result", "probes"),
        ("result", "writes_performed"),
        ("result", "authority_flags"),
    )
    assert smoke_specs["health.archon.session-heartbeat"]["optional_readiness"] is True
    assert smoke_specs["health.archon.session-heartbeat"]["expected_action"] == "health"
    assert smoke_specs["n8n.readiness"]["optional_readiness"] is True
    assert smoke_specs["n8n.readiness"]["expected_action"] == "n8n.readiness"
    assert smoke_specs["n8n.readiness"]["allowed_statuses"] == {
        "ready": {"exit_code": 0, "ok": True},
        "blocked": {"exit_code": 1, "ok": False},
    }
    assert smoke_specs["n8n.readiness"]["required_result_paths"] == (
        ("result", "status"),
        ("result", "readiness_status"),
        ("result", "blocked_reasons"),
        ("result", "live_http_call"),
        ("result", "connection", "blocked_reasons"),
        ("result", "registry", "ok"),
        ("result", "forbidden"),
        ("result", "writes_performed"),
        ("result", "authority_flags"),
    )
    assert smoke_specs["n8n.dry-run"]["argv"] == [
        "n8n",
        "dry-run",
        "send_discord_draft_alert",
        "--caller",
        "chaseos_runtime_mcp",
        "--payload",
        "{}",
        "--json",
    ]
    assert smoke_specs["n8n.dry-run"]["expected_action"] == "n8n.dry-run"
    assert smoke_specs["n8n.dry-run"]["required_result_paths"] == (
        ("result", "status"),
        ("result", "readiness_status"),
        ("result", "workflow_id"),
        ("result", "dry_run"),
        ("result", "live_http_call"),
        ("result", "writes_performed"),
        ("result", "draft", "policy", "current_status"),
        ("result", "forbidden_actions"),
        ("result", "authority_flags"),
    )


def test_cli_contract_ratchet_deferred_smoke_map_documents_unsafe_or_noncanonical_surfaces() -> None:
    deferred_specs = {spec["name"]: spec for spec in DEFERRED_SMOKE_COMMANDS}
    smoke_names = {spec["name"] for spec in SMOKE_COMMANDS}

    assert "health.session-heartbeat" not in deferred_specs
    assert deferred_specs["capture.family"]["status"] == "permanent_deferred_mutating_or_external"
    assert deferred_specs["capture.family"]["closure_status"] == "closed_by_capture_status_and_validate_smokes"
    assert deferred_specs["capture.family"]["representative_smoke"] == "capture.validate"
    assert "intake.ls" not in deferred_specs
    assert "intake.inspect" not in deferred_specs
    assert "maintain.dry-run" not in deferred_specs
    assert "run.operator_today.dry-run" not in deferred_specs
    assert deferred_specs["n8n.execute"]["closure_status"] == "closed_by_n8n_readiness_and_dry_run_smokes"
    assert deferred_specs["n8n.execute"]["representative_smoke"] == "n8n.dry-run"
    assert "health.openclaw.gateway" in smoke_names
    assert "health.hermes.gateway" in smoke_names
    assert "health.codex.session-heartbeat" in smoke_names
    assert "health.archon.session-heartbeat" in smoke_names
    assert "n8n.readiness" in smoke_names
    assert "n8n.dry-run" in smoke_names
    assert "capture.status" in smoke_names
    assert "capture.validate" in smoke_names
    assert "intake.ls" in smoke_names
    assert "intake.inspect" in smoke_names
    assert "maintain.status" in smoke_names
    assert "maintain.fixture-dry-run" in smoke_names
    assert "run.operator_today.dry-run" in smoke_names
    assert "capture.family" not in smoke_names

    result = verify_cli_contract_ratchet(run_smokes=False)
    result_deferred = {spec["name"]: spec for spec in result["deferred_smoke_commands"]}
    assert "maintain.dry-run" not in result_deferred
    assert result_deferred["n8n.execute"]["command"] == "chaseos n8n execute"
    assert result_deferred["n8n.execute"]["representative_smoke"] == "n8n.dry-run"
    closure_rows = {row["name"]: row for row in result["deferred_closure_map"]}
    assert closure_rows["n8n.execute"]["representative_smoke_present"] is True
    assert closure_rows["capture.family"]["blocker_type"] == "mutating_or_external"
    assert all(row["closure_status"].startswith("closed_") for row in closure_rows.values())

    family_rows = {row["family"]: row for row in family_ratchet_dispositions(_load_contract())}
    assert family_rows["capture"]["status"] == "smoke_covered"
    assert family_rows["health"]["status"] == "smoke_covered"
    assert family_rows["intake"]["status"] == "smoke_covered"
    assert family_rows["maintain"]["status"] == "smoke_covered"
    assert family_rows["n8n"]["status"] == "smoke_covered"
    assert family_rows["run"]["status"] == "smoke_covered"
    assert family_rows["test"]["status"] == "contract_docs_only"
    assert all(row["status"] != "unknown" for row in family_rows.values())


def test_cli_contract_ratchet_deferred_closure_map_is_machine_checkable() -> None:
    closure_rows = {row["name"]: row for row in deferred_smoke_closure_map()}

    assert deferred_smoke_closure_failures() == []
    assert set(closure_rows) == {
        "n8n.execute",
        "capture.family",
    }
    for name, row in closure_rows.items():
        assert row["command"].startswith("chaseos "), name
        assert row["reason"], name
        assert row["fixture_readiness"], name
        assert row["promotion_condition"], name
        assert row["representative_smoke_present"] is True, name
        assert row["forbidden_during_ratchet"], name


def test_cli_contract_ratchet_read_only_smoke_failures_name_exact_path(capsys) -> None:
    class FakeCli:
        @staticmethod
        def main(argv: list[str]) -> int:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "action": "gate.validation",
                        "result": {"errors": []},
                        "errors": [],
                        "warnings": [],
                        "audit_id": None,
                    }
                )
            )
            return 0

    spec = {
        "name": "gate.validate",
        "argv": ["gate", "validate", "--json"],
        "expected_action": "gate.validate",
        "required_result_paths": (("result", "valid"), ("result", "errors")),
    }

    _result, failures = _run_cli_json_smoke(FakeCli, spec)
    capsys.readouterr()

    assert "chaseos gate validate --json expected action 'gate.validate', got 'gate.validation'" in failures
    assert "chaseos gate validate --json missing required result path result.valid" in failures


def test_cli_contract_ratchet_expected_nonzero_smoke_failures_name_exact_expectation(capsys) -> None:
    class FakeCli:
        @staticmethod
        def main(argv: list[str]) -> int:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "action": "core-export.readiness",
                        "result": {
                            "readiness_status": "blocked",
                            "blocking_issues": [],
                            "writes_performed": False,
                            "real_export_allowed_without_gate": False,
                        },
                        "errors": [],
                        "warnings": [],
                        "audit_id": None,
                    }
                )
            )
            return 0

    spec = {
        "name": "core-export.readiness",
        "argv": ["core-export", "readiness", "--json"],
        "expected_action": "core-export.readiness",
        "expected_exit_code": 1,
        "expected_ok": False,
        "required_result_paths": (
            ("result", "readiness_status"),
            ("result", "blocking_issues"),
        ),
    }

    result, failures = _run_cli_json_smoke(FakeCli, spec)
    capsys.readouterr()

    assert result["expectation_profile"] == "read_only_expected_nonzero_result_paths"
    assert result["expected_exit_code"] == 1
    assert result["expected_ok"] is False
    assert "chaseos core-export readiness --json exited 0; expected 1" in failures
    assert "chaseos core-export readiness --json returned ok=True; expected False" in failures


def test_cli_contract_ratchet_optional_live_readiness_accepts_unavailable(capsys) -> None:
    class FakeCli:
        @staticmethod
        def main(argv: list[str]) -> int:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "action": "health",
                        "result": {
                            "runtime_id": "openclaw",
                            "status": "unavailable",
                            "gateway_detected": False,
                            "candidate_urls": ["http://127.0.0.1:18789/"],
                            "candidate_ports": [18789],
                            "probes": [],
                            "writes_performed": False,
                            "authority_flags": {"read_only": True},
                        },
                        "errors": [{"code": "connection_error"}],
                        "warnings": [],
                        "audit_id": None,
                    }
                )
            )
            return 1

    spec = {
        "name": "health.openclaw.gateway",
        "argv": ["health", "openclaw", "--json"],
        "expected_action": "health",
        "optional_live_readiness": True,
        "allowed_statuses": {
            "healthy": {"exit_code": 0, "ok": True},
            "unavailable": {"exit_code": 1, "ok": False},
        },
        "required_result_paths": (
            ("result", "runtime_id"),
            ("result", "status"),
            ("result", "gateway_detected"),
        ),
    }

    result, failures = _run_cli_json_smoke(FakeCli, spec)
    capsys.readouterr()

    assert failures == []
    assert result["expectation_profile"] == "optional_live_readiness_result_paths"
    assert result["observed_status"] == "unavailable"
    assert result["expected_exit_code"] == 1
    assert result["expected_ok"] is False


def test_cli_contract_ratchet_optional_live_readiness_rejects_unknown_status(capsys) -> None:
    class FakeCli:
        @staticmethod
        def main(argv: list[str]) -> int:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "action": "health",
                        "result": {"status": "mystery"},
                        "errors": [],
                        "warnings": [],
                        "audit_id": None,
                    }
                )
            )
            return 1

    spec = {
        "name": "health.openclaw.gateway",
        "argv": ["health", "openclaw", "--json"],
        "expected_action": "health",
        "optional_live_readiness": True,
        "allowed_statuses": {
            "healthy": {"exit_code": 0, "ok": True},
            "unavailable": {"exit_code": 1, "ok": False},
        },
    }

    _result, failures = _run_cli_json_smoke(FakeCli, spec)
    capsys.readouterr()

    assert (
        "chaseos health openclaw --json observed readiness status 'mystery'; "
        "expected one of ['healthy', 'unavailable']"
    ) in failures


def test_cli_contract_ratchet_optional_readiness_accepts_blocked(capsys) -> None:
    class FakeCli:
        @staticmethod
        def main(argv: list[str]) -> int:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "action": "n8n.readiness",
                        "result": {
                            "status": "blocked",
                            "readiness_status": "blocked",
                            "blocked_reasons": ["N8N_BASE_URL is not set"],
                            "live_http_call": False,
                            "connection": {"blocked_reasons": ["N8N_BASE_URL is not set"]},
                            "registry": {"ok": True},
                            "forbidden": {"credential_values_logged": False},
                            "writes_performed": False,
                            "authority_flags": {"read_only": True},
                        },
                        "errors": [{"code": "blocked"}],
                        "warnings": [],
                        "audit_id": None,
                    }
                )
            )
            return 1

    spec = {
        "name": "n8n.readiness",
        "argv": ["n8n", "readiness", "--json"],
        "expected_action": "n8n.readiness",
        "optional_readiness": True,
        "allowed_statuses": {
            "ready": {"exit_code": 0, "ok": True},
            "blocked": {"exit_code": 1, "ok": False},
        },
        "required_result_paths": (
            ("result", "status"),
            ("result", "connection", "blocked_reasons"),
        ),
    }

    result, failures = _run_cli_json_smoke(FakeCli, spec)
    capsys.readouterr()

    assert failures == []
    assert result["expectation_profile"] == "optional_readiness_result_paths"
    assert result["observed_status"] == "blocked"
    assert result["expected_exit_code"] == 1
    assert result["expected_ok"] is False


def test_operator_handbook_coverage_failure_names_missing_command() -> None:
    contract = {
        "arg_sets": {},
        "commands": [
            {
                "path": ["gate", "validate"],
                "args": [],
                "family": "gate",
                "json_shape": "json",
                "side_effects": ["read:command-surface"],
            }
        ],
    }

    assert operator_handbook_coverage_failures(contract, "") == [
        "operator handbook missing command path: chaseos gate validate"
    ]


def test_setup_set_contract_discloses_setup_state_write_and_secret_boundary() -> None:
    command = _command_by_path(_load_contract(), ("setup", "set"))
    side_effects = set(command["side_effects"])

    assert "write:runtime/setup_state.json" in side_effects
    assert "metadata-only:credential-reference-targets" in side_effects
    assert "no secret value write" in side_effects
    assert "credential-boundary-enforced" in side_effects
    assert "read:command-surface" not in side_effects


def test_cli_contract_ratchet_siteops_candidate_smoke_uses_packaged_fixture_vault() -> None:
    siteops_smoke = next(
        spec for spec in SMOKE_COMMANDS if spec["name"] == "siteops.candidates.preflight"
    )

    assert SITEOPS_CANDIDATE_SMOKE_VAULT.exists()
    assert SITEOPS_CANDIDATE_SMOKE_VAULT == (
        ROOT / "runtime" / "cli" / "fixtures" / "browser_skill_candidates_vault"
    )
    assert "runtime/tests" not in SITEOPS_CANDIDATE_SMOKE_VAULT.as_posix()
    assert "candidate_browser_runtime_20260430_022443_example-com" not in siteops_smoke["argv"]
    assert "candidate_run_123" in siteops_smoke["argv"]
    assert "--vault-root" in siteops_smoke["argv"]
    assert str(SITEOPS_CANDIDATE_SMOKE_VAULT) in siteops_smoke["argv"]


def test_cli_contract_ratchet_siteops_fixture_is_packaged_data() -> None:
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]["runtime.cli"]

    assert (
        "fixtures/browser_skill_candidates_vault/03_INPUTS/"
        "Browser-Skill-Candidates/example-com/*.md"
    ) in package_data
    assert (
        "fixtures/browser_skill_candidates_vault/runtime/siteops/tenants/*.yaml"
        in package_data
    )


def test_cli_contract_ratchet_setup_state_fixture_is_packaged_data() -> None:
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]["runtime.cli"]
    setup_status_smoke = next(
        spec for spec in SMOKE_COMMANDS if spec["name"] == "setup.status"
    )

    assert SETUP_STATE_SMOKE_FIXTURE.exists()
    assert SETUP_STATE_SMOKE_FIXTURE == (
        ROOT / "runtime" / "cli" / "fixtures" / "setup_state" / "setup_state.json"
    )
    assert setup_status_smoke["setup_state_path"] == str(SETUP_STATE_SMOKE_FIXTURE)
    assert "runtime/setup_state.json" not in setup_status_smoke["setup_state_path"]
    assert "fixtures/setup_state/*.json" in package_data
    assert "operator_handbook_metadata.json" in package_data


def test_cli_contract_ratchet_intake_fixture_is_packaged_data() -> None:
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]["runtime.cli"]

    assert INTAKE_SMOKE_FIXTURE_VAULT.exists()
    assert INTAKE_SMOKE_FIXTURE_ITEM.exists()
    assert INTAKE_SMOKE_FIXTURE_VAULT == (
        ROOT / "runtime" / "cli" / "fixtures" / "intake_vault"
    )
    assert "runtime/tests" not in INTAKE_SMOKE_FIXTURE_VAULT.as_posix()
    assert "fixtures/intake_vault/README.md" in package_data
    assert "fixtures/intake_vault/.chaseos/*.json" in package_data
    assert "fixtures/intake_vault/03_INPUTS/00_QUARANTINE/Sources/*.md" in package_data
    assert "fixtures/intake_vault/03_INPUTS/00_QUARANTINE/Sources/*.json" in package_data
