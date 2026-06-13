"""
test_studio_aor_pipeline_monitor.py — Tests for Studio AOR Pipeline Monitor

Covers:
  TestListExecutions   (6 tests) — list_recent_executions
  TestInspectExecution (4 tests) — inspect_execution
  TestGetSummary       (5 tests) — get_execution_summary
  TestBoundary         (2 tests) — _BOUNDARY sentinel
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.studio.aor_pipeline_monitor import (
    list_recent_executions,
    inspect_execution,
    get_execution_summary,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    (vault / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    return vault


def _write_audit(
    vault: Path,
    filename: str,
    workflow_id: str = "operator_today",
    status: str = "success",
    stage_reached: str = "audit_record",
    escalation_reason=None,
    error=None,
    inputs_summary=None,
    outputs=None,
) -> Path:
    record = {
        "audit_id": f"audit-{filename[:8]}",
        "workflow_id": workflow_id,
        "timestamp_utc": "2026-04-30T10:00:00Z",
        "status": status,
        "stage_reached": stage_reached,
        "escalation_reason": escalation_reason,
        "error": error,
        "inputs_summary": inputs_summary or {"date": "2026-04-30"},
        "outputs": outputs or {"run": {"handler_status": "completed"}},
    }
    path = vault / "07_LOGS" / "Agent-Activity" / filename
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


# ── TestListExecutions ────────────────────────────────────────────────────────

class TestListExecutions:
    def test_empty_when_no_audit_dir(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        result = list_recent_executions(vault)
        assert result["ok"] is True
        assert result["execution_count"] == 0
        assert result["executions"] == []

    def test_detects_audit_record(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_audit(vault, "20260430-100000__operator_today__aabbccdd.json")
        result = list_recent_executions(vault)
        assert result["execution_count"] == 1
        assert result["executions"][0]["workflow_id"] == "operator_today"

    def test_sorted_newest_first(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_audit(vault, "20260430-080000__operator_today__aa.json")
        _write_audit(vault, "20260430-120000__operator_today__bb.json")
        result = list_recent_executions(vault)
        assert result["executions"][0]["filename"] > result["executions"][1]["filename"]

    def test_limit_applied(self, tmp_path):
        vault = _make_vault(tmp_path)
        for i in range(5):
            _write_audit(vault, f"20260430-0{i}0000__wf__id{i}.json")
        result = list_recent_executions(vault, limit=3)
        assert result["execution_count"] == 3

    def test_workflow_filter(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_audit(vault, "20260430-100000__operator_today__aa.json", workflow_id="operator_today")
        _write_audit(vault, "20260430-110000__graph_hygiene__bb.json", workflow_id="graph_hygiene")
        result = list_recent_executions(vault, workflow_filter="graph_hygiene")
        assert result["execution_count"] == 1
        assert result["executions"][0]["workflow_id"] == "graph_hygiene"

    def test_status_filter(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_audit(vault, "20260430-100000__wf__aa.json", status="success")
        _write_audit(vault, "20260430-110000__wf__bb.json", status="escalated")
        result = list_recent_executions(vault, status_filter="escalated")
        assert result["execution_count"] == 1
        assert result["executions"][0]["status"] == "escalated"


# ── TestInspectExecution ──────────────────────────────────────────────────────

class TestInspectExecution:
    def test_missing_file_returns_error(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = inspect_execution(vault, "nonexistent.json")
        assert result["ok"] is False
        assert "not found" in result["error"]

    def test_ok_result(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_audit(vault, "20260430-100000__operator_today__aa.json")
        result = inspect_execution(vault, "20260430-100000__operator_today__aa.json")
        assert result["ok"] is True
        assert result["workflow_id"] == "operator_today"

    def test_outputs_keys_only(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_audit(vault, "20260430-100000__wf__aa.json", outputs={"run": {"x": 1}, "writeback": {"y": 2}})
        result = inspect_execution(vault, "20260430-100000__wf__aa.json")
        assert "run" in result["outputs_keys"]
        assert "writeback" in result["outputs_keys"]
        assert "run" not in result  # raw run content not exposed

    def test_inputs_summary_present(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_audit(vault, "20260430-100000__wf__aa.json", inputs_summary={"date": "2026-04-30", "focus": "testing"})
        result = inspect_execution(vault, "20260430-100000__wf__aa.json")
        assert result["inputs_summary"]["focus"] == "testing"


# ── TestGetSummary ────────────────────────────────────────────────────────────

class TestGetSummary:
    def test_empty_when_no_audit_dir(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        result = get_execution_summary(vault)
        assert result["ok"] is True
        assert result["total_scanned"] == 0
        assert result["by_workflow"] == {}

    def test_counts_by_workflow(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_audit(vault, "20260430-100000__operator_today__aa.json", workflow_id="operator_today", status="success")
        _write_audit(vault, "20260430-110000__operator_today__bb.json", workflow_id="operator_today", status="success")
        _write_audit(vault, "20260430-120000__graph_hygiene__cc.json", workflow_id="graph_hygiene", status="success")
        result = get_execution_summary(vault)
        assert result["by_workflow"]["operator_today"]["total"] == 2
        assert result["by_workflow"]["graph_hygiene"]["total"] == 1

    def test_counts_by_status(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_audit(vault, "20260430-100000__wf__aa.json", status="success")
        _write_audit(vault, "20260430-110000__wf__bb.json", status="escalated")
        _write_audit(vault, "20260430-120000__wf__cc.json", status="success")
        result = get_execution_summary(vault)
        assert result["by_status"]["success"] == 2
        assert result["by_status"]["escalated"] == 1

    def test_success_counter_in_workflow_block(self, tmp_path):
        vault = _make_vault(tmp_path)
        _write_audit(vault, "20260430-100000__wf__aa.json", workflow_id="wf", status="success")
        _write_audit(vault, "20260430-110000__wf__bb.json", workflow_id="wf", status="escalated")
        result = get_execution_summary(vault)
        assert result["by_workflow"]["wf"]["success"] == 1
        assert result["by_workflow"]["wf"]["escalated"] == 1

    def test_limit_applied_to_scan(self, tmp_path):
        vault = _make_vault(tmp_path)
        for i in range(10):
            _write_audit(vault, f"20260430-0{i}0000__wf__id{i:02d}.json")
        result = get_execution_summary(vault, limit=5)
        assert result["total_scanned"] == 5


# ── TestBoundary ──────────────────────────────────────────────────────────────

class TestBoundary:
    def test_list_has_boundary(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = list_recent_executions(vault)
        assert result["boundary"]["writes_audit_files"] is False
        assert result["boundary"]["triggers_pipelines"] is False

    def test_summary_has_boundary(self, tmp_path):
        vault = _make_vault(tmp_path)
        result = get_execution_summary(vault)
        assert result["boundary"]["canonical_mutation_allowed"] is False
