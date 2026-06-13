"""Tests for Studio SiteOps Inspector."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from runtime.studio import siteops_inspector as inspector


def _test_vault(name: str) -> Path:
    path = (
        Path(__file__).resolve().parents[2]
        / ".pytest-tmp"
        / "studio-siteops-inspector"
        / name
    )
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_run(vault: Path, tenant: str, workspace: str, run_id: str, data: dict) -> Path:
    d = vault / "07_LOGS" / "SiteOps-Runs" / tenant / workspace
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{run_id}.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _write_approval(vault: Path, tenant: str, workspace: str, approval_id: str, data: dict) -> Path:
    d = vault / "07_LOGS" / "SiteOps-Approvals" / tenant / workspace
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{approval_id}.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _write_audit(vault: Path, tenant: str, workspace: str, run_id: str, events: list[dict]) -> None:
    d = vault / "07_LOGS" / "SiteOps-Audits" / tenant / workspace
    d.mkdir(parents=True, exist_ok=True)
    lines = "\n".join(json.dumps(e) for e in events)
    (d / f"{run_id}.jsonl").write_text(lines + "\n", encoding="utf-8")


def _base_run(run_id: str, workflow_id: str = "perplexity-research-capture",
              status: str = "succeeded", started: str = "2026-04-30T06:00:00+00:00") -> dict:
    return {
        "run_id": run_id,
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "workflow_id": workflow_id,
        "skill_id": "research.capture",
        "mode": "dry_run",
        "status": status,
        "started_at": started,
        "ended_at": started,
    }


def _base_approval(approval_id: str, run_id: str, status: str = "pending",
                   action: str = "external_share") -> dict:
    return {
        "approval_id": approval_id,
        "tenant_id": "local",
        "workspace_id": "default",
        "user_id": "local-user",
        "run_id": run_id,
        "workflow_id": "perplexity-research-capture",
        "action": action,
        "risk_level": "low",
        "approval_reason": "test",
        "requested_by": "operator",
        "required_approver_role": "approver",
        "status": status,
        "decided_by": None,
        "decided_at": None,
    }


# ── TestBoundarySentinel ──────────────────────────────────────────────────────

class TestBoundarySentinel(unittest.TestCase):
    def test_no_write_flags(self):
        b = inspector._BOUNDARY
        self.assertFalse(b["writes_run_records"])
        self.assertFalse(b["writes_approval_decisions"])
        self.assertFalse(b["executes_workflows"])
        self.assertFalse(b["triggers_browser"])
        self.assertFalse(b["canonical_mutation_allowed"])

    def test_read_flags(self):
        b = inspector._BOUNDARY
        self.assertTrue(b["reads_run_records"])
        self.assertTrue(b["reads_audit_events"])
        self.assertTrue(b["reads_approval_records"])


# ── TestLoadHelpers ───────────────────────────────────────────────────────────

class TestLoadHelpers(unittest.TestCase):
    def test_load_json_missing_returns_none(self):
        vault = _test_vault("helpers-missing")
        self.assertIsNone(inspector._load_json(vault / "no.json"))

    def test_load_json_valid(self):
        vault = _test_vault("helpers-json-valid")
        p = vault / "r.json"
        p.write_text(json.dumps({"run_id": "r1"}), encoding="utf-8")
        self.assertEqual(inspector._load_json(p)["run_id"], "r1")

    def test_load_json_malformed_returns_none(self):
        vault = _test_vault("helpers-json-bad")
        p = vault / "r.json"
        p.write_text("{bad", encoding="utf-8")
        self.assertIsNone(inspector._load_json(p))

    def test_load_jsonl_valid(self):
        vault = _test_vault("helpers-jsonl-valid")
        p = vault / "a.jsonl"
        p.write_text('{"e":1}\n{"e":2}\n', encoding="utf-8")
        self.assertEqual(len(inspector._load_jsonl(p)), 2)

    def test_load_jsonl_skips_malformed(self):
        vault = _test_vault("helpers-jsonl-bad")
        p = vault / "a.jsonl"
        p.write_text('{"e":1}\nbad\n{"e":3}\n', encoding="utf-8")
        self.assertEqual(len(inspector._load_jsonl(p)), 2)


# ── TestGetSiteOpsSummary ─────────────────────────────────────────────────────

class TestGetSiteOpsSummary(unittest.TestCase):
    def test_empty_vault_returns_ok_zeros(self):
        vault = _test_vault("summary-empty")
        result = inspector.get_siteops_summary(vault)
        self.assertTrue(result["ok"])
        self.assertEqual(result["surface"], "studio_siteops_inspector")
        self.assertEqual(result["total_runs"], 0)
        self.assertEqual(result["total_approvals"], 0)
        self.assertEqual(result["pending_approvals"], 0)

    def test_runs_counted_by_status(self):
        vault = _test_vault("summary-runs")
        _write_run(vault, "local", "default", "r1", _base_run("r1", status="succeeded"))
        _write_run(vault, "local", "default", "r2", _base_run("r2", status="approval_needed"))
        _write_run(vault, "local", "default", "r3", _base_run("r3", status="approval_needed"))
        result = inspector.get_siteops_summary(vault)
        self.assertEqual(result["total_runs"], 3)
        self.assertEqual(result["runs_by_status"]["succeeded"], 1)
        self.assertEqual(result["runs_by_status"]["approval_needed"], 2)

    def test_candidate_runs_counted(self):
        vault = _test_vault("summary-candidate")
        _write_run(vault, "local", "default", "r1", _base_run("r1", workflow_id="browser_skill_candidate.promotion"))
        _write_run(vault, "local", "default", "r2", _base_run("r2", workflow_id="other"))
        result = inspector.get_siteops_summary(vault)
        self.assertEqual(result["candidate_promotion_runs"], 1)

    def test_approvals_counted_by_status(self):
        vault = _test_vault("summary-approvals")
        _write_approval(vault, "local", "default", "a1", _base_approval("a1", "r1", status="pending"))
        _write_approval(vault, "local", "default", "a2", _base_approval("a2", "r2", status="pending"))
        _write_approval(vault, "local", "default", "a3", _base_approval("a3", "r3", status="approved"))
        result = inspector.get_siteops_summary(vault)
        self.assertEqual(result["total_approvals"], 3)
        self.assertEqual(result["pending_approvals"], 2)
        self.assertEqual(result["approvals_by_status"]["approved"], 1)

    def test_boundary_present(self):
        vault = _test_vault("summary-boundary")
        result = inspector.get_siteops_summary(vault)
        self.assertEqual(result["boundary"], inspector._BOUNDARY)

    def test_latest_run_at_populated(self):
        vault = _test_vault("summary-latest")
        _write_run(vault, "local", "default", "r1", _base_run("r1", started="2026-04-01T00:00:00+00:00"))
        _write_run(vault, "local", "default", "r2", _base_run("r2", started="2026-04-30T06:00:00+00:00"))
        result = inspector.get_siteops_summary(vault)
        self.assertEqual(result["latest_run_at"], "2026-04-30T06:00:00+00:00")


# ── TestListSiteOpsRuns ───────────────────────────────────────────────────────

class TestListSiteOpsRuns(unittest.TestCase):
    def test_empty_vault_returns_ok_empty(self):
        vault = _test_vault("runs-empty")
        result = inspector.list_siteops_runs(vault)
        self.assertTrue(result["ok"])
        self.assertEqual(result["run_count"], 0)
        self.assertEqual(result["runs"], [])

    def test_runs_listed_with_fields(self):
        vault = _test_vault("runs-fields")
        _write_run(vault, "local", "default", "r1", _base_run("r1"))
        result = inspector.list_siteops_runs(vault)
        self.assertEqual(result["run_count"], 1)
        run = result["runs"][0]
        self.assertEqual(run["run_id"], "r1")
        self.assertEqual(run["status"], "succeeded")
        self.assertIn("workflow_id", run)
        self.assertIn("started_at", run)

    def test_workflow_filter_applied(self):
        vault = _test_vault("runs-wf-filter")
        _write_run(vault, "local", "default", "r1", _base_run("r1", workflow_id="perplexity-research-capture"))
        _write_run(vault, "local", "default", "r2", _base_run("r2", workflow_id="gemini-image-edit"))
        result = inspector.list_siteops_runs(vault, workflow_filter="perplexity")
        self.assertEqual(result["run_count"], 1)
        self.assertEqual(result["runs"][0]["run_id"], "r1")

    def test_status_filter_applied(self):
        vault = _test_vault("runs-status-filter")
        _write_run(vault, "local", "default", "r1", _base_run("r1", status="succeeded"))
        _write_run(vault, "local", "default", "r2", _base_run("r2", status="approval_needed"))
        result = inspector.list_siteops_runs(vault, status_filter="approval_needed")
        self.assertEqual(result["run_count"], 1)
        self.assertEqual(result["runs"][0]["run_id"], "r2")

    def test_limit_respected(self):
        vault = _test_vault("runs-limit")
        for i in range(5):
            _write_run(vault, "local", "default", f"r{i}", _base_run(f"r{i}"))
        result = inspector.list_siteops_runs(vault, limit=3)
        self.assertEqual(result["run_count"], 3)

    def test_runs_sorted_newest_first(self):
        vault = _test_vault("runs-sort")
        _write_run(vault, "local", "default", "old", _base_run("old", started="2026-04-01T00:00:00+00:00"))
        _write_run(vault, "local", "default", "new", _base_run("new", started="2026-04-30T06:00:00+00:00"))
        result = inspector.list_siteops_runs(vault)
        self.assertEqual(result["runs"][0]["run_id"], "new")

    def test_boundary_present(self):
        vault = _test_vault("runs-boundary")
        result = inspector.list_siteops_runs(vault)
        self.assertEqual(result["boundary"], inspector._BOUNDARY)


# ── TestListSiteOpsApprovals ──────────────────────────────────────────────────

class TestListSiteOpsApprovals(unittest.TestCase):
    def test_empty_vault_returns_ok_empty(self):
        vault = _test_vault("approvals-empty")
        result = inspector.list_siteops_approvals(vault)
        self.assertTrue(result["ok"])
        self.assertEqual(result["approval_count"], 0)

    def test_approvals_listed_with_fields(self):
        vault = _test_vault("approvals-fields")
        _write_approval(vault, "local", "default", "a1", _base_approval("a1", "r1"))
        result = inspector.list_siteops_approvals(vault)
        self.assertEqual(result["approval_count"], 1)
        a = result["approvals"][0]
        self.assertEqual(a["approval_id"], "a1")
        self.assertEqual(a["status"], "pending")
        self.assertIn("action", a)
        self.assertIn("risk_level", a)

    def test_status_filter_applied(self):
        vault = _test_vault("approvals-status-filter")
        _write_approval(vault, "local", "default", "a1", _base_approval("a1", "r1", status="pending"))
        _write_approval(vault, "local", "default", "a2", _base_approval("a2", "r2", status="approved"))
        result = inspector.list_siteops_approvals(vault, status_filter="pending")
        self.assertEqual(result["approval_count"], 1)
        self.assertEqual(result["approvals"][0]["approval_id"], "a1")

    def test_all_approvals_returned_without_filter(self):
        vault = _test_vault("approvals-all")
        _write_approval(vault, "local", "default", "a1", _base_approval("a1", "r1", status="pending"))
        _write_approval(vault, "local", "default", "a2", _base_approval("a2", "r2", status="approved"))
        result = inspector.list_siteops_approvals(vault)
        self.assertEqual(result["approval_count"], 2)

    def test_boundary_present(self):
        vault = _test_vault("approvals-boundary")
        result = inspector.list_siteops_approvals(vault)
        self.assertEqual(result["boundary"], inspector._BOUNDARY)


# ── TestInspectSiteOpsRun ─────────────────────────────────────────────────────

class TestInspectSiteOpsRun(unittest.TestCase):
    def test_not_found_returns_ok_false(self):
        vault = _test_vault("inspect-not-found")
        result = inspector.inspect_siteops_run(vault, "nonexistent-run-id")
        self.assertFalse(result["ok"])
        self.assertIn("not found", result["error"])

    def test_found_returns_full_record(self):
        vault = _test_vault("inspect-found")
        run_id = "r1"
        _write_run(vault, "local", "default", run_id, _base_run(run_id))
        result = inspector.inspect_siteops_run(vault, run_id)
        self.assertTrue(result["ok"])
        self.assertEqual(result["run"]["run_id"], run_id)
        self.assertIn("audit_events", result)
        self.assertIn("approvals", result)

    def test_audit_events_attached(self):
        vault = _test_vault("inspect-audit")
        run_id = "r1"
        _write_run(vault, "local", "default", run_id, _base_run(run_id))
        _write_audit(vault, "local", "default", run_id, [
            {"event": "started", "ts": "2026-04-30T06:00:00Z"},
            {"event": "approval_created", "ts": "2026-04-30T06:00:01Z"},
            {"event": "ended", "ts": "2026-04-30T06:00:02Z"},
        ])
        result = inspector.inspect_siteops_run(vault, run_id)
        self.assertEqual(result["audit_events_shown"], 3)

    def test_audit_event_limit_respected(self):
        vault = _test_vault("inspect-limit")
        run_id = "r1"
        _write_run(vault, "local", "default", run_id, _base_run(run_id))
        events = [{"event": f"e{i}", "ts": f"2026-04-30T06:00:0{i}Z"} for i in range(5)]
        _write_audit(vault, "local", "default", run_id, events)
        result = inspector.inspect_siteops_run(vault, run_id, audit_event_limit=2)
        self.assertEqual(result["audit_events_shown"], 2)

    def test_matching_approvals_attached(self):
        vault = _test_vault("inspect-approvals")
        run_id = "r1"
        _write_run(vault, "local", "default", run_id, _base_run(run_id))
        _write_approval(vault, "local", "default", "a1", _base_approval("a1", run_id))
        result = inspector.inspect_siteops_run(vault, run_id)
        self.assertEqual(result["approval_count"], 1)
        self.assertEqual(result["approvals"][0]["approval_id"], "a1")

    def test_boundary_present(self):
        vault = _test_vault("inspect-boundary")
        run_id = "r1"
        _write_run(vault, "local", "default", run_id, _base_run(run_id))
        result = inspector.inspect_siteops_run(vault, run_id)
        self.assertEqual(result["boundary"], inspector._BOUNDARY)


# ── TestLiveVaultSmoke ────────────────────────────────────────────────────────

class TestLiveVaultSmoke(unittest.TestCase):
    """Reads from the real vault. Validates shape only."""

    VAULT = Path(__file__).resolve().parents[2]

    def test_get_siteops_summary_ok(self):
        result = inspector.get_siteops_summary(self.VAULT)
        self.assertTrue(result["ok"])
        self.assertIn("total_runs", result)
        self.assertIn("total_approvals", result)
        self.assertIn("pending_approvals", result)
        self.assertIn("candidate_promotion_runs", result)

    def test_list_siteops_runs_ok(self):
        result = inspector.list_siteops_runs(self.VAULT)
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(result["run_count"], 1)

    def test_list_siteops_approvals_ok(self):
        result = inspector.list_siteops_approvals(self.VAULT)
        self.assertTrue(result["ok"])
        self.assertGreaterEqual(result["approval_count"], 1)

    def test_list_pending_approvals(self):
        result = inspector.list_siteops_approvals(self.VAULT, status_filter="pending")
        self.assertTrue(result["ok"])
        for a in result["approvals"]:
            self.assertEqual(a["status"], "pending")

    def test_inspect_known_candidate_run(self):
        run_id = "siteops_candidate_20260430_063855_candidate-browser-runtime-20260430-022607-example-com"
        result = inspector.inspect_siteops_run(self.VAULT, run_id)
        self.assertTrue(result["ok"])
        self.assertEqual(result["run"]["run_id"], run_id)
        self.assertGreaterEqual(result["audit_events_shown"], 0)
        self.assertGreaterEqual(result["approval_count"], 1)
