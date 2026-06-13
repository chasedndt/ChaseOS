from __future__ import annotations

import json
from pathlib import Path

import pytest

import runtime.cli.main as cli
from runtime.runtime_surfaces.review_contract import build_route_review_contract


ROOT = Path(__file__).resolve().parents[3]


def test_route_review_contract_summarizes_all_capabilities_without_execution() -> None:
    payload = build_route_review_contract(ROOT)
    rendered = json.dumps(payload, sort_keys=True)

    assert payload["ok"] is True
    assert payload["contract"] == "runtime_surface_route_review"
    assert payload["requested_capability"] is None
    assert payload["review_row_count"] >= 50
    assert payload["route_preview"] is None
    assert payload["operator_review"]["review_surface_ready"] is True
    assert payload["operator_review"]["can_grant_approval"] is False
    assert payload["operator_review"]["can_execute_route"] is False
    assert payload["operator_review"]["can_write_ledger"] is False
    assert payload["safety"]["execution_performed"] is False
    assert payload["safety"]["runtime_dispatch_performed"] is False
    assert payload["safety"]["ledger_written"] is False
    assert payload["safety"]["approval_granted"] is False
    assert payload["safety"]["provider_calls_performed"] is False
    assert payload["safety"]["browser_control_performed"] is False
    assert "credential_policy" not in rendered
    assert "fallback_policy" not in rendered
    assert "implementation_refs" not in rendered


def test_route_review_contract_previews_approval_required_capability() -> None:
    payload = build_route_review_contract(ROOT, capability="browser.click")
    preview = payload["route_preview"]

    assert payload["requested_capability"] == "browser.click"
    assert payload["review_row_count"] == 1
    assert preview["decision"] == "approval_required"
    assert preview["selected_surface"] == "browser.operator.playwright"
    assert preview["execution_performed"] is False
    assert preview["ledger_written"] is False
    assert payload["operator_review"]["next_required_authority"] == "approval_gate_then_runtime/operator_surface"


def test_route_review_contract_surface_filter_denies_mismatch_without_fallback() -> None:
    payload = build_route_review_contract(ROOT, capability="browser.click", surface_id="agent.codex.bus")
    preview = payload["route_preview"]

    assert payload["requested_surface_id"] == "agent.codex.bus"
    assert payload["review_row_count"] == 0
    assert preview["decision"] == "deny_unknown"
    assert preview["selected_surface"] is None
    assert preview["execution_performed"] is False
    assert preview["ledger_written"] is False


def test_cli_parser_accepts_runtime_surfaces_route_review() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(
        ["runtime", "surfaces", "route-review", "--capability", "browser.click", "--surface", "browser.operator.playwright", "--json"]
    )

    assert args.runtime_command == "surfaces"
    assert args.runtime_subcommand == "route-review"
    assert args.capability_id == "browser.click"
    assert args.surface_id == "browser.operator.playwright"
    assert args.output_json is True


def test_cmd_runtime_surfaces_route_review_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "runtime",
            "surfaces",
            "route-review",
            "--capability",
            "browser.click",
            "--vault-root",
            str(ROOT),
            "--json",
        ]
    )

    assert args.func(args) == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["ok"] is True
    assert payload["requested_capability"] == "browser.click"
    assert payload["route_preview"]["decision"] == "approval_required"
    assert payload["route_preview"]["execution_performed"] is False
    assert payload["route_preview"]["ledger_written"] is False
    assert payload["safety"]["raw_manifest_exposed"] is False
