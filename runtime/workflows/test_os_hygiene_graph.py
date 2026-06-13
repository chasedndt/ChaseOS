from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from runtime.cli.vault_hygiene import HygieneReport
from runtime.workflows.os_hygiene_graph import run_os_hygiene_graph


def _report() -> HygieneReport:
    report = HygieneReport()
    report.files_scanned = 12
    return report


def test_os_hygiene_graph_blocks_scheduled_mutation_on_review_debt(monkeypatch, tmp_path: Path) -> None:
    import runtime.cli.daily_hub_linker as daily_hub_mod
    import runtime.cli.provenance_linker as provenance_mod
    import runtime.cli.vault_hygiene as hygiene_mod

    called = {"apply_fixes": False, "daily": False, "provenance": False}

    monkeypatch.setattr(hygiene_mod, "scan_vault", lambda vault_root: _report())
    monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda report, vault_root: [{"file": "loose.md"}])
    monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda report: {"duplicate_candidate": 1})
    monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda report: {"core_export_artifact": 1})

    def _apply_fixes(*args, **kwargs):
        called["apply_fixes"] = True

    def _daily_run(*args, **kwargs):
        called["daily"] = True
        return SimpleNamespace()

    def _provenance_run(*args, **kwargs):
        called["provenance"] = True
        return SimpleNamespace()

    monkeypatch.setattr(hygiene_mod, "apply_fixes", _apply_fixes)
    monkeypatch.setattr(daily_hub_mod, "run", _daily_run)
    monkeypatch.setattr(provenance_mod, "run", _provenance_run)

    result = run_os_hygiene_graph({}, tmp_path)

    assert result["status"] == "blocked_review_required"
    assert result["stage_1_vault_hygiene"]["strict_gate_failed"] is True
    assert result["stage_1_vault_hygiene"]["loose_node_review_count"] == 1
    assert result["stage_2_daily_hub"]["skipped"] is True
    assert result["stage_3_provenance"]["skipped"] is True
    assert "blocked_review_required" in result["writebacks"][0]["content"]
    assert called == {"apply_fixes": False, "daily": False, "provenance": False}


def test_os_hygiene_graph_allow_review_debt_override_runs_stages(monkeypatch, tmp_path: Path) -> None:
    import runtime.cli.daily_hub_linker as daily_hub_mod
    import runtime.cli.provenance_linker as provenance_mod
    import runtime.cli.vault_hygiene as hygiene_mod

    called = {"apply_fixes": False, "daily": False, "provenance": False}

    monkeypatch.setattr(hygiene_mod, "scan_vault", lambda vault_root: _report())
    monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda report, vault_root: [{"file": "loose.md"}])
    monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda report: {"duplicate_candidate": 1})
    monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda report: {"core_export_artifact": 1})
    monkeypatch.setattr(hygiene_mod, "render_report", lambda report, vault_root: "# report\n")

    def _apply_fixes(*args, **kwargs):
        called["apply_fixes"] = True

    def _daily_run(*args, **kwargs):
        called["daily"] = True
        return SimpleNamespace(
            files_scanned=2,
            dates_found=1,
            notes_created=0,
            notes_updated=0,
            backlinks_added=0,
            index_updated=False,
        )

    def _provenance_run(*args, **kwargs):
        called["provenance"] = True
        return SimpleNamespace(files_scanned=3, files_modified=0, links_added={})

    monkeypatch.setattr(hygiene_mod, "apply_fixes", _apply_fixes)
    monkeypatch.setattr(daily_hub_mod, "run", _daily_run)
    monkeypatch.setattr(provenance_mod, "run", _provenance_run)

    result = run_os_hygiene_graph({"allow_review_debt": True}, tmp_path)

    assert result["stage_1_vault_hygiene"]["strict_gate_failed"] is False
    assert result["stage_1_vault_hygiene"]["loose_node_review_count"] == 1
    assert result["stage_2_daily_hub"]["files_scanned"] == 2
    assert result["stage_3_provenance"]["files_scanned"] == 3
    assert "blocked_review_required" not in result["writebacks"][0]["content"]
    assert called == {"apply_fixes": True, "daily": True, "provenance": True}


