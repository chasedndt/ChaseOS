from pathlib import Path

import json

import runtime.cli.vault_hygiene as vault_hygiene

from runtime.cli.vault_hygiene import (
    apply_fixes,
    apply_review_decisions,
    build_loose_node_review_queue,
    build_review_summary,
    infer_node_category,
    main,
    propose_ambiguous_link_decisions,
    propose_unresolved_link_decisions,
    propose_review_decisions,
    render_decision_apply_result,
    render_json_report,
    render_review_summary,
    scan_vault,
    validate_ambiguous_link_decisions,
    validate_unresolved_link_decisions,
    write_ambiguous_approval_preview_copy,
    write_approval_preview_copy,
    write_unresolved_approval_preview_copy,
    write_loose_node_review_artifacts,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_core_export_canonical_duplicate_is_review_not_autowire(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Agent-Control-Plane]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Agent-Control-Plane.md", "# Agent Control Plane\n")
    _write(tmp_path / "core_export" / "templates" / "Agent-Control-Plane.core.md", "# Agent Control Plane\n")

    report = scan_vault(tmp_path)

    matches = [
        issue for issue in report.issues
        if issue.file_path == "core_export/templates/Agent-Control-Plane.core.md"
    ]
    assert matches
    assert matches[0].category == "duplicate_candidate"
    assert matches[0].severity == "review"
    assert matches[0].index_path == "06_AGENTS/Agent-Control-Plane.md"
    assert matches[0].canonical_path == "06_AGENTS/Agent-Control-Plane.md"
    assert matches[0].node_category == "core_export_artifact"
    assert matches[0].action == "review_duplicate_then_archive_or_delete"


def test_indexed_log_artifact_wires_to_local_index_not_vault_map(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "07_LOGS" / "Studio-Graph-Views" / "Studio-Graph-Views-Index.md", "# Studio Graph Views Index\n")
    _write(tmp_path / "07_LOGS" / "Studio-Graph-Views" / "2026-05-04-static-qa.md", "# Static QA\n")

    report = scan_vault(tmp_path)

    matches = [
        issue for issue in report.issues
        if issue.file_path == "07_LOGS/Studio-Graph-Views/2026-05-04-static-qa.md"
    ]
    assert matches
    assert matches[0].category == "loose_node"
    assert matches[0].severity == "auto_fix"
    assert matches[0].index_path == "07_LOGS/Studio-Graph-Views/Studio-Graph-Views-Index.md"
    assert matches[0].node_category == "studio_graph_evidence"


def test_indexed_folder_scan_accepts_path_qualified_index_links(tmp_path: Path) -> None:
    rel_path = "07_LOGS/Studio-Graph-Views/2026-05-04-static-qa.md"
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(
        tmp_path / "07_LOGS" / "Studio-Graph-Views" / "Studio-Graph-Views-Index.md",
        "# Studio Graph Views Index\n\n"
        f"[[{rel_path[:-3]}|2026-05-04-static-qa]]\n",
    )
    _write(tmp_path / rel_path, "# Static QA\n")

    report = scan_vault(tmp_path)

    assert not [
        issue for issue in report.issues
        if issue.category == "loose_node" and issue.file_path == rel_path
    ]


def test_semantic_hub_gap_fix_appends_path_qualified_governance_links(tmp_path: Path) -> None:
    target_rel = "06_AGENTS/Agent-Bus-Backend-Architecture.md"
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(
        tmp_path / "06_AGENTS" / "Vault-Map.md",
        "# Vault Map\n"
        f"[[{target_rel[:-3]}|Agent Bus Backend Architecture]]\n",
    )
    _write(tmp_path / "06_AGENTS" / "Agent-Control-Plane.md", "# Agent Control Plane\n")
    _write(tmp_path / target_rel, "# Agent Bus Backend Architecture\n")

    report = scan_vault(tmp_path, semantic_hub_fix_limit=1)

    matches = [
        issue for issue in report.issues
        if issue.category == "semantic_hub_gap" and issue.file_path == target_rel
    ]
    assert matches
    assert matches[0].severity == "auto_fix"
    assert matches[0].action == "append_governance_links"

    apply_fixes(tmp_path, report)

    content = (tmp_path / target_rel).read_text(encoding="utf-8")
    assert "[[06_AGENTS/Agent-Control-Plane|Agent-Control-Plane]]" in content
    assert "[[06_AGENTS/Vault-Map|Vault-Map]]" in content
    next_report = scan_vault(tmp_path, semantic_hub_fix_limit=10)
    assert not [
        issue for issue in next_report.issues
        if issue.category == "semantic_hub_gap" and issue.file_path == target_rel
    ]


def test_keep_excluded_runtime_readme_is_not_counted_as_semantic_hub_gap(tmp_path: Path) -> None:
    rel = "runtime/siteops/README.md"
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / vault_hygiene.KEEP_EXCLUDED_INDEX_REL, f"# Keep Excluded\n\n[[{rel[:-3]}|README]]\n")
    _write(tmp_path / rel, "# SiteOps README\n")
    digest = vault_hygiene.file_sha256(tmp_path / rel)
    _write(
        tmp_path / vault_hygiene.DECISION_REGISTRY_REL,
        json.dumps({
            "version": 1,
            "updated": "2026-05-06T00:00:00+00:00",
            "decisions": {
                rel: {
                    "decision": "keep_excluded",
                    "file_sha256": digest,
                    "approved_by": "test",
                }
            },
        }),
    )

    report = scan_vault(tmp_path, semantic_hub_fix_limit=10)

    assert not [
        issue for issue in report.issues
        if issue.category == "semantic_hub_gap" and issue.file_path == rel
    ]
    assert report.visible_graph_audit["semantic_hub_gap_count"] == 0


def test_ambiguous_link_fix_path_qualifies_known_canonical_target(tmp_path: Path) -> None:
    source_rel = "00_HOME/Assistant-Contract.md"
    archive_rel = "99_ARCHIVE/Vault-Hygiene-Review/Replaced-Duplicates/2026-05-05/Vault-Map.md"
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / archive_rel, "# Old Vault Map\n")
    _write(tmp_path / source_rel, "# Assistant Contract\n\nSee [[Vault-Map]].\n")

    report = scan_vault(tmp_path, ambiguous_link_fix_limit=1)

    matches = [
        issue for issue in report.issues
        if issue.category == "ambiguous_link_target" and issue.file_path == source_rel
    ]
    assert matches
    assert matches[0].severity == "auto_fix"
    assert matches[0].canonical_path == "06_AGENTS/Vault-Map.md"

    apply_fixes(tmp_path, report)

    content = (tmp_path / source_rel).read_text(encoding="utf-8")
    assert "[[06_AGENTS/Vault-Map|Vault-Map]]" in content
    next_report = scan_vault(tmp_path, ambiguous_link_fix_limit=10)
    assert not [
        issue for issue in next_report.issues
        if issue.category == "ambiguous_link_target" and issue.file_path == source_rel
    ]


def test_ambiguous_link_fix_path_qualifies_agent_runtime_canonical_target(tmp_path: Path) -> None:
    source_rel = "00_HOME/Runtime-Bridge.md"
    archive_rel = "core_export/reports/latest/previews/06_AGENTS/Runtime-InterAgent-Coordination-Bus.md"
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(
        tmp_path / "06_AGENTS" / "Runtime-InterAgent-Coordination-Bus.md",
        "# Runtime InterAgent Coordination Bus\n",
    )
    _write(tmp_path / archive_rel, "# Old Runtime InterAgent Coordination Bus\n")
    _write(tmp_path / source_rel, "# Runtime Bridge\n\nSee [[Runtime-InterAgent-Coordination-Bus]].\n")

    report = scan_vault(tmp_path, ambiguous_link_fix_limit=1)

    matches = [
        issue for issue in report.issues
        if issue.category == "ambiguous_link_target" and issue.file_path == source_rel
    ]
    assert matches
    assert matches[0].severity == "auto_fix"
    assert matches[0].canonical_path == "06_AGENTS/Runtime-InterAgent-Coordination-Bus.md"

    apply_fixes(tmp_path, report)

    content = (tmp_path / source_rel).read_text(encoding="utf-8")
    assert (
        "[[06_AGENTS/Runtime-InterAgent-Coordination-Bus|Runtime-InterAgent-Coordination-Bus]]"
        in content
    )


