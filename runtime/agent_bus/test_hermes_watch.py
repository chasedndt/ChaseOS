"""
test_hermes_watch.py — Tests for Hermes watch loop and LLM synthesis

Covers:
  TestHermesReviewSynthesis   (8 tests) — _execute_synthesis, _produce_review with synthesis
  TestHermesWatchLoop         (14 tests) — run_hermes_watch single-cycle and multi-cycle
  TestHermesWatchDispatch     (6 tests) — dispatch table, escalation for unhandled types
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

# ── helpers ───────────────────────────────────────────────────────────────────

def _make_vault(tmp_path: Path) -> Path:
    """Minimal vault with bus schema initialised."""
    (tmp_path / "00_HOME").mkdir(parents=True)
    (tmp_path / "00_HOME" / "Now.md").write_text("# Now\n\nDate: 2026-04-26\n")
    (tmp_path / "07_LOGS" / "Agent-Activity").mkdir(parents=True)
    (tmp_path / "07_LOGS" / "Build-Logs").mkdir(parents=True)
    (tmp_path / "07_LOGS" / "SBP-Runs").mkdir(parents=True)
    (tmp_path / "07_LOGS" / "Operator-Briefs").mkdir(parents=True)
    (tmp_path / "runtime" / "agent_bus").mkdir(parents=True)
    from runtime.agent_bus.bus import init_db
    init_db(tmp_path)
    return tmp_path


def _post_review_task(vault: Path, artifact_path: str = "07_LOGS/Build-Logs/test.md") -> str:
    """Create a review task on the bus, return task_id."""
    from runtime.agent_bus.bus import create_task
    result = create_task(
        vault,
        sender="OpenClaw",
        recipient="Hermes",
        intent="REVIEW",
        priority="normal",
        request="Review the artifact for structural completeness.",
        expected_output="Structured review with endorsed items and flags.",
        notes=f"artifact_path: {artifact_path}",
    )
    assert result["created"], result
    return result["task_id"]


def _post_planning_task(vault: Path) -> str:
    """Create a bounded planning task for Hermes, return task_id."""
    from runtime.agent_bus.bus import create_task
    result = create_task(
        vault,
        sender="OpenClaw",
        recipient="Hermes",
        intent="TASK",
        priority="normal",
        request="Produce a bounded implementation plan for the next runtime slice.",
        expected_output="Bus result packet and agent-activity audit writeback.",
        notes="task_type: planning\nsource: unit-test",
    )
    assert result["created"], result
    return result["task_id"]


# ── TestHermesReviewSynthesis ─────────────────────────────────────────────────

class TestHermesReviewSynthesis:

    def test_execute_synthesis_skipped_when_no_api_key(self):
        from runtime.workflows.hermes_review_execute import _execute_synthesis
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = _execute_synthesis(
                request="review",
                artifact_path="07_LOGS/Build-Logs/test.md",
                endorsed=["Non-empty"],
                flags=[],
                artifact_content="# Test\n\nContent here.",
            )
        assert result is None

    def test_execute_synthesis_returns_none_on_adapter_error(self):
        from runtime.workflows.hermes_review_execute import _execute_synthesis
        with patch("runtime.workflows.hermes_review_execute.execute_synthesis", side_effect=Exception("network error")):
            result = _execute_synthesis(
                request="review",
                artifact_path="07_LOGS/Build-Logs/test.md",
                endorsed=["Non-empty"],
                flags=[],
                artifact_content="# Test\n\nContent.",
            )
        assert result is None

    def test_execute_synthesis_returns_text_on_shared_adapter_success(self):
        from runtime.workflows.hermes_review_execute import _execute_synthesis
        from runtime.execution_adapters.execute import SynthesisResult

        with patch(
            "runtime.workflows.hermes_review_execute.execute_synthesis",
            return_value=SynthesisResult(
                text="Strong artifact.",
                model_id="claude-opus-4-7",
                runtime="hermes",
                usage={},
                fallback_used=False,
            ),
        ) as mock_execute:
            result = _execute_synthesis(
                request="review",
                artifact_path="07_LOGS/Build-Logs/test.md",
                endorsed=["Non-empty"],
                flags=[],
                artifact_content="# Test\n\nContent.",
            )
        assert result == "Strong artifact."
        assert mock_execute.call_args.kwargs["execution_adapter"] == "hermes"

    def test_execute_synthesis_handles_empty_adapter_text(self):
        from runtime.workflows.hermes_review_execute import _execute_synthesis
        from runtime.execution_adapters.execute import SynthesisResult

        with patch(
            "runtime.workflows.hermes_review_execute.execute_synthesis",
            return_value=SynthesisResult(
                text="",
                model_id="claude-opus-4-7",
                runtime="hermes",
                usage={},
                fallback_used=False,
            ),
        ):
            result = _execute_synthesis(
                request="review", artifact_path="test.md",
                endorsed=[], flags=[], artifact_content="content",
            )
        assert result is None

    def test_produce_review_without_synthesis(self):
        from runtime.workflows.hermes_review_execute import _produce_review
        result = _produce_review(
            request="Review artifact",
            artifact_path="07_LOGS/Build-Logs/test.md",
            artifact_content="# Test\n\n2026-04-26 content here with enough words.",
            synthesize=False,
        )
        assert result["synthesis"] is None
        assert "Hermes Review" in result["summary"]
        assert isinstance(result["endorsed"], list)
        assert isinstance(result["flags"], list)

    def test_produce_review_with_synthesis_injected(self):
        from runtime.workflows.hermes_review_execute import _produce_review
        with patch("runtime.workflows.hermes_review_execute._execute_synthesis", return_value="Great artifact."):
            result = _produce_review(
                request="Review",
                artifact_path="07_LOGS/Build-Logs/test.md",
                artifact_content="# Test\n\n2026-04-26 content here.",
                synthesize=True,
            )
        assert result["synthesis"] == "Great artifact."
        assert "### Synthesis" in result["summary"]
        assert "Great artifact." in result["summary"]

    def test_produce_review_none_content(self):
        from runtime.workflows.hermes_review_execute import _produce_review
        result = _produce_review(
            request="Review",
            artifact_path="07_LOGS/Build-Logs/test.md",
            artifact_content=None,
            synthesize=False,
        )
        assert result["synthesis"] is None
        assert "INCOMPLETE" in result["summary"]
        assert len(result["flags"]) > 0

    def test_produce_review_detects_frontmatter(self):
        from runtime.workflows.hermes_review_execute import _produce_review
        content = "---\ntype: agent-activity\n---\n\n# Test\n\n2026-04-26 content here enough words."
        result = _produce_review(
            request="Review",
            artifact_path="07_LOGS/Agent-Activity/test.md",
            artifact_content=content,
            synthesize=False,
        )
        endorsed_text = " ".join(result["endorsed"])
        assert "frontmatter" in endorsed_text


# ── TestHermesWatchLoop ───────────────────────────────────────────────────────

class TestHermesWatchLoop:

    def test_watch_single_cycle_no_tasks(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.hermes_watch import run_hermes_watch
        result = run_hermes_watch({}, vault)
        assert result["cycles_run"] == 1
        assert result["tasks_dispatched"] == 0
        assert result["tasks_escalated"] == 0
        assert len(result["cycle_summaries"]) == 1

    def test_watch_single_cycle_claims_review_task(self, tmp_path):
        vault = _make_vault(tmp_path)
        artifact = vault / "07_LOGS" / "Build-Logs" / "test.md"
        artifact.write_text("# Build Log\n\n2026-04-26 content here with enough words to pass.")
        _post_review_task(vault, "07_LOGS/Build-Logs/test.md")

        from runtime.workflows.hermes_watch import run_hermes_watch
        with patch("runtime.workflows.hermes_review_execute._execute_synthesis", return_value=None):
            result = run_hermes_watch({"synthesize": False}, vault)

        assert result["tasks_dispatched"] == 1
        assert result["tasks_escalated"] == 0

    def test_watch_returns_writebacks_from_handler(self, tmp_path):
        vault = _make_vault(tmp_path)
        artifact = vault / "07_LOGS" / "Build-Logs" / "test.md"
        artifact.write_text("# Build Log\n\n2026-04-26 content here.")
        _post_review_task(vault, "07_LOGS/Build-Logs/test.md")

        from runtime.workflows.hermes_watch import run_hermes_watch
        result = run_hermes_watch({"synthesize": False}, vault)

        assert len(result["writebacks"]) > 0
        paths = [w["path"] for w in result["writebacks"]]
        assert any("Agent-Activity" in p for p in paths)

    def test_watch_upserts_heartbeat_each_cycle(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.hermes_watch import run_hermes_watch
        from runtime.agent_bus.bus import list_tasks
        from runtime.agent_bus.backends.sqlite_backend import SQLiteBackend
        from runtime.agent_bus.backend_loader import get_backend

        run_hermes_watch({}, vault)

        backend = get_backend(vault)
        heartbeats = [h for h in backend.list_heartbeats() if h.get("runtime") == "Hermes"]
        assert len(heartbeats) >= 1

    def test_watch_preserves_explicit_instance_scope_on_heartbeat_and_claim(self, tmp_path):
        vault = _make_vault(tmp_path)
        _post_planning_task(vault)
        from runtime.workflows.hermes_watch import run_hermes_watch
        from runtime.agent_bus.bus import list_tasks
        from runtime.agent_bus.backend_loader import get_backend

        run_hermes_watch(
            {
                "runtime_instance_id": "hermes-discord-thread",
                "control_surface": "discord",
                "control_surface_key": "discord:ops:thread-1",
            },
            vault,
        )

        task = list_tasks(vault, recipient="Hermes")[0]
        heartbeat = next(
            h
            for h in get_backend(vault).list_heartbeats()
            if h.get("heartbeat_key") == "Hermes:hermes-discord-thread"
        )
        assert task["owner_instance"] == "hermes-discord-thread"
        assert heartbeat["heartbeat_scope"] == "instance"
        assert heartbeat["control_surface"] == "discord"
        assert heartbeat["control_surface_key"] == "discord:ops:thread-1"

    def test_watch_max_tasks_per_cycle_respected(self, tmp_path):
        vault = _make_vault(tmp_path)
        artifact = vault / "07_LOGS" / "Build-Logs" / "test.md"
        artifact.write_text("# Log\n\n2026-04-26 content here.")
        # Post 3 tasks but max_tasks_per_cycle=1
        for _ in range(3):
            _post_review_task(vault, "07_LOGS/Build-Logs/test.md")

        from runtime.workflows.hermes_watch import run_hermes_watch
        result = run_hermes_watch({"max_tasks_per_cycle": 1, "synthesize": False}, vault)

        # Only 1 dispatched in this single cycle
        assert result["tasks_dispatched"] == 1

    def test_watch_target_task_id_filters_open_tasks(self, tmp_path):
        vault = _make_vault(tmp_path)
        first_task = _post_planning_task(vault)
        target_task = _post_planning_task(vault)

        from runtime.agent_bus.bus import get_task
        from runtime.workflows.hermes_watch import run_hermes_watch

        result = run_hermes_watch(
            {
                "target_task_id": target_task,
                "max_tasks_per_cycle": 1,
                "synthesize": False,
            },
            vault,
        )

        assert result["tasks_dispatched"] == 1
        assert result["cycle_summaries"][0]["open_count"] == 1
        assert get_task(vault, first_task)["status"] == "open"
        assert get_task(vault, target_task)["status"] == "done"

    def test_watch_cycle_summary_has_expected_keys(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.hermes_watch import run_hermes_watch
        result = run_hermes_watch({}, vault)

        summary = result["cycle_summaries"][0]
        assert "cycle" in summary
        assert "now" in summary
        assert "open_count" in summary
        assert "dispatched" in summary
        assert "escalated" in summary

    def test_watch_invalid_interval_raises(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.hermes_watch import run_hermes_watch, WorkflowExecutionError
        with pytest.raises(WorkflowExecutionError):
            run_hermes_watch({"interval_seconds": 0}, vault)

    def test_watch_invalid_interval_negative_raises(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.hermes_watch import run_hermes_watch, WorkflowExecutionError
        with pytest.raises(WorkflowExecutionError):
            run_hermes_watch({"interval_seconds": -5}, vault)

    def test_watch_handler_exception_captured_not_raised(self, tmp_path):
        vault = _make_vault(tmp_path)
        artifact = vault / "07_LOGS" / "Build-Logs" / "test.md"
        artifact.write_text("# Log\n\n2026-04-26 content.")
        _post_review_task(vault, "07_LOGS/Build-Logs/test.md")

        import runtime.workflows.hermes_watch as hw
        original = hw._TASK_DISPATCH.copy()
        hw._TASK_DISPATCH["review"] = lambda task, vault_root, synthesize: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            from runtime.workflows.hermes_watch import run_hermes_watch
            result = run_hermes_watch({"synthesize": False}, vault)
        finally:
            hw._TASK_DISPATCH.update(original)

        # Dispatch failure → counted in escalated, not raised
        assert result["tasks_dispatched"] == 0
        assert result["tasks_escalated"] == 1
        assert result["cycles_run"] == 1

    def test_watch_no_tasks_result_structure(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.workflows.hermes_watch import run_hermes_watch
        result = run_hermes_watch({}, vault)
        assert "cycles_run" in result
        assert "tasks_dispatched" in result
        assert "tasks_escalated" in result
        assert "cycle_summaries" in result
        assert "writebacks" in result

    def test_watch_synthesize_false_passed_to_handler(self, tmp_path):
        vault = _make_vault(tmp_path)
        artifact = vault / "07_LOGS" / "Build-Logs" / "test.md"
        artifact.write_text("# Log\n\n2026-04-26 content.")
        _post_review_task(vault, "07_LOGS/Build-Logs/test.md")

        captured_inputs = {}

        import runtime.workflows.hermes_watch as hw
        original = hw._TASK_DISPATCH.copy()

        def mock_dispatch(task, vault_root, synthesize):
            captured_inputs["synthesize"] = synthesize
            from runtime.workflows.hermes_review_execute import run_hermes_review_execute
            return run_hermes_review_execute(
                {"task_id": task["task_id"], "synthesize": synthesize}, vault_root
            )

        hw._TASK_DISPATCH["review"] = mock_dispatch
        try:
            hw.run_hermes_watch({"synthesize": False}, vault)
        finally:
            hw._TASK_DISPATCH.update(original)

        assert captured_inputs.get("synthesize") is False

    def test_watch_aor_engine_runs_hermes_watch(self, tmp_path):
        vault = _make_vault(tmp_path)
        (tmp_path / "runtime" / "hermes").mkdir(parents=True, exist_ok=True)
        from runtime.aor.engine import run_workflow
        result = run_workflow("hermes_watch", {}, vault_root=vault)
        assert result.status in ("success", "escalated")

    def test_watch_multiple_tasks_all_dispatched(self, tmp_path):
        vault = _make_vault(tmp_path)
        artifact = vault / "07_LOGS" / "Build-Logs" / "test.md"
        artifact.write_text("# Log\n\n2026-04-26 content here enough words.")
        _post_review_task(vault, "07_LOGS/Build-Logs/test.md")
        _post_review_task(vault, "07_LOGS/Build-Logs/test.md")

        from runtime.workflows.hermes_watch import run_hermes_watch
        result = run_hermes_watch({"max_tasks_per_cycle": 2, "synthesize": False}, vault)

        assert result["tasks_dispatched"] == 2


# ── TestHermesWatchDispatch ───────────────────────────────────────────────────

class TestHermesWatchDispatch:

    def test_dispatch_table_has_review(self):
        from runtime.workflows.hermes_watch import _TASK_DISPATCH
        assert "review" in _TASK_DISPATCH

    def test_dispatch_table_has_bounded_analysis_types(self):
        from runtime.workflows.hermes_watch import _TASK_DISPATCH
        assert "planning" in _TASK_DISPATCH
        assert "shadow-audit" in _TASK_DISPATCH
        assert "developer-co-development" in _TASK_DISPATCH

    def test_task_type_inferred_from_intent(self):
        from runtime.workflows.hermes_watch import _task_type_from_task
        assert _task_type_from_task({"intent": "REVIEW"}) == "review"
        assert _task_type_from_task({"intent": "TASK"}) == "task"
        assert _task_type_from_task({"intent": "NOTICE"}) == "notice"
        assert _task_type_from_task({"intent": "unknown_type"}) == "unknown"

    def test_task_type_annotation_overrides_generic_task_intent(self):
        from runtime.workflows.hermes_watch import _task_type_from_task
        assert _task_type_from_task({"intent": "TASK", "notes": "task_type: planning"}) == "planning"
        assert _task_type_from_task({"intent": "TASK", "notes": "task_type: shadow_audit"}) == "shadow-audit"

    def test_unhandled_task_type_escalated(self, tmp_path):
        vault = _make_vault(tmp_path)
        # Post a TASK (not REVIEW) intent task — no handler in dispatch table
        from runtime.agent_bus.bus import create_task
        result = create_task(
            vault,
            sender="OpenClaw",
            recipient="Hermes",
            intent="TASK",
            priority="normal",
            request="Do some work.",
            expected_output="Result.",
        )
        assert result["created"]

        from runtime.workflows.hermes_watch import run_hermes_watch
        cycle_result = run_hermes_watch({"synthesize": False}, vault)

        assert cycle_result["tasks_escalated"] == 1
        assert cycle_result["tasks_dispatched"] == 0

    def test_escalated_task_marked_blocked_on_bus(self, tmp_path):
        vault = _make_vault(tmp_path)
        from runtime.agent_bus.bus import create_task, list_tasks
        create_task(
            vault,
            sender="OpenClaw",
            recipient="Hermes",
            intent="TASK",
            priority="normal",
            request="Do work.",
            expected_output="Result.",
        )

        from runtime.workflows.hermes_watch import run_hermes_watch
        run_hermes_watch({"synthesize": False}, vault)

        tasks = list_tasks(vault, recipient="Hermes")
        assert any(t["status"] == "blocked" for t in tasks)

    def test_review_task_dispatched_and_done(self, tmp_path):
        vault = _make_vault(tmp_path)
        artifact = vault / "07_LOGS" / "Build-Logs" / "test.md"
        artifact.write_text("# Log\n\n2026-04-26 some content here.")
        _post_review_task(vault, "07_LOGS/Build-Logs/test.md")

        from runtime.workflows.hermes_watch import run_hermes_watch
        from runtime.agent_bus.bus import list_tasks
        run_hermes_watch({"synthesize": False}, vault)

        tasks = list_tasks(vault, recipient="Hermes")
        assert any(t["status"] == "done" for t in tasks)

    def test_planning_task_dispatched_as_bounded_bus_analysis(self, tmp_path):
        vault = _make_vault(tmp_path)
        task_id = _post_planning_task(vault)

        from runtime.workflows.hermes_watch import run_hermes_watch
        from runtime.agent_bus.bus import list_tasks
        result = run_hermes_watch({"synthesize": False}, vault)

        assert result["tasks_dispatched"] == 1
        assert result["tasks_escalated"] == 0
        assert result["writebacks"]
        assert result["writebacks"][0]["path"].startswith("07_LOGS/Agent-Activity/")
        assert "hermes-watch-planning" in result["writebacks"][0]["path"]
        assert "No external connectors" in result["writebacks"][0]["content"]

        tasks = list_tasks(vault, recipient="Hermes")
        task = next(t for t in tasks if t["task_id"] == task_id)
        assert task["status"] == "done"

    def test_mixed_tasks_dispatched_and_escalated(self, tmp_path):
        vault = _make_vault(tmp_path)
        artifact = vault / "07_LOGS" / "Build-Logs" / "test.md"
        artifact.write_text("# Log\n\n2026-04-26 content here.")
        _post_review_task(vault, "07_LOGS/Build-Logs/test.md")

        from runtime.agent_bus.bus import create_task
        create_task(
            vault,
            sender="OpenClaw",
            recipient="Hermes",
            intent="TASK",
            priority="normal",
            request="Unhandled work.",
            expected_output="Result.",
        )

        from runtime.workflows.hermes_watch import run_hermes_watch
        result = run_hermes_watch({"max_tasks_per_cycle": 2, "synthesize": False}, vault)

        assert result["tasks_dispatched"] == 1
        assert result["tasks_escalated"] == 1
