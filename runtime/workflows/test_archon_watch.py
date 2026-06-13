"""
test_archon_watch.py — Tests for Archon Bus Watch Loop

Coverage:
  - _parse_notes: key:value extraction
  - _task_type_from_task: notes annotation, intent fallback, unknown fallback
  - _build_bounded_analysis_summary: structure, shorten
  - _build_bounded_analysis_audit: frontmatter, boundary statement
  - _dispatch_bounded_analysis: claim-and-dispatch, skip on claim failure, audit writeback
  - _dispatch_implementation / _dispatch_code_review / _dispatch_architecture_review: task_type routing
  - _escalate_unhandled: bus blocked, reason message
  - _run_one_cycle: heartbeat upsert, empty vault, dispatch, escalation, max_tasks_per_cycle
  - run_archon_watch: single cycle (interval_seconds=None), multi-cycle loop, invalid interval
  - Engine wiring: _resolve_workflow_handler returns run_archon_watch
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

from runtime.workflows.archon_watch import (
    WorkflowExecutionError,
    _parse_notes,
    _task_type_from_task,
    _normalize_task_type,
    _shorten,
    _safe_task_id_fragment,
    _build_bounded_analysis_summary,
    _build_bounded_analysis_audit,
    _dispatch_bounded_analysis,
    _dispatch_implementation,
    _dispatch_code_review,
    _dispatch_architecture_review,
    _escalate_unhandled,
    _TASK_DISPATCH,
    _run_one_cycle,
    run_archon_watch,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    """Create minimal vault structure for tests."""
    (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    (tmp_path / "00_HOME").mkdir(parents=True)
    (tmp_path / "00_HOME" / "Now.md").write_text("# Now\n", encoding="utf-8")
    (tmp_path / "runtime" / "agent_bus").mkdir(parents=True)
    return tmp_path


def _make_task(
    *,
    task_id: str = "task-001",
    intent: str = "implementation",
    request: str = "implement something",
    expected_output: str = "code",
    notes: str = "",
    recipient: str = "Archon",
) -> dict:
    return {
        "task_id": task_id,
        "intent": intent,
        "request": request,
        "expected_output": expected_output,
        "notes": notes,
        "recipient": recipient,
        "status": "open",
    }


# ── TestParseNotes ─────────────────────────────────────────────────────────────

class TestParseNotes(unittest.TestCase):
    def test_empty_notes(self):
        self.assertEqual(_parse_notes(None), {})
        self.assertEqual(_parse_notes(""), {})

    def test_single_annotation(self):
        result = _parse_notes("task_type: implementation")
        self.assertEqual(result["task_type"], "implementation")

    def test_multiple_annotations(self):
        notes = "task_type: code-review\nworkflow: archon_watch\nextra: value"
        result = _parse_notes(notes)
        self.assertEqual(result["task_type"], "code-review")
        self.assertEqual(result["workflow"], "archon_watch")
        self.assertEqual(result["extra"], "value")

    def test_keys_lowercased(self):
        result = _parse_notes("Task_Type: implementation")
        self.assertIn("task_type", result)

    def test_line_without_colon_ignored(self):
        result = _parse_notes("no colon here\ntask_type: implementation")
        self.assertEqual(result["task_type"], "implementation")
        self.assertEqual(len(result), 1)

    def test_value_with_colon_preserved(self):
        result = _parse_notes("path: runtime/agent_bus/bus.py:line:42")
        self.assertEqual(result["path"], "runtime/agent_bus/bus.py:line:42")


# ── TestTaskTypeFromTask ───────────────────────────────────────────────────────

class TestTaskTypeFromTask(unittest.TestCase):
    def test_notes_annotation_takes_priority(self):
        task = _make_task(intent="review", notes="task_type: implementation")
        self.assertEqual(_task_type_from_task(task), "implementation")

    def test_implementation_intent(self):
        task = _make_task(intent="implementation")
        self.assertEqual(_task_type_from_task(task), "implementation")

    def test_code_review_intent(self):
        task = _make_task(intent="code-review")
        self.assertEqual(_task_type_from_task(task), "code-review")

    def test_code_review_underscore_intent(self):
        task = _make_task(intent="code_review")
        self.assertEqual(_task_type_from_task(task), "code-review")

    def test_architecture_review_intent(self):
        task = _make_task(intent="architecture-review")
        self.assertEqual(_task_type_from_task(task), "architecture-review")

    def test_architecture_review_underscore_intent(self):
        task = _make_task(intent="architecture_review")
        self.assertEqual(_task_type_from_task(task), "architecture-review")

    def test_unknown_intent_falls_back(self):
        task = _make_task(intent="planningXYZ")
        self.assertEqual(_task_type_from_task(task), "unknown")

    def test_notes_annotation_overrides_intent(self):
        task = _make_task(intent="code-review", notes="task_type: architecture-review")
        self.assertEqual(_task_type_from_task(task), "architecture-review")


# ── TestNormalizeAndHelpers ───────────────────────────────────────────────────

class TestNormalizeAndHelpers(unittest.TestCase):
    def test_normalize_replaces_underscore(self):
        self.assertEqual(_normalize_task_type("code_review"), "code-review")

    def test_normalize_empty_returns_unknown(self):
        self.assertEqual(_normalize_task_type(None), "unknown")
        self.assertEqual(_normalize_task_type(""), "unknown")

    def test_shorten_short_value(self):
        self.assertEqual(_shorten("hello"), "hello")

    def test_shorten_truncates(self):
        long_val = "x" * 1000
        result = _shorten(long_val, limit=10)
        self.assertTrue(result.endswith("..."))
        self.assertLessEqual(len(result), 14)

    def test_safe_task_id_fragment_cleans_chars(self):
        result = _safe_task_id_fragment("task/001@abc!")
        self.assertNotIn("/", result)
        self.assertNotIn("@", result)
        self.assertNotIn("!", result)

    def test_safe_task_id_fragment_max_24(self):
        result = _safe_task_id_fragment("a" * 50)
        self.assertLessEqual(len(result), 24)


# ── TestBoundedAnalysisSummary ────────────────────────────────────────────────

class TestBoundedAnalysisSummary(unittest.TestCase):
    def test_summary_includes_task_type(self):
        task = _make_task(task_id="t-1", request="review the code", expected_output="review report")
        summary = _build_bounded_analysis_summary(task, "code-review")
        self.assertIn("code-review", summary)
        self.assertIn("t-1", summary)

    def test_summary_includes_request_and_expected(self):
        task = _make_task(request="my request", expected_output="my output")
        summary = _build_bounded_analysis_summary(task, "implementation")
        self.assertIn("my request", summary)
        self.assertIn("my output", summary)

    def test_summary_boundary_statement(self):
        task = _make_task()
        summary = _build_bounded_analysis_summary(task, "implementation")
        self.assertIn("No external connectors", summary)
        self.assertIn("Archon accepted", summary)

    def test_summary_empty_request_handled(self):
        task = _make_task(request="", expected_output="")
        summary = _build_bounded_analysis_summary(task, "architecture-review")
        self.assertIn("no request supplied", summary)


# ── TestBoundedAnalysisAudit ──────────────────────────────────────────────────

class TestBoundedAnalysisAudit(unittest.TestCase):
    def test_audit_has_frontmatter(self):
        task = _make_task(task_id="t-audit")
        summary = "summary text"
        audit = _build_bounded_analysis_audit(
            task=task, task_type="code-review", summary=summary, run_iso="2026-04-30T00:00:00Z"
        )
        self.assertIn("type: agent-activity", audit)
        self.assertIn("workflow: archon_watch", audit)
        self.assertIn("task_type: code-review", audit)
        self.assertIn("runtime: Archon", audit)

    def test_audit_includes_boundary_statement(self):
        task = _make_task()
        audit = _build_bounded_analysis_audit(
            task=task, task_type="implementation", summary="s", run_iso="2026-04-30T00:00:00Z"
        )
        self.assertIn("Boundary Statement", audit)

    def test_audit_includes_summary(self):
        task = _make_task()
        audit = _build_bounded_analysis_audit(
            task=task, task_type="implementation", summary="UNIQUE_SUMMARY_TEXT", run_iso="2026-04-30T00:00:00Z"
        )
        self.assertIn("UNIQUE_SUMMARY_TEXT", audit)


# ── TestDispatchBoundedAnalysis ───────────────────────────────────────────────

class TestDispatchBoundedAnalysis(unittest.TestCase):
    def _make_bus_mocks(self, claimed: bool = True):
        claim = MagicMock(return_value={"claimed": claimed, "reason": "already_claimed"})
        update = MagicMock()
        return claim, update

    def test_dispatch_success_returns_done(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            task = _make_task(task_id="t-001")
            claim, update = self._make_bus_mocks(claimed=True)
            with patch("runtime.agent_bus.bus.claim_task", claim), \
                 patch("runtime.agent_bus.bus.update_task_status", update):
                result = _dispatch_bounded_analysis(task, vault, "implementation")
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["task_type"], "implementation")
        self.assertEqual(len(result["writebacks"]), 1)

    def test_dispatch_claim_failure_returns_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            task = _make_task(task_id="t-002")
            claim, update = self._make_bus_mocks(claimed=False)
            with patch("runtime.agent_bus.bus.claim_task", claim), \
                 patch("runtime.agent_bus.bus.update_task_status", update):
                result = _dispatch_bounded_analysis(task, vault, "code-review")
        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["writebacks"], [])

    def test_dispatch_audit_path_under_agent_activity(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            task = _make_task(task_id="t-003")
            claim, update = self._make_bus_mocks(claimed=True)
            with patch("runtime.agent_bus.bus.claim_task", claim), \
                 patch("runtime.agent_bus.bus.update_task_status", update):
                result = _dispatch_bounded_analysis(task, vault, "architecture-review")
        wb = result["writebacks"][0]
        self.assertIn("07_LOGS/Agent-Activity/", wb["path"])
        self.assertIn("archon-watch", wb["path"])

    def test_dispatch_calls_update_status_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            task = _make_task(task_id="t-004")
            claim, update = self._make_bus_mocks(claimed=True)
            with patch("runtime.agent_bus.bus.claim_task", claim), \
                 patch("runtime.agent_bus.bus.update_task_status", update):
                _dispatch_bounded_analysis(task, vault, "implementation")
        self.assertEqual(update.call_count, 2)
        statuses = [c.kwargs.get("status") or c.args[2] for c in update.call_args_list
                    if c.kwargs.get("status") or len(c.args) > 2]
        all_statuses = [c.kwargs.get("status", "") for c in update.call_args_list]
        self.assertIn("in_progress", all_statuses)
        self.assertIn("done", all_statuses)


# ── TestHandlerWrappers ───────────────────────────────────────────────────────

class TestHandlerWrappers(unittest.TestCase):
    """_dispatch_implementation/_code_review/_architecture_review call the right task_type."""

    def _run_handler(self, handler, task):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            claim = MagicMock(return_value={"claimed": True})
            update = MagicMock()
            with patch("runtime.agent_bus.bus.claim_task", claim), \
                 patch("runtime.agent_bus.bus.update_task_status", update):
                return handler(task, vault)

    def test_implementation_handler(self):
        result = self._run_handler(_dispatch_implementation, _make_task())
        self.assertEqual(result["task_type"], "implementation")

    def test_code_review_handler(self):
        result = self._run_handler(_dispatch_code_review, _make_task())
        self.assertEqual(result["task_type"], "code-review")

    def test_architecture_review_handler(self):
        result = self._run_handler(_dispatch_architecture_review, _make_task())
        self.assertEqual(result["task_type"], "architecture-review")


# ── TestDispatchTable ─────────────────────────────────────────────────────────

class TestDispatchTable(unittest.TestCase):
    def test_all_three_task_types_registered(self):
        self.assertIn("implementation", _TASK_DISPATCH)
        self.assertIn("code-review", _TASK_DISPATCH)
        self.assertIn("architecture-review", _TASK_DISPATCH)

    def test_review_is_not_in_dispatch_table(self):
        self.assertNotIn("review", _TASK_DISPATCH)

    def test_unknown_is_not_in_dispatch_table(self):
        self.assertNotIn("unknown", _TASK_DISPATCH)


# ── TestEscalateUnhandled ─────────────────────────────────────────────────────

class TestEscalateUnhandled(unittest.TestCase):
    def test_escalate_calls_bus_blocked(self):
        task = _make_task(task_id="esc-001", intent="unknown-type")
        update = MagicMock()
        with patch("runtime.agent_bus.bus.update_task_status", update):
            result = _escalate_unhandled(task, Path("/tmp"))
        self.assertEqual(result["status"], "escalated")
        self.assertEqual(result["task_id"], "esc-001")
        self.assertIn("blocked", result["reason"])
        update.assert_called_once()
        kwargs = update.call_args.kwargs
        self.assertEqual(kwargs.get("status"), "blocked")

    def test_escalate_message_includes_task_type(self):
        task = _make_task(intent="planning", notes="task_type: planning")
        update = MagicMock()
        with patch("runtime.agent_bus.bus.update_task_status", update):
            result = _escalate_unhandled(task, Path("/tmp"))
        self.assertIn("planning", result["reason"])


# ── TestRunOneCycle ───────────────────────────────────────────────────────────

class TestRunOneCycle(unittest.TestCase):
    def _cycle(self, vault, open_tasks=None, claimed=True):
        open_tasks = open_tasks or []
        claim = MagicMock(return_value={"claimed": claimed})
        update = MagicMock()
        heartbeat = MagicMock()
        list_tasks = MagicMock(return_value=open_tasks)
        with patch("runtime.agent_bus.bus.list_tasks", list_tasks), \
             patch("runtime.agent_bus.bus.upsert_heartbeat", heartbeat), \
             patch("runtime.agent_bus.bus.claim_task", claim), \
             patch("runtime.agent_bus.bus.update_task_status", update):
            return _run_one_cycle(vault, max_tasks_per_cycle=2, now_iso="2026-04-30T00:00:00Z"), heartbeat

    def test_empty_vault_no_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            result, heartbeat = self._cycle(vault, open_tasks=[])
        self.assertEqual(result["open_count"], 0)
        self.assertEqual(result["processed_count"], 0)
        self.assertEqual(result["dispatched"], [])
        self.assertEqual(result["escalated"], [])
        self.assertEqual(heartbeat.call_count, 2)

    def test_dispatch_known_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            tasks = [_make_task(task_id="t-1", intent="implementation")]
            result, _ = self._cycle(vault, open_tasks=tasks, claimed=True)
        self.assertEqual(result["processed_count"], 1)
        self.assertEqual(len(result["dispatched"]), 1)
        self.assertEqual(result["dispatched"][0]["task_type"], "implementation")

    def test_escalate_unknown_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            tasks = [_make_task(task_id="t-unk", intent="something-unknown")]
            update = MagicMock()
            heartbeat = MagicMock()
            list_tasks = MagicMock(return_value=tasks)
            with patch("runtime.agent_bus.bus.list_tasks", list_tasks), \
                 patch("runtime.agent_bus.bus.upsert_heartbeat", heartbeat), \
                 patch("runtime.agent_bus.bus.update_task_status", update):
                result = _run_one_cycle(vault, max_tasks_per_cycle=2, now_iso="2026-04-30T00:00:00Z")
        self.assertEqual(len(result["escalated"]), 1)
        self.assertEqual(len(result["dispatched"]), 0)

    def test_max_tasks_per_cycle_respected(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            tasks = [
                _make_task(task_id=f"t-{i}", intent="implementation")
                for i in range(5)
            ]
            result, _ = self._cycle(vault, open_tasks=tasks, claimed=True)
        self.assertEqual(result["processed_count"], 2)

    def test_heartbeat_idle_when_no_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            result, heartbeat = self._cycle(vault, open_tasks=[])
        calls = heartbeat.call_args_list
        statuses = [c.kwargs.get("status", "") for c in calls]
        self.assertTrue(all(s == "idle" for s in statuses))

    def test_heartbeat_busy_when_dispatched(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            tasks = [_make_task(task_id="t-x", intent="implementation")]
            result, heartbeat = self._cycle(vault, open_tasks=tasks, claimed=True)
        statuses = [c.kwargs.get("status", "") for c in heartbeat.call_args_list]
        self.assertIn("busy", statuses)


# ── TestRunArchonWatch ────────────────────────────────────────────────────────

class TestRunArchonWatch(unittest.TestCase):
    def _run(self, inputs, tasks=None, claimed=True):
        tasks = tasks or []
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            list_tasks = MagicMock(return_value=tasks)
            heartbeat = MagicMock()
            claim = MagicMock(return_value={"claimed": claimed})
            update = MagicMock()
            with patch("runtime.agent_bus.bus.list_tasks", list_tasks), \
                 patch("runtime.agent_bus.bus.upsert_heartbeat", heartbeat), \
                 patch("runtime.agent_bus.bus.claim_task", claim), \
                 patch("runtime.agent_bus.bus.update_task_status", update):
                result = run_archon_watch(inputs, vault)
        return result

    def test_single_cycle_no_interval(self):
        result = self._run({"interval_seconds": None})
        self.assertEqual(result["cycles_run"], 1)
        self.assertIn("tasks_dispatched", result)
        self.assertIn("tasks_escalated", result)

    def test_single_cycle_omitted_interval(self):
        result = self._run({})
        self.assertEqual(result["cycles_run"], 1)

    def test_dispatch_counted(self):
        tasks = [_make_task(task_id="t-run", intent="code-review")]
        result = self._run({}, tasks=tasks, claimed=True)
        self.assertEqual(result["tasks_dispatched"], 1)

    def test_invalid_interval_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self.assertRaises(WorkflowExecutionError):
                run_archon_watch({"interval_seconds": 0}, vault)

    def test_negative_interval_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(Path(tmp))
            with self.assertRaises(WorkflowExecutionError):
                run_archon_watch({"interval_seconds": -5}, vault)

    def test_cycle_summary_structure(self):
        result = self._run({})
        self.assertEqual(len(result["cycle_summaries"]), 1)
        summary = result["cycle_summaries"][0]
        self.assertIn("cycle", summary)
        self.assertIn("now", summary)
        self.assertIn("open_count", summary)
        self.assertIn("dispatched", summary)
        self.assertIn("escalated", summary)

    def test_writebacks_aggregated(self):
        tasks = [_make_task(task_id="t-wb", intent="implementation")]
        result = self._run({}, tasks=tasks, claimed=True)
        self.assertIsInstance(result["writebacks"], list)

    def test_max_tasks_per_cycle_passed_through(self):
        result = self._run({"max_tasks_per_cycle": 5})
        self.assertEqual(result["cycles_run"], 1)


# ── TestEngineWiring ──────────────────────────────────────────────────────────

class TestEngineWiring(unittest.TestCase):
    def test_engine_resolves_archon_watch(self):
        from runtime.aor.engine import _resolve_workflow_handler
        handler = _resolve_workflow_handler("archon_watch")
        self.assertIsNotNone(handler)
        self.assertEqual(handler.__name__, "run_archon_watch")

    def test_engine_returns_none_for_unknown(self):
        from runtime.aor.engine import _resolve_workflow_handler
        self.assertIsNone(_resolve_workflow_handler("nonexistent_workflow_xyz"))


if __name__ == "__main__":
    unittest.main()