def test_ambiguous_link_fix_infers_single_non_export_canonical_target(tmp_path: Path) -> None:
    source_rel = "06_AGENTS/Draft.md"
    archive_rel = "core_export/reports/latest/previews/04_SOPS/Research-Ingest-SOP.md"
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "04_SOPS" / "Research-Ingest-SOP.md", "# Research Ingest SOP\n")
    _write(tmp_path / archive_rel, "# Export Preview\n")
    _write(tmp_path / source_rel, "# Draft\n\nSee [[Research-Ingest-SOP]].\n")

    report = scan_vault(tmp_path, ambiguous_link_fix_limit=1)

    matches = [
        issue for issue in report.issues
        if issue.category == "ambiguous_link_target" and issue.file_path == source_rel
    ]
    assert matches
    assert matches[0].canonical_path == "04_SOPS/Research-Ingest-SOP.md"

    apply_fixes(tmp_path, report)

    content = (tmp_path / source_rel).read_text(encoding="utf-8")
    assert "[[04_SOPS/Research-Ingest-SOP|Research-Ingest-SOP]]" in content


def test_ambiguous_link_fix_path_qualifies_template_canonical_target(tmp_path: Path) -> None:
    source_rel = "06_AGENTS/Draft.md"
    archive_rel = (
        "99_ARCHIVE/Vault-Hygiene-Review/Noncanonical-Artifacts/2026-05-05/"
        "core_export/reports/latest/previews/05_TEMPLATES/Source-Note-Template.md"
    )
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "05_TEMPLATES" / "Source-Note-Template.md", "# Source Note Template\n")
    _write(tmp_path / archive_rel, "# Export Preview\n")
    _write(tmp_path / source_rel, "# Draft\n\nSee [[Source-Note-Template]].\n")

    report = scan_vault(tmp_path, ambiguous_link_fix_limit=1)

    matches = [
        issue for issue in report.issues
        if issue.category == "ambiguous_link_target" and issue.file_path == source_rel
    ]
    assert matches
    assert matches[0].canonical_path == "05_TEMPLATES/Source-Note-Template.md"

    apply_fixes(tmp_path, report)

    content = (tmp_path / source_rel).read_text(encoding="utf-8")
    assert "[[05_TEMPLATES/Source-Note-Template|Source-Note-Template]]" in content


def test_ambiguous_link_fix_does_not_guess_when_multiple_primary_candidates(tmp_path: Path) -> None:
    source_rel = "06_AGENTS/Draft.md"
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "runtime" / "hermes" / "agents.md", "# Hermes Agents\n")
    _write(tmp_path / "runtime" / "openclaw" / "agents.md", "# OpenClaw Agents\n")
    _write(tmp_path / source_rel, "# Draft\n\nSee [[agents]].\n")

    report = scan_vault(tmp_path, ambiguous_link_fix_limit=1)

    assert not [
        issue for issue in report.issues
        if issue.category == "ambiguous_link_target" and issue.file_path == source_rel
    ]


def test_ambiguous_link_review_surfaces_unsafe_duplicate_without_loose_queue(tmp_path: Path) -> None:
    source_rel = "06_AGENTS/OpenClaw-Runtime-Profile.md"
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(
        tmp_path / "06_AGENTS" / "Vault-Map.md",
        "# Vault Map\n\n[[runtime/hermes/coordination_bridge|Hermes Bridge]]\n[[runtime/openclaw/coordination_bridge|OpenClaw Bridge]]\n",
    )
    _write(tmp_path / "runtime" / "hermes" / "coordination_bridge.md", "# Hermes Bridge\n\nRuntime bridge notes with [[06_AGENTS/Vault-Map|Vault Map]].\n")
    _write(tmp_path / "runtime" / "openclaw" / "coordination_bridge.md", "# OpenClaw Bridge\n\nRuntime bridge notes with [[06_AGENTS/Vault-Map|Vault Map]].\n")
    _write(tmp_path / source_rel, "# OpenClaw Runtime Profile\n\nSee [[coordination_bridge]].\n")

    report = scan_vault(tmp_path, ambiguous_link_review_limit=1)

    matches = [
        issue for issue in report.issues
        if issue.category == "ambiguous_link_target_review" and issue.file_path == source_rel
    ]
    assert len(matches) == 1
    assert matches[0].severity == "review"
    assert matches[0].action == "review_duplicate_stem_create_alias_or_path_qualify"
    assert "target=coordination_bridge" in matches[0].evidence
    assert any("candidate_count=2" == item for item in matches[0].evidence)
    assert not build_loose_node_review_queue(report, tmp_path)


def test_unresolved_link_review_surfaces_bounded_review_issue(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Draft.md", "# Draft\n\nSee [[Missing-Node]].\n")

    report = scan_vault(tmp_path, unresolved_link_review_limit=1)

    matches = [
        issue for issue in report.issues
        if issue.category == "unresolved_link_target"
    ]
    assert len(matches) == 1
    assert matches[0].severity == "review"
    assert matches[0].action == "review_target_create_rename_or_unlink"
    assert "target=Missing-Node" in matches[0].evidence
    assert not build_loose_node_review_queue(report, tmp_path)


def test_unresolved_link_proposal_writes_review_only_json_and_markdown(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Draft.md", "# Draft\n\nSee [[Missing-Node]].\n")

    report = scan_vault(tmp_path, unresolved_link_review_limit=5)
    proposal = propose_unresolved_link_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/unresolved-proposal.json",
        max_items=5,
    )

    payload = json.loads((tmp_path / proposal["proposal_path"]).read_text(encoding="utf-8"))
    markdown = (tmp_path / proposal["proposal_markdown_path"]).read_text(encoding="utf-8")
    graph_index = (tmp_path / "07_LOGS" / "Graph-Reports" / "Graph-Reports-Index.md").read_text(encoding="utf-8")

    assert proposal["proposal_count"] == 1
    assert payload["proposal_kind"] == "unresolved_link_target_review"
    assert payload["operator_approved"] is False
    assert payload["proposal_only"] is True
    assert payload["decisions"][0]["file"] == "06_AGENTS/Draft.md"
    assert payload["decisions"][0]["link_target"] == "Missing-Node"
    assert payload["decisions"][0]["decision"] == "review_target_create_rename_or_unlink"
    assert "create_target_node" in payload["decisions"][0]["allowed_decisions"]
    assert "Missing-Node" in markdown
    assert "[[unresolved-proposal]]" in graph_index


def test_unresolved_link_proposal_skips_rows_pending_in_older_unapproved_proposals(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Draft-A.md", "# Draft A\n\nSee [[Missing-A]].\n")
    _write(tmp_path / "06_AGENTS" / "Draft-B.md", "# Draft B\n\nSee [[Missing-B]].\n")

    first_report = scan_vault(tmp_path, unresolved_link_review_limit=2)
    first = propose_unresolved_link_decisions(
        first_report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/unresolved-proposal-1.json",
        max_items=1,
    )
    second_report = scan_vault(tmp_path, unresolved_link_review_limit=2)
    second = propose_unresolved_link_decisions(
        second_report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/unresolved-proposal-2.json",
        max_items=1,
    )

    first_payload = json.loads((tmp_path / first["proposal_path"]).read_text(encoding="utf-8"))
    second_payload = json.loads((tmp_path / second["proposal_path"]).read_text(encoding="utf-8"))

    assert first_payload["decisions"][0]["link_target"] == "Missing-A"
    assert second_payload["decisions"][0]["link_target"] == "Missing-B"
    assert second_payload["selection"]["pending_unresolved_rows_skipped"] == 1


def test_unresolved_link_proposal_cli_expands_scan_for_pending_rows(tmp_path: Path, monkeypatch, capsys) -> None:
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Draft-A.md", "# Draft A\n\nSee [[Missing-A]].\n")
    _write(tmp_path / "06_AGENTS" / "Draft-B.md", "# Draft B\n\nSee [[Missing-B]].\n")

    first_report = scan_vault(tmp_path, unresolved_link_review_limit=1)
    propose_unresolved_link_decisions(
        first_report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/unresolved-proposal-1.json",
        max_items=1,
    )

    monkeypatch.setattr(vault_hygiene, "VAULT_ROOT", tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "vault_hygiene",
            "--propose-unresolved-link-decisions",
            "--unresolved-proposal-max-items",
            "1",
            "--unresolved-proposal-path",
            "07_LOGS/Graph-Reports/unresolved-proposal-2.json",
            "--json",
        ],
    )

    main()

    output = capsys.readouterr().out
    payload = json.loads(output)
    proposal_payload = json.loads((tmp_path / payload["proposal_path"]).read_text(encoding="utf-8"))

    assert payload["proposal_count"] == 1
    assert payload["pending_unresolved_rows_skipped"] == 1
    assert proposal_payload["decisions"][0]["link_target"] == "Missing-B"


def test_validate_unresolved_link_decisions_accepts_approved_create_preview(tmp_path: Path) -> None:
    source_rel = "06_AGENTS/Draft.md"
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / source_rel, "# Draft\n\nSee [[Missing-Node]].\n")

    proposal = propose_unresolved_link_decisions(
        scan_vault(tmp_path, unresolved_link_review_limit=5),
        tmp_path,
        output_path="07_LOGS/Graph-Reports/unresolved-proposal.json",
        max_items=5,
    )
    proposal_path = tmp_path / proposal["proposal_path"]
    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    payload["operator_approved"] = True
    payload["approved_by"] = "operator"
    payload["decisions"][0]["decision"] = "create_target_node"
    payload["decisions"][0]["approved"] = True
    payload["decisions"][0]["create_path"] = "06_AGENTS/Missing-Node.md"
    proposal_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    validation = validate_unresolved_link_decisions(tmp_path, proposal_path)

    assert validation["status"] == "valid_non_executing"
    assert validation["valid"] is True
    assert validation["blocked_count"] == 0
    assert validation["production_execution_allowed"] is False
    assert validation["planned_actions"][0]["execution_ready"] is True
    assert validation["planned_actions"][0]["writes"] == [
        "06_AGENTS/Draft.md",
        "06_AGENTS/Missing-Node.md",
    ]
    assert "create target node 06_AGENTS/Missing-Node.md" in validation["planned_actions"][0]["effect"]


