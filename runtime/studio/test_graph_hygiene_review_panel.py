"""
Tests for runtime/studio/graph_hygiene_review_panel.py

Verifies:
- build_graph_hygiene_review_panel reads latest maintain-run + review-queue
- authority.canonical_mutation_allowed is always False
- missing Maintain-Runs directory → warnings, not crash
- missing review queue → warnings, not crash
- malformed JSON → warnings, not crash
- real vault integration (uses available fixtures)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.graph_hygiene_review_panel import build_graph_hygiene_review_panel


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Path:
    """Minimal vault with both log directories."""
    maintain_dir = tmp_path / "07_LOGS" / "Maintain-Runs"
    reports_dir  = tmp_path / "07_LOGS" / "Graph-Reports"
    maintain_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture()
def vault_with_run(tmp_vault: Path) -> Path:
    """Vault with one maintain-run log."""
    run_md = tmp_vault / "07_LOGS" / "Maintain-Runs" / "2026-05-20-os-hygiene-graph-run.md"
    run_md.write_text(
        "---\nworkflow_id: os_hygiene_graph\nrun_date: 2026-05-20\nstatus: blocked_review_required\nduration_seconds: 18.6\n---\n"
        "# OS Graph Maintenance Run - 2026-05-20\n\n"
        "## Stage Results\n\n"
        "| Stage | Status | Files Scanned | Detail |\n"
        "|-------|--------|--------------|--------|\n"
        "| Stage 1: Vault Hygiene | blocked_review_required | 6324 | review_gated_loose_nodes=144, duplicate_candidates=41 |\n"
        "| Stage 2: Daily Hub Linker | skipped | 0 | skipped because Stage 1 strict review gate failed |\n",
        encoding="utf-8",
    )
    return tmp_vault


@pytest.fixture()
def vault_with_queue(vault_with_run: Path) -> Path:
    """Vault with maintain-run + review queue JSON."""
    queue_path = vault_with_run / "07_LOGS" / "Graph-Reports" / "2026-05-15-loose-node-review-queue.json"
    queue_path.write_text(json.dumps({
        "timestamp": "2026-05-15T17:13:51+00:00",
        "status": "clear",
        "files_scanned": 5387,
        "total_issues": 94,
        "category_counts": {"loose_node": 2, "unresolved_link_target": 50, "ambiguous_link_target_review": 42},
        "node_category_counts": {"daily_note": 22},
        "loose_node_review_count": 0,
        "allowed_decisions": ["keep_and_wire", "keep_excluded", "delete_after_review"],
        "delete_policy": "No automatic delete. Operator approval required.",
        "queue": [],
    }), encoding="utf-8")
    return vault_with_run


# ---------------------------------------------------------------------------
# Authority boundary
# ---------------------------------------------------------------------------

def test_authority_canonical_mutation_always_false(vault_with_queue):
    result = build_graph_hygiene_review_panel(vault_with_queue)
    assert result["authority"]["canonical_mutation_allowed"] is False


def test_authority_delete_always_false(vault_with_queue):
    result = build_graph_hygiene_review_panel(vault_with_queue)
    assert result["authority"]["delete_allowed"] is False


def test_authority_graph_index_write_always_false(vault_with_queue):
    result = build_graph_hygiene_review_panel(vault_with_queue)
    assert result["authority"]["graph_index_write_allowed"] is False


# ---------------------------------------------------------------------------
# Happy path: maintain-run parsing
# ---------------------------------------------------------------------------

def test_reads_latest_run_status(vault_with_run):
    result = build_graph_hygiene_review_panel(vault_with_run)
    assert result["summary"]["latest_run_status"] == "blocked_review_required"


def test_reads_review_gated_loose_nodes(vault_with_run):
    result = build_graph_hygiene_review_panel(vault_with_run)
    assert result["summary"]["review_gated_loose_nodes"] == 144


def test_reads_duplicate_candidates(vault_with_run):
    result = build_graph_hygiene_review_panel(vault_with_run)
    assert result["summary"]["duplicate_candidates"] == 41


def test_run_stages_parsed(vault_with_run):
    result = build_graph_hygiene_review_panel(vault_with_run)
    stages = result["latest_run"]["stages"]
    assert len(stages) >= 1
    assert any("blocked_review_required" in s["status"] for s in stages)


def test_run_duration_parsed(vault_with_run):
    result = build_graph_hygiene_review_panel(vault_with_run)
    assert result["latest_run"]["duration_seconds"] == pytest.approx(18.6)


def test_surface_key_correct(vault_with_queue):
    result = build_graph_hygiene_review_panel(vault_with_queue)
    assert result["surface"] == "graph_hygiene_review_panel"


# ---------------------------------------------------------------------------
# Happy path: review queue parsing
# ---------------------------------------------------------------------------

def test_reads_review_queue_status(vault_with_queue):
    result = build_graph_hygiene_review_panel(vault_with_queue)
    assert result["review_queue"]["status"] == "clear"


def test_reads_review_queue_files_scanned(vault_with_queue):
    result = build_graph_hygiene_review_panel(vault_with_queue)
    assert result["review_queue"]["files_scanned"] == 5387


def test_reads_decision_vocabulary(vault_with_queue):
    result = build_graph_hygiene_review_panel(vault_with_queue)
    assert "keep_and_wire" in result["decision_vocabulary"]


def test_reads_delete_policy(vault_with_queue):
    result = build_graph_hygiene_review_panel(vault_with_queue)
    assert "No automatic delete" in result["delete_policy"]


def test_reads_category_counts(vault_with_queue):
    result = build_graph_hygiene_review_panel(vault_with_queue)
    counts = result["review_queue"]["category_counts"]
    assert counts["loose_node"] == 2
    assert counts["unresolved_link_target"] == 50


def test_artifact_paths_populated(vault_with_queue):
    result = build_graph_hygiene_review_panel(vault_with_queue)
    paths = result["artifact_paths"]
    assert paths["maintain_run"] is not None
    assert paths["review_queue"] is not None


# ---------------------------------------------------------------------------
# Missing directories: fail-open with warnings
# ---------------------------------------------------------------------------

def test_missing_maintain_runs_dir_produces_warning(tmp_path):
    reports_dir = tmp_path / "07_LOGS" / "Graph-Reports"
    reports_dir.mkdir(parents=True)
    result = build_graph_hygiene_review_panel(tmp_path)
    assert result["warnings"]
    assert any("Maintain-Runs" in w for w in result["warnings"])


def test_missing_graph_reports_dir_produces_warning(tmp_path):
    maintain_dir = tmp_path / "07_LOGS" / "Maintain-Runs"
    maintain_dir.mkdir(parents=True)
    result = build_graph_hygiene_review_panel(tmp_path)
    assert result["warnings"]
    assert any("Graph-Reports" in w for w in result["warnings"])


def test_missing_both_dirs_does_not_crash(tmp_path):
    # No log dirs at all — should not raise
    (tmp_path / "07_LOGS").mkdir()
    result = build_graph_hygiene_review_panel(tmp_path)
    assert result["authority"]["canonical_mutation_allowed"] is False


def test_empty_maintain_runs_dir_produces_warning(tmp_vault):
    result = build_graph_hygiene_review_panel(tmp_vault)
    assert any("Maintain-Runs" in w or "os-hygiene-graph-run" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Malformed inputs: fail-open
# ---------------------------------------------------------------------------

def test_malformed_json_queue_produces_warning(vault_with_run: Path):
    bad = vault_with_run / "07_LOGS" / "Graph-Reports" / "2026-01-01-loose-node-review-queue.json"
    bad.write_text("{not valid json", encoding="utf-8")
    result = build_graph_hygiene_review_panel(vault_with_run)
    # Should produce a warning but not crash
    assert isinstance(result["warnings"], list)
    assert result["authority"]["canonical_mutation_allowed"] is False


def test_missing_frontmatter_run_still_parses(tmp_vault: Path):
    run_md = tmp_vault / "07_LOGS" / "Maintain-Runs" / "2026-05-01-os-hygiene-graph-run.md"
    run_md.write_text(
        "# OS Graph Maintenance Run - 2026-05-01\n\n"
        "No frontmatter here. Status is unknown.\n\n"
        "| Stage 1: Vault Hygiene | blocked | 1000 | review_gated_loose_nodes=10, duplicate_candidates=3 |\n",
        encoding="utf-8",
    )
    result = build_graph_hygiene_review_panel(tmp_vault)
    assert result["latest_run"]["review_gated_loose_nodes"] == 10
    assert result["latest_run"]["duplicate_candidates"] == 3


# ---------------------------------------------------------------------------
# Picks LATEST file when multiple exist
# ---------------------------------------------------------------------------

def test_picks_latest_run_when_multiple(tmp_vault: Path):
    for date, count in [("2026-05-01", 5), ("2026-05-20", 50)]:
        (tmp_vault / "07_LOGS" / "Maintain-Runs" / f"{date}-os-hygiene-graph-run.md").write_text(
            f"---\nworkflow_id: os_hygiene_graph\nrun_date: {date}\nstatus: blocked_review_required\nduration_seconds: 1.0\n---\n"
            f"| Stage 1: Vault Hygiene | blocked | 100 | review_gated_loose_nodes={count}, duplicate_candidates=0 |\n",
            encoding="utf-8",
        )
    result = build_graph_hygiene_review_panel(tmp_vault)
    assert result["latest_run"]["run_date"] == "2026-05-20"
    assert result["summary"]["review_gated_loose_nodes"] == 50


def test_picks_latest_queue_when_multiple(vault_with_run: Path):
    for date, scanned in [("2026-04-01", 111), ("2026-05-15", 999)]:
        p = vault_with_run / "07_LOGS" / "Graph-Reports" / f"{date}-loose-node-review-queue.json"
        p.write_text(json.dumps({
            "status": "clear", "files_scanned": scanned, "total_issues": 0,
            "category_counts": {}, "loose_node_review_count": 0,
            "allowed_decisions": [], "queue": [],
        }), encoding="utf-8")
    result = build_graph_hygiene_review_panel(vault_with_run)
    assert result["review_queue"]["files_scanned"] == 999


# ---------------------------------------------------------------------------
# attention_required flag
# ---------------------------------------------------------------------------

def test_attention_required_true_when_blocked(vault_with_run):
    result = build_graph_hygiene_review_panel(vault_with_run)
    assert result["summary"]["attention_required"] is True


def test_attention_required_false_when_clear(tmp_vault: Path):
    run_md = tmp_vault / "07_LOGS" / "Maintain-Runs" / "2026-05-20-os-hygiene-graph-run.md"
    run_md.write_text(
        "---\nworkflow_id: os_hygiene_graph\nrun_date: 2026-05-20\nstatus: completed\nduration_seconds: 10.0\n---\n"
        "| Stage 1: Vault Hygiene | completed | 1000 | review_gated_loose_nodes=0, duplicate_candidates=0 |\n",
        encoding="utf-8",
    )
    result = build_graph_hygiene_review_panel(tmp_vault)
    assert result["summary"]["attention_required"] is False
