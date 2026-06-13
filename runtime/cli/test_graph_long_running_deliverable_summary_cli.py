"""CLI tests for the Studio Graph long-running deliverable summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[2]
if str(VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(VAULT_ROOT))

import runtime.cli.main as cli  # noqa: E402
from runtime.studio.test_graph_goal_completion_audit import (  # noqa: E402
    _approval,
    _seed_operator_packet,
    _seed_rehearsal_report,
)
from runtime.studio.test_graph_long_running_acceptance_audit import (  # noqa: E402
    _seed_runtime_overlay_evidence,
    _seed_vault,
    _use_short_evidence_paths,
)


def _files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def test_graph_long_running_deliverable_summary_cli_outputs_17_sections_without_mutation(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    _use_short_evidence_paths(monkeypatch)
    _seed_vault(tmp_path)
    _seed_runtime_overlay_evidence(tmp_path)
    _seed_rehearsal_report(tmp_path)
    _seed_operator_packet(tmp_path)
    approval_packet_id, approval_digest = _approval(tmp_path)
    before = _files(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "graph-long-running-deliverable-summary",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval_packet_id,
            "--approval-digest",
            approval_digest,
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    result = payload["result"]
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["action"] == "studio.graph-long-running-deliverable-summary"
    assert result["surface"] == "studio_graph_long_running_deliverable_summary"
    assert result["summary"]["deliverable_count"] == 17
    assert result["summary"]["safe_to_call_update_goal_complete"] is False
    assert result["authority"]["calls_update_goal"] is False
    assert result["authority"]["repairs_current_pointer"] is False
    assert result["authority"]["canonical_mutation_allowed"] is False
    assert _files(tmp_path) == before


def test_graph_long_running_deliverable_summary_cli_writes_bounded_report(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    _use_short_evidence_paths(monkeypatch)
    _seed_vault(tmp_path)
    _seed_runtime_overlay_evidence(tmp_path)
    _seed_rehearsal_report(tmp_path)
    approval_packet_id, approval_digest = _approval(tmp_path)

    exit_code = cli.main(
        [
            "studio",
            "graph-long-running-deliverable-summary",
            "--vault-root",
            str(tmp_path),
            "--approval-packet-id",
            approval_packet_id,
            "--approval-digest",
            approval_digest,
            "--write-report",
            "--report-slug",
            "test-cli-deliverable-summary",
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
    assert result["report_write"]["write_scope"] == "bounded_graph_long_running_deliverable_summary_report_only"