def test_validate_unresolved_link_decisions_accepts_approved_rename_preview(tmp_path: Path) -> None:
    source_rel = "06_AGENTS/Draft.md"
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / source_rel, "# Draft\n\nSee [[Missing-Node]].\n")
    _write(tmp_path / "06_AGENTS" / "Existing-Node.md", "# Existing Node\n")

    proposal = propose_unresolved_link_decisions(
        scan_vault(tmp_path, unresolved_link_review_limit=5),
        tmp_path,
        output_path="07_LOGS/Graph-Reports/unresolved-proposal.json",
        max_items=5,
    )
    proposal_path = tmp_path / proposal["proposal_path"]
    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    payload["operator_approved"] = True
    payload["approved_by"] = "operator"
    payload["decisions"][0]["decision"] = "rename_link_to_existing_node"
    payload["decisions"][0]["approved"] = True
    payload["decisions"][0]["replacement_target"] = "06_AGENTS/Existing-Node.md"
    proposal_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    validation = validate_unresolved_link_decisions(tmp_path, proposal_path)

    assert validation["status"] == "valid_non_executing"
    assert validation["blocked_count"] == 0
    assert validation["planned_actions"][0]["writes"] == [source_rel]
    assert "06_AGENTS/Existing-Node.md" in validation["planned_actions"][0]["effect"]


def test_validate_unresolved_link_decisions_blocks_unedited_generated_proposal(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Draft.md", "# Draft\n\nSee [[Missing-Node]].\n")

    proposal = propose_unresolved_link_decisions(
        scan_vault(tmp_path, unresolved_link_review_limit=5),
        tmp_path,
        output_path="07_LOGS/Graph-Reports/unresolved-proposal.json",
        max_items=5,
    )

    validation = validate_unresolved_link_decisions(tmp_path, tmp_path / proposal["proposal_path"])
    blockers = validation["planned_actions"][0]["execution_blockers"]

    assert validation["status"] == "blocked"
    assert validation["valid"] is False
    assert validation["blocked_count"] == 1
    assert "operator_approved must be true" in validation["errors"]
    assert "review placeholder decision is not executable; set decision to an allowed decision" in blockers
    assert "per-row approved must be true" in blockers


def test_write_unresolved_approval_preview_copy_is_non_executable(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Draft.md", "# Draft\n\nSee [[Missing-Node]].\n")

    proposal = propose_unresolved_link_decisions(
        scan_vault(tmp_path, unresolved_link_review_limit=5),
        tmp_path,
        output_path="07_LOGS/Graph-Reports/unresolved-proposal.json",
        max_items=5,
    )
    proposal_path = tmp_path / proposal["proposal_path"]
    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    payload["decisions"][0]["decision"] = "create_target_node"
    payload["decisions"][0]["approved"] = True
    payload["decisions"][0]["create_path"] = "06_AGENTS/Missing-Node.md"
    proposal_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    preview = write_unresolved_approval_preview_copy(tmp_path, proposal_path)
    preview_path = tmp_path / preview["approval_preview_path"]
    preview_payload = json.loads(preview_path.read_text(encoding="utf-8"))
    graph_index = (tmp_path / "07_LOGS" / "Graph-Reports" / "Graph-Reports-Index.md").read_text(encoding="utf-8")

    assert preview_payload["operator_approved"] is True
    assert preview_payload["approval_preview_only"] is True
    assert preview_payload["production_execution_allowed"] is False
    assert preview["validation"]["status"] == "valid_non_executing"
    assert Path(preview["approval_preview_path"]).name in graph_index


def test_validate_unresolved_link_decisions_cli_reports_blocked_generated_proposal(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Draft.md", "# Draft\n\nSee [[Missing-Node]].\n")
    proposal = propose_unresolved_link_decisions(
        scan_vault(tmp_path, unresolved_link_review_limit=5),
        tmp_path,
        output_path="07_LOGS/Graph-Reports/unresolved-proposal.json",
        max_items=5,
    )

    monkeypatch.setattr(vault_hygiene, "VAULT_ROOT", tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "vault_hygiene",
            "--validate-unresolved-link-decisions",
            proposal["proposal_path"],
            "--json",
        ],
    )

    try:
        main()
    except SystemExit as exc:
        assert exc.code == 2
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "blocked"
    assert payload["blocked_count"] == 1


def test_ambiguous_link_proposal_writes_review_only_json_and_markdown(tmp_path: Path) -> None:
    source_rel = "06_AGENTS/OpenClaw-Runtime-Profile.md"
    _write(tmp_path / source_rel, "[[coordination_bridge]]\n")
    _write(tmp_path / "runtime" / "hermes" / "coordination_bridge.md", "# Hermes Bridge\n")
    _write(tmp_path / "runtime" / "openclaw" / "coordination_bridge.md", "# OpenClaw Bridge\n")

    report = scan_vault(tmp_path, ambiguous_link_review_limit=5)
    proposal = propose_ambiguous_link_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/ambiguous-proposal.json",
        max_items=5,
    )

    payload = json.loads((tmp_path / proposal["proposal_path"]).read_text(encoding="utf-8"))
    markdown = (tmp_path / proposal["proposal_markdown_path"]).read_text(encoding="utf-8")
    graph_index = (tmp_path / "07_LOGS" / "Graph-Reports" / "Graph-Reports-Index.md").read_text(encoding="utf-8")

    assert proposal["proposal_count"] == 1
    assert payload["proposal_kind"] == "ambiguous_link_target_review"
    assert payload["operator_approved"] is False
    assert payload["proposal_only"] is True
    assert payload["decisions"][0]["link_target"] == "coordination_bridge"
    assert payload["decisions"][0]["recommended_decision"] == "operator_select_path_qualified_target"
    assert payload["decisions"][0]["allowed_decisions"] == [
        "path_qualify_to_existing_node",
        "create_alias_node",
        "rename_or_merge_duplicate_node",
        "remove_link",
        "defer",
    ]
    assert payload["decisions"][0]["candidate_count"] == 2
    assert "runtime/openclaw/coordination_bridge.md" in {
        row["path"] for row in payload["decisions"][0]["candidates"]
    }
    assert "graph-hygiene-ambiguous-link-proposal" in markdown
    assert "[[ambiguous-proposal]]" in graph_index


def test_ambiguous_link_proposal_skips_rows_pending_in_older_unapproved_proposals(tmp_path: Path) -> None:
    _write(tmp_path / "06_AGENTS" / "Source-A.md", "[[coordination_bridge]]\n")
    _write(tmp_path / "06_AGENTS" / "Source-B.md", "[[coordination_bridge]]\n")
    _write(tmp_path / "runtime" / "hermes" / "coordination_bridge.md", "# Hermes Bridge\n")
    _write(tmp_path / "runtime" / "openclaw" / "coordination_bridge.md", "# OpenClaw Bridge\n")

    first_report = scan_vault(tmp_path, ambiguous_link_review_limit=2)
    first = propose_ambiguous_link_decisions(
        first_report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/ambiguous-proposal-1.json",
        max_items=1,
    )
    second_report = scan_vault(tmp_path, ambiguous_link_review_limit=2)
    second = propose_ambiguous_link_decisions(
        second_report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/ambiguous-proposal-2.json",
        max_items=1,
    )

    first_payload = json.loads((tmp_path / first["proposal_path"]).read_text(encoding="utf-8"))
    second_payload = json.loads((tmp_path / second["proposal_path"]).read_text(encoding="utf-8"))

    assert first_payload["decisions"][0]["file"] == "06_AGENTS/Source-A.md"
    assert second_payload["decisions"][0]["file"] == "06_AGENTS/Source-B.md"
    assert second["pending_ambiguous_rows_skipped"] == 1
    assert second_payload["selection"]["pending_ambiguous_rows_skipped"] == 1


def test_ambiguous_link_proposal_cli_expands_scan_for_pending_rows(tmp_path: Path, monkeypatch, capsys) -> None:
    _write(tmp_path / "06_AGENTS" / "Source-A.md", "[[coordination_bridge]]\n")
    _write(tmp_path / "06_AGENTS" / "Source-B.md", "[[coordination_bridge]]\n")
    _write(tmp_path / "runtime" / "hermes" / "coordination_bridge.md", "# Hermes Bridge\n")
    _write(tmp_path / "runtime" / "openclaw" / "coordination_bridge.md", "# OpenClaw Bridge\n")

    first_report = scan_vault(tmp_path, ambiguous_link_review_limit=1)
    propose_ambiguous_link_decisions(
        first_report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/ambiguous-proposal-1.json",
        max_items=1,
    )

    monkeypatch.setattr(vault_hygiene, "VAULT_ROOT", tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "vault_hygiene",
            "--propose-ambiguous-link-decisions",
            "--ambiguous-proposal-max-items",
            "1",
            "--ambiguous-proposal-path",
            "07_LOGS/Graph-Reports/ambiguous-proposal-2.json",
            "--json",
        ],
    )

    main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    proposal_payload = json.loads((tmp_path / payload["proposal_path"]).read_text(encoding="utf-8"))

    assert payload["proposal_count"] == 1
    assert payload["pending_ambiguous_rows_skipped"] == 1
    assert proposal_payload["decisions"][0]["file"] == "06_AGENTS/Source-B.md"


