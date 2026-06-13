"""CLI-level tests for promoted Gate surface and run-command coordination enforcement."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402


def test_gate_check_coordination_blocks_chat_path() -> None:
    exit_code = cli.main(
        [
            "gate",
            "check-coordination",
            "hermes",
            "--coordination-sensitive",
            "--via",
            "chat",
            "--target-runtime",
            "OpenClaw",
        ]
    )

    assert exit_code == 1


def test_run_coordination_sensitive_workflow_requires_adapter(capsys) -> None:
    exit_code = cli.main(
        [
            "run",
            "hermes_review_execute",
            "--coordination-via",
            "runtime/agent_bus/",
            "--vault-root",
            str(_VAULT_ROOT),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "requires --adapter" in captured.err


def test_run_coordination_sensitive_workflow_requires_bus_path(capsys) -> None:
    exit_code = cli.main(
        [
            "run",
            "hermes_review_execute",
            "--adapter",
            "hermes",
            "--vault-root",
            str(_VAULT_ROOT),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "runtime/agent_bus/" in captured.err


def test_run_coordination_sensitive_workflow_enforces_manifest_adapter_and_calls_run_workflow(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_workflow(workflow_id, *, inputs, vault_root, dry_run=False):
        captured["workflow_id"] = workflow_id
        captured["inputs"] = inputs
        captured["vault_root"] = vault_root
        captured["dry_run"] = dry_run
        return SimpleNamespace(
            workflow_id=workflow_id,
            status="dry_run_ok",
            audit_id="audit-123",
            stage_reached="dry_run_exit",
            outputs={"dry_run": True},
            escalation_reason=None,
            error=None,
        )

    monkeypatch.setattr(cli, "run_workflow", fake_run_workflow)

    exit_code = cli.main(
        [
            "run",
            "hermes_review_execute",
            "--adapter",
            "hermes",
            "--coordination-via",
            "runtime/agent_bus/",
            "--dry-run",
            "--vault-root",
            str(_VAULT_ROOT),
        ]
    )

    assert exit_code == 0
    assert captured["workflow_id"] == "hermes_review_execute"
    assert captured["vault_root"] == _VAULT_ROOT
    assert captured["dry_run"] is True
    assert captured["inputs"] == {}
