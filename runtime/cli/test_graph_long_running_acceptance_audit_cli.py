"""CLI tests for the Studio Graph long-running acceptance audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[2]
if str(VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402
from runtime.studio.test_graph_long_running_acceptance_audit import (  # noqa: E402
    _seed_vault,
    _use_short_evidence_paths,
)


def test_graph_long_running_acceptance_audit_cli_reports_blocked_goal_without_mutation(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    _use_short_evidence_paths(monkeypatch)
    _seed_vault(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    exit_code = cli.main(
        [
            "studio",
            "graph-long-running-acceptance-audit",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.graph-long-running-acceptance-audit"
    assert result["surface"] == "studio_graph_long_running_acceptance_audit"
    assert result["summary"]["acceptance_audit_ready"] is True
    assert result["summary"]["objective_achieved"] is False
    assert result["summary"]["safe_to_call_update_goal_complete"] is False
    assert result["authority"]["repairs_current_pointer"] is False
    assert result["authority"]["approval_consumption_allowed"] is False
    assert result["authority"]["agent_bus_task_write_allowed"] is False
    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()) == before


def test_graph_long_running_acceptance_audit_cli_writes_bounded_report(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    _use_short_evidence_paths(monkeypatch)
    _seed_vault(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "graph-long-running-acceptance-audit",
            "--vault-root",
            str(tmp_path),
            "--write-report",
            "--report-slug",
            "test-cli-graph-acceptance-audit",
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert payload["ok"] is True
    assert result["report_write"]["written"] is True
    assert (tmp_path / result["report_write"]["json_path"]).is_file()
    assert (tmp_path / result["report_write"]["markdown_path"]).is_file()
    assert result["authority"]["writes_graph_store"] is False
    assert result["authority"]["canonical_mutation_allowed"] is False


def test_graph_goal_completion_audit_cli_blocks_without_mutation(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    _use_short_evidence_paths(monkeypatch)
    _seed_vault(tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    exit_code = cli.main(
        [
            "studio",
            "graph-goal-completion-audit",
            "--vault-root",
            str(tmp_path),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["action"] == "studio.graph-goal-completion-audit"
    assert result["surface"] == "studio_graph_goal_completion_audit"
    assert result["summary"]["can_call_update_goal_complete"] is False
    assert "live_current_pointer_repaired" in result["blocked_reasons"]
    assert result["authority"]["calls_update_goal"] is False
    assert result["authority"]["repairs_current_pointer"] is False
    assert result["authority"]["approval_execution_allowed"] is False
    assert result["authority"]["canonical_mutation_allowed"] is False
    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()) == before