def test_validate_ambiguous_link_decisions_accepts_approved_path_qualify_preview(tmp_path: Path) -> None:
    source_rel = "06_AGENTS/OpenClaw-Runtime-Profile.md"
    _write(tmp_path / source_rel, "# OpenClaw Runtime Profile\n\nSee [[coordination_bridge]].\n")
    _write(tmp_path / "runtime" / "hermes" / "coordination_bridge.md", "# Hermes Bridge\n")
    _write(tmp_path / "runtime" / "openclaw" / "coordination_bridge.md", "# OpenClaw Bridge\n")

    report = scan_vault(tmp_path, ambiguous_link_review_limit=5)
    proposal = propose_ambiguous_link_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/ambiguous-proposal.json",
        max_items=5,
    )
    proposal_path = tmp_path / proposal["proposal_path"]
    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    payload["operator_approved"] = True
    payload["approved_by"] = "operator"
    payload["decisions"][0]["decision"] = "path_qualify_to_existing_node"
    payload["decisions"][0]["approved"] = True
    payload["decisions"][0]["selected_target"] = "runtime/openclaw/coordination_bridge.md"
    proposal_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    validation = validate_ambiguous_link_decisions(tmp_path, proposal_path)

    assert validation["status"] == "valid_non_executing"
    assert validation["valid"] is True
    assert validation["blocked_count"] == 0
    assert validation["production_execution_allowed"] is False
    assert validation["planned_actions"][0]["execution_ready"] is True
    assert validation["planned_actions"][0]["writes"] == [source_rel]
    assert "runtime/openclaw/coordination_bridge.md" in validation["planned_actions"][0]["effect"]


def test_validate_ambiguous_link_decisions_blocks_unselected_generated_proposal(tmp_path: Path) -> None:
    _write(tmp_path / "06_AGENTS" / "OpenClaw-Runtime-Profile.md", "[[coordination_bridge]]\n")
    _write(tmp_path / "runtime" / "hermes" / "coordination_bridge.md", "# Hermes Bridge\n")
    _write(tmp_path / "runtime" / "openclaw" / "coordination_bridge.md", "# OpenClaw Bridge\n")

    report = scan_vault(tmp_path, ambiguous_link_review_limit=5)
    proposal = propose_ambiguous_link_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/ambiguous-proposal.json",
        max_items=5,
    )

    validation = validate_ambiguous_link_decisions(tmp_path, tmp_path / proposal["proposal_path"])
    blockers = validation["planned_actions"][0]["execution_blockers"]

    assert validation["status"] == "blocked"
    assert validation["valid"] is False
    assert validation["blocked_count"] == 1
    assert "operator_approved must be true" in validation["errors"]
    assert "decision must be set explicitly" in blockers
    assert "per-row approved must be true" in blockers


def test_write_ambiguous_approval_preview_copy_is_non_executable(tmp_path: Path) -> None:
    source_rel = "06_AGENTS/OpenClaw-Runtime-Profile.md"
    _write(tmp_path / source_rel, "[[coordination_bridge]]\n")
    _write(tmp_path / "runtime" / "hermes" / "coordination_bridge.md", "# Hermes Bridge\n")
    _write(tmp_path / "runtime" / "openclaw" / "coordination_bridge.md", "# OpenClaw Bridge\n")

    report = scan_vault(tmp_path, ambiguous_link_review_limit=5)
    proposal = propose_ambiguous_link_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/ambiguous-proposal.json",
        max_items=5,
    )
    proposal_path = tmp_path / proposal["proposal_path"]
    payload = json.loads(proposal_path.read_text(encoding="utf-8"))
    payload["decisions"][0]["decision"] = "path_qualify_to_existing_node"
    payload["decisions"][0]["approved"] = True
    payload["decisions"][0]["selected_target"] = "runtime/openclaw/coordination_bridge.md"
    proposal_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    preview = write_ambiguous_approval_preview_copy(tmp_path, proposal_path)
    preview_path = tmp_path / preview["approval_preview_path"]
    preview_payload = json.loads(preview_path.read_text(encoding="utf-8"))
    graph_index = (tmp_path / "07_LOGS" / "Graph-Reports" / "Graph-Reports-Index.md").read_text(encoding="utf-8")

    assert preview_payload["operator_approved"] is True
    assert preview_payload["approval_preview_only"] is True
    assert preview_payload["production_execution_allowed"] is False
    assert preview["validation"]["status"] == "valid_non_executing"
    assert Path(preview["approval_preview_path"]).name in graph_index


def test_validate_ambiguous_link_decisions_cli_reports_blocked_generated_proposal(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    _write(tmp_path / "06_AGENTS" / "OpenClaw-Runtime-Profile.md", "[[coordination_bridge]]\n")
    _write(tmp_path / "runtime" / "hermes" / "coordination_bridge.md", "# Hermes Bridge\n")
    _write(tmp_path / "runtime" / "openclaw" / "coordination_bridge.md", "# OpenClaw Bridge\n")
    proposal = propose_ambiguous_link_decisions(
        scan_vault(tmp_path, ambiguous_link_review_limit=5),
        tmp_path,
        output_path="07_LOGS/Graph-Reports/ambiguous-proposal.json",
        max_items=5,
    )

    monkeypatch.setattr(vault_hygiene, "VAULT_ROOT", tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "vault_hygiene",
            "--validate-ambiguous-link-decisions",
            proposal["proposal_path"],
            "--json",
        ],
    )

    try:
        main()
    except SystemExit as exc:
        assert exc.code == 2
    payload = json.loads(capsys.readouterr().out)

    assert payload["status"] == "blocked"
    assert payload["blocked_count"] == 1


def test_empty_markdown_slot_is_review_delete_candidate_not_junk(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "runtime" / "adapters" / "codex" / "runs" / "run-1" / "codex-stdout.md", "\n")

    report = scan_vault(tmp_path)

    matches = [
        issue for issue in report.issues
        if issue.file_path == "runtime/adapters/codex/runs/run-1/codex-stdout.md"
    ]
    assert matches
    assert matches[0].category == "empty_placeholder"
    assert matches[0].severity == "review"
    assert matches[0].action == "delete_candidate"


def test_graph_scan_skips_runtime_temp_file_removed_after_discovery(tmp_path: Path, monkeypatch) -> None:
    stable_path = tmp_path / "CLAUDE.md"
    transient_path = tmp_path / "runtime" / "browser_runtime" / "_tmp" / "transient.md"
    _write(stable_path, "[[Vault-Map]]\n")
    _write(transient_path, "# Transient\n")
    transient_path.unlink()

    monkeypatch.setattr(
        vault_hygiene,
        "_iter_markdown_paths",
        lambda root: [stable_path, transient_path],
    )

    states = vault_hygiene.build_vault_graph_state(tmp_path)

    assert "CLAUDE.md" in states
    assert "runtime/browser_runtime/_tmp/transient.md" not in states


