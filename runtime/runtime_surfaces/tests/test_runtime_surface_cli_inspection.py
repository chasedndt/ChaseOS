from __future__ import annotations

import json
from pathlib import Path

import pytest

import runtime.cli.main as cli
from runtime.runtime_surfaces.inspection import (
    RuntimeSurfaceInspectionError,
    build_runtime_surface_capability_summary,
    build_runtime_surface_summary,
)


ROOT = Path(__file__).resolve().parents[3]


def test_runtime_surface_summary_is_sanitized_and_read_only() -> None:
    payload = build_runtime_surface_summary(ROOT)
    rendered = json.dumps(payload, sort_keys=True)

    assert payload["ok"] is True
    assert payload["surface_count"] >= 7
    assert payload["safety"]["read_only"] is True
    assert payload["safety"]["execution_performed"] is False
    assert payload["safety"]["route_proposal_performed"] is False
    assert payload["safety"]["ledger_written"] is False
    assert payload["safety"]["provider_calls_performed"] is False
    assert payload["safety"]["browser_control_performed"] is False
    assert "credential_policy" not in rendered
    assert "fallback_policy" not in rendered
    assert "implementation_refs" not in rendered
    assert "writeback_surfaces" not in rendered


def test_runtime_surface_capability_summary_can_filter_surface() -> None:
    payload = build_runtime_surface_capability_summary(ROOT, surface_id="agent.codex.bus")

    assert payload["ok"] is True
    assert payload["surface_filter"] == "agent.codex.bus"
    assert payload["capability_policy_record_count"] > 0
    assert {record["surface_id"] for record in payload["capabilities"]} == {"agent.codex.bus"}
    assert any(record["capability_id"] == "code.patch" for record in payload["capabilities"])
    assert payload["safety"]["ledger_written"] is False


def test_runtime_surface_inspection_fails_closed_for_unknown_surface() -> None:
    with pytest.raises(RuntimeSurfaceInspectionError):
        build_runtime_surface_summary(ROOT, surface_id="unknown.surface")

    with pytest.raises(RuntimeSurfaceInspectionError):
        build_runtime_surface_capability_summary(ROOT, surface_id="unknown.surface")


def test_cli_parser_accepts_runtime_surfaces_commands() -> None:
    parser = cli.build_parser()

    summary_args = parser.parse_args(["runtime", "surfaces", "summary", "--json"])
    assert summary_args.runtime_command == "surfaces"
    assert summary_args.runtime_subcommand == "summary"
    assert summary_args.output_json is True

    capability_args = parser.parse_args(
        ["runtime", "surfaces", "capabilities", "--surface", "agent.codex.bus", "--json"]
    )
    assert capability_args.runtime_command == "surfaces"
    assert capability_args.runtime_subcommand == "capabilities"
    assert capability_args.surface_id == "agent.codex.bus"
    assert capability_args.output_json is True


def test_cmd_runtime_surfaces_json_output_is_sanitized(capsys: pytest.CaptureFixture[str]) -> None:
    parser = cli.build_parser()
    args = parser.parse_args(
        ["runtime", "surfaces", "capabilities", "--surface", "agent.codex.bus", "--vault-root", str(ROOT), "--json"]
    )

    assert args.func(args) == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    rendered = json.dumps(payload, sort_keys=True)

    assert payload["ok"] is True
    assert payload["surface_filter"] == "agent.codex.bus"
    assert payload["safety"]["execution_performed"] is False
    assert payload["safety"]["ledger_written"] is False
    assert "credential_policy" not in rendered
    assert "fallback_policy" not in rendered
