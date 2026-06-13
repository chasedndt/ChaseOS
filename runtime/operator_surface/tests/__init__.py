"""Browser Operator Surface policy hardening tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.cli import main as cli
from runtime.operator_surface.browser.policy import build_browser_policy_report
from runtime.operator_surface.capabilities import SurfaceType
from runtime.operator_surface.contracts import OperatorScope, StepResult
from runtime.operator_surface.executor import OperatorExecutor
from runtime.operator_surface.scopes import approval_required_actions_for


class _PolicyOnlyAdapter:
    APPROVAL_REQUIRED_ACTIONS = frozenset({"cookie_consent_accept"})

    def __init__(self):
        self.executed = False

    def initialize(self, scope, session) -> None:
        self.scope = scope
        self.session = session

    def execute_step(self, step, emit_event):
        self.executed = True
        return StepResult(
            step_index=step.get("step_index", 0),
            success=True,
            action_type=step.get("action_type", ""),
            target=step.get("target", ""),
            output={},
        )

    def recover(self, failed_step, emit_event):  # pragma: no cover - should not run
        raise AssertionError("recovery should not run before approval")

    def teardown(self, outcome, emit_event) -> None:
        return None

    def build_audit_payload(self) -> dict:
        return {"adapter_id": "policy-test"}


def test_browser_policy_report_declares_current_boundary() -> None:
    report = build_browser_policy_report()

    assert report["surface"] == "browser"
    assert report["read_only"] is True
    assert report["mutates_vault"] is False
    assert "form_submit" in report["effective_approval_required"]
    assert "credential_field_fill" in report["effective_approval_required"]
    assert "file_download" in report["effective_approval_required"]
    assert "cookie_consent_accept" in report["effective_approval_required"]
    assert "click" in report["adapter_supported_not_promoted_cli"]
    assert "type" in report["adapter_supported_not_promoted_cli"]
    assert report["governance"]["canonical_knowledge_write"] is False


def test_approval_required_actions_include_adapter_specific_policy() -> None:
    required = approval_required_actions_for(SurfaceType.BROWSER, _PolicyOnlyAdapter)

    assert "form_submit" in required
    assert "file_download" in required
    assert "cookie_consent_accept" in required


def test_executor_pauses_for_adapter_specific_approval_action(tmp_path: Path) -> None:
    adapter = _PolicyOnlyAdapter()
    scope = OperatorScope(
        run_id="",
        surface=SurfaceType.BROWSER,
        target_uris=["https://example.com"],
        allowed_origins=["https://example.com"],
    )
    plan = [
        {
            "action_type": "cookie_consent_accept",
            "target": "https://example.com",
            "step_index": 0,
        }
    ]

    audit = OperatorExecutor(vault_root=tmp_path).run(
        workflow_id="policy_test",
        surface=SurfaceType.BROWSER,
        scope=scope,
        adapter=adapter,
        plan=plan,
        goal="policy test",
    )

    assert audit.outcome == "AWAIT_APPROVAL"
    assert audit.approvals_required == 1
    assert audit.events[-1].event_type.value == "await_approval"
    assert adapter.executed is False


def test_operate_browser_policy_parser_wiring() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(["operate", "browser", "policy"])

    assert args.func.__name__ == "cmd_operate_browser_policy"
    assert args.operate_surface == "browser"
    assert args.operate_browser_cmd == "policy"


def test_operate_browser_policy_json_envelope(capsys) -> None:
    rc = cli.main(["operate", "browser", "policy", "--json"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["action"] == "operate.browser.policy"
    assert payload["result"]["read_only"] is True
    assert "click" in payload["result"]["adapter_supported_not_promoted_cli"]