def test_graph_orphan_fix_uses_path_links_for_duplicate_stems_and_review_archive(tmp_path: Path) -> None:
    active_rel = "05_TEMPLATES/Agent-Runtime-Profile-Template.md"
    archive_rel = (
        "99_ARCHIVE/Vault-Hygiene-Review/Noncanonical-Artifacts/2026-05-05/"
        "Agent-Runtime-Profile-Template.md"
    )
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    body = "# Agent Runtime Profile Template\n\nPurpose line.\nSecond line.\n"
    _write(tmp_path / active_rel, body)
    _write(tmp_path / archive_rel, body)

    report = scan_vault(tmp_path)
    vault_hygiene.apply_fixes(tmp_path, report)
    next_report = scan_vault(tmp_path)
    vault_map = (tmp_path / "06_AGENTS" / "Vault-Map.md").read_text(encoding="utf-8")
    archive_index = (
        tmp_path
        / "99_ARCHIVE"
        / "Vault-Hygiene-Review"
        / "Noncanonical-Artifacts"
        / "Noncanonical-Artifacts-Index.md"
    ).read_text(encoding="utf-8")

    assert f"[[{active_rel[:-3]}|Agent-Runtime-Profile-Template]]" in vault_map
    assert f"[[{archive_rel[:-3]}|Agent-Runtime-Profile-Template]]" in archive_index
    assert not [
        issue for issue in next_report.issues
        if issue.category == "graph_orphan" and issue.file_path in {active_rel, archive_rel}
    ]


def test_duplicate_candidate_appears_in_json_review_queue(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Permission-Matrix]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Permission-Matrix.md", "# Permission Matrix\n")
    _write(tmp_path / "core_export" / "templates" / "Permission-Matrix.core.md", "# Permission Matrix\n")

    report = scan_vault(tmp_path)
    payload = json.loads(render_json_report(report))
    queue = payload["loose_node_review_queue"]
    matches = [
        item for item in queue
        if item["file"] == "core_export/templates/Permission-Matrix.core.md"
    ]

    assert payload["loose_node_review_count"] == len(build_loose_node_review_queue(report))
    assert matches
    assert matches[0]["issue_category"] == "duplicate_candidate"
    assert matches[0]["node_category"] == "core_export_artifact"
    assert matches[0]["keep_or_canonical"] == "06_AGENTS/Permission-Matrix.md"
    assert matches[0]["decision_hint"] == "replace_with_canonical_after_review"
    assert matches[0]["recommended_action"] == "review_duplicate_then_archive_or_delete"
    assert "canonical_exists=true" in matches[0]["evidence"]


def test_infer_node_category_identifies_runtime_readmes_and_logs() -> None:
    assert infer_node_category("runtime/adapters/harness/README.md") == "runtime_readme"
    assert infer_node_category("07_LOGS/Build-Logs/2026-05-04-ChaseOS-example.md") == "build_log"
    assert infer_node_category("06_AGENTS/Harness-Adapter-Map.md") == "agent_draft_doc"


def test_write_review_queue_artifacts_indexes_markdown_queue(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Permission-Matrix]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Permission-Matrix.md", "# Permission Matrix\n")
    _write(tmp_path / "core_export" / "templates" / "Permission-Matrix.core.md", "# Permission Matrix\n")

    report = scan_vault(tmp_path)
    artifacts = write_loose_node_review_artifacts(report, tmp_path)
    json_path = tmp_path / artifacts["json"]
    md_path = tmp_path / artifacts["markdown"]
    index_path = tmp_path / "07_LOGS" / "Graph-Reports" / "Graph-Reports-Index.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert json_path.exists()
    assert md_path.exists()
    assert payload["loose_node_review_count"] >= 1
    assert "Permission-Matrix.core.md" in md_path.read_text(encoding="utf-8")
    assert f"[[{md_path.stem}]]" in index_path.read_text(encoding="utf-8")


def test_keep_excluded_decision_suppresses_matching_hash(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "runtime" / "adapters" / "harness" / "README.md", "# Harness README\n\nTechnical note.\n")

    report = scan_vault(tmp_path)
    queue = build_loose_node_review_queue(report, tmp_path)
    item = next(i for i in queue if i["file"] == "runtime/adapters/harness/README.md")
    decisions_path = tmp_path / "decisions.json"
    decisions_path.write_text(json.dumps({
        "operator_approved": True,
        "approved_by": "test-operator",
        "decisions": [{
            "file": item["file"],
            "decision": "keep_excluded",
            "file_sha256": item["file_sha256"],
            "reason": "Technical adapter README; keep outside graph navigation.",
        }],
    }), encoding="utf-8")

    result = apply_review_decisions(tmp_path, decisions_path, execute=True)
    assert result.status == "applied"
    assert result.applied == 1

    next_report = scan_vault(tmp_path)
    next_queue = build_loose_node_review_queue(next_report, tmp_path)
    assert not [i for i in next_queue if i["file"] == item["file"]]


def test_keep_excluded_visible_orphan_wires_to_holding_index(tmp_path: Path) -> None:
    rel = "runtime/adapters/harness/README.md"
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / rel, "# Harness README\n\nTechnical note.\n")

    report = scan_vault(tmp_path)
    item = next(i for i in build_loose_node_review_queue(report, tmp_path) if i["file"] == rel)
    decisions_path = tmp_path / "decisions.json"
    decisions_path.write_text(json.dumps({
        "operator_approved": True,
        "approved_by": "test-operator",
        "decisions": [{
            "file": item["file"],
            "decision": "keep_excluded",
            "file_sha256": item["file_sha256"],
            "reason": "Technical adapter README; keep outside canonical navigation.",
        }],
    }), encoding="utf-8")
    result = apply_review_decisions(tmp_path, decisions_path, execute=True)
    assert result.status == "applied"

    visible_report = scan_vault(tmp_path)
    visible_issues = [
        issue for issue in visible_report.issues
        if issue.file_path == rel and issue.category == "keep_excluded_visible_orphan"
    ]
    assert visible_issues
    assert visible_issues[0].severity == "auto_fix"
    assert visible_issues[0].index_path == vault_hygiene.KEEP_EXCLUDED_INDEX_REL
    assert not [i for i in build_loose_node_review_queue(visible_report, tmp_path) if i["file"] == rel]

    vault_hygiene.apply_fixes(tmp_path, visible_report)
    index_text = (tmp_path / vault_hygiene.KEEP_EXCLUDED_INDEX_REL).read_text(encoding="utf-8")
    graph_state = vault_hygiene.build_vault_graph_state(tmp_path)
    final_report = scan_vault(tmp_path)

    assert f"[[{rel[:-3]}|README]]" in index_text
    assert "[[Vault-Map]]" in index_text
    assert vault_hygiene.KEEP_EXCLUDED_INDEX_REL in graph_state[rel].inbound
    assert not [
        issue for issue in final_report.issues
        if issue.file_path == rel and issue.category == "keep_excluded_visible_orphan"
    ]


def test_review_summary_includes_visible_graph_audit(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "runtime" / "adapters" / "harness" / "README.md", "# Harness README\n\nTechnical note.\n")

    summary = build_review_summary(scan_vault(tmp_path), tmp_path)
    visible = summary["visible_graph_audit"]

    assert visible["raw_zero_degree_count"] >= 1
    assert "unresolved_link_target_count" in visible
    assert "connected_duplicate_stem_count" in visible
    assert "semantic_hub_gap_count" in visible


