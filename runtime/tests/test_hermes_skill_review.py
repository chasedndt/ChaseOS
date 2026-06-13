"""
test_hermes_skill_review.py — Tests for Hermes Skill Quarantine Review workflow

Covers:
  TestCandidateDetection     (6 tests) — _is_skill_candidate filter logic
  TestQuarantineScan         (6 tests) — _scan_quarantine path handling
  TestReportBuilder          (4 tests) — _build_review_report content
  TestRunHandler             (8 tests) — run_hermes_skill_review end-to-end
  TestEngineWiring           (3 tests) — _resolve_workflow_handler dispatch
  TestHermesWatchDispatch    (3 tests) — _TASK_DISPATCH idea-graduation entry
  TestMemoryExportCLI        (4 tests) — cmd_memory_export function
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_HERE = Path(__file__).resolve()
_VAULT_ROOT = _HERE.parents[2]
if str(_VAULT_ROOT) not in sys.path:
    sys.path.insert(0, str(_VAULT_ROOT))

from runtime.workflows.hermes_skill_review import (
    WorkflowExecutionError,
    _build_review_report,
    _is_skill_candidate,
    _scan_quarantine,
    run_hermes_skill_review,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "00_HOME").mkdir()
    (vault / "00_HOME" / "Now.md").write_text("# Now\n\nDate: 2026-04-29\n")
    (vault / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    (vault / "07_LOGS" / "Skill-Review").mkdir(parents=True)
    return vault


def _write_quarantine_item(
    vault: Path,
    filename: str,
    meta: dict,
    input_class: str = "digest",
) -> Path:
    q_dir = vault / "03_INPUTS" / "00_QUARANTINE" / input_class
    q_dir.mkdir(parents=True, exist_ok=True)
    content_path = q_dir / filename
    content_path.write_text("Content here.", encoding="utf-8")
    meta_path = q_dir / f"{filename}.meta.json"
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    return content_path


def _ai_meta(title: str = "Test") -> dict:
    return {
        "title": title,
        "origin_kind": "ai-generated",
        "input_class": "digest",
        "source": "hermes-research-synthesis:ws-test",
        "captured_at": "2026-04-29T12:00:00Z",
    }


def _human_meta(title: str = "Human") -> dict:
    return {
        "title": title,
        "origin_kind": "human",
        "input_class": "source",
        "source": "operator-upload",
        "captured_at": "2026-04-29T12:00:00Z",
    }


# ── TestCandidateDetection ────────────────────────────────────────────────────

class TestCandidateDetection:
    def test_ai_generated_is_candidate(self):
        assert _is_skill_candidate({"origin_kind": "ai-generated"})

    def test_synthesized_is_candidate(self):
        assert _is_skill_candidate({"origin_kind": "synthesized"})

    def test_generated_ideas_class_is_candidate(self):
        assert _is_skill_candidate({"input_class": "generated-ideas"})

    def test_hermes_source_prefix_is_candidate(self):
        assert _is_skill_candidate({"source": "hermes-research-synthesis:ws"})

    def test_hermes_underscore_prefix_is_candidate(self):
        assert _is_skill_candidate({"source": "hermes_watch_output"})

    def test_human_origin_not_candidate(self):
        assert not _is_skill_candidate(_human_meta())


# ── TestQuarantineScan ────────────────────────────────────────────────────────

class TestQuarantineScan:
    def test_returns_empty_when_no_quarantine(self, tmp_path):
        vault = _make_vault(tmp_path)
        candidates, scanned = _scan_quarantine(vault, max_scan=50, filter_class=None)
        assert candidates == []
        assert scanned == 0

    def test_detects_ai_generated_item(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_quarantine_item(vault, "item1.md", _ai_meta("Item 1"))
        candidates, scanned = _scan_quarantine(vault, max_scan=50, filter_class=None)
        assert len(candidates) == 1
        assert scanned == 1

    def test_skips_human_item(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_quarantine_item(vault, "human.md", _human_meta("Human"), input_class="source")
        candidates, scanned = _scan_quarantine(vault, max_scan=50, filter_class=None)
        assert len(candidates) == 0
        assert scanned == 1

    def test_max_scan_respected(self, tmp_path):
        vault = _make_vault(tmp_path)
        for i in range(5):
            _write_quarantine_item(vault, f"item{i}.md", _ai_meta(f"Item {i}"))
        candidates, scanned = _scan_quarantine(vault, max_scan=2, filter_class=None)
        assert scanned == 2

    def test_filter_class_applied(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_quarantine_item(vault, "ai.md", _ai_meta("AI"), input_class="digest")
        _write_quarantine_item(vault, "ideas.md",
                               {"origin_kind": "ai-generated", "input_class": "generated-ideas"},
                               input_class="generated-ideas")
        candidates, _ = _scan_quarantine(vault, max_scan=50, filter_class="digest")
        assert all(c["meta"].get("input_class") == "digest" for c in candidates)

    def test_corrupt_meta_silently_skipped(self, tmp_path):
        vault = _make_vault(tmp_path)
        q_dir = vault / "03_INPUTS" / "00_QUARANTINE" / "digest"
        q_dir.mkdir(parents=True)
        (q_dir / "bad.md").write_text("content")
        (q_dir / "bad.md.meta.json").write_text("NOT JSON")
        candidates, scanned = _scan_quarantine(vault, max_scan=50, filter_class=None)
        assert len(candidates) == 0


# ── TestReportBuilder ─────────────────────────────────────────────────────────

class TestReportBuilder:
    def test_empty_candidates_no_error(self):
        report = _build_review_report([], 0)
        assert "No Candidates Found" in report

    def test_candidates_listed(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_quarantine_item(vault, "item.md", _ai_meta("My Item"))
        candidates, _ = _scan_quarantine(vault, max_scan=50, filter_class=None)
        report = _build_review_report(candidates, 1)
        assert "Candidates for Operator Review" in report
        assert "My Item" in report

    def test_governance_boundary_present(self):
        report = _build_review_report([], 5)
        assert "Governance Boundary" in report
        assert "not promoted" in report or "not auto-promoted" in report or "explicit operator" in report

    def test_scanned_count_in_header(self):
        report = _build_review_report([], 12)
        assert "12" in report


# ── TestRunHandler ────────────────────────────────────────────────────────────

class TestRunHandler:
    def test_returns_items_scanned(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = run_hermes_skill_review({}, vault)
        assert "items_scanned" in result
        assert result["items_scanned"] == 0

    def test_returns_candidates_count(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = run_hermes_skill_review({}, vault)
        assert result["candidates"] == 0

    def test_writes_report_when_candidates_found(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_quarantine_item(vault, "ai.md", _ai_meta("AI Content"))
        result = run_hermes_skill_review({}, vault)
        assert result["candidates"] == 1
        assert result["report_path"] is not None
        assert "Skill-Review" in result["report_path"]

    def test_no_report_written_when_zero_candidates(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = run_hermes_skill_review({}, vault)
        assert result["report_path"] is None

    def test_writebacks_contains_audit(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = run_hermes_skill_review({}, vault)
        assert "writebacks" in result
        audit_wb = result["writebacks"][0]
        assert "07_LOGS/Agent-Activity" in audit_wb["path"]
        assert "hermes_skill_review" in audit_wb["content"]

    def test_audit_has_frontmatter(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = run_hermes_skill_review({}, vault)
        content = result["writebacks"][0]["content"]
        assert "workflow: hermes_skill_review" in content
        assert "authority: read-scan-report-only" in content

    def test_max_scan_input_respected(self, tmp_path):
        vault = _make_vault(tmp_path)
        for i in range(10):
            _write_quarantine_item(vault, f"item{i}.md", _ai_meta(f"Item {i}"))
        result = run_hermes_skill_review({"max_scan": 3}, vault)
        assert result["items_scanned"] == 3

    def test_min_items_suppresses_report(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_quarantine_item(vault, "one.md", _ai_meta("One"))
        result = run_hermes_skill_review({"min_items": 5}, vault)
        # Only 1 candidate, min=5, so no report written
        assert result["report_path"] is None


# ── TestEngineWiring ──────────────────────────────────────────────────────────

class TestEngineWiring:
    def test_engine_resolves_hermes_skill_review(self):
        from runtime.aor.engine import _resolve_workflow_handler
        handler = _resolve_workflow_handler("hermes_skill_review")
        assert handler is not None

    def test_handler_is_callable(self):
        from runtime.aor.engine import _resolve_workflow_handler
        handler = _resolve_workflow_handler("hermes_skill_review")
        assert callable(handler)

    def test_handler_is_correct_function(self):
        from runtime.aor.engine import _resolve_workflow_handler
        from runtime.workflows.hermes_skill_review import run_hermes_skill_review
        assert _resolve_workflow_handler("hermes_skill_review") is run_hermes_skill_review


# ── TestHermesWatchDispatch ───────────────────────────────────────────────────

class TestHermesWatchDispatch:
    def test_idea_graduation_in_dispatch(self):
        from runtime.workflows.hermes_watch import _TASK_DISPATCH
        assert "idea-graduation" in _TASK_DISPATCH

    def test_dispatch_fn_callable(self):
        from runtime.workflows.hermes_watch import _TASK_DISPATCH
        assert callable(_TASK_DISPATCH["idea-graduation"])

    def test_dispatch_runs_skill_review(self, tmp_path):
        vault = _make_vault(tmp_path)
        task = {"task_id": "t-001", "notes": "", "request": ""}
        from runtime.workflows.hermes_watch import _TASK_DISPATCH
        fn = _TASK_DISPATCH["idea-graduation"]
        result = fn(task, vault, False)
        assert "candidates" in result


# ── TestMemoryExportCLI ───────────────────────────────────────────────────────

class TestMemoryExportCLI:
    def test_cmd_exists(self):
        from runtime.cli.main import cmd_memory_export
        assert callable(cmd_memory_export)

    def test_json_output_shape(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        import argparse
        from runtime.cli.main import cmd_memory_export
        ns = argparse.Namespace(runtime_id="rt1", vault_root=str(vault), output_json=True)
        import io
        captured = []
        with patch("builtins.print", side_effect=lambda *a, **k: captured.append(str(a[0]))):
            with patch("runtime.cli.main._resolve_vault", return_value=vault):
                result = cmd_memory_export(ns)
        assert result == 0
        if captured:
            data = json.loads(captured[0])
            assert data["runtime_id"] == "rt1"

    def test_human_output_no_error(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        import argparse
        from runtime.cli.main import cmd_memory_export
        ns = argparse.Namespace(runtime_id="rt1", vault_root=str(vault), output_json=False)
        lines = []
        with patch("builtins.print", side_effect=lambda *a, **k: lines.append(str(a[0]))):
            with patch("runtime.cli.main._resolve_vault", return_value=vault):
                result = cmd_memory_export(ns)
        assert result == 0
        assert any("Memory Export" in line for line in lines)

    def test_export_parser_wired(self):
        from runtime.cli.main import build_parser
        parser = build_parser()
        args = parser.parse_args(["memory", "export", "hermes"])
        assert args.runtime_id == "hermes"
        assert hasattr(args, "func")
