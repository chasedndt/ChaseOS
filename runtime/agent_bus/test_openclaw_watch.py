"""
test_openclaw_watch.py — Tests for OpenClaw bus watch loop

Covers:
  TestTaskTypeInference    (10 tests) — _infer_task_type, _infer_workflow, _parse_notes
  TestOpenClawWatchLoop    (12 tests) — run_openclaw_watch single-cycle, dry_run, multi-task
  TestOpenClawDispatch     (8 tests)  — dispatch table, escalation, claim/result posting
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    (tmp_path / "00_HOME").mkdir(parents=True)
    (tmp_path / "00_HOME" / "Now.md").write_text("# Now\n\nDate: 2026-04-27\n")
    (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    (tmp_path / "07_LOGS" / "Build-Logs").mkdir(parents=True)
    (tmp_path / "07_LOGS" / "Operator-Briefs").mkdir(parents=True)
    (tmp_path / "runtime" / "agent_bus").mkdir(parents=True)
    from runtime.agent_bus.bus import init_db
    init_db(tmp_path)
    return tmp_path


def _post_task_to_openclaw(
    vault: Path,
    intent: str = "TASK",
    notes: str = "task_type: operator-briefing",
    priority: str = "normal",
) -> str:
    from runtime.agent_bus.bus import create_task
    result = create_task(
        vault,
        sender="Hermes",
        recipient="OpenClaw",
        intent=intent,
        priority=priority,
        request="Run operator briefing.",
        expected_output="Operator brief.",
        notes=notes,
    )
    assert result["created"], result
    return result["task_id"]


def _noop_handler(task, vault_root):
    return {"status": "done", "writebacks": []}


# ── TestTaskTypeInference ─────────────────────────────────────────────────────

class TestTaskTypeInference:

    def test_parse_notes_extracts_key_value(self):
        from runtime.workflows.openclaw_watch import _parse_notes
        notes = "task_type: operator-briefing\nworkflow: operator_today"
        result = _parse_notes(notes)
        assert result["task_type"] == "operator-briefing"
        assert result["workflow"] == "operator_today"

    def test_parse_notes_empty(self):
        from runtime.workflows.openclaw_watch import _parse_notes
        assert _parse_notes("") == {}
        assert _parse_notes(None) == {}

    def test_infer_task_type_from_review_intent(self):
        from runtime.workflows.openclaw_watch import _infer_task_type
        task = {"intent": "REVIEW", "notes": ""}
        assert _infer_task_type(task) == "review"

    def test_infer_task_type_from_notes_annotation(self):
        from runtime.workflows.openclaw_watch import _infer_task_type
        task = {"intent": "TASK", "notes": "task_type: graph-hygiene"}
        assert _infer_task_type(task) == "graph-hygiene"

    def test_infer_task_type_from_workflow_annotation(self):
        from runtime.workflows.openclaw_watch import _infer_task_type
        task = {"intent": "TASK", "notes": "workflow: graph_hygiene"}
        assert _infer_task_type(task) == "graph-hygiene"

    def test_infer_task_type_unknown_workflow(self):
        from runtime.workflows.openclaw_watch import _infer_task_type
        task = {"intent": "TASK", "notes": "workflow: nonexistent_workflow"}
        assert _infer_task_type(task) == "unknown"

    def test_infer_task_type_no_annotation_fallback(self):
        from runtime.workflows.openclaw_watch import _infer_task_type
        task = {"intent": "TASK", "notes": "artifact_path: something.md"}
        assert _infer_task_type(task) == "unknown"

    def test_infer_workflow_operator_briefing_default(self):
        from runtime.workflows.openclaw_watch import _infer_workflow
        task = {"notes": "task_type: operator-briefing"}
        assert _infer_workflow(task, "operator-briefing") == "operator_today"

    def test_infer_workflow_operator_close_day_annotation(self):
        from runtime.workflows.openclaw_watch import _infer_workflow
        task = {"notes": "workflow: operator_close_day"}
        assert _infer_workflow(task, "operator-briefing") == "operator_close_day"

    def test_infer_workflow_graph_hygiene_default(self):
        from runtime.workflows.openclaw_watch import _infer_workflow
        task = {"notes": "task_type: graph-hygiene"}
        assert _infer_workflow(task, "graph-hygiene") == "graph_hygiene"

    def test_infer_workflow_source_pack_builder_default(self):
        from runtime.workflows.openclaw_watch import _infer_workflow
        task = {"notes": "task_type: source-pack-builder"}
        assert _infer_workflow(task, "source-pack-builder") == "source_pack_builder"


# ── TestOpenClawWatchLoop ─────────────────────────────────────────────────────

class TestOpenClawWatchLoop:

    def test_watch_single_cycle_no_tasks(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.openclaw_watch import run_openclaw_watch
        result = run_openclaw_watch({}, vault)
        assert result["cycles_run"] == 1
        assert result["tasks_dispatched"] == 0
        assert result["tasks_escalated"] == 0

    def test_watch_result_structure(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.openclaw_watch import run_openclaw_watch
        result = run_openclaw_watch({}, vault)
        assert "cycles_run" in result
        assert "tasks_dispatched" in result
        assert "tasks_escalated" in result
        assert "cycle_summaries" in result
        assert "writebacks" in result

    def test_watch_cycle_summary_has_expected_keys(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.openclaw_watch import run_openclaw_watch
        result = run_openclaw_watch({}, vault)
        summary = result["cycle_summaries"][0]
        assert "cycle" in summary
        assert "now" in summary
        assert "open_count" in summary
        assert "dispatched" in summary
        assert "escalated" in summary
        assert "dry_run" in summary

    def test_watch_invalid_interval_raises(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.openclaw_watch import run_openclaw_watch, WorkflowExecutionError
        with pytest.raises(WorkflowExecutionError):
            run_openclaw_watch({"interval_seconds": 0}, vault)

    def test_watch_dry_run_does_not_claim(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_task_to_openclaw(vault, notes="task_type: operator-briefing")
        from runtime.workflows.openclaw_watch import run_openclaw_watch
        from runtime.agent_bus.bus import list_tasks
        result = run_openclaw_watch({"dry_run": True}, vault)
        # dry_run: counted in dispatched list but task stays open on bus
        tasks = list_tasks(vault, recipient="OpenClaw", status="open")
        assert len(tasks) == 1  # still open — not claimed
        assert result["cycle_summaries"][0]["dry_run"] is True

    def test_watch_upserts_heartbeat(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.openclaw_watch import run_openclaw_watch
        from runtime.agent_bus.backend_loader import get_backend
        run_openclaw_watch({}, vault)
        heartbeats = [h for h in get_backend(vault).list_heartbeats() if h.get("runtime") == "OpenClaw"]
        assert len(heartbeats) >= 1

    def test_watch_preserves_explicit_instance_scope_on_heartbeat_and_claim(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_task_to_openclaw(vault, notes="task_type: operator-briefing")
        import runtime.workflows.openclaw_watch as ow
        original = ow._TASK_DISPATCH.copy()
        ow._TASK_DISPATCH["operator-briefing"] = lambda t, v: _noop_handler(t, v)
        try:
            from runtime.workflows.openclaw_watch import run_openclaw_watch
            run_openclaw_watch(
                {
                    "runtime_instance_id": "openclaw-discord-worker",
                    "control_surface": "discord",
                    "control_surface_key": "discord:ops",
                },
                vault,
            )
        finally:
            ow._TASK_DISPATCH.update(original)

        from runtime.agent_bus.bus import list_tasks
        from runtime.agent_bus.backend_loader import get_backend

        task = list_tasks(vault, recipient="OpenClaw")[0]
        heartbeat = next(
            h
            for h in get_backend(vault).list_heartbeats()
            if h.get("heartbeat_key") == "OpenClaw:openclaw-discord-worker"
        )
        assert task["owner_instance"] == "openclaw-discord-worker"
        assert heartbeat["heartbeat_scope"] == "instance"
        assert heartbeat["control_surface"] == "discord"
        assert heartbeat["control_surface_key"] == "discord:ops"

    def test_watch_max_tasks_per_cycle_respected(self, tmp_path):
        vault = _make_vault(tmp_path)
        import runtime.workflows.openclaw_watch as ow
        original = ow._TASK_DISPATCH.copy()
        ow._TASK_DISPATCH["operator-briefing"] = lambda t, v: _noop_handler(t, v)
        try:
            for _ in range(3):
                _post_task_to_openclaw(vault, notes="task_type: operator-briefing")
            from runtime.workflows.openclaw_watch import run_openclaw_watch
            result = run_openclaw_watch({"max_tasks_per_cycle": 1}, vault)
        finally:
            ow._TASK_DISPATCH.update(original)
        assert result["tasks_dispatched"] == 1

    def test_watch_target_task_id_filters_open_tasks(self, tmp_path):
        vault = _make_vault(tmp_path)
        import runtime.workflows.openclaw_watch as ow
        original = ow._TASK_DISPATCH.copy()
        ow._TASK_DISPATCH["operator-briefing"] = lambda t, v: _noop_handler(t, v)
        try:
            first_task = _post_task_to_openclaw(vault, notes="task_type: operator-briefing")
            target_task = _post_task_to_openclaw(vault, notes="task_type: operator-briefing")
            from runtime.agent_bus.bus import get_task
            from runtime.workflows.openclaw_watch import run_openclaw_watch
            result = run_openclaw_watch(
                {
                    "target_task_id": target_task,
                    "max_tasks_per_cycle": 1,
                },
                vault,
            )
        finally:
            ow._TASK_DISPATCH.update(original)

        assert result["tasks_dispatched"] == 1
        assert result["cycle_summaries"][0]["open_count"] == 1
        assert get_task(vault, first_task)["status"] == "open"
        assert get_task(vault, target_task)["status"] == "done"

    def test_watch_handler_exception_captured(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_task_to_openclaw(vault, notes="task_type: operator-briefing")
        import runtime.workflows.openclaw_watch as ow
        original = ow._TASK_DISPATCH.copy()
        ow._TASK_DISPATCH["operator-briefing"] = lambda t, v: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            from runtime.workflows.openclaw_watch import run_openclaw_watch
            result = run_openclaw_watch({}, vault)
        finally:
            ow._TASK_DISPATCH.update(original)
        assert result["tasks_dispatched"] == 0
        assert result["tasks_escalated"] == 1

    def test_watch_aor_engine_runs_openclaw_watch(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.aor.engine import run_workflow
        result = run_workflow("openclaw_watch", {}, vault_root=vault)
        assert result.status in ("success", "escalated")

    def test_watch_dispatched_task_marked_done_on_bus(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_task_to_openclaw(vault, notes="task_type: operator-briefing")
        import runtime.workflows.openclaw_watch as ow
        original = ow._TASK_DISPATCH.copy()
        ow._TASK_DISPATCH["operator-briefing"] = lambda t, v: _noop_handler(t, v)
        try:
            from runtime.workflows.openclaw_watch import run_openclaw_watch
            run_openclaw_watch({}, vault)
        finally:
            ow._TASK_DISPATCH.update(original)
        from runtime.agent_bus.bus import list_tasks
        tasks = list_tasks(vault, recipient="OpenClaw")
        assert any(t["status"] == "done" for t in tasks)

    def test_watch_writebacks_aggregated(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_task_to_openclaw(vault, notes="task_type: operator-briefing")
        import runtime.workflows.openclaw_watch as ow
        original = ow._TASK_DISPATCH.copy()
        ow._TASK_DISPATCH["operator-briefing"] = lambda t, v: {
            "status": "done",
            "writebacks": [{"path": "07_LOGS/Agent-Activity/test.md", "content": "test"}],
        }
        try:
            from runtime.workflows.openclaw_watch import run_openclaw_watch
            result = run_openclaw_watch({}, vault)
        finally:
            ow._TASK_DISPATCH.update(original)
        assert len(result["writebacks"]) > 0

    def test_watch_multiple_tasks_dispatched(self, tmp_path):
        vault = _make_vault(tmp_path)
        import runtime.workflows.openclaw_watch as ow
        original = ow._TASK_DISPATCH.copy()
        ow._TASK_DISPATCH["operator-briefing"] = lambda t, v: _noop_handler(t, v)
        ow._TASK_DISPATCH["graph-hygiene"] = lambda t, v: _noop_handler(t, v)
        try:
            _post_task_to_openclaw(vault, notes="task_type: operator-briefing")
            _post_task_to_openclaw(vault, notes="task_type: graph-hygiene")
            from runtime.workflows.openclaw_watch import run_openclaw_watch
            result = run_openclaw_watch({"max_tasks_per_cycle": 3}, vault)
        finally:
            ow._TASK_DISPATCH.update(original)
        assert result["tasks_dispatched"] == 2


# ── TestOpenClawDispatch ──────────────────────────────────────────────────────

class TestOpenClawDispatch:

    def test_dispatch_table_has_expected_keys(self):
        from runtime.workflows.openclaw_watch import _TASK_DISPATCH
        assert "operator-briefing" in _TASK_DISPATCH
        assert "graph-hygiene" in _TASK_DISPATCH
        assert "vault-maintenance" in _TASK_DISPATCH
        assert "scheduled-briefing" in _TASK_DISPATCH
        assert "source-pack-builder" in _TASK_DISPATCH
        # review intentionally absent — OpenClaw is secondary reviewer only
        assert "review" not in _TASK_DISPATCH

    def test_unknown_task_type_escalated(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_task_to_openclaw(vault, notes="task_type: nonexistent-type")
        from runtime.workflows.openclaw_watch import run_openclaw_watch
        result = run_openclaw_watch({}, vault)
        assert result["tasks_escalated"] == 1
        assert result["tasks_dispatched"] == 0

    def test_unknown_task_marked_blocked_on_bus(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_task_to_openclaw(vault, notes="task_type: nonexistent-type")
        from runtime.workflows.openclaw_watch import run_openclaw_watch
        from runtime.agent_bus.bus import list_tasks
        run_openclaw_watch({}, vault)
        tasks = list_tasks(vault, recipient="OpenClaw")
        assert any(t["status"] == "blocked" for t in tasks)

    def test_review_intent_escalated_not_dispatched(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_task_to_openclaw(vault, intent="REVIEW", notes="artifact_path: 07_LOGS/Build-Logs/test.md")
        from runtime.workflows.openclaw_watch import run_openclaw_watch
        result = run_openclaw_watch({}, vault)
        # review → inferred as "review" → not in _TASK_DISPATCH → escalated
        assert result["tasks_escalated"] == 1

    def test_workflow_annotation_routes_close_day(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_task_to_openclaw(vault, notes="workflow: operator_close_day")
        import runtime.workflows.openclaw_watch as ow
        original = ow._TASK_DISPATCH.copy()
        captured = {}
        def mock_briefing(task, vault_root):
            from runtime.workflows.openclaw_watch import _infer_workflow
            captured["workflow"] = _infer_workflow(task, "operator-briefing")
            return _noop_handler(task, vault_root)
        ow._TASK_DISPATCH["operator-briefing"] = mock_briefing
        try:
            from runtime.workflows.openclaw_watch import run_openclaw_watch
            run_openclaw_watch({}, vault)
        finally:
            ow._TASK_DISPATCH.update(original)
        assert captured.get("workflow") == "operator_close_day"

    def test_mixed_known_unknown_tasks(self, tmp_path):
        vault = _make_vault(tmp_path)
        import runtime.workflows.openclaw_watch as ow
        original = ow._TASK_DISPATCH.copy()
        ow._TASK_DISPATCH["graph-hygiene"] = lambda t, v: _noop_handler(t, v)
        try:
            _post_task_to_openclaw(vault, notes="task_type: graph-hygiene")
            _post_task_to_openclaw(vault, notes="task_type: unknown-type")
            from runtime.workflows.openclaw_watch import run_openclaw_watch
            result = run_openclaw_watch({"max_tasks_per_cycle": 3}, vault)
        finally:
            ow._TASK_DISPATCH.update(original)
        assert result["tasks_dispatched"] == 1
        assert result["tasks_escalated"] == 1

    def test_claim_marks_task_in_progress_then_done(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_task_to_openclaw(vault, notes="task_type: graph-hygiene")
        import runtime.workflows.openclaw_watch as ow
        original = ow._TASK_DISPATCH.copy()
        ow._TASK_DISPATCH["graph-hygiene"] = lambda t, v: _noop_handler(t, v)
        try:
            from runtime.workflows.openclaw_watch import run_openclaw_watch
            run_openclaw_watch({}, vault)
        finally:
            ow._TASK_DISPATCH.update(original)
        from runtime.agent_bus.backends.sqlite_backend import SQLiteBackend
        from runtime.agent_bus.backend_loader import get_backend
        backend = get_backend(vault)
        tasks = backend.list_tasks()
        task = next((t for t in tasks if t["recipient"] == "OpenClaw"), None)
        assert task is not None
        assert task["status"] == "done"

    def test_task_type_annotation_takes_precedence_over_workflow(self):
        from runtime.workflows.openclaw_watch import _infer_task_type
        # task_type: annotation wins over workflow: annotation
        task = {"intent": "TASK", "notes": "task_type: graph-hygiene\nworkflow: operator_today"}
        assert _infer_task_type(task) == "graph-hygiene"

    def test_source_pack_builder_requires_input_envelope(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_task_to_openclaw(vault, notes="task_type: source-pack-builder")
        from runtime.workflows.openclaw_watch import run_openclaw_watch
        result = run_openclaw_watch({}, vault)
        assert result["tasks_dispatched"] == 0
        assert result["tasks_escalated"] == 1
        assert "source-pack-builder requires" in result["cycle_summaries"][0].get("reason", "") or result["tasks_escalated"] == 1

    def test_source_pack_builder_dispatches_with_declared_json_input_packet(self, tmp_path):
        vault = _make_vault(tmp_path)
        packet_path = vault / "runtime" / "agent_bus" / "source-pack-input.json"
        packet_path.write_text(
            '{"objective":"Build bounded pack","project_scope":"Test","pack_id":"test-pack",'
            '"sources":[{"source_id":"s1","source_class":"source_note","path":"02_KNOWLEDGE/source.md",'
            '"display_name":"Source","base_trust_tier":4}],'
            '"write_target_root":"runtime/acquisition/packs/test-pack"}',
            encoding="utf-8",
        )
        _post_task_to_openclaw(
            vault,
            notes="task_type: source-pack-builder\nsource_pack_inputs_path: runtime/agent_bus/source-pack-input.json",
        )
        import runtime.workflows.openclaw_watch as ow
        captured = {}
        def fake_run_source_pack_builder(inputs, vault_root):
            captured["inputs"] = inputs
            captured["vault_root"] = vault_root
            return {"summary": "source pack built", "writebacks": [{"path": "runtime/acquisition/packs/test-pack"}]}
        with patch("runtime.acquisition.source_pack_builder.run_source_pack_builder", fake_run_source_pack_builder):
            result = ow.run_openclaw_watch({}, vault)
        assert result["tasks_dispatched"] == 1
        assert captured["inputs"]["pack_id"] == "test-pack"
        assert captured["inputs"]["acquirer_identity"] == "OpenClaw"
        assert captured["inputs"]["adapter_id"] == "openclaw"
        assert captured["vault_root"] == vault