def test_strikezone_rss_staged_capture_wires_to_project_staging_index(tmp_path: Path) -> None:
    rel = "runtime/acquisition/staging/strikezone/20260506-095135-strikezone-rss-coindesk.md"
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "ChaseOS-Vault-Maintenance.md", "# Vault Maintenance\n")
    _write(tmp_path / "06_AGENTS" / "Graph-Hygiene-CLI-and-OpenClaw-Cron-Runbook.md", "# Runbook\n")
    _write(tmp_path / "01_PROJECTS" / "StrikeZone" / "StrikeZone-Crypto-OS.md", "# StrikeZone Crypto\n")
    _write(tmp_path / "01_PROJECTS" / "TradingSystems" / "TradingSystems-OS.md", "# Trading Systems\n")
    _write(tmp_path / "01_PROJECTS" / "TradingSystems" / "CryptoPerps-OS.md", "# Crypto Perps\n")
    _write(
        tmp_path / "runtime" / "acquisition" / "manual" / "strikezone" / "StrikeZone-Research-Import-Operator-Guide.md",
        "# StrikeZone Research Import Operator Guide\n",
    )
    _write(
        tmp_path / "02_KNOWLEDGE" / "Trading-Systems" / "Trading-Systems-Engineering.md",
        "# Trading Systems Engineering\n",
    )
    _write(
        tmp_path / rel,
        """<!-- staged-capture
source_id: strikezone-rss-coindesk
display_name: CoinDesk RSS - crypto news
source_platform: rss
source_class: staged_capture
trust_tier: 3
origin_kind: rss-feed
freshness_window: daily
captured_at: 2026-05-06T09:51:35+00:00
query: rss_feed:https://www.coindesk.com/arc/outboundfeeds/rss/
-->

# Feed: CoinDesk

## BTC headline
Link: https://example.com
""",
    )

    report = scan_vault(tmp_path)
    issue = next(i for i in report.issues if i.file_path == rel)

    assert issue.category == "strikezone_staged_capture_orphan"
    assert issue.severity == "auto_fix"
    assert issue.index_path == vault_hygiene.STRIKEZONE_RSS_STAGING_INDEX_REL
    assert issue.canonical_path == "01_PROJECTS/StrikeZone/StrikeZone-Crypto-OS.md"

    vault_hygiene.apply_fixes(tmp_path, report)
    index_text = (tmp_path / vault_hygiene.STRIKEZONE_RSS_STAGING_INDEX_REL).read_text(encoding="utf-8")
    final_state = vault_hygiene.build_vault_graph_state(tmp_path)
    final_report = scan_vault(tmp_path)
    final_queue = build_loose_node_review_queue(final_report, tmp_path)

    assert "[[StrikeZone-Crypto-OS]]" in index_text
    assert "[[TradingSystems/TradingSystems-OS|Trading Systems / Market Ops]]" in index_text
    assert f"[[{rel[:-3]}|20260506-095135-strikezone-rss-coindesk]]" in index_text
    assert vault_hygiene.STRIKEZONE_RSS_STAGING_INDEX_REL in final_state[rel].inbound
    assert not [i for i in final_queue if i["file"] == rel]


def test_strikezone_manual_templates_wire_to_local_readme(tmp_path: Path) -> None:
    rel = "runtime/acquisition/manual/strikezone/templates/grok_digest.template.md"
    readme_rel = "runtime/acquisition/manual/strikezone/README.md"
    _write(tmp_path / "CLAUDE.md", "[[06_AGENTS/Vault-Map|Vault Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / readme_rel, "# StrikeZone Research Import Drop Folders\n")
    _write(tmp_path / rel, "# Grok Market Digest\n\nPaste operator-reviewed digest content here.\n")

    report = scan_vault(tmp_path)
    issue = next(i for i in report.issues if i.file_path == rel)

    assert issue.category == "graph_orphan"
    assert issue.severity == "auto_fix"
    assert issue.action == "wire_strikezone_manual_template_to_readme"
    assert issue.index_path == readme_rel
    assert not [i for i in build_loose_node_review_queue(report, tmp_path) if i["file"] == rel]

    vault_hygiene.apply_fixes(tmp_path, report)
    readme_text = (tmp_path / readme_rel).read_text(encoding="utf-8")
    final_state = vault_hygiene.build_vault_graph_state(tmp_path)

    assert f"[[{rel[:-3]}|grok_digest.template]]" in readme_text
    assert readme_rel in final_state[rel].inbound


def test_replace_with_canonical_archives_duplicate_candidate(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Agent-Control-Plane]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Agent-Control-Plane.md", "# Agent Control Plane\n\n[[Vault-Map]]\n\nCanonical body.\n")
    _write(tmp_path / "core_export" / "templates" / "Agent-Control-Plane.core.md", "# Agent Control Plane\n")

    report = scan_vault(tmp_path)
    queue = build_loose_node_review_queue(report, tmp_path)
    item = next(i for i in queue if i["file"] == "core_export/templates/Agent-Control-Plane.core.md")
    decisions_path = tmp_path / "decisions.json"
    decisions_path.write_text(json.dumps({
        "operator_approved": True,
        "approved_by": "test-operator",
        "decisions": [{
            "file": item["file"],
            "decision": "replace_with_canonical",
            "approved": True,
            "expected_sha256": item["file_sha256"],
            "canonical_path": item["canonical_path"],
            "reason": "Canonical control-plane file is the kept version.",
        }],
    }), encoding="utf-8")

    result = apply_review_decisions(tmp_path, decisions_path, execute=True)
    assert result.status == "applied"
    assert result.applied == 1
    assert not (tmp_path / "core_export" / "templates" / "Agent-Control-Plane.core.md").exists()
    assert (tmp_path / "06_AGENTS" / "Agent-Control-Plane.md").exists()
    assert result.files_moved
    assert result.files_moved[0]["to"].startswith("99_ARCHIVE/Vault-Hygiene-Review/Replaced-Duplicates/")
    assert result.decision_log_path in result.files_written
    assert "T" in Path(result.decision_log_path).name
    decision_log = json.loads((tmp_path / result.decision_log_path).read_text(encoding="utf-8"))
    assert result.decision_log_path in decision_log["files_written"]
    index_text = (tmp_path / "07_LOGS" / "Graph-Reports" / "Graph-Reports-Index.md").read_text(encoding="utf-8")
    assert Path(result.decision_log_path).name in index_text


def test_noncanonical_artifact_proposal_uses_artifact_archive_decision(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(
        tmp_path / "core_export" / "reports" / "latest" / "mistaken-runtime-note.md",
        "# Mistaken Runtime Note\n\nPartial content from an abandoned runtime write.\n",
    )

    report = scan_vault(tmp_path)
    proposal = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/proposal.json",
        max_items=1,
        categories=["review_only_artifact"],
    )
    payload = json.loads((tmp_path / proposal["proposal_path"]).read_text(encoding="utf-8"))
    decision = payload["decisions"][0]
    result = apply_review_decisions(tmp_path, tmp_path / proposal["proposal_path"], execute=False)
    rendered = render_decision_apply_result(result)

    assert decision["file"] == "core_export/reports/latest/mistaken-runtime-note.md"
    assert decision["decision"] == "archive_noncanonical_artifact"
    assert decision["approved"] is False
    assert decision["expected_sha256"]
    assert result.status == "dry_run_valid"
    assert result.planned_actions[0]["execution_ready"] is False
    assert result.planned_actions[0]["moves"][0]["to"].startswith(
        "99_ARCHIVE/Vault-Hygiene-Review/Noncanonical-Artifacts/"
    )
    assert "Noncanonical-Artifacts/Noncanonical-Artifacts-Index.md" in rendered


def test_archive_noncanonical_artifact_moves_and_indexes_artifact(tmp_path: Path) -> None:
    artifact_rel = "core_export/reports/latest/mistaken-runtime-note.md"
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(
        tmp_path / artifact_rel,
        "# Mistaken Runtime Note\n\nPartial content from an abandoned runtime write.\n",
    )

    report = scan_vault(tmp_path)
    queue = build_loose_node_review_queue(report, tmp_path)
    item = next(i for i in queue if i["file"] == artifact_rel)
    decisions_path = tmp_path / "decisions.json"
    decisions_path.write_text(json.dumps({
        "operator_approved": True,
        "approved_by": "test-operator",
        "decisions": [{
            "file": item["file"],
            "decision": "archive_noncanonical_artifact",
            "approved": True,
            "expected_sha256": item["file_sha256"],
            "reason": "Review-only export artifact; keep as connected cleanup evidence.",
        }],
    }), encoding="utf-8")

    result = apply_review_decisions(tmp_path, decisions_path, execute=True)
    moved_rel = result.files_moved[0]["to"]
    index_rel = "99_ARCHIVE/Vault-Hygiene-Review/Noncanonical-Artifacts/Noncanonical-Artifacts-Index.md"
    registry = json.loads((tmp_path / "runtime" / "graph" / "vault_hygiene_decisions.json").read_text(encoding="utf-8"))
    index_content = (tmp_path / index_rel).read_text(encoding="utf-8")
    next_report = scan_vault(tmp_path)
    next_queue = build_loose_node_review_queue(next_report, tmp_path)

    assert result.status == "applied"
    assert result.applied == 1
    assert not (tmp_path / artifact_rel).exists()
    assert moved_rel.startswith("99_ARCHIVE/Vault-Hygiene-Review/Noncanonical-Artifacts/")
    assert (tmp_path / moved_rel).exists()
    assert index_rel in result.files_written
    assert artifact_rel in index_content
    assert moved_rel in index_content
    assert registry["decisions"][artifact_rel]["decision"] == "archive_noncanonical_artifact"
    assert registry["decisions"][artifact_rel]["archive_path"] == moved_rel
    assert registry["decisions"][artifact_rel]["artifact_index_path"] == index_rel
    assert not [i for i in next_queue if i["file"] == artifact_rel]
    assert not [i for i in next_queue if i["file"].startswith("99_ARCHIVE/Vault-Hygiene-Review/")]


def test_destructive_decision_blocks_without_per_file_approval(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "runtime" / "adapters" / "codex" / "runs" / "run-1" / "codex-stdout.md", "\n")

    report = scan_vault(tmp_path)
    queue = build_loose_node_review_queue(report, tmp_path)
    item = next(i for i in queue if i["file"] == "runtime/adapters/codex/runs/run-1/codex-stdout.md")
    decisions_path = tmp_path / "decisions.json"
    decisions_path.write_text(json.dumps({
        "operator_approved": True,
        "approved_by": "test-operator",
        "decisions": [{
            "file": item["file"],
            "decision": "delete_after_review",
            "expected_sha256": item["file_sha256"],
            "reason": "Empty placeholder.",
        }],
    }), encoding="utf-8")

    result = apply_review_decisions(tmp_path, decisions_path, execute=True)
    assert result.status == "blocked"
    assert result.blocked == 1
    assert (tmp_path / "runtime" / "adapters" / "codex" / "runs" / "run-1" / "codex-stdout.md").exists()


def test_propose_review_decisions_writes_unapproved_small_batch(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Agent-Control-Plane]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Agent-Control-Plane.md", "# Agent Control Plane\n\n[[Vault-Map]]\n\nCanonical body.\n")
    _write(tmp_path / "core_export" / "templates" / "Agent-Control-Plane.core.md", "# Agent Control Plane\n")
    _write(tmp_path / "runtime" / "adapters" / "codex" / "runs" / "run-1" / "codex-stdout.md", "\n")

    report = scan_vault(tmp_path)
    proposal = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/proposal.json",
        max_items=2,
        categories=["duplicate_candidate", "empty_placeholder"],
    )
    payload = json.loads((tmp_path / proposal["proposal_path"]).read_text(encoding="utf-8"))
    markdown = (tmp_path / proposal["proposal_markdown_path"]).read_text(encoding="utf-8")
    graph_index = (tmp_path / "07_LOGS" / "Graph-Reports" / "Graph-Reports-Index.md").read_text(encoding="utf-8")

    assert payload["operator_approved"] is False
    assert payload["proposal_only"] is True
    assert len(payload["decisions"]) == 2
    assert proposal["proposal_markdown_path"] == "07_LOGS/Graph-Reports/proposal.md"
    assert "## Decisions" in markdown
    assert "`core_export/templates/Agent-Control-Plane.core.md`" in markdown
    assert "Loose Node Decision Proposal" in graph_index
    assert "decision proposal guard" in graph_index
    assert any(d["decision"] == "replace_with_canonical" and d["approved"] is False for d in payload["decisions"])
    assert any(d["decision"] == "delete_after_review" and d["approved"] is False for d in payload["decisions"])


