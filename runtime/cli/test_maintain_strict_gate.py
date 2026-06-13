from __future__ import annotations

import argparse
import json
from types import SimpleNamespace

import runtime.cli.main as cli_main


def test_maintain_json_strict_gate_skips_downstream_stages(monkeypatch, capsys) -> None:
    called = {"daily": False, "provenance": False}

    hygiene_report = SimpleNamespace(
        files_scanned=5,
        issues=[],
        strict_gate_failed=True,
        strict_gate_review_count=2,
        review_artifacts={},
        files_fixed=0,
        wikilinks_fixed=0,
        nodes_wired=0,
        indexes_created=0,
    )

    def _hygiene_run(**kwargs):
        return hygiene_report

    def _daily_run(**kwargs):
        called["daily"] = True
        return SimpleNamespace(files_scanned=1)

    def _provenance_run(**kwargs):
        called["provenance"] = True
        return SimpleNamespace(files_scanned=1, links_added={})

    monkeypatch.setattr(cli_main.hygiene_mod, "run", _hygiene_run)
    monkeypatch.setattr(cli_main.hygiene_mod, "summarize_issues", lambda report: {"duplicate_candidate": 2})
    monkeypatch.setattr(cli_main.hygiene_mod, "summarize_node_categories", lambda report: {"agent_draft_doc": 2})
    monkeypatch.setattr(cli_main.hygiene_mod, "build_loose_node_review_queue", lambda report: [{}, {}])
    monkeypatch.setattr(cli_main.daily_hub_mod, "run", _daily_run)
    monkeypatch.setattr(cli_main.provenance_mod, "run", _provenance_run)

    rc = cli_main.cmd_maintain(
        argparse.Namespace(
            dry_run=True,
            output_json=True,
            strict_graph_review=True,
            write_graph_review_queue=False,
        )
    )

    assert rc == 2
    assert called == {"daily": False, "provenance": False}
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "blocked_review_required"
    assert payload["review_required"] is True
    assert payload["errors"] == ["blocked_review_required"]
    assert payload["stage_1_vault_hygiene"]["loose_node_review_count"] == 2
    assert payload["stage_2_daily_hub"]["skipped"] is True
    assert payload["stage_2_daily_hub"]["files_scanned"] == 0
    assert payload["stage_3_provenance"]["skipped"] is True
    assert payload["stage_3_provenance"]["files_scanned"] == 0