def test_os_hygiene_graph_passes_ambiguous_review_inputs(monkeypatch, tmp_path: Path) -> None:
    import runtime.cli.daily_hub_linker as daily_hub_mod
    import runtime.cli.provenance_linker as provenance_mod
    import runtime.cli.vault_hygiene as hygiene_mod

    captured: dict[str, object] = {}

    def _scan(vault_root: Path, **kwargs):
        captured.update(kwargs)
        return _report()

    monkeypatch.setattr(hygiene_mod, "scan_vault", _scan)
    monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda report, vault_root: [])
    monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda report: {})
    monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda report: {})
    monkeypatch.setattr(hygiene_mod, "render_report", lambda report, vault_root: "# report\n")
    monkeypatch.setattr(hygiene_mod, "apply_fixes", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        daily_hub_mod,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            files_scanned=0,
            dates_found=0,
            notes_created=0,
            notes_updated=0,
            backlinks_added=0,
            index_updated=False,
        ),
    )
    monkeypatch.setattr(
        provenance_mod,
        "run",
        lambda *args, **kwargs: SimpleNamespace(files_scanned=0, files_modified=0, links_added={}),
    )

    result = run_os_hygiene_graph(
        {
            "review_ambiguous_links": True,
            "ambiguous_review_limit": 17,
            "review_unresolved_links": True,
            "unresolved_link_limit": 19,
        },
        tmp_path,
    )

    assert result["stage_1_vault_hygiene"]["ambiguous_link_review_requested"] is True
    assert result["stage_1_vault_hygiene"]["ambiguous_review_limit"] == 17
    assert captured["ambiguous_link_review_limit"] == 17
    assert captured["unresolved_link_review_limit"] == 19


def test_os_hygiene_graph_can_write_ambiguous_link_proposal(monkeypatch, tmp_path: Path) -> None:
    import runtime.cli.daily_hub_linker as daily_hub_mod
    import runtime.cli.provenance_linker as provenance_mod
    import runtime.cli.vault_hygiene as hygiene_mod

    captured: dict[str, object] = {}

    def _scan(vault_root: Path, **kwargs):
        captured.update(kwargs)
        return _report()

    def _proposal(report, vault_root, **kwargs):
        captured["proposal_kwargs"] = kwargs
        return {
            "proposal_path": kwargs["output_path"],
            "proposal_markdown_path": kwargs["output_path"].replace(".json", ".md"),
            "proposal_count": 7,
            "proposal_kind": "ambiguous_link_target_review",
            "operator_approved": False,
        }

    monkeypatch.setattr(hygiene_mod, "scan_vault", _scan)
    monkeypatch.setattr(hygiene_mod, "_pending_ambiguous_link_proposal_keys", lambda *args, **kwargs: {("A.md", "Target")})
    monkeypatch.setattr(hygiene_mod, "propose_ambiguous_link_decisions", _proposal)
    monkeypatch.setattr(hygiene_mod, "build_loose_node_review_queue", lambda report, vault_root: [])
    monkeypatch.setattr(hygiene_mod, "summarize_issues", lambda report: {})
    monkeypatch.setattr(hygiene_mod, "summarize_node_categories", lambda report: {})
    monkeypatch.setattr(hygiene_mod, "render_report", lambda report, vault_root: "# report\n")
    monkeypatch.setattr(hygiene_mod, "apply_fixes", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        daily_hub_mod,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            files_scanned=0,
            dates_found=0,
            notes_created=0,
            notes_updated=0,
            backlinks_added=0,
            index_updated=False,
        ),
    )
    monkeypatch.setattr(
        provenance_mod,
        "run",
        lambda *args, **kwargs: SimpleNamespace(files_scanned=0, files_modified=0, links_added={}),
    )

    result = run_os_hygiene_graph(
        {
            "dry_run": True,
            "propose_ambiguous_link_decisions": True,
            "ambiguous_proposal_path": "07_LOGS/Graph-Reports/a.json",
            "ambiguous_proposal_max_items": 5,
            "ambiguous_review_limit": 1,
        },
        tmp_path,
    )

    assert captured["ambiguous_link_review_limit"] == 6
    assert captured["proposal_kwargs"] == {
        "output_path": "07_LOGS/Graph-Reports/a.json",
        "max_items": 5,
        "include_pending": False,
    }
    assert result["stage_1_vault_hygiene"]["ambiguous_link_proposal_requested"] is True
    assert result["stage_1_vault_hygiene"]["ambiguous_link_proposal"]["proposal_count"] == 7