def test_apply_review_decisions_dry_run_renders_execution_plan(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Agent-Control-Plane]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Agent-Control-Plane.md", "# Agent Control Plane\n\n[[Vault-Map]]\n\nCanonical body.\n")
    _write(tmp_path / "core_export" / "templates" / "Agent-Control-Plane.core.md", "# Agent Control Plane\n")

    report = scan_vault(tmp_path)
    proposal = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/proposal.json",
        max_items=1,
        categories=["duplicate_candidate"],
    )
    result = apply_review_decisions(tmp_path, tmp_path / proposal["proposal_path"], execute=False)
    rendered = render_decision_apply_result(result)

    assert result.status == "dry_run_valid"
    assert result.planned_actions
    assert result.planned_actions[0]["execution_ready"] is False
    assert result.planned_actions[0]["canonical_path"] == "06_AGENTS/Agent-Control-Plane.md"
    assert result.planned_actions[0]["moves"][0]["to"].startswith(
        "99_ARCHIVE/Vault-Hygiene-Review/Replaced-Duplicates/"
    )
    assert "operator_approved must be true" in rendered
    assert "per-decision approved must be true" in rendered
    assert "canonical kept: 06_AGENTS/Agent-Control-Plane.md" in rendered
    assert "move: core_export/templates/Agent-Control-Plane.core.md -> 99_ARCHIVE/Vault-Hygiene-Review/Replaced-Duplicates/" in rendered


def test_approval_preview_copy_shows_approved_shape_but_blocks_execution(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Agent-Control-Plane]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Agent-Control-Plane.md", "# Agent Control Plane\n\n[[Vault-Map]]\n\nCanonical body.\n")
    _write(tmp_path / "core_export" / "templates" / "Agent-Control-Plane.core.md", "# Agent Control Plane\n")

    report = scan_vault(tmp_path)
    proposal = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/proposal.json",
        max_items=1,
        categories=["duplicate_candidate"],
    )
    preview = write_approval_preview_copy(tmp_path, tmp_path / proposal["proposal_path"])
    preview_path = tmp_path / preview["approval_preview_path"]
    preview_payload = json.loads(preview_path.read_text(encoding="utf-8"))
    graph_index = (tmp_path / "07_LOGS" / "Graph-Reports" / "Graph-Reports-Index.md").read_text(encoding="utf-8")
    dry_run_result = apply_review_decisions(tmp_path, preview_path, execute=False)
    execute_result = apply_review_decisions(tmp_path, preview_path, execute=True)
    rendered = render_decision_apply_result(dry_run_result)

    assert preview_payload["operator_approved"] is True
    assert preview_payload["approval_preview_only"] is True
    assert preview_payload["production_execution_allowed"] is False
    assert preview_payload["decisions"][0]["approved"] is True
    assert dry_run_result.status == "dry_run_valid"
    assert dry_run_result.approval_preview_only is True
    assert dry_run_result.planned_actions[0]["execution_ready"] is True
    assert "Approval preview only: true" in rendered
    assert execute_result.status == "blocked"
    assert execute_result.blocked == 1
    assert "approval-preview decision copy cannot be executed" in execute_result.messages[0]["reason"]
    assert Path(preview["approval_preview_path"]).name in graph_index
    assert (tmp_path / "core_export" / "templates" / "Agent-Control-Plane.core.md").exists()


def test_review_archive_files_do_not_reenter_queue_or_proposals(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Agent-Control-Plane]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Agent-Control-Plane.md", "# Agent Control Plane\n\n[[Vault-Map]]\n\nCanonical body.\n")
    _write(
        tmp_path
        / "99_ARCHIVE"
        / "Vault-Hygiene-Review"
        / "Replaced-Duplicates"
        / "2026-05-04"
        / "core_export"
        / "templates"
        / "Agent-Control-Plane.core.md",
        "# Agent Control Plane\n",
    )
    _write(tmp_path / "core_export" / "templates" / "Permission-Matrix.core.md", "# Permission Matrix\n")
    _write(tmp_path / "06_AGENTS" / "Permission-Matrix.md", "# Permission Matrix\n\n[[Vault-Map]]\n\nCanonical body.\n")

    report = scan_vault(tmp_path)
    queue = build_loose_node_review_queue(report, tmp_path)
    proposal = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/proposal.json",
        max_items=10,
        categories=["duplicate_candidate"],
    )
    payload = json.loads((tmp_path / proposal["proposal_path"]).read_text(encoding="utf-8"))

    assert not [
        item for item in queue
        if item["file"].startswith("99_ARCHIVE/Vault-Hygiene-Review/")
    ]
    assert not [
        decision for decision in payload["decisions"]
        if decision["file"].startswith("99_ARCHIVE/Vault-Hygiene-Review/")
    ]
    assert any(
        decision["file"] == "core_export/templates/Permission-Matrix.core.md"
        for decision in payload["decisions"]
    )


def test_pending_unapproved_proposals_reserve_items_from_later_batches(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Agent-Control-Plane]]\n[[Permission-Matrix]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Agent-Control-Plane.md", "# Agent Control Plane\n\n[[Vault-Map]]\n\nCanonical body.\n")
    _write(tmp_path / "06_AGENTS" / "Permission-Matrix.md", "# Permission Matrix\n\n[[Vault-Map]]\n\nCanonical body.\n")
    _write(tmp_path / "core_export" / "templates" / "Agent-Control-Plane.core.md", "# Agent Control Plane\n")
    _write(tmp_path / "core_export" / "templates" / "Permission-Matrix.core.md", "# Permission Matrix\n")
    pending_path = tmp_path / "07_LOGS" / "Graph-Reports" / "pending-proposal.json"
    _write(pending_path, json.dumps({
        "operator_approved": False,
        "proposal_only": True,
        "decisions": [{
            "file": "core_export/templates/Agent-Control-Plane.core.md",
            "decision": "replace_with_canonical",
        }],
    }))

    report = scan_vault(tmp_path)
    regenerated = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/pending-proposal.json",
        max_items=1,
        categories=["duplicate_candidate"],
    )
    next_batch = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/next-proposal.json",
        max_items=10,
        categories=["duplicate_candidate"],
    )
    regenerated_payload = json.loads((tmp_path / regenerated["proposal_path"]).read_text(encoding="utf-8"))
    next_payload = json.loads((tmp_path / next_batch["proposal_path"]).read_text(encoding="utf-8"))

    assert regenerated["pending_proposal_files_skipped"] == 0
    assert regenerated_payload["decisions"][0]["file"] == "core_export/templates/Agent-Control-Plane.core.md"
    assert next_batch["pending_proposal_files_skipped"] == 1
    assert "07_LOGS/Graph-Reports/pending-proposal.json" in next_batch["pending_proposal_sources"]
    assert not [
        decision for decision in next_payload["decisions"]
        if decision["file"] == "core_export/templates/Agent-Control-Plane.core.md"
    ]
    assert any(
        decision["file"] == "core_export/templates/Permission-Matrix.core.md"
        for decision in next_payload["decisions"]
    )


def test_proposal_can_include_stale_pending_conflicts_with_supersedes_metadata(tmp_path: Path) -> None:
    file_rel = "runtime/acquisition/manual/example/templates/grok_digest.template.md"
    pending_rel = "07_LOGS/Graph-Reports/pending-runtime-proposal.json"
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / file_rel, "# Grok Digest Template\n\nRuntime-only template.\n")
    _write(tmp_path / pending_rel, json.dumps({
        "operator_approved": False,
        "proposal_only": True,
        "decisions": [{
            "file": file_rel,
            "decision": "keep_excluded",
        }],
    }))

    report = scan_vault(tmp_path)
    blocked = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/blocked-proposal.json",
        max_items=10,
        categories=["runtime_markdown_loose"],
    )
    conflict = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/conflict-proposal.json",
        max_items=10,
        categories=["runtime_markdown_loose"],
        include_pending_conflicts=True,
    )
    conflict_payload = json.loads((tmp_path / conflict["proposal_path"]).read_text(encoding="utf-8"))
    conflict_markdown = (tmp_path / conflict["proposal_markdown_path"]).read_text(encoding="utf-8")
    decision = conflict_payload["decisions"][0]

    assert blocked["pending_proposal_files_skipped"] == 1
    assert blocked["proposal_count"] == 0
    assert conflict["pending_proposal_files_skipped"] == 0
    assert conflict["pending_conflicts_included"] == 1
    assert conflict_payload["selection"]["include_pending_conflicts"] is True
    assert conflict_payload["selection"]["pending_conflicts_included"] == 1
    assert decision["file"] == file_rel
    assert decision["decision"] == "archive_noncanonical_artifact"
    assert decision["supersedes_pending_decisions"] == ["keep_excluded"]
    assert decision["supersedes_pending_proposal_sources"] == [pending_rel]
    assert "Pending conflicts included" in conflict_markdown


def test_proposal_can_consolidate_same_decision_pending_items(tmp_path: Path) -> None:
    file_rel = "runtime/agents/README.md"
    pending_rel = "07_LOGS/Graph-Reports/pending-readme-proposal.json"
    _write(tmp_path / "CLAUDE.md", "[[Vault-Map]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / file_rel, "# Runtime Agents\n\nTechnical runtime README.\n")
    _write(tmp_path / pending_rel, json.dumps({
        "operator_approved": False,
        "proposal_only": True,
        "decisions": [{
            "file": file_rel,
            "decision": "keep_excluded",
        }],
    }))

    report = scan_vault(tmp_path)
    blocked = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/blocked-proposal.json",
        max_items=10,
        categories=["technical_readme_loose"],
    )
    consolidated = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/consolidated-proposal.json",
        max_items=10,
        categories=["technical_readme_loose"],
        include_pending_same_decision=True,
    )
    consolidated_payload = json.loads((tmp_path / consolidated["proposal_path"]).read_text(encoding="utf-8"))
    consolidated_markdown = (tmp_path / consolidated["proposal_markdown_path"]).read_text(encoding="utf-8")
    decision = consolidated_payload["decisions"][0]

    assert blocked["pending_proposal_files_skipped"] == 1
    assert blocked["proposal_count"] == 0
    assert consolidated["pending_proposal_files_skipped"] == 0
    assert consolidated["pending_same_decisions_included"] == 1
    assert consolidated_payload["selection"]["include_pending_same_decision"] is True
    assert consolidated_payload["selection"]["pending_same_decisions_included"] == 1
    assert decision["file"] == file_rel
    assert decision["decision"] == "keep_excluded"
    assert decision["consolidates_pending_decisions"] == ["keep_excluded"]
    assert decision["consolidates_pending_proposal_sources"] == [pending_rel]
    assert "supersedes_pending_decisions" not in decision
    assert "Pending same decisions included" in consolidated_markdown


def test_approved_sibling_proposal_does_not_reserve_old_unapproved_items(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Agent-Control-Plane]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Agent-Control-Plane.md", "# Agent Control Plane\n\n[[Vault-Map]]\n\nCanonical body.\n")
    _write(tmp_path / "core_export" / "templates" / "Agent-Control-Plane.core.md", "# Agent Control Plane\n")
    base_payload = {
        "proposal_only": True,
        "decisions": [{
            "file": "core_export/templates/Agent-Control-Plane.core.md",
            "decision": "replace_with_canonical",
        }],
    }
    _write(
        tmp_path / "07_LOGS" / "Graph-Reports" / "old-proposal.json",
        json.dumps({"operator_approved": False, **base_payload}),
    )
    _write(
        tmp_path / "07_LOGS" / "Graph-Reports" / "old-proposal-approved.json",
        json.dumps({"operator_approved": True, **base_payload}),
    )

    report = scan_vault(tmp_path)
    proposal = propose_review_decisions(
        report,
        tmp_path,
        output_path="07_LOGS/Graph-Reports/new-proposal.json",
        max_items=10,
        categories=["duplicate_candidate"],
    )
    payload = json.loads((tmp_path / proposal["proposal_path"]).read_text(encoding="utf-8"))

    assert proposal["pending_proposal_files_skipped"] == 0
    assert "07_LOGS/Graph-Reports/old-proposal.json" not in proposal["pending_proposal_sources"]
    assert any(
        decision["file"] == "core_export/templates/Agent-Control-Plane.core.md"
        for decision in payload["decisions"]
    )


def test_review_summary_shows_categories_decisions_and_effects(tmp_path: Path) -> None:
    _write(tmp_path / "CLAUDE.md", "[[Agent-Control-Plane]]\n")
    _write(tmp_path / "06_AGENTS" / "Vault-Map.md", "# Vault Map\n")
    _write(tmp_path / "06_AGENTS" / "Agent-Control-Plane.md", "# Agent Control Plane\n\n[[Vault-Map]]\n\nCanonical body.\n")
    _write(tmp_path / "core_export" / "templates" / "Agent-Control-Plane.core.md", "# Agent Control Plane\n")
    _write(tmp_path / "runtime" / "adapters" / "codex" / "runs" / "run-1" / "codex-stdout.md", "\n")

    report = scan_vault(tmp_path)
    summary = build_review_summary(report, tmp_path, max_items=5)
    rendered = render_review_summary(summary)

    assert summary["review_count"] >= 2
    assert summary["issue_counts"]["duplicate_candidate"] == 1
    assert summary["active_review_issue_counts"]["duplicate_candidate"] == 1
    assert summary["raw_issue_counts"]["duplicate_candidate"] == 1
    assert summary["recommended_decision_counts"]["replace_with_canonical"] == 1
    assert "Raw scan issue categories:" in rendered
    assert "Active review-queue categories:" in rendered
    assert "99_ARCHIVE/Vault-Hygiene-Review/Replaced-Duplicates/YYYY-MM-DD/core_export/templates/Agent-Control-Plane.core.md" in rendered
    assert "delete this file only after explicit operator approval" in rendered
